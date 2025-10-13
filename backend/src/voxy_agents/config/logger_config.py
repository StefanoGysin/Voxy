"""
Configuração central de logging com Loguru.
Baseado na documentação oficial: https://loguru.readthedocs.io/

Migração Loguru - Sprint 2: Implementação completa + Correções e Melhorias
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
        logger.bind(
            event="GENERAL",
            source=record.name  # uvicorn, litellm, httpx, etc.
        ).opt(
            depth=depth,
            exception=record.exc_info
        ).log(level, record.getMessage())


def setup_stdlib_intercept():
    """
    Configura InterceptHandler para capturar logs de bibliotecas stdlib.
    DEVE ser chamado ANTES de importar FastAPI/Uvicorn.
    """
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Interceptar loggers específicos de terceiros
    # Correção: Adicionar 'LiteLLM', 'httpx', 'httpcore' para reduzir ruído HTTP
    intercepted_loggers = [
        'uvicorn',
        'uvicorn.error',
        'uvicorn.access',
        'fastapi',
        'litellm',
        'LiteLLM',  # LiteLLM com L maiúsculo
        'httpx',
        'httpcore'
    ]

    for logger_name in intercepted_loggers:
        _logger = logging.getLogger(logger_name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

        # Reduzir ruído: loggers muito verbosos em DEBUG
        if logger_name in ('httpx', 'httpcore', 'litellm', 'LiteLLM'):
            _logger.setLevel(logging.WARNING)  # Só erros/avisos


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
    log_level = os.getenv("VOXY_LOG_LEVEL", "DEBUG" if env == "development" else "INFO")
    log_dir = Path(os.getenv("VOXY_LOG_DIR", "logs"))
    enable_json = os.getenv("VOXY_LOG_JSON", "false").lower() == "true"

    # Criar diretório de logs
    log_dir.mkdir(parents=True, exist_ok=True)

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

    # SINK 1: Console (desenvolvimento apenas)
    if env == "development":
        # diagnose=True apenas em dev para tracebacks ricos
        # source mostra origem de logs externos (uvicorn, litellm, etc.)
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[event]}</cyan> | <blue>{extra[source]}</blue> | {message}",
            level=log_level,
            colorize=True,
            enqueue=False,  # Console não precisa de enqueue
            diagnose=True,  # Tracebacks ricos em dev
            filter=mask_sensitive_data
        )

    # SINK 2: Arquivo principal (INFO em produção, log_level em dev)
    main_level = "INFO" if env == "production" else log_level

    logger.add(
        log_dir / "voxy_main.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[event]} | {message}",
        level=main_level,
        rotation="10 MB",
        retention=5,
        compression="zip",
        enqueue=True,  # CRÍTICO para async safety em produção
        filter=mask_sensitive_data
    )

    # SINK 3: Erros com diagnóstico (diagnose apenas em dev)
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
        filter=mask_sensitive_data
    )

    # SINK 4: Performance (isolado) - usa formatador custom
    logger.add(
        log_dir / "voxy_performance.log",
        format=_format_performance,
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
    sinks_count = 6 if enable_json else 5

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
        event="LOGGER_INIT",
        env=env,
        log_level=log_level,
        sinks=sinks_count
    ).info("Loguru configurado com sucesso")
