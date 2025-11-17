"""
Chat routes for VOXY Agents with authentication and persistence.
Consolidated and secured - no unauthenticated endpoints.

NOTE: All chat-related endpoints have been REMOVED.
- REST chat endpoint: Removed (duplicated WebSocket functionality)
- Vision usage stats: Removed (not used)

All chat functionality is now handled via WebSocket /ws/{user_id} in
fastapi_server.py to eliminate code duplication and provide a single
source of truth for feature flags.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model with authentication and vision support."""

    message: str
    session_id: Optional[str] = None
    image_url: Optional[str] = None  # Support for image analysis with Vision Agent


class ChatResponse(BaseModel):
    """Chat response model with vision analysis metadata and tools tracking."""

    response: str
    session_id: str
    request_id: str
    timestamp: datetime
    processing_time: float
    agent_type: Optional[str] = None
    tools_used: list[str] = []  # List of tools/subagents used
    cached: bool = False
    vision_metadata: Optional[dict] = (
        None  # Vision analysis metadata (model, cost, etc.)
    )


class WebSocketMessage(BaseModel):
    """WebSocket message model with vision support."""

    type: str  # 'chat', 'system', 'error', 'vision'
    message: str
    session_id: Optional[str] = None
    image_url: Optional[str] = None  # For vision analysis requests
    vision_metadata: Optional[dict] = None  # Vision analysis metadata


# ============================================================================
# All Chat Endpoints REMOVED
# ============================================================================
# The following endpoints have been removed:
# 1. POST /api/chat - REST chat endpoint (duplicated WebSocket)
# 2. GET /api/chat/vision-usage - Vision usage stats (not used)
#
# All chat functionality is now handled via WebSocket /ws/{user_id}
#
# Reasons for removal:
# 1. Frontend uses 100% WebSocket (0 REST usage)
# 2. Eliminates code duplication (REST vs WebSocket)
# 3. Single source of truth for feature flags
# 4. Reduces maintenance burden and potential bugs
#
# If REST API is needed in the future, it can be implemented as a wrapper
# over the WebSocket connection.
# ============================================================================
