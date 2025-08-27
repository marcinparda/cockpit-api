"""User roles enum for role-based access control."""

from enum import Enum


class Roles(Enum):
    """Enum for user roles."""

    ADMIN = "Admin"
    USER = "User"
    TEST_USER = "TestUser"
