"""
Base classes and utilities for VOXY agents.

This module provides base functionality for all agents in the system,
following the separation of concerns principle:
- Agent classes: Pure business logic (testable independently)
- Node functions: LangGraph integration (infrastructure)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from loguru import logger


class BaseAgent(ABC):
    """
    Abstract base class for VOXY agents.

    Agents implement pure business logic for specific tasks (calculation,
    translation, etc.) and can be tested independently of LangGraph.

    The agent is responsible for:
    - Building prompts with specialized instructions
    - Calling LLM with appropriate parameters
    - Processing and validating responses
    - Returning structured results

    Example:
        >>> class MyAgent(BaseAgent):
        ...     def get_instructions(self) -> str:
        ...         return "You are a helpful assistant"
        ...
        ...     async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        ...         # Implementation here
        ...         pass
    """

    def __init__(self, llm: BaseChatModel, agent_name: str):
        """
        Initialize base agent.

        Args:
            llm: LangChain chat model instance (e.g., ChatLiteLLM)
            agent_name: Name of the agent for logging purposes
        """
        self.llm = llm
        self.agent_name = agent_name
        self.logger = logger.bind(agent=agent_name)

    @abstractmethod
    def get_instructions(self) -> str:
        """
        Get specialized instructions for this agent.

        Returns:
            System prompt with agent-specific instructions

        Note:
            This should be implemented by each agent with their
            specialized capabilities and guidelines.
        """
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process agent logic.

        Args:
            input_data: Input data for processing (validated)

        Returns:
            Processing result with metadata

        Raises:
            ValueError: If input_data is invalid
            Exception: If processing fails

        Example:
            >>> result = await agent.process({
            ...     "message": "Calculate 2+2",
            ...     "context": {"user_id": "123"}
            ... })
            >>> result["response"]
            '2 + 2 = 4'
        """
        pass

    def log_info(self, message: str, **kwargs):
        """Log info message with agent context."""
        self.logger.info(f"[{self.agent_name}] {message}", **kwargs)

    def log_debug(self, message: str, **kwargs):
        """Log debug message with agent context."""
        self.logger.debug(f"[{self.agent_name}] {message}", **kwargs)

    def log_error(self, message: str, **kwargs):
        """Log error message with agent context."""
        self.logger.error(f"[{self.agent_name}] {message}", **kwargs)


class SyncAgent(ABC):
    """
    Synchronous version of BaseAgent for simpler use cases.

    Use this when your agent doesn't need async operations.
    Most agents should use BaseAgent (async) for consistency.
    """

    def __init__(self, llm: BaseChatModel, agent_name: str):
        self.llm = llm
        self.agent_name = agent_name
        self.logger = logger.bind(agent=agent_name)

    @abstractmethod
    def get_instructions(self) -> str:
        """Get specialized instructions for this agent."""
        pass

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent logic synchronously."""
        pass
