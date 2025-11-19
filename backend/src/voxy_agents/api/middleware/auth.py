"""
Authentication middleware for VOXY Agents with Supabase JWT.

DEPRECATED: This file is kept for backward compatibility only.
New code should import from platform.auth instead.

Migration path:
    from voxy_agents.api.middleware.auth import get_current_user
    → from platform.auth import get_current_user
"""

# Re-export from new location for backward compatibility
from platform.auth import (
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
