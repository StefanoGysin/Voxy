"""
Session Manager for VOXY system.

DEPRECATED: This file is kept for backward compatibility only.
New code should import from platform.sessions instead.

Migration path:
    from voxy_agents.core.sessions.session_manager import SessionManager
    → from platform.sessions import SessionManager
"""

# Re-export from new location for backward compatibility
from platform.sessions import SessionManager

__all__ = ["SessionManager"]
