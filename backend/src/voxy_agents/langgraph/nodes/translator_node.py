"""
Translator Node - LangGraph Implementation

LangGraph node wrapping the Translator subagent logic.
Maintains 100% feature parity with OpenAI Agents SDK implementation.

Architecture:
- Uses same LiteLLM configuration (load_translator_config)
- Reuses existing instructions
- Returns VoxyState-compatible updates
- Can be used as standalone node or supervisor tool

Reference: LangGraph Tool-Calling Supervisor pattern
https://langchain-ai.github.io/langgraph/concepts/multi_agent/
"""

from typing import Annotated, Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from langgraph.prebuilt import InjectedState
from loguru import logger

from ...config.models_config import load_translator_config
from ..graph_state import VoxyState


def _get_translator_instructions() -> str:
    """Get specialized instructions for translation (same as SDK version)."""
    return """
    Você é um subagente de tradução especializado do sistema VOXY.

    CAPACIDADES:
    - Tradução entre qualquer par de idiomas
    - Detecção automática do idioma de origem
    - Preservação do contexto e significado
    - Adaptação cultural quando apropriado
    - Formatação e estilo consistentes

    DIRETRIZES:
    - Use sua capacidade nativa de tradução multilingue
    - Mantenha o tom e estilo do texto original
    - Para textos técnicos, preserve terminologia específica
    - Para textos criativos, adapte culturalmente quando necessário
    - Se o idioma de destino não for especificado, pergunte

    FORMATO DE RESPOSTA:
    - Retorne apenas a tradução solicitada
    - Seja preciso e fluente
    - Mantenha formatação original (markdown, etc.)

    EXEMPLOS:
    Input: "Translate 'Hello world' to Portuguese"
    Output: "Olá mundo"

    Input: "Traduzir 'Bom dia' para inglês"
    Output: "Good morning"
    """


def create_translator_node() -> Callable:
    """
    Factory function to create a translator LangGraph node.

    Returns:
        Node function compatible with StateGraph.add_node()

    Example:
        >>> from langgraph.graph import StateGraph
        >>> builder = StateGraph(VoxyState)
        >>> translator_node = create_translator_node()
        >>> builder.add_node("translator", translator_node)
    """
    # Load configuration once during node creation
    config = load_translator_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    logger.bind(event="LANGGRAPH|NODE_INIT").info(
        "Translator node created",
        model=config.get_litellm_model_path(),
        provider=config.provider,
    )

    def translator_node(state: VoxyState) -> dict[str, Any]:
        """
        Translator LangGraph node function.

        Args:
            state: Current VoxyState with message history

        Returns:
            State update dict with translator response

        Example:
            >>> state = {
            ...     "messages": [
            ...         {"role": "user", "content": "Translate 'Hello' to French"}
            ...     ],
            ...     "context": {"thread_id": "123"}
            ... }
            >>> result = translator_node(state)
            >>> result["messages"][-1].content
            'Bonjour'
        """
        # Extract latest user message
        messages = state["messages"]
        if not messages:
            logger.bind(event="LANGGRAPH|TRANSLATOR_NODE").warning(
                "No messages in state"
            )
            return {"messages": [AIMessage(content="No message to translate")]}

        # Build prompt with instructions + user message
        system_message = SystemMessage(content=_get_translator_instructions())
        prompt_messages = [system_message] + messages

        # Invoke LiteLLM model
        logger.bind(event="LANGGRAPH|TRANSLATOR_NODE").debug(
            "Invoking translator model",
            model=config.get_litellm_model_path(),
            message_count=len(prompt_messages),
        )

        response = litellm_model.invoke(prompt_messages)

        logger.bind(event="LANGGRAPH|TRANSLATOR_NODE").info(
            "Translation completed",
            response_length=(
                len(response.content) if hasattr(response, "content") else 0
            ),
        )

        # Return state update with AI response
        return {"messages": [response]}

    return translator_node


def create_translator_tool():
    """
    Create a LangChain @tool for supervisor agent to call translator.

    Returns:
        Tool instance for create_react_agent tools list

    Example:
        >>> from langgraph.prebuilt import create_react_agent
        >>> translator_tool = create_translator_tool()
        >>> supervisor = create_react_agent(
        ...     model=model,
        ...     tools=[translator_tool],
        ... )
    """
    # Load configuration once during tool creation
    config = load_translator_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    @tool
    def translate_text(
        text: str,
        target_language: str,
        source_language: str | None = None,
        state: Annotated[VoxyState, InjectedState] | None = None,
    ) -> str:
        """
        Translate text between languages using native model capabilities.

        Args:
            text: Text to translate
            target_language: Target language (e.g., "Portuguese", "French", "Spanish")
            source_language: Source language (optional, auto-detected if not provided)
            state: Injected VoxyState (for context access)

        Returns:
            Translated text

        Examples:
            >>> translate_text("Hello world", "Portuguese")
            'Olá mundo'

            >>> translate_text("Bom dia", "English", source_language="Portuguese")
            'Good morning'
        """
        # Build translation prompt
        if source_language:
            prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}"
        else:
            prompt = f"Translate the following text to {target_language}:\n\n{text}"

        # Build messages
        system_message = SystemMessage(content=_get_translator_instructions())
        user_message = HumanMessage(content=prompt)
        messages_list = [system_message, user_message]

        # Invoke model
        logger.bind(event="LANGGRAPH|TRANSLATOR_TOOL").debug(
            "Translating text",
            text_length=len(text),
            target_language=target_language,
            source_language=source_language,
        )

        response = litellm_model.invoke(messages_list)

        # Extract content from AIMessage
        translated_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.bind(event="LANGGRAPH|TRANSLATOR_TOOL").info(
            "Translation completed",
            original_length=len(text),
            translated_length=len(translated_text),
        )

        return translated_text

    return translate_text


# Global node instance (lazy initialization pattern)
_translator_node_instance = None


def get_translator_node() -> Callable:
    """
    Get the global translator node instance using lazy initialization.

    Returns:
        Translator node function
    """
    global _translator_node_instance
    if _translator_node_instance is None:
        _translator_node_instance = create_translator_node()
    return _translator_node_instance
