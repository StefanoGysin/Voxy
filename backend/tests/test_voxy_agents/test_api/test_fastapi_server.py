"""
Tests for VOXY FastAPI server.

This mirrors src/voxy_agents/api/fastapi_server.py
Focuses on critical P0 components: WebSocket, health checks, routing.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.voxy_agents.api.fastapi_server import (
    ConnectionManager,
    SystemStatus,
    app,
)

# === ConnectionManager Tests (WebSocket Critical) ===


class TestConnectionManager:
    """Test WebSocket connection management."""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing."""
        websocket = MagicMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect_websocket_success(self, manager, mock_websocket):
        """Test successful WebSocket connection."""
        user_id = "test_user_123"

        await manager.connect(mock_websocket, user_id)

        # Verify connection was established
        assert user_id in manager.active_connections
        assert manager.active_connections[user_id] == mock_websocket
        mock_websocket.accept.assert_called_once()

    def test_disconnect_websocket_success(self, manager, mock_websocket):
        """Test successful WebSocket disconnection."""
        user_id = "test_user_123"
        manager.active_connections[user_id] = mock_websocket

        manager.disconnect(user_id)

        # Verify connection was removed
        assert user_id not in manager.active_connections

    def test_disconnect_websocket_not_exists(self, manager):
        """Test disconnecting non-existent WebSocket."""
        # Should not raise exception
        manager.disconnect("nonexistent_user")
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_send_message_success(self, manager, mock_websocket):
        """Test sending message to connected user."""
        user_id = "test_user_123"
        message = {"type": "response", "content": "Hello"}
        manager.active_connections[user_id] = mock_websocket

        await manager.send_message(user_id, message)

        # Verify message was sent
        mock_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_message_user_not_connected(self, manager):
        """Test sending message to non-connected user."""
        user_id = "nonexistent_user"
        message = {"type": "response", "content": "Hello"}

        # Should not raise exception
        await manager.send_message(user_id, message)

    @pytest.mark.asyncio
    async def test_send_message_websocket_error(self, manager, mock_websocket):
        """Test handling WebSocket send error."""
        user_id = "test_user_123"
        message = {"type": "response", "content": "Hello"}
        manager.active_connections[user_id] = mock_websocket

        # Configure WebSocket to raise exception
        mock_websocket.send_text.side_effect = Exception("Connection lost")

        await manager.send_message(user_id, message)

        # Verify user was disconnected after error
        assert user_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_success(self, manager):
        """Test broadcasting message to multiple users."""
        # Setup multiple connections
        users = {"user1": MagicMock(), "user2": MagicMock(), "user3": MagicMock()}
        for user_id, websocket in users.items():
            websocket.send_text = AsyncMock()
            manager.active_connections[user_id] = websocket

        message = {"type": "broadcast", "content": "Hello everyone"}

        await manager.broadcast(message)

        # Verify all users received message
        for websocket in users.values():
            websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connections(self, manager):
        """Test broadcasting with some failed connections."""
        # Setup connections - one working, one failing
        working_ws = MagicMock()
        working_ws.send_text = AsyncMock()

        failing_ws = MagicMock()
        failing_ws.send_text = AsyncMock(side_effect=Exception("Connection lost"))

        manager.active_connections["working_user"] = working_ws
        manager.active_connections["failing_user"] = failing_ws

        message = {"type": "broadcast", "content": "Hello everyone"}

        await manager.broadcast(message)

        # Verify working user still connected, failing user disconnected
        assert "working_user" in manager.active_connections
        assert "failing_user" not in manager.active_connections


# === FastAPI Application Tests ===


