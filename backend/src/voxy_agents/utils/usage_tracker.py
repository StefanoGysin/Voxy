"""
Token Usage Tracking Utility for VOXY Agents.

Provides centralized token usage tracking following OpenAI Agents SDK and LiteLLM
best practices. Extracts metrics from RunResult.context_wrapper.usage and logs
structured data via Loguru for enterprise observability.

Architecture:
- Extracts usage from result.context_wrapper.usage (correct SDK pattern)
- Calculates cost estimates via LiteLLM completion_cost
- Logs structured metrics with Loguru bind(event="USAGE_TRACKING|...")
- Supports PATH 1 (Vision + VOXY) and PATH 2 (VOXY only) tracking

Usage:
    from voxy_agents.utils.usage_tracker import extract_usage, log_usage_metrics

    result = await Runner.run(agent, message, session=session)
    usage = extract_usage(result)
    log_usage_metrics(trace_id="abc123", path="PATH_1", voxy_usage=usage)
"""

from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger


@dataclass
class SubagentInfo:
    """
    Information about a subagent invoked during VOXY processing.

    Used for hierarchical usage logging to show which models were involved,
    even though token breakdown is aggregated (SDK limitation).

    Attributes:
        name: Friendly agent name (e.g., "Weather Agent")
        model: LiteLLM model path (e.g., "openrouter/openai/gpt-4.1-nano")
        config: Model configuration dict (max_tokens, temperature, etc.)
        input_preview: Preview of input sent to subagent (truncated)
        output_preview: Preview of output from subagent (truncated)
    """

    name: str
    model: str
    config: dict[str, Any]
    input_preview: str
    output_preview: str


@dataclass
class UsageMetrics:
    """
    Token usage metrics for a single agent run.

    Follows OpenAI Agents SDK Usage object structure:
    - requests: Number of LLM API calls made
    - input_tokens: Total tokens in prompts sent to LLM
    - output_tokens: Total tokens in LLM responses
    - total_tokens: Sum of input_tokens + output_tokens

    Attributes:
        requests: Number of LLM API requests
        input_tokens: Total input (prompt) tokens
        output_tokens: Total output (completion) tokens
        total_tokens: Total tokens (input + output)
        estimated_cost_usd: Estimated cost in USD (optional, calculated via LiteLLM)
    """

    requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: Optional[float] = None


def extract_usage(result) -> Optional[UsageMetrics]:
    """
    Extract token usage metrics from OpenAI Agents SDK RunResult.

    IMPORTANT: OpenAI Agents SDK stores usage in result.context_wrapper.usage,
    NOT result.usage. This function follows the correct SDK pattern.

    Args:
        result: RunResult from Runner.run() or Runner.run_sync()

    Returns:
        UsageMetrics if usage data is available, None otherwise

    Example:
        >>> result = await Runner.run(agent, "Hello")
        >>> usage = extract_usage(result)
        >>> if usage:
        ...     print(f"Total tokens: {usage.total_tokens}")
    """
    # Check for context_wrapper.usage (correct SDK pattern)
    if not hasattr(result, "context_wrapper"):
        logger.bind(event="USAGE_TRACKER|EXTRACTION_FAILED").warning(
            "RunResult missing context_wrapper attribute",
            result_type=type(result).__name__,
        )
        return None

    if not hasattr(result.context_wrapper, "usage"):
        logger.bind(event="USAGE_TRACKER|EXTRACTION_FAILED").warning(
            "context_wrapper missing usage attribute"
        )
        return None

    usage = result.context_wrapper.usage

    # Validate usage object has expected attributes
    if not all(
        hasattr(usage, attr)
        for attr in ["requests", "input_tokens", "output_tokens", "total_tokens"]
    ):
        logger.bind(event="USAGE_TRACKER|EXTRACTION_FAILED").warning(
            "Usage object missing required attributes",
            available_attrs=dir(usage),
        )
        return None

    # Extract metrics
    metrics = UsageMetrics(
        requests=usage.requests,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
    )

    logger.bind(event="USAGE_TRACKER|EXTRACTION_SUCCESS").debug(
        "Usage metrics extracted successfully",
        requests=metrics.requests,
        total_tokens=metrics.total_tokens,
    )

    return metrics


