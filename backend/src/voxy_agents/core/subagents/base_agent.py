"""
Base class for all subagents in the VOXY system.

This provides the common interface and functionality that all
specialized agents must implement.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel

from ...config.settings import model_config, settings

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Standardized response from an agent."""

    success: bool
    result: Any
    error_message: Optional[str] = None
    execution_time: float
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class BaseAgent(ABC):
    """
    Abstract base class for all VOXY subagents.

    All subagents inherit from this class and implement the execute method.
    This ensures consistent interface and provides common functionality.
    """

    def __init__(self, agent_name: str, model_tier: str = "high_performance"):
        """
        Initialize base agent.

        Args:
            agent_name: Name of the agent (e.g., "translator", "calculator")
            model_tier: Model tier to use ("ultra_efficient", "high_performance")
        """
        self.name = agent_name
        self.model_tier = model_tier
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Load model configuration
        self.model_config = model_config["models"]["subagents"][model_tier]
        self.model_name = self.model_config["name"]
        self.max_tokens = self.model_config["max_tokens"]
        self.temperature = self.model_config["temperature"]

        # Performance tracking
        self.total_cost = 0.0
        self.execution_count = 0
        self.total_execution_time = 0.0

        logger.info(
            f"{agent_name} agent initialized with {model_tier} tier ({self.model_name})"
        )

    @abstractmethod
    async def execute(
        self, arguments: dict[str, Any], session_id: str
    ) -> AgentResponse:
        """
        Execute the agent's main functionality.

        This is the main method that subclasses must implement.
        It should process the given arguments and return a standardized response.

        Args:
            arguments: Dictionary of arguments for the agent
            session_id: Current session identifier

        Returns:
            AgentResponse with the result and metadata
        """
        pass

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make a call to the configured LLM.

        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            response_format: Optional response format specification

        Returns:
            Dictionary with response and metadata
        """
        start_time = datetime.now()

        try:
            kwargs = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = await self.client.chat.completions.create(**kwargs)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Calculate cost
            cost = self._calculate_cost(response.usage)
            self.total_cost += cost
            self.execution_count += 1
            self.total_execution_time += execution_time

            return {
                "content": response.choices[0].message.content,
                "usage": response.usage,
                "execution_time": execution_time,
                "cost": cost,
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error calling LLM in {self.name}: {e}")
            raise

    def _calculate_cost(self, usage) -> float:
        """Calculate cost based on token usage."""
        if not usage:
            return 0.0

        input_cost = (usage.prompt_tokens / 1000) * self.model_config[
            "cost_per_input_token"
        ]
        output_cost = (usage.completion_tokens / 1000) * self.model_config[
            "cost_per_output_token"
        ]

        return input_cost + output_cost

    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics for this agent."""
        avg_execution_time = self.total_execution_time / max(1, self.execution_count)
        avg_cost = self.total_cost / max(1, self.execution_count)

        return {
            "name": self.name,
            "model_tier": self.model_tier,
            "model_name": self.model_name,
            "execution_count": self.execution_count,
            "total_cost": self.total_cost,
            "average_cost": avg_cost,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": avg_execution_time,
        }

    async def health_check(self) -> bool:
        """Perform a health check on the agent."""
        try:
            # Simple test call
            response = await self._call_llm(
                "You are a test agent.",
                "Respond with 'OK' if you're working correctly.",
            )
            return "OK" in response["content"]
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return False
