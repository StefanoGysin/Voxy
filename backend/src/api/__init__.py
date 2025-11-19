"""
API Layer for VOXY Agents

FastAPI application with REST routes and WebSocket support.

Modules:
    - server: FastAPI application
    - websocket: WebSocket communication
    - routes: REST endpoints (auth, chat, images, messages, sessions)
"""

from .server import app

__all__ = ["app"]
