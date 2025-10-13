"""
Middleware FastAPI para propagação automática de contexto de logging.

Migração Loguru - Sprint 3: Context Propagation
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from loguru import logger


class LoggingContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que adiciona contexto automático a todos os logs durante uma request.

    Contexto propagado:
    - trace_id: UUID único da request (ou header X-Trace-ID)
    - user_id: ID do usuário autenticado (se disponível)
    - path: Caminho da URL
    - method: Método HTTP
    """

    async def dispatch(self, request: Request, call_next):
        # Gerar ou extrair trace_id
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())[:8]

        # Extrair user_id se disponível no request.state
        user_id = getattr(request.state, "user_id", None)

        # Auto-bind contexto para TODOS os logs durante esta request
        with logger.contextualize(
            trace_id=trace_id,
            user_id=user_id,
            path=request.url.path,
            method=request.method
        ):
            logger.bind(event="HTTP_REQUEST_START").info(
                "Request iniciado"
            )

            try:
                response = await call_next(request)

                logger.bind(event="HTTP_REQUEST_END").info(
                    "Request concluído",
                    status_code=response.status_code
                )

                # Adicionar trace_id ao response header para rastreamento
                response.headers["X-Trace-ID"] = trace_id
                return response

            except Exception as e:
                logger.bind(event="HTTP_REQUEST_ERROR").exception(
                    "Request falhou com exceção"
                )
                raise
