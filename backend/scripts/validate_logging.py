"""
Script de validação para cada fase da migração Loguru.
Uso: poetry run python scripts/validate_logging.py --phase 2
"""

import logging
import sys
from pathlib import Path

# Adicionar src ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def validate_phase_2_intercept():
    """Valida que InterceptHandler captura logs stdlib."""
    print("🔍 Validando Fase 2: InterceptHandler\n")

    # Configurar Loguru ANTES de testar
    from voxy_agents.config.logger_config import (
        configure_logger,
        setup_stdlib_intercept,
    )

    configure_logger()
    setup_stdlib_intercept()

    from loguru import logger

    # Capturar logs
    output = []
    handler_id = logger.add(output.append, format="{message}")

    # Emitir log via stdlib
    stdlib_logger = logging.getLogger("test_stdlib")
    stdlib_logger.info("Test message from stdlib")

    logger.remove(handler_id)

    captured = any("Test message from stdlib" in str(log) for log in output)

    print(f"{'✅' if captured else '❌'} Logs stdlib capturados pelo InterceptHandler")

    if not captured:
        print("\n❌ FALHA: InterceptHandler não está funcionando")
        print("Verifique:")
        print("  1. setup_stdlib_intercept() foi chamado ANTES de imports FastAPI?")
        print("  2. InterceptHandler.emit() está implementado corretamente?")

    return captured


def validate_phase_2_uvicorn():
    """Valida que logs do Uvicorn são capturados."""
    print("\n🔍 Testando captura Uvicorn logger\n")

    from loguru import logger

    output = []
    handler_id = logger.add(output.append, format="{message}")

    # Simular log do Uvicorn
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.info("Test uvicorn message")

    logger.remove(handler_id)

    captured = any("Test uvicorn message" in str(log) for log in output)

    print(f"{'✅' if captured else '❌'} Logs Uvicorn capturados")

    return captured


def validate_phase_2_masking():
    """Valida que dados sensíveis são mascarados."""
    print("\n🔍 Testando mascaramento de dados sensíveis\n")

    from loguru import logger
    from voxy_agents.config.log_filters import mask_sensitive_data

    output = []
    handler_id = logger.add(
        output.append, format="{message}", filter=mask_sensitive_data
    )

    # Testar vários padrões sensíveis
    logger.info(
        "API Key: sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd"
    )
    logger.info("JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature")
    logger.info("Email: user@example.com")
    logger.info("Bearer: Bearer abc123def456")

    logger.remove(handler_id)

    # Verificar mascaramento
    logs_text = " ".join(str(log) for log in output)

    masked_api = "[MASKED_API_KEY]" in logs_text and "sk-or-v1-" not in logs_text
    masked_jwt = "[MASKED_JWT]" in logs_text and "payload" not in logs_text
    masked_email = "***@example.com" in logs_text
    masked_bearer = "[MASKED]" in logs_text and "abc123" not in logs_text

    print(f"{'✅' if masked_api else '❌'} API keys mascaradas")
    print(f"{'✅' if masked_jwt else '❌'} JWT tokens mascarados")
    print(f"{'✅' if masked_email else '❌'} Emails mascarados")
    print(f"{'✅' if masked_bearer else '❌'} Bearer tokens mascarados")

    return all([masked_api, masked_jwt, masked_email, masked_bearer])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validar fases da migração Loguru")
    parser.add_argument("--phase", type=int, required=True, choices=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    if args.phase == 2:
        test1 = validate_phase_2_intercept()
        test2 = validate_phase_2_uvicorn()
        test3 = validate_phase_2_masking()

        success = test1 and test2 and test3

        print(f"\n{'✅ SPRINT 2 VALIDADO' if success else '❌ SPRINT 2 FALHOU'}")
        sys.exit(0 if success else 1)
