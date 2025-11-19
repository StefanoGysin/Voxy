"""
LangGraph Graph Builder

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy instead.

Migration path:
    from voxy_agents.langgraph.graph_builder import create_phase2_graph
    → from voxy import create_phase2_graph
"""

# Re-export from new location for backward compatibility
from voxy.graph_builder import create_phase2_graph

__all__ = ["create_phase2_graph"]
