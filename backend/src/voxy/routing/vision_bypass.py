"""
Vision Bypass Node - LangGraph Implementation

PATH1 implementation - bypasses orchestrator and goes directly to vision agent.
Migrated from voxy_agents/langgraph/nodes/vision_bypass.py to voxy/routing/.
"""

from typing import Any

from langchain_core.messages import AIMessage
from loguru import logger

from agents.vision import create_vision_node
from voxy_agents.langgraph.graph_state import VoxyState, update_context


def vision_bypass_node(state: VoxyState) -> dict[str, Any]:
    """
    Vision bypass node - PATH1 direct execution with actual Vision Agent.

    Invokes the Vision Agent node directly for image analysis without
    going through the supervisor orchestrator.

    Args:
        state: Current VoxyState with image_url in context

    Returns:
        State update with vision analysis result

    Example:
        >>> state = {
        ...     "messages": [{"role": "user", "content": "What is this?"}],
        ...     "context": {"image_url": "https://example.com/img.jpg"}
        ... }
        >>> result = vision_bypass_node(state)
        >>> "vision_analysis" in result["context"]
        True
    """
    # Extract image_url from context
    image_url = state.get("context", {}).get("image_url")

    logger.bind(event="LANGGRAPH|VISION_BYPASS").info(
        "Vision bypass node executing (PATH1 - direct to Vision Agent)",
        has_image_url=bool(image_url),
    )

    if not image_url:
        # No image URL - return error message
        response = AIMessage(
            content="I notice you want image analysis, but no image URL was provided. Please provide an image URL."
        )

        logger.bind(event="LANGGRAPH|VISION_BYPASS").warning(
            "No image URL in context for vision bypass"
        )

        return {"messages": [response]}

    # Invoke actual Vision Agent node
    vision_node = create_vision_node()
    result = vision_node(state)

    # Extract vision analysis from response
    if result.get("messages"):
        last_message = result["messages"][-1]
        analysis_content = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        # Store analysis metadata in context
        vision_analysis = {
            "image_url": image_url,
            "analysis_type": "direct_bypass",
            "result": analysis_content,
        }

        logger.bind(event="LANGGRAPH|VISION_BYPASS").info(
            "Vision bypass completed",
            image_url_length=len(image_url),
            analysis_length=len(analysis_content),
        )

        # Update context with vision analysis AND route_taken
        updated_context = update_context(
            state,
            vision_analysis=vision_analysis,
            route_taken="PATH_1",  # Mark PATH1 for observability
        )

        return {
            "messages": result["messages"],
            **updated_context,
        }
    else:
        # Fallback if no messages returned
        logger.bind(event="LANGGRAPH|VISION_BYPASS").warning(
            "Vision node returned no messages"
        )
        return result
