"""Tests for UserPermission model and related functionality."""

import pytest
from uuid import uuid4
from datetime import datetime

from src.app.auth.models import UserPermission


class TestUserPermissionModel:
    """Test UserPermission SQLAlchemy model."""

    def test_user_permission_model_attributes(self):
        """Test that UserPermission model has all required attributes."""
        user_permission = UserPermission()

        # Check all required attributes exist
        assert hasattr(user_permission, 'id')
        assert hasattr(user_permission, 'user_id')
        assert hasattr(user_permission, 'permission_id')
        assert hasattr(user_permission, 'created_at')
        assert hasattr(user_permission, 'updated_at')

        # Check relationships
        assert hasattr(user_permission, 'user')
        assert hasattr(user_permission, 'permission')

    def test_user_permission_repr(self):
        """Test UserPermission model string representation."""
        permission_id = uuid4()
        user_id = uuid4()
        permission_id_val = uuid4()

        # Create a mock object for testing repr
        class MockUserPermission:
            def __init__(self, id, user_id, permission_id):
                self.id = id
                self.user_id = user_id
                self.permission_id = permission_id

            def __repr__(self):
                return f"<UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id})>"

        mock_permission = MockUserPermission(
            permission_id, user_id, permission_id_val)
        expected = f"<UserPermission(id={permission_id}, user_id={user_id}, permission_id={permission_id_val})>"
        assert repr(mock_permission) == expected

    def test_user_permission_table_name(self):
        """Test that UserPermission has correct table name."""
        assert UserPermission.__tablename__ == "user_permissions"
