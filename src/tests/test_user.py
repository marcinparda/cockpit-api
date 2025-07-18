"""Tests for User model and schemas."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.user_role import UserRole
from src.schemas.user import UserCreate, UserUpdate, User as UserResponse


class TestUserModel:
    """Test User SQLAlchemy model."""

    def test_user_model_attributes(self):
        """Test that User model has all required attributes."""
        user = User()

        # Check all required attributes exist
        assert hasattr(user, 'id')
        assert hasattr(user, 'email')
        assert hasattr(user, 'password_hash')
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'role_id')
        assert hasattr(user, 'password_changed')
        assert hasattr(user, 'created_by')
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')

        # Check relationships
        assert hasattr(user, 'role')
        assert hasattr(user, 'permissions')
        assert hasattr(user, 'creator')

    def test_user_repr(self):
        """Test User model string representation."""
        user_id = uuid4()
        user = User()
        user.id = user_id
        user.email = "test@example.com"
        user.is_active = True

        expected = f"<User(id={user_id}, email=test@example.com, is_active=True)>"
        assert repr(user) == expected


class TestUserSchemas:
    """Test User Pydantic schemas."""

    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
        role_id = uuid4()

        # Valid user creation data
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role_id": role_id,
            "is_active": True
        }

        user_create = UserCreate(**user_data)
        assert user_create.email == "test@example.com"
        assert user_create.password == "SecurePass123!"
        assert user_create.role_id == role_id
        assert user_create.is_active is True

    def test_user_create_password_validation(self):
        """Test password validation in UserCreate schema."""
        role_id = uuid4()
        base_data = {
            "email": "test@example.com",
            "role_id": role_id
        }

        # Test password too short
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            UserCreate(**base_data, password="short")

        # Test password without uppercase
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            UserCreate(**base_data, password="lowercase123!")

        # Test password without lowercase
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            UserCreate(**base_data, password="UPPERCASE123!")

        # Test password without digit
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            UserCreate(**base_data, password="NoNumbers!")

        # Test password without special character
        with pytest.raises(ValueError, match="Password must contain at least one special character"):
            UserCreate(**base_data, password="NoSpecial123")

    def test_user_update_schema(self):
        """Test UserUpdate schema."""
        role_id = uuid4()

        # All fields optional
        user_update = UserUpdate()
        assert user_update.email is None
        assert user_update.is_active is None
        assert user_update.role_id is None

        # With values
        user_update = UserUpdate(
            email="updated@example.com",
            is_active=False,
            role_id=role_id
        )
        assert user_update.email == "updated@example.com"
        assert user_update.is_active is False
        assert user_update.role_id == role_id

    def test_user_response_schema(self):
        """Test User response schema."""
        user_id = uuid4()
        role_id = uuid4()
        created_by = uuid4()
        now = datetime.now(UTC)

        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "is_active": True,
            "role_id": role_id,
            "password_changed": False,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }

        user_response = UserResponse(**user_data)
        assert user_response.id == user_id
        assert user_response.email == "test@example.com"
        assert user_response.is_active is True
        assert user_response.role_id == role_id
        assert user_response.password_changed is False
        assert user_response.created_by == created_by
        assert user_response.created_at == now
        assert user_response.updated_at == now
