"""
LangGraph Usage Callback Handler

Captures LLM usage events and tool invocations from LangGraph execution
for integration with the existing usage_tracker.py infrastructure.

Architecture:
- Inherits from BaseCallbackHandler (LangChain)
- Captures on_chat_model_end, on_tool_start, on_tool_end events
- Stores usage metadata and tool invocation data
- Provides data for usage_extractor.py to build UsageMetrics

Phase 4A: Token tracking via on_chat_model_end
Phase 4B: Tool tracking via on_tool_start/end
"""

from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from loguru import logger


class ToolInvocationData:
    """
    Stores data about a single tool invocation captured during LangGraph execution.

    Matches the structure needed to build SubagentInfo for hierarchical logging.
    """

    def __init__(
        self,
        tool_name: str,
        run_id: str,
        inputs: dict[str, Any] | None = None,
        outputs: Any | None = None,
    ):
        self.tool_name = tool_name
        self.run_id = run_id
        self.inputs = inputs or {}
        self.outputs = outputs
        self.completed = False

    def __repr__(self) -> str:
        status = "✓" if self.completed else "⏳"
        return f"<ToolInvocation {status} {self.tool_name} [{self.run_id[:8]}]>"


class UsageCallbackHandler(BaseCallbackHandler):
    """
    Callback handler for capturing token usage and tool invocations from LangGraph.

    Designed to integrate with existing usage_tracker.py infrastructure while
    adapting to LangGraph's event-based architecture.

    Attributes:
        llm_usage_events: List of LLMResult objects with usage metadata
        tool_invocations: List of ToolInvocationData objects
        total_llm_calls: Counter for LLM invocations
        total_tool_calls: Counter for tool invocations

    Usage:
        handler = UsageCallbackHandler()
        config = {"callbacks": [handler]}
        result = graph.invoke(state, config=config)

        # After invocation, extract data
        usage = extract_usage_from_callback(handler)
        tools = extract_tool_invocations_from_callback(handler)
    """

    def __init__(self) -> None:
        super().__init__()
        # Phase 4A: Token usage tracking
        self.llm_usage_events: list[LLMResult] = []
        self.total_llm_calls: int = 0

        # Phase 4B: Tool invocation tracking
        self.tool_invocations: dict[str, ToolInvocationData] = {}
        self.total_tool_calls: int = 0

        logger.bind(event="USAGE_CALLBACK|INIT").debug(
            "UsageCallbackHandler initialized for LangGraph observability"
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts running."""
        self.total_llm_calls += 1
        logger.bind(event="USAGE_CALLBACK|LLM_START").debug(
            f"LLM call started [run_id={run_id}] (total={self.total_llm_calls})"
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when LLM ends running.

        Phase 4A: Captures token usage from LLMResult.

        LLMResult structure:
        - generations: list of chat generations
        - llm_output: dict with usage metadata
        - llm_output["token_usage"]: dict with input_tokens, output_tokens, total_tokens
        """
        # Store complete LLMResult for later extraction
        self.llm_usage_events.append(response)

        # Extract usage for immediate logging
        usage = self._extract_usage_from_llm_result(response)
        if usage:
            logger.bind(event="USAGE_CALLBACK|LLM_END").debug(
                f"LLM call completed [run_id={run_id}] | "
                f"Tokens: {usage.get('input_tokens', 0)} in + "
                f"{usage.get('output_tokens', 0)} out = "
                f"{usage.get('total_tokens', 0)} total"
            )
        else:
            logger.bind(event="USAGE_CALLBACK|LLM_END_NO_USAGE").debug(
                f"LLM call completed [run_id={run_id}] but no usage metadata found"
            )

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when chat model starts."""
        self.total_llm_calls += 1
        logger.bind(event="USAGE_CALLBACK|CHAT_MODEL_START").debug(
            f"Chat model call started [run_id={run_id}] (total={self.total_llm_calls})"
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when a tool starts executing.

        Phase 4B: Tracks tool invocations for hierarchical logging.

        Args:
            serialized: Tool configuration (contains 'name' key)
            input_str: String representation of inputs
            run_id: Unique ID for this tool run
            inputs: Structured input dict (preferred over input_str)
        """
        tool_name = serialized.get("name", "unknown_tool")
        run_id_str = str(run_id)

        # Create tool invocation record
        invocation = ToolInvocationData(
            tool_name=tool_name,
            run_id=run_id_str,
            inputs=inputs or {"input_str": input_str},
        )
        self.tool_invocations[run_id_str] = invocation
        self.total_tool_calls += 1

        logger.bind(event="USAGE_CALLBACK|TOOL_START").debug(
            f"Tool started: {tool_name} [run_id={run_id_str[:8]}...] "
            f"(total={self.total_tool_calls})"
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when a tool finishes executing.

        Phase 4B: Marks tool as completed and stores output.

        Args:
            output: Tool execution result
            run_id: Matches the run_id from on_tool_start
        """
        run_id_str = str(run_id)

        if run_id_str in self.tool_invocations:
            invocation = self.tool_invocations[run_id_str]
            invocation.outputs = output
            invocation.completed = True

            logger.bind(event="USAGE_CALLBACK|TOOL_END").debug(
                f"Tool completed: {invocation.tool_name} [run_id={run_id_str[:8]}...] ✓"
            )
        else:
            logger.bind(event="USAGE_CALLBACK|TOOL_END_ORPHAN").warning(
                f"Tool end event without matching start [run_id={run_id_str[:8]}...]"
            )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool encounters an error."""
        run_id_str = str(run_id)

        if run_id_str in self.tool_invocations:
            invocation = self.tool_invocations[run_id_str]
            invocation.outputs = f"ERROR: {error}"
            invocation.completed = False

            logger.bind(event="USAGE_CALLBACK|TOOL_ERROR").warning(
                f"Tool error: {invocation.tool_name} [run_id={run_id_str[:8]}...] | "
                f"Error: {error}"
            )

    def _extract_usage_from_llm_result(
        self, result: LLMResult
    ) -> dict[str, int] | None:
        """
        Extract token usage from LLMResult.

        LangChain/LangGraph models return usage in different formats:
        1. result.llm_output["token_usage"] (OpenAI, Anthropic via LangChain)
        2. result.llm_output["usage"] (some providers)
        3. generations[0].message.usage_metadata (LangChain core messages)

        Returns dict with keys: input_tokens, output_tokens, total_tokens
        """
        # Try llm_output first
        if result.llm_output:
            # Format 1: token_usage key
            if "token_usage" in result.llm_output:
                usage = result.llm_output["token_usage"]
                return {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }

            # Format 2: usage key (direct)
            if "usage" in result.llm_output:
                usage = result.llm_output["usage"]
                return {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }

        # Try generations (message-level usage_metadata)
        if result.generations:
            for generation_list in result.generations:
                for generation in generation_list:
                    if hasattr(generation, "message") and hasattr(
                        generation.message, "usage_metadata"
                    ):
                        metadata = generation.message.usage_metadata
                        if metadata:
                            return {
                                "input_tokens": metadata.get("input_tokens", 0),
                                "output_tokens": metadata.get("output_tokens", 0),
                                "total_tokens": metadata.get("total_tokens", 0),
                            }

        return None

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary of captured telemetry.

        Returns:
            dict with counts and aggregated metrics
        """
        total_input = 0
        total_output = 0
        total_tokens = 0

        for result in self.llm_usage_events:
            usage = self._extract_usage_from_llm_result(result)
            if usage:
                total_input += usage.get("input_tokens", 0)
                total_output += usage.get("output_tokens", 0)
                total_tokens += usage.get("total_tokens", 0)

        return {
            "llm_calls": self.total_llm_calls,
            "tool_calls": self.total_tool_calls,
            "usage": {
                "input_tokens": total_input,
                "output_tokens": total_output,
                "total_tokens": total_tokens,
            },
            "tools_completed": sum(
                1 for inv in self.tool_invocations.values() if inv.completed
            ),
            "tools_failed": sum(
                1 for inv in self.tool_invocations.values() if not inv.completed
            ),
        }

    def reset(self) -> None:
        """Reset handler state (useful for reusing handler across multiple runs)."""
        self.llm_usage_events.clear()
        self.tool_invocations.clear()
        self.total_llm_calls = 0
        self.total_tool_calls = 0
        logger.bind(event="USAGE_CALLBACK|RESET").debug("UsageCallbackHandler reset")
