"""
Supabase integration for VOXY Agents.

Provides database client, authentication, and storage services.

Public API:
    - get_supabase_client(): Get Supabase client with anon key
    - get_supabase_service_client(): Get Supabase client with service_role key (full access)

Database operations are available in .database module (for future imports if needed).
"""

from .client import get_supabase_client, get_supabase_service_client

__all__ = [
    "get_supabase_client",
    "get_supabase_service_client",
]
