"""
Translator Subagent - OpenAI Agents SDK Implementation

Subagente especializado em tradução usando capacidades nativas do modelo.
Implementa as decisões do CREATIVE MODE para otimização multi-modelo.

Migração Loguru - Sprint 5
"""

from loguru import logger

from agents import Agent, ModelSettings

from ...config.models_config import load_translator_config
from ...utils.llm_factory import create_litellm_model


class TranslatorAgent:
    """
    Subagente de tradução usando capacidades nativas do modelo.

    Características:
    - Usa o3-mini para eficiência de custo
    - Aproveitagem das capacidades nativas de tradução
    - Sem dependências externas ou APIs
    - Otimizado para múltiplos idiomas
    """

    def __init__(self):
        """Initialize the translator subagent with configurable LiteLLM model."""
        config = load_translator_config()
        model = create_litellm_model(config)

        self.agent = Agent(
            name="Subagente Tradutor VOXY",
            model=model,
            instructions=self._get_instructions(),
            model_settings=ModelSettings(
                include_usage=config.include_usage,
                temperature=config.temperature,
            ),
        )

        self.config = config
        logger.bind(event="TRANSLATOR_AGENT|INIT").info(
            "Translator subagent initialized",
            provider=config.provider,
            model=config.model_name
        )

    def _get_instructions(self) -> str:
        """Get specialized instructions for translation."""
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

    def get_agent(self) -> Agent:
        """Get the underlying Agent instance for tool registration."""
        return self.agent


# Global instance using lazy initialization
_translator_agent = None


def get_translator_agent() -> TranslatorAgent:
    """
    Get the global translator agent instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _translator_agent
    if _translator_agent is None:
        _translator_agent = TranslatorAgent()
    return _translator_agent
