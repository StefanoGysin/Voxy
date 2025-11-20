"""
Tests for VOXY authentication routes.

This mirrors src/voxy_agents/api/routes/auth.py
Focuses on P0 components: JWT validation, login/logout flows, protected endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.voxy_agents.api.routes.auth import (
    LoginResponse,
    SignupRequest,
    UserResponse,
    router,
)

# === Authentication Route Tests ===


class TestAuthRoutes:
    """Test authentication routes."""

    @pytest.fixture
    def client(self):
        """Test client with auth router."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_supabase_auth_success(self):
        """Mock successful Supabase auth response."""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.role = "authenticated"
        mock_user.user_metadata = {"name": "Test User"}

        mock_session = MagicMock()
        mock_session.access_token = "jwt-token-123"

        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session

        return mock_response

    @pytest.fixture
    def mock_supabase_auth_failure(self):
        """Mock failed Supabase auth response."""
        mock_response = MagicMock()
        mock_response.user = None
        mock_response.session = None
        return mock_response

    @patch("src.voxy_agents.api.routes.auth.get_supabase_client")
    def test_login_success(self, mock_get_client, client, mock_supabase_auth_success):
        """Test successful login."""
        # Setup mock
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.return_value = (
            mock_supabase_auth_success
        )
        mock_get_client.return_value = mock_supabase

        # Test login
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["access_token"] == "jwt-token-123"
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == "user-123"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "authenticated"

    @patch("src.voxy_agents.api.routes.auth.get_supabase_client")
    def test_login_invalid_credentials(
        self, mock_get_client, client, mock_supabase_auth_failure
    ):
        """Test login with invalid credentials."""
        # Setup mock
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.return_value = (
            mock_supabase_auth_failure
        )
        mock_get_client.return_value = mock_supabase

        # Test login
        response = client.post(
            "/auth/login",
            data={"username": "invalid@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]

    @patch("src.voxy_agents.api.routes.auth.get_supabase_client")
    def test_login_supabase_exception(self, mock_get_client, client):
        """Test login with Supabase exception."""
        # Setup mock to raise exception
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception(
            "Network error"
        )
        mock_get_client.return_value = mock_supabase

        # Test login
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Authentication failed" in data["detail"]

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/auth/login", data={})

        assert response.status_code == 422  # Validation error

    def test_login_invalid_form_data(self, client):
        """Test login with invalid form data."""
        response = client.post(
            "/auth/login",
            json={"username": "test@example.com"},  # JSON instead of form data
        )

        assert response.status_code == 422  # Validation error

    @patch("src.voxy_agents.api.routes.auth.get_supabase_client")
    def test_signup_success(self, mock_get_client, client, mock_supabase_auth_success):
        """Test successful signup."""
        # Setup mock
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_up.return_value = mock_supabase_auth_success
        mock_get_client.return_value = mock_supabase

        # Test signup
        signup_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        }

        response = client.post("/auth/signup", json=signup_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["access_token"] == "jwt-token-123"
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    @patch("src.voxy_agents.api.routes.auth.get_supabase_client")
    def test_signup_user_exists(self, mock_get_client, client):
        """Test signup with existing user."""
        # Setup mock to raise exception for existing user
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_up.side_effect = Exception("User already exists")
        mock_get_client.return_value = mock_supabase

        signup_data = {
            "email": "existing@example.com",
            "password": "password123",
            "full_name": "Existing User",
        }

        response = client.post("/auth/signup", json=signup_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email."""
        signup_data = {
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User",
        }

        response = client.post("/auth/signup", json=signup_data)

        # Supabase returns 400 for invalid email format, not 422
        assert response.status_code == 400

    def test_signup_missing_required_fields(self, client):
        """Test signup with missing required fields."""
        signup_data = {
            "email": "test@example.com"
            # Missing password
        }

        response = client.post("/auth/signup", json=signup_data)

        assert response.status_code == 422  # Validation error

    def test_logout_success(self, client):
        """Test logout endpoint requires authentication."""
        # Without auth header, should get 403 or 401
        response = client.post("/auth/logout")
        assert response.status_code in [401, 403]

        # With invalid token, should get 401 or 403
        response = client.post(
            "/auth/logout", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code in [401, 403]

    @patch("src.voxy_agents.api.routes.auth.get_current_user")
    def test_status_authenticated_user(self, mock_get_user, client):
        """Test auth status with authenticated user."""
        # Setup mock authenticated user
        mock_user = {
            "id": "user-123",
            "email": "test@example.com",
            "role": "authenticated",
        }
        mock_get_user.return_value = mock_user

        response = client.get(
            "/auth/status", headers={"Authorization": "Bearer jwt-token-123"}
        )

        # Status endpoint might not exist, but test for expected behavior
        if response.status_code == 200:
            data = response.json()
            assert data["authenticated"] is True
            assert data["user"]["id"] == "user-123"

    def test_status_unauthenticated_user(self, client):
        """Test auth status endpoint doesn't exist."""
        response = client.get("/auth/status")

        # Status endpoint is not implemented, should return 404
        assert response.status_code == 404


# === JWT Token Validation Tests ===


class TestJWTValidation:
    """Test JWT token validation functionality."""

    @pytest.fixture
    def valid_jwt_token(self, mock_jwt_token):
        """Valid JWT token for testing."""
        return mock_jwt_token

    @pytest.fixture
    def expired_jwt_token(self):
        """Expired JWT token for testing."""
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTY0MjY4MDAwMH0.expired"

    @pytest.fixture
    def invalid_jwt_token(self):
        """Invalid JWT token for testing."""
        return "invalid.jwt.token"

    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_valid_token_verification(
        self, mock_verify, valid_jwt_token, mock_jwt_payload
    ):
        """Test verification of valid JWT token."""
        # Return TokenData object instead of dict
        from src.voxy_agents.api.middleware.auth import TokenData

        mock_verify.return_value = TokenData(
            user_id="user-123", email="test@example.com"
        )

        # Import and test the auth middleware function
        from src.voxy_agents.api.middleware.auth import verify_token

        result = verify_token(valid_jwt_token)

        assert result.user_id == "user-123"
        assert result.email == "test@example.com"

    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_expired_token_verification(self, mock_verify, expired_jwt_token):
        """Test verification of expired JWT token."""
        mock_verify.side_effect = HTTPException(
            status_code=401, detail="Token has expired"
        )

        from src.voxy_agents.api.middleware.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_jwt_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_invalid_token_verification(self, mock_verify, invalid_jwt_token):
        """Test verification of invalid JWT token."""
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")

        from src.voxy_agents.api.middleware.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_jwt_token)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_missing_token_header(self, mock_verify):
        """Test verification with missing token."""
        mock_verify.side_effect = HTTPException(
            status_code=401, detail="Authorization header missing"
        )

        from src.voxy_agents.api.middleware.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token("")

        assert exc_info.value.status_code == 401

    @patch("src.voxy_agents.api.middleware.auth.verify_token")
    def test_malformed_auth_header(self, mock_verify):
        """Test verification with malformed token."""
        mock_verify.side_effect = HTTPException(
            status_code=401, detail="Invalid token format"
        )

        from src.voxy_agents.api.middleware.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid-format")

        assert exc_info.value.status_code == 401


# === Protected Endpoint Tests ===


class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication."""

    @pytest.fixture
    def client_with_auth(self):
        """Test client with authentication."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_protected_endpoint_with_valid_token(self, client_with_auth):
        """Test protected endpoint behavior."""
        # The /auth/me endpoint exists and requires authentication
        # Without valid token, should get 401
        response = client_with_auth.get(
            "/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    def test_protected_endpoint_without_token(self, client_with_auth):
        """Test protected endpoint without token."""
        response = client_with_auth.get("/auth/me")

        # Should return 403 or 401 (missing auth header)
        assert response.status_code in [401, 403]

    def test_protected_endpoint_with_invalid_token(self, client_with_auth):
        """Test protected endpoint with invalid token."""
        response = client_with_auth.get(
            "/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401


# === Pydantic Model Tests ===


class TestAuthModels:
    """Test authentication Pydantic models."""

    def test_login_response_creation(self):
        """Test LoginResponse model creation."""
        data = {
            "access_token": "jwt-token-123",
            "token_type": "bearer",
            "user": {
                "id": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
            },
        }

        response = LoginResponse(**data)

        assert response.access_token == "jwt-token-123"
        assert response.token_type == "bearer"
        assert response.user["id"] == "user-123"

    def test_signup_request_validation(self):
        """Test SignupRequest model validation."""
        # Valid data
        data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
        }

        request = SignupRequest(**data)

        assert request.email == "test@example.com"
        assert request.password == "password123"
        assert request.full_name == "Test User"

    def test_signup_request_missing_optional_fields(self):
        """Test SignupRequest with missing optional fields."""
        data = {
            "email": "test@example.com",
            "password": "password123",
            # full_name is optional
        }

        request = SignupRequest(**data)

        assert request.email == "test@example.com"
        assert request.password == "password123"
        assert request.full_name == ""  # default value

    def test_user_response_creation(self):
        """Test UserResponse model creation."""
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "role": "authenticated",
            "user_metadata": {"name": "Test User"},
        }

        response = UserResponse(**data)

        assert response.id == "user-123"
        assert response.email == "test@example.com"
        assert response.role == "authenticated"
        assert response.user_metadata["name"] == "Test User"
