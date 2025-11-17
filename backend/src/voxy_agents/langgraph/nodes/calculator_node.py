"""
Calculator Node - LangGraph Implementation

LangGraph node wrapping the Calculator subagent logic.
Maintains 100% feature parity with OpenAI Agents SDK implementation.

Architecture:
- Uses same LiteLLM configuration (load_calculator_config)
- Reuses existing instructions
- Returns VoxyState-compatible updates
- Can be used as standalone node or supervisor tool

Reference: backend/src/voxy_agents/core/subagents/calculator_agent.py (SDK version)
"""

from typing import Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from loguru import logger

from ...config.models_config import load_calculator_config
from ..graph_state import VoxyState


def _get_calculator_instructions() -> str:
    """Get specialized instructions for calculator (same as SDK version)."""
    return """
    Você é um subagente de cálculo especializado do sistema VOXY.

    CAPACIDADES:
    - Realizar cálculos matemáticos básicos e avançados
    - Operações aritméticas (+, -, *, /, ^, √)
    - Funções trigonométricas (sin, cos, tan)
    - Logaritmos e exponenciais
    - Conversões de unidades básicas
    - Explicar o raciocínio por trás dos cálculos

    DIRETRIZES:
    - Sempre mostre o passo a passo dos cálculos
    - Use notação matemática clara
    - Verifique a precisão dos resultados
    - Se houver múltiplas interpretações, pergunte
    - Indique unidades de medida quando apropriado

    FORMATO DE RESPOSTA:
    - Apresente o cálculo de forma estruturada
    - Mostre etapas intermediárias quando relevante
    - Forneça o resultado final destacado
    - Adicione explicações quando necessário

    EXEMPLOS:
    Input: "Quanto é 25 × 4 + 10?"
    Output:
    Cálculo:
    1. 25 × 4 = 100
    2. 100 + 10 = 110

    Resultado: 110

    Input: "Raiz quadrada de 144"
    Output: √144 = 12
    """


def create_calculator_node() -> Callable:
    """
    Factory function to create a calculator LangGraph node.

    Returns:
        Node function compatible with StateGraph.add_node()

    Example:
        >>> from langgraph.graph import StateGraph
        >>> builder = StateGraph(VoxyState)
        >>> calculator_node = create_calculator_node()
        >>> builder.add_node("calculator", calculator_node)
    """
    # Load configuration once during node creation
    config = load_calculator_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    logger.bind(event="LANGGRAPH|NODE_INIT").info(
        "Calculator node created",
        model=config.get_litellm_model_path(),
        provider=config.provider,
    )

    def calculator_node(state: VoxyState) -> dict[str, Any]:
        """
        Calculator LangGraph node function.

        Args:
            state: Current VoxyState with message history

        Returns:
            State update dict with calculator response

        Example:
            >>> state = {
            ...     "messages": [
            ...         {"role": "user", "content": "Calculate 2+2"}
            ...     ],
            ...     "context": {"thread_id": "123"}
            ... }
            >>> result = calculator_node(state)
            >>> result["messages"][-1].content
            'Cálculo:\n2 + 2 = 4\n\nResultado: 4'
        """
        # Extract latest user message
        messages = state["messages"]
        if not messages:
            logger.bind(event="LANGGRAPH|CALCULATOR_NODE").warning(
                "No messages in state"
            )
            return {"messages": [AIMessage(content="No calculation to perform")]}

        # Build prompt with instructions + user message
        system_message = SystemMessage(content=_get_calculator_instructions())
        prompt_messages = [system_message] + messages

        # Invoke LiteLLM model
        logger.bind(event="LANGGRAPH|CALCULATOR_NODE").debug(
            "Invoking calculator model",
            model=config.get_litellm_model_path(),
            message_count=len(prompt_messages),
        )

        response = litellm_model.invoke(prompt_messages)

        logger.bind(event="LANGGRAPH|CALCULATOR_NODE").info(
            "Calculation completed",
            response_length=(
                len(response.content) if hasattr(response, "content") else 0
            ),
        )

        # Return state update with AI response
        return {"messages": [response]}

    return calculator_node


def create_calculator_tool():
    """
    Create a LangChain @tool for supervisor agent to call calculator.

    Returns:
        Tool instance for create_react_agent tools list

    Example:
        >>> from langgraph.prebuilt import create_react_agent
        >>> calculator_tool = create_calculator_tool()
        >>> supervisor = create_react_agent(
        ...     model=model,
        ...     tools=[calculator_tool],
        ... )
    """
    # Load configuration once during tool creation
    config = load_calculator_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    @tool
    def calculate(expression: str) -> str:
        """
        Perform mathematical calculations with step-by-step explanations.

        Args:
            expression: Mathematical expression to calculate (e.g., "2+2", "sqrt(144)", "25 * 4 + 10")

        Returns:
            Calculation result with explanation

        Examples:
            >>> calculate("2+2")
            'Cálculo:\n2 + 2 = 4\n\nResultado: 4'

            >>> calculate("25 * 4 + 10")
            'Cálculo:\n1. 25 × 4 = 100\n2. 100 + 10 = 110\n\nResultado: 110'
        """
        # Build calculation prompt
        prompt = (
            f"Calculate the following expression and show your work:\n\n{expression}"
        )

        # Build messages
        system_message = SystemMessage(content=_get_calculator_instructions())
        user_message = HumanMessage(content=prompt)
        messages_list = [system_message, user_message]

        # Invoke model
        logger.bind(event="LANGGRAPH|CALCULATOR_TOOL").debug(
            "Calculating expression",
            expression_length=len(expression),
        )

        response = litellm_model.invoke(messages_list)

        # Extract content from AIMessage
        result_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        logger.bind(event="LANGGRAPH|CALCULATOR_TOOL").info(
            "Calculation completed",
            expression_length=len(expression),
            result_length=len(result_text),
        )

        return result_text

    return calculate


# Global node instance (lazy initialization pattern)
_calculator_node_instance = None


def get_calculator_node() -> Callable:
    """
    Get the global calculator node instance using lazy initialization.

    Returns:
        Calculator node function
    """
    global _calculator_node_instance
    if _calculator_node_instance is None:
        _calculator_node_instance = create_calculator_node()
    return _calculator_node_instance
