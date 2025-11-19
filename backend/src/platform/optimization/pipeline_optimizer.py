"""
Pipeline Optimizer for Vision Agent

Remove overhead desnecessário identificado nos logs:
- Múltiplas chamadas de function_call vazias
- Processamento de conteúdo vazio
- Session validation redundante
- Steps desnecessários no pipeline

Baseado na análise que identificou 40s de overhead em análise de 48s.
"""

import asyncio
import functools
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PipelineOptimizer:
    """
    Otimizador de pipeline para reduzir overhead desnecessário.

    Features:
    - Skip de validações redundantes
    - Batching de operações similares
    - Lazy loading de recursos
    - Pipeline caching para operações custosas
    """

    def __init__(self):
        self.validation_cache = {}  # Cache para validações
        self.session_cache = {}  # Cache para sessões validadas
        self.operation_stats = {}  # Estatísticas de operações

    def skip_redundant_validations(self, func: Callable) -> Callable:
        """Decorator para pular validações redundantes."""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache para validação
            cache_key = self._generate_validation_key(func.__name__, args, kwargs)

            # Verificar se validação já foi feita recentemente
            if cache_key in self.validation_cache:
                last_validation, result = self.validation_cache[cache_key]
                if (
                    datetime.now() - last_validation
                ).total_seconds() < 300:  # 5 minutos
                    logger.debug(f"⚡ Skipping redundant validation: {func.__name__}")
                    return result

            # Executar validação e cachear resultado
            start_time = datetime.now()
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()

            self.validation_cache[cache_key] = (datetime.now(), result)

            # Log apenas se demorou mais que 100ms
            if duration > 0.1:
                logger.info(f"⏱️ Validation {func.__name__}: {duration:.3f}s")

            return result

        return wrapper

    def batch_similar_operations(self, batch_size: int = 5, timeout: float = 0.1):
        """Decorator para fazer batch de operações similares."""

        def decorator(func: Callable) -> Callable:
            batch_queue = []
            last_batch_time = datetime.now()

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                nonlocal batch_queue, last_batch_time

                # Adicionar operação ao batch
                operation = (args, kwargs, asyncio.Future())
                batch_queue.append(operation)

                # Verificar se deve processar batch
                time_since_last = (datetime.now() - last_batch_time).total_seconds()
                should_process = (
                    len(batch_queue) >= batch_size or time_since_last > timeout
                )

                if should_process:
                    current_batch = batch_queue.copy()
                    batch_queue.clear()
                    last_batch_time = datetime.now()

                    # Processar batch
                    await self._process_batch(func, current_batch)

                # Retornar resultado da operação atual
                return await operation[2]

            return wrapper

        return decorator

    async def _process_batch(self, func: Callable, batch: list[tuple]):
        """Processa batch de operações."""
        try:
            start_time = datetime.now()

            # Executar todas as operações do batch
            tasks = []
            for args, kwargs, future in batch:
                task = asyncio.create_task(func(*args, **kwargs))
                tasks.append((task, future))

            # Aguardar todas as operações
            for task, future in tasks:
                try:
                    result = await task
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"⚡ Processed batch of {len(batch)} operations in {duration:.3f}s"
            )

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            # Set exception em todos os futures
            for _, _, future in batch:
                if not future.done():
                    future.set_exception(e)

    @asynccontextmanager
    async def lazy_resource_loading(self, resource_name: str):
        """Context manager para lazy loading de recursos."""
        resource = None
        try:
            logger.debug(f"⚡ Lazy loading resource: {resource_name}")

            # Simular carregamento de recurso apenas quando necessário
            if resource_name not in self.session_cache:
                start_time = datetime.now()
                # Aqui seria o carregamento real do recurso
                await asyncio.sleep(0.001)  # Simular operação
                duration = (datetime.now() - start_time).total_seconds()

                self.session_cache[resource_name] = {
                    "loaded_at": datetime.now(),
                    "data": f"resource_{resource_name}",
                }

                logger.debug(f"⚡ Loaded resource {resource_name} in {duration:.3f}s")

            resource = self.session_cache[resource_name]
            yield resource

        except Exception as e:
            logger.error(f"Resource loading error for {resource_name}: {e}")
            raise
        finally:
            # Cleanup se necessário
            pass

    def skip_empty_content_processing(self, func: Callable) -> Callable:
        """Decorator para pular processamento de conteúdo vazio."""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Verificar se há conteúdo para processar
            content = kwargs.get("content") or (args[0] if args else None)

            if not content or (isinstance(content, str) and not content.strip()):
                logger.debug(f"⚡ Skipping empty content processing: {func.__name__}")
                return None

            # Verificar se conteúdo é só espaços em branco
            if isinstance(content, str) and len(content.strip()) == 0:
                logger.debug(f"⚡ Skipping whitespace-only content: {func.__name__}")
                return None

            return await func(*args, **kwargs)

        return wrapper

    def measure_operation_time(self, operation_name: str):
        """Decorator para medir tempo de operações e identificar gargalos."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = datetime.now()

                try:
                    result = await func(*args, **kwargs)

                    duration = (datetime.now() - start_time).total_seconds()

                    # Atualizar estatísticas
                    if operation_name not in self.operation_stats:
                        self.operation_stats[operation_name] = {
                            "total_calls": 0,
                            "total_time": 0.0,
                            "max_time": 0.0,
                            "min_time": float("inf"),
                            "avg_time": 0.0,
                        }

                    stats = self.operation_stats[operation_name]
                    stats["total_calls"] += 1
                    stats["total_time"] += duration
                    stats["max_time"] = max(stats["max_time"], duration)
                    stats["min_time"] = min(stats["min_time"], duration)
                    stats["avg_time"] = stats["total_time"] / stats["total_calls"]

                    # Log apenas operações que demoram mais que threshold
                    if duration > 0.1:  # 100ms
                        logger.info(
                            f"⏱️ {operation_name}: {duration:.3f}s (avg: {stats['avg_time']:.3f}s)"
                        )

                    return result

                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    logger.error(
                        f"❌ {operation_name} failed after {duration:.3f}s: {e}"
                    )
                    raise

            return wrapper

        return decorator

    def _generate_validation_key(
        self, func_name: str, args: tuple, kwargs: dict
    ) -> str:
        """Gera chave única para cache de validação."""
        import hashlib

        # Serializar argumentos relevantes (ignorar objetos complexos)
        serializable_args = []
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                serializable_args.append(str(arg))

        serializable_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool)):
                serializable_kwargs[k] = str(v)

        cache_data = f"{func_name}|{serializable_args}|{serializable_kwargs}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def get_optimization_stats(self) -> dict[str, Any]:
        """Retorna estatísticas de otimização."""
        return {
            "validation_cache_size": len(self.validation_cache),
            "session_cache_size": len(self.session_cache),
            "operation_stats": self.operation_stats,
            "total_operations_tracked": sum(
                stats["total_calls"] for stats in self.operation_stats.values()
            ),
            "total_time_measured": sum(
                stats["total_time"] for stats in self.operation_stats.values()
            ),
        }

    async def cleanup_expired_caches(self) -> None:
        """Remove entradas expiradas dos caches."""
        try:
            now = datetime.now()

            # Limpar cache de validação (5 minutos)
            expired_validations = []
            for key, (timestamp, _) in self.validation_cache.items():
                if (now - timestamp).total_seconds() > 300:
                    expired_validations.append(key)

            for key in expired_validations:
                del self.validation_cache[key]

            # Limpar cache de sessão (30 minutos)
            expired_sessions = []
            for key, data in self.session_cache.items():
                if (now - data["loaded_at"]).total_seconds() > 1800:
                    expired_sessions.append(key)

            for key in expired_sessions:
                del self.session_cache[key]

            if expired_validations or expired_sessions:
                logger.info(
                    f"🧹 Cleaned optimization caches: {len(expired_validations)} validations, "
                    f"{len(expired_sessions)} sessions"
                )

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


# Global instance
pipeline_optimizer = PipelineOptimizer()
