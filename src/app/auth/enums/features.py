from enum import Enum


class Features(str, Enum):
    CATEGORIES = "categories"
    EXPENSES = "expenses"
    PAYMENT_METHODS = "payment_methods"
    TODO_ITEMS = "todo_items"
    ROLES = "roles"
    USERS = "users"
