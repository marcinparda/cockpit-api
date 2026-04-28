"""Actions and Features enums for the permission system."""

from enum import Enum


class Actions(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class Features(str, Enum):
    ROLES = "roles"
    USERS = "users"
    REDIS_STORE = "redis_store"
    BRAIN = "brain"
    VIKUNJA = "vikunja"
    ACTUAL_BUDGET = "actual_budget"