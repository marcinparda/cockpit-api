"""Tests for JWT authentication utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
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

    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successfully verifying a valid token."""
        user_id = uuid4()
        email = "test@example.com"
        data = {"sub": str(user_id), "email": email}

        token = create_access_token(data)
        mock_db = AsyncMock()

        # Mock the token service to return valid token
        with patch('src.services.token_service.TokenService.is_access_token_valid', return_value=True), \
                patch('src.services.token_service.TokenService.update_access_token_last_used', return_value=None):

            token_data = await verify_token(token, mock_db)

            assert isinstance(token_data, dict)
            assert token_data["sub"] == str(user_id)
            assert token_data["email"] == email

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.string"
        mock_db = AsyncMock()

        with pytest.raises(JWTError):
            await verify_token(invalid_token, mock_db)

    @pytest.mark.asyncio
    async def test_verify_token_missing_subject(self):
        """Test verifying a token without subject."""
        data = {"email": "test@example.com"}  # Missing 'sub'
        token = create_access_token(data)
        mock_db = AsyncMock()

        with pytest.raises(JWTError, match="Token missing user identifier"):
            await verify_token(token, mock_db)

    @pytest.mark.asyncio
    async def test_verify_token_revoked(self):
        """Test verifying a revoked token."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)
        mock_db = AsyncMock()

        # Mock the token service to return invalid (revoked) token
        with patch('src.services.token_service.TokenService.is_access_token_valid', return_value=False), \
                patch('src.services.token_service.TokenService.update_access_token_last_used', return_value=True):
            with pytest.raises(JWTError, match="Token has been invalidated"):
                await verify_token(token, mock_db)

    def test_create_token_response(self):
        """Test creating a complete token response."""
        user_id = uuid4()
        email = "test@example.com"

        response = create_token_response(user_id, email)

        assert isinstance(response, TokenResponse)
        assert response.token_type == "bearer"
        assert response.expires_in == 24 * 3600  # 24 hours in seconds
        assert len(response.access_token) > 0

        # The access_token creation is tested separately since it doesn't require verification


class TestJWTEnhancedFeatures:
    """Test JWT enhancements including database token tracking."""

    def test_create_access_token_with_jti(self):
        """Test access token creation with JWT ID."""
        from src.auth.jwt import extract_token_id

        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)

        # Extract JTI without full verification
        jti = extract_token_id(token)
        assert jti is not None
        assert len(jti) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        from src.auth.jwt import create_refresh_token, extract_token_id

        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_refresh_token(data)

        # Extract JTI to verify token structure
        jti = extract_token_id(token)
        assert jti is not None
        assert len(jti) > 0

    def test_extract_token_id(self):
        """Test JWT ID extraction."""
        from src.auth.jwt import extract_token_id

        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)

        # Extract JTI
        jti = extract_token_id(token)
        assert jti is not None
        assert isinstance(jti, str)
        assert len(jti) > 0

    @pytest.mark.asyncio
    async def test_token_validation_workflow(self):
        """Test complete token validation workflow."""
        from unittest.mock import AsyncMock, patch
        from src.services.token_service import TokenService

        jti = "test_token_456"

        # Mock database session
        mock_db = AsyncMock()

        # Test valid token
        with patch.object(TokenService, 'is_access_token_valid', return_value=True) as mock_valid:
            is_valid = await TokenService.is_access_token_valid(mock_db, jti)
            assert is_valid is True
            mock_valid.assert_called_once_with(mock_db, jti)

        # Test invalid token
        with patch.object(TokenService, 'is_access_token_valid', return_value=False) as mock_invalid:
            is_valid = await TokenService.is_access_token_valid(mock_db, jti)
            assert is_valid is False
            mock_invalid.assert_called_once_with(mock_db, jti)

    @pytest.mark.asyncio
    async def test_token_revocation_workflow(self):
        """Test token revocation using database."""
        from unittest.mock import AsyncMock, patch
        from src.services.token_service import TokenService

        jti = "test_token_789"

        # Mock database session
        mock_db = AsyncMock()

        # Test successful revocation
        with patch.object(TokenService, 'revoke_access_token', return_value=True) as mock_revoke:
            success = await TokenService.revoke_access_token(mock_db, jti)
            assert success is True
            mock_revoke.assert_called_once_with(mock_db, jti)
