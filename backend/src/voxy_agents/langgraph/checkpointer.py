"""
LangGraph Checkpointer Utilities

DEPRECATED: This file is kept for backward compatibility only.
New code should import from voxy instead.

Migration path:
    from voxy_agents.langgraph.checkpointer import CheckpointerType
    → from voxy import CheckpointerType
"""

# Re-export from new location for backward compatibility
from voxy.checkpointer import (
    CheckpointerType,
    create_checkpointer,
    get_checkpoint_config,
)

__all__ = ["CheckpointerType", "create_checkpointer", "get_checkpoint_config"]
