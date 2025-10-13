"""
Configuração central de logging com Loguru.
Baseado na documentação oficial: https://loguru.readthedocs.io/

Migração Loguru - Sprint 2: Implementação completa
"""
import sys
import os
import logging
import inspect
from pathlib import Path
from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Implementação oficial do Loguru para interceptar logs do stdlib.
    Captura logs de FastAPI, Uvicorn, LiteLLM e outras bibliotecas.

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

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_stdlib_intercept():
    """
    Configura InterceptHandler para capturar logs de bibliotecas stdlib.
    DEVE ser chamado ANTES de importar FastAPI/Uvicorn.
    """
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Interceptar loggers específicos de terceiros
    for logger_name in ['uvicorn', 'uvicorn.error', 'uvicorn.access', 'fastapi', 'litellm']:
        _logger = logging.getLogger(logger_name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False


def configure_logger():
    """
    Configuração principal do Loguru.
    Remove handlers padrão e adiciona sinks customizados.
    """
    # Ler configuração do ambiente
    env = os.getenv("VOXY_ENV", "development")
    log_level = os.getenv("VOXY_LOG_LEVEL", "DEBUG" if env == "development" else "INFO")
    log_dir = Path(os.getenv("VOXY_LOG_DIR", "logs"))
    enable_json = os.getenv("VOXY_LOG_JSON", "false").lower() == "true"

    # Criar diretório de logs
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remover handler padrão
    logger.remove()

    # Importar filtros
    from .log_filters import mask_sensitive_data

    # Patcher para adicionar event default
    def add_event_default(record):
        if "event" not in record["extra"]:
            record["extra"]["event"] = "GENERAL"
        return True

    # SINK 1: Console (desenvolvimento)
    if env == "development":
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[event]}</cyan> | {message}",
            level=log_level,
            colorize=True,
            enqueue=False,  # Console não precisa de enqueue
            filter=add_event_default
        )

    # SINK 2: Arquivo principal
    def combined_filter(record):
        add_event_default(record)
        return mask_sensitive_data(record)

    logger.add(
        log_dir / "voxy_main.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event]} | {message}",
        level="INFO",
        rotation="10 MB",
        retention=5,
        compression="zip",
        enqueue=True,  # CRÍTICO para async safety
        filter=combined_filter
    )

    # SINK 3: Erros com diagnóstico
    logger.add(
        log_dir / "voxy_error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event]} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention=10,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True if env == "development" else False,
        filter=combined_filter
    )

    # SINK 4: Performance (isolado)
    logger.add(
        log_dir / "voxy_performance.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[event]} | {extra[duration_ms]}ms | {extra[tokens]} tokens | ${extra[cost]}",
        level="DEBUG",
        filter=lambda record: "duration_ms" in record["extra"] or "cost" in record["extra"],
        rotation="50 MB",
        retention=10,
        compression="zip",
        enqueue=True
    )

    # SINK 5: Audit trail (90 dias de retenção)
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
        diagnose=False
    )

    # SINK 6: JSON estruturado (opcional)
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
            filter=mask_sensitive_data
        )

    # SINK 7: Sentry (se configurado)
    sentry_dsn = os.getenv("VOXY_LOG_SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from .sentry_sink import sentry_sink

            sentry_sdk.init(dsn=sentry_dsn, environment=env)
            logger.add(sentry_sink, level="ERROR")
        except ImportError:
            logger.warning("Sentry SDK não instalado - sink desabilitado")

    logger.bind(event="LOGGER_INIT").info(
        "Loguru configurado com sucesso",
        env=env,
        log_level=log_level,
        sinks=7 if sentry_dsn else 6
    )
