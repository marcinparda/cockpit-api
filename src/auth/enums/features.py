from enum import Enum


class Features(str, Enum):
    API_KEYS = "api_keys"
    CATEGORIES = "categories"
    EXPENSES = "expenses"
    PAYMENT_METHODS = "payment_methods"
    SHOPPING_ITEMS = "shopping_items"
