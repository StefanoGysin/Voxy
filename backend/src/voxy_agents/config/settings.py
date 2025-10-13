"""
Configuration settings for VOXY Agents system.
Simple configuration using environment variables.
"""

import os
from typing import Any

from dotenv import load_dotenv

# Load environment variables from .env file
# override=True ensures .env values take precedence over shell exports
load_dotenv(override=True)


class Settings:
    """Simple settings class for VOXY Agents."""

    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", "")

        # Supabase Configuration
        self.supabase_url = os.getenv("SUPABASE_URL", "https://supabase.gysin.pro")
        self.supabase_anon_key = os.getenv(
            "SUPABASE_ANON_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzQ3MTczNjAwLCJleHAiOjE5MDQ5NDAwMDB9.WGZRH-XvQqQXMI5F-2hzJ_XfxknSBKYuHjO5Q2DJYBA",
        )
        self.supabase_service_key = os.getenv(
            "SUPABASE_SERVICE_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NDcxNzM2MDAsImV4cCI6MTkwNDk0MDAwMH0.VP-eEm8I1zd74I6L-WM9kCxeCkLlYbgnK6YsYHkq7J0",
        )
        # JWT secret from Supabase (REQUIRED for authentication)
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

        # JWT Configuration
        self.jwt_expiration_hours = int(
            os.getenv("SUPABASE_JWT_EXPIRATION_HOURS", "24")
        )
        self.jwt_access_token_expire_seconds = (
            self.jwt_expiration_hours * 3600
        )  # Convert hours to seconds

        # Validate required Supabase configuration
        if not self.supabase_jwt_secret:
            print(
                "⚠️  WARNING: SUPABASE_JWT_SECRET not configured. Authentication will fail!"
            )
            print(
                "   Get your JWT secret from: Supabase Dashboard → Project Settings → API → JWT Secret"
            )
            # For development only - use a fallback that will work with the test data
            self.supabase_jwt_secret = "vubs0ShBE2fWU2QVWydZoIe5JKJbivtVKp6AhGqv"

        # Redis Configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        # System Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Model Configuration (defaults for 2025)
        # LEGACY: VOXY_ORCHESTRATOR_MODEL is deprecated - use ORCHESTRATOR_* vars in models_config.py
        # This field is maintained for backward compatibility only
        self.orchestrator_model = os.getenv(
            "VOXY_ORCHESTRATOR_MODEL", "gpt-4o"
        )  # Deprecated: Use load_orchestrator_config() instead
        self.subagent_efficient_model = os.getenv(
            "SUBAGENT_EFFICIENT_MODEL", "gpt-4o-mini"
        )
        self.subagent_api_model = os.getenv("SUBAGENT_API_MODEL", "gpt-4o-mini")

        # Vision Agent Configuration (GPT-5 + fallback)
        self.vision_primary_model = os.getenv("VISION_PRIMARY_MODEL", "gpt-5")
        self.vision_fallback_model = os.getenv("VISION_FALLBACK_MODEL", "gpt-4o")

        # Vision Agent Rate Limiting
        self.vision_rate_limit_per_minute = int(
            os.getenv("VISION_RATE_LIMIT_PER_MINUTE", "10")
        )
        self.vision_rate_limit_per_hour = int(
            os.getenv("VISION_RATE_LIMIT_PER_HOUR", "50")
        )
        self.vision_monthly_quota = int(os.getenv("VISION_MONTHLY_QUOTA", "1000"))

        # Vision Agent Cost Control
        self.vision_max_cost_per_analysis = float(
            os.getenv("VISION_MAX_COST_PER_ANALYSIS", "0.10")
        )
        self.vision_daily_budget_limit = float(
            os.getenv("VISION_DAILY_BUDGET_LIMIT", "50.00")
        )
        self.vision_monthly_budget_limit = float(
            os.getenv("VISION_MONTHLY_BUDGET_LIMIT", "500.00")
        )

        # Vision Flow Corrections Feature Flag
        # Set to "false" to disable post-processing and revert to legacy flow
        self.enable_vision_postprocessing = (
            os.getenv("ENABLE_VISION_POSTPROCESSING", "true").lower() == "true"
        )

        # Calculator Agent Configuration (via LiteLLM)
        self.calculator_provider = os.getenv("CALCULATOR_PROVIDER", "openrouter")
        self.calculator_model = os.getenv("CALCULATOR_MODEL", "x-ai/grok-code-fast-1")
        self.calculator_max_tokens = int(os.getenv("CALCULATOR_MAX_TOKENS", "2000"))
        self.calculator_temperature = float(os.getenv("CALCULATOR_TEMPERATURE", "0.1"))
        self.calculator_include_usage = (
            os.getenv("CALCULATOR_INCLUDE_USAGE", "true").lower() == "true"
        )

        # Corrector Agent Configuration (via LiteLLM)
        self.corrector_provider = os.getenv("CORRECTOR_PROVIDER", "openai")
        self.corrector_model = os.getenv("CORRECTOR_MODEL", "gpt-4o-mini")
        self.corrector_max_tokens = int(os.getenv("CORRECTOR_MAX_TOKENS", "2000"))
        self.corrector_temperature = float(os.getenv("CORRECTOR_TEMPERATURE", "0.1"))

        # Weather Agent Configuration (via LiteLLM)
        self.weather_provider = os.getenv("WEATHER_PROVIDER", "openai")
        self.weather_model = os.getenv("WEATHER_MODEL", "gpt-4o-mini")
        self.weather_max_tokens = int(os.getenv("WEATHER_MAX_TOKENS", "2000"))
        self.weather_temperature = float(os.getenv("WEATHER_TEMPERATURE", "0.1"))


