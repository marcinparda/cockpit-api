"""Test cookie authentication implementation."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from src.core.config import settings
from src.auth.jwt_dependencies import get_current_user


class TestCookieAuthentication:
    """Test cookie-based authentication functionality."""

    def test_cookie_configuration_loaded(self):
        """Test that cookie configuration is properly loaded."""
        assert hasattr(settings, 'COOKIE_DOMAIN')
        assert hasattr(settings, 'COOKIE_SECURE')
        assert hasattr(settings, 'COOKIE_HTTPONLY')
        assert hasattr(settings, 'COOKIE_SAMESITE')
        assert hasattr(settings, 'ACCESS_TOKEN_COOKIE_MAX_AGE')
        assert hasattr(settings, 'REFRESH_TOKEN_COOKIE_MAX_AGE')
        assert hasattr(settings, 'ENVIRONMENT')

        # Verify default values
        assert settings.COOKIE_HTTPONLY is True
        assert settings.COOKIE_SAMESITE in ["strict", "lax", "none"]
        assert settings.ACCESS_TOKEN_COOKIE_MAX_AGE == 1800  # 30 minutes
        assert settings.REFRESH_TOKEN_COOKIE_MAX_AGE == 604800  # 7 days
        assert settings.ENVIRONMENT == "development"

    @pytest.mark.asyncio
    async def test_flexible_auth_with_cookie(self):
        """Test authentication with cookie token."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        # Mock verify_token and get_user_with_role
        with patch("src.auth.jwt_dependencies.verify_token") as mock_verify:
            with patch("src.auth.jwt_dependencies.get_user_with_role") as mock_get_user:
                mock_verify.return_value = {"sub": str(
                    mock_user.id), "email": mock_user.email}
                mock_get_user.return_value = mock_user

                # Test with cookie authentication
                user = await get_current_user(
                    access_token="cookie_token_123",
                    authorization=None,
                    credentials=None,
                    db=mock_db
                )

                assert user == mock_user
                mock_verify.assert_called_once_with(
                    "cookie_token_123", mock_db)
                mock_get_user.assert_called_once_with(mock_db, mock_user.id)

    @pytest.mark.asyncio
    async def test_flexible_auth_with_bearer_token(self):
        """Test authentication with Bearer token (backward compatibility)."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        # Mock verify_token and get_user_with_role
        with patch("src.auth.jwt_dependencies.verify_token") as mock_verify:
            with patch("src.auth.jwt_dependencies.get_user_with_role") as mock_get_user:
                mock_verify.return_value = {"sub": str(
                    mock_user.id), "email": mock_user.email}
                mock_get_user.return_value = mock_user

                # Test with Bearer token authentication
                user = await get_current_user(
                    access_token=None,
                    authorization="Bearer bearer_token_123",
                    credentials=None,
                    db=mock_db
                )

                assert user == mock_user
                mock_verify.assert_called_once_with(
                    "bearer_token_123", mock_db)
                mock_get_user.assert_called_once_with(mock_db, mock_user.id)

    @pytest.mark.asyncio
    async def test_flexible_auth_no_authentication(self):
        """Test that proper error is raised when no authentication is provided."""
        from fastapi import HTTPException

        mock_db = AsyncMock()

        # Test with no authentication
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                access_token=None,
                authorization=None,
                credentials=None,
                db=mock_db
            )

        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_flexible_auth_prefers_cookie(self):
        """Test that cookie authentication is preferred over Bearer token."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        # Mock verify_token and get_user_with_role
        with patch("src.auth.jwt_dependencies.verify_token") as mock_verify:
            with patch("src.auth.jwt_dependencies.get_user_with_role") as mock_get_user:
                mock_verify.return_value = {"sub": str(
                    mock_user.id), "email": mock_user.email}
                mock_get_user.return_value = mock_user

                # Test with both cookie and Bearer token - should prefer cookie
                user = await get_current_user(
                    access_token="cookie_token_123",
                    authorization="Bearer bearer_token_456",
                    credentials=None,
                    db=mock_db
                )

                assert user == mock_user
                # Should have used the cookie token, not the Bearer token
                mock_verify.assert_called_once_with(
                    "cookie_token_123", mock_db)
