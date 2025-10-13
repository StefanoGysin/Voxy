"""
LLM Factory for VOXY Subagents.

Factory pattern for creating LLM model instances with support for multiple providers
through LiteLLM (OpenRouter, OpenAI, Anthropic, etc.).
"""

import logging
from typing import Optional

from agents.extensions.models.litellm_model import LitellmModel

from ..config.models_config import SubagentModelConfig

logger = logging.getLogger(__name__)


def create_litellm_model(config: SubagentModelConfig) -> LitellmModel:
    """
    Create a LiteLLM model instance from configuration.

    This factory function handles:
    - API key validation
    - Model path formatting (provider/model)
    - Error handling and logging
    - Provider-specific configurations

    Args:
        config: SubagentModelConfig with provider, model, and API key

    Returns:
        LitellmModel: Configured LiteLLM model instance

    Raises:
        ValueError: If API key is missing or configuration is invalid

    Example:
        >>> from voxy_agents.config.models_config import load_calculator_config
        >>> config = load_calculator_config()
        >>> model = create_litellm_model(config)
        >>> # Use model with Agent
        >>> agent = Agent(model=model, ...)
    """
    # Validate API key
    if not config.api_key:
        raise ValueError(
            f"API key is required for provider '{config.provider}'. "
            f"Please set the appropriate environment variable."
        )

    # Get formatted model path for LiteLLM
    model_path = config.get_litellm_model_path()

    # Log model creation (DEBUG level to reduce noise in production)
    logger.debug(
        f"Creating LiteLLM model: {model_path} "
        f"(max_tokens={config.max_tokens}, temperature={config.temperature})"
    )

    # Create LiteLLM model instance
    try:
        model = LitellmModel(
            model=model_path,
            api_key=config.api_key,
        )

        logger.debug(f"✓ LiteLLM model created successfully: {model_path}")
        return model

    except Exception as e:
        logger.error(f"✗ Failed to create LiteLLM model: {model_path}")
        logger.error(f"  Error: {str(e)}")
        raise


def create_openrouter_model(
    model_name: str,
    api_key: str,
    max_tokens: int = 2000,
    temperature: float = 0.1,
) -> LitellmModel:
    """
    Convenience function to create an OpenRouter model directly.

    Args:
        model_name: OpenRouter model name (e.g., "x-ai/grok-code-fast-1")
        api_key: OpenRouter API key
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        LitellmModel: Configured OpenRouter model instance

    Example:
        >>> model = create_openrouter_model(
        ...     model_name="x-ai/grok-code-fast-1",
        ...     api_key="sk-or-..."
        ... )
    """
    config = SubagentModelConfig(
        provider="openrouter",
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return create_litellm_model(config)


def create_openai_model(
    model_name: str,
    api_key: str,
    max_tokens: int = 2000,
    temperature: float = 0.1,
) -> LitellmModel:
    """
    Convenience function to create an OpenAI model directly.

    Args:
        model_name: OpenAI model name (e.g., "gpt-4o-mini")
        api_key: OpenAI API key
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        LitellmModel: Configured OpenAI model instance

    Example:
        >>> model = create_openai_model(
        ...     model_name="gpt-4o-mini",
        ...     api_key="sk-..."
        ... )
    """
    config = SubagentModelConfig(
        provider="openai",
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return create_litellm_model(config)


def get_model_info(model_path: str) -> dict:
    """
    Get information about a LiteLLM model path.

    Args:
        model_path: LiteLLM model path (e.g., "openrouter/x-ai/grok-code-fast-1")

    Returns:
        dict: Model information including provider and model name

    Example:
        >>> info = get_model_info("openrouter/x-ai/grok-code-fast-1")
        >>> print(info["provider"])  # "openrouter"
        >>> print(info["model"])     # "x-ai/grok-code-fast-1"
    """
    parts = model_path.split("/", 1)
    if len(parts) == 2:
        provider, model = parts
        return {
            "provider": provider,
            "model": model,
            "full_path": model_path,
        }
    else:
        return {
            "provider": "unknown",
            "model": model_path,
            "full_path": model_path,
        }
