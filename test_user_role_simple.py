#!/usr/bin/env python3
"""Simple validation script for UserRole implementation."""
from src.schemas.user_role import UserRoleCreate, UserRoleUpdate, UserRole as UserRoleSchema
from src.models.user_role import UserRole
from datetime import datetime
from uuid import UUID
import sys
sys.path.append('/app')


def test_user_role_model():
    """Test UserRole model attributes."""
    print("🧪 Testing UserRole model...")

    role = UserRole()

    # Test attributes exist
    assert hasattr(role, 'id'), "Missing id attribute"
    assert hasattr(role, 'name'), "Missing name attribute"
    assert hasattr(role, 'description'), "Missing description attribute"
    assert hasattr(role, 'created_at'), "Missing created_at attribute"
    assert hasattr(role, 'updated_at'), "Missing updated_at attribute"

    # Test table name
    assert UserRole.__tablename__ == "user_roles", f"Wrong table name: {UserRole.__tablename__}"

    print("✅ UserRole model tests passed!")


def test_user_role_schemas():
    """Test UserRole schemas."""
    print("🧪 Testing UserRole schemas...")

    # Test UserRoleCreate
    role_data = {
        "name": "Manager",
        "description": "Management role with elevated permissions"
    }
    role = UserRoleCreate(**role_data)
    assert role.name == "Manager", f"Wrong name: {role.name}"
    assert role.description == "Management role with elevated permissions", f"Wrong description: {role.description}"

    # Test UserRoleCreate without description
    role_minimal = UserRoleCreate(name="BasicUser")
    assert role_minimal.name == "BasicUser", f"Wrong name: {role_minimal.name}"
    assert role_minimal.description is None, f"Description should be None: {role_minimal.description}"

    # Test UserRoleUpdate
    update_data = {
        "name": "UpdatedRole",
        "description": "Updated description"
    }
    role_update = UserRoleUpdate(**update_data)
    assert role_update.name == "UpdatedRole", f"Wrong name: {role_update.name}"
    assert role_update.description == "Updated description", f"Wrong description: {role_update.description}"

    # Test UserRole response schema
    role_id = "123e4567-e89b-12d3-a456-426614174000"
    now = datetime.now()

    response_data = {
        "id": role_id,
        "name": "Admin",
        "description": "Administrator role",
        "created_at": now,
        "updated_at": now
    }

    role_response = UserRoleSchema(**response_data)
    assert str(role_response.id) == role_id, f"Wrong id: {role_response.id}"
    assert role_response.name == "Admin", f"Wrong name: {role_response.name}"
    assert role_response.description == "Administrator role", f"Wrong description: {role_response.description}"
    assert role_response.created_at == now, f"Wrong created_at: {role_response.created_at}"
    assert role_response.updated_at == now, f"Wrong updated_at: {role_response.updated_at}"

    print("✅ UserRole schema tests passed!")


def test_default_roles():
    """Test default role creation."""
    print("🧪 Testing default roles...")

    # Test Admin role
    admin_role = UserRoleCreate(
        name="Admin",
        description="Full system access with all permissions"
    )
    assert admin_role.name == "Admin", f"Wrong admin name: {admin_role.name}"
    assert admin_role.description is not None, "Admin description should not be None"

    # Test User role
    user_role = UserRoleCreate(
        name="User",
        description="Standard user access with assigned permissions"
    )
    assert user_role.name == "User", f"Wrong user name: {user_role.name}"
    assert user_role.description is not None, "User description should not be None"

    # Test TestUser role
    test_user_role = UserRoleCreate(
        name="TestUser",
        description="Limited access for testing purposes"
    )
    assert test_user_role.name == "TestUser", f"Wrong test user name: {test_user_role.name}"
    assert test_user_role.description is not None, "TestUser description should not be None"

    print("✅ Default role tests passed!")


def test_schema_validation():
    """Test schema validation."""
    print("🧪 Testing schema validation...")

    # Test that empty name fails
    try:
        UserRoleCreate(name="")
        assert False, "Empty name should have failed validation"
    except ValueError:
        pass  # Expected

    print("✅ Schema validation tests passed!")


def main():
    """Run all tests."""
    print("🚀 Starting UserRole implementation tests...\n")

    try:
        test_user_role_model()
        test_user_role_schemas()
        test_default_roles()
        test_schema_validation()

        print("\n🎉 All tests passed! UserRole implementation is working correctly.")
        print("📊 Test Summary:")
        print("   ✅ UserRole model attributes")
        print("   ✅ UserRole schemas (Create, Update, Response)")
        print("   ✅ Default role creation")
        print("   ✅ Schema validation")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
