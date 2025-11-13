"""
Model Configuration for VOXY Subagents.

Centralizes model configuration for all subagents, supporting multiple providers
through LiteLLM (OpenRouter, OpenAI, Anthropic, etc.).
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from dotenv import load_dotenv

# Load environment variables
# override=True ensures .env values take precedence over shell exports
load_dotenv(override=True)


@dataclass
class SubagentModelConfig:
    """
    Configuration for a subagent's LLM model.

    Attributes:
        provider: LLM provider (openrouter, openai, anthropic, etc.)
        model_name: Model identifier (e.g., "x-ai/grok-code-fast-1")
        api_key: API key for the provider
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        include_usage: Whether to track token usage
        agent_name: Agent identifier for reasoning config lookup (orchestrator, vision, calculator, etc.)
        reasoning_enabled: Whether to enable reasoning/thinking capture
        thinking_budget_tokens: Token budget for Claude Extended Thinking
        gemini_thinking_budget: Token budget for Gemini Thinking Config
        reasoning_effort: Reasoning effort level for OpenAI (minimal, low, medium, high)
    """

    provider: str
    model_name: str
    api_key: str
    max_tokens: int = 2000
    temperature: float = 0.1
    include_usage: bool = True
    agent_name: str = "generic"  # Used for reasoning config lookup

    # Reasoning/Thinking configuration (optional)
    reasoning_enabled: bool = True
    thinking_budget_tokens: Optional[int] = None
    gemini_thinking_budget: Optional[int] = None
    reasoning_effort: Optional[str] = None

    def get_litellm_model_path(self) -> str:
        """
        Get the full LiteLLM model path.

        Returns:
            str: Formatted model path for LiteLLM (e.g., "openrouter/x-ai/grok-code-fast-1")
        """
        # For OpenRouter, format is: openrouter/provider/model
        # For OpenAI direct, format is: openai/model
        if self.provider == "openrouter":
            return f"openrouter/{self.model_name}"
        elif self.provider == "openai":
            return f"openai/{self.model_name}"
        else:
            # For other providers, use provider/model format
            return f"{self.provider}/{self.model_name}"

    def get_reasoning_params(self) -> dict:
        """
        Get reasoning-specific parameters for LiteLLM request.

        Returns:
            dict: Extra parameters for reasoning/thinking based on provider
        """
        if not self.reasoning_enabled:
            return {}

        params: dict[str, Any] = {}

        # Claude Extended Thinking
        if (
            self.provider in ["anthropic", "claude"]
            or "claude" in self.model_name.lower()
        ):
            if self.thinking_budget_tokens:
                params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget_tokens,
                }

        # Gemini Thinking Config
        elif (
            self.provider in ["google", "gemini"] or "gemini" in self.model_name.lower()
        ):
            if self.gemini_thinking_budget is not None:
                params["thinking_config"] = {
                    "thinking_budget": self.gemini_thinking_budget
                }

        # OpenAI Reasoning Effort
        elif (
            self.provider == "openai"
            or self.model_name.startswith("gpt-")
            or self.model_name.startswith("o1-")
        ):
            if self.reasoning_effort:
                params["reasoning_effort"] = self.reasoning_effort

        return params


def load_calculator_config() -> SubagentModelConfig:
    """
    Load Calculator Agent configuration from environment variables.

    Environment Variables:
        CALCULATOR_PROVIDER: Provider name (default: "openrouter")
        CALCULATOR_MODEL: Model name (configured in .env - see .env.example)
        OPENROUTER_API_KEY: OpenRouter API key (required if provider=openrouter)
        OPENAI_API_KEY: OpenAI API key (required if provider=openai)
        CALCULATOR_MAX_TOKENS: Max tokens (default: 2000)
        CALCULATOR_TEMPERATURE: Temperature (default: 0.1)
        CALCULATOR_INCLUDE_USAGE: Track usage (default: true)
        CALCULATOR_REASONING_ENABLED: Enable reasoning capture (default: true)

    Returns:
        SubagentModelConfig: Calculator agent configuration

    Raises:
        ValueError: If required configuration is missing
    """
    provider = os.getenv("CALCULATOR_PROVIDER", "openrouter")
    model_name = os.getenv("CALCULATOR_MODEL")

    if not model_name:
        raise ValueError(
            "CALCULATOR_MODEL not configured. Please set in .env file. "
            "See .env.example for configuration options."
        )

    # Determine API key based on provider
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required when CALCULATOR_PROVIDER=openrouter"
            )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when CALCULATOR_PROVIDER=openai"
            )
    else:
        # For other providers, try provider-specific key
        api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
        if not api_key:
            raise ValueError(
                f"{provider.upper()}_API_KEY environment variable is required when CALCULATOR_PROVIDER={provider}"
            )

    max_tokens = int(os.getenv("CALCULATOR_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("CALCULATOR_TEMPERATURE", "0.1"))
    include_usage = os.getenv("CALCULATOR_INCLUDE_USAGE", "true").lower() == "true"

    # Reasoning configuration (Grok supports reasoning_content by default)
    reasoning_enabled = (
        os.getenv("CALCULATOR_REASONING_ENABLED", "true").lower() == "true"
    )

    return SubagentModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        include_usage=include_usage,
        agent_name="calculator",
        reasoning_enabled=reasoning_enabled,
    )


def load_corrector_config() -> SubagentModelConfig:
    """
    Load Corrector Agent configuration from environment variables.

    Environment Variables:
        CORRECTOR_PROVIDER: Provider name (default: "openai")
        CORRECTOR_MODEL: Model name (configured in .env - see .env.example)
        CORRECTOR_MAX_TOKENS: Max tokens (default: 2000)
        CORRECTOR_TEMPERATURE: Temperature (default: 0.1)

    Returns:
        SubagentModelConfig: Corrector agent configuration

    Raises:
        ValueError: If required configuration is missing
    """
    provider = os.getenv("CORRECTOR_PROVIDER", "openai")
    model_name = os.getenv("CORRECTOR_MODEL")

    if not model_name:
        raise ValueError(
            "CORRECTOR_MODEL not configured. Please set in .env file. "
            "See .env.example for configuration options."
        )

    # Determine API key based on provider
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
    else:  # Default to OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "")

    max_tokens = int(os.getenv("CORRECTOR_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("CORRECTOR_TEMPERATURE", "0.1"))
    include_usage = os.getenv("CORRECTOR_INCLUDE_USAGE", "true").lower() == "true"

    return SubagentModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        include_usage=include_usage,
        agent_name="corrector",
    )


def load_weather_config() -> SubagentModelConfig:
    """
    Load Weather Agent configuration from environment variables.

    Environment Variables:
        WEATHER_PROVIDER: Provider name (default: "openai")
        WEATHER_MODEL: Model name (configured in .env - see .env.example)
        WEATHER_MAX_TOKENS: Max tokens (default: 2000)
        WEATHER_TEMPERATURE: Temperature (default: 0.1)

    Returns:
        SubagentModelConfig: Weather agent configuration

    Raises:
        ValueError: If required configuration is missing
    """
    provider = os.getenv("WEATHER_PROVIDER", "openai")
    model_name = os.getenv("WEATHER_MODEL")

    if not model_name:
        raise ValueError(
            "WEATHER_MODEL not configured. Please set in .env file. "
            "See .env.example for configuration options."
        )

    # Determine API key based on provider
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
    else:  # Default to OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "")

    max_tokens = int(os.getenv("WEATHER_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("WEATHER_TEMPERATURE", "0.1"))
    include_usage = os.getenv("WEATHER_INCLUDE_USAGE", "true").lower() == "true"

    return SubagentModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        include_usage=include_usage,
        agent_name="weather",
    )


def load_translator_config() -> SubagentModelConfig:
    """
    Load Translator Agent configuration from environment variables.

    Environment Variables:
        TRANSLATOR_PROVIDER: Provider name (default: "openrouter")
        TRANSLATOR_MODEL: Model name (configured in .env - see .env.example)
        OPENROUTER_API_KEY: OpenRouter API key (required if provider=openrouter)
        OPENAI_API_KEY: OpenAI API key (required if provider=openai)
        TRANSLATOR_MAX_TOKENS: Max tokens (default: 2000)
        TRANSLATOR_TEMPERATURE: Temperature (default: 0.3)
        TRANSLATOR_INCLUDE_USAGE: Track usage (default: true)

    Returns:
        SubagentModelConfig: Translator agent configuration

    Raises:
        ValueError: If required configuration is missing
    """
    provider = os.getenv("TRANSLATOR_PROVIDER", "openrouter")
    model_name = os.getenv("TRANSLATOR_MODEL")

    if not model_name:
        raise ValueError(
            "TRANSLATOR_MODEL not configured. Please set in .env file. "
            "See .env.example for configuration options."
        )

    # Determine API key based on provider
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required when TRANSLATOR_PROVIDER=openrouter"
            )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when TRANSLATOR_PROVIDER=openai"
            )
    else:
        # For other providers, try provider-specific key
        api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
        if not api_key:
            raise ValueError(
                f"{provider.upper()}_API_KEY environment variable is required when TRANSLATOR_PROVIDER={provider}"
            )

    max_tokens = int(os.getenv("TRANSLATOR_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("TRANSLATOR_TEMPERATURE", "0.3"))
    include_usage = os.getenv("TRANSLATOR_INCLUDE_USAGE", "true").lower() == "true"

    return SubagentModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        include_usage=include_usage,
        agent_name="translator",
    )


@dataclass
class VisionModelConfig(SubagentModelConfig):
    """
    Vision-specific configuration extending base SubagentModelConfig.

    Additional Attributes:
        reasoning_effort: Adaptive reasoning level (minimal, low, medium, high)
        enable_postprocessing: Enable conversational post-processing
        cache_ttl_base: Base TTL for cache entries in seconds
    """

    reasoning_effort: str = "medium"
    enable_postprocessing: bool = True
    cache_ttl_base: int = 600


def load_vision_config() -> VisionModelConfig:
    """
    Load Vision Agent configuration from environment variables.

    Environment Variables:
        VISION_PROVIDER: Provider name (default: "openrouter")
        VISION_MODEL: Model name (configured in .env - see .env.example)
        OPENROUTER_API_KEY: OpenRouter API key (required if provider=openrouter)
        OPENAI_API_KEY: OpenAI API key (required if provider=openai)
        VISION_MAX_TOKENS: Max tokens (default: 2000)
        VISION_TEMPERATURE: Temperature (default: 0.1)
        VISION_REASONING_EFFORT: Reasoning level (default: "medium")
        VISION_CACHE_TTL: Cache TTL in seconds (default: 600)
        ENABLE_VISION_POSTPROCESSING: Enable post-processing (default: true)

    Returns:
        VisionModelConfig: Vision agent configuration

    Raises:
        ValueError: If required configuration is missing
    """
    provider = os.getenv("VISION_PROVIDER", "openrouter")
    model_name = os.getenv("VISION_MODEL")

    if not model_name:
        raise ValueError(
            "VISION_MODEL not configured. Please set in .env file. "
            "See .env.example for configuration options."
        )

    # Determine API key based on provider
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required when VISION_PROVIDER=openrouter"
            )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when VISION_PROVIDER=openai"
            )
    else:
        # For other providers, try provider-specific key
        api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
        if not api_key:
            raise ValueError(
                f"{provider.upper()}_API_KEY environment variable is required when VISION_PROVIDER={provider}"
            )

    max_tokens = int(os.getenv("VISION_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("VISION_TEMPERATURE", "0.1"))
    include_usage = os.getenv("VISION_INCLUDE_USAGE", "true").lower() == "true"
    reasoning_effort = os.getenv("VISION_REASONING_EFFORT", "medium")
    cache_ttl_base = int(os.getenv("VISION_CACHE_TTL", "600"))
    enable_postprocessing = (
        os.getenv("ENABLE_VISION_POSTPROCESSING", "true").lower() == "true"
    )

    return VisionModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        include_usage=include_usage,
        agent_name="vision",
        reasoning_effort=reasoning_effort,
        cache_ttl_base=cache_ttl_base,
        enable_postprocessing=enable_postprocessing,
    )


@dataclass
class OrchestratorModelConfig(SubagentModelConfig):
    """
    VOXY Orchestrator-specific configuration extending base SubagentModelConfig.

    Additional Attributes:
        reasoning_effort: Adaptive reasoning level for complex orchestration (minimal, low, medium, high)
        enable_streaming: Future feature flag for streaming responses (not yet implemented)
    """

    reasoning_effort: str = "medium"
    enable_streaming: bool = False


def load_orchestrator_config() -> OrchestratorModelConfig:
    """
    Load VOXY Orchestrator configuration from environment variables.

    Environment Variables:
        ORCHESTRATOR_PROVIDER: Provider name (default: "openrouter")
        ORCHESTRATOR_MODEL: Model name (configured in .env - see .env.example)
        OPENROUTER_API_KEY: OpenRouter API key (required if provider=openrouter)
        OPENAI_API_KEY: OpenAI API key (required if provider=openai)
        ANTHROPIC_API_KEY: Anthropic API key (required if provider=anthropic)
        ORCHESTRATOR_MAX_TOKENS: Max tokens (default: 4000)
        ORCHESTRATOR_TEMPERATURE: Temperature (default: 0.3)
        ORCHESTRATOR_REASONING_EFFORT: Reasoning level (default: "medium")
        ORCHESTRATOR_THINKING_BUDGET_TOKENS: Claude Extended Thinking budget (default: 10000)
        ORCHESTRATOR_REASONING_ENABLED: Enable reasoning capture (default: true)
        ORCHESTRATOR_INCLUDE_USAGE: Track usage (default: true)
        ORCHESTRATOR_ENABLE_STREAMING: Enable streaming (default: false)

    Returns:
        OrchestratorModelConfig: Orchestrator configuration

    Raises:
        ValueError: If required configuration is missing
    """
    provider = os.getenv("ORCHESTRATOR_PROVIDER", "openrouter")
    model_name = os.getenv("ORCHESTRATOR_MODEL")

    if not model_name:
        raise ValueError(
            "ORCHESTRATOR_MODEL not configured. Please set in .env file. "
            "See .env.example for configuration options."
        )

    # Determine API key based on provider
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required when ORCHESTRATOR_PROVIDER=openrouter"
            )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when ORCHESTRATOR_PROVIDER=openai"
            )
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required when ORCHESTRATOR_PROVIDER=anthropic"
            )
    else:
        # For other providers, try provider-specific key
        api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
        if not api_key:
            raise ValueError(
                f"{provider.upper()}_API_KEY environment variable is required when ORCHESTRATOR_PROVIDER={provider}"
            )

    max_tokens = int(os.getenv("ORCHESTRATOR_MAX_TOKENS", "4000"))
    temperature = float(os.getenv("ORCHESTRATOR_TEMPERATURE", "0.3"))
    include_usage = os.getenv("ORCHESTRATOR_INCLUDE_USAGE", "true").lower() == "true"
    reasoning_effort = os.getenv("ORCHESTRATOR_REASONING_EFFORT", "medium")
    enable_streaming = (
        os.getenv("ORCHESTRATOR_ENABLE_STREAMING", "false").lower() == "true"
    )

    # Reasoning configuration (Claude Extended Thinking support)
    reasoning_enabled = (
        os.getenv("ORCHESTRATOR_REASONING_ENABLED", "true").lower() == "true"
    )
    thinking_budget = os.getenv("ORCHESTRATOR_THINKING_BUDGET_TOKENS")
    thinking_budget_tokens = int(thinking_budget) if thinking_budget else 10000

    return OrchestratorModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        include_usage=include_usage,
        agent_name="orchestrator",
        reasoning_effort=reasoning_effort,
        enable_streaming=enable_streaming,
        reasoning_enabled=reasoning_enabled,
        thinking_budget_tokens=thinking_budget_tokens,
    )
