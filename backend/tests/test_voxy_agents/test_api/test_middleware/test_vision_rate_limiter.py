"""
Tests for Vision Agent Rate Limiter

Testa o sistema de rate limiting específico do Vision Agent GPT-5:
- Rate limits (10/min, 50/hour)
- Cost tracking em tempo real
- Budget monitoring
- Redis persistence
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from src.voxy_agents.api.middleware.vision_rate_limiter import (
    VisionRateLimiter,
    get_vision_rate_limiter,
)


class TestVisionRateLimiter:
    """Test suite for VisionRateLimiter."""

    @pytest.fixture
    def rate_limiter(self):
        """Create VisionRateLimiter instance for testing."""
        with patch(
            "src.voxy_agents.api.middleware.vision_rate_limiter.get_redis_cache"
        ) as mock_redis:
            mock_cache = AsyncMock()
            mock_redis.return_value = mock_cache
            limiter = VisionRateLimiter()
            limiter.cache = mock_cache
            return limiter, mock_cache

    @pytest.mark.asyncio
    async def test_init_rate_limiter(self, rate_limiter):
        """Test VisionRateLimiter initialization."""
        limiter, mock_cache = rate_limiter

        # Check default values from settings
        assert limiter.uploads_per_minute == 10
        assert limiter.analyses_per_hour == 50
        assert limiter.monthly_quota == 1000
        assert limiter.max_cost_per_analysis == 0.10
        assert limiter.daily_budget_limit == 50.00
        assert limiter.monthly_budget_limit == 500.00

    @pytest.mark.asyncio
    async def test_check_upload_rate_limit_within_limits(self, rate_limiter):
        """Test rate limit check when within limits."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - all within limits
        mock_cache.get.side_effect = [
            "5",  # minute count (< 10)
            "20",  # hour count (< 50)
            "100",  # month count (< 1000)
        ]

        # Should pass without exception
        result = await limiter.check_upload_rate_limit("test_user")
        assert result is True

        # Verify Redis calls
        assert mock_cache.connect.called
        assert mock_cache.disconnect.called
        assert mock_cache.get.call_count == 3

    @pytest.mark.asyncio
    async def test_check_upload_rate_limit_minute_exceeded(self, rate_limiter):
        """Test rate limit check when minute limit exceeded."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - minute limit exceeded
        mock_cache.get.side_effect = [
            "10",  # minute count (>= 10)
        ]

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_upload_rate_limit("test_user")

        assert exc_info.value.status_code == 429
        assert "10 uploads per minute" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_upload_rate_limit_hour_exceeded(self, rate_limiter):
        """Test rate limit check when hour limit exceeded."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - hour limit exceeded
        mock_cache.get.side_effect = [
            "5",  # minute count (< 10)
            "50",  # hour count (>= 50)
        ]

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_upload_rate_limit("test_user")

        assert exc_info.value.status_code == 429
        assert "50 analyses per hour" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_upload_rate_limit_month_exceeded(self, rate_limiter):
        """Test rate limit check when monthly quota exceeded."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - monthly quota exceeded
        mock_cache.get.side_effect = [
            "5",  # minute count (< 10)
            "20",  # hour count (< 50)
            "1000",  # month count (>= 1000)
        ]

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_upload_rate_limit("test_user")

        assert exc_info.value.status_code == 429
        assert "1000 analyses per month" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_cost_limits_within_budget(self, rate_limiter):
        """Test cost check when within budget limits."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - within budget
        mock_cache.get.side_effect = [
            "10.50",  # daily cost (< 50.00)
            "250.75",  # monthly cost (< 500.00)
        ]

        # Should pass without exception
        result = await limiter.check_cost_limits("test_user", 0.05)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_cost_limits_per_analysis_exceeded(self, rate_limiter):
        """Test cost check when per-analysis limit exceeded."""
        limiter, mock_cache = rate_limiter

        # Should raise HTTPException for high cost
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_cost_limits("test_user", 0.15)  # > 0.10 limit

        assert exc_info.value.status_code == 402
        assert "exceeds limit $0.1000" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_cost_limits_daily_budget_exceeded(self, rate_limiter):
        """Test cost check when daily budget exceeded."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - daily budget near limit
        mock_cache.get.side_effect = [
            "49.98",  # daily cost (+ 0.05 would exceed 50.00)
            "250.75",  # monthly cost
        ]

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_cost_limits("test_user", 0.05)

        assert exc_info.value.status_code == 402
        assert "Daily budget limit exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_cost_limits_monthly_budget_exceeded(self, rate_limiter):
        """Test cost check when monthly budget exceeded."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses - monthly budget near limit
        mock_cache.get.side_effect = [
            "10.50",  # daily cost
            "499.98",  # monthly cost (+ 0.05 would exceed 500.00)
        ]

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_cost_limits("test_user", 0.05)

        assert exc_info.value.status_code == 402
        assert "Monthly budget limit exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_increment_usage(self, rate_limiter):
        """Test usage increment after successful analysis."""
        limiter, mock_cache = rate_limiter

        # Mock datetime to ensure consistent date
        with patch(
            "src.voxy_agents.api.middleware.vision_rate_limiter.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 9, 20, 14, 30, 0)
            mock_datetime.strftime = datetime.strftime

            # Should increment all counters
            await limiter.increment_usage("test_user", 0.0375)

        # Verify Redis increment calls
        assert mock_cache.increment.call_count == 3  # minute, hour, month
        assert mock_cache.increment_float.call_count == 2  # daily, monthly cost

        # Check that increment_float was called with correct cost
        mock_cache.increment_float.assert_any_call(
            "vision:cost:daily:test_user:20250920", 0.0375, expire=86400
        )

    @pytest.mark.asyncio
    async def test_get_user_usage_stats(self, rate_limiter):
        """Test getting user usage statistics."""
        limiter, mock_cache = rate_limiter

        # Mock Redis responses for stats
        mock_cache.get.side_effect = [
            "3",  # minute count
            "15",  # hour count
            "85",  # month count
            "12.45",  # daily cost
            "156.78",  # monthly cost
        ]

        stats = await limiter.get_user_usage_stats("test_user")

        # Verify structure and values
        assert "rate_limits" in stats
        assert "cost_tracking" in stats
        assert "remaining" in stats

        assert stats["rate_limits"]["uploads_this_minute"] == 3
        assert stats["rate_limits"]["analyses_this_hour"] == 15
        assert stats["rate_limits"]["analyses_this_month"] == 85

        assert stats["cost_tracking"]["daily_cost"] == 12.45
        assert stats["cost_tracking"]["monthly_cost"] == 156.78

        assert stats["remaining"]["uploads_this_minute"] == 7  # 10 - 3
        assert stats["remaining"]["analyses_this_hour"] == 35  # 50 - 15
        assert stats["remaining"]["daily_budget_remaining"] == 37.55  # 50.00 - 12.45

    @pytest.mark.asyncio
    async def test_reset_user_limits_all(self, rate_limiter):
        """Test resetting all user limits."""
        limiter, mock_cache = rate_limiter

        result = await limiter.reset_user_limits("test_user", "all")

        assert result is True
        # Should delete all 5 key types
        assert mock_cache.delete.call_count == 5

    @pytest.mark.asyncio
    async def test_reset_user_limits_specific(self, rate_limiter):
        """Test resetting specific limit type."""
        limiter, mock_cache = rate_limiter

        result = await limiter.reset_user_limits("test_user", "minute")

        assert result is True
        # Should delete only 1 key
        assert mock_cache.delete.call_count == 1

    @pytest.mark.asyncio
    async def test_reset_user_limits_error_handling(self, rate_limiter):
        """Test error handling in reset_user_limits."""
        limiter, mock_cache = rate_limiter

        # Mock Redis error
        mock_cache.delete.side_effect = Exception("Redis error")

        result = await limiter.reset_user_limits("test_user", "all")

        assert result is False

    @pytest.mark.asyncio
    async def test_global_instance_singleton(self):
        """Test that get_vision_rate_limiter returns singleton."""
        with patch(
            "src.voxy_agents.api.middleware.vision_rate_limiter.get_redis_cache"
        ):
            limiter1 = get_vision_rate_limiter()
            limiter2 = get_vision_rate_limiter()

            # Should be the same instance
            assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_rate_limit_key_format(self, rate_limiter):
        """Test that Redis keys are formatted correctly."""
        limiter, mock_cache = rate_limiter

        with patch(
            "src.voxy_agents.api.middleware.vision_rate_limiter.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 9, 20, 14, 30, 0)
            mock_datetime.strftime = datetime.strftime

            await limiter.increment_usage("user123", 0.05)

            # Verify key formats
            expected_calls = [
                "vision:uploads:user123:202509201430",  # minute key
                "vision:analyses:user123:2025092014",  # hour key
                "vision:quota:user123:202509",  # month key
            ]

            for call in mock_cache.increment.call_args_list:
                assert any(expected in str(call) for expected in expected_calls)

    @pytest.mark.asyncio
    async def test_cost_tracking_precision(self, rate_limiter):
        """Test cost tracking maintains precision."""
        limiter, mock_cache = rate_limiter

        # Test with precise cost
        precise_cost = 0.0347
        await limiter.increment_usage("test_user", precise_cost)

        # Verify increment_float called with precise value
        mock_cache.increment_float.assert_any_call(
            f"vision:cost:daily:test_user:{datetime.now().strftime('%Y%m%d')}",
            precise_cost,
            expire=86400,
        )

    @pytest.mark.asyncio
    async def test_redis_connection_handling(self, rate_limiter):
        """Test Redis connection and disconnection handling."""
        limiter, mock_cache = rate_limiter

        await limiter.check_upload_rate_limit("test_user")

        # Should connect and disconnect
        mock_cache.connect.assert_called()
        mock_cache.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_expiration_times(self, rate_limiter):
        """Test that correct expiration times are set."""
        limiter, mock_cache = rate_limiter

        await limiter.increment_usage("test_user", 0.05)

        # Verify expiration times in increment calls
        increment_calls = mock_cache.increment.call_args_list
        increment_float_calls = mock_cache.increment_float.call_args_list

        # Minute: 60s, Hour: 3600s, Month: ~31 days
        assert any("expire=60" in str(call) for call in increment_calls)
        assert any("expire=3600" in str(call) for call in increment_calls)
        assert any(
            "expire=2678400" in str(call) for call in increment_calls
        )  # 31*24*3600

        # Daily: 24h, Monthly: ~31 days
        assert any("expire=86400" in str(call) for call in increment_float_calls)
        assert any("expire=2678400" in str(call) for call in increment_float_calls)
