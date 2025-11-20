"""
VOXY Agents Main Entry Point - LangGraph Implementation

Sistema multi-agente completo usando LangGraph.
Implementa orquestração inteligente com Vision Agent integrado.

Arquitetura:
- VOXY (agente principal) com LLM configurável (ORCHESTRATOR_MODEL)
- 5 subagentes especializados como LangGraph nodes/tools
- Vision Agent integrado no graph com dual-path (bypass + orchestrated)
- Sistema de sessões via SQLite checkpointer para contexto persistente
- Análise avançada de imagens com Vision model configurável (VISION_MODEL)

Migrated from voxy_agents/langgraph_main.py to voxy/main.py.

⚠️ ORDEM DE IMPORTS É CRÍTICA PARA LOGGING
1️⃣ Configurar Loguru
2️⃣ Instalar InterceptHandler
3️⃣ Importar outros módulos
"""

# ruff: noqa: E402
# Reason: Logging must be configured before other imports

# ===== 0️⃣ PRÉ-CONFIG: Suprimir duplicação de logs LiteLLM =====
import os

os.environ["LITELLM_LOG"] = "ERROR"  # Só erros críticos (evita duplicação DEBUG/INFO)

# ===== 1️⃣ PRIMEIRO: Configurar Loguru =====
from src.shared.config.logger_config import configure_logger

configure_logger()

# ===== 2️⃣ SEGUNDO: Instalar InterceptHandler ANTES de outros imports =====
from src.shared.config.logger_config import setup_stdlib_intercept

setup_stdlib_intercept()

# ===== 3️⃣ TERCEIRO: AGORA importar outros módulos =====
import asyncio
from typing import Any, Optional

from loguru import logger

from voxy.checkpointer import CheckpointerType
from voxy.orchestrator import get_langgraph_orchestrator


class VOXYSystem:
    """
    Sistema VOXY completo - ponto de entrada principal.

    Integra todos os componentes usando LangGraph para orquestração.
    Implementa padrão stateful multi-agent com checkpointer persistence.
    """

    def __init__(
        self,
        checkpointer_type: CheckpointerType = CheckpointerType.SQLITE,
        db_path: str | None = None,
    ):
        """
        Initialize the complete VOXY system with LangGraph orchestration.

        Args:
            checkpointer_type: Type of checkpointer (memory, sqlite, postgres)
            db_path: Optional database path (defaults to LANGGRAPH_DB_PATH env var)
        """
        # Get LangGraph orchestrator singleton
        # Uses environment variable LANGGRAPH_DB_PATH if db_path not provided
        if db_path is None:
            db_path = os.getenv("LANGGRAPH_DB_PATH", "data/voxy_langgraph.db")

        self.orchestrator = get_langgraph_orchestrator(
            checkpointer_type=checkpointer_type,
            db_path=db_path,
        )

        # Log initialization summary
        self._log_system_summary()

    def _log_system_summary(self):
        """Log LangGraph system initialization summary."""
        from src.shared.config.models_config import load_vision_config

        vision_config = load_vision_config()

        logger.bind(event="STARTUP|LANGGRAPH_SYSTEM").info(
            "   \n"
            "   ✓ VOXY LangGraph System Initialized\n"
            f"      ├─ Orchestrator: LangGraph StateGraph\n"
            f"      ├─ Checkpointer: {self.orchestrator.checkpointer_type.value}\n"
            f"      ├─ DB Path: {self.orchestrator.db_path}\n"
            "      ├─ Subagents: 5 nodes (translator, corrector, weather, calculator, vision)\n"
            f"      ├─ Vision Model: {vision_config.get_litellm_model_path()}\n"
            f"      ├─ Vision Config: {vision_config.max_tokens} tokens, temp={vision_config.temperature}\n"
            "      └─ ✓ Ready"
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
            # Process through LangGraph orchestrator with session management
            result = await self.orchestrator.process_message(
                message=message,
                session_id=session_id,
                user_id=user_id,
                image_url=image_url,
            )

            # Extract response content and metadata
            response = result.get("content", "")

            # Build metadata compatible with FastAPI expectations
            metadata: dict[str, Any] = {
                "agent_type": "langgraph",
                "engine": "langgraph",
                "route_taken": result.get("route_taken"),
                "thread_id": result.get("thread_id"),
                "trace_id": result.get("trace_id"),
                "tools_used": result.get("tools_used", []),
                "usage": result.get("usage", {}),
                "vision_analysis": result.get("vision_analysis"),
                "user_id": user_id,
                "session_id": session_id,
            }

            return response, metadata

        except Exception as e:
            logger.bind(event="VOXY_SYSTEM|CHAT_ERROR").exception(
                "Error in VOXY LangGraph chat"
            )
            error_metadata: dict[str, str | list | None] = {
                "agent_type": "system_error",
                "engine": "langgraph",
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
        checkpointer_type_value = (
            self.orchestrator.checkpointer_type.value
            if isinstance(self.orchestrator.checkpointer_type, CheckpointerType)
            else self.orchestrator.checkpointer_type
        )
        return {
            "orchestrator_type": "langgraph",
            "checkpointer_type": checkpointer_type_value,
            "db_path": self.orchestrator.db_path,
            "subagents_count": 5,  # translator, corrector, weather, calculator, vision
            "system_status": "operational",
        }


# Global VOXY system instance - using lazy initialization
_voxy_system: VOXYSystem | None = None


def get_voxy_system(
    checkpointer_type: CheckpointerType = CheckpointerType.SQLITE,
    db_path: str | None = None,
) -> VOXYSystem:
    """
    Get the global VOXY system instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.

    Args:
        checkpointer_type: Type of checkpointer (only used on first call)
        db_path: Database path (only used on first call)

    Returns:
        VOXYSystem instance with LangGraph orchestration
    """
    global _voxy_system
    if _voxy_system is None:
        _voxy_system = VOXYSystem(
            checkpointer_type=checkpointer_type,
            db_path=db_path,
        )
    return _voxy_system


async def main():
    """
    Example usage of the VOXY system.
    Demonstrates the multi-agent capabilities with LangGraph.
    """
    print("🎯 VOXY Agents System - LangGraph Implementation")
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

    # Use a single session for conversation history
    session_id = "demo-session-123"

    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Usuário: {message}")

        try:
            voxy_system = get_voxy_system()
            response, metadata = await voxy_system.chat(
                message, user_id=f"test_user_{i}", session_id=session_id
            )
            print(f"   VOXY: {response}")
            print(f"   Engine: {metadata.get('engine', 'unknown')}")
            print(f"   Route: {metadata.get('route_taken', 'unknown')}")
            if metadata.get("tools_used"):
                print(f"   Tools: {', '.join(metadata['tools_used'])}")
            if metadata.get("usage"):
                usage = metadata["usage"]
                print(
                    f"   Tokens: {usage.get('total_tokens', 0)} "
                    f"(in: {usage.get('input_tokens', 0)}, "
                    f"out: {usage.get('output_tokens', 0)})"
                )
        except Exception as e:
            print(f"   Erro: {e}")

    # Show system statistics
    print("\n📊 Estatísticas do Sistema:")
    voxy_system = get_voxy_system()
    stats = voxy_system.get_system_stats()
    print(f"   - Tipo de orquestrador: {stats['orchestrator_type']}")
    print(f"   - Checkpointer: {stats['checkpointer_type']}")
    print(f"   - Database: {stats['db_path']}")
    print(f"   - Subagentes: {stats['subagents_count']}")
    print(f"   - Status: {stats['system_status']}")


if __name__ == "__main__":
    asyncio.run(main())
