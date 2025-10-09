"""
Weather API integration for VOXY system.

Uses OpenWeatherMap API to fetch current weather and forecasts.
"""

import logging
from typing import Any

import httpx

from ...config.settings import settings

logger = logging.getLogger(__name__)


class WeatherAPI:
    """
    Weather API client for OpenWeatherMap integration.

    Provides current weather, forecasts, and weather alerts.
    """

    def __init__(self):
        self.api_key = settings.openweather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geo_url = "https://api.openweathermap.org/geo/1.0"

        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")

    async def get_current_weather(
        self, location: str, units: str = "metric"
    ) -> dict[str, Any]:
        """
        Get current weather for a location.

        Args:
            location: City name, state/country code (e.g., "London,UK")
            units: Temperature units (metric, imperial, kelvin)

        Returns:
            Dictionary with weather data
        """
        if not self.api_key:
            return {"error": "Weather API not configured"}

        try:
            # First, get coordinates for the location
            coords = await self._get_coordinates(location)
            if "error" in coords:
                return coords

            # Get current weather
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": coords["lat"],
                        "lon": coords["lon"],
                        "appid": self.api_key,
                        "units": units,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

                data = response.json()

                # Format response
                return {
                    "location": {
                        "name": data["name"],
                        "country": data["sys"]["country"],
                        "coordinates": [coords["lat"], coords["lon"]],
                    },
                    "current": {
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "description": data["weather"][0]["description"],
                        "main": data["weather"][0]["main"],
                        "wind_speed": data.get("wind", {}).get("speed", 0),
                        "wind_direction": data.get("wind", {}).get("deg", 0),
                        "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                        "cloudiness": data["clouds"]["all"],
                    },
                    "units": units,
                    "timestamp": data["dt"],
                }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {e}")
            return {"error": f"Failed to fetch weather data: {str(e)}"}
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return {"error": f"Weather service error: {str(e)}"}

    async def get_forecast(
        self, location: str, days: int = 5, units: str = "metric"
    ) -> dict[str, Any]:
        """
        Get weather forecast for a location.

        Args:
            location: City name, state/country code
            days: Number of days (1-5)
            units: Temperature units

        Returns:
            Dictionary with forecast data
        """
        if not self.api_key:
            return {"error": "Weather API not configured"}

        days = min(max(days, 1), 5)  # Limit to 1-5 days

        try:
            # Get coordinates
            coords = await self._get_coordinates(location)
            if "error" in coords:
                return coords

            # Get forecast
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": coords["lat"],
                        "lon": coords["lon"],
                        "appid": self.api_key,
                        "units": units,
                        "cnt": days * 8,  # 8 forecasts per day (3-hour intervals)
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

                data = response.json()

                # Group forecasts by day
                daily_forecasts: dict[str, list[dict]] = {}
                for item in data["list"]:
                    date = item["dt_txt"].split(" ")[0]
                    if date not in daily_forecasts:
                        daily_forecasts[date] = []
                    daily_forecasts[date].append(item)

                # Format response
                forecast_data = []
                for date, forecasts in list(daily_forecasts.items())[:days]:
                    day_data = {"date": date, "forecasts": []}
                    forecasts_list = day_data["forecasts"]

                    for forecast in forecasts:
                        forecasts_list.append(
                            {
                                "time": forecast["dt_txt"].split(" ")[1],
                                "temperature": forecast["main"]["temp"],
                                "feels_like": forecast["main"]["feels_like"],
                                "humidity": forecast["main"]["humidity"],
                                "description": forecast["weather"][0]["description"],
                                "main": forecast["weather"][0]["main"],
                                "wind_speed": forecast.get("wind", {}).get("speed", 0),
                                "precipitation_prob": forecast.get("pop", 0) * 100,
                            }
                        )

                    forecast_data.append(day_data)

                return {
                    "location": {
                        "name": data["city"]["name"],
                        "country": data["city"]["country"],
                        "coordinates": [coords["lat"], coords["lon"]],
                    },
                    "forecast": forecast_data,
                    "units": units,
                }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching forecast: {e}")
            return {"error": f"Failed to fetch forecast data: {str(e)}"}
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return {"error": f"Forecast service error: {str(e)}"}

    async def _get_coordinates(self, location: str) -> dict[str, Any]:
        """Get coordinates for a location using geocoding API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.geo_url}/direct",
                    params={"q": location, "limit": 1, "appid": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()

                data = response.json()
                if not data:
                    return {"error": f"Location '{location}' not found"}

                return {
                    "lat": data[0]["lat"],
                    "lon": data[0]["lon"],
                    "name": data[0]["name"],
                    "country": data[0].get("country", ""),
                    "state": data[0].get("state", ""),
                }

        except Exception as e:
            logger.error(f"Error geocoding location: {e}")
            return {"error": f"Failed to find location: {str(e)}"}
