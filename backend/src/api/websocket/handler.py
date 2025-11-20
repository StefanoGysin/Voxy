"""
WebSocket Message Handler

Handles incoming WebSocket messages and orchestrates responses.
Extracted from fastapi_server.py websocket_endpoint.
"""

import json
import uuid
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from voxy.main import get_voxy_system

from .manager import manager


async def handle_websocket_connection(
    websocket: WebSocket,
    user_id: str,
    user_email: str,
):
    """
    Handle WebSocket connection lifecycle and messages.

    Args:
        websocket: WebSocket connection instance
        user_id: Authenticated user ID from JWT
        user_email: User email from JWT
    """
    await manager.connect(websocket, user_id)

    # Send welcome message
    await manager.send_message(
        user_id,
        {
            "type": "connection",
            "message": "Conectado ao VOXY Agents System (authenticated)",
            "user_id": user_id,
            "email": user_email,
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
                await _handle_ping(user_id)
                continue

            # Handle chat messages
            await _handle_chat_message(user_id, message_data)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.bind(event="WEBSOCKET|DISCONNECT").info(
            "WebSocket client disconnected", user_id=user_id[:16]
        )
    except Exception as e:
        logger.bind(event="WEBSOCKET|ERROR").error(
            "WebSocket error", user_id=user_id[:16], error=str(e)
        )
        manager.disconnect(user_id)


async def _handle_ping(user_id: str):
    """Handle ping message with pong response."""
    await manager.send_message(
        user_id,
        {
            "type": "pong",
            "timestamp": datetime.now().isoformat(),
        },
    )


async def _handle_chat_message(user_id: str, message_data: dict):
    """
    Handle chat message from user.

    Args:
        user_id: User identifier
        message_data: Message dict with 'message', optional 'session_id', 'image_url'
    """
    # Send processing indicator
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
        # Extract data
        user_message = message_data["message"]
        frontend_session_id = message_data.get("session_id")
        image_url = message_data.get("image_url")

        # Determine session_id
        if frontend_session_id:
            session_id = frontend_session_id
            logger.bind(event="WEBSOCKET|SESSION").info(
                "Using frontend session_id", session_id=session_id
            )
        else:
            # Fallback: Generate session ID (UUID format for Supabase compatibility)
            session_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"voxy.session.{user_id}"))
            logger.bind(event="WEBSOCKET|SESSION").warning(
                "No session_id from frontend, using fallback", session_id=session_id
            )

        # Debug logging for image URL
        if image_url:
            logger.bind(event="WEBSOCKET|IMAGE").debug(
                "Image URL detected",
                message_preview=user_message[:50],
                image_url_length=len(image_url),
            )

        # Process with VOXY orchestrator
        logger.bind(event="WEBSOCKET|PROCESS").info(
            "Processing with LangGraph orchestrator",
            session_id=session_id,
            user_id=user_id[:16],
            has_image=bool(image_url),
        )

        voxy_system = get_voxy_system()
        response, metadata = await voxy_system.chat(
            message=user_message,
            user_id=user_id,
            session_id=session_id,
            image_url=image_url,
        )

        # Log response details
        logger.bind(event="WEBSOCKET|RESPONSE").info(
            "LangGraph response extracted",
            response_type=type(response).__name__,
            response_length=len(response) if response else 0,
            preview=response[:200] if response else "EMPTY",
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Prepare WebSocket message
        ws_message = {
            "type": "response",
            "message": response,
            "user_input": user_message,
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

        # Log outgoing message
        logger.bind(event="WEBSOCKET|SEND").info(
            "Sending WebSocket response",
            user_id=user_id[:16],
            message_length=len(ws_message["message"]) if ws_message["message"] else 0,
            processing_time=processing_time,
        )

        # Send response
        await manager.send_message(user_id, ws_message)

        logger.bind(event="WEBSOCKET|COMPLETE").info(
            "WebSocket message sent successfully",
            user_id=user_id[:16],
            chars_sent=len(ws_message["message"]) if ws_message["message"] else 0,
        )

    except Exception as e:
        logger.bind(event="WEBSOCKET|PROCESSING_ERROR").error(
            "Error processing WebSocket message", user_id=user_id[:16], error=str(e)
        )
        await manager.send_message(
            user_id,
            {
                "type": "error",
                "message": f"Erro ao processar mensagem: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            },
        )
