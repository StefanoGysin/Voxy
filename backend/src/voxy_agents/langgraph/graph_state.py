"""
LangGraph State Management

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy instead.

Migration path:
    from voxy_agents.langgraph.graph_state import VoxyState
    → from voxy import VoxyState
"""

# Re-export from new location for backward compatibility
from voxy.graph_state import VoxyState, create_initial_state, update_context

__all__ = ["VoxyState", "create_initial_state", "update_context"]
