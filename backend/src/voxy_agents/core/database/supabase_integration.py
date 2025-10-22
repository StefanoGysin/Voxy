"""
Supabase integration for VOXY Agents persistence.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ...api.middleware.supabase_client import (
    get_supabase_client,
    get_supabase_service_client,
)
from .models import (
    ChatSession,
    Message,
    MessageWithAgent,
    SessionDetail,
    SessionSummary,
)

logger = logging.getLogger(__name__)


def _format_item_hierarchical(
    item: dict, index: int, total: int, indent="   │  "
) -> str:
    """
    Format an item (message/reasoning/function_call) in hierarchical visual format.

    Args:
        item: Dictionary containing item data
        index: Current item index (0-based)
        total: Total number of items
        indent: Base indentation string

    Returns:
        Formatted hierarchical string
    """
    item_type = item.get("type", "unknown")
    role = item.get("role", "")
    is_last = index == total - 1
    branch = "└─" if is_last else "├─"
    vertical = "   " if is_last else "│  "

    # Emoji mapping based on type/role
    emoji_map = {
        "user": "📥",
        "assistant": "📤",
        "reasoning": "🧠",
        "function_call": "🔧",
        "function_call_output": "📊",
        "message": "💬",
    }

    emoji = emoji_map.get(role or item_type, "📄")

    lines = []
    lines.append(f"{indent}{branch} {emoji} Item {index + 1}/{total}")

    # Add type-specific details
    if role:
        lines.append(f"{indent}{vertical}├─ Role: {role}")

    if item_type and item_type != "message":
        lines.append(f"{indent}{vertical}├─ Type: {item_type}")

    # Handle content/summary/output based on item structure
    content = None
    if "content" in item:
        content = item["content"]
        content_label = "Content"
    elif "summary" in item:
        # Reasoning item with summary
        summary = item["summary"]
        if isinstance(summary, list) and summary:
            if isinstance(summary[0], dict) and "text" in summary[0]:
                content = summary[0]["text"]
            else:
                content = str(summary)
        content_label = "Reasoning"
    elif "output" in item:
        content = item["output"]
        content_label = "Output"
    elif "arguments" in item:
        content = item["arguments"]
        content_label = "Arguments"

    # Format content with truncation
    if content:
        if isinstance(content, str):
            if len(content) > 100:
                truncated = f"{content[:100]}... [{len(content) - 100} chars omitted]"
            else:
                truncated = content
        elif isinstance(content, list):
            # Handle list of content parts
            text_parts = []
            for part in content:
                if isinstance(part, dict):
                    if "text" in part:
                        text_parts.append(part["text"])
                    elif "output_text" in part:
                        text_parts.append(part["output_text"])
            combined = " ".join(text_parts)
            if len(combined) > 100:
                truncated = f"{combined[:100]}... [{len(combined) - 100} chars omitted]"
            else:
                truncated = combined
        else:
            truncated = str(content)[:100]

        lines.append(f'{indent}{vertical}├─ {content_label}: "{truncated}"')

    # Add function-specific details
    if "name" in item:
        lines.append(f"{indent}{vertical}├─ Function: {item['name']}")
    if "call_id" in item:
        lines.append(f"{indent}{vertical}├─ Call ID: {item['call_id'][:16]}...")
    if "status" in item:
        lines.append(f"{indent}{vertical}└─ Status: {item['status']}")
    else:
        # Change last ├─ to └─
        if lines[-1].endswith('chars omitted]"') or ":" in lines[-1]:
            lines[-1] = lines[-1].replace("├─", "└─")

    return "\n".join(lines)


class SupabaseIntegration:
    """Handle all Supabase database operations for VOXY Agents."""

    def __init__(self):
        self.client = get_supabase_client()
        self.service_client = get_supabase_service_client()

    async def create_session(
        self, user_id: str, title: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session.

        Args:
            user_id: ID of the authenticated user
            title: Optional title for the session

        Returns:
            ChatSession: Created session
        """
        session = ChatSession(
            user_id=user_id,
            title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )

        # Insert into Supabase using service client to bypass RLS
        result = (
            self.service_client.table("chat_sessions")
            .insert(
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata,
                }
            )
            .execute()
        )

        if result.data:
            return session
        else:
            raise Exception(f"Failed to create session: {result}")

    async def save_message(
        self,
        session_id: str,
        request_id: str,
        content: str,
        role: str,
        agent_type: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Message:
        """
        Save a message to the database.

        Args:
            session_id: ID of the chat session
            request_id: ID of the request (for grouping user/assistant pairs)
            content: Message content
            role: Message role ('user', 'assistant', 'system')
            agent_type: Type of agent that generated the message
            metadata: Additional metadata

        Returns:
            Message: Saved message
        """
        # Ensure content is always a string - handle structured content
        if isinstance(content, dict):
            # Extract text from structured content
            if "text" in content:
                content = content["text"]
            elif "output_text" in content:
                content = content["output_text"]
            else:
                content = str(content)
                logger.warning(f"⚠️ Unexpected dict content in save_message: {content}")
        elif isinstance(content, list):
            content = " ".join(str(x) for x in content)
        elif not isinstance(content, str):
            content = str(content)
            logger.warning(
                f"⚠️ Converting non-string content in save_message: {type(content)}"
            )

        message = Message(
            session_id=session_id,
            request_id=request_id,
            content=content,
            role=role,
            agent_type=agent_type,
            metadata=metadata or {},
        )

        # Insert into Supabase using service client to bypass RLS
        result = (
            self.service_client.table("messages")
            .insert(
                {
                    "id": message.id,
                    "session_id": message.session_id,
                    "request_id": message.request_id,
                    "content": message.content,
                    "role": message.role,
                    "agent_type": message.agent_type,
                    "created_at": message.created_at.isoformat(),
                    "metadata": message.metadata,
                }
            )
            .execute()
        )

        if result.data:
            # Update session's updated_at timestamp
            await self.update_session_timestamp(session_id)
            return message
        else:
            raise Exception(f"Failed to save message: {result}")

    async def update_session_timestamp(self, session_id: str) -> None:
        """Update session's updated_at timestamp."""
        result = (
            self.client.table("chat_sessions")
            .update({"updated_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", session_id)
            .execute()
        )
        return result

    async def get_user_sessions(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[SessionSummary]:
        """
        Get chat sessions for a user with summary information.

        Args:
            user_id: ID of the user
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List[SessionSummary]: List of session summaries
        """
        # Get sessions with message count and last message
        result = (
            self.client.table("chat_sessions")
            .select("*, messages(content, created_at)")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        sessions = []
        for session_data in result.data:
            messages = session_data.get("messages", [])
            last_message = messages[-1]["content"] if messages else None

            sessions.append(
                SessionSummary(
                    id=session_data["id"],
                    title=session_data.get("title"),
                    last_message=last_message,
                    message_count=len(messages),
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    updated_at=datetime.fromisoformat(session_data["updated_at"]),
                )
            )

        return sessions

    async def get_session_detail(
        self, session_id: str, user_id: str
    ) -> Optional[SessionDetail]:
        """
        Get detailed session information with all messages.

        Args:
            session_id: ID of the session
            user_id: ID of the user (for authorization)

        Returns:
            Optional[SessionDetail]: Session detail or None if not found
        """
        # Get session with all messages
        result = (
            self.client.table("chat_sessions")
            .select("*, messages(*)")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not result.data:
            return None

        session_data = result.data
        messages = []

        for msg_data in session_data.get("messages", []):
            messages.append(
                MessageWithAgent(
                    id=msg_data["id"],
                    content=msg_data["content"],
                    role=msg_data["role"],
                    agent_type=msg_data.get("agent_type"),
                    created_at=datetime.fromisoformat(msg_data["created_at"]),
                    metadata=msg_data.get("metadata", {}),
                )
            )

        # Sort messages by creation time
        messages.sort(key=lambda m: m.created_at)

        return SessionDetail(
            id=session_data["id"],
            title=session_data.get("title"),
            created_at=datetime.fromisoformat(session_data["created_at"]),
            updated_at=datetime.fromisoformat(session_data["updated_at"]),
            metadata=session_data.get("metadata", {}),
            messages=messages,
        )

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete a chat session and all its messages.

        Args:
            session_id: ID of the session to delete
            user_id: ID of the user (for authorization)

        Returns:
            bool: True if deleted successfully
        """
        # First, delete all messages in the session
        self.client.table("messages").delete().eq("session_id", session_id).execute()

        # Then delete the session
        result = (
            self.client.table("chat_sessions")
            .delete()
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return bool(result.data)

    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """
        Delete a specific message.

        Args:
            message_id: ID of the message to delete
            user_id: ID of the user (for authorization via session ownership)

        Returns:
            bool: True if deleted successfully

        Raises:
            ValueError: If message not found or user doesn't own it
        """
        # First verify the message exists and user owns it through session
        message_result = (
            self.client.table("messages")
            .select("session_id")
            .eq("id", message_id)
            .execute()
        )

        if not message_result.data:
            raise ValueError("Message not found")

        session_id = message_result.data[0]["session_id"]

        # Verify user owns the session
        session_result = (
            self.client.table("chat_sessions")
            .select("id")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not session_result.data:
            raise ValueError("Message not found or access denied")

        # Delete the message
        result = self.client.table("messages").delete().eq("id", message_id).execute()

        return bool(result.data)

    async def update_session_title(
        self, session_id: str, user_id: str, title: str
    ) -> bool:
        """
        Update a session's title.

        Args:
            session_id: ID of the session
            user_id: ID of the user (for authorization)
            title: New title

        Returns:
            bool: True if updated successfully
        """
        result = (
            self.client.table("chat_sessions")
            .update(
                {"title": title, "updated_at": datetime.now(timezone.utc).isoformat()}
            )
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return bool(result.data)

    async def get_session_context(
        self, session_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get recent messages from a session for context building.

        Args:
            session_id: ID of the session
            limit: Maximum number of recent messages to return

        Returns:
            List[Dict[str, Any]]: List of recent messages formatted for context
        """
        # Get recent messages ordered by creation time
        result = (
            self.client.table("messages")
            .select("content, role, agent_type, created_at")
            .eq("session_id", session_id)
            .order(
                "created_at", desc=False  # Ascending order to get chronological context
            )
            .limit(limit)
            .execute()
        )

        if not result.data:
            return []

        # Format messages for context
        context_messages = []
        for msg in result.data:
            # Skip system messages for context building
            if msg["role"] in ["user", "assistant"]:
                context_messages.append(
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["created_at"],
                    }
                )

        # Return only the most recent messages if we have more than limit
        if len(context_messages) > limit:
            context_messages = context_messages[-limit:]

        return context_messages


class SupabaseSession:
    """
    OpenAI Agents SDK compatible Session implementation using Supabase.

    Implements the Session protocol required by the OpenAI Agents SDK's Runner.run()
    for automatic conversation history management.
    """

    def __init__(
        self,
        session_id: str,
        user_id: str,
        supabase_integration: Optional[SupabaseIntegration] = None,
    ):
        """
        Initialize SupabaseSession.

        Args:
            session_id: Unique identifier for the chat session
            user_id: User ID for the session
            supabase_integration: Optional SupabaseIntegration instance
        """
        self.session_id = session_id
        self.user_id = user_id
        self.supabase_integration = supabase_integration or SupabaseIntegration()
        self._session_exists = False

    async def _ensure_session_exists(self) -> None:
        """Ensure the session exists in the database."""
        if not self._session_exists:
            try:
                # Debug log to check session_id format
                logger.debug(
                    f"🔍 Checking session exists: session_id={self.session_id}, type={type(self.session_id)}"
                )

                # Check if session exists
                check_result = (
                    self.supabase_integration.client.table("chat_sessions")
                    .select("id")
                    .eq("id", self.session_id)
                    .execute()
                )

                if check_result.data:
                    # Session exists, mark as verified
                    self._session_exists = True
                    logger.debug(f"Session {self.session_id} already exists")
                else:
                    # Session doesn't exist, create it
                    session = ChatSession(
                        id=self.session_id,
                        user_id=self.user_id,
                        title=f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    )

                    # Insert into Supabase with specific session ID
                    self.supabase_integration.client.table("chat_sessions").insert(
                        {
                            "id": session.id,
                            "user_id": session.user_id,
                            "title": session.title,
                            "created_at": session.created_at.isoformat(),
                            "updated_at": session.updated_at.isoformat(),
                            "metadata": session.metadata,
                        }
                    ).execute()

                    logger.info(
                        f"\n💾 [DATABASE] Supabase Session Created\n"
                        f"   ├─ Session ID: {self.session_id}\n"
                        f"   ├─ User ID: {self.user_id[:8]}...\n"
                        f"   ├─ Title: {session.title}\n"
                        f"   └─ ✓ Persisted to chat_sessions"
                    )

                self._session_exists = True
            except Exception as e:
                logger.error(f"Error ensuring session exists: {e}")
                logger.error(
                    f"🚨 Debug info - session_id: {repr(self.session_id)}, user_id: {repr(self.user_id)}"
                )
                # Don't raise - allow session to work in memory mode

    async def get_items(self, limit: Optional[int] = None) -> list[dict]:
        """
        Retrieve conversation history for this session.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries in OpenAI format
        """
        await self._ensure_session_exists()

        try:
            # Get session context (recent messages)
            context_limit = limit or 50
            context_messages = await self.supabase_integration.get_session_context(
                self.session_id, context_limit
            )

            # Convert to OpenAI Agents SDK format
            items = []
            for msg in context_messages:
                items.append({"role": msg["role"], "content": msg["content"]})

            return items

        except Exception as e:
            logger.error(f"Error retrieving session items: {e}")
            return []

    async def add_items(self, items: list[dict]) -> None:
        """
        Store new items for this session.

        Args:
            items: List of message dictionaries to store
        """
        # Format items hierarchically
        total_items = len(items)
        formatted_items = []
        for idx, item in enumerate(items):
            formatted_items.append(_format_item_hierarchical(item, idx, total_items))

        logger.info(
            f"\n💾 [DATABASE] Adding Items to Session\n"
            f"   ├─ Session ID: {self.session_id}\n"
            f"   ├─ Total Items: {total_items}\n"
            f"   │\n" + "\n".join(formatted_items)
        )

        await self._ensure_session_exists()

        try:
            # Save each message with its own unique request_id
            for item in items:
                # Generate a unique request_id for each individual message using UUID4
                import uuid

                unique_request_id = str(uuid.uuid4())

                # Ensure content is always a string - handle OpenAI SDK format
                raw_content = item.get("content", "")

                # Debug log - show both raw and processed content
                raw_content_preview = str(raw_content)[:100] if raw_content else ""
                logger.debug(
                    f"💾 Raw content type: {type(raw_content)}, preview: {raw_content_preview}"
                )

                if isinstance(raw_content, dict):
                    # Handle OpenAI SDK format - extract text from structured content
                    if "text" in raw_content:
                        content = raw_content["text"]
                    elif "output_text" in raw_content:
                        content = raw_content["output_text"]
                    else:
                        # Fallback: convert to string but log warning
                        content = str(raw_content)
                        logger.warning(
                            f"⚠️ Unexpected dict content format: {raw_content}"
                        )
                elif isinstance(raw_content, list):
                    # Handle list of content objects (common in OpenAI SDK responses)
                    processed_parts = []
                    for part in raw_content:
                        if isinstance(part, dict):
                            if "text" in part:
                                processed_parts.append(part["text"])
                            elif "output_text" in part:
                                processed_parts.append(part["output_text"])
                            else:
                                processed_parts.append(str(part))
                                logger.warning(f"⚠️ Unexpected list item format: {part}")
                        else:
                            processed_parts.append(str(part))
                    content = " ".join(processed_parts)
                elif isinstance(raw_content, str):
                    content = raw_content
                else:
                    content = str(raw_content)
                    logger.warning(
                        f"⚠️ Converting non-string content: {type(raw_content)} -> {content[:100]}"
                    )

                # Debug log after processing
                logger.debug(
                    f"💾 Processed content: {content[:100] if content else 'EMPTY'}"
                )

                # Skip saving empty content to avoid database clutter
                if not content or content.strip() == "":
                    logger.debug(
                        f"⚠️ Skipping empty content for session {self.session_id}"
                    )
                    continue

                await self.supabase_integration.save_message(
                    session_id=self.session_id,
                    request_id=unique_request_id,
                    content=content,
                    role=item.get("role", "user"),
                    agent_type=item.get("agent_type"),
                    metadata=item.get("metadata", {}),
                )

        except Exception as e:
            logger.error(f"Error saving session items: {e}")
            # Don't raise - allow conversation to continue

    async def pop_item(self) -> Optional[dict]:
        """
        Remove and return the most recent item from this session.

        Returns:
            Most recent message dictionary or None if session is empty
        """
        await self._ensure_session_exists()

        try:
            # Get all items
            items = await self.get_items()

            if not items:
                return None

            # Get the most recent item
            last_item = items[-1]

            # Note: Supabase implementation doesn't support atomic pop
            # This is a limitation - we return the item but don't remove it
            # For full implementation, would need to add delete_last_message method
            logger.warning(
                "pop_item() called but Supabase implementation doesn't support atomic removal"
            )

            return last_item

        except Exception as e:
            logger.error(f"Error popping session item: {e}")
            return None

    async def clear_session(self) -> None:
        """Clear all items from this session."""
        try:
            await self.supabase_integration.delete_session(
                self.session_id, self.user_id
            )
            self._session_exists = False

        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            # Don't raise - allow operation to continue