def load_model_config() -> dict[str, Any]:
    """Load model configuration."""
    return {
        "models": {
            "orchestrator": {
                "name": settings.orchestrator_model,
                "max_tokens": 4000,
                "temperature": 0.3,
                "cost_per_input_token": 0.000005,  # $5 per 1M tokens
                "cost_per_output_token": 0.000015,  # $15 per 1M tokens
            },
            "subagent_efficient": {
                "name": settings.subagent_efficient_model,
                "max_tokens": 2000,
                "temperature": 0.1,
                "cost_per_input_token": 0.00000015,  # $0.15 per 1M tokens
                "cost_per_output_token": 0.0000006,  # $0.60 per 1M tokens
            },
            "vision_gpt5": {
                "name": settings.vision_primary_model,
                "max_tokens": 2000,
                "temperature": 0.1,
                "cost_per_input_token": 0.00001,  # $0.01 per 1K tokens (GPT-5 estimated)
                "cost_per_output_token": 0.00003,  # $0.03 per 1K tokens (GPT-5 estimated)
                "cost_per_image": 0.02,  # $0.02 per image analysis
                "rate_limit_per_minute": settings.vision_rate_limit_per_minute,
                "rate_limit_per_hour": settings.vision_rate_limit_per_hour,
                "monthly_quota": settings.vision_monthly_quota,
                "max_cost_per_analysis": settings.vision_max_cost_per_analysis,
                "daily_budget_limit": settings.vision_daily_budget_limit,
                "monthly_budget_limit": settings.vision_monthly_budget_limit,
            },
            "vision_fallback": {
                "name": settings.vision_fallback_model,
                "max_tokens": 2000,
                "temperature": 0.1,
                "cost_per_input_token": 0.000005,  # $5 per 1M tokens (GPT-4o)
                "cost_per_output_token": 0.000015,  # $15 per 1M tokens (GPT-4o)
                "cost_per_image": 0.01,  # $0.01 per image analysis (GPT-4o)
            },
        }
    }


# Global settings instance
settings = Settings()
model_config = load_model_config()
