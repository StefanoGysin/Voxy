"""
LangGraph Graph Builder - Supervisor Pattern

Assembles the complete VOXY LangGraph orchestration graph with:
- Entry router (PATH1 vs PATH2 decision)
- Vision bypass stub (Phase 2) or full implementation (Phase 3+)
- Supervisor node (stub in Phase 2, full ReAct agent in Phase 3+)
- Subagent nodes (Translator in Phase 2, all 5 in Phase 3+)

Architecture:
                     ┌──────────────┐
                     │    START     │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │entry_router  │
                     └──────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
    ┌─────────▼─────────┐       ┌────────▼────────┐
    │ vision_bypass     │       │   supervisor    │
    │ (PATH1 - direct)  │       │ (PATH2 - decide)│
    └─────────┬─────────┘       └────────┬────────┘
              │                           │
              │                  ┌────────▼────────┐
              │                  │  translator     │
              │                  │  (tool call)    │
              │                  └────────┬────────┘
              │                           │
              └───────────┬───────────────┘
                          │
                   ┌──────▼───────┐
                   │     END      │
                   └──────────────┘

Reference: LangGraph Supervisor Multi-Agent Pattern
https://langchain-ai.github.io/langgraph/concepts/multi_agent/
"""

from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from loguru import logger

from .checkpointer import CheckpointerType, create_checkpointer
from .graph_state import VoxyState
from .nodes.entry_router import entry_router
from .nodes.translator_node import create_translator_node
from .nodes.vision_bypass import vision_bypass_node


def _create_supervisor_stub_node():
    """
    Create stub supervisor node for Phase 2.

    Phase 3 will replace this with create_react_agent() with full tools.
    For now, returns a simple response acknowledging the request.

    Returns:
        Supervisor node function
    """

    def supervisor_stub_node(state: VoxyState) -> dict[str, Any]:
        """
        Supervisor stub node (Phase 2).

        In Phase 3, this will be replaced by:
        - create_react_agent(model, tools=[translator_tool, ...])
        - Full ReAct loop with tool calling
        - Multi-agent orchestration

        Args:
            state: Current VoxyState

        Returns:
            State update with stub response
        """
        messages = state["messages"]

        logger.bind(event="LANGGRAPH|SUPERVISOR_STUB").info(
            "Supervisor stub executing (Phase 2)",
            message_count=len(messages),
        )

        # STUB: Phase 2 - Simple acknowledgment
        stub_response = AIMessage(
            content="[Phase 2 Stub] VOXY Supervisor received your request. "
            "In Phase 3, I will orchestrate the appropriate subagent (translator, calculator, etc.)."
        )

        logger.bind(event="LANGGRAPH|SUPERVISOR_STUB").info("Supervisor stub completed")

        return {"messages": [stub_response]}

    return supervisor_stub_node


class SupervisorGraphBuilder:
    """
    Builder class for assembling VOXY LangGraph orchestration graph.

    Supports incremental migration phases:
    - Phase 2: Entry router + vision bypass stub + translator + supervisor stub
    - Phase 3: Full supervisor (ReAct agent) + all 5 subagents + vision agent
    - Phase 4+: Advanced features (streaming, memory, etc.)

    Example:
        >>> builder = SupervisorGraphBuilder()
        >>> builder.add_entry_router()
        >>> builder.add_vision_bypass_stub()
        >>> builder.add_translator_node()
        >>> builder.add_supervisor_stub()
        >>> graph = builder.compile(checkpointer_type=CheckpointerType.MEMORY)
        >>> result = graph.invoke(state, config=config)
    """

    def __init__(self):
        """Initialize graph builder with VoxyState schema."""
        self.builder = StateGraph(VoxyState)
        self._nodes_added = set()
        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "SupervisorGraphBuilder initialized"
        )

    def add_entry_router(self) -> "SupervisorGraphBuilder":
        """
        Add entry router node with conditional routing (PATH1 vs PATH2).

        Routing logic:
        - PATH1 (vision_bypass): image_url present + vision keywords detected
        - PATH2 (supervisor): All other cases

        Returns:
            Self for method chaining
        """
        self.builder.add_node("entry_router_node", lambda state: state)

        # Conditional edge: entry_router decides next node
        self.builder.add_conditional_edges(
            "entry_router_node",
            entry_router,  # Returns "vision_bypass" | "supervisor"
            {
                "vision_bypass": "vision_bypass",
                "supervisor": "supervisor",
            },
        )

        self._nodes_added.add("entry_router")

        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "Entry router added with conditional edges"
        )

        return self

    def add_vision_bypass_stub(self) -> "SupervisorGraphBuilder":
        """
        Add vision bypass stub node (Phase 2 implementation).

        Phase 3 will integrate actual VisionAgent.analyze_image().

        Returns:
            Self for method chaining
        """
        self.builder.add_node("vision_bypass", vision_bypass_node)
        self.builder.add_edge("vision_bypass", END)

        self._nodes_added.add("vision_bypass")

        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "Vision bypass stub added (Phase 2)"
        )

        return self

    def add_translator_node(self) -> "SupervisorGraphBuilder":
        """
        Add translator node from Phase 1 implementation.

        Uses create_translator_node() factory with LiteLLM integration.

        Returns:
            Self for method chaining
        """
        translator_node = create_translator_node()
        self.builder.add_node("translator", translator_node)
        self.builder.add_edge("translator", END)

        self._nodes_added.add("translator")

        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "Translator node added (from Phase 1)"
        )

        return self

    def add_supervisor_stub(self) -> "SupervisorGraphBuilder":
        """
        Add supervisor stub node (Phase 2 implementation).

        Phase 3 will replace with create_react_agent() with full tools list.

        Returns:
            Self for method chaining
        """
        supervisor_stub = _create_supervisor_stub_node()
        self.builder.add_node("supervisor", supervisor_stub)

        # For Phase 2 stub, supervisor goes directly to END
        # Phase 3 will route to subagents via tool calls
        self.builder.add_edge("supervisor", END)

        self._nodes_added.add("supervisor")

        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "Supervisor stub added (Phase 2)"
        )

        return self

    def compile(
        self,
        checkpointer_type: CheckpointerType | str = CheckpointerType.MEMORY,
        db_path: str | None = None,
    ):
        """
        Compile the graph with checkpointer for state persistence.

        Args:
            checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
            db_path: Database path for persistent checkpointers (optional)

        Returns:
            Compiled CompiledGraph ready for invocation

        Example:
            >>> graph = builder.compile(CheckpointerType.SQLITE, "voxy_graph.db")
            >>> result = graph.invoke(state, config={"configurable": {"thread_id": "123"}})
        """
        # Add START edge to entry_router
        self.builder.add_edge(START, "entry_router_node")

        # Create checkpointer
        checkpointer = create_checkpointer(checkpointer_type, db_path)

        # Compile graph
        compiled_graph = self.builder.compile(checkpointer=checkpointer)

        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "Graph compiled successfully",
            checkpointer_type=checkpointer_type,
            nodes_count=len(self._nodes_added),
            nodes=sorted(self._nodes_added),
        )

        return compiled_graph


def create_phase2_graph(
    checkpointer_type: CheckpointerType | str = CheckpointerType.MEMORY,
    db_path: str | None = None,
):
    """
    Factory function to create Phase 2 complete graph.

    Assembles:
    - Entry router (PATH1/PATH2 decision)
    - Vision bypass stub (PATH1 direct execution)
    - Supervisor stub (PATH2 acknowledgment)
    - Translator node (from Phase 1)

    Args:
        checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
        db_path: Database path for persistent checkpointers (optional)

    Returns:
        Compiled graph ready for invocation

    Example:
        >>> graph = create_phase2_graph(CheckpointerType.MEMORY)
        >>> state = create_initial_state(
        ...     messages=[{"role": "user", "content": "Translate 'Hello' to French"}],
        ...     thread_id="session-123"
        ... )
        >>> config = get_checkpoint_config(thread_id="session-123")
        >>> result = graph.invoke(state, config=config)
    """
    builder = SupervisorGraphBuilder()

    builder.add_entry_router()
    builder.add_vision_bypass_stub()
    builder.add_translator_node()
    builder.add_supervisor_stub()

    graph = builder.compile(checkpointer_type, db_path)

    logger.bind(event="LANGGRAPH|GRAPH_FACTORY").info(
        "Phase 2 graph created",
        checkpointer_type=checkpointer_type,
    )

    return graph