def calculate_cost_estimate(
    usage: UsageMetrics,
    model_path: str,
) -> Optional[float]:
    """
    Calculate estimated cost in USD using LiteLLM's cost tracking.

    Args:
        usage: UsageMetrics with token counts
        model_path: LiteLLM model path (configurable via .env, e.g., "openrouter/anthropic/claude-sonnet-4.5")

    Returns:
        Estimated cost in USD, or None if calculation fails

    Example:
        >>> usage = UsageMetrics(requests=1, input_tokens=100, output_tokens=50, total_tokens=150)
        >>> cost = calculate_cost_estimate(usage, "openrouter/anthropic/claude-haiku-4.5")  # Example only
        >>> print(f"${cost:.6f}")
    """
    try:
        from litellm import cost_per_token

        # Calculate cost per token type
        input_cost, output_cost = cost_per_token(
            model=model_path,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
        )

        total_cost = input_cost + output_cost

        logger.bind(event="USAGE_TRACKER|COST_CALCULATED").debug(
            "Cost estimate calculated",
            model=model_path,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            total_cost_usd=total_cost,
        )

        return total_cost

    except Exception as e:
        logger.bind(event="USAGE_TRACKER|COST_CALCULATION_FAILED").warning(
            "Failed to calculate cost estimate",
            error=str(e),
            model=model_path,
        )
        return None


def log_usage_metrics(
    trace_id: str,
    path: str,
    voxy_usage: Optional[UsageMetrics],
    vision_usage: Optional[UsageMetrics] = None,
    total_time: float = 0.0,
    vision_time: float = 0.0,
    voxy_time: float = 0.0,
    model_path: Optional[str] = None,
    voxy_model: Optional[str] = None,
    voxy_config: Optional[dict[str, Any]] = None,
    subagents_called: Optional[list[SubagentInfo]] = None,
) -> None:
    """
    Log token usage metrics with hierarchical visual structure.

    Creates enterprise-grade observability logs with complete metrics for
    cost tracking, performance analysis, and debugging. Shows all models
    involved in the request with clear visual hierarchy.

    Args:
        trace_id: Unique request trace ID (8-char UUID)
        path: Execution path ("PATH_1" for Vision+VOXY, "PATH_2" for VOXY only)
        voxy_usage: VOXY Orchestrator usage metrics
        vision_usage: Vision Agent usage metrics (PATH 1 only, optional)
        total_time: Total processing time in seconds
        vision_time: Vision Agent processing time (PATH 1 only)
        voxy_time: VOXY Orchestrator processing time
        model_path: LiteLLM model path for cost calculation (optional)
        voxy_model: VOXY model name for display (optional)
        voxy_config: VOXY config dict for display (optional)
        subagents_called: List of subagents invoked during processing (optional)

    Example:
        >>> voxy_usage = UsageMetrics(requests=2, input_tokens=450, output_tokens=180, total_tokens=630)
        >>> subagents = [SubagentInfo(
        ...     name="Weather Agent",
        ...     model="openrouter/openai/gpt-4.1-nano",  # Example - configurable via .env
        ...     config={"max_tokens": 1500, "temperature": 0.1},
        ...     input_preview="Zurich",
        ...     output_preview="☁️ Zurich está com 8°C..."
        ... )]
        >>> log_usage_metrics(
        ...     trace_id="aa757833",
        ...     path="PATH_2",
        ...     voxy_usage=voxy_usage,
        ...     total_time=12.90,
        ...     voxy_time=12.90,
        ...     model_path="openrouter/anthropic/claude-sonnet-4.5",  # Example - configurable via .env
        ...     voxy_model="claude-sonnet-4.5",  # Example - configurable via .env
        ...     voxy_config={"max_tokens": 4000, "temperature": 0.3},
        ...     subagents_called=subagents
        ... )
    """
    # Check if usage is available
    if not voxy_usage and not vision_usage:
        logger.bind(event="USAGE_TRACKING|UNAVAILABLE").warning(
            "No usage metrics available for tracking",
            trace_id=trace_id,
            path=path,
            reason="Both voxy_usage and vision_usage are None",
        )
        return

    # Calculate cost estimate if model_path provided
    cost_estimate = None
    if voxy_usage and model_path:
        cost_estimate = calculate_cost_estimate(voxy_usage, model_path)

    # Build structured log data
    log_data = {
        "trace_id": trace_id,
        "path": path,
        "total_time_s": round(total_time, 2),
    }

    # Add Vision Agent metrics (PATH 1 only)
    if vision_usage:
        log_data.update(
            {
                "vision_time_s": round(vision_time, 2),
                "vision_requests": vision_usage.requests,
                "vision_input_tokens": vision_usage.input_tokens,
                "vision_output_tokens": vision_usage.output_tokens,
                "vision_total_tokens": vision_usage.total_tokens,
            }
        )

    # Add VOXY Orchestrator metrics
    if voxy_usage:
        log_data.update(
            {
                "voxy_time_s": round(voxy_time, 2),
                "voxy_requests": voxy_usage.requests,
                "voxy_input_tokens": voxy_usage.input_tokens,
                "voxy_output_tokens": voxy_usage.output_tokens,
                "voxy_total_tokens": voxy_usage.total_tokens,
            }
        )

    # Add cost estimate if available
    if cost_estimate is not None:
        log_data["estimated_cost_usd"] = round(cost_estimate, 6)

    # Log with structured binding
    logger.bind(event="USAGE_TRACKING|METRICS").info(
        "Token usage metrics tracked", **log_data
    )

    # Build hierarchical visual summary
    _log_hierarchical_summary(
        trace_id=trace_id,
        path=path,
        voxy_usage=voxy_usage,
        vision_usage=vision_usage,
        total_time=total_time,
        vision_time=vision_time,
        voxy_time=voxy_time,
        cost_estimate=cost_estimate,
        voxy_model=voxy_model,
        voxy_config=voxy_config,
        subagents_called=subagents_called,
    )


