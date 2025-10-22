"""
Global message management and search routes for VOXY Agents.
Provides cross-session message operations with authentication.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ...core.database.supabase_integration import SupabaseIntegration
from ..middleware.auth import User, get_current_active_user
from ..models import (
    MessageResponse,
    MessagesListResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


# Shared models imported from api.models:
# - MessageResponse
# - MessagesListResponse
# - SearchRequest
# - SearchResultItem
# - SearchResponse


class MessageStatsResponse(BaseModel):
    """User message statistics."""

    total_messages: int
    user_messages: int
    assistant_messages: int
    sessions_count: int
    agents_used: list[str]
    date_range: dict[str, Optional[datetime]]
    top_agents: list[dict[str, Any]]


@router.get("/", response_model=MessagesListResponse)
async def get_user_messages(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Messages per page"),
    role_filter: Optional[str] = Query(
        None, description="Filter by role (user/assistant)"
    ),
    agent_filter: Optional[str] = Query(None, description="Filter by agent type"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all messages for the authenticated user across all sessions.

    Supports pagination and basic filtering by role and agent type.
    """
    db = SupabaseIntegration()

    try:
        # Get user sessions first
        user_sessions = await db.get_user_sessions(
            user_id=current_user.id, limit=1000  # Get all user sessions
        )

        if not user_sessions:
            return MessagesListResponse(
                messages=[],
                total=0,
                page=page,
                per_page=per_page,
                has_next=False,
                has_prev=False,
            )

        # Collect all messages from all sessions
        all_messages = []
        session_titles = {}

        for session_summary in user_sessions:
            session_titles[session_summary.id] = session_summary.title

            # Get messages from this session
            session_context = await db.get_session_context(
                session_id=session_summary.id, limit=1000
            )

            for msg in session_context:
                # Apply filters
                if role_filter and msg.role != role_filter:
                    continue
                if agent_filter and msg.agent_type != agent_filter:
                    continue

                all_messages.append(msg)

        # Sort by creation date (newest first)
        all_messages.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total = len(all_messages)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_messages = all_messages[start_idx:end_idx]

        # Convert to response format
        messages = []
        for msg in paginated_messages:
            messages.append(
                MessageResponse(
                    id=msg.id,
                    session_id=msg.session_id,
                    session_title=session_titles.get(msg.session_id, "Unknown Session"),
                    content=msg.content,
                    role=msg.role,
                    agent_type=msg.agent_type,
                    metadata=msg.metadata or {},
                    created_at=msg.created_at,
                )
            )

        return MessagesListResponse(
            messages=messages,
            total=total,
            page=page,
            per_page=per_page,
            has_next=end_idx < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Error getting user messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )


