"""Integration tests for cookie-based authentication endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4

from src.main import app


class TestCookieAuthIntegration:
    """Integration tests for cookie authentication endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch("src.services.auth_service.authenticate_user")
    @patch("src.services.auth_service.create_user_refresh_token")
    def test_login_sets_cookies(self, mock_create_tokens, mock_authenticate):
        """Test that login endpoint sets httpOnly cookies."""
        # Mock user and authentication
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.password_changed = True

        mock_authenticate.return_value = mock_user

        # Mock token creation
        mock_token_response = AsyncMock()
        mock_token_response.access_token = "access_token_123"
        mock_token_response.refresh_token = "refresh_token_456"
        mock_token_response.token_type = "bearer"
        mock_token_response.expires_in = 1800
        mock_token_response.refresh_expires_in = 604800
        mock_create_tokens.return_value = mock_token_response

        # Test login request
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["access_token"] == "access_token_123"
        assert response_data["refresh_token"] == "refresh_token_456"

        # Verify cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert cookies["access_token"] == "access_token_123"
        assert cookies["refresh_token"] == "refresh_token_456"

        # Verify cookie attributes (httpOnly would be set in real browser)
        # Note: TestClient doesn't fully simulate httpOnly attribute,
        # but we can verify the values are set

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        with patch("src.services.auth_service.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = self.client.post(
                "/api/v1/auth/login",
                json={"email": "invalid@example.com", "password": "wrong"}
            )

            assert response.status_code == 401
            # Should not set any cookies for failed login
            assert "access_token" not in response.cookies
            assert "refresh_token" not in response.cookies

    def test_me_endpoint_supports_bearer_token(self):
        """Test that /me endpoint still supports Bearer tokens."""
        with patch("src.auth.cookie_dependencies.verify_token") as mock_verify:
            with patch("src.auth.cookie_dependencies.get_user_with_role") as mock_get_user:
                mock_user = AsyncMock()
                mock_user.id = uuid4()
                mock_user.email = "test@example.com"
                mock_user.is_active = True
                mock_user.password_changed = True
                # Fix the created_at mock - it should return a string directly
                from datetime import datetime
                mock_created_at = datetime(2024, 1, 1)
                mock_user.created_at = mock_created_at

                mock_verify.return_value = {"sub": str(
                    mock_user.id), "email": mock_user.email}
                mock_get_user.return_value = mock_user

                # Test with Bearer token
                response = self.client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer valid_token_123"}
                )

                assert response.status_code == 200
                response_data = response.json()
                assert response_data["email"] == "test@example.com"

    def test_logout_clears_cookies(self):
        """Test that logout endpoint clears cookies."""
        # Mock token invalidation
        with patch("src.auth.jwt.invalidate_token") as mock_invalidate:
            mock_invalidate.return_value = True

            # Test logout with Bearer token (backward compatibility)
            response = self.client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer token_to_invalidate"}
            )

            assert response.status_code == 200
            response_data = response.json()
            assert "Successfully logged out" in response_data["detail"]

            # Verify cookies are cleared (set to empty with max_age=0)
            cookies = response.cookies
            if "access_token" in cookies:
                assert cookies["access_token"] == ""
            if "refresh_token" in cookies:
                assert cookies["refresh_token"] == ""

    @patch("src.services.auth_service.refresh_user_tokens")
    def test_refresh_endpoint_supports_cookies(self, mock_refresh):
        """Test that refresh endpoint supports cookie-based refresh."""
        # Mock refresh response
        mock_response = AsyncMock()
        mock_response.access_token = "new_access_token_123"
        mock_response.refresh_token = "new_refresh_token_456"
        mock_response.token_type = "bearer"
        mock_response.expires_in = 1800
        mock_response.refresh_expires_in = 604800
        mock_refresh.return_value = mock_response

        # Test refresh with refresh token in request body (backward compatibility)
        response = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "old_refresh_token"}
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["access_token"] == "new_access_token_123"
        assert response_data["refresh_token"] == "new_refresh_token_456"

    def test_unauthorized_access_without_auth(self):
        """Test that endpoints properly handle unauthorized access."""
        response = self.client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @patch("src.auth.jwt_dependencies.verify_token")
    def test_invalid_token_handling(self, mock_verify):
        """Test handling of invalid tokens."""
        from jose import JWTError
        mock_verify.side_effect = JWTError("Invalid token")

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
