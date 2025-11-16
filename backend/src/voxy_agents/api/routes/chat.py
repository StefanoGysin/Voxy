"""
Chat routes for VOXY Agents with authentication and persistence.
Consolidated and secured - no unauthenticated endpoints.

Supports dual-engine architecture via VOXY_LANGGRAPH_ENABLED feature flag:
- SDK Engine: OpenAI Agents SDK orchestrator (default, production-ready)
- LangGraph Engine: LangGraph orchestrator (Phase 2-6 migration, POC/testing)
"""

import hashlib
import os
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from loguru import logger
from pydantic import BaseModel

from ...core.cache.redis_cache import get_redis_cache
from ...core.database.supabase_integration import SupabaseIntegration
from ...core.utils.id_generator import generate_unique_request_id

# LangGraph imports (Phase 2-6 migration)
from ...langgraph.checkpointer import CheckpointerType
from ...langgraph.orchestrator import get_langgraph_orchestrator
from ...main import get_voxy_system
from ..middleware.auth import User, get_current_active_user
from ..middleware.vision_rate_limiter import get_vision_rate_limiter

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model with authentication and vision support."""

    message: str
    session_id: Optional[str] = None
    image_url: Optional[str] = None  # Support for image analysis with Vision Agent


class ChatResponse(BaseModel):
    """Chat response model with vision analysis metadata and tools tracking."""

    response: str
    session_id: str
    request_id: str
    timestamp: datetime
    processing_time: float
    agent_type: Optional[str] = None
    tools_used: list[str] = []  # List of tools/subagents used
    cached: bool = False
    vision_metadata: Optional[dict] = (
        None  # Vision analysis metadata (model, cost, etc.)
    )


class WebSocketMessage(BaseModel):
    """WebSocket message model with vision support."""

    type: str  # 'chat', 'system', 'error', 'vision'
    message: str
    session_id: Optional[str] = None
    image_url: Optional[str] = None  # For vision analysis requests
    vision_metadata: Optional[dict] = None  # Vision analysis metadata


@router.post("/", response_model=ChatResponse)
async def chat_with_voxy(
    request: ChatRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Chat with VOXY system with authentication and persistence.

    Saves user messages and responses to the database and uses Redis cache.
    """
    start_time = datetime.now()
    request_id = generate_unique_request_id()  # UUID único com timestamp
    db = SupabaseIntegration()
    cache = get_redis_cache()

    try:
        # Debug logging for REST endpoint
        print(
            f"🔍 REST DEBUG - Received request: message='{request.message}', image_url='{request.image_url}'"
        )

        # Initialize cache connection
        await cache.connect()

        # Vision Agent rate limiting for image analysis requests
        if request.image_url:
            rate_limiter = get_vision_rate_limiter()
            # Check rate limits before processing
            await rate_limiter.check_upload_rate_limit(current_user.id)
            # Estimated cost for Vision Agent image analysis
            estimated_cost = 0.05  # $0.05 estimated per analysis
            await rate_limiter.check_cost_limits(current_user.id, estimated_cost)

        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session = await db.create_session(
                user_id=current_user.id,
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
            session_id = session.id

        # Save user message with image metadata if provided
        user_metadata = {"user_id": current_user.id}
        if request.image_url:
            user_metadata["image_url"] = request.image_url
            user_metadata["has_image"] = True

        await db.save_message(
            session_id=session_id,
            request_id=request_id,
            content=request.message,
            role="user",
            metadata=user_metadata,
        )

        # Check cache for agent response (include image_url in hash for vision requests)
        cache_input = request.message
        if request.image_url:
            cache_input = f"{request.message}|IMAGE:{request.image_url}"
        input_hash = hashlib.sha256(cache_input.encode()).hexdigest()
        cached_response = await cache.get_cached_agent_response("voxy", input_hash)

        if cached_response:
            # Use cached response
            response_text = cached_response["response"]
            agent_type = cached_response.get("agent_type")
            vision_metadata = cached_response.get("vision_metadata")
            cached = True
            # Create metadata dict for cached response
            metadata = {
                "tools_used": cached_response.get("tools_used", []),
                "agent_type": agent_type,
                "vision_metadata": vision_metadata,
            }
        else:
            # Check feature flag for LangGraph vs SDK orchestrator
            use_langgraph = (
                os.getenv("VOXY_LANGGRAPH_ENABLED", "false").lower() == "true"
            )

            try:
                if use_langgraph:
                    # PHASE 2-6: LangGraph orchestrator
                    logger.bind(event="CHAT_API|ENGINE").info(
                        "Using LangGraph orchestrator",
                        session_id=session_id,
                        user_id=current_user.id,
                    )

                    langgraph_orchestrator = get_langgraph_orchestrator(
                        checkpointer_type=CheckpointerType.SQLITE,
                        db_path="voxy_graph.db",
                    )

                    result = await langgraph_orchestrator.process_message(
                        message=request.message,
                        session_id=session_id,
                        user_id=current_user.id,
                        image_url=request.image_url,
                    )

                    # Adapt LangGraph response to SDK format
                    response_text = result["content"]
                    agent_type = result.get("route_taken", "langgraph")
                    vision_metadata = result.get("vision_analysis")
                    cached = False

                    # Phase 4A: Extract usage metrics from result
                    usage = result.get("usage")
                    tools_used = []

                    # Create metadata dict compatible with SDK format
                    metadata = {
                        "agent_type": agent_type,
                        "vision_metadata": vision_metadata,
                        "tools_used": tools_used,  # Will be populated from usage extraction
                        "engine": "langgraph",
                        "thread_id": result.get("thread_id"),
                        "trace_id": result.get("trace_id"),  # Phase 4A
                    }

                    # Phase 4A: Add usage metrics to metadata if available
                    if usage:
                        metadata["usage"] = {
                            "requests": usage.requests,
                            "input_tokens": usage.input_tokens,
                            "output_tokens": usage.output_tokens,
                            "total_tokens": usage.total_tokens,
                            "estimated_cost_usd": usage.estimated_cost_usd,
                        }

                        logger.bind(
                            event="CHAT_API|USAGE_TRACKED",
                            trace_id=result.get("trace_id"),
                        ).info(
                            f"LangGraph usage: {usage.total_tokens} tokens, "
                            f"${usage.estimated_cost_usd:.6f}"
                            if usage.estimated_cost_usd
                            else f"LangGraph usage: {usage.total_tokens} tokens"
                        )

                else:
                    # DEFAULT: OpenAI Agents SDK orchestrator (production)
                    logger.bind(event="CHAT_API|ENGINE").info(
                        "Using SDK orchestrator",
                        session_id=session_id,
                        user_id=current_user.id,
                    )

                    voxy_system = get_voxy_system()
                    response_text, metadata = await voxy_system.chat(
                        message=request.message,
                        user_id=current_user.id,
                        session_id=session_id,
                        image_url=request.image_url,
                    )
                    agent_type = metadata.get("agent_type", "voxy")
                    vision_metadata = metadata.get("vision_metadata")
                    cached = False

            except Exception as voxy_error:
                logger.bind(event="CHAT_API|ERROR").error(
                    "VOXY system error",
                    error_type=type(voxy_error).__name__,
                    error_msg=str(voxy_error),
                    user_id=current_user.id,
                    session_id=session_id,
                    has_vision=bool(request.image_url),
                    engine="langgraph" if use_langgraph else "sdk",
                    exc_info=True,
                )
                response_text = f"Desculpe, ocorreu um erro interno: {str(voxy_error)}"
                agent_type = "error"
                vision_metadata = None
                cached = False
                metadata = {
                    "agent_type": "error",
                    "tools_used": [],
                    "error": str(voxy_error),
                }

            # Cache the response with tools_used
            cache_data = {
                "response": response_text,
                "agent_type": agent_type,
                "tools_used": metadata.get("tools_used", []),
                "timestamp": datetime.now().isoformat(),
            }
            if vision_metadata:
                cache_data["vision_metadata"] = vision_metadata

            await cache.cache_agent_response(
                agent_type="voxy",
                input_hash=input_hash,
                response=cache_data,
            )

        # Save assistant response
        await db.save_message(
            session_id=session_id,
            request_id=request_id,
            content=response_text,
            role="assistant",
            agent_type=agent_type,
            metadata={
                "cached": cached,
                "processing_time": (datetime.now() - start_time).total_seconds(),
            },
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Ensure response_text is always a string
        if isinstance(response_text, list):
            response_text = " ".join(str(x) for x in response_text)
        elif not isinstance(response_text, str):
            response_text = str(response_text)

        # Update Vision Agent usage if image was analyzed successfully
        if request.image_url and vision_metadata and not cached:
            rate_limiter = get_vision_rate_limiter()
            actual_cost = vision_metadata.get(
                "total_cost", 0.05
            )  # Use actual cost or fallback
            await rate_limiter.increment_usage(current_user.id, actual_cost)

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            request_id=request_id,
            timestamp=datetime.now(),
            processing_time=processing_time,
            agent_type=agent_type,
            tools_used=metadata.get("tools_used", []),  # Extract from metadata
            cached=cached,
            vision_metadata=vision_metadata,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )
    finally:
        await cache.disconnect()


# /no-auth endpoint removed for security reasons - all endpoints now require authentication


# NOTE: WebSocket functionality has been consolidated into fastapi_server.py
# The /api/chat/ws endpoint has been moved to /ws/{user_id} in the main server
# This consolidates all WebSocket handling in one place for better maintainability


# WebSocket endpoint has been consolidated to /ws/{user_id} in fastapi_server.py
# This eliminates duplication and provides a single point of WebSocket management


@router.get("/vision-usage")
async def get_vision_usage_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get Vision Agent usage statistics for the current user.

    Returns rate limits, cost tracking, and remaining quotas.
    """
    try:
        rate_limiter = get_vision_rate_limiter()
        stats = await rate_limiter.get_user_usage_stats(current_user.id)
        return {
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat(),
            **stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}",
        )
