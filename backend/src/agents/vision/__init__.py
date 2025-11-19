"""
Vision Agent - Multimodal image analysis.

This agent provides detailed image analysis using LiteLLM multimodal models.
Supports OCR, object detection, scene understanding, and document analysis.

Public API:
    - create_vision_node(): Factory for LangGraph node
    - create_vision_tool(): Tool for supervisor agent
    - get_vision_node(): Lazy-initialized global instance
"""

from .node import create_vision_node, create_vision_tool, get_vision_node

__all__ = [
    "create_vision_node",
    "create_vision_tool",
    "get_vision_node",
]