def _log_hierarchical_summary(
    trace_id: str,
    path: str,
    voxy_usage: Optional[UsageMetrics],
    vision_usage: Optional[UsageMetrics],
    total_time: float,
    vision_time: float,
    voxy_time: float,
    cost_estimate: Optional[float],
    voxy_model: Optional[str],
    voxy_config: Optional[dict[str, Any]],
    subagents_called: Optional[list[SubagentInfo]],
) -> None:
    """
    Log hierarchical visual summary with tree structure.

    Creates visual hierarchy showing:
    - VOXY Orchestrator model and config
    - Token usage (aggregated - includes subagent calls)
    - Subagents called (if any)
    - Performance metrics
    """
    # Build header
    lines = [f"📊 [TRACE:{trace_id}] Token Usage Summary ({path})"]
    lines.append("   │")

    # VOXY Orchestrator section
    lines.append("   ├─ 🤖 VOXY Orchestrator")

    if voxy_model:
        lines.append(f"   │  ├─ Model: {voxy_model}")

    if voxy_config:
        max_tokens = voxy_config.get("max_tokens", "N/A")
        temperature = voxy_config.get("temperature", "N/A")
        lines.append(f"   │  ├─ Config: {max_tokens} tokens, temp={temperature}")

    lines.append("   │  │")

    # Token usage section (aggregated)
    if voxy_usage:
        lines.append("   │  ├─ 📊 Token Usage (Aggregated - includes subagent calls)")
        lines.append(f"   │  │  ├─ Total requests: {voxy_usage.requests:,}")
        lines.append(f"   │  │  ├─ Input tokens: {voxy_usage.input_tokens:,}")
        lines.append(f"   │  │  ├─ Output tokens: {voxy_usage.output_tokens:,}")
        lines.append(f"   │  │  ├─ Total tokens: {voxy_usage.total_tokens:,}")

        if cost_estimate is not None:
            lines.append(f"   │  │  └─ Estimated cost: ${cost_estimate:.6f}")
        else:
            lines.append("   │  │  └─ Estimated cost: N/A")

        lines.append("   │  │")

    # Subagents section
    if subagents_called:
        lines.append("   │  └─ 🔧 Subagents Called")

        for idx, subagent in enumerate(subagents_called):
            is_last = idx == len(subagents_called) - 1
            prefix = "      └─" if is_last else "      ├─"
            continuation = "         " if is_last else "      │  "

            lines.append(f"{prefix} {subagent.name}")
            lines.append(f"{continuation}├─ Model: {subagent.model}")

            # Config
            max_tokens = subagent.config.get("max_tokens", "N/A")
            temperature = subagent.config.get("temperature", "N/A")
            lines.append(
                f"{continuation}├─ Config: {max_tokens} tokens, temp={temperature}"
            )

            # Input preview (truncated)
            input_truncated = (
                subagent.input_preview[:50] + "..."
                if len(subagent.input_preview) > 50
                else subagent.input_preview
            )
            lines.append(f'{continuation}├─ Input: "{input_truncated}"')

            # Output preview (truncated)
            output_truncated = (
                subagent.output_preview[:60] + "..."
                if len(subagent.output_preview) > 60
                else subagent.output_preview
            )
            lines.append(f'{continuation}└─ Output: "{output_truncated}"')
    else:
        lines.append("   │  └─ 🔧 Subagents Called: None")

    lines.append("   │")

    # Performance section
    lines.append("   └─ ⏱️  Performance")
    lines.append(f"      ├─ Total processing: {total_time:.2f}s")

    if cost_estimate and total_time > 0:
        cost_per_second = cost_estimate / total_time
        lines.append(f"      └─ Cost per second: ${cost_per_second:.6f}/s")
    else:
        lines.append("      └─ Cost per second: N/A")

    # Log all lines as single multiline message
    logger.info("\n".join(lines))
