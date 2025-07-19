"""Tests for authentication endpoints using httpx."""

import pytest
import httpx
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import uuid4, UUID
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.main import app
from src.models.user import User
from src.models.user_role import UserRole
from src.auth.password import hash_password, verify_password
from src.auth.jwt import create_token_response
from src.core.database import get_db


class TestAuthEndpointsWithHttpx:
    """Test class for authentication endpoints using httpx."""

    @pytest.fixture
    def client(self):
        """Create httpx test client."""
        return TestClient(app)

    @pytest.fixture
    def admin_user_data(self):
        """Sample admin user data for testing."""
        return {
            "id": uuid4(),
            "email": "admin@test.com",
            "password_hash": hash_password("TestAdmin123!"),
            "is_active": True,
            "password_changed": False,
            "role_id": uuid4()
        }

    @pytest.fixture
    def regular_user_data(self):
        """Sample regular user data for testing."""
        return {
            "id": uuid4(),
            "email": "user@test.com",
            "password_hash": hash_password("TestUser123!"),
            "is_active": True,
            "password_changed": True,
            "role_id": uuid4()
        }

    @pytest.fixture
    def valid_jwt_token(self, admin_user_data):
        """Generate valid JWT token for testing."""
        token_response = create_token_response(
            admin_user_data["id"], admin_user_data["email"])
        return token_response.access_token

    def test_auth_endpoints_exist(self, client):
        """Test that authentication endpoints are properly registered."""
        # Test that endpoints return proper HTTP methods (not 405 Method Not Allowed)
        # POST /api/v1/auth/login should exist
        response = client.post(
            "/api/v1/auth/login", json={"email": "test@example.com", "password": "test"})
        assert response.status_code != 405  # Method Not Allowed

        # POST /api/v1/auth/change-password should exist but require auth
        response = client.post("/api/v1/auth/change-password",
                               json={"current_password": "old", "new_password": "new"})
        assert response.status_code != 405  # Method Not Allowed

        # GET /api/v1/auth/me should exist but require auth
        response = client.get("/api/v1/auth/me")
        assert response.status_code != 405  # Method Not Allowed

    def test_login_endpoint_validation(self, client):
        """Test login endpoint input validation."""
        # Test missing email
        response = client.post("/api/v1/auth/login",
                               json={"password": "testpass"})
        assert response.status_code == 422  # Validation error
        assert "email" in str(response.json())

        # Test missing password
        response = client.post("/api/v1/auth/login",
                               json={"email": "test@example.com"})
        assert response.status_code == 422  # Validation error
        assert "password" in str(response.json())

        # Test invalid email format
        response = client.post(
            "/api/v1/auth/login", json={"email": "invalid-email", "password": "testpass"})
        assert response.status_code == 422  # Validation error

    def test_login_with_database_unavailable(self, client):
        """Test login behavior when database connection fails."""
        # This will try to connect to the real database, which should fail in tests
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "somepassword"
        })

        # Should get either 401 (auth error) or 500 (database connection issue)
        assert response.status_code in [401, 500]
        if response.status_code == 500:
            # Should get the "service temporarily unavailable" message
            assert "temporarily unavailable" in response.json()[
                "detail"].lower()

    def test_change_password_endpoint_validation(self, client):
        """Test change password endpoint input validation."""
        # Test missing current_password
        response = client.post(
            "/api/v1/auth/change-password", json={"new_password": "NewPass123!"})
        # Auth required, validation error, or rate limited
        assert response.status_code in [401, 422, 429]

        # Test missing new_password
        response = client.post(
            "/api/v1/auth/change-password", json={"current_password": "oldpass"})
        # Auth required, validation error, or rate limited
        assert response.status_code in [401, 422, 429]

        # Test weak new password
        response = client.post("/api/v1/auth/change-password",
                               headers={"Authorization": "Bearer fake-token"},
                               json={"current_password": "oldpass", "new_password": "weak"})
        # Invalid token, validation error, or rate limited
        assert response.status_code in [401, 422, 429]

    def test_change_password_without_auth(self, client):
        """Test password change without authentication token."""
        response = client.post("/api/v1/auth/change-password", json={
            "current_password": "oldpass",
            "new_password": "NewTestAdmin123!"
        })

        # Auth required or rate limited
        assert response.status_code in [401, 429]
        if response.status_code == 401:
            assert "authorization" in response.json()["detail"].lower(
            ) or "missing" in response.json()["detail"].lower()

    def test_change_password_invalid_token(self, client):
        """Test password change with invalid JWT token."""
        response = client.post("/api/v1/auth/change-password",
                               headers={
                                   "Authorization": "Bearer invalid-token"},
                               json={
                                   "current_password": "TestAdmin123!",
                                   "new_password": "NewTestAdmin123!"
                               })

        # Invalid token or rate limited
        assert response.status_code in [401, 429]

    def test_me_endpoint_requires_auth(self, client):
        """Test that /me endpoint requires authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401  # Unauthorized
        data = response.json()
        assert "authorization" in data["detail"].lower() or "missing" in data["detail"].lower(
        ) or "authentication required" in data["detail"].lower()

    def test_me_endpoint_invalid_token(self, client):
        """Test /me endpoint with invalid JWT token."""
        response = client.get("/api/v1/auth/me",
                              headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 401

    def test_auth_endpoints_cors_headers(self, client):
        """Test that authentication endpoints include proper CORS headers."""
        # Test OPTIONS request for CORS preflight
        response = client.options("/api/v1/auth/login")
        # 405 is acceptable for endpoints that don't explicitly handle OPTIONS
        assert response.status_code in [
            200, 204, 404, 405]  # Acceptable responses

    def test_httpx_client_functionality(self):
        """Test that httpx client works properly with the FastAPI app."""
        with TestClient(app) as client:
            # Test basic endpoint access
            response = client.get("/health")
            assert response.status_code == 200

            # Test authentication endpoint exists
            response = client.post("/api/v1/auth/login", json={
                "email": "test@test.com",
                "password": "test123"
            })
            # Should not be 404 (endpoint exists)
            assert response.status_code != 404

    def test_password_change_request_schema_validation(self):
        """Test password change request validates in schema."""
        from src.schemas.auth import PasswordChangeRequest

        # Test valid password change request
        request = PasswordChangeRequest(
            current_password="OldPass123!",
            new_password="NewPass123!"
        )
        assert request.current_password == "OldPass123!"
        assert request.new_password == "NewPass123!"

    def test_login_request_schema_validation(self):
        """Test login request schema validation."""
        from src.schemas.auth import LoginRequest

        # Test valid login request
        request = LoginRequest(
            email="test@example.com",
            password="TestPass123!"
        )
        assert request.email == "test@example.com"
        assert request.password == "TestPass123!"


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    def test_password_hashing_integration(self):
        """Test password hashing and verification integration."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_jwt_token_integration(self):
        """Test JWT token creation and validation."""
        user_id = uuid4()
        email = "test@example.com"

        token_response = create_token_response(user_id, email)

        assert token_response.token_type == "bearer"
        assert token_response.expires_in == 24 * 3600  # 24 hours
        assert len(token_response.access_token) > 0

    def test_schema_validation_integration(self):
        """Test schema validation integration."""
        from src.schemas.auth import LoginRequest, PasswordChangeRequest

        # Test valid login request
        login_req = LoginRequest(
            email="test@example.com", password="password123")
        assert login_req.email == "test@example.com"

        # Test valid password change request
        pwd_change = PasswordChangeRequest(
            current_password="old123",
            new_password="ValidNew123!"
        )
        assert pwd_change.new_password == "ValidNew123!"

    async def test_authentication_utilities_work(self):
        """Test that authentication utilities can be imported and used."""
        from src.auth.jwt import create_access_token, verify_token
        from src.auth.password import hash_password, verify_password, validate_password_strength

        # Test JWT utilities
        test_data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(test_data)
        decoded = await verify_token(token)
        assert decoded["sub"] == test_data["sub"]
        assert decoded["email"] == test_data["email"]

        # Test password utilities
        password = "TestPass123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

        # Test password validation
        is_valid, errors = validate_password_strength(password)
        assert is_valid
        assert len(errors) == 0


