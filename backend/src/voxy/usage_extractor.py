"""
LangGraph Usage Extraction Utilities

Extracts token usage metrics and tool invocations from LangGraph execution results
and converts them to the format expected by usage_tracker.py.

Architecture:
- Bridges LangGraph state/callbacks → usage_tracker.py interface
- Maintains SDK-LangGraph format parity for seamless feature flag switching
- Supports multi-model cost aggregation

Phase 4A: extract_usage_from_state() - Token usage from VoxyState
Phase 4B: extract_tool_invocations() - Subagent calls for hierarchical logs
Phase 4D: aggregate_costs_by_model() - Multi-model cost calculation
"""

from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from loguru import logger

from shared.utils.usage_tracker import SubagentInfo, UsageMetrics
from voxy.graph_state import VoxyState

from .usage_callback import (
    ToolInvocationData,
    UsageCallbackHandler,
)

try:
    from litellm import cost_per_token

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.bind(event="USAGE_EXTRACTOR|LITELLM_MISSING").warning(
        "LiteLLM not available, cost calculation will be disabled"
    )


def extract_usage_from_state(
    state: VoxyState, callback_handler: UsageCallbackHandler | None = None
) -> UsageMetrics | None:
    """
    Extract token usage metrics from LangGraph VoxyState.

    Traverses state["messages"] to find AIMessage objects with usage_metadata,
    aggregates tokens across all LLM calls, and returns UsageMetrics compatible
    with usage_tracker.py.

    Args:
        state: VoxyState after graph execution
        callback_handler: Optional callback handler with additional telemetry

    Returns:
        UsageMetrics with aggregated token counts, or None if no usage data found

    Example:
        >>> result = graph.invoke(state, config=config)
        >>> usage = extract_usage_from_state(result)
        >>> if usage:
        ...     print(f"Total: {usage.total_tokens} tokens")
    """
    messages = state.get("messages", [])

    if not messages:
        logger.bind(event="USAGE_EXTRACTOR|NO_MESSAGES").debug(
            "No messages in state, cannot extract usage"
        )
        return None

    # Aggregate usage from AIMessage.usage_metadata
    total_input_tokens = 0
    total_output_tokens = 0
    total_requests = 0

    for message in messages:
        if isinstance(message, AIMessage):
            # LangGraph/LangChain attaches usage_metadata to AIMessage
            if hasattr(message, "usage_metadata") and message.usage_metadata:
                metadata = message.usage_metadata
                total_input_tokens += metadata.get("input_tokens", 0)
                total_output_tokens += metadata.get("output_tokens", 0)
                total_requests += 1

                logger.bind(event="USAGE_EXTRACTOR|AI_MESSAGE_USAGE").debug(
                    f"Found usage in AIMessage: "
                    f"{metadata.get('input_tokens', 0)} in + "
                    f"{metadata.get('output_tokens', 0)} out"
                )

    # Fallback: try callback handler if state didn't have usage
    if total_requests == 0 and callback_handler:
        logger.bind(event="USAGE_EXTRACTOR|FALLBACK_CALLBACK").debug(
            "No usage in state messages, trying callback handler"
        )
        summary = callback_handler.get_summary()
        callback_usage = summary.get("usage", {})

        total_input_tokens = callback_usage.get("input_tokens", 0)
        total_output_tokens = callback_usage.get("output_tokens", 0)
        total_requests = callback_usage.get("llm_calls", 0)

    # Build UsageMetrics
    if total_requests == 0:
        logger.bind(event="USAGE_EXTRACTOR|NO_USAGE_FOUND").debug(
            "No usage metadata found in state or callback handler"
        )
        return None

    total_tokens = total_input_tokens + total_output_tokens

    usage = UsageMetrics(
        requests=total_requests,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=None,  # Calculated separately via aggregate_costs_by_model
    )

    logger.bind(event="USAGE_EXTRACTOR|EXTRACTION_SUCCESS").debug(
        f"Extracted usage: {total_requests} requests, {total_tokens} total tokens"
    )

    return usage


