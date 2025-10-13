"""
Corrector Subagent - OpenAI Agents SDK Implementation

Subagente especializado em correção ortográfica e gramatical.
Usa capacidades nativas do modelo para eficiência máxima.

Migração Loguru - Sprint 5
"""

from loguru import logger

from agents import Agent, ModelSettings

from ...config.models_config import load_corrector_config
from ...utils.llm_factory import create_litellm_model


class CorrectorAgent:
    """
    Subagente de correção usando capacidades nativas do modelo.

    Características:
    - Usa o3-mini para eficiência de custo
    - Correção ortográfica e gramatical avançada
    - Preservação do significado original
    - Suporte a múltiplos idiomas
    """

    def __init__(self):
        """Initialize the corrector subagent with configurable LiteLLM model."""
        import time
        start_time = time.perf_counter()

        config = load_corrector_config()
        model = create_litellm_model(config)

        self.agent = Agent(
            name="Subagente Corretor VOXY",
            model=model,
            instructions=self._get_instructions(),
            model_settings=ModelSettings(
                include_usage=config.include_usage,
                temperature=config.temperature,
            ),
        )

        self.config = config
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.bind(event="STARTUP|SUBAGENT_INIT").info(
            f"\n"
            f"   ├─ ✓ Corrector\n"
            f"   │  ├─ Model: {config.get_litellm_model_path()}\n"
            f"   │  ├─ Config: {config.max_tokens} tokens, temp={config.temperature}\n"
            f"   │  └─ ✓ Ready in {elapsed_ms:.1f}ms"
        )

    def _get_instructions(self) -> str:
        """Get specialized instructions for text correction."""
        return """
        Você é um subagente de correção especializado do sistema VOXY.

        CAPACIDADES:
        - Correção ortográfica precisa
        - Correção gramatical avançada
        - Melhoria de clareza e fluidez
        - Preservação do significado original
        - Detecção automática do idioma

        DIRETRIZES:
        - Use sua capacidade nativa de gramática e ortografia
        - Corrija APENAS erros, mantendo o estilo original
        - Preserve a intenção e tom do autor
        - Mantenha termos técnicos e nomes próprios
        - Não reescreva completamente - apenas corrija

        TIPOS DE CORREÇÃO:
        - Erros ortográficos (grafia incorreta)
        - Erros gramaticais (concordância, conjugação)
        - Pontuação inadequada
        - Acentuação incorreta
        - Estrutura sintática confusa

        FORMATO DE RESPOSTA:
        - Retorne apenas o texto corrigido
        - Mantenha formatação original (parágrafos, quebras)
        - Preserve maiúsculas/minúsculas quando apropriado

        EXEMPLOS:
        Input: "Eu foi na loja ontem."
        Output: "Eu fui à loja ontem."

        Input: "Os menino está brincando no parque"
        Output: "Os meninos estão brincando no parque."

        Input: "Hello, how are you doing today"
        Output: "Hello, how are you doing today?"
        """

    def get_agent(self) -> Agent:
        """Get the underlying Agent instance for tool registration."""
        return self.agent


# Global instance using lazy initialization
_corrector_agent = None


def get_corrector_agent():
    """
    Get the global corrector agent instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _corrector_agent
    if _corrector_agent is None:
        _corrector_agent = CorrectorAgent()
    return _corrector_agent
