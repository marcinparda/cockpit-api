"""
Basic integration test for the new database-backed token system.
"""
import asyncio
import pytest
from uuid import uuid4

from src.services.token_service import TokenService
from src.auth.jwt import create_access_token, verify_token
from src.core.config import settings


class TestTokenIntegration:
    """Test the new token system integration."""

    def test_token_service_creation_without_db(self):
        """Test that we can create tokens without database (fallback mode)."""
        test_data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(test_data)

        # Verify token structure
        assert isinstance(token, str)
        assert len(token) > 20  # JWT should be reasonably long

        # Test without database - should work in fallback mode
        async def test_verify():
            payload = await verify_token(token)  # No db parameter
            return payload

        result = asyncio.run(test_verify())
        assert result["sub"] == test_data["sub"]
        assert result["email"] == test_data["email"]
        assert "jti" in result
        assert "exp" in result

    def test_token_settings_exist(self):
        """Test that token management settings exist."""
        assert hasattr(settings, 'TOKEN_CLEANUP_INTERVAL_HOURS')
        assert hasattr(settings, 'TOKEN_CLEANUP_RETENTION_DAYS')

        # Verify default values
        assert settings.TOKEN_CLEANUP_INTERVAL_HOURS == 24
        assert settings.TOKEN_CLEANUP_RETENTION_DAYS == 7
