"""Tests for user permission system."""

import pytest
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from src.auth.permissions import (
    check_user_permissions,
    get_user_permissions,
    user_has_admin_role,
    get_admin_permissions
)
from src.auth.enums.features import Features
from src.auth.enums.actions import Actions
from src.auth.enums.roles import Roles
from src.models.user import User
from src.models.user_role import UserRole
from src.models.user_permission import UserPermission
from src.models.permission import Permission
from src.models.feature import Feature
from src.models.action import Action


class TestUserPermissions:
    """Test user permission checking functions."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def admin_user(self):
        """Create a mock admin user."""
        user = MagicMock(spec=User)
        user.id = UUID("12345678-1234-5678-9abc-123456789abc")
        user.is_active = True
        user.role = MagicMock(spec=UserRole)
        user.role.name = Roles.ADMIN.value
        return user

    @pytest.fixture
    def regular_user(self):
        """Create a mock regular user."""
        user = MagicMock(spec=User)
        user.id = UUID("87654321-4321-8765-cba9-987654321cba")
        user.is_active = True
        user.role = MagicMock(spec=UserRole)
        user.role.name = Roles.USER.value
        return user

    @pytest.fixture
    def inactive_user(self):
        """Create a mock inactive user."""
        user = MagicMock(spec=User)
        user.id = UUID("11111111-1111-1111-1111-111111111111")
        user.is_active = False
        user.role = MagicMock(spec=UserRole)
        user.role.name = Roles.USER.value
        return user

    @pytest.fixture
    def feature_obj(self):
        """Create a mock feature object."""
        feature = MagicMock(spec=Feature)
        feature.id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        feature.name = "EXPENSES"
        return feature

    @pytest.fixture
    def action_obj(self):
        """Create a mock action object."""
        action = MagicMock(spec=Action)
        action.id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        action.name = "READ"
        return action

    @pytest.fixture
    def permission_obj(self, feature_obj, action_obj):
        """Create a mock permission object."""
        permission = MagicMock(spec=Permission)
        permission.id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
        permission.feature_id = feature_obj.id
        permission.action_id = action_obj.id
        return permission

    @pytest.fixture
    def user_permission_obj(self, permission_obj):
        """Create a mock user permission object."""
        user_perm = MagicMock(spec=UserPermission)
        user_perm.permission_id = permission_obj.id
        return user_perm

    @pytest.mark.asyncio
    async def test_check_user_permissions_admin_user(self, mock_db, admin_user):
        """Test that admin users have all permissions."""
        # Mock database query for user
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = admin_user
        mock_db.execute.return_value = mock_result

        result = await check_user_permissions(
            mock_db, admin_user.id, Features.EXPENSES, Actions.READ
        )

        assert result is True
        # Should only query for user, not features/actions/permissions
        assert mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_check_user_permissions_inactive_user(self, mock_db, inactive_user):
        """Test that inactive users have no permissions."""
        # Mock database query for user
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = inactive_user
        mock_db.execute.return_value = mock_result

        result = await check_user_permissions(
            mock_db, inactive_user.id, Features.EXPENSES, Actions.READ
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_user_not_found(self, mock_db):
        """Test that non-existent users have no permissions."""
        # Mock database query for user returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = UUID("00000000-0000-0000-0000-000000000000")
        result = await check_user_permissions(
            mock_db, user_id, Features.EXPENSES, Actions.READ
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_regular_user_with_permission(
        self, mock_db, regular_user, feature_obj, action_obj, permission_obj, user_permission_obj
    ):
        """Test that regular users with specific permissions are granted access."""
        # Mock database queries
        mock_results = [
            MagicMock(),  # User query
            MagicMock(),  # Feature query
            MagicMock(),  # Action query
            MagicMock(),  # Permission query
            MagicMock(),  # UserPermission query
        ]

        mock_results[0].scalars.return_value.first.return_value = regular_user
        mock_results[1].scalars.return_value.first.return_value = feature_obj
        mock_results[2].scalars.return_value.first.return_value = action_obj
        mock_results[3].scalars.return_value.first.return_value = permission_obj
        mock_results[4].scalars.return_value.first.return_value = user_permission_obj

        mock_db.execute.side_effect = mock_results

        result = await check_user_permissions(
            mock_db, regular_user.id, Features.EXPENSES, Actions.READ
        )

        assert result is True
        assert mock_db.execute.call_count == 5

    @pytest.mark.asyncio
    async def test_check_user_permissions_regular_user_without_permission(
        self, mock_db, regular_user, feature_obj, action_obj, permission_obj
    ):
        """Test that regular users without specific permissions are denied access."""
        # Mock database queries
        mock_results = [
            MagicMock(),  # User query
            MagicMock(),  # Feature query
            MagicMock(),  # Action query
            MagicMock(),  # Permission query
            MagicMock(),  # UserPermission query
        ]

        mock_results[0].scalars.return_value.first.return_value = regular_user
        mock_results[1].scalars.return_value.first.return_value = feature_obj
        mock_results[2].scalars.return_value.first.return_value = action_obj
        mock_results[3].scalars.return_value.first.return_value = permission_obj
        # No user permission
        mock_results[4].scalars.return_value.first.return_value = None

        mock_db.execute.side_effect = mock_results

        result = await check_user_permissions(
            mock_db, regular_user.id, Features.EXPENSES, Actions.READ
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_permissions_admin_user(self, mock_db, admin_user):
        """Test getting all permissions for admin user."""
        # Mock database queries
        mock_results = [
            MagicMock(),  # User query
            MagicMock(),  # All permissions query
        ]

        mock_results[0].scalars.return_value.first.return_value = admin_user
        mock_results[1].scalars.return_value.all.return_value = [
            "perm1", "perm2", "perm3"]

        mock_db.execute.side_effect = mock_results

        result = await get_user_permissions(mock_db, admin_user.id)

        assert result == ["perm1", "perm2", "perm3"]
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_permissions_regular_user(self, mock_db, regular_user):
        """Test getting permissions for regular user."""
        # Mock database queries
        mock_results = [
            MagicMock(),  # User query
            MagicMock(),  # User permissions query
        ]

        mock_results[0].scalars.return_value.first.return_value = regular_user
        mock_results[1].scalars.return_value.all.return_value = [
            "perm1", "perm2"]

        mock_db.execute.side_effect = mock_results

        result = await get_user_permissions(mock_db, regular_user.id)

        assert result == ["perm1", "perm2"]
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_permissions_inactive_user(self, mock_db, inactive_user):
        """Test getting permissions for inactive user."""
        # Mock database query for user
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = inactive_user
        mock_db.execute.return_value = mock_result

        result = await get_user_permissions(mock_db, inactive_user.id)

        assert result == []
        assert mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_user_has_admin_role_admin_user(self, mock_db, admin_user):
        """Test checking admin role for admin user."""
        # Mock database query for user
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = admin_user
        mock_db.execute.return_value = mock_result

        result = await user_has_admin_role(mock_db, admin_user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_user_has_admin_role_regular_user(self, mock_db, regular_user):
        """Test checking admin role for regular user."""
        # Mock database query for user
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = regular_user
        mock_db.execute.return_value = mock_result

        result = await user_has_admin_role(mock_db, regular_user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_user_has_admin_role_user_not_found(self, mock_db):
        """Test checking admin role for non-existent user."""
        # Mock database query for user returning None
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = UUID("00000000-0000-0000-0000-000000000000")
        result = await user_has_admin_role(mock_db, user_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_admin_permissions(self, mock_db):
        """Test getting all permissions for admin role."""
        # Mock database query for all permissions
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            "perm1", "perm2", "perm3"]
        mock_db.execute.return_value = mock_result

        result = await get_admin_permissions(mock_db)

        assert result == ["perm1", "perm2", "perm3"]
        assert mock_db.execute.call_count == 1


class TestUserPermissionHelpers:
    """Test user permission helper functions."""

    def test_user_feature_permissions_helper_import(self):
        """Test that user permission helpers can be imported."""
        from src.auth.permission_helpers import (
            get_user_feature_permissions,
            get_user_expenses_permissions,
            get_user_categories_permissions,
            get_user_payment_methods_permissions,
            get_user_todo_items_permissions,
            get_user_api_keys_permissions,
            get_user_shared_permissions
        )

        # Test that helpers are callable
        assert callable(get_user_feature_permissions)
        assert callable(get_user_expenses_permissions)
        assert callable(get_user_categories_permissions)
        assert callable(get_user_payment_methods_permissions)
        assert callable(get_user_todo_items_permissions)
        assert callable(get_user_api_keys_permissions)
        assert callable(get_user_shared_permissions)

    def test_user_permission_dependency_creation(self):
        """Test that user permission dependencies can be created."""
        from src.auth.permission_helpers import get_user_feature_permissions

        # Test creating a permission dependency
        permission_dep = get_user_feature_permissions(
            Features.EXPENSES, Actions.READ)
        assert callable(permission_dep)


class TestUserPermissionDependencies:
    """Test user permission FastAPI dependencies."""

    def test_user_permission_dependencies_import(self):
        """Test that user permission dependencies can be imported."""
        from src.auth.dependencies import require_user_permissions, require_admin_role

        # Test that dependencies are callable
        assert callable(require_user_permissions)
        assert callable(require_admin_role)

    def test_user_permission_dependencies_have_correct_signature(self):
        """Test that user permission dependencies have the correct signature."""
        from src.auth.dependencies import require_user_permissions, require_admin_role
        import inspect

        # Check require_user_permissions signature
        sig = inspect.signature(require_user_permissions)
        params = list(sig.parameters.keys())
        assert "feature" in params
        assert "action" in params
        assert "current_user" in params
        assert "db" in params

        # Check require_admin_role signature
        sig = inspect.signature(require_admin_role)
        params = list(sig.parameters.keys())
        assert "current_user" in params
