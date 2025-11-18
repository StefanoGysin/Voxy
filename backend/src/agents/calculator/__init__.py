"""
Calculator Agent - Mathematical calculations with step-by-step explanations.

This agent performs mathematical calculations using LLM reasoning,
providing detailed explanations and step-by-step solutions.

Public API:
    - create_calculator_node(): Factory for LangGraph node
    - create_calculator_tool(): Tool for supervisor agent
    - get_calculator_node(): Lazy-initialized global instance
"""

from .node import create_calculator_node, create_calculator_tool, get_calculator_node

__all__ = [
    "create_calculator_node",
    "create_calculator_tool",
    "get_calculator_node",
]
