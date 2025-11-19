"""
Weather Tool - OpenWeatherMap API integration.

Provides current weather and forecast data using OpenWeatherMap API.
This is the ONLY external tool currently used by agents.

Public API:
    - WeatherAPI: Main client class
"""

from .client import WeatherAPI

__all__ = ["WeatherAPI"]
