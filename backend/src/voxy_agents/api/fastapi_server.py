"""
FastAPI Server for VOXY Agents System

Provides REST API and WebSocket endpoints for the VOXY multi-agent system.
Implements Progressive Disclosure Interface from CREATIVE MODE decisions.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from ..langgraph_main import get_voxy_system
from .middleware.auth import TokenData
from .middleware.logging_context import LoggingContextMiddleware
from .routes import auth_router, chat_router, images_router, sessions_router
from .routes.messages import router as messages_router

# NOTE: Test router disabled during LangGraph migration (SDK-specific)
# from .routes.test import router as test_router

# Pydantic models for API - Chat models moved to routes/chat.py
# Kept only system-level models here


class SystemStatus(BaseModel):
    status: str
    subagents_count: int
    version: str = "0.1.0"
    uptime: float


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected: {user_id}")

    async def send_message(self, user_id: str, message: dict):
        """Send message to specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected.append(user_id)

        # Clean up disconnected clients
        for user_id in disconnected:
            self.disconnect(user_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    import time

    startup_start = time.perf_counter()

    # Startup
    logger.bind(event="STARTUP|BEGIN").info("🚀 VOXY Agents System Initializing...")

    # Initialize VOXY system once during startup
    voxy_system = get_voxy_system()
    app.state.voxy_system = voxy_system

    # Calculate timing
    elapsed = time.perf_counter() - startup_start

    # Get orchestrator model path dynamically from environment
    from ..config.models_config import load_orchestrator_config

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


# Global instances
app = FastAPI(
    title="VOXY Agents API",
    description="Sistema multi-agente inteligente com OpenAI Agents SDK",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

manager = ConnectionManager()
start_time = datetime.now()

# Logging Context Middleware - DEVE vir ANTES do CORS para capturar tudo
app.add_middleware(LoggingContextMiddleware)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Example frontend
        "http://127.0.0.1:3001",  # Example frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers - Refactored structure
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(images_router, prefix="/api")
# NOTE: Test router disabled during LangGraph migration (SDK-specific)
# app.include_router(test_router, prefix="/api")  # Subagent testing endpoints


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "VOXY Agents API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", response_model=SystemStatus)
async def health_check():
    """System health check endpoint."""
    uptime = (datetime.now() - start_time).total_seconds()
    voxy_system = get_voxy_system()
    stats = voxy_system.get_system_stats()

    return SystemStatus(
        status=stats["system_status"],
        subagents_count=stats["subagents_count"],
        uptime=uptime,
    )


# REMOVED: Public chat endpoint for security consolidation
# All chat functionality now requires authentication via /api/chat/
# This eliminates architectural duplication and enforces security policy


@app.get("/stats")
async def get_stats():
    """Get detailed system statistics."""
    voxy_system = get_voxy_system()
    stats = voxy_system.get_system_stats()
    uptime = (datetime.now() - start_time).total_seconds()

    return {
        **stats,
        "uptime_seconds": uptime,
        "active_connections": len(manager.active_connections),
        "server_start_time": start_time.isoformat(),
    }


async def get_websocket_token(
    websocket: WebSocket, token: Optional[str] = Query(None)
) -> TokenData:
    """
    Mandatory WebSocket authentication dependency.
    Validates JWT token and returns TokenData or closes connection with 1008 (Policy Violation).
    """
    if not token:
        logger.warning(
            "🚫 WebSocket connection rejected: No authentication token provided"
        )
        await websocket.close(code=1008, reason="Authentication required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required for WebSocket connection",
        )

    try:
        logger.info(
            f"🔐 Attempting WebSocket JWT validation for token: {token[:20]}..."
        )

        # Use the same verification as the rest of the API
        from .middleware.auth import verify_token

        token_data = await verify_token(token)

        logger.info(
            f"✅ WebSocket authenticated user: {token_data.user_id} ({token_data.email})"
        )
        return token_data
    except HTTPException as e:
        logger.warning(f"🚫 WebSocket authentication failed: {e.detail}")
        await websocket.close(code=1008, reason=f"Authentication failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ WebSocket authentication error: {e}")
        await websocket.close(code=1008, reason="Authentication error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token_data: TokenData = Depends(get_websocket_token),
):
    """
    WebSocket endpoint for real-time communication.

    Implements Progressive Disclosure Interface from CREATIVE MODE.
    Requires mandatory JWT authentication via query parameter.

    Security: Validates that URL user_id matches authenticated token user_id.
    """
    # Validate that URL user_id matches authenticated token user_id
    if user_id != token_data.user_id:
        logger.warning(
            f"🚫 WebSocket user_id mismatch: URL={user_id}, Token={token_data.user_id}"
        )
        await websocket.close(
            code=1008,
            reason="User ID mismatch: URL user_id must match authenticated token",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in URL does not match authenticated user",
        )

    await manager.connect(websocket, user_id)

    # Send welcome message with authenticated user info
    await manager.send_message(
        user_id,
        {
            "type": "connection",
            "message": "Conectado ao VOXY Agents System (authenticated)",
            "user_id": user_id,
            "email": token_data.email,
            "authenticated": True,
            "timestamp": datetime.now().isoformat(),
        },
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle ping messages
            if message_data.get("type") == "ping":
                await manager.send_message(
                    user_id,
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                continue

            # Send processing indicator for chat messages
            await manager.send_message(
                user_id,
                {
                    "type": "processing",
                    "message": "VOXY está processando...",
                    "timestamp": datetime.now().isoformat(),
                },
            )

            start_time = datetime.now()

            try:
                # Use session_id from frontend if provided, otherwise generate fallback
                frontend_session_id = message_data.get("session_id")
                image_url = message_data.get(
                    "image_url"
                )  # Extract image URL for Vision Agent

                if frontend_session_id:
                    session_id = frontend_session_id
                    logger.info(f"🎯 Using frontend session_id: {session_id}")
                else:
                    # Fallback: Generate session ID for this user (UUID format for Supabase compatibility)
                    import uuid

                    session_id = str(
                        uuid.uuid5(uuid.NAMESPACE_DNS, f"voxy.session.{user_id}")
                    )
                    logger.warning(
                        f"⚠️  No session_id from frontend, using fallback: {session_id}"
                    )

                # Debug logging for image URL
                print(
                    f"🔍 FastAPI WebSocket DEBUG - message='{message_data['message']}', image_url='{image_url}'"
                )

                # LangGraph orchestrator (default and only engine)
                logger.bind(event="WEBSOCKET|ENGINE").info(
                    "🎯 WebSocket using LangGraph orchestrator",
                    session_id=session_id,
                    user_id=user_id,
                )

                voxy_system = get_voxy_system()
                response, metadata = await voxy_system.chat(
                    message=message_data["message"],
                    user_id=user_id,
                    session_id=session_id,
                    image_url=image_url,
                )

                # Log response details for debugging
                logger.bind(event="WEBSOCKET|RESPONSE_DEBUG").info(
                    f"🔍 LangGraph response extracted: "
                    f"type={type(response).__name__}, "
                    f"length={len(response) if response else 0}, "
                    f"preview={response[:200] if response else 'EMPTY'}..."
                )

                processing_time = (datetime.now() - start_time).total_seconds()

                # Prepare WebSocket message
                ws_message = {
                    "type": "response",
                    "message": response,
                    "user_input": message_data["message"],
                    "session_id": session_id,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "engine": metadata.get("engine", "langgraph"),
                        "route_taken": metadata.get("route_taken"),
                        "thread_id": metadata.get("thread_id"),
                        "trace_id": metadata.get("trace_id"),
                    },
                }

                # CRITICAL DEBUG: Log message being sent (INFO level to always show)
                logger.bind(event="WEBSOCKET|SEND_DEBUG").info(
                    f"📤 Sending WebSocket: "
                    f"user={user_id}, "
                    f"type={ws_message['type']}, "
                    f"msg_length={len(ws_message['message']) if ws_message['message'] else 0}, "
                    f"preview={ws_message['message'][:200] if ws_message['message'] else 'EMPTY'}..."
                )

                # Send response with session_id and metadata for frontend tracking
                await manager.send_message(user_id, ws_message)

                logger.bind(event="WEBSOCKET|SEND_COMPLETE").info(
                    f"✅ WebSocket message sent: {len(ws_message['message']) if ws_message['message'] else 0} chars",
                    user_id=user_id,
                    processing_time=processing_time,
                )

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_message(
                    user_id,
                    {
                        "type": "error",
                        "message": f"Erro ao processar mensagem: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WebSocket client {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
        manager.disconnect(user_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.voxy_agents.api.fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
