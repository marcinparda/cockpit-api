"""Quick test to verify the updated login endpoint returns refresh tokens."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.services.auth_service import login_user
from src.schemas.auth import LoginResponse


@pytest.mark.asyncio
async def test_login_user_returns_refresh_token():
    """Test that login_user now returns refresh token in response."""
    # Mock user
    mock_user = AsyncMock()
    mock_user.id = uuid4()
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.password_changed = True

    # Mock database session
    mock_db = AsyncMock()

    # Mock authenticate_user and create_user_refresh_token
    with patch("src.services.auth_service.authenticate_user") as mock_auth:
        with patch("src.services.auth_service.create_user_refresh_token") as mock_create_tokens:
            mock_auth.return_value = mock_user
            mock_create_tokens.return_value = AsyncMock(
                access_token="access_token_123",
                refresh_token="refresh_token_456",
                token_type="bearer",
                expires_in=86400,
                refresh_expires_in=2592000
            )

            # Call login_user
            response = await login_user(mock_db, "test@example.com", "password123")

            # Verify response structure
            assert isinstance(response, LoginResponse)
            assert response.message == "Successfully logged in"


if __name__ == "__main__":
    pytest.main([__file__])
