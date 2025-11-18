"""
Base utilities for creating LangGraph nodes from agents.

This module provides helper functions to create LangGraph-compatible
node functions from agent classes, maintaining separation between
business logic (agents) and infrastructure (LangGraph).
"""

from typing import Any, Callable, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_litellm import ChatLiteLLM
from loguru import logger


def create_simple_node(
    agent_name: str,
    instructions_fn: Callable[[], str],
    llm_config,
) -> Callable:
    """
    Create a simple LangGraph node from instructions and config.

    This is a lightweight factory for agents that don't need complex
    state management. Suitable for stateless transformations like
    calculation, translation, correction.

    Args:
        agent_name: Name of the agent (for logging)
        instructions_fn: Function that returns system instructions
        llm_config: Model configuration object (from models_config.py)

    Returns:
        LangGraph node function compatible with StateGraph.add_node()

    Example:
        >>> def get_calculator_instructions():
        ...     return "You are a calculator..."
        >>>
        >>> config = load_calculator_config()
        >>> calculator_node = create_simple_node(
        ...     "calculator",
        ...     get_calculator_instructions,
        ...     config
        ... )
        >>> # Use in graph:
        >>> graph.add_node("calculator", calculator_node)
    """
    # Create LiteLLM model instance (once during node creation)
    litellm_model = ChatLiteLLM(
        model=llm_config.get_litellm_model_path(),
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
    )

    logger.bind(event="LANGGRAPH|NODE_INIT").info(
        f"{agent_name.capitalize()} node created",
        model=llm_config.get_litellm_model_path(),
        provider=llm_config.provider,
    )

    def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node function.

        Args:
            state: Current VoxyState with message history

        Returns:
            State update dict with agent response
        """
        # Extract messages
        messages = state.get("messages", [])
        if not messages:
            logger.bind(event=f"LANGGRAPH|{agent_name.upper()}_NODE").warning(
                "No messages in state"
            )
            return {"messages": [AIMessage(content="No input to process")]}

        # Build prompt: system instructions + conversation history
        system_message = SystemMessage(content=instructions_fn())
        prompt_messages = [system_message] + messages

        # Log invocation
        logger.bind(event=f"LANGGRAPH|{agent_name.upper()}_NODE").debug(
            f"Invoking {agent_name} model",
            model=llm_config.get_litellm_model_path(),
            message_count=len(prompt_messages),
        )

        # Call LLM
        response = litellm_model.invoke(prompt_messages)

        # Log completion
        logger.bind(event=f"LANGGRAPH|{agent_name.upper()}_NODE").info(
            f"{agent_name.capitalize()} completed",
            response_length=len(response.content) if hasattr(response, "content") else 0,
        )

        # Return state update
        return {"messages": [response]}

    return node_function


def create_lazy_node(
    node_factory: Callable[[], Callable]
) -> Callable:
    """
    Create a lazy-initialized node wrapper.

    Delays node creation until first use, useful for expensive
    initialization or when you want to control when models are loaded.

    Args:
        node_factory: Function that creates the actual node

    Returns:
        Wrapped node function with lazy initialization

    Example:
        >>> def create_expensive_node():
        ...     # Heavy initialization here
        ...     return node_function
        >>>
        >>> lazy_node = create_lazy_node(create_expensive_node)
        >>> # Node is only created when first called
        >>> graph.add_node("expensive", lazy_node)
    """
    _instance = None

    def lazy_wrapper(*args, **kwargs):
        nonlocal _instance
        if _instance is None:
            _instance = node_factory()
        return _instance(*args, **kwargs)

    return lazy_wrapper


# Singleton pattern for global node instances
_node_instances: Dict[str, Callable] = {}


def get_or_create_node(
    node_name: str,
    factory: Callable[[], Callable]
) -> Callable:
    """
    Get cached node instance or create new one.

    Implements singleton pattern for node instances to avoid
    recreating expensive resources (LLM clients, etc.).

    Args:
        node_name: Unique identifier for this node
        factory: Function that creates the node if not cached

    Returns:
        Node function (cached or newly created)

    Example:
        >>> calculator = get_or_create_node(
        ...     "calculator",
        ...     create_calculator_node
        ... )
        >>> # Second call returns same instance:
        >>> same_calculator = get_or_create_node(
        ...     "calculator",
        ...     create_calculator_node
        ... )
        >>> assert calculator is same_calculator
    """
    if node_name not in _node_instances:
        _node_instances[node_name] = factory()
        logger.bind(event="NODE_CACHE").debug(
            f"Created and cached node: {node_name}"
        )
    return _node_instances[node_name]
