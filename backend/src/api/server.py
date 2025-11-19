"""
FastAPI Application Server - VOXY Agents

Clean, modular FastAPI application.
Extracted from voxy_agents/api/fastapi_server.py (monolith).

Architecture:
    - Lifespan: Startup/shutdown events
    - Middleware: CORS, Logging
    - Routes: Auth, Chat, Sessions, Messages, Images
    - WebSocket: /ws/{user_id} endpoint
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from voxy_agents.api.middleware.logging_context import LoggingContextMiddleware
from voxy_agents.api.routes import (
    auth as auth_router,
    chat as chat_router,
    images as images_router,
    messages as messages_router,
    sessions as sessions_router,
)
from voxy_agents.config.models_config import load_orchestrator_config
from voxy_agents.langgraph_main import get_voxy_system

from .websocket import get_websocket_token, handle_websocket_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    startup_start = time.perf_counter()

    # Startup
    logger.bind(event="STARTUP|BEGIN").info("🚀 VOXY Agents System Initializing...")

    # Initialize VOXY system once during startup
    voxy_system = get_voxy_system()
    app.state.voxy_system = voxy_system

    # Calculate timing
    elapsed = time.perf_counter() - startup_start

    # Get orchestrator model path dynamically from environment
    orchestrator_config = load_orchestrator_config()
    orchestrator_model = orchestrator_config.get_litellm_model_path()

    # Startup summary
    logger.bind(event="STARTUP|COMPLETE").info(
        f"\n"
        f"✅ VOXY System Ready\n"
        f"   ├─ Total time: {elapsed:.2f}s\n"
        f"   ├─ Redis: Connected\n"
        f"   ├─ Subagents: 5 registered (translator, corrector, weather, calculator, vision)\n"
        f"   ├─ Orchestrator: {orchestrator_model}\n"
        f"   └─ Listening: http://0.0.0.0:8000"
    )

    yield

    # Shutdown
    logger.bind(event="SHUTDOWN").info("🛑 VOXY Agents API Server shutting down...")


# FastAPI application
app = FastAPI(
    title="VOXY Agents API",
    description="Sistema multi-agente inteligente com LangGraph",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Track startup time
start_time = datetime.now()

# Middleware (order matters!)
# 1. Logging Context Middleware - MUST come BEFORE CORS to capture everything
app.add_middleware(LoggingContextMiddleware)

# 2. CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(chat_router.router, prefix="/api")
app.include_router(sessions_router.router, prefix="/api")
app.include_router(messages_router.router, prefix="/api")
app.include_router(images_router.router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "VOXY Agents API",
        "version": "0.2.0",
        "status": "operational",
        "docs": "/docs",
        "architecture": "clean",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check endpoint."""
    uptime = (datetime.now() - start_time).total_seconds()
    voxy_system = get_voxy_system()
    stats = voxy_system.get_system_stats()

    return {
        "status": stats["system_status"],
        "subagents_count": stats["subagents_count"],
        "uptime": uptime,
        "version": "0.2.0",
    }


# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token_data=Depends(get_websocket_token),
):
    """
    WebSocket endpoint for real-time communication.
    
    Requires JWT authentication via query parameter: /ws/{user_id}?token=<jwt>
    Validates that URL user_id matches authenticated token user_id.
    """
    # Validate user_id matches token
    if user_id != token_data.user_id:
        logger.bind(event="WEBSOCKET|AUTH_MISMATCH").warning(
            "User ID mismatch",
            url_user_id=user_id,
            token_user_id=token_data.user_id
        )
        await websocket.close(
            code=1008,
            reason="User ID mismatch: URL user_id must match authenticated token",
        )
        return

    # Handle connection
    await handle_websocket_connection(
        websocket=websocket,
        user_id=user_id,
        user_email=token_data.email,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
