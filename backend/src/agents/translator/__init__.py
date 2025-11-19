"""
Translator Agent - Multilingual translation with context preservation.

Public API:
    - create_translator_node(): Factory for LangGraph node
    - create_translator_tool(): Tool for supervisor agent
    - get_translator_node(): Lazy-initialized global instance
"""

from .node import create_translator_node, create_translator_tool, get_translator_node

__all__ = [
    "create_translator_node",
    "create_translator_tool",
    "get_translator_node",
]
