"""
Usage Callback Handler

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy instead.

Migration path:
    from voxy_agents.langgraph.usage_callback import UsageCallbackHandler
    → from voxy.usage_callback import UsageCallbackHandler
"""

# Re-export from new location for backward compatibility
from voxy.usage_callback import UsageCallbackHandler

__all__ = ["UsageCallbackHandler"]
