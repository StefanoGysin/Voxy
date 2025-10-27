"""
Reasoning Configuration Module

Gerencia configurações de reasoning/thinking para diferentes provedores LLM.
Suporta Extended Thinking (Claude), Thinking Config (Gemini), Reasoning Effort (OpenAI).

Author: VOXY System
Date: 2025-10-14
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger


@dataclass
class ReasoningConfig:
    """
    Configuração universal de reasoning para LLM.

    Diferentes providers usam diferentes parâmetros:
    - Claude: thinking_budget_tokens
    - Gemini: gemini_thinking_budget
    - OpenAI: reasoning_effort
    - Grok/DeepSeek: reasoning_content (automático no response)
    """

    # Global settings
    enabled: bool = True
    strategy: str = "auto"  # auto, api, response_field, logs, stats

    # Claude Extended Thinking
    # Budget de tokens para thinking (10000 = ~10K tokens de raciocínio)
    thinking_budget_tokens: Optional[int] = None

    # Gemini Thinking Config
    # Budget para thinking (0-24576, -1 = auto)
    gemini_thinking_budget: Optional[int] = None

    # OpenAI Reasoning Effort
    # Níveis: "minimal", "low", "medium", "high"
    reasoning_effort: Optional[str] = None

    # Fallback settings
    enable_log_parsing: bool = True  # Fallback para providers sem API de reasoning

    def to_openrouter_params(self, provider: str, model: str) -> dict[str, Any]:
        """
        Converte config para formato OpenRouter unificado.

        OpenRouter usa parâmetro 'reasoning' unificado que funciona para TODOS os providers.
        Diferente de to_litellm_params() que usa formato provider-specific.

        Args:
            provider: Nome do provider (sempre 'openrouter' quando chamado)
            model: Nome do modelo (configurable via .env, e.g., anthropic/claude-sonnet-4.5)

        Returns:
            Dict com reasoning no formato OpenRouter unificado
        """
        if not self.enabled:
            return {}

        params: dict[str, Any] = {}
        reasoning_config: dict[str, Any] = {"enabled": True}

        # Prioridade 1: max_tokens (mais específico)
        if self.thinking_budget_tokens:
            reasoning_config["max_tokens"] = self.thinking_budget_tokens
        elif self.gemini_thinking_budget:
            reasoning_config["max_tokens"] = self.gemini_thinking_budget

        # Prioridade 2: effort (se não tem max_tokens)
        if self.reasoning_effort and "max_tokens" not in reasoning_config:
            reasoning_config["effort"] = self.reasoning_effort  # high/medium/low

        params["reasoning"] = reasoning_config

        logger.bind(event="REASONING_CONFIG|OPENROUTER").debug(
            "OpenRouter unified reasoning enabled", config=reasoning_config, model=model
        )

        return params

    def to_litellm_params(self, provider: str, model: str) -> dict[str, Any]:
        """
        Converte config para parâmetros LiteLLM conforme o provider.

        IMPORTANTE: Use to_openrouter_params() quando provider for 'openrouter'.
        Este método é para Anthropic/OpenAI/Google DIRETO.

        Args:
            provider: Nome do provider (anthropic, google, openai, etc.)
            model: Nome do modelo

        Returns:
            Dict com parâmetros extras para LiteLLM request
        """
        if not self.enabled:
            return {}

        # NOVO: Detectar OpenRouter e usar formato unificado
        if provider == "openrouter" or model.startswith("openrouter/"):
            return self.to_openrouter_params(provider, model)

        params: dict[str, Any] = {}

        # Claude Extended Thinking (ANTHROPIC DIRETO)
        if provider in ["anthropic", "claude"] or "claude" in model.lower():
            if self.thinking_budget_tokens:
                params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget_tokens,
                }

        # Gemini Thinking Config (GOOGLE DIRETO)
        elif provider in ["google", "gemini"] or "gemini" in model.lower():
            if self.gemini_thinking_budget is not None:
                params["thinking_config"] = {
                    "thinking_budget": self.gemini_thinking_budget
                }

        # OpenAI Reasoning Effort (OPENAI DIRETO)
        elif (
            provider == "openai" or model.startswith("gpt-") or model.startswith("o1-")
        ):
            if self.reasoning_effort:
                params["reasoning_effort"] = self.reasoning_effort

        return params

    def get_metadata(self) -> dict[str, Any]:
        """Retorna metadata de reasoning para logging."""
        return {
            "enabled": self.enabled,
            "strategy": self.strategy,
            "thinking_budget_tokens": self.thinking_budget_tokens,
            "gemini_thinking_budget": self.gemini_thinking_budget,
            "reasoning_effort": self.reasoning_effort,
            "enable_log_parsing": self.enable_log_parsing,
        }


# ============================================================================
# Configuration Loaders
# ============================================================================


def load_orchestrator_reasoning_config() -> ReasoningConfig:
    """Carrega configuração de reasoning para VOXY Orchestrator."""
    enabled = os.getenv("ORCHESTRATOR_REASONING_ENABLED", "true").lower() == "true"

    # Claude Extended Thinking (default para Orchestrator)
    thinking_budget = os.getenv("ORCHESTRATOR_THINKING_BUDGET_TOKENS")
    thinking_budget_int = int(thinking_budget) if thinking_budget else 10000

    # Gemini Thinking Config
    gemini_budget = os.getenv("ORCHESTRATOR_GEMINI_THINKING_BUDGET")
    gemini_budget_int = int(gemini_budget) if gemini_budget else None

    # OpenAI Reasoning Effort
    reasoning_effort = os.getenv("ORCHESTRATOR_REASONING_EFFORT")

    config = ReasoningConfig(
        enabled=enabled,
        thinking_budget_tokens=thinking_budget_int,
        gemini_thinking_budget=gemini_budget_int,
        reasoning_effort=reasoning_effort or "medium",
    )

    logger.bind(event="REASONING_CONFIG|ORCHESTRATOR_LOADED").info(
        "Orchestrator reasoning config loaded", **config.get_metadata()
    )

    return config


def load_vision_reasoning_config() -> ReasoningConfig:
    """Carrega configuração de reasoning para Vision Agent."""
    enabled = os.getenv("VISION_REASONING_ENABLED", "true").lower() == "true"

    # Claude/OpenAI Vision models usam thinking budget
    thinking_budget = os.getenv("VISION_THINKING_BUDGET_TOKENS")
    thinking_budget_int = int(thinking_budget) if thinking_budget else 8000

    # Gemini Vision
    gemini_budget = os.getenv("VISION_GEMINI_THINKING_BUDGET")
    gemini_budget_int = int(gemini_budget) if gemini_budget else None

    # OpenAI reasoning effort
    reasoning_effort = os.getenv("VISION_REASONING_EFFORT")

    config = ReasoningConfig(
        enabled=enabled,
        thinking_budget_tokens=thinking_budget_int,
        gemini_thinking_budget=gemini_budget_int,
        reasoning_effort=reasoning_effort or "medium",
    )

    logger.bind(event="REASONING_CONFIG|VISION_LOADED").info(
        "Vision Agent reasoning config loaded", **config.get_metadata()
    )

    return config


def load_calculator_reasoning_config() -> ReasoningConfig:
    """Carrega configuração de reasoning para Calculator Agent."""
    enabled = os.getenv("CALCULATOR_REASONING_ENABLED", "true").lower() == "true"

    # Grok Code Fast 1 suporta reasoning_content automaticamente
    # Não precisa de parâmetros extras, mas podemos controlar via flags

    config = ReasoningConfig(
        enabled=enabled,
        strategy="response_field",  # Grok retorna reasoning_content
        enable_log_parsing=True,  # Fallback
    )

    logger.bind(event="REASONING_CONFIG|CALCULATOR_LOADED").info(
        "Calculator Agent reasoning config loaded", **config.get_metadata()
    )

    return config


def load_corrector_reasoning_config() -> ReasoningConfig:
    """Carrega configuração de reasoning para Corrector Agent."""
    enabled = os.getenv("CORRECTOR_REASONING_ENABLED", "false").lower() == "true"

    # Gemini Flash pode usar thinking config se habilitado
    gemini_budget = os.getenv("CORRECTOR_GEMINI_THINKING_BUDGET")
    gemini_budget_int = int(gemini_budget) if gemini_budget else 512

    config = ReasoningConfig(
        enabled=enabled,
        gemini_thinking_budget=gemini_budget_int if enabled else None,
        enable_log_parsing=True,
    )

    logger.bind(event="REASONING_CONFIG|CORRECTOR_LOADED").info(
        "Corrector Agent reasoning config loaded", **config.get_metadata()
    )

    return config


def load_translator_reasoning_config() -> ReasoningConfig:
    """Carrega configuração de reasoning para Translator Agent."""
    enabled = os.getenv("TRANSLATOR_REASONING_ENABLED", "false").lower() == "true"

    # Gemini Pro pode usar thinking config se habilitado
    gemini_budget = os.getenv("TRANSLATOR_GEMINI_THINKING_BUDGET")
    gemini_budget_int = int(gemini_budget) if gemini_budget else 1024

    config = ReasoningConfig(
        enabled=enabled,
        gemini_thinking_budget=gemini_budget_int if enabled else None,
        enable_log_parsing=True,
    )

    logger.bind(event="REASONING_CONFIG|TRANSLATOR_LOADED").info(
        "Translator Agent reasoning config loaded", **config.get_metadata()
    )

    return config


def load_weather_reasoning_config() -> ReasoningConfig:
    """Carrega configuração de reasoning para Weather Agent."""
    # Weather Agent não precisa de reasoning (apenas consulta API)
    enabled = os.getenv("WEATHER_REASONING_ENABLED", "false").lower() == "true"

    config = ReasoningConfig(enabled=enabled, strategy="none", enable_log_parsing=False)

    logger.bind(event="REASONING_CONFIG|WEATHER_LOADED").debug(
        "Weather Agent reasoning config loaded (disabled by default)"
    )

    return config


def load_generic_reasoning_config(agent_name: str) -> ReasoningConfig:
    """
    Carrega configuração genérica de reasoning para agentes customizados.

    Args:
        agent_name: Nome do agente (usado para buscar env vars)

    Returns:
        ReasoningConfig com configuração padrão
    """
    prefix = agent_name.upper()

    enabled = os.getenv(f"{prefix}_REASONING_ENABLED", "false").lower() == "true"

    thinking_budget = os.getenv(f"{prefix}_THINKING_BUDGET_TOKENS")
    thinking_budget_int = int(thinking_budget) if thinking_budget else None

    gemini_budget = os.getenv(f"{prefix}_GEMINI_THINKING_BUDGET")
    gemini_budget_int = int(gemini_budget) if gemini_budget else None

    reasoning_effort = os.getenv(f"{prefix}_REASONING_EFFORT")

    config = ReasoningConfig(
        enabled=enabled,
        thinking_budget_tokens=thinking_budget_int,
        gemini_thinking_budget=gemini_budget_int,
        reasoning_effort=reasoning_effort,
        enable_log_parsing=True,
    )

    logger.bind(event="REASONING_CONFIG|GENERIC_LOADED").info(
        f"{agent_name} reasoning config loaded", **config.get_metadata()
    )

    return config


# ============================================================================
# Reasoning Config Factory
# ============================================================================

_REASONING_CONFIG_LOADERS = {
    "orchestrator": load_orchestrator_reasoning_config,
    "vision": load_vision_reasoning_config,
    "calculator": load_calculator_reasoning_config,
    "corrector": load_corrector_reasoning_config,
    "translator": load_translator_reasoning_config,
    "weather": load_weather_reasoning_config,
}


def get_reasoning_config(agent_name: str) -> ReasoningConfig:
    """
    Factory function para obter reasoning config por nome do agente.

    Args:
        agent_name: Nome do agente (orchestrator, vision, calculator, etc.)

    Returns:
        ReasoningConfig apropriado para o agente
    """
    loader = _REASONING_CONFIG_LOADERS.get(agent_name.lower())

    if loader:
        return loader()
    else:
        logger.bind(event="REASONING_CONFIG|GENERIC_FALLBACK").warning(
            f"No specific reasoning config for '{agent_name}', using generic"
        )
        return load_generic_reasoning_config(agent_name)
