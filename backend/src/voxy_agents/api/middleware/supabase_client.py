"""
Supabase client configuration for VOXY Agents.

DEPRECATED: This file is kept for backward compatibility only.
New code should import from integrations.supabase instead.

Migration path:
    from voxy_agents.api.middleware.supabase_client import get_supabase_client
    → from integrations.supabase import get_supabase_client
"""

# Re-export from new location for backward compatibility
from integrations.supabase import get_supabase_client, get_supabase_service_client

__all__ = [
    "get_supabase_client",
    "get_supabase_service_client",
]
