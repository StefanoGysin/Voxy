"""
Token management service for VOXY Agents.
Handles JWT token blacklisting and validation using Redis.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

import redis
import jwt
from ..config.settings import settings


class TokenManager:
    """Manages JWT token blacklisting and validation."""
    
    def __init__(self):
        """Initialize Redis connection for token blacklist."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connected for token management")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("⚠️ Token blacklisting will be disabled")
            self.redis_client = None

    def _get_blacklist_key(self, jti: str) -> str:
        """Generate Redis key for blacklisted token."""
        return f"voxy:token:blacklist:{jti}"

    def _get_token_info_key(self, jti: str) -> str:
        """Generate Redis key for token information."""
        return f"voxy:token:info:{jti}"

    async def blacklist_token(self, jti: str, user_id: str, expiration: datetime) -> bool:
        """
        Add token to blacklist.
        
        Args:
            jti: JWT ID to blacklist
            user_id: User ID who owns the token
            expiration: Token expiration time
            
        Returns:
            True if successfully blacklisted, False otherwise
        """
        if not self.redis_client:
            print("⚠️ Redis not available, cannot blacklist token")
            return False
            
        try:
            # Calculate TTL (seconds until expiration)
            now = datetime.now(timezone.utc)
            ttl = int((expiration - now).total_seconds())
            
            if ttl <= 0:
                print(f"🕒 Token {jti} already expired, no need to blacklist")
                return True
                
            # Store in blacklist with TTL
            blacklist_key = self._get_blacklist_key(jti)
            token_info = {
                "user_id": user_id,
                "blacklisted_at": now.isoformat(),
                "expires_at": expiration.isoformat()
            }
            
            # Set with expiration time
            self.redis_client.setex(
                blacklist_key,
                ttl,
                json.dumps(token_info)
            )
            
            print(f"🚫 Token {jti} blacklisted for user {user_id} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to blacklist token {jti}: {e}")
            return False

    async def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            jti: JWT ID to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        if not self.redis_client:
            # If Redis is not available, assume token is valid
            return False
            
        try:
            blacklist_key = self._get_blacklist_key(jti)
            result = self.redis_client.get(blacklist_key)
            
            is_blacklisted = result is not None
            if is_blacklisted:
                print(f"🚫 Token {jti} is blacklisted")
                
            return is_blacklisted
            
        except Exception as e:
            print(f"❌ Failed to check token blacklist for {jti}: {e}")
            # On error, assume token is valid for security
            return False

    async def store_token_info(self, jti: str, user_id: str, email: str, expiration: datetime) -> bool:
        """
        Store token information for tracking.
        
        Args:
            jti: JWT ID
            user_id: User ID
            email: User email
            expiration: Token expiration
            
        Returns:
            True if successfully stored, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            # Calculate TTL
            now = datetime.now(timezone.utc)
            ttl = int((expiration - now).total_seconds())
            
            if ttl <= 0:
                return False
                
            info_key = self._get_token_info_key(jti)
            token_info = {
                "user_id": user_id,
                "email": email,
                "created_at": now.isoformat(),
                "expires_at": expiration.isoformat()
            }
            
            self.redis_client.setex(
                info_key,
                ttl,
                json.dumps(token_info)
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to store token info for {jti}: {e}")
            return False

    async def get_token_info(self, jti: str) -> Optional[dict]:
        """
        Get token information.
        
        Args:
            jti: JWT ID
            
        Returns:
            Token information dict or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            info_key = self._get_token_info_key(jti)
            result = self.redis_client.get(info_key)
            
            if result:
                return json.loads(result)
            return None
            
        except Exception as e:
            print(f"❌ Failed to get token info for {jti}: {e}")
            return None

    async def blacklist_user_tokens(self, user_id: str) -> int:
        """
        Blacklist all tokens for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of tokens blacklisted
        """
        if not self.redis_client:
            return 0
            
        try:
            # Find all token info keys for the user
            info_pattern = f"voxy:token:info:*"
            info_keys = self.redis_client.keys(info_pattern)
            
            blacklisted_count = 0
            now = datetime.now(timezone.utc)
            
            for info_key in info_keys:
                try:
                    token_data = self.redis_client.get(info_key)
                    if not token_data:
                        continue
                        
                    token_info = json.loads(token_data)
                    
                    # Check if this token belongs to the user
                    if token_info.get("user_id") == user_id:
                        # Extract JTI from key
                        jti = info_key.split(":")[-1]
                        
                        # Parse expiration time
                        exp_str = token_info.get("expires_at")
                        if exp_str:
                            expiration = datetime.fromisoformat(exp_str.replace('Z', '+00:00'))
                            
                            # Blacklist if not expired
                            if expiration > now:
                                await self.blacklist_token(jti, user_id, expiration)
                                blacklisted_count += 1
                                
                except Exception as e:
                    print(f"❌ Error processing token {info_key}: {e}")
                    continue
            
            print(f"🚫 Blacklisted {blacklisted_count} tokens for user {user_id}")
            return blacklisted_count
            
        except Exception as e:
            print(f"❌ Failed to blacklist user tokens for {user_id}: {e}")
            return 0

    def get_redis_stats(self) -> dict:
        """Get Redis connection statistics."""
        if not self.redis_client:
            return {"status": "disconnected", "error": "Redis not available"}
            
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global token manager instance
token_manager = TokenManager()