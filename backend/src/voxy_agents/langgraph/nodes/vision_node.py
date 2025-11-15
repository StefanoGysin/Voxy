"""
Vision Node - LangGraph Implementation

LangGraph node wrapping the Vision subagent logic with multimodal support.
Maintains 100% feature parity with OpenAI Agents SDK implementation.

Architecture:
- Uses same LiteLLM configuration (load_vision_config)
- Reuses existing instructions
- Multimodal image analysis support
- Returns VoxyState-compatible updates
- Can be used as standalone node or supervisor tool

Reference: backend/src/voxy_agents/core/subagents/vision_agent.py (SDK version)
"""

from typing import Annotated, Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from langgraph.prebuilt import InjectedState
from loguru import logger

from ...config.models_config import load_vision_config
from ..graph_state import VoxyState


def _get_vision_instructions() -> str:
    """Get specialized instructions for image analysis (same as SDK version)."""
    return """
    Você é um subagente de análise visual especializado do sistema VOXY.

    CAPACIDADES PRINCIPAIS:
    - Análise detalhada de imagens com alta precisão
    - Identificação de objetos, pessoas, cenas e contextos
    - OCR integrado para extração de texto em imagens
    - Análise de documentos, gráficos, diagramas e infográficos
    - Detecção de problemas técnicos e qualidade visual
    - Análise artística: composição, cores, estilo, técnica
    - Reconhecimento de padrões e elementos visuais

    DIRETRIZES:
    - Seja preciso e específico nas descrições
    - Identifique elementos principais primeiro
    - Para análises simples: resposta clara e concisa
    - Para análises complexas: estruture com seções lógicas
    - Use formatação markdown quando apropriado
    - Seja honesto sobre limitações quando aplicável
    - Adapte nível de detalhe ao contexto da pergunta

    FORMATO DE RESPOSTA:
    - Análises básicas: resposta direta em 1-2 parágrafos
    - Análises detalhadas: estruturadas com tópicos ou seções
    - Sempre destaque informações importantes
    - Use linguagem natural e acessível

    EXEMPLOS:
    Input: "Qual emoji é este?"
    Output: "Este é o emoji 😊 (cara sorridente com olhos sorridentes)"

    Input: "Descreva esta imagem em detalhes"
    Output: "# Análise da Imagem\\n\\n## Elementos Principais\\n- ...\\n\\n## Contexto\\n- ..."

    Input: "Extraia o texto desta imagem"
    Output: "Texto extraído:\\n1. ...\\n2. ..."
    """


