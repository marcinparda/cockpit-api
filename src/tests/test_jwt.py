"""Tests for JWT authentication utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError

from src.auth.jwt import (
    create_access_token,
    verify_token,
    create_token_response
)
from src.schemas.auth import TokenData, TokenResponse


class TestJWTUtils:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = uuid4()
        data = {"sub": str(user_id), "email": "test@example.com"}

        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test creating an access token with custom expiration."""
        user_id = uuid4()
        data = {"sub": str(user_id), "email": "test@example.com"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self):
        """Test successfully verifying a valid token."""
        user_id = uuid4()
        email = "test@example.com"
        data = {"sub": str(user_id), "email": email}

        token = create_access_token(data)
        token_data = verify_token(token)

        assert isinstance(token_data, TokenData)
        assert token_data.user_id == user_id
        assert token_data.email == email

    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            verify_token(invalid_token)

    def test_verify_token_missing_subject(self):
        """Test verifying a token without subject."""
        data = {"email": "test@example.com"}  # Missing 'sub'
        token = create_access_token(data)

        with pytest.raises(JWTError, match="Token missing user identifier"):
            verify_token(token)

    def test_verify_token_invalid_uuid(self):
        """Test verifying a token with invalid UUID format."""
        data = {"sub": "not-a-uuid", "email": "test@example.com"}
        token = create_access_token(data)

        with pytest.raises(JWTError, match="Invalid user ID format"):
            verify_token(token)

    def test_create_token_response(self):
        """Test creating a complete token response."""
        user_id = uuid4()
        email = "test@example.com"

        response = create_token_response(user_id, email)

        assert isinstance(response, TokenResponse)
        assert response.token_type == "bearer"
        assert response.expires_in == 24 * 3600  # 24 hours in seconds
        assert len(response.access_token) > 0

        # Verify the token can be decoded
        token_data = verify_token(response.access_token)
        assert token_data.user_id == user_id
        assert token_data.email == email
