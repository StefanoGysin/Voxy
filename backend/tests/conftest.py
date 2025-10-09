"""
Pytest configuration and global fixtures for VOXY Agents tests.
"""

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest


# Set up test event loop
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


# === OpenAI Mocking Infrastructure ===


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = AsyncMock()

    # Mock completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"test": "response"}'
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 30
    mock_response.usage.total_tokens = 80

    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_openai_agents_sdk():
    """Mock OpenAI Agents SDK components."""
    mock_agent = MagicMock()
    mock_runner = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test agent response")]

    mock_runner.run = AsyncMock(return_value=mock_response)

    with (
        patch("agents.Agent", return_value=mock_agent),
        patch("agents.Runner", return_value=mock_runner),
        patch("agents.function_tool") as mock_function_tool,
    ):
        mock_function_tool.return_value = MagicMock()

        yield {
            "agent": mock_agent,
            "runner": mock_runner,
            "response": mock_response,
            "function_tool": mock_function_tool,
        }


# === Supabase Mocking Infrastructure ===


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()

    # Mock table operations
    mock_table = MagicMock()

    # Mock select operations
    mock_table.select.return_value.execute.return_value = MagicMock(data=[])
    mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "test", "content": "test"}]
    )

    # Mock insert operations
    mock_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "new-id", "created_at": "2024-01-01T00:00:00Z"}]
    )

    # Mock update operations
    mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "test", "updated_at": "2024-01-01T00:00:00Z"}]
    )

    # Mock delete operations
    mock_table.delete.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    # Table methods
    mock_client.table.return_value = mock_table
    mock_client.from_.return_value = mock_table

    return mock_client


@pytest.fixture
def mock_supabase_session():
    """Mock SupabaseSession for testing."""
    mock_session = MagicMock()

    # Session operations
    mock_session.create_session = AsyncMock(return_value="session-123")
    mock_session.get_session = AsyncMock(
        return_value={
            "id": "session-123",
            "user_id": "user-123",
            "created_at": "2024-01-01T00:00:00Z",
        }
    )
    mock_session.save_message = AsyncMock(return_value="message-123")
    mock_session.get_history = AsyncMock(return_value=[])

    return mock_session


@pytest.fixture
def mock_supabase_clients():
    """Mock both Supabase clients (user and service)."""
    mock_user_client = MagicMock()
    mock_service_client = MagicMock()

    # Mock table operations for both clients
    for client in [mock_user_client, mock_service_client]:
        mock_table = MagicMock()

        # Mock select operations
        mock_table.select.return_value.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "test", "content": "test"}]
        )

        # Mock insert operations
        mock_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-id", "created_at": "2024-01-01T00:00:00Z"}]
        )

        # Mock update operations
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "test", "updated_at": "2024-01-01T00:00:00Z"}]
        )

        # Mock delete operations
        mock_table.delete.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        # Table methods
        client.table.return_value = mock_table
        client.from_.return_value = mock_table

    return {"user_client": mock_user_client, "service_client": mock_service_client}


# === Redis Mocking Infrastructure ===


@pytest.fixture
def mock_redis_client():
    """Mock Redis client using fakeredis."""
    # Use fakeredis for actual Redis-like behavior in tests
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    return redis_client


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache wrapper."""
    mock_cache = MagicMock()

    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.delete = AsyncMock(return_value=True)
    mock_cache.exists = AsyncMock(return_value=False)
    mock_cache.ttl = AsyncMock(return_value=-1)

    return mock_cache


# === Global State Cleanup Infrastructure ===


@pytest.fixture(autouse=True)
def cleanup_global_state():
    """
    Cleanup global state between tests to ensure proper isolation.
    This fixture runs automatically before every test.
    """
    # Store original modules before test
    yield

    # After test: Reset any global singletons
    # Reset VOXY system singleton
    import src.voxy_agents.main

    if hasattr(src.voxy_agents.main, "_voxy_system"):
        src.voxy_agents.main._voxy_system = None

    # Reset subagent singletons
    import src.voxy_agents.core.subagents.calculator_agent

    src.voxy_agents.core.subagents.calculator_agent._instance = None

    import src.voxy_agents.core.subagents.corrector_agent

    src.voxy_agents.core.subagents.corrector_agent._instance = None

    import src.voxy_agents.core.subagents.translator_agent

    src.voxy_agents.core.subagents.translator_agent._instance = None

    import src.voxy_agents.core.subagents.weather_agent

    src.voxy_agents.core.subagents.weather_agent._instance = None

    # Reset orchestrator singleton
    import src.voxy_agents.core.voxy_orchestrator

    if hasattr(src.voxy_agents.core.voxy_orchestrator, "_instance"):
        src.voxy_agents.core.voxy_orchestrator._instance = None


# === HTTP Client Mocking Infrastructure ===


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for external API calls."""
    mock_client = MagicMock()

    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_response.raise_for_status.return_value = None

    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)

    return mock_client


# === FastAPI Testing Infrastructure ===


@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI app for testing."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return TestClient(app)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing."""
    mock_websocket = MagicMock()

    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_text = AsyncMock(return_value='{"message": "test"}')
    mock_websocket.send_text = AsyncMock()
    mock_websocket.close = AsyncMock()

    return mock_websocket


# === Authentication Mocking Infrastructure ===


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing."""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6OTk5OTk5OTk5OX0.test"


@pytest.fixture
def mock_jwt_payload():
    """Mock JWT payload for testing."""
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "exp": 9999999999,
        "iat": 1642680000,
        "role": "authenticated",
    }


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user for testing."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "role": "authenticated",
        "metadata": {},
    }


# === Sample Data Fixtures ===


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return "test-session-123"


@pytest.fixture
def sample_user_input():
    """Sample user input for testing."""
    return "Hello, can you help me with something?"


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "id": "msg-123",
        "session_id": "session-123",
        "user_id": "user-123",
        "role": "user",
        "content": "Hello, how are you?",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "id": "session-123",
        "user_id": "user-123",
        "title": "Test Conversation",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "message_count": 5,
    }


@pytest.fixture
def mock_weather_api_response():
    """Mock weather API response."""
    return {
        "location": {
            "name": "London",
            "country": "GB",
            "coordinates": [51.5074, -0.1278],
        },
        "current": {
            "temperature": 15.5,
            "feels_like": 14.2,
            "humidity": 72,
            "pressure": 1013,
            "description": "partly cloudy",
            "main": "Clouds",
            "wind_speed": 3.6,
            "wind_direction": 230,
            "visibility": 10.0,
            "cloudiness": 40,
        },
        "units": "metric",
        "timestamp": 1642680000,
    }


# === Environment Setup for Tests ===


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    test_env = {
        "OPENAI_API_KEY": "test-key",
        "SUPABASE_URL": "http://localhost:8000",
        "SUPABASE_ANON_KEY": "test-anon-key",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "REDIS_URL": "redis://localhost:6379/1",
        "JWT_SECRET": "test-jwt-secret",
        "OPENWEATHER_API_KEY": "test-weather-key",
    }

    # Set test environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# === Test Markers ===


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "external: tests that call external APIs")
    config.addinivalue_line("markers", "slow: slow running tests")
    config.addinivalue_line("markers", "websocket: WebSocket tests")
    config.addinivalue_line("markers", "auth: authentication tests")
    config.addinivalue_line("markers", "database: database tests")