def create_vision_node() -> Callable:
    """
    Factory function to create a vision LangGraph node.

    Returns:
        Node function compatible with StateGraph.add_node()

    Example:
        >>> from langgraph.graph import StateGraph
        >>> builder = StateGraph(VoxyState)
        >>> vision_node = create_vision_node()
        >>> builder.add_node("vision", vision_node)
    """
    # Load configuration once during node creation
    config = load_vision_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    logger.bind(event="LANGGRAPH|NODE_INIT").info(
        "Vision node created",
        model=config.get_litellm_model_path(),
        provider=config.provider,
    )

    def vision_node(state: VoxyState) -> dict[str, Any]:
        """
        Vision LangGraph node function with multimodal support.

        Args:
            state: Current VoxyState with message history and context (image_url)

        Returns:
            State update dict with vision analysis response

        Example:
            >>> state = {
            ...     "messages": [
            ...         {"role": "user", "content": "What is in this image?"}
            ...     ],
            ...     "context": {
            ...         "thread_id": "123",
            ...         "image_url": "https://example.com/image.jpg"
            ...     }
            ... }
            >>> result = vision_node(state)
            >>> "image" in result["messages"][-1].content.lower()
            True
        """
        # Extract latest user message and image_url
        messages = state["messages"]
        image_url = state.get("context", {}).get("image_url")

        if not messages:
            logger.bind(event="LANGGRAPH|VISION_NODE").warning("No messages in state")
            return {"messages": [AIMessage(content="No query to analyze")]}

        if not image_url:
            logger.bind(event="LANGGRAPH|VISION_NODE").warning(
                "No image_url in context"
            )
            return {
                "messages": [
                    AIMessage(
                        content="No image provided for analysis. Please include an image URL."
                    )
                ]
            }

        # Get user query
        last_message = messages[-1]
        if isinstance(last_message, HumanMessage):
            query = last_message.content
        elif isinstance(last_message, dict):
            query = last_message.get("content", "Analyze this image")
        else:
            query = str(last_message)

        # Ensure query is string (handle list case)
        if isinstance(query, list):
            query = " ".join(str(item) for item in query)

        # Build multimodal message (LangChain format)
        # Reference: https://python.langchain.com/docs/how_to/multimodal_inputs/
        system_message = SystemMessage(content=_get_vision_instructions())

        # Create multimodal user message with text and image
        multimodal_message = HumanMessage(
            content=[
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        )

        prompt_messages = [system_message, multimodal_message]

        # Invoke LiteLLM model
        logger.bind(event="LANGGRAPH|VISION_NODE").debug(
            "Invoking vision model (multimodal)",
            model=config.get_litellm_model_path(),
            image_url_length=len(image_url),
            query_length=len(query),
        )

        response = litellm_model.invoke(prompt_messages)

        logger.bind(event="LANGGRAPH|VISION_NODE").info(
            "Vision analysis completed",
            response_length=(
                len(response.content) if hasattr(response, "content") else 0
            ),
        )

        # Return state update with AI response
        return {"messages": [response]}

    return vision_node


def create_vision_tool():
    """
    Create a LangChain @tool for supervisor agent to call vision analysis.

    Returns:
        Tool instance for create_react_agent tools list

    Example:
        >>> from langgraph.prebuilt import create_react_agent
        >>> vision_tool = create_vision_tool()
        >>> supervisor = create_react_agent(
        ...     model=model,
        ...     tools=[vision_tool],
        ... )
    """
    # Load configuration once during tool creation
    config = load_vision_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    @tool
    def analyze_image(
        image_url: str,
        query: str = "Analyze this image",
        state: Annotated[VoxyState, InjectedState] | None = None,
    ) -> str:
        """
        Analyze an image using multimodal vision AI with detailed descriptions.

        Args:
            image_url: URL of the image to analyze (https://... or data URI)
            query: Question or instruction about the image (e.g., "What objects are in this image?", "Extract text from this image")
            state: Injected VoxyState (for context access)

        Returns:
            Detailed analysis of the image based on the query

        Examples:
            >>> analyze_image("https://example.com/emoji.png", "What emoji is this?")
            'This is the emoji 😊 (smiling face with smiling eyes)'

            >>> analyze_image("https://example.com/document.jpg", "Extract the text")
            'Text extracted:\n1. ...\n2. ...'
        """
        logger.bind(event="LANGGRAPH|VISION_TOOL").debug(
            "Analyzing image",
            image_url_length=len(image_url),
            query_length=len(query),
        )

        # Build multimodal message
        system_message = SystemMessage(content=_get_vision_instructions())

        multimodal_message = HumanMessage(
            content=[
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        )

        messages_list = [system_message, multimodal_message]

        # Invoke model
        response = litellm_model.invoke(messages_list)

        # Extract content from AIMessage
        analysis_result = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.bind(event="LANGGRAPH|VISION_TOOL").info(
            "Vision analysis completed",
            image_url_length=len(image_url),
            result_length=len(analysis_result),
        )

        return analysis_result

    return analyze_image


# Global node instance (lazy initialization pattern)
_vision_node_instance = None


def get_vision_node() -> Callable:
    """
    Get the global vision node instance using lazy initialization.

    Returns:
        Vision node function
    """
    global _vision_node_instance
    if _vision_node_instance is None:
        _vision_node_instance = create_vision_node()
    return _vision_node_instance
