"""
Tests for VOXY Supabase integration.

This mirrors src/voxy_agents/core/database/supabase_integration.py
Focuses on P0 components: CRUD operations, session persistence, error scenarios.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.voxy_agents.core.database.models import ChatSession, Message
from src.voxy_agents.core.database.supabase_integration import SupabaseIntegration

# === SupabaseIntegration Tests ===


class TestSupabaseIntegration:
    """Test Supabase integration class."""

    # Using global mock_supabase_clients fixture from conftest.py

    @pytest.fixture
    def supabase_integration(self, mock_supabase_clients):
        """Create SupabaseIntegration instance with mocked clients."""
        regular_client = mock_supabase_clients["user_client"]
        service_client = mock_supabase_clients["service_client"]

        with (
            patch(
                "src.voxy_agents.core.database.supabase_integration.get_supabase_client",
                return_value=regular_client,
            ),
            patch(
                "src.voxy_agents.core.database.supabase_integration.get_supabase_service_client",
                return_value=service_client,
            ),
        ):
            integration = SupabaseIntegration()
            integration.client = regular_client
            integration.service_client = service_client
            return integration

    # === Session Management Tests ===

    @pytest.mark.asyncio
    async def test_create_session_success(self, supabase_integration):
        """Test successful session creation."""
        user_id = "user-123"
        title = "Test Session"

        # Mock successful insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(
                data=[{"id": "session-123", "user_id": user_id, "title": title}]
            )
        )

        session = await supabase_integration.create_session(user_id, title)

        # Verify session creation
        assert isinstance(session, ChatSession)
        assert session.user_id == user_id
        assert session.title == title
        assert session.id is not None

        # Verify Supabase was called correctly
        supabase_integration.service_client.table.assert_called_with("chat_sessions")

    @pytest.mark.asyncio
    async def test_create_session_auto_title(self, supabase_integration):
        """Test session creation with auto-generated title."""
        user_id = "user-123"

        # Mock successful insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[{"id": "session-123", "user_id": user_id}])
        )

        session = await supabase_integration.create_session(user_id)

        # Verify auto-generated title
        assert session.title.startswith("Chat ")
        assert len(session.title) > 5  # Should have timestamp

    @pytest.mark.asyncio
    async def test_create_session_database_error(self, supabase_integration):
        """Test session creation with database error."""
        user_id = "user-123"

        # Mock failed insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=None)
        )

        with pytest.raises(Exception) as exc_info:
            await supabase_integration.create_session(user_id)

        assert "Failed to create session" in str(exc_info.value)

    # === Message Management Tests ===

    @pytest.mark.asyncio
    async def test_save_message_success(self, supabase_integration):
        """Test successful message saving."""
        session_id = "session-123"
        request_id = "request-123"
        content = "Hello VOXY"
        role = "user"

        # Mock successful message insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[{"id": "msg-123", "content": content}])
        )

        # Mock update_session_timestamp
        with patch.object(
            supabase_integration, "update_session_timestamp"
        ) as mock_update:
            mock_update.return_value = None

            message = await supabase_integration.save_message(
                session_id, request_id, content, role
            )

        # Verify message creation
        assert isinstance(message, Message)
        assert message.session_id == session_id
        assert message.request_id == request_id
        assert message.content == content
        assert message.role == role

        # Verify database operations
        supabase_integration.service_client.table.assert_called_with("messages")
        mock_update.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_save_message_with_metadata(self, supabase_integration):
        """Test saving message with metadata and agent type."""
        session_id = "session-123"
        request_id = "request-123"
        content = "Translated text"
        role = "assistant"
        agent_type = "translator"
        metadata = {"source_language": "en", "target_language": "es"}

        # Mock successful insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[{"id": "msg-123"}])
        )

        with patch.object(supabase_integration, "update_session_timestamp"):
            message = await supabase_integration.save_message(
                session_id, request_id, content, role, agent_type, metadata
            )

        assert message.agent_type == agent_type
        assert message.metadata == metadata

    @pytest.mark.asyncio
    async def test_save_message_content_processing(self, supabase_integration):
        """Test message content processing for different data types."""
        session_id = "session-123"
        request_id = "request-123"
        role = "assistant"

        # Mock successful insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[{"id": "msg-123"}])
        )

        with patch.object(supabase_integration, "update_session_timestamp"):
            # Test dict content with 'text' key
            dict_content = {"text": "Hello world", "other": "data"}
            message = await supabase_integration.save_message(
                session_id, request_id, dict_content, role
            )
            assert message.content == "Hello world"

            # Test dict content with 'output_text' key
            dict_content2 = {"output_text": "Processed text", "metadata": {}}
            message2 = await supabase_integration.save_message(
                session_id, request_id, dict_content2, role
            )
            assert message2.content == "Processed text"

            # Test list content
            list_content = ["Hello", "world", "from", "VOXY"]
            message3 = await supabase_integration.save_message(
                session_id, request_id, list_content, role
            )
            assert message3.content == "Hello world from VOXY"

            # Test other data types
            int_content = 12345
            message4 = await supabase_integration.save_message(
                session_id, request_id, int_content, role
            )
            assert message4.content == "12345"

    @pytest.mark.asyncio
    async def test_save_message_database_error(self, supabase_integration):
        """Test message saving with database error."""
        session_id = "session-123"
        request_id = "request-123"
        content = "Hello VOXY"
        role = "user"

        # Mock failed insert
        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=None)
        )

        with pytest.raises(Exception) as exc_info:
            await supabase_integration.save_message(
                session_id, request_id, content, role
            )

        assert "Failed to save message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_session_timestamp(self, supabase_integration):
        """Test updating session timestamp."""
        session_id = "session-123"

        # Mock successful update
        mock_table = supabase_integration.client.table.return_value
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        await supabase_integration.update_session_timestamp(session_id)

        # Verify update was called
        mock_table.update.assert_called_once()
        mock_table.update.return_value.eq.assert_called_once_with("id", session_id)

    # === Session Retrieval Tests ===

    @pytest.mark.asyncio
    async def test_get_user_sessions_success(self, supabase_integration):
        """Test retrieving user sessions."""
        user_id = "user-123"

        # Mock session data with messages field
        session_data = [
            {
                "id": "session-1",
                "user_id": user_id,
                "title": "First Chat",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:30:00Z",
                "messages": [
                    {"content": "Hello", "created_at": "2024-01-01T10:00:00Z"}
                ],
            },
            {
                "id": "session-2",
                "user_id": user_id,
                "title": "Second Chat",
                "created_at": "2024-01-01T11:00:00Z",
                "updated_at": "2024-01-01T11:15:00Z",
                "messages": [
                    {"content": "Hi there", "created_at": "2024-01-01T11:00:00Z"}
                ],
            },
        ]

        # Mock successful query (using .range() not .limit().offset())
        supabase_integration.client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(
            data=session_data
        )

        sessions = await supabase_integration.get_user_sessions(user_id)

        # Verify results - should return SessionSummary objects
        assert len(sessions) == 2
        assert sessions[0].id == "session-1"
        assert sessions[0].title == "First Chat"
        assert sessions[0].last_message == "Hello"
        assert sessions[0].message_count == 1
        assert sessions[1].id == "session-2"
        assert sessions[1].title == "Second Chat"
        assert sessions[1].last_message == "Hi there"
        assert sessions[1].message_count == 1

    @pytest.mark.asyncio
    async def test_get_user_sessions_empty(self, supabase_integration):
        """Test retrieving user sessions when none exist."""
        user_id = "user-123"

        # Mock empty result
        supabase_integration.client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(
            data=[]
        )

        sessions = await supabase_integration.get_user_sessions(user_id)

        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_get_user_sessions_with_pagination(self, supabase_integration):
        """Test retrieving user sessions with pagination."""
        user_id = "user-123"
        limit = 10
        offset = 20

        # Mock query chain - using .range() instead of .limit().offset()
        mock_table = supabase_integration.client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_order = mock_eq.order.return_value
        mock_range = mock_order.range.return_value
        mock_range.execute.return_value = MagicMock(data=[])

        await supabase_integration.get_user_sessions(user_id, limit, offset)

        # Verify pagination parameters - range(offset, offset + limit - 1)
        expected_end = offset + limit - 1
        mock_order.range.assert_called_with(offset, expected_end)

    # === Message History Tests ===

    @pytest.mark.asyncio
    async def test_get_session_detail_success(self, supabase_integration):
        """Test retrieving session detail with messages."""
        session_id = "session-123"
        user_id = "user-123"

        # Mock session detail data
        session_detail_data = {
            "id": session_id,
            "user_id": user_id,
            "title": "Test Chat",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:30:00Z",
            "messages": [
                {
                    "id": "msg-1",
                    "session_id": session_id,
                    "content": "Hello",
                    "role": "user",
                    "created_at": "2024-01-01T10:00:00Z",
                },
                {
                    "id": "msg-2",
                    "session_id": session_id,
                    "content": "Hi there!",
                    "role": "assistant",
                    "agent_type": "voxy",
                    "created_at": "2024-01-01T10:01:00Z",
                },
            ],
        }

        # Mock successful query - using .single() not .execute()
        mock_table = supabase_integration.client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq1 = mock_select.eq.return_value
        mock_eq2 = mock_eq1.eq.return_value
        mock_eq2.single.return_value.execute.return_value = MagicMock(
            data=session_detail_data
        )

        detail = await supabase_integration.get_session_detail(session_id, user_id)

        # Verify results - should return SessionDetail object
        assert detail.id == session_id
        assert detail.title == "Test Chat"
        assert len(detail.messages) == 2
        assert detail.messages[0].role == "user"
        assert detail.messages[1].role == "assistant"
        assert detail.messages[1].agent_type == "voxy"

    @pytest.mark.asyncio
    async def test_get_session_detail_not_found(self, supabase_integration):
        """Test retrieving non-existent session detail."""
        session_id = "nonexistent-session"
        user_id = "user-123"

        # Mock no result found - simulate Supabase returning None
        mock_table = supabase_integration.client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq1 = mock_select.eq.return_value
        mock_eq2 = mock_eq1.eq.return_value
        mock_eq2.single.return_value.execute.return_value = MagicMock(data=None)

        detail = await supabase_integration.get_session_detail(session_id, user_id)

        assert detail is None

    # === Session Deletion Tests ===

    @pytest.mark.asyncio
    async def test_delete_session_success(self, supabase_integration):
        """Test successful session deletion."""
        session_id = "session-123"
        user_id = "user-123"

        # Mock successful deletion (messages first, then session)
        supabase_integration.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": session_id}]
        )

        result = await supabase_integration.delete_session(session_id, user_id)

        assert result is True

        # Verify table was called (for both messages and session deletion)
        assert supabase_integration.client.table.call_count >= 2

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, supabase_integration):
        """Test deleting non-existent session."""
        session_id = "nonexistent-session"
        user_id = "user-123"

        # Mock empty deletion result (need to mock both messages and session deletion)
        mock_result = MagicMock(data=[])
        supabase_integration.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
            mock_result
        )
        supabase_integration.client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = await supabase_integration.delete_session(session_id, user_id)

        assert result is False

    # === Error Handling Tests ===

    @pytest.mark.asyncio
    async def test_database_connection_error(self, supabase_integration):
        """Test handling database connection errors."""
        # Configure client to raise connection error
        supabase_integration.service_client.table.side_effect = Exception(
            "Connection failed"
        )

        with pytest.raises(Exception) as exc_info:
            await supabase_integration.create_session("user-123")

        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_session_id(self, supabase_integration):
        """Test operations with invalid session ID."""
        invalid_session_id = ""

        # Mock successful message saving with empty session_id
        message_data = {
            "id": "msg-123",
            "session_id": invalid_session_id,
            "content": "content",
            "role": "user",
            "created_at": "2024-01-01T10:00:00Z",
        }

        supabase_integration.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[message_data])
        )

        # Should work with empty session_id (implementation doesn't validate)
        message = await supabase_integration.save_message(
            invalid_session_id, "req-123", "content", "user"
        )

        assert message.session_id == invalid_session_id
        assert message.content == "content"

    @pytest.mark.asyncio
    async def test_invalid_user_id(self, supabase_integration):
        """Test operations with invalid user ID."""
        invalid_user_id = None

        with pytest.raises((ValueError, TypeError)):
            await supabase_integration.create_session(invalid_user_id)


# === SupabaseSession Wrapper Tests ===


class TestSupabaseSession:
    """Test SupabaseSession wrapper functionality."""

    @pytest.fixture
    def supabase_session(self, mock_supabase_session):
        """SupabaseSession instance for testing."""
        return mock_supabase_session

    @pytest.mark.asyncio
    async def test_session_wrapper_create_session(self, supabase_session):
        """Test session wrapper create_session method."""
        user_id = "user-123"

        session_id = await supabase_session.create_session(user_id)

        assert session_id == "session-123"
        supabase_session.create_session.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_session_wrapper_save_message(self, supabase_session):
        """Test session wrapper save_message method."""
        session_id = "session-123"
        content = "Test message"

        message_id = await supabase_session.save_message(session_id, content)

        assert message_id == "message-123"
        supabase_session.save_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_wrapper_get_history(self, supabase_session):
        """Test session wrapper get_history method."""
        session_id = "session-123"

        history = await supabase_session.get_history(session_id)

        assert isinstance(history, list)
        supabase_session.get_history.assert_called_once_with(session_id)


# === Integration Test Scenarios ===


@pytest.mark.integration
class TestSupabaseIntegrationScenarios:
    """Test complete integration scenarios."""

    @pytest.fixture
    def integration_client(self, mock_supabase_clients):
        """Integration test setup with realistic mock data."""
        regular_client = mock_supabase_clients["user_client"]
        service_client = mock_supabase_clients["service_client"]

        with (
            patch(
                "src.voxy_agents.core.database.supabase_integration.get_supabase_client",
                return_value=regular_client,
            ),
            patch(
                "src.voxy_agents.core.database.supabase_integration.get_supabase_service_client",
                return_value=service_client,
            ),
        ):
            integration = SupabaseIntegration()
            # Explicitly set the clients to ensure they are properly mocked
            integration.client = regular_client
            integration.service_client = service_client
            return integration

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, integration_client):
        """Test complete conversation flow: create session, save messages, retrieve history."""
        user_id = "integration-user"

        # Mock successful operations
        session_data = {
            "id": "session-123",
            "user_id": user_id,
            "title": "Integration Test",
        }
        message_data = {"id": "msg-123", "content": "Hello"}

        # Override the default AsyncMock to use regular MagicMock for execute()
        integration_client.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[session_data])
        )

        # 1. Create session
        session = await integration_client.create_session(user_id, "Integration Test")
        assert session.user_id == user_id

        # 2. Save user message
        integration_client.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(data=[message_data])
        )

        with patch.object(integration_client, "update_session_timestamp"):
            user_msg = await integration_client.save_message(
                session.id, "req-1", "Hello VOXY", "user"
            )
            assert user_msg.role == "user"

            # 3. Save assistant response
            assistant_msg = await integration_client.save_message(
                session.id, "req-1", "Hello! How can I help you?", "assistant", "voxy"
            )
            assert assistant_msg.role == "assistant"
            assert assistant_msg.agent_type == "voxy"

    @pytest.mark.asyncio
    async def test_session_lifecycle_management(self, integration_client):
        """Test complete session lifecycle: create, use, delete."""
        user_id = "lifecycle-user"

        # Mock creation
        integration_client.service_client.table.return_value.insert.return_value.execute = MagicMock(
            return_value=MagicMock(
                data=[{"id": "session-lifecycle", "user_id": user_id}]
            )
        )

        # Create session
        session = await integration_client.create_session(user_id)

        # Mock deletion - delete_session uses regular client, not service_client
        # First, mock messages deletion (first call)
        integration_client.client.table.return_value.delete.return_value.eq.return_value.execute = MagicMock(
            return_value=MagicMock(data=[])
        )

        # Then mock session deletion (second call)
        integration_client.client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute = MagicMock(
            return_value=MagicMock(data=[{"id": session.id}])
        )

        # Delete session - needs user_id parameter
        deleted = await integration_client.delete_session(session.id, user_id)
        assert deleted is True
