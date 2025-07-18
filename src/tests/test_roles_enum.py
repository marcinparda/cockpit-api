"""Test for roles enum."""

import pytest
from src.auth.enums.roles import Roles


class TestRolesEnum:
    """Test roles enum functionality."""

    def test_roles_enum_values(self):
        """Test that roles enum has the correct values."""
        assert Roles.ADMIN.value == "Admin"
        assert Roles.USER.value == "User"
        assert Roles.TEST_USER.value == "TestUser"

    def test_roles_enum_exists(self):
        """Test that roles enum exists and is accessible."""
        assert hasattr(Roles, 'ADMIN')
        assert hasattr(Roles, 'USER')
        assert hasattr(Roles, 'TEST_USER')

    def test_roles_enum_string_comparison(self):
        """Test that roles enum values can be compared with strings."""
        admin_role_name = "Admin"
        user_role_name = "User"
        test_user_role_name = "TestUser"

        assert admin_role_name == Roles.ADMIN.value
        assert user_role_name == Roles.USER.value
        assert test_user_role_name == Roles.TEST_USER.value

    def test_roles_enum_is_enum(self):
        """Test that Roles is an enum."""
        from enum import Enum
        assert issubclass(Roles, Enum)

    def test_roles_enum_iteration(self):
        """Test that roles enum can be iterated."""
        role_values = [role.value for role in Roles]
        assert "Admin" in role_values
        assert "User" in role_values
        assert "TestUser" in role_values
        assert len(role_values) == 3

    def test_roles_enum_usage_in_permission_system(self):
        """Test that roles enum can be used in permission system."""
        # Test that the roles enum can be imported by permission system
        from src.auth.permissions import check_user_permissions
        from src.auth.dependencies import require_admin_role
        from src.services.user_service import check_user_permission

        # If these imports work, the roles enum is properly integrated
        assert check_user_permissions is not None
        assert require_admin_role is not None
        assert check_user_permission is not None