@router.post("/search", response_model=SearchResponse)
async def advanced_search_messages(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Advanced search across all user messages with filtering and context.

    Provides relevance scoring, highlighting, and message context.
    """
    start_time = datetime.now()
    db = SupabaseIntegration()

    try:
        # Get target sessions
        if request.session_ids:
            # Verify user owns all specified sessions
            target_sessions = []
            for session_id in request.session_ids:
                session = await db.get_session_detail(
                    session_id=session_id, user_id=current_user.id
                )
                if session:
                    target_sessions.append(session)

            if not target_sessions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No accessible sessions found",
                )
        else:
            # Search across all user sessions
            user_sessions = await db.get_user_sessions(
                user_id=current_user.id, limit=1000
            )
            target_sessions = []
            for session_summary in user_sessions:
                session_detail = await db.get_session_detail(
                    session_id=session_summary.id, user_id=current_user.id
                )
                if session_detail:
                    target_sessions.append(session_detail)

        # Search through messages
        matching_messages = []
        all_messages_by_session = {}  # For context lookup

        for session in target_sessions:
            session_context = await db.get_session_context(
                session_id=session.id, limit=1000
            )
            all_messages_by_session[session.id] = session_context

            for i, msg in enumerate(session_context):
                # Apply text search
                if request.query.lower() not in msg.content.lower():
                    continue

                # Apply filters
                if request.role_filter and msg.role != request.role_filter:
                    continue
                if request.agent_filter and msg.agent_type != request.agent_filter:
                    continue
                if request.date_from and msg.created_at < request.date_from:
                    continue
                if request.date_to and msg.created_at > request.date_to:
                    continue

                # Calculate relevance (simple scoring)
                relevance = 0.5
                query_words = request.query.lower().split()
                content_lower = msg.content.lower()

                for word in query_words:
                    if word in content_lower:
                        relevance += 0.1
                        # Boost for exact matches
                        if word == request.query.lower():
                            relevance += 0.3

                relevance = min(relevance, 1.0)

                # Get context messages
                context_before = None
                context_after = None

                if i > 0:
                    context_before = session_context[i - 1].content[:100] + "..."
                if i < len(session_context) - 1:
                    context_after = session_context[i + 1].content[:100] + "..."

                # Create search result
                highlighted_content = msg.content
                for word in query_words:
                    highlighted_content = highlighted_content.replace(
                        word, f"<mark>{word}</mark>"
                    )
                    highlighted_content = highlighted_content.replace(
                        word.capitalize(), f"<mark>{word.capitalize()}</mark>"
                    )

                matching_messages.append(
                    {
                        "message": msg,
                        "session": session,
                        "relevance": relevance,
                        "highlighted_content": highlighted_content,
                        "context_before": context_before,
                        "context_after": context_after,
                    }
                )

        # Sort by relevance and date
        matching_messages.sort(
            key=lambda x: (x["relevance"], x["message"].created_at), reverse=True
        )

        # Apply limit
        matching_messages = matching_messages[: request.limit]

        # Convert to response format
        search_results = []
        for match in matching_messages:
            msg = match["message"]
            session = match["session"]

            search_results.append(
                SearchResultItem(
                    id=msg.id,
                    session_id=msg.session_id,
                    session_title=session.title or "Untitled Session",
                    content=msg.content,
                    highlighted_content=match["highlighted_content"],
                    role=msg.role,
                    agent_type=msg.agent_type,
                    metadata=msg.metadata or {},
                    relevance_score=match["relevance"],
                    created_at=msg.created_at,
                    context_before=match["context_before"],
                    context_after=match["context_after"],
                )
            )

        search_time = (datetime.now() - start_time).total_seconds() * 1000

        filters_applied = {
            "session_ids": request.session_ids,
            "role_filter": request.role_filter,
            "agent_filter": request.agent_filter,
            "date_from": request.date_from,
            "date_to": request.date_to,
        }

        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            filters_applied=filters_applied,
            search_time_ms=search_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/stats", response_model=MessageStatsResponse)
async def get_message_stats(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive statistics about user messages and agent usage.
    """
    db = SupabaseIntegration()

    try:
        # Get all user sessions
        user_sessions = await db.get_user_sessions(user_id=current_user.id, limit=1000)

        if not user_sessions:
            return MessageStatsResponse(
                total_messages=0,
                user_messages=0,
                assistant_messages=0,
                sessions_count=0,
                agents_used=[],
                date_range={"earliest": None, "latest": None},
                top_agents=[],
            )

        # Collect statistics
        total_messages = 0
        user_messages = 0
        assistant_messages = 0
        agents_used = set()
        agent_counts = {}
        earliest_date = None
        latest_date = None

        for session_summary in user_sessions:
            session_context = await db.get_session_context(
                session_id=session_summary.id, limit=1000
            )

            for msg in session_context:
                total_messages += 1

                if msg.role == "user":
                    user_messages += 1
                elif msg.role == "assistant":
                    assistant_messages += 1

                if msg.agent_type:
                    agents_used.add(msg.agent_type)
                    agent_counts[msg.agent_type] = (
                        agent_counts.get(msg.agent_type, 0) + 1
                    )

                # Track date range
                if earliest_date is None or msg.created_at < earliest_date:
                    earliest_date = msg.created_at
                if latest_date is None or msg.created_at > latest_date:
                    latest_date = msg.created_at

        # Top agents by usage
        top_agents = [
            {
                "agent": agent,
                "count": count,
                "percentage": round((count / total_messages) * 100, 2),
            }
            for agent, count in sorted(
                agent_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        return MessageStatsResponse(
            total_messages=total_messages,
            user_messages=user_messages,
            assistant_messages=assistant_messages,
            sessions_count=len(user_sessions),
            agents_used=list(agents_used),
            date_range={"earliest": earliest_date, "latest": latest_date},
            top_agents=top_agents,
        )

    except Exception as e:
        logger.error(f"Error getting message stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a specific message.

    Verifies user ownership through session validation.
    """
    db = SupabaseIntegration()

    try:
        # Delete the message using the new method
        success = await db.delete_message(
            message_id=message_id, user_id=current_user.id
        )

        if success:
            logger.info(
                f"Successfully deleted message {message_id} for user {current_user.id}"
            )
            return {
                "message": "Message deleted successfully",
                "message_id": message_id,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete message",
            )

    except ValueError as e:
        # Handle message not found or access denied
        logger.warning(f"Message deletion failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for message management."""
    return {
        "status": "healthy",
        "service": "message-management",
        "features": ["search", "statistics", "global-access", "context-aware"],
    }
