"""
LangGraph Orchestrator Service

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy instead.

Migration path:
    from voxy_agents.langgraph.orchestrator import LangGraphOrchestrator
    → from voxy import LangGraphOrchestrator

    from voxy_agents.langgraph.orchestrator import get_langgraph_orchestrator
    → from voxy.orchestrator import get_langgraph_orchestrator
"""

# Re-export from new location for backward compatibility
from voxy import LangGraphOrchestrator
from voxy.orchestrator import get_langgraph_orchestrator

__all__ = ["LangGraphOrchestrator", "get_langgraph_orchestrator"]