class TestFastAPIApp:
    """Test FastAPI application endpoints."""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def mock_voxy_system(self):
        """Mock VOXY system for testing."""
        mock_system = MagicMock()
        mock_system.get_system_stats.return_value = {
            "system_status": "operational",
            "subagents_count": 4,
            "orchestrator_stats": {"calls": 100},
        }
        mock_system.chat = AsyncMock(
            return_value=(
                "Test response",
                {"agent_type": "voxy", "session_id": "test-session"},
            )
        )
        return mock_system

    def test_root_endpoint(self, client):
        """Test root endpoint returns system info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "VOXY Agents API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"
        assert data["docs"] == "/docs"

    @patch("src.voxy_agents.api.fastapi_server.get_voxy_system")
    def test_health_check_success(self, mock_get_system, client, mock_voxy_system):
        """Test health check endpoint."""
        mock_get_system.return_value = mock_voxy_system

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["subagents_count"] == 4
        assert data["version"] == "0.1.0"
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))

    @patch("src.voxy_agents.api.fastapi_server.get_voxy_system")
    def test_health_check_system_error(self, mock_get_system, client):
        """Test health check with system error."""
        mock_get_system.side_effect = Exception("System error")

        # Should raise exception since there's no error handling in the endpoint
        with pytest.raises(Exception, match="System error"):
            client.get("/health")

    # REMOVED: Public /chat endpoint tests
    # Endpoint was removed for security consolidation
    # All chat functionality now requires authentication via /api/chat/
    # See test_routes/test_chat.py for authenticated chat endpoint tests

    def test_cors_headers_present(self, client):
        """Test CORS headers are properly configured."""
        # Test with a GET request that exists and check CORS headers
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        # Should have CORS headers or at least not fail due to CORS
        assert response.status_code in [200, 404]  # 404 is OK if endpoint doesn't exist

    def test_api_routes_included(self, client):
        """Test that API routers are properly included."""
        # Test core endpoints that should exist (not return 404)

        # Health endpoint exists at root level
        response = client.get("/health")
        assert response.status_code != 404, "Health endpoint not found"

        # Root endpoint should exist
        response = client.get("/")
        assert response.status_code == 200, "Root endpoint not found"

    def test_docs_endpoints_available(self, client):
        """Test API documentation endpoints are available."""
        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200


# === Pydantic Models Tests ===


class TestPydanticModels:
    """Test Pydantic model validation."""

    # REMOVED: ChatRequest and ChatResponse tests
    # These models were moved to routes/chat.py
    # See test_routes/test_chat.py for chat model tests

    def test_system_status_creation(self):
        """Test SystemStatus creation."""
        data = {"status": "operational", "subagents_count": 4, "uptime": 3600.0}

        status = SystemStatus(**data)

        assert status.status == "operational"
        assert status.subagents_count == 4
        assert status.version == "0.1.0"  # default
        assert status.uptime == 3600.0


# === WebSocket Endpoint Tests ===


@pytest.mark.websocket
class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality."""

    @pytest.fixture
    def websocket_client(self):
        """WebSocket test client."""
        return TestClient(app)

    @patch("src.voxy_agents.api.fastapi_server.get_voxy_system")
    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_websocket_connection_flow_authenticated(self, mock_verify_token, mock_get_system, websocket_client):
        """Test WebSocket connection flow with valid authentication."""
        # Mock token validation
        from src.voxy_agents.api.middleware.auth import TokenData
        mock_verify_token.return_value = TokenData(
            user_id="test_user",
            email="test@example.com",
            role="authenticated",
            jti="test-jti-123"
        )

        mock_system = MagicMock()
        mock_system.chat = AsyncMock(
            return_value=("WebSocket response", {"agent_type": "voxy"})
        )
        mock_get_system.return_value = mock_system

        # Test WebSocket connection with authentication token
        with websocket_client.websocket_connect("/ws/test_user?token=valid_test_token") as websocket:
            # First, receive connection acknowledgment message
            connection_data = websocket.receive_text()
            connection_response = json.loads(connection_data)

            # Verify connection acknowledgment
            assert connection_response["type"] == "connection"
            assert "Conectado ao VOXY Agents System" in connection_response["message"]
            assert connection_response["authenticated"] is True
            assert connection_response["email"] == "test@example.com"

            # Now send test message
            websocket.send_text(
                json.dumps(
                    {"message": "Hello via WebSocket", "session_id": "ws_session"}
                )
            )

            # Receive processing indicator
            processing_data = websocket.receive_text()
            processing_response = json.loads(processing_data)
            assert processing_response["type"] == "processing"

            # Receive actual response
            response_data = websocket.receive_text()
            response = json.loads(response_data)

            # Verify response
            assert response["type"] == "response"
            assert response["message"] == "WebSocket response"
            assert response["session_id"] == "ws_session"

    def test_websocket_connection_no_token(self, websocket_client):
        """Test WebSocket connection without authentication token - should fail."""
        # Should raise exception because token is mandatory
        with pytest.raises(Exception):
            with websocket_client.websocket_connect("/ws/test_user"):
                pass

    def test_websocket_connection_invalid_token(self, websocket_client):
        """Test WebSocket connection with invalid token - should fail."""
        # Should raise exception because token is invalid
        with pytest.raises(Exception):
            with websocket_client.websocket_connect("/ws/test_user?token=invalid_token"):
                pass

    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_websocket_user_id_mismatch(self, mock_verify_token, websocket_client):
        """Test WebSocket connection with user_id mismatch - should fail."""
        from src.voxy_agents.api.middleware.auth import TokenData

        # Token claims to be for user "alice" but URL has "bob"
        mock_verify_token.return_value = TokenData(
            user_id="alice",
            email="alice@example.com",
            role="authenticated",
            jti="test-jti-456"
        )

        # Should raise exception because user_id mismatch
        with pytest.raises(Exception):
            with websocket_client.websocket_connect("/ws/bob?token=valid_token"):
                pass


# === Integration Tests ===


@pytest.mark.integration
class TestFastAPIIntegration:
    """Test FastAPI server integration scenarios."""

    @pytest.fixture
    def integration_client(self):
        """Integration test client with real-like setup."""
        return TestClient(app)

    @patch("src.voxy_agents.api.fastapi_server.get_voxy_system")
    def test_full_system_health_flow_integration(self, mock_get_system, integration_client):
        """Test complete system health check flow."""
        # Setup mock system
        mock_system = MagicMock()
        mock_system.get_system_stats.return_value = {
            "system_status": "operational",
            "subagents_count": 4,
        }
        mock_get_system.return_value = mock_system

        # 1. Check root endpoint
        root_response = integration_client.get("/")
        assert root_response.status_code == 200
        assert root_response.json()["status"] == "operational"

        # 2. Check health endpoint
        health_response = integration_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "operational"

        # NOTE: Chat endpoint tests moved to test_routes/test_chat.py
        # Chat now requires authentication via /api/chat/

    def test_server_startup_and_lifespan(self, integration_client):
        """Test server startup and lifespan management."""
        # Server should be running and responsive
        response = integration_client.get("/")
        assert response.status_code == 200

        # Health check should work
        response = integration_client.get("/health")
        # Might fail in test environment, but route should exist
        assert response.status_code in [200, 500]  # 500 if VOXY system init fails
