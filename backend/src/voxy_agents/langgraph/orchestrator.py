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

from voxy_agents.utils.usage_tracker import log_usage_metrics

from .checkpointer import CheckpointerType, get_checkpoint_config
from .graph_builder import create_phase2_graph
from .graph_state import VoxyState, create_initial_state
from .usage_callback import UsageCallbackHandler
from .usage_extractor import (
    aggregate_costs_by_model,
    extract_tool_invocations,
    extract_usage_from_state,
)


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

        Phase 4A: Now includes token usage tracking and cost estimation.
        Phase 4E: Loads existing checkpoint to enable conversation history.

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
                - usage: Token usage metrics (Phase 4A)

        Example:
            >>> response = await orchestrator.process_message(
            ...     message="What is in this image?",
            ...     session_id="session-123",
            ...     image_url="https://example.com/img.jpg"
            ... )
            >>> response["route_taken"]
            'vision_bypass'
            >>> response["usage"]["total_tokens"]
            450
        """
        # Generate trace ID for observability (Phase 4A)
        trace_id = str(uuid4())[:8]

        # Generate thread_id from session_id or create new UUID
        thread_id = session_id or f"thread-{uuid4()}"

        # Phase 4E: Load existing checkpoint or create new state
        # This enables conversation history by preserving messages across invocations
        config = get_checkpoint_config(thread_id=thread_id)

        try:
            # Try to load existing checkpoint for this thread
            # get_state() returns a StateSnapshot with .values containing the state
            snapshot = self.graph.get_state(config)

            if snapshot and snapshot.values and snapshot.values.get("messages"):
                # Checkpoint exists - append new message to history
                logger.bind(
                    event="LANGGRAPH|ORCHESTRATOR_CHECKPOINT_LOADED", trace_id=trace_id
                ).info(
                    "Loading existing checkpoint",
                    thread_id=thread_id,
                    existing_messages=len(snapshot.values["messages"]),
                )

                # Use existing state and append new message
                state = dict(snapshot.values)  # Create mutable copy
                state["messages"].append(HumanMessage(content=message))  # type: ignore[arg-type]

                # Update context with new data if provided
                initial_context = context or {}
                if image_url:
                    initial_context["image_url"] = image_url
                if initial_context:
                    state["context"].update(initial_context)
            else:
                # No checkpoint - create initial state (first message in conversation)
                logger.bind(
                    event="LANGGRAPH|ORCHESTRATOR_NEW_CONVERSATION", trace_id=trace_id
                ).info(
                    "Creating new conversation",
                    thread_id=thread_id,
                )

                initial_context = context or {}
                if image_url:
                    initial_context["image_url"] = image_url

                initial_state = create_initial_state(
                    messages=[HumanMessage(content=message)],  # type: ignore[arg-type]
                    thread_id=thread_id,
                    session_id=session_id,
                    user_id=user_id,
                )

                # Convert to mutable dict for consistency
                state = dict(initial_state)
                # Merge context
                state["context"].update(initial_context)
        except Exception as e:
            # Fallback to creating new state if checkpoint loading fails
            logger.bind(
                event="LANGGRAPH|ORCHESTRATOR_CHECKPOINT_ERROR", trace_id=trace_id
            ).warning(
                f"Failed to load checkpoint, creating new state: {e}",
                thread_id=thread_id,
            )

            initial_context = context or {}
            if image_url:
                initial_context["image_url"] = image_url

            initial_state = create_initial_state(
                messages=[HumanMessage(content=message)],  # type: ignore[arg-type]
                thread_id=thread_id,
                session_id=session_id,
                user_id=user_id,
            )

            # Convert to mutable dict for consistency
            state = dict(initial_state)
            # Merge context
            state["context"].update(initial_context)

        # Phase 4A: Create usage callback handler
        usage_handler = UsageCallbackHandler()

        # Add callbacks and metadata to existing config
        config["callbacks"] = [usage_handler]
        config["metadata"] = {"trace_id": trace_id}

        logger.bind(event="LANGGRAPH|ORCHESTRATOR_INVOKE", trace_id=trace_id).info(
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

        # Phase 4A: Extract usage metrics
        usage = extract_usage_from_state(result, usage_handler)

        # Phase 4B: Extract tool invocations for hierarchical logging
        subagents = extract_tool_invocations(result, usage_handler)

        # Phase 4D: Calculate multi-model cost
        total_cost = aggregate_costs_by_model(result, usage_handler)
        if usage and total_cost is not None:
            usage.estimated_cost_usd = total_cost

        # Phase 4A: Log usage metrics (maintains SDK parity)
        if usage:
            # Determine path for logging (PATH_1 or PATH_2)
            path = "PATH_1" if vision_analysis else "PATH_2"

            # Log usage with hierarchical subagent details
            log_usage_metrics(
                trace_id=trace_id,
                path=path,
                voxy_usage=usage,
                vision_usage=None,  # Vision usage would be tracked separately in PATH_1
                subagents_called=subagents,
            )

            logger.bind(event="LANGGRAPH|USAGE_TRACKED", trace_id=trace_id).info(
                f"Usage tracked: {usage.total_tokens} tokens, "
                f"${usage.estimated_cost_usd:.6f} cost, "
                f"{len(subagents)} subagents"
                if usage.estimated_cost_usd
                else f"Usage tracked: {usage.total_tokens} tokens, {len(subagents)} subagents"
            )

        logger.bind(event="LANGGRAPH|ORCHESTRATOR_COMPLETE", trace_id=trace_id).info(
            "Message processed successfully",
            thread_id=thread_id,
            route_taken=route_taken,
            has_vision_analysis=bool(vision_analysis),
            response_length=len(response_content),
            total_tokens=usage.total_tokens if usage else 0,
        )

        return {
            "content": response_content,
            "session_id": session_id,
            "thread_id": thread_id,
            "route_taken": route_taken,
            "vision_analysis": vision_analysis,
            "usage": usage,  # Phase 4A: Include usage in response
            "trace_id": trace_id,  # Phase 4A: Include trace_id for debugging
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
