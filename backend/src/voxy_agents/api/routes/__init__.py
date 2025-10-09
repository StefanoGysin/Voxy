"""
API routes for VOXY Agents.
"""

from .auth import router as auth_router
from .chat import router as chat_router
from .images import router as images_router
from .sessions import router as sessions_router

__all__ = ["auth_router", "chat_router", "images_router", "sessions_router"]
