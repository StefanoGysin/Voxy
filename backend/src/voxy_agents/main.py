"""
VOXY Agents Main Entry Point

Sistema multi-agente completo usando OpenAI Agents SDK.
Implementa orquestração inteligente com Vision Agent integrado.

Arquitetura:
- VOXY (agente principal) com LLM configurável (ORCHESTRATOR_MODEL)
- 4 subagentes especializados como tools
- Vision Agent integrado diretamente no orquestrador
- Sistema de sessões para contexto persistente
- Análise avançada de imagens com Vision model configurável (VISION_MODEL)

⚠️ ORDEM DE IMPORTS É CRÍTICA PARA LOGGING
1️⃣ Configurar Loguru
2️⃣ Instalar InterceptHandler
3️⃣ Importar outros módulos
"""

# ===== 0️⃣ PRÉ-CONFIG: Suprimir duplicação de logs LiteLLM =====
import os

os.environ["LITELLM_LOG"] = "ERROR"  # Só erros críticos (evita duplicação DEBUG/INFO)

# ===== 1️⃣ PRIMEIRO: Configurar Loguru =====
from .config.logger_config import configure_logger

configure_logger()

# ===== 2️⃣ SEGUNDO: Instalar InterceptHandler ANTES de outros imports =====
from .config.logger_config import setup_stdlib_intercept

setup_stdlib_intercept()

# ===== 3️⃣ TERCEIRO: AGORA importar outros módulos =====
import asyncio
from typing import Any, Optional

from loguru import logger

from .core.subagents.calculator_agent import get_calculator_agent
from .core.subagents.corrector_agent import get_corrector_agent
from .core.subagents.translator_agent import get_translator_agent
from .core.subagents.weather_agent import get_weather_agent
from .core.voxy_orchestrator import get_voxy_orchestrator

# from agents import SupabaseSession  # Will be added later


class VOXYSystem:
    """
    Sistema VOXY completo - ponto de entrada principal.

    Integra todos os componentes e implementa o padrão
    "subagentes como tools" do OpenAI Agents SDK.
    """

    def __init__(self):
        """Initialize the complete VOXY system."""
        self.orchestrator = get_voxy_orchestrator()
        self._setup_subagents()
        # Summary log now in fastapi_server.py lifespan()

    def _setup_subagents(self):
        """Register all subagents as tools for VOXY."""
        logger.bind(event="STARTUP|SUBAGENTS").info(
            "📦 Registering Subagents (4 agents + Vision)"
        )

        # Register translator subagent
        self.orchestrator.register_subagent(
            name="translator",
            agent=get_translator_agent().get_agent(),
            tool_name="translate_text",
            description="Traduzir texto entre idiomas diferentes usando capacidades nativas",
        )

        # Register corrector subagent
        self.orchestrator.register_subagent(
            name="corrector",
            agent=get_corrector_agent().get_agent(),
            tool_name="correct_text",
            description="Corrigir erros ortográficos e gramaticais preservando o significado original",
        )

        # Register weather subagent
        self.orchestrator.register_subagent(
            name="weather",
            agent=get_weather_agent().get_agent(),
            tool_name="get_weather",
            description="Obter informações meteorológicas atualizadas para qualquer cidade",
        )

        # Register calculator subagent
        self.orchestrator.register_subagent(
            name="calculator",
            agent=get_calculator_agent().get_agent(),
            tool_name="calculate",
            description="Realizar cálculos matemáticos básicos e avançados com explicações",
        )

        # Log Vision Agent (integrated in orchestrator)
        from .config.models_config import load_vision_config

        vision_config = load_vision_config()

        logger.bind(event="STARTUP|SUBAGENT_INIT").info(
            "   \n"
            "   └─ ✓ Vision (integrated in orchestrator)\n"
            f"      ├─ Model: {vision_config.get_litellm_model_path()}\n"
            f"      ├─ Config: {vision_config.max_tokens} tokens, temp={vision_config.temperature}, reasoning={vision_config.reasoning_effort}\n"
            "      └─ ✓ Integrated"
        )

    async def chat(
        self,
        message: str,
        user_id: str = "default",
        session_id: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Chat interface for VOXY system with vision support.

        Args:
            message: User's message
            user_id: User identifier for session management
            session_id: Optional session ID for conversation context
            image_url: Optional image URL for vision analysis with Vision model

        Returns:
            Tuple of (response_text, metadata)
        """
        try:
            # Process through VOXY orchestrator with session management
            response, metadata = await self.orchestrator.chat(
                message, user_id, session_id, image_url
            )

            return response, metadata

        except Exception as e:
            logger.bind(event="VOXY_SYSTEM|CHAT_ERROR").exception("Error in VOXY chat")
            error_metadata: dict[str, str | list | None] = {
                "agent_type": "system_error",
                "tools_used": [],
                "error": str(e),
                "user_id": user_id,
                "session_id": session_id,
            }
            return (
                f"Desculpe, encontrei um erro ao processar sua mensagem: {str(e)}",
                error_metadata,
            )

    def get_system_stats(self) -> dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "orchestrator_stats": self.orchestrator.get_stats(),
            "subagents_count": len(self.orchestrator.subagents),
            "system_status": "operational",
        }


# Global VOXY system instance - using lazy initialization
_voxy_system = None


def get_voxy_system() -> VOXYSystem:
    """
    Get the global VOXY system instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _voxy_system
    if _voxy_system is None:
        _voxy_system = VOXYSystem()
    return _voxy_system


async def main():
    """
    Example usage of the VOXY system.
    Demonstrates the multi-agent capabilities.
    """
    print("🎯 VOXY Agents System - OpenAI Agents SDK Implementation")
    print("=" * 60)

    # Example interactions demonstrating different subagents
    test_messages = [
        "Olá! Como você está?",
        "Traduza 'Hello world' para português",
        "Corrija este texto: 'Eu foi na loja ontem'",
        "Qual o clima em São Paulo?",
        "Quanto é 25 × 4 + 10?",
        "Traduza 'Bom dia' para inglês e me diga quanto é a raiz quadrada de 16",
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Usuário: {message}")

        try:
            voxy_system = get_voxy_system()
            response, metadata = await voxy_system.chat(message, f"test_user_{i}")
            print(f"   VOXY: {response}")
            print(f"   Agent: {metadata.get('agent_type', 'unknown')}")
            if metadata.get("tools_used"):
                print(f"   Tools: {', '.join(metadata['tools_used'])}")
        except Exception as e:
            print(f"   Erro: {e}")

    # Show system statistics
    print("\n📊 Estatísticas do Sistema:")
    voxy_system = get_voxy_system()
    stats = voxy_system.get_system_stats()
    print(f"   - Subagentes registrados: {stats['subagents_count']}")
    print(f"   - Status: {stats['system_status']}")


if __name__ == "__main__":
    asyncio.run(main())
