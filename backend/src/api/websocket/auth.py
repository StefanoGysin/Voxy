"""
WebSocket Authentication

JWT token validation for WebSocket connections.
Extracted from fastapi_server.py.
"""

from typing import Optional

from fastapi import HTTPException, Query, WebSocket, status
from loguru import logger

from src.platform.auth import TokenData, verify_token


async def get_websocket_token(
    websocket: WebSocket, token: Optional[str] = Query(None)
) -> TokenData:
    """
    Mandatory WebSocket authentication dependency.

    Validates JWT token and returns TokenData or closes connection with 1008 (Policy Violation).

    Args:
        websocket: WebSocket connection instance
        token: JWT token from query parameter

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        logger.bind(event="WEBSOCKET|AUTH_FAILED").warning(
            "WebSocket connection rejected: No authentication token provided"
        )
        await websocket.close(code=1008, reason="Authentication required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required for WebSocket connection",
        )

    try:
        logger.bind(event="WEBSOCKET|AUTH_ATTEMPT").info(
            "Attempting WebSocket JWT validation", token_preview=token[:20] + "..."
        )

        # Use the same verification as the rest of the API
        token_data = await verify_token(token)

        # Validate token data
        if not token_data.user_id or not token_data.email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user information",
            )

        logger.bind(event="WEBSOCKET|AUTH_SUCCESS").info(
            "WebSocket authenticated",
            user_id=token_data.user_id[:16],
            email=token_data.email,
        )
        return token_data

    except HTTPException as e:
        logger.bind(event="WEBSOCKET|AUTH_FAILED").warning(
            "WebSocket authentication failed", detail=e.detail
        )
        await websocket.close(code=1008, reason=f"Authentication failed: {e.detail}")
        raise

    except Exception as e:
        logger.bind(event="WEBSOCKET|AUTH_ERROR").error(
            "WebSocket authentication error", error=str(e)
        )
        await websocket.close(code=1008, reason="Authentication error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )
