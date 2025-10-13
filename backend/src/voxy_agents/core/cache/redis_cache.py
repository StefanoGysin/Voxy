"""
Redis cache implementation for VOXY Agents.

Migração Loguru - Sprint 4
"""

import asyncio
import json
from datetime import timedelta
from functools import lru_cache
from typing import Any, Optional, Union

import redis.asyncio as redis
from loguru import logger

from ...config.settings import settings


class RedisCache:
    """Redis cache manager for VOXY Agents."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if not self._redis:
            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            try:
                await self._redis.ping()
                logger.bind(event="REDIS_CACHE|CONNECT").info("Redis connection established")
            except Exception as e:
                logger.bind(event="REDIS_CACHE|CONNECT_ERROR").exception("Redis connection failed")
                self._redis = None
                raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self._redis:
            await self.connect()

        try:
            value = await self._redis.get(key)
            if value:
                logger.bind(event="REDIS_CACHE|GET_HIT").debug("Cache hit", key=key[:50])
                return json.loads(value)
            logger.bind(event="REDIS_CACHE|GET_MISS").debug("Cache miss", key=key[:50])
            return None
        except Exception as e:
            logger.bind(event="REDIS_CACHE|GET_ERROR").error("Redis get error", key=key[:50], error=str(e))
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds or timedelta)

        Returns:
            True if successful
        """
        if not self._redis:
            await self.connect()

        try:
            serialized_value = json.dumps(value, default=str)

            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                result = await self._redis.setex(key, ttl, serialized_value)
            else:
                result = await self._redis.set(key, serialized_value)

            logger.bind(event="REDIS_CACHE|SET").debug("Cache set", key=key[:50], ttl=ttl)
            return result
        except Exception as e:
            logger.bind(event="REDIS_CACHE|SET_ERROR").error("Redis set error", key=key[:50], error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted
        """
        if not self._redis:
            await self.connect()

        try:
            result = bool(await self._redis.delete(key))
            logger.bind(event="REDIS_CACHE|DELETE").debug("Cache delete", key=key[:50], deleted=result)
            return result
        except Exception as e:
            logger.bind(event="REDIS_CACHE|DELETE_ERROR").error("Redis delete error", key=key[:50], error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        if not self._redis:
            await self.connect()

        try:
            return bool(await self._redis.exists(key))
        except Exception as e:
            logger.bind(event="REDIS_CACHE|EXISTS_ERROR").error("Redis exists error", key=key[:50], error=str(e))
            return False

    async def get_or_set(
        self, key: str, factory_func, ttl: Optional[Union[int, timedelta]] = None
    ) -> Any:
        """
        Get value from cache or set it using factory function.

        Args:
            key: Cache key
            factory_func: Function to generate value if not cached
            ttl: Time to live

        Returns:
            Cached or generated value
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value

        # Generate new value
        new_value = (
            await factory_func()
            if asyncio.iscoroutinefunction(factory_func)
            else factory_func()
        )

        # Cache the new value
        await self.set(key, new_value, ttl)

        return new_value

    # Specific cache methods for VOXY Agents

    async def cache_agent_response(
        self,
        agent_type: str,
        input_hash: str,
        response: Any,
        ttl: timedelta = timedelta(hours=1),
    ) -> bool:
        """
        Cache agent response.

        Args:
            agent_type: Type of agent (voxy, translator, weather, etc.)
            input_hash: Hash of the input parameters
            response: Agent response to cache
            ttl: Time to live

        Returns:
            True if cached successfully
        """
        key = f"agent:{agent_type}:{input_hash}"
        return await self.set(key, response, ttl)

    async def get_cached_agent_response(
        self, agent_type: str, input_hash: str
    ) -> Optional[Any]:
        """
        Get cached agent response.

        Args:
            agent_type: Type of agent
            input_hash: Hash of the input parameters

        Returns:
            Cached response or None
        """
        key = f"agent:{agent_type}:{input_hash}"
        return await self.get(key)

    async def cache_session(
        self, session_id: str, session_data: Any, ttl: timedelta = timedelta(minutes=30)
    ) -> bool:
        """
        Cache session data.

        Args:
            session_id: Session ID
            session_data: Session data to cache
            ttl: Time to live

        Returns:
            True if cached successfully
        """
        key = f"session:{session_id}"
        return await self.set(key, session_data, ttl)

    async def get_cached_session(self, session_id: str) -> Optional[Any]:
        """
        Get cached session data.

        Args:
            session_id: Session ID

        Returns:
            Cached session data or None
        """
        key = f"session:{session_id}"
        return await self.get(key)

    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate cached session.

        Args:
            session_id: Session ID

        Returns:
            True if invalidated
        """
        key = f"session:{session_id}"
        return await self.delete(key)

    async def increment(
        self, key: str, amount: int = 1, expire: Optional[int] = None
    ) -> int:
        """
        Increment a numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment by (default: 1)
            expire: Expiration time in seconds

        Returns:
            New value after increment
        """
        if not self._redis:
            await self.connect()

        try:
            # Use Redis INCR/INCRBY for atomic increment
            if amount == 1:
                new_value = await self._redis.incr(key)
            else:
                new_value = await self._redis.incrby(key, amount)

            # Set expiration if specified
            if expire and new_value == amount:  # Only set expire on first increment
                await self._redis.expire(key, expire)

            return new_value
        except Exception as e:
            logger.bind(event="REDIS_CACHE|INCREMENT_ERROR").error("Redis increment error", key=key[:50], error=str(e))
            return 0

    async def increment_float(
        self, key: str, amount: float, expire: Optional[int] = None
    ) -> float:
        """
        Increment a floating point value in cache.

        Args:
            key: Cache key
            amount: Amount to increment by
            expire: Expiration time in seconds

        Returns:
            New value after increment
        """
        if not self._redis:
            await self.connect()

        try:
            # Use Redis INCRBYFLOAT for atomic float increment
            new_value = await self._redis.incrbyfloat(key, amount)

            # Set expiration if this is the first increment
            current_ttl = await self._redis.ttl(key)
            if expire and current_ttl == -1:  # Key exists but has no expiration
                await self._redis.expire(key, expire)

            return new_value
        except Exception as e:
            logger.bind(event="REDIS_CACHE|INCREMENT_FLOAT_ERROR").error("Redis increment_float error", key=key[:50], error=str(e))
            return 0.0


@lru_cache
def get_redis_cache() -> RedisCache:
    """
    Get Redis cache instance.

    Returns:
        RedisCache: Configured Redis cache instance
    """
    return RedisCache(settings.redis_url)
