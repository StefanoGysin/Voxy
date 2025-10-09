"""
Vision Agent Rate Limiting Middleware

Implementa rate limiting específico para o Vision Agent GPT-5:
- 10 uploads/min por usuário
- 50 análises/hour por usuário
- Cost tracking em tempo real
- Budget limits configuráveis
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from ...config.settings import settings
from ...core.cache.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)


class VisionRateLimiter:
    """
    Rate limiter específico para Vision Agent GPT-5.

    Implementa:
    - Rate limiting por usuário (10/min, 50/hour)
    - Cost tracking em tempo real
    - Budget monitoring e alerts
    - Redis-based persistence
    """

    def __init__(self):
        """Initialize the vision rate limiter."""
        self.cache = get_redis_cache()

        # Rate limits from settings
        self.uploads_per_minute = settings.vision_rate_limit_per_minute
        self.analyses_per_hour = settings.vision_rate_limit_per_hour
        self.monthly_quota = settings.vision_monthly_quota

        # Cost limits from settings
        self.max_cost_per_analysis = settings.vision_max_cost_per_analysis
        self.daily_budget_limit = settings.vision_daily_budget_limit
        self.monthly_budget_limit = settings.vision_monthly_budget_limit

    async def check_upload_rate_limit(self, user_id: str) -> bool:
        """
        Check if user can upload/analyze another image based on rate limits.

        Args:
            user_id: User identifier

        Returns:
            True if within limits, False otherwise

        Raises:
            HTTPException: If rate limit exceeded
        """
        await self.cache.connect()

        try:
            now = datetime.now()

            # Check minute limit (uploads)
            minute_key = f"vision:uploads:{user_id}:{now.strftime('%Y%m%d%H%M')}"
            minute_count = await self.cache.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0

            if minute_count >= self.uploads_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {self.uploads_per_minute} uploads per minute. Try again later.",
                )

            # Check hour limit (analyses)
            hour_key = f"vision:analyses:{user_id}:{now.strftime('%Y%m%d%H')}"
            hour_count = await self.cache.get(hour_key)
            hour_count = int(hour_count) if hour_count else 0

            if hour_count >= self.analyses_per_hour:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {self.analyses_per_hour} analyses per hour. Try again later.",
                )

            # Check monthly quota
            month_key = f"vision:quota:{user_id}:{now.strftime('%Y%m')}"
            month_count = await self.cache.get(month_key)
            month_count = int(month_count) if month_count else 0

            if month_count >= self.monthly_quota:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Monthly quota exceeded: {self.monthly_quota} analyses per month.",
                )

            return True

        finally:
            await self.cache.disconnect()

    async def check_cost_limits(self, user_id: str, estimated_cost: float) -> bool:
        """
        Check if user can proceed based on cost limits.

        Args:
            user_id: User identifier
            estimated_cost: Estimated cost for the analysis

        Returns:
            True if within limits, False otherwise

        Raises:
            HTTPException: If cost limit exceeded
        """
        await self.cache.connect()

        try:
            now = datetime.now()

            # Check per-analysis cost limit
            if estimated_cost > self.max_cost_per_analysis:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Analysis cost ${estimated_cost:.4f} exceeds limit ${self.max_cost_per_analysis:.4f}",
                )

            # Check daily budget
            daily_key = f"vision:cost:daily:{user_id}:{now.strftime('%Y%m%d')}"
            daily_cost = await self.cache.get(daily_key)
            daily_cost = float(daily_cost) if daily_cost else 0.0

            if daily_cost + estimated_cost > self.daily_budget_limit:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Daily budget limit exceeded. Current: ${daily_cost:.4f}, Limit: ${self.daily_budget_limit:.2f}",
                )

            # Check monthly budget
            monthly_key = f"vision:cost:monthly:{user_id}:{now.strftime('%Y%m')}"
            monthly_cost = await self.cache.get(monthly_key)
            monthly_cost = float(monthly_cost) if monthly_cost else 0.0

            if monthly_cost + estimated_cost > self.monthly_budget_limit:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Monthly budget limit exceeded. Current: ${monthly_cost:.2f}, Limit: ${self.monthly_budget_limit:.2f}",
                )

            return True

        finally:
            await self.cache.disconnect()

    async def increment_usage(self, user_id: str, actual_cost: float) -> None:
        """
        Increment usage counters after successful analysis.

        Args:
            user_id: User identifier
            actual_cost: Actual cost of the analysis
        """
        await self.cache.connect()

        try:
            now = datetime.now()

            # Increment rate limit counters
            minute_key = f"vision:uploads:{user_id}:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"vision:analyses:{user_id}:{now.strftime('%Y%m%d%H')}"
            month_key = f"vision:quota:{user_id}:{now.strftime('%Y%m')}"

            # Set expiration times
            await self.cache.increment(minute_key, expire=60)  # 1 minute
            await self.cache.increment(hour_key, expire=3600)  # 1 hour
            await self.cache.increment(month_key, expire=31 * 24 * 3600)  # ~1 month

            # Update cost tracking
            daily_cost_key = f"vision:cost:daily:{user_id}:{now.strftime('%Y%m%d')}"
            monthly_cost_key = f"vision:cost:monthly:{user_id}:{now.strftime('%Y%m')}"

            await self.cache.increment_float(
                daily_cost_key, actual_cost, expire=24 * 3600
            )  # 1 day
            await self.cache.increment_float(
                monthly_cost_key, actual_cost, expire=31 * 24 * 3600
            )  # ~1 month

            logger.info(
                f"Vision usage updated for user {user_id}: "
                f"cost=${actual_cost:.4f}, "
                f"minute_uploads=+1, hour_analyses=+1, month_quota=+1"
            )

        finally:
            await self.cache.disconnect()

    async def get_user_usage_stats(self, user_id: str) -> dict[str, Any]:
        """
        Get current usage statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with usage statistics
        """
        await self.cache.connect()

        try:
            now = datetime.now()

            # Get current counters
            minute_key = f"vision:uploads:{user_id}:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"vision:analyses:{user_id}:{now.strftime('%Y%m%d%H')}"
            month_key = f"vision:quota:{user_id}:{now.strftime('%Y%m')}"
            daily_cost_key = f"vision:cost:daily:{user_id}:{now.strftime('%Y%m%d')}"
            monthly_cost_key = f"vision:cost:monthly:{user_id}:{now.strftime('%Y%m')}"

            minute_count = int(await self.cache.get(minute_key) or 0)
            hour_count = int(await self.cache.get(hour_key) or 0)
            month_count = int(await self.cache.get(month_key) or 0)
            daily_cost = float(await self.cache.get(daily_cost_key) or 0.0)
            monthly_cost = float(await self.cache.get(monthly_cost_key) or 0.0)

            return {
                "rate_limits": {
                    "uploads_this_minute": minute_count,
                    "uploads_per_minute_limit": self.uploads_per_minute,
                    "analyses_this_hour": hour_count,
                    "analyses_per_hour_limit": self.analyses_per_hour,
                    "analyses_this_month": month_count,
                    "monthly_quota": self.monthly_quota,
                },
                "cost_tracking": {
                    "daily_cost": daily_cost,
                    "daily_budget_limit": self.daily_budget_limit,
                    "monthly_cost": monthly_cost,
                    "monthly_budget_limit": self.monthly_budget_limit,
                    "max_cost_per_analysis": self.max_cost_per_analysis,
                },
                "remaining": {
                    "uploads_this_minute": max(
                        0, self.uploads_per_minute - minute_count
                    ),
                    "analyses_this_hour": max(0, self.analyses_per_hour - hour_count),
                    "analyses_this_month": max(0, self.monthly_quota - month_count),
                    "daily_budget_remaining": max(
                        0, self.daily_budget_limit - daily_cost
                    ),
                    "monthly_budget_remaining": max(
                        0, self.monthly_budget_limit - monthly_cost
                    ),
                },
            }

        finally:
            await self.cache.disconnect()

    async def reset_user_limits(self, user_id: str, limit_type: str = "all") -> bool:
        """
        Reset specific limits for a user (admin function).

        Args:
            user_id: User identifier
            limit_type: Type of limit to reset ("minute", "hour", "month", "daily_cost", "monthly_cost", "all")

        Returns:
            True if successful
        """
        await self.cache.connect()

        try:
            now = datetime.now()

            keys_to_delete = []

            if limit_type in ["minute", "all"]:
                keys_to_delete.append(
                    f"vision:uploads:{user_id}:{now.strftime('%Y%m%d%H%M')}"
                )

            if limit_type in ["hour", "all"]:
                keys_to_delete.append(
                    f"vision:analyses:{user_id}:{now.strftime('%Y%m%d%H')}"
                )

            if limit_type in ["month", "all"]:
                keys_to_delete.append(f"vision:quota:{user_id}:{now.strftime('%Y%m')}")

            if limit_type in ["daily_cost", "all"]:
                keys_to_delete.append(
                    f"vision:cost:daily:{user_id}:{now.strftime('%Y%m%d')}"
                )

            if limit_type in ["monthly_cost", "all"]:
                keys_to_delete.append(
                    f"vision:cost:monthly:{user_id}:{now.strftime('%Y%m')}"
                )

            for key in keys_to_delete:
                await self.cache.delete(key)

            logger.info(f"Reset {limit_type} limits for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset limits for user {user_id}: {e}")
            return False

        finally:
            await self.cache.disconnect()


# Global instance
_vision_rate_limiter = None


def get_vision_rate_limiter() -> VisionRateLimiter:
    """Get the global vision rate limiter instance."""
    global _vision_rate_limiter
    if _vision_rate_limiter is None:
        _vision_rate_limiter = VisionRateLimiter()
    return _vision_rate_limiter
