"""
Vision Bypass Node - LangGraph Implementation

PATH1 implementation - bypasses orchestrator and goes directly to vision agent.
This is a stub for Phase 2; full implementation in Phase 3.

Reference: VOXY Orchestrator dual-path architecture
backend/src/voxy_agents/core/voxy_orchestrator.py
"""

from typing import Any

from langchain_core.messages import AIMessage
from loguru import logger

from ..graph_state import VoxyState, update_context


def vision_bypass_node(state: VoxyState) -> dict[str, Any]:
    """
    Vision bypass node - PATH1 direct execution (stub for Phase 2).

    In Phase 3, this will invoke the actual Vision Agent.
    For now, returns a placeholder response.

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
        "Vision bypass node executing (Phase 2 stub)",
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

    # STUB: Phase 2 - return placeholder
    # Phase 3 will integrate actual VisionAgent.analyze_image()
    stub_response = AIMessage(
        content=f"[Phase 2 Stub] Vision analysis would be performed on: {image_url[:100]}..."
    )

    # Store stub analysis in context
    stub_analysis = {
        "image_url": image_url,
        "analysis_type": "stub",
        "result": "Phase 2 stub - full implementation in Phase 3",
    }

    logger.bind(event="LANGGRAPH|VISION_BYPASS").info(
        "Vision bypass stub completed", image_url_length=len(image_url)
    )

    # Update context with vision analysis
    updated_context = update_context(state, vision_analysis=stub_analysis)

    return {
        "messages": [stub_response],
        **updated_context,
    }
