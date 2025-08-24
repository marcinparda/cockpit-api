"""Tests for UserRole model and schemas."""
import pytest
from pydantic import ValidationError
from uuid import UUID
from datetime import datetime
from src.models.user_role import UserRole
from src.app.auth.schemas import UserRoleCreate, UserRoleUpdate, UserRole as UserRoleSchema
from src.app.auth.enums.roles import Roles


class TestUserRoleModel:
    """Test UserRole SQLAlchemy model."""

    def test_user_role_model_attributes(self):
        """Test that UserRole model has expected attributes."""
        # Test that the model can be instantiated
        role = UserRole()

        # Test that all expected attributes exist
        assert hasattr(role, 'id')
        assert hasattr(role, 'name')
        assert hasattr(role, 'description')
        assert hasattr(role, 'created_at')
        assert hasattr(role, 'updated_at')

        # Test table name
        assert UserRole.__tablename__ == "user_roles"


class TestUserRoleSchemas:
    """Test UserRole Pydantic schemas."""

    def test_user_role_create_schema(self):
        """Test UserRoleCreate schema validation."""
        # Valid role creation
        role_data = {
            "name": "Manager",
            "description": "Management role with elevated permissions"
        }
        role = UserRoleCreate(**role_data)
        assert role.name == "Manager"
        assert role.description == "Management role with elevated permissions"

        # Valid role creation without description
        role_minimal = UserRoleCreate(name="BasicUser")
        assert role_minimal.name == "BasicUser"
        assert role_minimal.description is None

    def test_user_role_create_schema_validation(self):
        """Test UserRoleCreate schema validation errors."""
        # Missing name should fail
        with pytest.raises(ValidationError):
            UserRoleCreate()

        # Empty name should fail
        with pytest.raises(ValidationError):
            UserRoleCreate(name="")

        # Whitespace-only name should fail
        with pytest.raises(ValidationError):
            UserRoleCreate(name="   ")

    def test_user_role_update_schema(self):
        """Test UserRoleUpdate schema."""
        role_data = {
            "name": "UpdatedRole",
            "description": "Updated description"
        }
        role = UserRoleUpdate(**role_data)
        assert role.name == "UpdatedRole"
        assert role.description == "Updated description"

    def test_user_role_response_schema(self):
        """Test UserRole response schema."""
        # Create a mock role response
        role_id = "123e4567-e89b-12d3-a456-426614174000"
        now = datetime.now()

        role_data = {
            "id": role_id,
            "name": Roles.ADMIN.value,
            "description": "Administrator role",
            "created_at": now,
            "updated_at": now
        }

        role = UserRoleSchema(**role_data)
        assert str(role.id) == role_id
        assert role.name == Roles.ADMIN.value
        assert role.description == "Administrator role"
        assert role.created_at == now
        assert role.updated_at == now

    def test_user_role_schema_from_attributes(self):
        """Test that schema can be created from model attributes."""
        # This tests the Config.from_attributes = True setting
        mock_model = type('MockModel', (), {
            'id': UUID('123e4567-e89b-12d3-a456-426614174000'),
            'name': 'TestRole',
            'description': 'Test description',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })()

        # This should work because of from_attributes = True
        role = UserRoleSchema.model_validate(mock_model)
        assert role.name == 'TestRole'
        assert role.description == 'Test description'


class TestUserRoleIntegration:
    """Integration tests for UserRole functionality."""

    def test_role_name_uniqueness_constraint(self):
        """Test that role names must be unique (will be enforced by database)."""
        # This test documents the expectation that role names are unique
        # The actual constraint is enforced at the database level
        role1_data = {"name": "UniqueRole", "description": "First role"}
        role2_data = {"name": "UniqueRole", "description": "Second role"}

        role1 = UserRoleCreate(**role1_data)
        role2 = UserRoleCreate(**role2_data)

        # Both objects can be created in Python, but database will enforce uniqueness
        assert role1.name == role2.name
        assert role1.description != role2.description

    def test_default_roles_structure(self):
        """Test that default roles have expected structure."""
        admin_role = UserRoleCreate(
            name=Roles.ADMIN.value,
            description="Full system access with all permissions"
        )
        user_role = UserRoleCreate(
            name=Roles.USER.value,
            description="Standard user access with assigned permissions"
        )
        test_user_role = UserRoleCreate(
            name=Roles.TEST_USER.value,
            description="Limited access for testing purposes"
        )

        # Verify all default roles can be created
        # Test role names
        assert admin_role.name == Roles.ADMIN.value
        assert user_role.name == Roles.USER.value
        assert test_user_role.name == Roles.TEST_USER.value

        # Verify they all have descriptions
        assert admin_role.description is not None
        assert user_role.description is not None
        assert test_user_role.description is not None
