"""
LLM Factory for VOXY Subagents.

Factory pattern for creating LLM model instances with support for multiple providers
through LiteLLM (OpenRouter, OpenAI, Anthropic, etc.).
"""

import logging
from typing import Any, Optional

from agents import ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
from openai.types.shared import Reasoning

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
        model_name: OpenAI model name (configurable via .env, e.g., "gpt-4o-mini")
        api_key: OpenAI API key
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        LitellmModel: Configured OpenAI model instance

    Example:
        >>> model = create_openai_model(
        ...     model_name="gpt-4o-mini",  # Example - configurable via .env
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


def get_reasoning_params(config: SubagentModelConfig) -> dict[str, Any]:
    """
    Extract reasoning/thinking parameters from model configuration.

    These parameters should be passed to the Agent when running inference,
    not when creating the model instance.

    IMPORTANT: Detects OpenRouter provider and uses unified 'reasoning' format.
    For direct providers (anthropic, google, openai), uses provider-specific format.

    Args:
        config: SubagentModelConfig with reasoning configuration

    Returns:
        dict: Reasoning parameters for LiteLLM API call
            - For OpenRouter: {"reasoning": {"enabled": true, "max_tokens": 10000, "effort": "high"}}
            - For Claude (direct): {"thinking": {"type": "enabled", "budget_tokens": 10000}}
            - For Gemini (direct): {"thinking_config": {"thinking_budget": 1024}}
            - For OpenAI (direct): {"reasoning_effort": "medium"}
            - For others: {} (empty dict)

    Example:
        >>> config = load_orchestrator_config()
        >>> params = get_reasoning_params(config)
        >>> # Use with Agent's model_config or extra_params
        >>> runner = Runner(agent, additional_params=params)
    """
    if not config.reasoning_enabled:
        logger.debug("Reasoning disabled for this agent")
        return {}

    # Detect OpenRouter and use unified format
    model_path = config.get_litellm_model_path()
    if config.provider == "openrouter" or model_path.startswith("openrouter/"):
        # Import reasoning_config to use to_openrouter_params()
        from ..config.reasoning_config import get_reasoning_config

        # Extract agent name from config (e.g., "orchestrator", "vision", "calculator")
        # Determine agent name from model usage pattern
        if hasattr(config, "agent_name"):
            agent_name = config.agent_name
        else:
            # Fallback: try to infer from config context (will use generic loader)
            agent_name = "generic"

        reasoning_config = get_reasoning_config(agent_name)
        reasoning_params = reasoning_config.to_openrouter_params(
            provider=config.provider, model=model_path
        )
    else:
        # Use provider-specific format for direct providers
        reasoning_params = config.get_reasoning_params()

    if reasoning_params:
        logger.debug(
            f"Reasoning parameters extracted for {model_path}: "
            f"{list(reasoning_params.keys())}"
        )
    else:
        logger.debug(f"No reasoning parameters configured for {model_path}")

    return reasoning_params


def create_model_with_reasoning(
    config: SubagentModelConfig,
) -> tuple[LitellmModel, dict[str, Any]]:
    """
    Create LiteLLM model and extract reasoning parameters in one call.

    Convenience function that combines model creation and reasoning parameter extraction.

    Args:
        config: SubagentModelConfig with model and reasoning configuration

    Returns:
        tuple: (LitellmModel instance, reasoning parameters dict)

    Example:
        >>> config = load_orchestrator_config()
        >>> model, reasoning_params = create_model_with_reasoning(config)
        >>> # Use model with Agent, pass reasoning_params at runtime
        >>> agent = Agent(model=model, ...)
        >>> runner = Runner(agent)
        >>> result = runner.run(..., **reasoning_params)
    """
    model = create_litellm_model(config)
    reasoning_params = get_reasoning_params(config)

    return model, reasoning_params


def build_model_settings(
    config: SubagentModelConfig,
    reasoning_params: Optional[dict[str, Any]] = None,
) -> ModelSettings:
    """
    Build ModelSettings for a subagent, applying reasoning parameters when available.

    Args:
        config: Subagent model configuration.
        reasoning_params: Optional reasoning parameters extracted from configuration.

    Returns:
        ModelSettings configured with usage tracking, temperature, max_tokens, and
        provider-specific reasoning parameters.
    """
    extra_args: Optional[dict[str, Any]] = None
    reasoning_setting: Optional[Reasoning] = None

    if reasoning_params:
        # Shallow copy to avoid mutating caller state
        extra_args = dict(reasoning_params)

        # Convert OpenAI reasoning effort into ModelSettings.reasoning
        effort = extra_args.pop("reasoning_effort", None)
        if effort:
            reasoning_setting = Reasoning(effort=effort)

        if not extra_args:
            extra_args = None

    return ModelSettings(
        include_usage=config.include_usage,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        reasoning=reasoning_setting,
        extra_args=extra_args,
    )
