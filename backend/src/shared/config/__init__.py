"""
Shared configuration module for VOXY Agents system.

Migrated from voxy_agents/config/.
"""

from src.shared.config.models_config import (
    OrchestratorModelConfig,
    SubagentModelConfig,
    VisionModelConfig,
    load_calculator_config,
    load_corrector_config,
    load_orchestrator_config,
    load_translator_config,
    load_vision_config,
    load_weather_config,
)
from src.shared.config.settings import Settings, load_model_config, settings

__all__ = [
    "Settings",
    "settings",
    "load_model_config",
    "SubagentModelConfig",
    "VisionModelConfig",
    "OrchestratorModelConfig",
    "load_calculator_config",
    "load_corrector_config",
    "load_orchestrator_config",
    "load_translator_config",
    "load_vision_config",
    "load_weather_config",
]
