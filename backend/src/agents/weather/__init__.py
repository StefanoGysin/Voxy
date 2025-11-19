"""
Weather Agent - Real-time weather information via OpenWeatherMap.

This agent provides current weather and forecast data using OpenWeatherMap API.
Primarily used as a TOOL in the supervisor, not as a standalone node.

Public API:
    - create_weather_node(): Factory for LangGraph node
    - create_weather_tool(): Tool for supervisor agent
    - get_weather_node(): Lazy-initialized global instance
"""

from .node import create_weather_node, create_weather_tool, get_weather_node

__all__ = [
    "create_weather_node",
    "create_weather_tool",
    "get_weather_node",
]
