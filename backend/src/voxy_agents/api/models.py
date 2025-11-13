"""
Shared API models for VOXY Agents routes.

Centralizes Pydantic models that are used across multiple API routers
to eliminate duplication and prevent semantic drift between endpoints.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# ===== Message Models =====


class MessageResponse(BaseModel):
    """
    Unified message response model used across session and message endpoints.

    Used by:
    - /api/sessions/{session_id}/messages
    - /api/messages/
    """

    id: str
    session_id: str
    session_title: Optional[str] = None  # Included for cross-session contexts
    content: str
    role: str  # 'user' or 'assistant'
    agent_type: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MessagesListResponse(BaseModel):
    """
    Response model for paginated message lists.

    Used by:
    - /api/sessions/{session_id}/messages
    - /api/messages/
    """

    messages: list[MessageResponse]
    total: int
    page: int
    per_page: int
    has_next: bool = False
    has_prev: bool = False


# ===== Search Models =====


class SearchRequest(BaseModel):
    """
    Advanced search request model with comprehensive filtering options.

    Used by:
    - /api/sessions/search
    - /api/messages/search

    Supports both simple queries and advanced filtering by role, agent, dates, etc.
    """

    query: str = Field(..., min_length=1, description="Search query text")
    session_id: Optional[str] = Field(
        default=None, description="Limit search to specific session"
    )
    session_ids: Optional[list[str]] = Field(
        default=None, description="Limit search to multiple sessions"
    )
    role_filter: Optional[str] = Field(
        default=None, description="Filter by message role (user/assistant)"
    )
    agent_filter: Optional[str] = Field(
        default=None, description="Filter by agent type"
    )
    date_from: Optional[datetime] = Field(
        default=None, description="Search messages from this date onwards"
    )
    date_to: Optional[datetime] = Field(
        default=None, description="Search messages until this date"
    )
    limit: int = Field(
        default=50, ge=1, le=200, description="Maximum number of results"
    )


class SearchResultItem(BaseModel):
    """
    Individual search result with relevance scoring and context.

    Used by:
    - /api/sessions/search
    - /api/messages/search

    Includes highlighting, relevance scoring, and optional context messages.
    """

    id: str
    session_id: str
    session_title: Optional[str] = None
    content: str
    highlighted_content: Optional[str] = None
    role: str
    agent_type: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = 0.5
    created_at: datetime
    # Optional context fields for advanced search
    context_before: Optional[str] = None  # Previous message for context
    context_after: Optional[str] = None  # Next message for context


class SearchResponse(BaseModel):
    """
    Search response model with results and metadata.

    Used by:
    - /api/sessions/search
    - /api/messages/search
    """

    results: list[SearchResultItem]
    total: int
    query: str
    filters_applied: Optional[dict[str, Any]] = None  # For advanced search metadata
    search_time_ms: Optional[float] = None  # For performance tracking
