"""
Configuração central de logging com Loguru.
Baseado na documentação oficial: https://loguru.readthedocs.io/

Migração Loguru - Sprint 2: Implementação completa + Correções e Melhorias
"""

import inspect
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load .env file BEFORE reading any environment variables
# override=True ensures .env values take precedence over shell exports
load_dotenv(override=True)


class InterceptHandler(logging.Handler):
    """
    Implementação oficial do Loguru para interceptar logs do stdlib.
    Captura logs de FastAPI, Uvicorn, LiteLLM e outras bibliotecas.

    Features:
    - Preserva contexto de origem (record.name armazenado em 'source')
    - Mantém padrão event="GENERAL" para logs externos
    - Rastreabilidade via campo 'source' (uvicorn, litellm, httpx, etc.)

    Fonte: https://loguru.readthedocs.io/en/stable/resources/migration.html
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        # Preservar contexto de origem via campo 'source'
        # Mantém padrão event="GENERAL" + rastreabilidade por source

        # Fix: Escape curly braces to prevent Loguru formatting errors
        # Mensagens interceptadas podem conter JSON (ex: hpack headers) com {, }, :
        # que o Loguru interpreta como format placeholders → ValueError/KeyError
        # Ref: https://loguru.readthedocs.io/en/stable/resources/troubleshooting.rst
        message = record.getMessage()
        escaped_message = message.replace("{", "{{").replace("}", "}}")

        logger.bind(
            event="GENERAL", source=record.name  # uvicorn, litellm, httpx, etc.
        ).opt(depth=depth, exception=record.exc_info).log(level, escaped_message)


def setup_stdlib_intercept():
    """
    Configura InterceptHandler para capturar logs de bibliotecas stdlib.
    DEVE ser chamado ANTES de importar FastAPI/Uvicorn.
    """
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Interceptar loggers específicos de terceiros
    # Correção: Adicionar 'LiteLLM', 'httpx', 'httpcore', 'hpack' para reduzir ruído HTTP
    intercepted_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "litellm",
        "LiteLLM",  # LiteLLM com L maiúsculo
        "LiteLLM Proxy",  # LiteLLM Proxy warnings (backoff dependency)
        "httpx",
        "httpcore",
        "hpack",  # HTTP/2 header compression (muito verboso em DEBUG)
        "hpack.hpack",
    ]

    for logger_name in intercepted_loggers:
        _logger = logging.getLogger(logger_name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

        # Reduzir ruído: loggers muito verbosos em DEBUG
        if logger_name in (
            "httpx",
            "httpcore",
            "litellm",
            "LiteLLM",
            "LiteLLM Proxy",
            "hpack",
            "hpack.hpack",
        ):
            _logger.setLevel(logging.ERROR)  # Só erros críticos


def _format_performance(record):
    """
    Formatador custom para sink de performance.
    Usa .get() para evitar KeyError quando faltarem campos.
    """
    extra = record["extra"]
    duration = extra.get("duration_ms", "N/A")
    tokens = extra.get("tokens", "N/A")
    cost = extra.get("cost", "N/A")

    time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    event = extra.get("event", "UNKNOWN")

    return f"{time_str} | {event} | {duration}ms | {tokens} tokens | ${cost}\n"


def configure_logger():
    """
    Configuração principal do Loguru.
    Remove handlers padrão e adiciona sinks customizados.

    Melhorias:
    - Usa patcher ao invés de filter repetido
    - Separa configurações por ambiente
    - Formatador custom para performance sink
    """
    # Ler configuração do ambiente
    env = os.getenv("VOXY_ENV", "development")
    log_level_str = os.getenv(
        "VOXY_LOG_LEVEL", "DEBUG" if env == "development" else "INFO"
    )
    log_dir = Path(os.getenv("VOXY_LOG_DIR", "logs"))
    enable_json = os.getenv("VOXY_LOG_JSON", "false").lower() == "true"

    # Converter para variável global acessível nos filtros
    is_debug_mode = log_level_str == "DEBUG"

    # Criar diretório de logs
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log informativo do path absoluto (para debugging)
    # Imprime ANTES de remover o handler padrão para garantir visibilidade
    abs_log_path = log_dir.absolute()
    print(f"[Loguru Init] Log files directory: {abs_log_path}")

    # Remover handler padrão
    logger.remove()

    # Importar filtros
    from .log_filters import mask_sensitive_data

    # Patcher para adicionar defaults (executa uma vez por log)
    def add_defaults_patcher(record):
        if "event" not in record["extra"]:
            record["extra"]["event"] = "GENERAL"
        if "source" not in record["extra"]:
            record["extra"]["source"] = ""  # Empty for internal logs

    # Configurar patcher global (melhoria: evita executar filter múltiplas vezes)
    logger.configure(patcher=add_defaults_patcher)

    # Formatador custom para logs de startup (visual limpo em produção)
    def _format_startup_visual(record):
        """
        Formatador condicional para logs STARTUP.

        - DEBUG mode: Mostra cabeçalho completo (rastreamento técnico)
        - INFO/WARNING/ERROR: Omite cabeçalho, só conteúdo visual (limpo)
        """
        event = record["extra"].get("event", "")

        # Se for evento STARTUP e não estiver em DEBUG, omitir cabeçalho
        if event.startswith("STARTUP|") and not is_debug_mode:
            # Visual limpo: apenas a mensagem
            return record["message"] + "\n"

        # Formato completo com cabeçalho (DEBUG mode ou eventos não-STARTUP)
        # Usar formato string do Loguru com tags de cor
        time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record["level"].name
        event_display = record["extra"].get("event", "GENERAL")
        source = record["extra"].get("source", "")
        message = record["message"]

        # Formato com tags do Loguru (processadas automaticamente quando colorize=True)
        if source:
            return f"<green>{time_str}</green> | <level>{level: <8}</level> | <cyan>{event_display}</cyan> | <blue>{source}</blue> | {message}\n"
        else:
            return f"<green>{time_str}</green> | <level>{level: <8}</level> | <cyan>{event_display}</cyan> | {message}\n"

    # Filtro para logs técnicos em modo INFO (voxy_main.log + console limpos)
    def _filter_clean_logs(record):
        """
        Filtra eventos técnicos em modo INFO para manter voxy_main.log limpo.

        Eventos filtrados (só aparecem em DEBUG):
        - REASONING_CONFIG|* (config loading técnico)
        - GENERAL (logs de bibliotecas externas como uvicorn)
        - LOGGER_INIT (inicialização do próprio logger)
        - VOXY_ORCHESTRATOR|REASONING_CONFIG (config do orchestrator)

        Em DEBUG mode: todos os eventos passam (return True)
        Em INFO mode: eventos técnicos são filtrados (return False)
        """
        if is_debug_mode:
            # DEBUG mode: mostrar tudo
            return True

        # INFO mode: filtrar eventos técnicos
        event = record["extra"].get("event", "GENERAL")

        # Lista de prefixos de eventos técnicos para filtrar
        technical_events = [
            "REASONING_CONFIG",  # Config loading (TRANSLATOR_LOADED, etc.)
            "GENERAL",  # Logs externos (uvicorn, litellm, etc.)
            "LOGGER_INIT",  # Inicialização do logger
        ]

        # Filtros específicos adicionais
        # VOXY_ORCHESTRATOR|REASONING_CONFIG (não todo VOXY_ORCHESTRATOR|*)
        if event == "VOXY_ORCHESTRATOR|REASONING_CONFIG":
            return False

        # Filtrar eventos técnicos
        for tech_event in technical_events:
            if event.startswith(tech_event):
                return False  # Não mostrar em INFO mode

        # Passar todos os outros eventos importantes
        return True

    # Filtro combinado para console e voxy_main.log (mask + clean logs)
    def _combined_filter(record):
        """Combina filtro de dados sensíveis + filtro de logs técnicos."""
        return mask_sensitive_data(record) and _filter_clean_logs(record)

    # SINK 1: Console (desenvolvimento apenas)
    if env == "development":
        # diagnose=True apenas em dev para tracebacks ricos
        # Formatador custom omite cabeçalho em STARTUP quando não está em DEBUG
        # Filtro aplicado: logs limpos em INFO, completos em DEBUG
        logger.add(
            sys.stdout,
            format=_format_startup_visual,  # Custom formatter
            level=log_level_str,
            colorize=True,
            enqueue=False,  # Console não precisa de enqueue
            diagnose=True,  # Tracebacks ricos em dev
            filter=_combined_filter,  # Filtro duplo (mask + clean)
        )

    # Formatador custom para voxy_main.log (logs limpos em INFO)
    def _format_main_log(record):
        """
        Formatador condicional para voxy_main.log.

        - DEBUG mode: Mostra event prefix completo (e.g., STARTUP|SUBAGENTS)
        - INFO/WARNING/ERROR: Omite event prefix (logs limpos)

        Exemplo:
        DEBUG: 2025-11-08 04:47:09.512 | INFO | STARTUP|SUBAGENTS | 📦 Registering...
        INFO:  2025-11-08 04:47:09.512 | INFO | 📦 Registering...
        """
        time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record["level"].name
        event = record["extra"].get("event", "GENERAL")
        message = record["message"]

        # Se estiver em DEBUG mode, mostrar event prefix
        if is_debug_mode:
            return f"{time_str} | {level: <8} | {event} | {message}\n"
        else:
            # INFO mode: logs limpos sem event prefix
            return f"{time_str} | {level: <8} | {message}\n"

    # SINK 2: Arquivo principal (INFO em produção, log_level em dev)
    # Logs limpos sem event prefixes quando VOXY_LOG_LEVEL=INFO
    # Filtro duplo: mask_sensitive_data + _filter_clean_logs
    main_level = "INFO" if env == "production" else log_level_str

    logger.add(
        log_dir / "voxy_main.log",
        format=_format_main_log,  # Formatador custom (clean logs em INFO)
        level=main_level,
        rotation="10 MB",
        retention=5,
        compression="zip",
        enqueue=True,  # CRÍTICO para async safety em produção
        filter=_combined_filter,  # Filtro duplo
    )

    # SINK 3: Arquivo DEBUG (sempre ativo, independente de VOXY_LOG_LEVEL)
    # Captura TODOS os logs em nível DEBUG com event prefixes completos
    # Útil para troubleshooting sem mudar VOXY_LOG_LEVEL
    logger.add(
        log_dir / "voxy_debug.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event]} | {message}",
        level="DEBUG",  # Sempre DEBUG
        rotation="25 MB",  # Maior pois captura mais logs
        retention=3,  # Menos retenção (volume maior)
        compression="zip",
        enqueue=True,
        filter=mask_sensitive_data,
    )

    # SINK 4: Erros com diagnóstico (diagnose apenas em dev)
    logger.add(
        log_dir / "voxy_error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event]} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention=10,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=env == "development",  # Apenas em dev para evitar expor info sensível
        filter=mask_sensitive_data,
    )

    # SINK 5: Performance (isolado) - usa formatador custom
    logger.add(
        log_dir / "voxy_performance.log",
        format=_format_performance,
        level="DEBUG",
        filter=lambda record: "duration_ms" in record["extra"]
        or "cost" in record["extra"],
        rotation="50 MB",
        retention=10,
        compression="zip",
        enqueue=True,
    )

    # SINK 6: Audit trail (90 dias de retenção)
    logger.add(
        log_dir / "voxy_audit.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[event]} | {extra[user_id]} | {extra[action]} | {message}",
        level="INFO",
        filter=lambda record: record["extra"].get("event", "").startswith("AUDIT_"),
        rotation="100 MB",
        retention="90 days",  # Compliance regulatório
        compression="zip",
        enqueue=True,
        backtrace=False,  # Não expor stack traces em audit
        diagnose=False,
    )

    # SINK 7: JSON estruturado (opcional)
    if enable_json:
        logger.add(
            log_dir / "voxy_structured.json",
            format="{message}",
            level="INFO",
            rotation="100 MB",
            retention=7,
            compression="zip",
            serialize=True,
            enqueue=True,
            filter=mask_sensitive_data,
        )

    # SINK 8: Sentry (se configurado)
    sentry_dsn = os.getenv("VOXY_LOG_SENTRY_DSN")
    # Atualizado: agora temos 7 sinks base (console, main, debug, error, perf, audit, json)
    sinks_count = 7 if enable_json else 6

    if sentry_dsn:
        try:
            import sentry_sdk

            from .sentry_sink import sentry_sink

            sentry_sdk.init(dsn=sentry_dsn, environment=env)
            logger.add(sentry_sink, level="ERROR")
            sinks_count += 1
        except ImportError:
            logger.warning("Sentry SDK não instalado - sink desabilitado")

    # Log de inicialização (correção: metadados agora aparecem via bind)
    logger.bind(
        event="LOGGER_INIT", env=env, log_level=log_level_str, sinks=sinks_count
    ).info("Loguru configurado com sucesso")
