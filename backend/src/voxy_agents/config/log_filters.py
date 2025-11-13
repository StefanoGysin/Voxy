"""
Filtros de logging para mascaramento de dados sensíveis.
Conformidade: LGPD, GDPR

Migração Loguru - Sprint 2: Implementação completa
"""

import re

# Padrões de dados sensíveis
SENSITIVE_PATTERNS = {
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    "email": re.compile(r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"),
    "api_key_openrouter": re.compile(r"sk-or-v1-[a-zA-Z0-9]{10,}"),
    "api_key_openai": re.compile(r"sk-[a-zA-Z0-9]{10,}"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9_-]+", re.IGNORECASE),
    "authorization": re.compile(
        r"Authorization:\s*Bearer\s+[A-Za-z0-9_-]+", re.IGNORECASE
    ),
}


def mask_sensitive_data(record: dict) -> bool:
    """
    Filtra dados sensíveis de mensagens de log.

    Mascaramento aplicado:
    - JWT tokens → eyJ...[MASKED_JWT]
    - Emails → user***@domain.com
    - API keys → sk-...[MASKED]
    - Bearer tokens → Bearer [MASKED]

    Returns:
        bool: True para permitir o log (sempre retornar True para filtros de mascaramento)
    """
    message = record["message"]

    # Aplicar regex patterns
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if pattern_name == "jwt":
            message = pattern.sub(r"eyJ...[MASKED_JWT]", message)
        elif pattern_name == "email":
            # Preserva domínio, mascara usuário
            message = pattern.sub(r"***@\2", message)
        elif pattern_name.startswith("api_key"):
            message = pattern.sub(r"[MASKED_API_KEY]", message)
        else:
            message = pattern.sub(r"[MASKED]", message)

    # Mascarar campos 'extra' sensíveis
    if "extra" in record:
        sensitive_keys = [
            "password",
            "token",
            "api_key",
            "secret",
            "authorization",
            "bearer",
        ]
        for key in sensitive_keys:
            if key in record["extra"]:
                record["extra"][key] = "***MASKED***"

    record["message"] = message
    return True
