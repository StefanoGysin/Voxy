"""
Supabase client configuration for VOXY Agents.
"""

from functools import lru_cache

from supabase import Client, create_client

from ...config.settings import settings


@lru_cache
def get_supabase_client() -> Client:
    """
    Get configured Supabase client instance with anon key.

    Returns:
        Client: Configured Supabase client
    """
    return create_client(
        supabase_url=settings.supabase_url, supabase_key=settings.supabase_anon_key
    )


@lru_cache
def get_supabase_service_client() -> Client:
    """
    Get configured Supabase client instance with service_role key.
    This bypasses RLS and has full database access.

    Returns:
        Client: Configured Supabase service client
    """
    return create_client(
        supabase_url=settings.supabase_url, supabase_key=settings.supabase_service_key
    )
