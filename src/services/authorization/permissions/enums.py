"""Actions and Features enums for the permission system."""

from enum import Enum


class Actions(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class Features(str, Enum):
    CATEGORIES = "categories"
    EXPENSES = "expenses"
    PAYMENT_METHODS = "payment_methods"
    TODO_ITEMS = "todo_items"
    ROLES = "roles"
    USERS = "users"