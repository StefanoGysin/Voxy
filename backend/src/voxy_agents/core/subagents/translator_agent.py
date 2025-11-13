"""
Translator Subagent - OpenAI Agents SDK Implementation

Subagente especializado em tradução usando capacidades nativas do modelo.
Implementa as decisões do CREATIVE MODE para otimização multi-modelo.

Migração Loguru - Sprint 5
"""

from agents import Agent
from loguru import logger

from ...config.models_config import load_translator_config
from ...utils.llm_factory import build_model_settings, create_model_with_reasoning


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
        import time

        start_time = time.perf_counter()

        config = load_translator_config()
        model, reasoning_params = create_model_with_reasoning(config)
        model_settings = build_model_settings(config, reasoning_params)

        self.agent = Agent(
            name="Subagente Tradutor VOXY",
            model=model,
            instructions=self._get_instructions(),
            model_settings=model_settings,
        )

        self.config = config
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Log initialization with reasoning config
        reasoning_status = "enabled" if config.reasoning_enabled else "disabled"
        reasoning_info = ""
        if config.reasoning_enabled:
            if config.thinking_budget_tokens:
                reasoning_info = f", thinking={config.thinking_budget_tokens} tokens"
            elif config.gemini_thinking_budget:
                reasoning_info = f", gemini_budget={config.gemini_thinking_budget}"
            elif config.reasoning_effort:
                reasoning_info = f", effort={config.reasoning_effort}"

        logger.bind(event="STARTUP|SUBAGENT_INIT").info(
            f"\n"
            f"   ├─ ✓ Translator\n"
            f"   │  ├─ Model: {config.get_litellm_model_path()}\n"
            f"   │  ├─ Provider: {config.provider}\n"
            f"   │  ├─ Config: {config.max_tokens} tokens, temp={config.temperature}\n"
            f"   │  ├─ Reasoning: {reasoning_status}{reasoning_info}\n"
            f"   │  └─ ✓ Ready in {elapsed_ms:.1f}ms"
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
