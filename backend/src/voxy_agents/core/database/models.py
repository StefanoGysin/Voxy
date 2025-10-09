"""
Database models for VOXY Agents persistence.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    """Chat session model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """Message model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    request_id: str
    content: str
    role: str  # 'user', 'assistant', 'system'
    agent_type: Optional[str] = None  # 'voxy', 'translator', 'weather', etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionSummary(BaseModel):
    """Session summary for listing."""

    id: str
    title: Optional[str]
    last_message: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime


class MessageWithAgent(BaseModel):
    """Message with agent information."""

    id: str
    content: str
    role: str
    agent_type: Optional[str]
    created_at: datetime
    metadata: dict[str, Any]


class SessionDetail(BaseModel):
    """Detailed session information."""

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
    messages: list[MessageWithAgent] = Field(default_factory=list)
