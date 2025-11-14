"""
Entry Router Node - LangGraph Implementation

Routes incoming messages to either:
- PATH1: Vision bypass (direct to vision agent when image_url + keywords detected)
- PATH2: Standard orchestrator flow (VOXY supervisor decides)

This preserves the dual-path logic from the original SDK implementation.

Reference: VOXY Orchestrator dual-path architecture
backend/src/voxy_agents/core/voxy_orchestrator.py
"""

import re
from typing import Literal

from langchain_core.messages import HumanMessage
from loguru import logger

from ..graph_state import VoxyState


def detect_vision_bypass(message: str, image_url: str | None) -> bool:
    """
    Detect if message should bypass orchestrator and go directly to vision agent.

    PATH1 Criteria (bypass):
    - image_url is provided
    - Message contains vision-related keywords

    Args:
        message: User message text
        image_url: Optional image URL

    Returns:
        True if should bypass to vision agent, False otherwise

    Examples:
        >>> detect_vision_bypass("What is this?", "https://example.com/img.jpg")
        True

        >>> detect_vision_bypass("Translate hello", None)
        False

        >>> detect_vision_bypass("Analyze this image", "https://example.com/img.jpg")
        True
    """
    if not image_url:
        return False

    # Vision-related keywords (case-insensitive)
    vision_keywords = [
        r"\bimage\b",
        r"\bphoto\b",
        r"\bpicture\b",
        r"\banalyze\b",
        r"\banalise\b",
        r"\bdescribe\b",
        r"\bdescreva\b",
        r"\bwhat.*see\b",
        r"\bwhat.*this\b",
        r"\bwhat.*in\b",
        r"\bidentify\b",
        r"\bidentifique\b",
        r"\bocr\b",
        r"\bread.*text\b",
        r"\bemoji\b",
    ]

    message_lower = message.lower()

    for keyword_pattern in vision_keywords:
        if re.search(keyword_pattern, message_lower):
            logger.bind(event="LANGGRAPH|ENTRY_ROUTER").info(
                "Vision bypass detected",
                keyword_matched=keyword_pattern,
                has_image_url=bool(image_url),
            )
            return True

    return False


def entry_router(state: VoxyState) -> Literal["vision_bypass", "supervisor"]:
    """
    Entry router node - decides PATH1 (bypass) vs PATH2 (supervisor).

    Args:
        state: Current VoxyState

    Returns:
        "vision_bypass" for PATH1, "supervisor" for PATH2

    Example:
        >>> state = {
        ...     "messages": [{"role": "user", "content": "What is this image?"}],
        ...     "context": {"image_url": "https://example.com/img.jpg"}
        ... }
        >>> entry_router(state)
        'vision_bypass'
    """
    # Extract latest user message
    messages = state["messages"]
    if not messages:
        logger.bind(event="LANGGRAPH|ENTRY_ROUTER").warning("No messages in state")
        return "supervisor"

    # Get last message content
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        message_content = last_message.content
    elif isinstance(last_message, dict):
        message_content = last_message.get("content", "")
    else:
        message_content = str(last_message)

    # Ensure message_content is a string (handle list case from LangChain)
    if isinstance(message_content, list):
        # Convert list to string (join if multiple items)
        message_content = " ".join(str(item) for item in message_content)

    # Check for image_url in context or state
    image_url = state.get("context", {}).get("image_url")

    # Detect vision bypass
    should_bypass = detect_vision_bypass(message_content, image_url)

    if should_bypass:
        logger.bind(event="LANGGRAPH|ENTRY_ROUTER").info(
            "Routing to PATH1 (vision bypass)",
            message_length=len(message_content),
            has_image=bool(image_url),
        )
        return "vision_bypass"
    else:
        logger.bind(event="LANGGRAPH|ENTRY_ROUTER").info(
            "Routing to PATH2 (supervisor)",
            message_length=len(message_content),
            has_image=bool(image_url),
        )
        return "supervisor"
