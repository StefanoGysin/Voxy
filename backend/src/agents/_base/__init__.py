"""
Base classes and utilities for VOXY agents.

This module provides:
- BaseAgent: Abstract base for agent business logic
- create_simple_node: Factory for creating LangGraph nodes
- Utility functions for node management
"""

from .agent import BaseAgent, SyncAgent
from .node import create_simple_node, create_lazy_node, get_or_create_node

__all__ = [
    "BaseAgent",
    "SyncAgent",
    "create_simple_node",
    "create_lazy_node",
    "get_or_create_node",
]
