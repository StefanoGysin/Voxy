"""
Weather Subagent - OpenAI Agents SDK Implementation

Subagente especializado em informações meteorológicas.
Usa APIs externas para dados em tempo real.

Migração Loguru - Sprint 5
"""

from agents import Agent, ModelSettings, function_tool
from loguru import logger

from ...config.models_config import load_weather_config
from ...utils.llm_factory import create_litellm_model


@function_tool
def get_weather_api(city: str, country: str = "BR") -> str:  # pragma: no cover
    """
    Get weather information for a city using OpenWeatherMap API.

    Args:
        city: Name of the city
        country: Country code (default: BR for Brazil)

    Returns:
        Weather information as formatted string

    Note: This function is decorated with @function_tool and cannot be directly
    tested due to OpenAI Agents SDK limitations. Coverage is excluded.
    """
    import os  # pragma: no cover

    import httpx  # pragma: no cover

    api_key = os.getenv("OPENWEATHER_API_KEY")  # pragma: no cover
    if not api_key:  # pragma: no cover
        return f"⚠️ API de clima não configurada para {city}"  # pragma: no cover

    try:  # pragma: no cover
        # OpenWeatherMap API call
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric&lang=pt"  # pragma: no cover

        with httpx.Client() as client:  # pragma: no cover
            response = client.get(url)  # pragma: no cover

        if response.status_code == 200:  # pragma: no cover
            data = response.json()  # pragma: no cover

            temp = data["main"]["temp"]  # pragma: no cover
            feels_like = data["main"]["feels_like"]  # pragma: no cover
            humidity = data["main"]["humidity"]  # pragma: no cover
            description = data["weather"][0]["description"]  # pragma: no cover
            wind_speed = data["wind"]["speed"]  # pragma: no cover

            return f"🌤️ {city}: {temp:.0f}°C ({description}), sensação térmica {feels_like:.0f}°C, umidade {humidity}%, vento {wind_speed:.1f}m/s"  # pragma: no cover

        elif response.status_code == 404:  # pragma: no cover
            return f"❌ Cidade '{city}' não encontrada. Verifique o nome e tente novamente."  # pragma: no cover  # pragma: no cover

        else:  # pragma: no cover
            return f"⚠️ Erro ao obter clima de {city}: {response.status_code}"  # pragma: no cover

    except Exception as e:  # pragma: no cover
        return f"⚠️ Erro na consulta meteorológica para {city}: {str(e)}"  # pragma: no cover


class WeatherAgent:
    """
    Subagente meteorológico com acesso a APIs de clima.

    Características:
    - Usa gpt-4o-mini para processamento eficiente
    - Integração com OpenWeatherMap API
    - Formatação inteligente de dados meteorológicos
    - Suporte a múltiplas cidades e países
    """

    def __init__(self):
        """Initialize the weather subagent with configurable LiteLLM model."""
        import time

        start_time = time.perf_counter()

        config = load_weather_config()
        model = create_litellm_model(config)

        self.agent = Agent(
            name="Subagente Meteorológico VOXY",
            model=model,
            instructions=self._get_instructions(),
            tools=[get_weather_api],  # API tool necessária
            model_settings=ModelSettings(
                include_usage=config.include_usage,
                temperature=config.temperature,
            ),
        )

        self.config = config
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Log initialization with reasoning config
        reasoning_status = "enabled" if config.reasoning_enabled else "disabled"
        reasoning_info = ""
        if config.reasoning_enabled:
            if config.thinking_budget_tokens:
                reasoning_info = f", thinking={config.thinking_budget_tokens} tokens"
            elif config.reasoning_effort:
                reasoning_info = f", effort={config.reasoning_effort}"

        logger.bind(event="STARTUP|SUBAGENT_INIT").info(
            f"\n"
            f"   ├─ ✓ Weather\n"
            f"   │  ├─ Model: {config.get_litellm_model_path()}\n"
            f"   │  ├─ Provider: {config.provider}\n"
            f"   │  ├─ Config: {config.max_tokens} tokens, temp={config.temperature}\n"
            f"   │  ├─ Reasoning: {reasoning_status}{reasoning_info}\n"
            f"   │  └─ ✓ Ready in {elapsed_ms:.1f}ms"
        )

    def _get_instructions(self) -> str:
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
        - Use a ferramenta get_weather_api para dados atualizados
        - Identifique automaticamente a cidade mencionada
        - Se a cidade for ambígua, especifique o país/estado
        - Formate as informações de forma clara e útil
        - Inclua detalhes relevantes (temperatura, condição, umidade)

        PROCESSAMENTO:
        1. Extraia o nome da cidade da solicitação
        2. Use get_weather_api para obter dados
        3. Formate a resposta de forma amigável
        4. Adicione contexto ou recomendações quando apropriado

        FORMATO DE RESPOSTA:
        - Seja claro e informativo
        - Use unidades apropriadas (Celsius para Brasil)
        - Inclua ícones ou emojis quando útil
        - Forneça contexto relevante

        EXEMPLOS:
        Input: "Qual o clima em São Paulo?"
        Process: get_weather_api("São Paulo", "BR")
        Output: "🌤️ São Paulo está com 22°C, ensolarado. Umidade de 65% e vento de 10km/h. Perfeito para atividades ao ar livre!"

        Input: "Como está o tempo em Londres?"
        Process: get_weather_api("London", "UK")
        Output: "🌧️ Londres está com 15°C, chuva leve. Umidade alta de 85%. Recomendo levar guarda-chuva!"
        """

    def get_agent(self) -> Agent:
        """Get the underlying Agent instance for tool registration."""
        return self.agent


# Global instance using lazy initialization
_weather_agent = None


def get_weather_agent():
    """
    Get the global weather agent instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _weather_agent
    if _weather_agent is None:
        _weather_agent = WeatherAgent()
    return _weather_agent
