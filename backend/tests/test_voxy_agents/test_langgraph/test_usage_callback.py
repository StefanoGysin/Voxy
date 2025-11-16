"""
Unit tests for LangGraph Usage Callback Handler (Phase 4A).

Tests the callback handler's ability to capture LLM usage events and tool invocations.
"""

from uuid import uuid4

from langchain_core.outputs import LLMResult

from voxy_agents.langgraph.usage_callback import (
    ToolInvocationData,
    UsageCallbackHandler,
)


class TestUsageCallbackHandler:
    """Test suite for UsageCallbackHandler."""

    def test_initialization(self):
        """Test handler initializes with empty state."""
        handler = UsageCallbackHandler()

        assert handler.total_llm_calls == 0
        assert handler.total_tool_calls == 0
        assert len(handler.llm_usage_events) == 0
        assert len(handler.tool_invocations) == 0

    def test_on_llm_start_increments_counter(self):
        """Test on_llm_start increments LLM call counter."""
        handler = UsageCallbackHandler()

        handler.on_llm_start(
            serialized={"name": "test_model"},
            prompts=["test prompt"],
            run_id=uuid4(),
        )

        assert handler.total_llm_calls == 1

    def test_on_llm_end_captures_usage(self):
        """Test on_llm_end captures usage from LLMResult."""
        handler = UsageCallbackHandler()

        # Create mock LLMResult with usage metadata
        llm_result = LLMResult(
            generations=[],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                }
            },
        )

        handler.on_llm_end(response=llm_result, run_id=uuid4())

        assert len(handler.llm_usage_events) == 1
        assert handler.llm_usage_events[0] == llm_result

        # Extract usage from captured event
        usage = handler._extract_usage_from_llm_result(llm_result)
        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["total_tokens"] == 150

    def test_on_tool_start_creates_invocation_record(self):
        """Test on_tool_start creates tool invocation record."""
        handler = UsageCallbackHandler()

        run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "translate_text"},
            input_str="Hello",
            run_id=run_id,
            inputs={"text": "Hello", "target_language": "pt-BR"},
        )

        assert handler.total_tool_calls == 1
        assert str(run_id) in handler.tool_invocations

        invocation = handler.tool_invocations[str(run_id)]
        assert invocation.tool_name == "translate_text"
        assert invocation.inputs["text"] == "Hello"
        assert invocation.completed is False

    def test_on_tool_end_marks_invocation_complete(self):
        """Test on_tool_end marks tool invocation as completed."""
        handler = UsageCallbackHandler()

        run_id = uuid4()

        # Start tool
        handler.on_tool_start(
            serialized={"name": "calculate"},
            input_str="2 + 2",
            run_id=run_id,
        )

        # End tool
        handler.on_tool_end(output="4", run_id=run_id)

        invocation = handler.tool_invocations[str(run_id)]
        assert invocation.completed is True
        assert invocation.outputs == "4"

    def test_on_tool_error_handles_errors(self):
        """Test on_tool_error captures error information."""
        handler = UsageCallbackHandler()

        run_id = uuid4()

        # Start tool
        handler.on_tool_start(
            serialized={"name": "get_weather"},
            input_str="Tokyo",
            run_id=run_id,
        )

        # Tool error
        error = ValueError("API key invalid")
        handler.on_tool_error(error=error, run_id=run_id)

        invocation = handler.tool_invocations[str(run_id)]
        assert invocation.completed is False
        assert "ERROR" in invocation.outputs
        assert "API key invalid" in invocation.outputs

    def test_get_summary_aggregates_metrics(self):
        """Test get_summary returns aggregated telemetry."""
        handler = UsageCallbackHandler()

        # Simulate 2 LLM calls
        handler.on_llm_start(serialized={}, prompts=[], run_id=uuid4())
        handler.on_llm_start(serialized={}, prompts=[], run_id=uuid4())

        llm_result_1 = LLMResult(
            generations=[],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                }
            },
        )
        llm_result_2 = LLMResult(
            generations=[],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 100,
                    "total_tokens": 300,
                }
            },
        )

        handler.on_llm_end(response=llm_result_1, run_id=uuid4())
        handler.on_llm_end(response=llm_result_2, run_id=uuid4())

        # Simulate 1 tool call
        tool_run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "translate_text"}, input_str="", run_id=tool_run_id
        )
        handler.on_tool_end(output="Bonjour", run_id=tool_run_id)

        summary = handler.get_summary()

        assert summary["llm_calls"] == 2
        assert summary["tool_calls"] == 1
        assert summary["usage"]["input_tokens"] == 300  # 100 + 200
        assert summary["usage"]["output_tokens"] == 150  # 50 + 100
        assert summary["usage"]["total_tokens"] == 450  # 150 + 300
        assert summary["tools_completed"] == 1
        assert summary["tools_failed"] == 0

    def test_reset_clears_handler_state(self):
        """Test reset clears all handler state."""
        handler = UsageCallbackHandler()

        # Add some data
        handler.on_llm_start(serialized={}, prompts=[], run_id=uuid4())
        handler.on_tool_start(serialized={"name": "test"}, input_str="", run_id=uuid4())

        assert handler.total_llm_calls > 0
        assert handler.total_tool_calls > 0

        # Reset
        handler.reset()

        assert handler.total_llm_calls == 0
        assert handler.total_tool_calls == 0
        assert len(handler.llm_usage_events) == 0
        assert len(handler.tool_invocations) == 0


class TestToolInvocationData:
    """Test suite for ToolInvocationData."""

    def test_initialization(self):
        """Test ToolInvocationData initializes correctly."""
        invocation = ToolInvocationData(
            tool_name="translate_text",
            run_id="abc123",
            inputs={"text": "Hello"},
            outputs="Bonjour",
        )

        assert invocation.tool_name == "translate_text"
        assert invocation.run_id == "abc123"
        assert invocation.inputs["text"] == "Hello"
        assert invocation.outputs == "Bonjour"
        assert invocation.completed is False  # Not marked complete until explicit

    def test_repr_format(self):
        """Test __repr__ shows useful debugging info."""
        invocation = ToolInvocationData(
            tool_name="calculate", run_id="test-run-id-12345678", inputs={}
        )

        repr_str = repr(invocation)
        assert "ToolInvocation" in repr_str
        assert "calculate" in repr_str
        assert "test-run" in repr_str  # First 8 chars of run_id
        assert "⏳" in repr_str  # In progress emoji

        # Mark as completed
        invocation.completed = True
        repr_str = repr(invocation)
        assert "✓" in repr_str  # Completed emoji
