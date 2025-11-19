"""
Corrector Agent - Spelling and grammar correction.

This agent corrects orthographic and grammatical errors while
preserving the original meaning and style of the text.

Public API:
    - create_corrector_node(): Factory for LangGraph node
    - create_corrector_tool(): Tool for supervisor agent
    - get_corrector_node(): Lazy-initialized global instance
"""

from .node import create_corrector_node, create_corrector_tool, get_corrector_node

__all__ = [
    "create_corrector_node",
    "create_corrector_tool",
    "get_corrector_node",
]
