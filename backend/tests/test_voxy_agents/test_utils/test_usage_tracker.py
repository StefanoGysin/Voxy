"""
Unit tests for Token Usage Tracking Utility.

Tests extraction, cost calculation, and logging of token usage metrics
following OpenAI Agents SDK and LiteLLM patterns.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.voxy_agents.utils.usage_tracker import (
    SubagentInfo,
    UsageMetrics,
    calculate_cost_estimate,
    extract_usage,
    log_usage_metrics,
)


class TestUsageMetrics:
    """Test UsageMetrics dataclass."""

    def test_usage_metrics_creation(self):
        """Test creating UsageMetrics instance."""
        metrics = UsageMetrics(
            requests=2, input_tokens=450, output_tokens=180, total_tokens=630
        )

        assert metrics.requests == 2
        assert metrics.input_tokens == 450
        assert metrics.output_tokens == 180
        assert metrics.total_tokens == 630
        assert metrics.estimated_cost_usd is None

    def test_usage_metrics_with_cost(self):
        """Test creating UsageMetrics with cost estimate."""
        metrics = UsageMetrics(
            requests=2,
            input_tokens=450,
            output_tokens=180,
            total_tokens=630,
            estimated_cost_usd=0.00189,
        )

        assert metrics.estimated_cost_usd == 0.00189


class TestExtractUsage:
    """Test extract_usage() function."""

    def test_extract_usage_success(self):
        """Test successful extraction of usage from RunResult."""
        # Mock RunResult with context_wrapper.usage
        mock_usage = MagicMock()
        mock_usage.requests = 2
        mock_usage.input_tokens = 450
        mock_usage.output_tokens = 180
        mock_usage.total_tokens = 630

        mock_context_wrapper = MagicMock()
        mock_context_wrapper.usage = mock_usage

        mock_result = MagicMock()
        mock_result.context_wrapper = mock_context_wrapper

        # Extract usage
        metrics = extract_usage(mock_result)

        # Verify
        assert metrics is not None
        assert isinstance(metrics, UsageMetrics)
        assert metrics.requests == 2
        assert metrics.input_tokens == 450
        assert metrics.output_tokens == 180
        assert metrics.total_tokens == 630

    def test_extract_usage_missing_context_wrapper(self):
        """Test graceful degradation when context_wrapper is missing."""
        # Mock RunResult without context_wrapper
        mock_result = MagicMock(spec=[])  # Empty spec - no attributes

        # Extract usage
        metrics = extract_usage(mock_result)

        # Should return None gracefully
        assert metrics is None

    def test_extract_usage_missing_usage_attribute(self):
        """Test graceful degradation when usage attribute is missing."""
        # Mock RunResult with context_wrapper but no usage
        mock_context_wrapper = MagicMock(spec=[])  # No usage attribute
        mock_result = MagicMock()
        mock_result.context_wrapper = mock_context_wrapper

        # Extract usage
        metrics = extract_usage(mock_result)

        # Should return None gracefully
        assert metrics is None

    def test_extract_usage_incomplete_usage_object(self):
        """Test graceful degradation when usage object has missing attributes."""

        # Mock usage with missing attributes (force AttributeError)
        class IncompleteUsage:
            def __init__(self):
                self.requests = 2
                # Deliberately missing: input_tokens, output_tokens, total_tokens

        mock_usage = IncompleteUsage()

        mock_context_wrapper = MagicMock()
        mock_context_wrapper.usage = mock_usage

        mock_result = MagicMock()
        mock_result.context_wrapper = mock_context_wrapper

        # Extract usage
        metrics = extract_usage(mock_result)

        # Should return None gracefully
        assert metrics is None


class TestCalculateCostEstimate:
    """Test calculate_cost_estimate() function."""

    @patch("litellm.cost_per_token")
    def test_calculate_cost_success(self, mock_cost_per_token):
        """Test successful cost calculation."""
        # Mock cost_per_token return values
        mock_cost_per_token.return_value = (0.00135, 0.00054)  # (input, output)

        usage = UsageMetrics(
            requests=2, input_tokens=450, output_tokens=180, total_tokens=630
        )

        cost = calculate_cost_estimate(usage, "openrouter/anthropic/claude-sonnet-4.5")

        # Verify
        assert cost is not None
        assert cost == pytest.approx(
            0.00189
        )  # 0.00135 + 0.00054 (floating point precision)
        mock_cost_per_token.assert_called_once_with(
            model="openrouter/anthropic/claude-sonnet-4.5",
            prompt_tokens=450,
            completion_tokens=180,
        )

    @patch("litellm.cost_per_token")
    def test_calculate_cost_failure(self, mock_cost_per_token):
        """Test graceful degradation when cost calculation fails."""
        # Mock cost_per_token to raise exception
        mock_cost_per_token.side_effect = Exception("API error")

        usage = UsageMetrics(
            requests=2, input_tokens=450, output_tokens=180, total_tokens=630
        )

        cost = calculate_cost_estimate(usage, "unknown/model")

        # Should return None gracefully
        assert cost is None


class TestLogUsageMetrics:
    """Test log_usage_metrics() function."""

    def test_log_usage_path1_with_cost(self):
        """Test logging PATH 1 metrics with cost estimate."""
        voxy_usage = UsageMetrics(
            requests=2, input_tokens=450, output_tokens=180, total_tokens=630
        )

        # Should not raise any exceptions
        log_usage_metrics(
            trace_id="aa757833",
            path="PATH_1",
            voxy_usage=voxy_usage,
            total_time=21.97,
            vision_time=10.02,
            voxy_time=11.95,
            model_path="openrouter/anthropic/claude-sonnet-4.5",
        )

    def test_log_usage_path2_without_cost(self):
        """Test logging PATH 2 metrics without cost estimate."""
        voxy_usage = UsageMetrics(
            requests=1, input_tokens=200, output_tokens=80, total_tokens=280
        )

        # Should not raise any exceptions
        log_usage_metrics(
            trace_id="12345678",
            path="PATH_2",
            voxy_usage=voxy_usage,
            total_time=5.5,
            voxy_time=5.5,
        )

    def test_log_usage_no_metrics_available(self):
        """Test logging when no metrics are available."""
        # Should not raise any exceptions
        log_usage_metrics(
            trace_id="00000000",
            path="PATH_2",
            voxy_usage=None,
            vision_usage=None,
            total_time=3.0,
        )

    def test_log_usage_vision_metrics_only(self):
        """Test logging with only vision metrics (hypothetical case)."""
        vision_usage = UsageMetrics(
            requests=1, input_tokens=100, output_tokens=50, total_tokens=150
        )

        # Should not raise any exceptions
        log_usage_metrics(
            trace_id="vision123",
            path="PATH_1",
            voxy_usage=None,
            vision_usage=vision_usage,
            total_time=10.0,
            vision_time=10.0,
        )

    def test_log_usage_with_subagent_hierarchy(self):
        """Test logging with hierarchical subagent information."""
        voxy_usage = UsageMetrics(
            requests=2, input_tokens=3200, output_tokens=1486, total_tokens=4686
        )

        subagents = [
            SubagentInfo(
                name="Weather Agent",
                model="openrouter/openai/gpt-4.1-nano",
                config={"max_tokens": 1500, "temperature": 0.1},
                input_preview="Zurich",
                output_preview="☁️ Zurich está com 8°C, com céu nublado...",
            )
        ]

        # Should not raise any exceptions
        log_usage_metrics(
            trace_id="ebfa63bd",
            path="PATH_2",
            voxy_usage=voxy_usage,
            total_time=12.90,
            voxy_time=12.90,
            model_path="openrouter/anthropic/claude-sonnet-4.5",
            voxy_model="claude-sonnet-4.5",
            voxy_config={"max_tokens": 4000, "temperature": 0.3},
            subagents_called=subagents,
        )

    def test_log_usage_with_multiple_subagents(self):
        """Test logging with multiple subagents in hierarchy."""
        voxy_usage = UsageMetrics(
            requests=3, input_tokens=5000, output_tokens=2000, total_tokens=7000
        )

        subagents = [
            SubagentInfo(
                name="Translator Agent",
                model="openrouter/anthropic/claude-haiku-4.5",
                config={"max_tokens": 2000, "temperature": 0.3},
                input_preview='{"text": "Hello world", "target_language": "pt-BR"}',
                output_preview="Olá mundo",
            ),
            SubagentInfo(
                name="Calculator Agent",
                model="openrouter/anthropic/claude-haiku-4.5",
                config={"max_tokens": 2000, "temperature": 0.1},
                input_preview="2 + 2",
                output_preview="4",
            ),
        ]

        # Should not raise any exceptions
        log_usage_metrics(
            trace_id="multi123",
            path="PATH_2",
            voxy_usage=voxy_usage,
            total_time=15.5,
            voxy_time=15.5,
            model_path="openrouter/anthropic/claude-sonnet-4.5",
            voxy_model="claude-sonnet-4.5",
            voxy_config={"max_tokens": 4000, "temperature": 0.3},
            subagents_called=subagents,
        )

    def test_log_usage_with_long_input_output_truncation(self):
        """Test that long inputs/outputs are properly truncated in display."""
        voxy_usage = UsageMetrics(
            requests=1, input_tokens=500, output_tokens=200, total_tokens=700
        )

        # Create subagent with very long input/output
        long_input = "A" * 100  # 100 characters
        long_output = "B" * 150  # 150 characters

        subagents = [
            SubagentInfo(
                name="Test Agent",
                model="openrouter/test/model",
                config={"max_tokens": 1000, "temperature": 0.5},
                input_preview=long_input,
                output_preview=long_output,
            )
        ]

        # Should not raise any exceptions and should handle truncation
        log_usage_metrics(
            trace_id="truncate1",
            path="PATH_2",
            voxy_usage=voxy_usage,
            total_time=8.0,
            voxy_time=8.0,
            model_path="openrouter/test/model",
            voxy_model="test-model",
            voxy_config={"max_tokens": 1000, "temperature": 0.5},
            subagents_called=subagents,
        )
