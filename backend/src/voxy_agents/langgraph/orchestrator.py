"""
LangGraph Orchestrator Service

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy instead.

Migration path:
    from voxy_agents.langgraph.orchestrator import LangGraphOrchestrator
    → from voxy import LangGraphOrchestrator
"""

# Re-export from new location for backward compatibility
from voxy import LangGraphOrchestrator

__all__ = ["LangGraphOrchestrator"]
