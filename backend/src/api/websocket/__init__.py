"""
WebSocket API for VOXY Agents

Real-time communication via WebSocket with JWT authentication.
Extracted from fastapi_server.py monolith.

Public API:
    - manager: Global ConnectionManager singleton
    - get_websocket_token: Auth dependency for WebSocket
    - MessageType: WebSocket message types enum
    - WebSocketMessage: Message model
"""

from .auth import get_websocket_token
from .manager import ConnectionManager, manager
from .models import ChatRequest, ChatResponse, MessageType, WebSocketMessage

__all__ = [
    "manager",
    "ConnectionManager",
    "get_websocket_token",
    "MessageType",
    "WebSocketMessage",
    "ChatRequest",
    "ChatResponse",
]
