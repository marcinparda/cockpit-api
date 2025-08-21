from enum import Enum


class Features(str, Enum):
    API_KEYS = "api_keys"
    CATEGORIES = "categories"
    EXPENSES = "expenses"
    PAYMENT_METHODS = "payment_methods"
    TODO_ITEMS = "todo_items"
    SHARED = "shared"
    ROLES = "roles"
    USERS = "users"
