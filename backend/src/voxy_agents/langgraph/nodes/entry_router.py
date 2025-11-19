"""
Entry Router Node - LangGraph Implementation

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy.routing instead.

Migration path:
    from voxy_agents.langgraph.nodes.entry_router import entry_router
    → from voxy.routing import entry_router
"""

# Re-export from new location for backward compatibility
from voxy.routing import detect_vision_bypass, entry_router

__all__ = [
    "entry_router",
    "detect_vision_bypass",
]
