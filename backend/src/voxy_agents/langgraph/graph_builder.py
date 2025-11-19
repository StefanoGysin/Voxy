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

from langchain_litellm import ChatLiteLLM
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from loguru import logger

from ..config.models_config import load_orchestrator_config
from .checkpointer import CheckpointerType, create_checkpointer
from .graph_state import VoxyState
from agents.calculator import create_calculator_tool
from agents.corrector import create_corrector_tool
from .nodes.entry_router import entry_router
from agents.translator import create_translator_node, create_translator_tool
from .nodes.vision_bypass import vision_bypass_node
from .nodes.vision_node import create_vision_tool
from agents.weather import create_weather_tool


def _get_supervisor_instructions() -> str:
    """Get specialized instructions for VOXY supervisor (same as SDK version)."""
    return """
    Você é o VOXY, assistente inteligente com capacidades multimodais e acesso a subagentes especializados.

    CAPACIDADES:
    - Análise e roteamento inteligente de solicitações
    - Coordenação de 5 subagentes especializados
    - Processamento multimodal (texto + imagens)
    - Execução de múltiplas tarefas quando necessário

    SUBAGENTES DISPONÍVEIS:
    - translate_text: Traduções entre idiomas (preserva contexto e significado)
    - correct_text: Correção ortográfica e gramatical (preserva significado)
    - calculate: Cálculos matemáticos com explicações passo a passo
    - get_weather: Informações meteorológicas em tempo real (OpenWeatherMap)
    - analyze_image: Análise multimodal de imagens (OCR, objetos, contexto)

    DIRETRIZES:
    - Analise a solicitação do usuário e escolha o(s) subagente(s) apropriado(s)
    - Use APENAS os subagentes quando necessário; para conversas simples, responda diretamente
    - Pode chamar múltiplos subagentes se a tarefa exigir (ex: traduzir e depois corrigir)
    - Forneça contexto claro ao chamar subagentes
    - Agregue e formate as respostas dos subagentes de forma clara
    - Para análise de imagens, use analyze_image com URL da imagem
    - Seja natural, útil e eficiente

    EXEMPLOS DE ROTEAMENTO:
    - "Traduza 'Hello' para português" → translate_text
    - "Corrija: 'Eu foi na loja'" → correct_text
    - "Quanto é 25 × 4?" → calculate
    - "Clima em São Paulo" → get_weather
    - "Qual emoji é este?" (com imagem) → analyze_image
    - "Olá, como vai?" → Resposta direta (sem subagente)
    - "Traduza e corrija este texto" → translate_text + correct_text (sequencial)
    """


