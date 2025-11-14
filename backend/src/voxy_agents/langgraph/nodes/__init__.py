"""
LangGraph Node Implementations

This module contains LangGraph node functions for VOXY subagents.
Each node wraps the existing subagent logic while conforming to LangGraph's
node interface (receive VoxyState, return state updates).

Nodes can be used in two ways:
1. Standalone nodes in a StateGraph
2. Tools for supervisor via @tool decorator

Available Nodes:
- translator_node: Translation subagent (Phase 1 POC)
- (Future) corrector_node, weather_node, calculator_node, vision_node
"""

from .translator_node import create_translator_node, create_translator_tool

__all__ = [
    "create_translator_node",
    "create_translator_tool",
]