def extract_usage_from_callback(
    callback_handler: UsageCallbackHandler,
) -> UsageMetrics | None:
    """
    Extract usage metrics directly from callback handler.

    Alternative to extract_usage_from_state when callback is the source of truth.

    Args:
        callback_handler: Handler with captured LLM usage events

    Returns:
        UsageMetrics or None
    """
    summary = callback_handler.get_summary()
    usage_data = summary.get("usage", {})

    if usage_data.get("total_tokens", 0) == 0:
        return None

    return UsageMetrics(
        requests=summary.get("llm_calls", 0),
        input_tokens=usage_data.get("input_tokens", 0),
        output_tokens=usage_data.get("output_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0),
        estimated_cost_usd=None,
    )


def extract_tool_invocations(
    state: VoxyState,
    callback_handler: UsageCallbackHandler | None = None,
) -> list[SubagentInfo]:
    """
    Extract tool invocations from LangGraph execution for hierarchical logging.

    Phase 4B: Builds SubagentInfo list from tool calls captured in:
    1. Callback handler (preferred - has inputs/outputs)
    2. State messages (fallback - ToolMessage objects)

    Args:
        state: VoxyState after graph execution
        callback_handler: Optional callback with tool invocation data

    Returns:
        List of SubagentInfo objects for log_usage_metrics()

    Example:
        >>> tools = extract_tool_invocations(result, handler)
        >>> for tool in tools:
        ...     print(f"{tool.name}: {tool.model}")
    """
    subagents: list[SubagentInfo] = []

    # Primary source: callback handler (has full data)
    if callback_handler and callback_handler.tool_invocations:
        for invocation in callback_handler.tool_invocations.values():
            subagent_info = _build_subagent_info_from_tool_invocation(invocation, state)
            if subagent_info:
                subagents.append(subagent_info)

        logger.bind(event="USAGE_EXTRACTOR|TOOLS_FROM_CALLBACK").debug(
            f"Extracted {len(subagents)} tool invocations from callback handler"
        )
        return subagents

    # Fallback: parse ToolMessage from state messages
    messages = state.get("messages", [])
    for message in messages:
        if isinstance(message, ToolMessage):
            subagent_info = _build_subagent_info_from_tool_message(message, state)
            if subagent_info:
                subagents.append(subagent_info)

    logger.bind(event="USAGE_EXTRACTOR|TOOLS_FROM_STATE").debug(
        f"Extracted {len(subagents)} tool invocations from state messages"
    )

    return subagents


def _build_subagent_info_from_tool_invocation(
    invocation: ToolInvocationData, state: VoxyState
) -> SubagentInfo | None:
    """
    Build SubagentInfo from ToolInvocationData captured by callback.

    Maps tool names to friendly agent names and extracts model configs.
    """
    # Map tool names to agent names
    tool_to_agent_map = {
        "translate_text": "Translator Agent",
        "correct_text": "Corrector Agent",
        "get_weather": "Weather Agent",
        "calculate": "Calculator Agent",
        "analyze_image": "Vision Agent",
    }

    agent_name = tool_to_agent_map.get(invocation.tool_name, invocation.tool_name)

    # Extract model from state context (if available)
    # In Phase 3, subagents use models from models_config.py
    # TODO: Extract actual model config from state context when available

    # Fallback to reading from environment/config
    # For now, use placeholder - will be enhanced in Phase 4D
    model = "configured_via_env"  # Will be replaced with actual model lookup
    config = {"max_tokens": "configured", "temperature": "configured"}

    # Preview inputs/outputs
    input_preview = _preview_data(invocation.inputs)
    output_preview = (
        _preview_data(invocation.outputs) if invocation.completed else "⏳ In progress"
    )

    return SubagentInfo(
        name=agent_name,
        model=model,
        config=config,
        input_preview=input_preview,
        output_preview=output_preview,
    )


def _build_subagent_info_from_tool_message(
    message: ToolMessage, state: VoxyState
) -> SubagentInfo | None:
    """
    Build SubagentInfo from ToolMessage in state (fallback when no callback).

    Less detailed than callback version but provides basic tracking.
    """
    tool_name = getattr(message, "name", "unknown_tool")

    # Map to agent name
    tool_to_agent_map = {
        "translate_text": "Translator Agent",
        "correct_text": "Corrector Agent",
        "get_weather": "Weather Agent",
        "calculate": "Calculator Agent",
        "analyze_image": "Vision Agent",
    }

    agent_name = tool_to_agent_map.get(tool_name, tool_name)

    return SubagentInfo(
        name=agent_name,
        model="configured_via_env",
        config={"source": "ToolMessage"},
        input_preview="<from ToolMessage>",
        output_preview=_preview_data(message.content),
    )


def _preview_data(data: Any, max_length: int = 100) -> str:
    """
    Create preview string from data (dict, str, etc.).

    Args:
        data: Input or output data
        max_length: Maximum preview length

    Returns:
        Truncated string representation
    """
    if data is None:
        return "<None>"

    if isinstance(data, dict):
        # Show first key-value pair
        if data:
            key, value = next(iter(data.items()))
            preview = f"{key}: {value}"
        else:
            preview = "{}"
    else:
        preview = str(data)

    # Truncate if too long
    if len(preview) > max_length:
        preview = preview[:max_length] + "..."

    return preview


def aggregate_costs_by_model(
    state: VoxyState,
    callback_handler: UsageCallbackHandler | None = None,
) -> float | None:
    """
    Calculate total cost across multiple models used in LangGraph execution.

    Phase 4D: Iterates through AIMessages, extracts model and usage metadata,
    calculates cost per model using LiteLLM, and sums total.

    Args:
        state: VoxyState after execution
        callback_handler: Optional callback for additional metadata

    Returns:
        Total estimated cost in USD, or None if calculation fails

    Example:
        >>> total_cost = aggregate_costs_by_model(result)
        >>> print(f"Total: ${total_cost:.6f}")
    """
    if not LITELLM_AVAILABLE:
        logger.bind(event="USAGE_EXTRACTOR|LITELLM_UNAVAILABLE").warning(
            "LiteLLM not available, cannot calculate costs"
        )
        return None

    messages = state.get("messages", [])
    total_cost = 0.0
    models_used: dict[str, dict[str, int]] = (
        {}
    )  # model -> {input_tokens, output_tokens}

    for message in messages:
        if isinstance(message, AIMessage) and hasattr(message, "usage_metadata"):
            metadata = message.usage_metadata
            if not metadata:
                continue

            # Extract model name
            # LangGraph may store model in response_metadata or message attributes
            model_name = None
            if hasattr(message, "response_metadata"):
                model_name = message.response_metadata.get("model_name")

            # Fallback: try to get from additional_kwargs or context
            if not model_name and hasattr(message, "additional_kwargs"):
                model_name = message.additional_kwargs.get("model")

            # If still no model, skip cost calculation for this message
            if not model_name:
                logger.bind(event="USAGE_EXTRACTOR|NO_MODEL_NAME").debug(
                    "AIMessage has usage but no model name, skipping cost"
                )
                continue

            # Aggregate usage per model
            if model_name not in models_used:
                models_used[model_name] = {"input_tokens": 0, "output_tokens": 0}

            models_used[model_name]["input_tokens"] += metadata.get("input_tokens", 0)
            models_used[model_name]["output_tokens"] += metadata.get("output_tokens", 0)

    # Calculate cost per model
    for model_name, usage in models_used.items():
        try:
            input_cost, output_cost = cost_per_token(
                model=model_name,
                prompt_tokens=usage["input_tokens"],
                completion_tokens=usage["output_tokens"],
            )
            model_cost = (input_cost or 0.0) + (output_cost or 0.0)
            total_cost += model_cost

            logger.bind(event="USAGE_EXTRACTOR|MODEL_COST").debug(
                f"Model: {model_name} | "
                f"Tokens: {usage['input_tokens']} in + {usage['output_tokens']} out | "
                f"Cost: ${model_cost:.6f}"
            )
        except Exception as e:
            logger.bind(event="USAGE_EXTRACTOR|COST_CALC_ERROR").warning(
                f"Failed to calculate cost for model {model_name}: {e}"
            )

    if total_cost == 0.0:
        return None

    logger.bind(event="USAGE_EXTRACTOR|TOTAL_COST").info(
        f"Total estimated cost: ${total_cost:.6f} across {len(models_used)} models"
    )

    return total_cost


def enrich_usage_with_cost(usage: UsageMetrics, model_path: str) -> UsageMetrics:
    """
    Add cost estimation to UsageMetrics using single model.

    Fallback for when aggregate_costs_by_model cannot determine per-message models.

    Args:
        usage: UsageMetrics without cost
        model_path: LiteLLM model path (e.g., "openrouter/anthropic/claude-sonnet-4.5")

    Returns:
        UsageMetrics with estimated_cost_usd filled
    """
    if not LITELLM_AVAILABLE or usage.estimated_cost_usd is not None:
        return usage

    try:
        input_cost, output_cost = cost_per_token(
            model=model_path,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
        )
        total_cost = (input_cost or 0.0) + (output_cost or 0.0)

        usage.estimated_cost_usd = total_cost

        logger.bind(event="USAGE_EXTRACTOR|COST_ENRICHMENT").debug(
            f"Added cost estimate: ${total_cost:.6f} for model {model_path}"
        )
    except Exception as e:
        logger.bind(event="USAGE_EXTRACTOR|COST_ENRICHMENT_ERROR").warning(
            f"Failed to enrich usage with cost: {e}"
        )

    return usage
