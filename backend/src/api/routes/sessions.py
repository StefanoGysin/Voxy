"""
Session management routes for VOXY Agents.
Consolidated with historical chat_history.py functionality.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel

from src.api.models import (
    MessageResponse,
    MessagesListResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from src.integrations.supabase.database import SupabaseIntegration
from src.integrations.supabase.models import SessionDetail, SessionSummary
from src.platform.auth import User, get_current_active_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    """Create session request model."""

    title: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Create session response model."""

    id: str
    title: str
    message: str = "Session created successfully"


class UpdateSessionRequest(BaseModel):
    """Update session request model."""

    title: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


# Shared models imported from api.models:
# - MessageResponse
# - MessagesListResponse
# - SearchRequest
# - SearchResultItem
# - SearchResponse


@router.get("/", response_model=list[SessionSummary])
async def get_user_sessions(
    limit: int = Query(50, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get chat sessions for the current user.

    Returns a list of session summaries with basic information.
    """
    db = SupabaseIntegration()

    try:
        sessions = await db.get_user_sessions(
            user_id=current_user.id, limit=limit, offset=offset
        )
        return sessions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}",
        )


@router.post("/", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Create a new chat session.

    Returns the created session information.
    """
    db = SupabaseIntegration()

    try:
        session = await db.create_session(user_id=current_user.id, title=request.title)

        return CreateSessionResponse(
            id=session.id, title=session.title or "Untitled Session"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific session.

    Returns the session with all its messages.
    """
    db = SupabaseIntegration()

    try:
        session = await db.get_session_detail(
            session_id=session_id, user_id=current_user.id
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}",
        )


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update session information.

    Supports updating the session title and metadata.
    """
    db = SupabaseIntegration()

    try:
        # Only update title if provided
        if request.title is not None:
            success = await db.update_session_title(
                session_id=session_id, user_id=current_user.id, title=request.title
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
                )

        return {"message": "Session updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}",
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Delete a chat session and all its messages.

    This action cannot be undone.
    """
    db = SupabaseIntegration()

    try:
        success = await db.delete_session(
            session_id=session_id, user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}",
        )


# ===== MESSAGE ENDPOINTS (Consolidated from chat_history.py) =====


@router.get("/{session_id}/messages", response_model=MessagesListResponse)
async def get_session_messages(
    session_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Messages per page"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get messages for a specific session with pagination.

    Returns messages in chronological order (oldest first).
    """
    db = SupabaseIntegration()

    try:
        # Verify session belongs to user and get session context
        session = await db.get_session_detail(
            session_id=session_id, user_id=current_user.id
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        # Get messages with pagination using existing methods
        session_context = await db.get_session_context(
            session_id=session_id, limit=per_page
        )

        # Apply offset manually since method doesn't support it
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_context = session_context[start_idx:end_idx]

        # Convert to response format
        messages = []
        for msg in paginated_context:
            messages.append(
                MessageResponse(
                    id=msg["id"],
                    session_id=msg["session_id"],
                    content=msg["content"],
                    role=msg["role"],
                    agent_type=msg.get("agent_type"),
                    metadata=msg.get("metadata") or {},
                    created_at=msg["created_at"],
                )
            )

        # Get total count (simplified - in production would be optimized)
        total_context = await db.get_session_context(session_id=session_id, limit=1000)
        total = len(total_context)

        return MessagesListResponse(
            messages=messages,
            total=total,
            page=page,
            per_page=per_page,
            has_next=page * per_page < total,
            has_prev=page > 1,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(event="SESSIONS_API|ERROR").error(
            "Error getting session messages",
            error_type=type(e).__name__,
            error_msg=str(e),
            session_id=session_id,
            user_id=current_user.id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )


@router.post("/search", response_model=SearchResponse)
async def search_user_messages(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Search messages across all user sessions or within a specific session.

    Provides simple text search with basic relevance scoring.
    """
    db = SupabaseIntegration()

    try:
        # This is a simplified implementation
        # In production, you'd want full-text search with proper indexing

        if request.session_id:
            # Search within specific session - verify ownership
            session = await db.get_session_detail(
                session_id=request.session_id, user_id=current_user.id
            )
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
                )

            # Get session messages and filter
            session_context = await db.get_session_context(
                session_id=request.session_id, limit=request.limit
            )

            matching_messages = [
                msg
                for msg in session_context
                if request.query.lower() in msg["content"].lower()
            ]

        else:
            # Search across all user sessions
            user_sessions = await db.get_user_sessions(
                user_id=current_user.id, limit=100
            )

            matching_messages = []
            for session_summary in user_sessions:
                session_context = await db.get_session_context(
                    session_id=session_summary.id, limit=50
                )

                session_matches = [
                    msg
                    for msg in session_context
                    if request.query.lower() in msg["content"].lower()
                ]
                matching_messages.extend(session_matches)

            # Limit results
            matching_messages = matching_messages[: request.limit]

        # Convert to search results
        search_results = []
        for msg in matching_messages:
            # Get session title for context
            session_title = "Unknown Session"
            try:
                session_detail = await db.get_session_detail(
                    session_id=msg["session_id"], user_id=current_user.id
                )
                if session_detail:
                    session_title = session_detail.title or "Untitled Session"
            except Exception:
                pass  # Keep default title

            # Simple highlighting
            highlighted_content = msg["content"].replace(
                request.query, f"<mark>{request.query}</mark>"
            )

            search_results.append(
                SearchResultItem(
                    id=msg["id"],
                    session_id=msg["session_id"],
                    session_title=session_title,
                    content=msg["content"],
                    highlighted_content=highlighted_content,
                    role=msg["role"],
                    agent_type=msg.get("agent_type"),
                    metadata=msg.get("metadata") or {},
                    relevance_score=0.75,  # Simplified scoring
                    created_at=msg["created_at"],
                )
            )

        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(event="SESSIONS_API|ERROR").error(
            "Error searching messages",
            error_type=type(e).__name__,
            error_msg=str(e),
            user_id=current_user.id,
            query=request.query,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for session management."""
    return {
        "status": "healthy",
        "service": "session-management",
        "features": ["sessions", "messages", "search"],
    }
