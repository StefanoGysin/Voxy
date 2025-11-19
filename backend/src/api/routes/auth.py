"""
Authentication routes for VOXY Agents.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel

from ...config.settings import settings
from integrations.redis import token_manager
from platform.auth import User, get_current_user
from ..middleware.supabase_client import get_supabase_client

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class SignupRequest(BaseModel):
    """Signup request model."""

    email: str
    password: str
    full_name: str = ""


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: str
    role: str
    user_metadata: dict[str, Any] = {}


def create_custom_jwt_token(user_data: dict[str, Any]) -> tuple[str, str]:
    """
    Create a custom JWT token with extended expiration time and unique JTI.

    Args:
        user_data: User data to include in the token

    Returns:
        Tuple of (JWT token string, JTI) for token tracking and blacklisting
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(seconds=settings.jwt_access_token_expire_seconds)

    # Generate unique JWT ID for token tracking and blacklisting
    jti = str(uuid.uuid4())

    # Create payload following JWT standards with JTI for tracking
    payload = {
        "sub": user_data["id"],  # Subject (user ID)
        "email": user_data["email"],
        "role": user_data.get("role", "authenticated"),
        "aud": "authenticated",  # Audience
        "iss": "voxy-agents",  # Issuer
        "iat": int(now.timestamp()),  # Issued at
        "exp": int(expiration.timestamp()),  # Expiration
        "jti": jti,  # JWT ID for unique token identification and blacklisting
        "user_metadata": user_data.get("user_metadata", {}),
    }

    # Sign the token using the same secret as verification
    token = jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")
    return token, jti


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with email and password.

    Returns JWT token for authenticated requests.
    """
    supabase = get_supabase_client()

    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password(
            {
                "email": form_data.username,  # OAuth2PasswordRequestForm uses 'username' field
                "password": form_data.password,
            }
        )

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create custom JWT token with 24-hour expiration
        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "role": getattr(response.user, "role", "authenticated"),
            "user_metadata": getattr(response.user, "user_metadata", {}),
        }

        custom_token, jti = create_custom_jwt_token(user_data)
        print(f"🔐 Created token with JTI: {jti} for user: {response.user.email}")

        # Store token info in Redis for tracking and blacklisting
        expiration = datetime.now(timezone.utc) + timedelta(
            seconds=settings.jwt_access_token_expire_seconds
        )
        await token_manager.store_token_info(
            jti=jti,
            user_id=response.user.id,
            email=response.user.email,
            expiration=expiration,
        )

        return LoginResponse(
            access_token=custom_token,  # Use our custom 24-hour token
            user=user_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/signup", response_model=LoginResponse)
async def signup(signup_data: SignupRequest):
    """
    Sign up a new user.

    Creates a new account and returns JWT token.
    """
    supabase = get_supabase_client()

    try:
        # Sign up with Supabase
        response = supabase.auth.sign_up(
            {
                "email": signup_data.email,
                "password": signup_data.password,
                "options": {"data": {"full_name": signup_data.full_name}},
            }
        )

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account",
            )

        # If email confirmation is required, session might be None
        if response.session:
            # Create custom JWT token with 24-hour expiration
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "role": getattr(response.user, "role", "authenticated"),
                "user_metadata": getattr(response.user, "user_metadata", {}),
            }

            custom_token, jti = create_custom_jwt_token(user_data)
            print(f"🔐 Signup token with JTI: {jti} for user: {response.user.email}")

            # Store token info in Redis for tracking
            expiration = datetime.now(timezone.utc) + timedelta(
                seconds=settings.jwt_access_token_expire_seconds
            )
            await token_manager.store_token_info(
                jti=jti,
                user_id=response.user.id,
                email=response.user.email,
                expiration=expiration,
            )

            return LoginResponse(
                access_token=custom_token,  # Use our custom 24-hour token
                user=user_data,
            )
        else:
            # Email confirmation required
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail="Account created. Please check your email for confirmation.",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Signup failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: User = Depends(get_current_user),
):
    """
    Logout current user and blacklist the JWT token.

    Invalidates both Supabase session and JWT token via blacklisting.
    """
    supabase = get_supabase_client()

    try:
        # Extract JTI from token for blacklisting
        token = credentials.credentials

        # Decode token to get JTI without full verification (already verified in get_current_user)
        try:
            import jwt as jwt_decode

            payload = jwt_decode.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                # Convert exp to datetime
                token_expiration = datetime.fromtimestamp(exp, tz=timezone.utc)

                # Blacklist the current token
                blacklisted = await token_manager.blacklist_token(
                    jti=jti, user_id=current_user.id, expiration=token_expiration
                )

                if blacklisted:
                    print(
                        f"🚫 Token {jti} blacklisted on logout for user: {current_user.email}"
                    )
                else:
                    print(
                        f"⚠️ Failed to blacklist token {jti} for user: {current_user.email}"
                    )

        except Exception as token_error:
            print(f"⚠️ Could not extract JTI for blacklisting: {token_error}")

        # Also logout from Supabase
        try:
            supabase.auth.sign_out()
        except Exception as supabase_error:
            print(f"⚠️ Supabase logout error (non-critical): {supabase_error}")

        return {"message": "Successfully logged out", "token_invalidated": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.

    Returns details about the authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        user_metadata=current_user.user_metadata or {},
    )


@router.get("/validate")
async def validate_token(current_user: User = Depends(get_current_user)):
    """
    Validate JWT token.

    Returns success if token is valid.
    """
    return {"valid": True, "user_id": current_user.id, "email": current_user.email}
