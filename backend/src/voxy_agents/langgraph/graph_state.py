"""
LangGraph State Management

Defines the shared state structure for VOXY LangGraph implementation.
Extends MessagesState with additional context channels for:
- Vision analysis results (PATH1/PATH2)
- Session metadata (Supabase session_id, thread_id)
- Tool invocation tracking
- Usage metrics

Reference: LangGraph MessagesState documentation
https://langchain-ai.github.io/langgraph/concepts/persistence/
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, BaseMessage
from langgraph.graph.message import add_messages


class VoxyState(TypedDict):
    """
    VOXY LangGraph state extending MessagesState.

    Channels:
        messages: Chat message history with automatic merging via add_messages reducer
        context: Additional context dict containing:
            - vision_analysis: Optional[dict] - Vision Agent bypass results (PATH1)
            - session_id: Optional[str] - Supabase session ID
            - thread_id: str - LangGraph thread ID (maps to session_id)
            - user_id: Optional[str] - Authenticated user ID
            - tool_invocations: list[dict] - Tool call tracking for observability
            - metadata: dict - Additional runtime metadata
        remaining_steps: Number of ReAct agent reasoning steps remaining (required by create_react_agent)

    Example:
        state = {
            "messages": [
                {"role": "user", "content": "Translate 'Hello' to French"}
            ],
            "context": {
                "thread_id": "session-123",
                "session_id": "uuid-456",
                "user_id": "user-789",
                "tool_invocations": [],
                "metadata": {}
            },
            "remaining_steps": 25
        }
    """

    # Messages channel with add_messages reducer (auto-merge)
    # Reference: https://langchain-ai.github.io/langgraph/concepts/low_level/#messagesstate
    messages: Annotated[list[AnyMessage], add_messages]

    # Context channel for additional state (replaced on update, not merged)
    context: dict[str, Any]

    # Remaining steps for ReAct agent (required by create_react_agent)
    # Default is 25 steps, can be overridden in config
    remaining_steps: int


def create_initial_state(
    messages: list[dict[str, str]] | list[BaseMessage] | None = None,
    thread_id: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
    remaining_steps: int = 25,
) -> VoxyState:
    """
    Create initial VoxyState with default context.

    Args:
        messages: Initial message history (default: empty)
        thread_id: LangGraph thread ID (required for checkpointing)
        session_id: Supabase session ID (optional)
        user_id: Authenticated user ID (optional)
        remaining_steps: Max ReAct agent reasoning steps (default: 25)

    Returns:
        VoxyState with initialized context

    Example:
        >>> state = create_initial_state(
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     thread_id="thread-123",
        ...     session_id="session-456"
        ... )
        >>> state["context"]["thread_id"]
        'thread-123'
        >>> state["remaining_steps"]
        25
    """
    return {
        "messages": messages or [],  # type: ignore[typeddict-item]
        "context": {
            "thread_id": thread_id,
            "session_id": session_id,
            "user_id": user_id,
            "vision_analysis": None,
            "tool_invocations": [],
            "metadata": {},
        },
        "remaining_steps": remaining_steps,
    }


def update_context(state: VoxyState, **updates: Any) -> dict[str, Any]:
    """
    Helper to update context dict while preserving existing keys.

    Args:
        state: Current VoxyState
        **updates: Key-value pairs to update in context

    Returns:
        Update dict for LangGraph node return

    Example:
        >>> def vision_node(state: VoxyState):
        ...     analysis = {"detected": "emoji"}
        ...     return update_context(state, vision_analysis=analysis)
    """
    updated_context = {**state["context"], **updates}
    return {"context": updated_context}
