"""
WebSocket Message Models

Pydantic models for WebSocket communication.
Extracted from voxy_agents/api/routes/chat.py.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MessageType(str, Enum):
    """WebSocket message types."""

    CHAT = "chat"
    RESPONSE = "response"
    PROCESSING = "processing"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    SYSTEM = "system"
    VISION = "vision"


class WebSocketMessage(BaseModel):
    """
    WebSocket message model with vision support.

    Used for both incoming (user) and outgoing (assistant) messages.
    """

    type: str  # MessageType enum value
    message: str
    session_id: Optional[str] = None
    image_url: Optional[str] = None  # For vision analysis requests
    vision_metadata: Optional[dict] = None  # Vision analysis metadata


class ChatRequest(BaseModel):
    """User chat request via WebSocket."""

    message: str
    session_id: Optional[str] = None
    image_url: Optional[str] = None


class ChatResponse(BaseModel):
    """Assistant chat response via WebSocket."""

    type: str = MessageType.RESPONSE
    message: str
    session_id: str
    usage: Optional[dict] = None
    metadata: Optional[dict] = None
