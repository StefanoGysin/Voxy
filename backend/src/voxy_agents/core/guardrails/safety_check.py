"""
Safety Checker for VOXY Agents

Simple safety validation for user inputs.
"""

import logging
import re

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Simple safety checker for user inputs."""

    def __init__(self):
        """Initialize safety checker with basic rules."""
        # Basic inappropriate content patterns
        self.blocked_patterns = [
            r"\b(hate|violence|harm)\b",
            r"\b(illegal|drugs|weapons)\b",
            # Add more patterns as needed
        ]

        logger.info("Safety checker initialized")

    async def is_safe(self, text: str) -> bool:
        """
        Check if input text is safe.

        Args:
            text: Text to check

        Returns:
            True if safe, False if potentially harmful
        """
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower()

        # Check against blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Potentially unsafe content detected: {pattern}")
                return False

        # Basic length check
        if len(text) > 10000:  # Reasonable limit
            logger.warning("Input text too long")
            return False

        return True
