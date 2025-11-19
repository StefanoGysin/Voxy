"""
API Routes for VOXY Agents

REST endpoints for authentication, chat, images, messages, and sessions.
Migrated from voxy_agents/api/routes/.

Routers:
    - auth: Authentication (login, signup, logout)
    - chat: Chat models (WebSocketMessage)
    - images: Image management (upload, list, delete)
    - messages: Message history
    - sessions: Session management
"""

from . import auth, chat, images, messages, sessions

__all__ = [
    "auth",
    "chat",
    "images",
    "messages",
    "sessions",
]
