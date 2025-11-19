"""
Corrector Node - LangGraph Implementation

LangGraph node wrapping the Corrector subagent logic.
Migrated to new clean architecture (agents/corrector/).

Architecture:
- Uses same LiteLLM configuration (load_corrector_config)
- Maintains 100% feature parity with previous implementation
- Returns VoxyState-compatible updates
- Can be used as standalone node or supervisor tool
"""

from typing import Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from loguru import logger

from voxy_agents.config.models_config import load_corrector_config
from voxy_agents.langgraph.graph_state import VoxyState


def _get_corrector_instructions() -> str:
    """Get specialized instructions for correction."""
    return """
    Você é um subagente de correção especializado do sistema VOXY.

    CAPACIDADES:
    - Corrigir erros ortográficos e gramaticais
    - Identificar e corrigir problemas de concordância
    - Melhorar clareza e fluência do texto
    - Preservar o significado e intenção original
    - Sugerir alternativas quando apropriado
    - Explicar correções quando solicitado

    DIRETRIZES:
    - Mantenha o tom e estilo do texto original
    - Corrija apenas erros evidentes
    - Não altere o significado do texto
    - Se houver múltiplas correções válidas, escolha a mais natural
    - Preserve formatação (markdown, pontuação, etc.)
    - Para textos técnicos, mantenha terminologia específica

    FORMATO DE RESPOSTA:
    - Retorne apenas o texto corrigido
    - Seja preciso e respeite o contexto
    - Mantenha formatação original quando possível

    EXEMPLOS:
    Input: "Eu foi na loja ontem"
    Output: "Eu fui à loja ontem"

    Input: "Os menino brinca no parque"
    Output: "Os meninos brincam no parque"

    Input: "Preciso fazer uns teste amanha"
    Output: "Preciso fazer uns testes amanhã"
    """


def create_corrector_node() -> Callable:
    """
    Factory function to create a corrector LangGraph node.

    Returns:
        Node function compatible with StateGraph.add_node()

    Example:
        >>> from langgraph.graph import StateGraph
        >>> builder = StateGraph(VoxyState)
        >>> corrector_node = create_corrector_node()
        >>> builder.add_node("corrector", corrector_node)
    """
    # Load configuration once during node creation
    config = load_corrector_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    logger.bind(event="LANGGRAPH|NODE_INIT").info(
        "Corrector node created",
        model=config.get_litellm_model_path(),
        provider=config.provider,
    )

    def corrector_node(state: VoxyState) -> dict[str, Any]:
        """
        Corrector LangGraph node function.

        Args:
            state: Current VoxyState with message history

        Returns:
            State update dict with corrector response

        Example:
            >>> state = {
            ...     "messages": [
            ...         {"role": "user", "content": "Correct: 'Eu foi na loja'"}
            ...     ],
            ...     "context": {"thread_id": "123"}
            ... }
            >>> result = corrector_node(state)
            >>> result["messages"][-1].content
            'Eu fui à loja'
        """
        # Extract latest user message
        messages = state["messages"]
        if not messages:
            logger.bind(event="LANGGRAPH|CORRECTOR_NODE").warning(
                "No messages in state"
            )
            return {"messages": [AIMessage(content="No text to correct")]}

        # Build prompt with instructions + user message
        system_message = SystemMessage(content=_get_corrector_instructions())
        prompt_messages = [system_message] + messages

        # Invoke LiteLLM model
        logger.bind(event="LANGGRAPH|CORRECTOR_NODE").debug(
            "Invoking corrector model",
            model=config.get_litellm_model_path(),
            message_count=len(prompt_messages),
        )

        response = litellm_model.invoke(prompt_messages)

        logger.bind(event="LANGGRAPH|CORRECTOR_NODE").info(
            "Correction completed",
            response_length=(
                len(response.content) if hasattr(response, "content") else 0
            ),
        )

        # Return state update with AI response
        return {"messages": [response]}

    return corrector_node


def create_corrector_tool():
    """
    Create a LangChain @tool for supervisor agent to call corrector.

    Returns:
        Tool instance for create_react_agent tools list

    Example:
        >>> from langgraph.prebuilt import create_react_agent
        >>> corrector_tool = create_corrector_tool()
        >>> supervisor = create_react_agent(
        ...     model=model,
        ...     tools=[corrector_tool],
        ... )
    """
    # Load configuration once during tool creation
    config = load_corrector_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    @tool
    def correct_text(text: str) -> str:
        """
        Correct spelling and grammar errors in text.

        Args:
            text: Text to correct

        Returns:
            Corrected text preserving original meaning and style

        Examples:
            >>> correct_text("Eu foi na loja ontem")
            'Eu fui à loja ontem'

            >>> correct_text("Os menino brinca no parque")
            'Os meninos brincam no parque'
        """
        # Build correction prompt
        prompt = f"Correct the following text (spelling and grammar):\n\n{text}"

        # Build messages
        system_message = SystemMessage(content=_get_corrector_instructions())
        user_message = HumanMessage(content=prompt)
        messages_list = [system_message, user_message]

        # Invoke model
        logger.bind(event="LANGGRAPH|CORRECTOR_TOOL").debug(
            "Correcting text",
            text_length=len(text),
        )

        response = litellm_model.invoke(messages_list)

        # Extract content from AIMessage
        result_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.bind(event="LANGGRAPH|CORRECTOR_TOOL").info(
            "Correction completed",
            text_length=len(text),
            result_length=len(result_text),
        )

        return result_text

    return correct_text


# Global node instance (lazy initialization pattern)
_corrector_node_instance = None


def get_corrector_node() -> Callable:
    """
    Get the global corrector node instance using lazy initialization.

    Returns:
        Corrector node function
    """
    global _corrector_node_instance
    if _corrector_node_instance is None:
        _corrector_node_instance = create_corrector_node()
    return _corrector_node_instance
