"""
Session management platform for VOXY Agents.

Provides conversation context tracking, interaction history, and session lifecycle management.

Public API:
    - SessionManager: Main session manager class
"""

from .session_manager import SessionManager

__all__ = ["SessionManager"]
