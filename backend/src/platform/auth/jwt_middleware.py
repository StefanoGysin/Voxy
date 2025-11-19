"""
Authentication middleware for VOXY Agents with Supabase JWT.
Enhanced with token blacklisting support.

Migrated from voxy_agents/api/middleware/auth.py to platform/auth/.
"""

from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from integrations.redis import token_manager
from voxy_agents.config.settings import settings

# Security scheme for JWT tokens
security = HTTPBearer()


class User(BaseModel):
    """User model for authenticated users."""

    id: str
    email: str
    role: str = "authenticated"
    app_metadata: Optional[dict[str, Any]] = None
    user_metadata: Optional[dict[str, Any]] = None


class TokenData(BaseModel):
    """Token data extracted from JWT."""

    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    jti: Optional[str] = None  # JWT ID for blacklisting


async def verify_token(token: str) -> TokenData:
    """
    Verify Supabase JWT token and extract user data.
    Now includes blacklist checking for enhanced security.

    Args:
        token: JWT token string

    Returns:
        TokenData: Extracted token data

    Raises:
        HTTPException: If token is invalid or blacklisted
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Supabase JWT secret for verification
        jwt_secret = settings.supabase_jwt_secret

        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret not configured. Check SUPABASE_JWT_SECRET environment variable.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode JWT token following FastAPI best practices
        # For Supabase JWTs, we need to specify the correct audience
        payload = jwt.decode(
            token, jwt_secret, algorithms=["HS256"], audience="authenticated"
        )

        # Extract user information using 'sub' as per FastAPI standards
        user_id: str = payload.get("sub")  # Standard JWT 'subject' field
        email: str = payload.get("email", "")
        role: str = payload.get("role", "authenticated")
        jti: str = payload.get("jti", "")  # JWT ID for blacklisting

        if user_id is None:
            raise credentials_exception

        # Check if token is blacklisted (if JTI is present)
        if jti and await token_manager.is_token_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(user_id=user_id, email=email, role=role, jti=jti)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: Authorization credentials from request

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    # Verify token and extract data (now async)
    token_data = await verify_token(credentials.credentials)

    # Always use token data as the primary source
    # Supabase auth.get_user() often fails in production
    return User(
        id=token_data.user_id,
        email=token_data.email,
        role=token_data.role or "authenticated",
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (additional validation can be added here).

    Args:
        current_user: Current authenticated user

    Returns:
        User: Active user

    Raises:
        HTTPException: If user is inactive
    """
    # Add any additional user validation here
    # For example, check if user is disabled in your database

    return current_user


# Optional: Function for dependency injection without credentials exception
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.

    Args:
        credentials: Optional authorization credentials

    Returns:
        Optional[User]: Current user or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