def _create_supervisor_react_agent():
    """
    Create full ReAct supervisor agent with all 5 subagent tools (Phase 3).

    Replaces Phase 2 stub with create_react_agent() using:
    - LiteLLM orchestrator model (configurable via .env)
    - All 5 subagent tools: translator, corrector, calculator, weather, vision
    - VOXY supervisor instructions

    Returns:
        Compiled ReAct agent (LangGraph subgraph)
    """
    # Load orchestrator configuration
    config = load_orchestrator_config()

    # Create ChatLiteLLM for supervisor
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    # Create all 5 subagent tools
    tools = [
        create_translator_tool(),  # Phase 1
        create_calculator_tool(),  # Phase 3
        create_corrector_tool(),  # Phase 3
        create_weather_tool(),  # Phase 3
        create_vision_tool(),  # Phase 3
    ]

    logger.bind(event="LANGGRAPH|SUPERVISOR_INIT").info(
        "Creating ReAct supervisor with all 5 subagent tools",
        model=config.get_litellm_model_path(),
        tools_count=len(tools),
    )

    # Create ReAct agent (supervisor)
    supervisor_agent = create_react_agent(
        model=litellm_model,
        tools=tools,
        state_schema=VoxyState,
        prompt=_get_supervisor_instructions(),
    )

    logger.bind(event="LANGGRAPH|SUPERVISOR_INIT").info(
        "ReAct supervisor created successfully"
    )

    return supervisor_agent


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

        # Wrap vision bypass to add route tracking
        def vision_bypass_with_routing(state):
            result = vision_bypass_node(state)
            # Ensure route_taken is set (vision_bypass_node should set it)
            if "context" not in result or "route_taken" not in result.get(
                "context", {}
            ):
                # Fallback: set route_taken if not already set
                from .graph_state import update_context

                updated = update_context(state, route_taken="PATH_1")
                result = {**result, **updated}
            return result

        self.builder.add_node("vision_bypass", vision_bypass_with_routing)
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

    def add_supervisor(self) -> "SupervisorGraphBuilder":
        """
        Add full ReAct supervisor agent (Phase 3 implementation).

        Uses create_react_agent() with all 5 subagent tools.

        Returns:
            Self for method chaining
        """
        supervisor_agent = _create_supervisor_react_agent()

        # Wrap supervisor to add route tracking
        def supervisor_with_routing(state):
            result = supervisor_agent.invoke(state)
            # Add PATH_2 marker to context
            from .graph_state import update_context

            updated = update_context(state, route_taken="PATH_2")
            return {**result, **updated}

        # Add the supervisor ReAct agent as a node (wrapped)
        # create_react_agent returns a compiled graph that we add as a subgraph
        self.builder.add_node("supervisor", supervisor_with_routing)

        # Supervisor now handles tool calling internally via ReAct loop
        # It goes to END when done
        self.builder.add_edge("supervisor", END)

        self._nodes_added.add("supervisor")

        logger.bind(event="LANGGRAPH|GRAPH_BUILDER").info(
            "Full ReAct supervisor added (Phase 3) with 5 subagent tools"
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
            >>> graph = builder.compile(CheckpointerType.SQLITE)  # Uses env var
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
    Factory function to create Phase 2 graph (DEPRECATED - use create_phase3_graph).

    Kept for backward compatibility with Phase 2 tests.
    Now delegates to create_phase3_graph() which has full implementation.

    Args:
        checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
        db_path: Database path for persistent checkpointers (optional)

    Returns:
        Compiled graph ready for invocation
    """
    logger.bind(event="LANGGRAPH|GRAPH_FACTORY").warning(
        "create_phase2_graph() is deprecated, use create_phase3_graph()"
    )
    return create_phase3_graph(checkpointer_type, db_path)


def create_phase3_graph(
    checkpointer_type: CheckpointerType | str = CheckpointerType.MEMORY,
    db_path: str | None = None,
):
    """
    Factory function to create Phase 3 complete graph.

    Assembles:
    - Entry router (PATH1/PATH2 decision)
    - Vision bypass with actual Vision Agent (PATH1 direct execution)
    - Full ReAct supervisor with 5 subagent tools (PATH2 orchestration)
    - All 5 subagents: translator, calculator, corrector, weather, vision

    Args:
        checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
        db_path: Database path for persistent checkpointers (optional)

    Returns:
        Compiled graph ready for invocation

    Example:
        >>> graph = create_phase3_graph(CheckpointerType.MEMORY)
        >>> state = create_initial_state(
        ...     messages=[{"role": "user", "content": "Translate 'Hello' to French"}],
        ...     thread_id="session-123"
        ... )
        >>> config = get_checkpoint_config(thread_id="session-123")
        >>> result = graph.invoke(state, config=config)
    """
    builder = SupervisorGraphBuilder()

    builder.add_entry_router()
    builder.add_vision_bypass_stub()  # Now uses actual Vision Agent (Phase 3)
    builder.add_supervisor()  # Full ReAct supervisor with 5 tools (Phase 3)

    graph = builder.compile(checkpointer_type, db_path)

    logger.bind(event="LANGGRAPH|GRAPH_FACTORY").info(
        "Phase 3 graph created with full ReAct supervisor + 5 subagent tools",
        checkpointer_type=checkpointer_type,
    )

    return graph
