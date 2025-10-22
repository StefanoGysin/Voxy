"""
Helper utilities para logging padronizado com Loguru.
Acelera migração com templates copiar/colar.

Migração Loguru - Sprint 1: Infraestrutura Base
"""

import inspect
import time
from functools import wraps

from loguru import logger


def create_component_logger(component_name: str):
    """
    Factory para criar logger especializado por componente.

    Uso:
        class TranslatorAgent:
            def __init__(self):
                self.logger = create_component_logger("TRANSLATOR_AGENT")
                self.logger.info("Agent initialized")

    Args:
        component_name: Nome do componente (UPPERCASE recomendado)

    Returns:
        Logger bound com component name no contexto extra
    """
    return logger.bind(component=component_name)


def log_performance(event_prefix: str):
    """
    Decorator para logar performance automaticamente.

    Loga automaticamente:
    - Início da operação (DEBUG)
    - Fim da operação com tempo de processamento (INFO)
    - Erros com tempo parcial (ERROR + exception)

    Uso:
        @log_performance("TRANSLATOR_AGENT")
        async def translate(self, text: str):
            # Performance auto-logged
            return result

    Args:
        event_prefix: Prefixo para eventos (ex: "TRANSLATOR_AGENT", "VISION_AGENT")
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()

            logger.bind(event=f"{event_prefix}|PROCESSING_START").debug(
                f"Iniciando {func.__name__}"
            )

            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start

                logger.bind(
                    event=f"{event_prefix}|PROCESSING_COMPLETE",
                    duration_ms=elapsed * 1000,
                ).info(f"{func.__name__} concluído", processing_time=f"{elapsed:.2f}s")

                return result
            except Exception:
                elapsed = time.perf_counter() - start
                logger.bind(
                    event=f"{event_prefix}|ERROR", duration_ms=elapsed * 1000
                ).exception(f"{func.__name__} falhou")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Versão síncrona (mesmo código)
            start = time.perf_counter()
            logger.bind(event=f"{event_prefix}|PROCESSING_START").debug(
                f"Iniciando {func.__name__}"
            )
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.bind(
                    event=f"{event_prefix}|PROCESSING_COMPLETE",
                    duration_ms=elapsed * 1000,
                ).info(f"{func.__name__} concluído", processing_time=f"{elapsed:.2f}s")
                return result
            except Exception:
                elapsed = time.perf_counter() - start
                logger.bind(
                    event=f"{event_prefix}|ERROR", duration_ms=elapsed * 1000
                ).exception(f"{func.__name__} falhou")
                raise

        # Detectar se função é async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class LoggedComponent:
    """
    Base class para componentes com logging integrado.

    Automaticamente cria self.logger bound com component_name.

    Uso:
        class TranslatorAgent(LoggedComponent):
            component_name = "TRANSLATOR_AGENT"

            async def translate(self, text: str):
                self.logger.info("Translating...")
                # logger já está disponível com component bound

    Attributes:
        component_name: Nome do componente (deve ser sobrescrito pela subclasse)
        logger: Logger instance bound com component_name
    """

    component_name: str = "UNKNOWN"

    def __init__(self):
        self.logger = logger.bind(component=self.component_name)
