"""
Weather Node - LangGraph Implementation

LangGraph node wrapping the Weather subagent logic with OpenWeatherMap API.
Maintains 100% feature parity with OpenAI Agents SDK implementation.

Architecture:
- Uses same LiteLLM configuration (load_weather_config)
- Reuses existing instructions
- OpenWeatherMap API integration
- Returns VoxyState-compatible updates
- Can be used as standalone node or supervisor tool

Reference: backend/src/voxy_agents/core/subagents/weather_agent.py (SDK version)
"""

import os
from typing import Annotated, Any, Callable

import httpx
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from langgraph.prebuilt import InjectedState
from loguru import logger

from ...config.models_config import load_weather_config
from ..graph_state import VoxyState


def _get_weather_instructions() -> str:
    """Get specialized instructions for weather information (same as SDK version)."""
    return """
    Você é um subagente meteorológico especializado do sistema VOXY.

    CAPACIDADES:
    - Obtenção de dados meteorológicos em tempo real
    - Interpretação de condições climáticas
    - Previsões e tendências
    - Recomendações baseadas no clima
    - Suporte a cidades globais

    DIRETRIZES:
    - Use a ferramenta get_weather para dados atualizados
    - Identifique automaticamente a cidade mencionada
    - Se a cidade for ambígua, especifique o país/estado
    - Formate as informações de forma clara e útil
    - Inclua detalhes relevantes (temperatura, condição, umidade)

    PROCESSAMENTO:
    1. Extraia o nome da cidade da solicitação
    2. Use get_weather para obter dados
    3. Formate a resposta de forma amigável
    4. Adicione contexto ou recomendações quando apropriado

    FORMATO DE RESPOSTA:
    - Seja claro e informativo
    - Use unidades apropriadas (Celsius para Brasil)
    - Inclua ícones ou emojis quando útil
    - Forneça contexto relevante

    EXEMPLOS:
    Input: "Como está o tempo em São Paulo?"
    Output: "🌤️ São Paulo: 23°C (céu limpo), sensação térmica 24°C, umidade 65%, vento 3.2m/s"

    Input: "Clima no Rio de Janeiro"
    Output: "☀️ Rio de Janeiro: 28°C (ensolarado), sensação térmica 30°C, umidade 70%, vento 2.5m/s"
    """


def _get_weather_api(city: str, country: str = "BR") -> str:
    """
    Get weather information from OpenWeatherMap API.

    Args:
        city: Name of the city
        country: Country code (default: BR for Brazil)

    Returns:
        Weather information as formatted string
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return f"⚠️ API de clima não configurada para {city}"

    try:
        # OpenWeatherMap API call
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric&lang=pt"

        with httpx.Client() as client:
            response = client.get(url)

        if response.status_code == 200:
            data = response.json()

            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]

            return f"🌤️ {city}: {temp:.0f}°C ({description}), sensação térmica {feels_like:.0f}°C, umidade {humidity}%, vento {wind_speed:.1f}m/s"

        elif response.status_code == 404:
            return f"❌ Cidade '{city}' não encontrada. Verifique o nome e tente novamente."

        else:
            return f"⚠️ Erro ao obter clima de {city}: {response.status_code}"

    except Exception as e:
        return f"⚠️ Erro na consulta meteorológica para {city}: {str(e)}"


def create_weather_node() -> Callable:
    """
    Factory function to create a weather LangGraph node.

    Returns:
        Node function compatible with StateGraph.add_node()

    Example:
        >>> from langgraph.graph import StateGraph
        >>> builder = StateGraph(VoxyState)
        >>> weather_node = create_weather_node()
        >>> builder.add_node("weather", weather_node)
    """
    # Load configuration once during node creation
    config = load_weather_config()

    # Create ChatLiteLLM for LangChain integration
    litellm_model = ChatLiteLLM(
        model=config.get_litellm_model_path(),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    logger.bind(event="LANGGRAPH|NODE_INIT").info(
        "Weather node created",
        model=config.get_litellm_model_path(),
        provider=config.provider,
    )

    def weather_node(state: VoxyState) -> dict[str, Any]:
        """
        Weather LangGraph node function.

        Args:
            state: Current VoxyState with message history

        Returns:
            State update dict with weather response

        Example:
            >>> state = {
            ...     "messages": [
            ...         {"role": "user", "content": "Weather in São Paulo?"}
            ...     ],
            ...     "context": {"thread_id": "123"}
            ... }
            >>> result = weather_node(state)
            >>> "São Paulo" in result["messages"][-1].content
            True
        """
        # Extract latest user message
        messages = state["messages"]
        if not messages:
            logger.bind(event="LANGGRAPH|WEATHER_NODE").warning("No messages in state")
            return {"messages": [AIMessage(content="No weather query to process")]}

        # Build prompt with instructions + user message
        system_message = SystemMessage(content=_get_weather_instructions())
        prompt_messages = [system_message] + messages

        # Invoke LiteLLM model
        logger.bind(event="LANGGRAPH|WEATHER_NODE").debug(
            "Invoking weather model",
            model=config.get_litellm_model_path(),
            message_count=len(prompt_messages),
        )

        response = litellm_model.invoke(prompt_messages)

        logger.bind(event="LANGGRAPH|WEATHER_NODE").info(
            "Weather query completed",
            response_length=(
                len(response.content) if hasattr(response, "content") else 0
            ),
        )

        # Return state update with AI response
        return {"messages": [response]}

    return weather_node


def create_weather_tool():
    """
    Create a LangChain @tool for supervisor agent to call weather.

    Returns:
        Tool instance for create_react_agent tools list

    Example:
        >>> from langgraph.prebuilt import create_react_agent
        >>> weather_tool = create_weather_tool()
        >>> supervisor = create_react_agent(
        ...     model=model,
        ...     tools=[weather_tool],
        ... )
    """

    @tool
    def get_weather(
        city: str,
        country: str = "BR",
        state: Annotated[VoxyState, InjectedState] | None = None,
    ) -> str:
        """
        Get current weather information for a city using real-time data from OpenWeatherMap API.

        Args:
            city: Name of the city (e.g., "São Paulo", "Rio de Janeiro", "New York")
            country: Country code (default: "BR" for Brazil, use "US" for USA, etc.)
            state: Injected VoxyState (for context access)

        Returns:
            Formatted weather information with temperature, conditions, humidity, and wind

        Examples:
            >>> get_weather("São Paulo")
            '🌤️ São Paulo: 23°C (céu limpo), sensação térmica 24°C, umidade 65%, vento 3.2m/s'

            >>> get_weather("New York", "US")
            '🌤️ New York: 18°C (cloudy), feels like 17°C, humidity 55%, wind 4.5m/s'
        """
        logger.bind(event="LANGGRAPH|WEATHER_TOOL").debug(
            "Fetching weather",
            city=city,
            country=country,
        )

        # Call OpenWeatherMap API
        weather_info = _get_weather_api(city, country)

        logger.bind(event="LANGGRAPH|WEATHER_TOOL").info(
            "Weather fetched successfully",
            city=city,
            result_length=len(weather_info),
        )

        return weather_info

    return get_weather


# Global node instance (lazy initialization pattern)
_weather_node_instance = None


def get_weather_node() -> Callable:
    """
    Get the global weather node instance using lazy initialization.

    Returns:
        Weather node function
    """
    global _weather_node_instance
    if _weather_node_instance is None:
        _weather_node_instance = create_weather_node()
    return _weather_node_instance
