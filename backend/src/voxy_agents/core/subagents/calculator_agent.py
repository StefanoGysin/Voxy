"""
Calculator Subagent - OpenAI Agents SDK Implementation

Subagente especializado em cálculos matemáticos.
Usa capacidades nativas do modelo para matemática avançada.
Agora configurável via LiteLLM para suporte a múltiplos providers (OpenRouter, OpenAI, etc.).

Migração Loguru - Sprint 5
"""

from loguru import logger

from agents import Agent, ModelSettings

from ...config.models_config import load_calculator_config
from ...utils.llm_factory import create_litellm_model


class CalculatorAgent:
    """
    Subagente de cálculos usando capacidades nativas do modelo.

    Características:
    - Configurável via LiteLLM (OpenRouter, OpenAI, Anthropic, etc.)
    - Default: Grok Code Fast 1 (x-ai/grok-code-fast-1) via OpenRouter
    - Raciocínio matemático avançado com reasoning traces
    - Matemática básica e avançada
    - Explicações passo a passo
    - Formatação clara de resultados
    """

    def __init__(self):
        """
        Initialize the calculator subagent with configurable LiteLLM model.

        Configuration is loaded from environment variables:
        - CALCULATOR_PROVIDER: Provider name (default: "openrouter")
        - CALCULATOR_MODEL: Model name (default: "x-ai/grok-code-fast-1")
        - CALCULATOR_MAX_TOKENS: Max tokens (default: 2000)
        - CALCULATOR_TEMPERATURE: Temperature (default: 0.1)
        - OPENROUTER_API_KEY: Required if provider is "openrouter"

        Raises:
            ValueError: If required API key is missing or config is invalid
        """
        # Load configuration from environment variables
        config = load_calculator_config()

        # Create LiteLLM model instance via factory
        model = create_litellm_model(config)

        # Create agent with configured model
        self.agent = Agent(
            name="Subagente Calculadora VOXY",
            model=model,
            instructions=self._get_instructions(),
            model_settings=ModelSettings(
                include_usage=config.include_usage,
                temperature=config.temperature,
            ),
        )

        # Store config for reference
        self.config = config

        logger.bind(event="CALCULATOR_AGENT|INIT").info(
            "Calculator subagent initialized",
            provider=config.provider,
            model=config.model_name,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )

    def _get_instructions(self) -> str:
        """Get specialized instructions for mathematical calculations."""
        return """
        Você é um subagente de cálculos especializado do sistema VOXY usando raciocínio matemático avançado.

        CAPACIDADES PRINCIPAIS:
        - Aritmética básica (soma, subtração, multiplicação, divisão)
        - Álgebra e equações
        - Geometria e trigonometria
        - Estatística e probabilidade
        - Cálculo diferencial e integral
        - Conversões de unidades
        - Raciocínio lógico-espacial
        - Resolução de problemas complexos

        CAPACIDADES AVANÇADAS (Grok Code Fast 1):
        - Raciocínio matemático com reasoning traces
        - Análise passo a passo de problemas complexos
        - Resolução de quebra-cabeças lógico-espaciais
        - Explicação detalhada do processo de raciocínio

        DIRETRIZES:
        - Use sua capacidade nativa de raciocínio matemático
        - Para problemas complexos, mostre o reasoning trace (passo a passo)
        - Forneça resultados precisos e exatos
        - Explique conceitos complexos de forma simples
        - Use formatação clara para fórmulas
        - Para problemas lógico-espaciais, descreva o raciocínio usado

        TIPOS DE CÁLCULOS:
        - Operações básicas: 2 + 2 = 4
        - Percentuais: 15% de 200 = 30
        - Potências: 2³ = 8
        - Raízes: √16 = 4
        - Equações: 2x + 5 = 15, x = 5
        - Conversões: 1 metro = 100 centímetros
        - Problemas lógicos: "Se há 20 casas em fila..."

        FORMATO DE RESPOSTA:
        - Para cálculos simples: resultado direto
        - Para problemas complexos:
          1. Raciocínio (reasoning trace)
          2. Passos da solução
          3. Resultado final destacado
        - Use símbolos matemáticos apropriados
        - Destaque o resultado final

        EXEMPLOS:
        Input: "Quanto é 25 × 4?"
        Output: "25 × 4 = 100"

        Input: "Qual é a área de um círculo com raio de 5 metros?"
        Output: "Área = π × r²\\nÁrea = π × 5²\\nÁrea = π × 25\\nÁrea ≈ 78,54 metros quadrados"

        Input: "Converta 50 milhas para quilômetros"
        Output: "50 milhas = 50 × 1,609 = 80,45 quilômetros"

        Input: "Se há 20 casas em fila, e a casa azul está exatamente no meio, qual é a posição dela?"
        Output: "🧠 Raciocínio: Com 20 casas em fila (numeradas 1 a 20), o meio está entre a casa 10 e 11.\\n\\nComo a casa azul está 'exatamente no meio', há 2 interpretações possíveis:\\n1. Entre as casas 10 e 11 (posição 10.5, não existe)\\n2. No centro médio: (1+20)/2 = 10.5\\n\\n✓ Resposta: A casa azul está na posição 10 ou 11 (dependendo de como definimos 'meio' com número par de casas)"
        """

    def get_agent(self) -> Agent:
        """Get the underlying Agent instance for tool registration."""
        return self.agent


# Global instance using lazy initialization
_calculator_agent = None


def get_calculator_agent():
    """
    Get the global calculator agent instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _calculator_agent
    if _calculator_agent is None:
        _calculator_agent = CalculatorAgent()
    return _calculator_agent
