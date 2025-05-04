from enum import Enum


class Resources(str, Enum):
    API_KEYS = "api_keys"
    CATEGORIES = "categories"
    EXPENSES = "expenses"
    PAYMENT_METHODS = "payment_methods"


class Actions(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class PermissionPresets:
    ADMIN = {
        Resources.API_KEYS: [Actions.CREATE, Actions.READ, Actions.UPDATE, Actions.DELETE],
        Resources.CATEGORIES: [Actions.CREATE, Actions.READ, Actions.UPDATE, Actions.DELETE],
        Resources.EXPENSES: [Actions.CREATE, Actions.READ, Actions.UPDATE, Actions.DELETE],
        Resources.PAYMENT_METHODS: [Actions.CREATE,
                                    Actions.READ, Actions.UPDATE, Actions.DELETE]
    }

    READ_ONLY = {
        Resources.API_KEYS: [Actions.READ],
        Resources.CATEGORIES: [Actions.READ],
        Resources.EXPENSES: [Actions.READ],
        Resources.PAYMENT_METHODS: [Actions.READ]
    }