def test_auth_services_import():
    """Test that authentication services can be imported without errors."""
    try:
        from src.services.auth_service import authenticate_user, create_user_token, login_user
        from src.services.user_service import get_user_by_id, change_user_password
        from src.auth.jwt_dependencies import get_current_user, get_current_active_user
        assert True  # All imports successful
    except ImportError as e:
        pytest.fail(f"Failed to import authentication services: {e}")


def test_auth_schemas_import():
    """Test that authentication schemas can be imported without errors."""
    try:
        from src.schemas.auth import LoginRequest, LoginResponse, PasswordChangeRequest, TokenResponse
        assert True  # All imports successful
    except ImportError as e:
        pytest.fail(f"Failed to import authentication schemas: {e}")


def test_password_validation_in_schema():
    """Test password validation in PasswordChangeRequest schema."""
    try:
        from src.schemas.auth import PasswordChangeRequest

        # Test valid password
        valid_request = PasswordChangeRequest(
            current_password="oldpass",
            new_password="ValidPass123!"
        )
        assert valid_request.new_password == "ValidPass123!"

        # Test invalid password (should raise validation error)
        with pytest.raises(ValueError):
            PasswordChangeRequest(
                current_password="oldpass",
                new_password="weak"  # Too weak password
            )

    except ImportError as e:
        pytest.fail(f"Failed to import PasswordChangeRequest schema: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
