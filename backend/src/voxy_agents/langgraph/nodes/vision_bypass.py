"""
Vision Bypass Node - LangGraph Implementation

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy.routing instead.

Migration path:
    from voxy_agents.langgraph.nodes.vision_bypass import vision_bypass_node
    → from voxy.routing import vision_bypass_node
"""

# Re-export from new location for backward compatibility
from voxy.routing import vision_bypass_node

__all__ = ["vision_bypass_node"]
