"""
Session Manager for VOXY system.

Manages conversation sessions, context, and memory for multi-agent workflows.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

# For now, we'll use in-memory storage. In production, this would use Supabase/Redis
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user sessions and conversation context.

    Responsibilities:
    - Track conversation history
    - Manage context compression
    - Store session metadata
    - Handle session lifecycle
    """

    def __init__(self):
        # In-memory storage (replace with Supabase in production)
        self.sessions: dict[str, dict[str, Any]] = {}
        self.max_session_age = timedelta(hours=24)
        self.max_context_messages = 20

        logger.info("Session Manager initialized with in-memory storage")

    async def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new session.

        Args:
            user_id: Optional user identifier

        Returns:
            Session ID
        """
        session_id = str(uuid4())

        session_data = {
            "id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "interactions": [],
            "context": {
                "recent_interactions": [],
                "topics": [],
                "preferences": {},
                "tool_usage": {},
            },
            "metadata": {
                "total_requests": 0,
                "total_cost": 0.0,
                "successful_requests": 0,
                "failed_requests": 0,
            },
        }

        self.sessions[session_id] = session_data
        logger.info(f"Created new session: {session_id}")

        return session_id

    async def get_context(self, session_id: str) -> dict[str, Any]:
        """
        Get context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Session context dictionary
        """
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return {}

        session = self.sessions[session_id]

        # Update last activity
        session["last_activity"] = datetime.now()

        return session["context"]

    async def add_interaction(
        self,
        session_id: str,
        user_input: str,
        response: str,
        workflow_results: dict[str, Any],
    ) -> None:
        """
        Add an interaction to the session.

        Args:
            session_id: Session identifier
            user_input: User's input
            response: VOXY's response
            workflow_results: Results from the workflow
        """
        if session_id not in self.sessions:
            logger.warning(f"Session not found for interaction: {session_id}")
            return

        session = self.sessions[session_id]

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "workflow_results": workflow_results,
            "tools_used": list(workflow_results.get("results", {}).keys()),
        }

        # Add to interactions
        session["interactions"].append(interaction)

        # Update context
        await self._update_context(session_id, interaction)

        # Update metadata
        session["metadata"]["total_requests"] += 1
        if workflow_results.get("results"):
            session["metadata"]["successful_requests"] += 1
        else:
            session["metadata"]["failed_requests"] += 1

        # Add cost if available
        if "estimated_cost" in workflow_results:
            session["metadata"]["total_cost"] += workflow_results["estimated_cost"]

        logger.debug(f"Added interaction to session {session_id}")

    async def _update_context(
        self, session_id: str, interaction: dict[str, Any]
    ) -> None:
        """Update session context based on new interaction."""
        session = self.sessions[session_id]
        context = session["context"]

        # Add to recent interactions (keep only last N)
        context["recent_interactions"].append(
            {
                "user": interaction["user_input"][:200],  # Truncate for context
                "assistant": interaction["response"][:200],
                "tools": interaction["tools_used"],
            }
        )

        # Keep only recent interactions
        if len(context["recent_interactions"]) > self.max_context_messages:
            context["recent_interactions"] = context["recent_interactions"][
                -self.max_context_messages :
            ]

        # Update tool usage tracking
        for tool in interaction["tools_used"]:
            if tool in context["tool_usage"]:
                context["tool_usage"][tool] += 1
            else:
                context["tool_usage"][tool] = 1

        # Extract topics (simple keyword extraction)
        await self._extract_topics(session_id, interaction["user_input"])

    async def _extract_topics(self, session_id: str, user_input: str) -> None:
        """Extract and track topics from user input."""
        # Simple topic extraction (in production, use NLP)
        keywords = [
            "weather",
            "translate",
            "translation",
            "calculate",
            "math",
            "correct",
            "grammar",
            "forecast",
            "temperature",
            "rain",
        ]

        context = self.sessions[session_id]["context"]

        for keyword in keywords:
            if keyword.lower() in user_input.lower():
                if keyword not in context["topics"]:
                    context["topics"].append(keyword)

        # Keep only recent topics
        if len(context["topics"]) > 10:
            context["topics"] = context["topics"][-10:]

    async def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a session."""
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]

        return {
            "session_id": session_id,
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "duration": (
                session["last_activity"] - session["created_at"]
            ).total_seconds(),
            "total_interactions": len(session["interactions"]),
            "metadata": session["metadata"],
            "context_summary": {
                "topics": session["context"]["topics"],
                "most_used_tools": sorted(
                    session["context"]["tool_usage"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5],
            },
        }

    async def cleanup_old_sessions(self) -> int:
        """Clean up old sessions and return count of cleaned sessions."""
        cutoff_time = datetime.now() - self.max_session_age
        old_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session["last_activity"] < cutoff_time
        ]

        for session_id in old_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")

        return len(old_sessions)

    async def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get summary of all active sessions."""
        summaries = []

        for session_id, session in self.sessions.items():
            summaries.append(
                {
                    "session_id": session_id,
                    "user_id": session.get("user_id"),
                    "created_at": session["created_at"].isoformat(),
                    "last_activity": session["last_activity"].isoformat(),
                    "interaction_count": len(session["interactions"]),
                    "total_cost": session["metadata"]["total_cost"],
                }
            )

        return summaries
