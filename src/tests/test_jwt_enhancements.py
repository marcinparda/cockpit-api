"""Tests for JWT enhancements including blacklist and refresh tokens."""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4

from src.auth.jwt import (
    create_access_token, create_refresh_token, verify_token,
    invalidate_token, extract_token_id,
    create_refresh_token_response, refresh_access_token
)
from src.auth.jwt_blacklist import (
    JWTBlacklist, JWTBlacklistEntry, jwt_blacklist,
    blacklist_token, is_token_blacklisted, remove_token_from_blacklist,
    get_blacklist_stats
)
from src.schemas.auth import RefreshTokenRequest, LogoutRequest
from src.services.auth_service import (
    create_user_refresh_token, login_user,
    refresh_user_tokens, logout_user
)


class TestJWTBlacklist:
    """Test JWT blacklist functionality."""

    def test_jwt_blacklist_entry_initialization(self):
        """Test JWTBlacklistEntry initialization."""
        expires_at = time.time() + 3600
        entry = JWTBlacklistEntry("token123", expires_at)

        assert entry.token_id == "token123"
        assert entry.expires_at == expires_at
        assert entry.is_expired() is False

    def test_jwt_blacklist_entry_expiration(self):
        """Test JWT blacklist entry expiration."""
        expires_at = time.time() - 1  # Already expired
        entry = JWTBlacklistEntry("token123", expires_at)

        assert entry.is_expired() is True

    def test_jwt_blacklist_add_token(self):
        """Test adding token to blacklist."""
        blacklist = JWTBlacklist()

        blacklist.add_token("token123")
        assert "token123" in blacklist.blacklisted_tokens
        assert "token123" in blacklist.token_expiry

    def test_jwt_blacklist_is_blacklisted(self):
        """Test checking if token is blacklisted."""
        blacklist = JWTBlacklist()

        # Token not in blacklist
        assert blacklist.is_blacklisted("token123") is False

        # Add token to blacklist
        blacklist.add_token("token123")
        assert blacklist.is_blacklisted("token123") is True

        # Add expired token
        expires_at = time.time() - 1
        blacklist.add_token("expired_token", expires_at)
        assert blacklist.is_blacklisted("expired_token") is False

    def test_jwt_blacklist_remove_token(self):
        """Test removing token from blacklist."""
        blacklist = JWTBlacklist()

        blacklist.add_token("token123")
        assert blacklist.is_blacklisted("token123") is True

        blacklist.remove_token("token123")
        assert blacklist.is_blacklisted("token123") is False

    def test_jwt_blacklist_cleanup(self):
        """Test automatic cleanup of expired tokens."""
        blacklist = JWTBlacklist()

        # Add current token
        blacklist.add_token("current_token")

        # Add expired token
        expires_at = time.time() - 1
        blacklist.add_token("expired_token", expires_at)

        # Force cleanup
        blacklist._cleanup_expired()

        assert blacklist.is_blacklisted("current_token") is True
        assert blacklist.is_blacklisted("expired_token") is False

    def test_jwt_blacklist_stats(self):
        """Test blacklist statistics."""
        blacklist = JWTBlacklist()

        stats = blacklist.get_stats()
        assert stats["total_blacklisted"] == 0
        assert "last_cleanup" in stats

        blacklist.add_token("token123")
        stats = blacklist.get_stats()
        assert stats["total_blacklisted"] == 1


class TestJWTBlacklistGlobalFunctions:
    """Test global blacklist functions."""

    def test_global_blacklist_functions(self):
        """Test global blacklist functions."""
        # Clear any existing tokens
        jwt_blacklist.blacklisted_tokens.clear()
        jwt_blacklist.token_expiry.clear()

        # Test adding token
        blacklist_token("global_token")
        assert is_token_blacklisted("global_token") is True

        # Test removing token
        remove_token_from_blacklist("global_token")
        assert is_token_blacklisted("global_token") is False

        # Test stats
        stats = get_blacklist_stats()
        assert isinstance(stats, dict)
        assert "total_blacklisted" in stats


