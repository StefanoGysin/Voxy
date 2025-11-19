"""
Authentication platform for VOXY Agents.

Provides JWT middleware, token validation, and user authentication.

Public API:
    - User: User model for authenticated users
    - TokenData: Token data extracted from JWT
    - verify_token: Verify and decode JWT token
    - get_current_user: Dependency for getting authenticated user
    - get_current_active_user: Dependency for getting active user
    - get_optional_user: Optional authentication dependency
    - security: HTTPBearer security scheme
"""

from .jwt_middleware import (
    TokenData,
    User,
    get_current_active_user,
    get_current_user,
    get_optional_user,
    security,
    verify_token,
)

__all__ = [
    "User",
    "TokenData",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "security",
]
