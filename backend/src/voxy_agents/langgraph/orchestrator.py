"""
LangGraph Orchestrator Service

Service layer wrapping LangGraph implementation with interface compatible
with the existing OpenAI Agents SDK VoxyOrchestrator.

Provides:
- Session management via thread_id (maps to SDK session_id)
- Message invocation through compiled LangGraph graph
- Response extraction and formatting
- Checkpointer state persistence
- Feature parity with SDK orchestrator

Architecture:
    FastAPI Route → LangGraphOrchestrator → Compiled Graph → Nodes → Response

Phase 2 Usage:
    - Entry router decides PATH1 (vision) vs PATH2 (supervisor)
    - Translator node available via supervisor (stub)
    - Vision bypass stub for PATH1

Phase 3+ Usage:
    - Full ReAct supervisor with 5 subagent tools
    - Vision agent integrated
    - Streaming support
    - Advanced memory

Reference: backend/src/voxy_agents/core/voxy_orchestrator.py (SDK version)
"""

from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from .checkpointer import CheckpointerType, get_checkpoint_config
from .graph_builder import create_phase2_graph
from .graph_state import VoxyState, create_initial_state


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator service for VOXY multi-agent system.

    Maintains feature parity with SDK VoxyOrchestrator while using LangGraph
    for orchestration instead of OpenAI Agents SDK.

    Attributes:
        graph: Compiled LangGraph graph with checkpointer
        checkpointer_type: Type of checkpointer being used
        db_path: Database path for persistent checkpointers

    Example:
        >>> orchestrator = LangGraphOrchestrator(
        ...     checkpointer_type=CheckpointerType.SQLITE,
        ...     db_path="voxy_graph.db"
        ... )
        >>> response = await orchestrator.process_message(
        ...     message="Translate 'Hello' to French",
        ...     session_id="session-123",
        ...     user_id="user-456"
        ... )
        >>> print(response["content"])
        'Bonjour'
    """

    def __init__(
        self,
        checkpointer_type: CheckpointerType | str = CheckpointerType.MEMORY,
        db_path: str | None = None,
    ):
        """
        Initialize LangGraph orchestrator.

        Args:
            checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
            db_path: Database path for persistent checkpointers (optional)
        """
        self.checkpointer_type = checkpointer_type
        self.db_path = db_path

        # Create Phase 2 graph (entry router + vision stub + translator + supervisor stub)
        self.graph = create_phase2_graph(
            checkpointer_type=checkpointer_type,
            db_path=db_path,
        )

        logger.bind(event="LANGGRAPH|ORCHESTRATOR_INIT").info(
            "LangGraphOrchestrator initialized",
            checkpointer_type=checkpointer_type,
            db_path=db_path,
        )

    async def process_message(
        self,
        message: str,
        session_id: str | None = None,
        user_id: str | None = None,
        image_url: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Process user message through LangGraph orchestration.

        Args:
            message: User message text
            session_id: Supabase session ID (maps to thread_id)
            user_id: Authenticated user ID
            image_url: Optional image URL for vision analysis
            context: Additional context dict

        Returns:
            Response dict with:
                - content: AI response text
                - session_id: Session ID used
                - thread_id: LangGraph thread ID
                - route_taken: "vision_bypass" or "supervisor"
                - vision_analysis: Optional vision analysis result (PATH1)

        Example:
            >>> response = await orchestrator.process_message(
            ...     message="What is in this image?",
            ...     session_id="session-123",
            ...     image_url="https://example.com/img.jpg"
            ... )
            >>> response["route_taken"]
            'vision_bypass'
        """
        # Generate thread_id from session_id or create new UUID
        thread_id = session_id or f"thread-{uuid4()}"

        # Create initial state
        initial_context = context or {}
        if image_url:
            initial_context["image_url"] = image_url

        state = create_initial_state(
            messages=[HumanMessage(content=message)],  # type: ignore[arg-type]
            thread_id=thread_id,
            session_id=session_id,
            user_id=user_id,
        )

        # Merge context
        state["context"].update(initial_context)

        # Create checkpoint config
        config = get_checkpoint_config(thread_id=thread_id)

        logger.bind(event="LANGGRAPH|ORCHESTRATOR_INVOKE").info(
            "Processing message",
            thread_id=thread_id,
            session_id=session_id,
            has_image=bool(image_url),
            message_length=len(message),
        )

        # Invoke graph
        result: VoxyState = self.graph.invoke(state, config=config)

        # Extract response
        response_message = result["messages"][-1]
        response_content = (
            response_message.content
            if hasattr(response_message, "content")
            else str(response_message)
        )

        # Determine route taken (for debugging/monitoring)
        route_taken = self._determine_route_taken(result)

        # Extract vision analysis if present (PATH1)
        vision_analysis = result.get("context", {}).get("vision_analysis")

        logger.bind(event="LANGGRAPH|ORCHESTRATOR_COMPLETE").info(
            "Message processed successfully",
            thread_id=thread_id,
            route_taken=route_taken,
            has_vision_analysis=bool(vision_analysis),
            response_length=len(response_content),
        )

        return {
            "content": response_content,
            "session_id": session_id,
            "thread_id": thread_id,
            "route_taken": route_taken,
            "vision_analysis": vision_analysis,
        }

    def _determine_route_taken(self, result: VoxyState) -> str:
        """
        Determine which route was taken by examining response content.

        Heuristic based on stub response patterns (Phase 2).
        Phase 3+ can use graph execution metadata.

        Args:
            result: Final VoxyState after graph execution

        Returns:
            "vision_bypass" | "supervisor" | "unknown"
        """
        messages = result.get("messages", [])
        if not messages:
            return "unknown"

        last_message = messages[-1]
        content = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        # Heuristic detection based on stub response patterns
        if "Vision analysis would be performed" in content:
            return "vision_bypass"
        elif "VOXY Supervisor received your request" in content:
            return "supervisor"
        elif isinstance(last_message, AIMessage):
            # Actual subagent response (translator, etc.)
            return "supervisor"
        else:
            return "unknown"

    async def get_session_history(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve message history for a session from checkpointer.

        Args:
            session_id: Session ID to retrieve history for

        Returns:
            List of message dicts with role and content

        Note:
            Phase 2 stub implementation. Full implementation in Phase 3
            will query checkpointer state for the thread_id.
        """
        # STUB: Phase 2
        # Phase 3 will implement actual checkpointer state retrieval
        logger.bind(event="LANGGRAPH|ORCHESTRATOR_HISTORY").warning(
            "get_session_history stub (Phase 2)",
            session_id=session_id,
        )

        return []

    def get_graph_schema(self) -> dict[str, Any]:
        """
        Get compiled graph schema for debugging/visualization.

        Returns:
            Graph schema dict with nodes and edges

        Example:
            >>> schema = orchestrator.get_graph_schema()
            >>> print(schema["nodes"])
            ['entry_router_node', 'vision_bypass', 'supervisor', 'translator']
        """
        # LangGraph compiled graphs expose get_graph() for schema
        graph_schema = self.graph.get_graph()

        logger.bind(event="LANGGRAPH|ORCHESTRATOR_SCHEMA").debug(
            "Graph schema retrieved"
        )

        return {
            "nodes": list(graph_schema.nodes.keys()),
            "edges": [{"from": edge[0], "to": edge[1]} for edge in graph_schema.edges],
        }


# Global singleton instance (lazy initialization)
_orchestrator_instance: LangGraphOrchestrator | None = None


def get_langgraph_orchestrator(
    checkpointer_type: CheckpointerType | str = CheckpointerType.MEMORY,
    db_path: str | None = None,
) -> LangGraphOrchestrator:
    """
    Get global LangGraphOrchestrator instance (singleton pattern).

    Args:
        checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
        db_path: Database path for persistent checkpointers (optional)

    Returns:
        LangGraphOrchestrator instance

    Example:
        >>> orchestrator = get_langgraph_orchestrator(CheckpointerType.SQLITE)
        >>> response = await orchestrator.process_message(...)
    """
    global _orchestrator_instance

    if _orchestrator_instance is None:
        _orchestrator_instance = LangGraphOrchestrator(
            checkpointer_type=checkpointer_type,
            db_path=db_path,
        )

    return _orchestrator_instance