class TestJWTEnhancements:
    """Test JWT token enhancements."""

    def test_create_access_token_with_jti(self):
        """Test access token creation with JWT ID."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)

        # Decode and verify JTI is present
        payload = verify_token(token)
        assert "jti" in payload
        assert payload["jti"] is not None
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_refresh_token(data)

        # Decode and verify
        payload = verify_token(token)
        assert "jti" in payload
        assert payload["token_type"] == "refresh"
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]

    def test_verify_token_with_blacklist_check(self):
        """Test token verification with blacklist check."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)

        # Token should verify successfully
        payload = verify_token(token)
        assert payload["sub"] == data["sub"]

        # Add token to blacklist
        jti = payload["jti"]
        blacklist_token(jti)

        # Token should now fail verification
        with pytest.raises(Exception):  # JWTError
            verify_token(token)

    def test_invalidate_token(self):
        """Test token invalidation."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)

        # Token should verify successfully
        payload = verify_token(token)
        assert payload["sub"] == data["sub"]

        # Invalidate token
        success = invalidate_token(token)
        assert success is True

        # Token should now fail verification
        with pytest.raises(Exception):  # JWTError
            verify_token(token)

    def test_extract_token_id(self):
        """Test JWT ID extraction."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)

        # Extract JTI
        jti = extract_token_id(token)
        assert jti is not None

        # Verify it matches the payload
        payload = verify_token(token)
        assert payload["jti"] == jti

    def test_create_refresh_token_response(self):
        """Test refresh token response creation."""
        user_id = uuid4()
        email = "test@example.com"

        response = create_refresh_token_response(user_id, email)

        assert response.token_type == "bearer"
        assert response.expires_in > 0
        assert response.refresh_expires_in > 0
        assert len(response.access_token) > 0
        assert len(response.refresh_token) > 0

        # Verify tokens are valid
        access_payload = verify_token(response.access_token)
        refresh_payload = verify_token(response.refresh_token)

        assert access_payload["sub"] == str(user_id)
        assert refresh_payload["sub"] == str(user_id)
        assert refresh_payload["token_type"] == "refresh"

    def test_refresh_access_token(self):
        """Test access token refresh."""
        user_id = uuid4()
        email = "test@example.com"

        # Create initial refresh token
        refresh_token = create_refresh_token({
            "sub": str(user_id),
            "email": email
        })

        # Refresh the token
        new_access_token, new_refresh_token = refresh_access_token(
            refresh_token)

        # Verify new tokens are valid
        access_payload = verify_token(new_access_token)
        refresh_payload = verify_token(new_refresh_token)

        assert access_payload["sub"] == str(user_id)
        assert refresh_payload["sub"] == str(user_id)
        assert refresh_payload["token_type"] == "refresh"

        # Old refresh token should be blacklisted
        with pytest.raises(Exception):  # JWTError
            verify_token(refresh_token)


class TestAuthServiceEnhancements:
    """Test authentication service enhancements."""

    @patch("src.services.auth_service.authenticate_user")
    def test_login_user(self, mock_authenticate):
        """Test login with refresh token."""
        # Mock user
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.password_changed = True
        mock_authenticate.return_value = mock_user

        # Mock database session
        db = MagicMock()

        # Test login
        async def test_async():
            response = await login_user(db, "test@example.com", "password")

            assert hasattr(response, "access_token")
            assert hasattr(response, "refresh_token")
            assert response.token_type == "bearer"

        import asyncio
        asyncio.run(test_async())

    def test_refresh_user_tokens(self):
        """Test user token refresh."""
        user_id = uuid4()
        email = "test@example.com"

        # Create initial refresh token
        refresh_token = create_refresh_token({
            "sub": str(user_id),
            "email": email
        })

        # Test refresh
        async def test_async():
            response = await refresh_user_tokens(refresh_token)

            assert hasattr(response, "access_token")
            assert hasattr(response, "refresh_token")
            assert response.token_type == "bearer"

        import asyncio
        asyncio.run(test_async())

    def test_logout_user(self):
        """Test user logout."""
        user_id = uuid4()
        email = "test@example.com"

        # Create tokens
        access_token = create_access_token({
            "sub": str(user_id),
            "email": email
        })
        refresh_token = create_refresh_token({
            "sub": str(user_id),
            "email": email
        })

        # Test logout
        async def test_async():
            success = await logout_user(access_token, refresh_token)
            assert success is True

            # Tokens should be invalidated
            with pytest.raises(Exception):  # JWTError
                verify_token(access_token)
            with pytest.raises(Exception):  # JWTError
                verify_token(refresh_token)

        import asyncio
        asyncio.run(test_async())


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_refresh_token_request_schema(self):
        """Test refresh token request schema."""
        request = RefreshTokenRequest(refresh_token="test_token")
        assert request.refresh_token == "test_token"

    def test_logout_request_schema(self):
        """Test logout request schema."""
        # Without refresh token
        request = LogoutRequest()
        assert request.refresh_token is None

        # With refresh token
        request = LogoutRequest(refresh_token="test_token")
        assert request.refresh_token == "test_token"


if __name__ == "__main__":
    pytest.main([__file__])
