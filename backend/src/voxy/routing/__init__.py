"""
VOXY Routing - Entry router and path management.

Implements dual-path architecture:
- PATH1: Vision bypass (direct to vision agent when image detected)
- PATH2: Supervisor orchestrator (VOXY decides which agent to use)

Public API:
    - entry_router: Main routing function (PATH1 vs PATH2)
    - vision_bypass_node: PATH1 implementation
    - detect_vision_bypass: Vision detection logic
"""

from .entry_router import detect_vision_bypass, entry_router
from .vision_bypass import vision_bypass_node

__all__ = [
    "entry_router",
    "vision_bypass_node",
    "detect_vision_bypass",
]
