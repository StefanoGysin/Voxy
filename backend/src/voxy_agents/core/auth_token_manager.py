"""
Token management service for VOXY Agents.

DEPRECATED: This file is kept for backward compatibility only.
New code should import from integrations.redis instead.

Migration path:
    from voxy_agents.core.auth_token_manager import token_manager
    → from integrations.redis import token_manager
"""

# Re-export from new location for backward compatibility
from integrations.redis import TokenManager, token_manager

__all__ = ["TokenManager", "token_manager"]
