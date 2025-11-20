"""
WebSocket Connection Manager

Manages active WebSocket connections for real-time communication.
Extracted from fastapi_server.py (monolith) to api/websocket/.
"""

import json

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.

    Responsibilities:
    - Accept and register new WebSocket connections
    - Track active connections by user_id
    - Send messages to specific users
    - Broadcast messages to all connected users
    - Handle disconnections and cleanup
    """

    def __init__(self):
        """Initialize connection manager with empty connections dict."""
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Connect a new WebSocket client.

        Args:
            websocket: WebSocket connection instance
            user_id: User identifier (from JWT token)
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.bind(event="WEBSOCKET|CONNECT").info(
            "WebSocket connected",
            user_id=user_id[:16],
            total_connections=len(self.active_connections),
        )

    def disconnect(self, user_id: str):
        """
        Disconnect a WebSocket client.

        Args:
            user_id: User identifier to disconnect
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.bind(event="WEBSOCKET|DISCONNECT").info(
                "WebSocket disconnected",
                user_id=user_id[:16],
                remaining_connections=len(self.active_connections),
            )

    async def send_message(self, user_id: str, message: dict):
        """
        Send message to specific user.

        Args:
            user_id: Target user identifier
            message: Message dict to send (will be JSON serialized)
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
                logger.bind(event="WEBSOCKET|SEND").debug(
                    "Message sent to user",
                    user_id=user_id[:16],
                    message_type=message.get("type", "unknown"),
                )
            except Exception as e:
                logger.bind(event="WEBSOCKET|SEND_ERROR").error(
                    "Error sending message", user_id=user_id[:16], error=str(e)
                )
                self.disconnect(user_id)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message dict to broadcast (will be JSON serialized)
        """
        disconnected = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.bind(event="WEBSOCKET|BROADCAST_ERROR").error(
                    "Error broadcasting", user_id=user_id[:16], error=str(e)
                )
                disconnected.append(user_id)

        # Clean up disconnected clients
        for user_id in disconnected:
            self.disconnect(user_id)

        if disconnected:
            logger.bind(event="WEBSOCKET|BROADCAST").warning(
                "Broadcast completed with failures",
                failed_count=len(disconnected),
                total_connections=len(self.active_connections),
            )


# Global singleton instance
manager = ConnectionManager()
