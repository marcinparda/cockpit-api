"""Tests for user management endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestUserManagementEndpoints:
    """Test user management endpoints without database dependencies."""

    def test_user_endpoints_exist(self):
        """Test that user management endpoints are properly registered."""
        client = TestClient(app)

        # Test endpoints exist (will fail auth but should not be 404)
        response = client.get("/api/v1/users/")
        assert response.status_code != 404  # Should be 401 (unauthorized)

        response = client.post("/api/v1/users/", json={})
        assert response.status_code != 404  # Should be 401/422

        response = client.get(
            "/api/v1/users/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code != 404  # Should be 401/422

    def test_role_endpoints_exist(self):
        """Test that role management endpoints are properly registered."""
        client = TestClient(app)

        # Test endpoints exist (will fail auth but should not be 404)
        response = client.get("/api/v1/roles/")
        assert response.status_code != 404  # Should be 401 (unauthorized)

    def test_user_endpoints_require_auth(self):
        """Test that user management endpoints require authentication."""
        client = TestClient(app)

        # All admin endpoints should require authentication
        endpoints = [
            ("GET", "/api/v1/users/"),
            ("POST", "/api/v1/users/"),
            ("GET", "/api/v1/users/123e4567-e89b-12d3-a456-426614174000"),
            ("PUT", "/api/v1/users/123e4567-e89b-12d3-a456-426614174000"),
            ("DELETE", "/api/v1/users/123e4567-e89b-12d3-a456-426614174000"),
            ("GET", "/api/v1/roles/"),
        ]

        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            assert response.status_code in [
                401, 422], f"Endpoint {method} {endpoint} should require auth"

    def test_user_endpoints_with_invalid_auth(self):
        """Test user endpoints with invalid JWT token."""
        client = TestClient(app)
        headers = {"Authorization": "Bearer invalid-token"}

        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 401

        response = client.get("/api/v1/roles/", headers=headers)
        assert response.status_code == 401


class TestUserSchemaIntegration:
    """Test user schema integration."""

    def test_user_schemas_import(self):
        """Test that all user schemas can be imported."""
        from src.app.users.schemas import (
            UserCreate, UserUpdate, UserWithRole, UserWithPermissions,
            UserPermissionAssign, UserPermissionRevoke,
            PasswordResetRequest, PasswordResetResponse
        )

        # Verify schemas are available
        assert UserCreate is not None
        assert UserUpdate is not None
        assert UserWithRole is not None
        assert UserWithPermissions is not None
        assert UserPermissionAssign is not None
        assert UserPermissionRevoke is not None
        assert PasswordResetRequest is not None
        assert PasswordResetResponse is not None

    def test_user_permission_assign_schema(self):
        """Test UserPermissionAssign schema validation."""
        from src.app.users.schemas import UserPermissionAssign
        from uuid import uuid4

        # Valid data
        data = UserPermissionAssign(
            permission_ids=[uuid4(), uuid4()]
        )
        assert len(data.permission_ids) == 2

        # Empty list should be valid
        data = UserPermissionAssign(permission_ids=[])
        assert len(data.permission_ids) == 0

    def test_password_reset_schemas(self):
        """Test password reset schemas."""
        from src.app.users.schemas import PasswordResetRequest, PasswordResetResponse

        # Reset request with password
        request = PasswordResetRequest(new_password="NewPass123!")
        assert request.new_password == "NewPass123!"

        # Reset request without password (generated)
        request = PasswordResetRequest()
        assert request.new_password is None

        # Reset response
        response = PasswordResetResponse(
            message="Password reset successfully",
            new_password="TempPass456!"
        )
        assert response.message == "Password reset successfully"
        assert response.new_password == "TempPass456!"


class TestUserServiceIntegration:
    """Test user service integration."""

    def test_user_service_imports(self):
        """Test that all user service functions can be imported."""
        from src.app.users.service import (
            get_all_users, create_user, update_user, delete_user,
            assign_user_role, assign_user_permissions, revoke_user_permission,
            reset_user_password, get_all_roles, generate_temporary_password
        )

        # Verify functions are available
        assert callable(get_all_users)
        assert callable(create_user)
        assert callable(update_user)
        assert callable(delete_user)
        assert callable(assign_user_role)
        assert callable(assign_user_permissions)
        assert callable(revoke_user_permission)
        assert callable(reset_user_password)
        assert callable(get_all_roles)
        assert callable(generate_temporary_password)

    def test_generate_temporary_password(self):
        """Test temporary password generation."""
        from src.app.users.service import generate_temporary_password

        # Default length
        password = generate_temporary_password()
        assert len(password) == 12
        assert isinstance(password, str)

        # Custom length
        password = generate_temporary_password(16)
        assert len(password) == 16

        # Generated passwords should be different
        password1 = generate_temporary_password()
        password2 = generate_temporary_password()
        assert password1 != password2


class TestAuthDependenciesIntegration:
    """Test authentication dependencies integration."""

    def test_auth_dependencies_import(self):
        """Test that auth dependencies can be imported."""
        from src.app.auth.dependencies import (
            require_admin_role, require_user_permissions
        )

        assert callable(require_admin_role)
        assert callable(require_user_permissions)

    def test_jwt_dependencies_import(self):
        """Test that JWT dependencies can be imported."""
        from src.app.auth.jwt_dependencies import (
            get_current_user, get_current_active_user
        )

        assert callable(get_current_user)
        assert callable(get_current_active_user)


class TestMainAppConfiguration:
    """Test main app router configuration."""

    def test_user_routers_registered(self):
        """Test that user and role routers are registered in main app."""
        from src.main import app

        # Check that routes are registered by trying to access them
        client = TestClient(app)

        # User management routes should exist (not 404)
        response = client.get("/api/v1/users/")
        assert response.status_code != 404, "User management routes should be registered"

        response = client.get("/api/v1/roles/")
        assert response.status_code != 404, "Role management routes should be registered"

    def test_app_includes_new_imports(self):
        """Test that main app imports include new modules."""
        import src.main
        import inspect

        # Get the source code of main.py
        source = inspect.getsource(src.main)

        # Check that users and roles are imported
        assert "users" in source
        assert "roles" in source
        assert "/api/v1/users" in source
        assert "/api/v1/roles" in source
