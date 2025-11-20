"""
Weather Node - LangGraph Implementation

LangGraph node wrapping the Weather subagent with OpenWeatherMap API.
Migrated to new clean architecture (agents/weather/).

Architecture:
- Uses same LiteLLM configuration (load_weather_config)
- Maintains 100% feature parity with previous implementation
- OpenWeatherMap API integration via tools/weather/
- Returns VoxyState-compatible updates
- Can be used as standalone node or supervisor tool
"""

import os
from typing import Any, Callable

import httpx
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from loguru import logger

from shared.config.models_config import load_weather_config
from voxy.graph_state import VoxyState


def _get_weather_instructions() -> str:
    """Get specialized instructions for weather information."""
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

            return f"🌤️ {city}: {temp}°C ({description}), sensação térmica {feels_like}°C, umidade {humidity}%, vento {wind_speed}m/s"
        else:
            return f"❌ Não foi possível obter o clima para {city}"

    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return f"⚠️ Erro ao consultar clima: {str(e)}"


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
    def get_weather(city: str, country: str = "BR") -> str:
        """
        Get current weather information for a city.

        Args:
            city: Name of the city (e.g., "São Paulo", "London")
            country: Country code (default: "BR" for Brazil)

        Returns:
            Current weather information with temperature, conditions, humidity, and wind

        Examples:
            >>> get_weather("São Paulo")
            '🌤️ São Paulo: 23°C (céu limpo), sensação térmica 24°C, umidade 65%, vento 3.2m/s'

            >>> get_weather("London", "UK")
            '🌧️ London: 15°C (chuva leve), sensação térmica 14°C, umidade 80%, vento 4.5m/s'
        """
        logger.bind(event="LANGGRAPH|WEATHER_TOOL").debug(
            "Fetching weather",
            city=city,
            country=country,
        )

        result = _get_weather_api(city, country)

        logger.bind(event="LANGGRAPH|WEATHER_TOOL").info(
            "Weather fetched",
            city=city,
            result_length=len(result),
        )

        return result

    return get_weather


def create_weather_node() -> Callable:
    """
    Factory function to create a weather LangGraph node.

    Note: Weather agent is primarily used as a TOOL in the supervisor.
    This node exists for completeness but the tool is the main interface.

    Returns:
        Node function compatible with StateGraph.add_node()
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

        Note: In practice, weather is used as a TOOL by the supervisor,
        not as a standalone node. This exists for consistency.

        Args:
            state: Current VoxyState with message history

        Returns:
            State update dict with weather response
        """
        messages = state["messages"]
        if not messages:
            logger.bind(event="LANGGRAPH|WEATHER_NODE").warning("No messages in state")
            return {"messages": [AIMessage(content="No weather query provided")]}

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

        return {"messages": [response]}

    return weather_node


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
