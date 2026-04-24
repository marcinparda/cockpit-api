CV_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_company",
            "description": "Search the web for company culture, values, tech stack, and buzzwords to tailor CV language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query, e.g. 'Stripe engineering culture values tech stack'",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cv_base_preset",
            "description": "Read all sections from the user's base CV preset. Always read before tailoring.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_cv_preset",
            "description": (
                "Propose a tailored CV preset based on the job offer. "
                "Pauses for user confirmation before saving. "
                "Include only sections relevant to the role. "
                "Limit experience bullets to 3 most relevant per role. "
                "Drop skills irrelevant to the position."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Preset name, e.g. 'Stripe - Senior Backend 2026-04-22'",
                    },
                    "sections": {
                        "type": "object",
                        "description": "CV sections to include. Omit sections to exclude them.",
                        "properties": {
                            "header": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "title": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "email": {"type": "string"},
                                    "linkedin": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                    },
                                    "location": {"type": "string"},
                                },
                            },
                            "summary": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of summary paragraphs. MUST be an array of strings, never a plain string.",
                            },
                            "skills": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "years": {"type": "number"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["name", "years", "description"],
                                },
                            },
                            "achievements": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["title", "description"],
                                },
                            },
                            "experience": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "company": {"type": "string"},
                                        "details": {"type": "string"},
                                        "date": {"type": "string"},
                                        "location": {"type": "string"},
                                        "description": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Bullet points. MUST be array of strings.",
                                        },
                                    },
                                    "required": ["title", "company", "date", "location", "description"],
                                },
                            },
                            "education": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "degree": {"type": "string"},
                                        "university": {"type": "string"},
                                        "years": {"type": "string"},
                                    },
                                    "required": ["degree", "university", "years"],
                                },
                            },
                            "projects": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "liveUrl": {"type": "string"},
                                        "code": {"type": "string"},
                                        "date": {"type": "string"},
                                        "description": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Bullet points. MUST be array of strings.",
                                        },
                                    },
                                    "required": ["name", "liveUrl", "code", "date", "description"],
                                },
                            },
                            "courses": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of course names. MUST be an array of strings.",
                            },
                        },
                    },
                },
                "required": ["name", "sections"],
            },
        },
    },
]

BUDGET_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "actual_list_accounts",
            "description": "List all Actual Budget accounts. Call first to get account IDs needed for transaction operations.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_create_account",
            "description": "Create a new budget account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Account name"},
                    "offbudget": {
                        "type": "boolean",
                        "description": "True = off-budget tracking account, false = regular budget account",
                    },
                },
                "required": ["name", "offbudget"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_list_categories",
            "description": "List all budget categories and groups. Call to get category IDs for transactions.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_list_payees",
            "description": "List all payees (merchants/vendors). Check before creating transactions to reuse existing IDs.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_search_transactions",
            "description": "Search transactions in an account within a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Account ID from actual_list_accounts"},
                    "since_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "until_date": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
                },
                "required": ["account_id", "since_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_create_transaction",
            "description": (
                "Create a single transaction. "
                "Amount in milliunits: 1000 = $1.00, negative = expense (-10500 = -$10.50), positive = income."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Account ID"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "amount": {"type": "integer", "description": "Milliunits. Negative = expense, positive = income."},
                    "payee_name": {"type": "string", "description": "Merchant name (creates payee if new)"},
                    "category_id": {"type": "string", "description": "Category ID (optional)"},
                    "notes": {"type": "string", "description": "Optional notes"},
                    "cleared": {"type": "boolean", "description": "Cleared status (default false)"},
                },
                "required": ["account_id", "date", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_batch_create_transactions",
            "description": (
                "Create multiple transactions at once. Use for bank statement imports. "
                "Amount in milliunits, negative = expense. learn_categories=true lets Actual learn from payee patterns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Account ID for all transactions"},
                    "transactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "description": "YYYY-MM-DD"},
                                "amount": {"type": "integer", "description": "Milliunits, negative=expense"},
                                "payee_name": {"type": "string"},
                                "category_id": {"type": "string", "description": "Optional"},
                                "notes": {"type": "string", "description": "Optional"},
                            },
                            "required": ["date", "amount"],
                        },
                    },
                    "learn_categories": {"type": "boolean", "description": "Default true"},
                },
                "required": ["account_id", "transactions"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_update_transaction",
            "description": "Update a transaction (assign category, fix payee, update notes, mark cleared).",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "category_id": {"type": "string", "description": "New category ID"},
                    "payee_name": {"type": "string"},
                    "notes": {"type": "string"},
                    "cleared": {"type": "boolean"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "amount": {"type": "integer", "description": "Milliunits"},
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actual_delete_transaction",
            "description": "Delete a transaction by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                },
                "required": ["transaction_id"],
            },
        },
    },
]

TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "vikunja_list_projects",
            "description": "List all Vikunja projects. Call to get project IDs for task operations.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_get_tasks",
            "description": (
                "Get tasks with optional filters. Filter syntax: field comparator value, joined with &&. "
                "Examples: 'due_date<=2026-04-24&&done=false' (overdue open tasks), "
                "'done=false' (all open). Sort by due_date asc for chronological order."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "Filter by project (omit = all projects)"},
                    "filter": {"type": "string", "description": "Filter expression, e.g. 'due_date<=2026-04-30&&done=false'"},
                    "s": {"type": "string", "description": "Full-text search"},
                    "sort_by": {"type": "string", "description": "'due_date', 'created', 'priority', 'title'"},
                    "order_by": {"type": "string", "description": "'asc' or 'desc'"},
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer", "description": "Max 500"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_create_task",
            "description": "Create a new task. Use vikunja_list_projects for project_id, vikunja_list_users for assignee IDs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string", "description": "Optional"},
                    "due_date": {"type": "string", "description": "ISO 8601, e.g. '2026-04-30T00:00:00Z'"},
                    "priority": {"type": "integer", "description": "0=none, 1=low, 2=medium, 3=high, 4=urgent, 5=critical"},
                    "assignees": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "User IDs from vikunja_list_users",
                    },
                },
                "required": ["project_id", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_update_task",
            "description": "Update a task (mark done, change due date, title, description, priority).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "done": {"type": "boolean"},
                    "due_date": {"type": "string", "description": "ISO 8601"},
                    "priority": {"type": "integer", "description": "0-5"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_delete_task",
            "description": "Permanently delete a task.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_list_users",
            "description": "Search users by name/username/email to find IDs for assignment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "s": {"type": "string", "description": "Search query. Omit to list all."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_assign_user_to_task",
            "description": "Assign a user to a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                },
                "required": ["task_id", "user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vikunja_remove_assignee",
            "description": "Remove a user assignment from a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                },
                "required": ["task_id", "user_id"],
            },
        },
    },
]

TOOLS = CV_TOOLS + BUDGET_TOOLS + TASK_TOOLS

CV_SECTIONS = ["header", "summary", "skills", "achievements", "experience", "education", "projects", "courses"]

TOOL_STATUS_MESSAGES: dict[str, str] = {
    "search_company": "Searching the web for company info...",
    "get_cv_base_preset": "Reading your base CV...",
    "create_cv_preset": "Preparing CV preset preview...",
    "actual_list_accounts": "Fetching accounts...",
    "actual_create_account": "Creating account...",
    "actual_list_categories": "Fetching categories...",
    "actual_list_payees": "Fetching payees...",
    "actual_search_transactions": "Searching transactions...",
    "actual_create_transaction": "Creating transaction...",
    "actual_batch_create_transactions": "Importing transactions...",
    "actual_update_transaction": "Updating transaction...",
    "actual_delete_transaction": "Deleting transaction...",
    "vikunja_list_projects": "Fetching projects...",
    "vikunja_get_tasks": "Fetching tasks...",
    "vikunja_create_task": "Creating task...",
    "vikunja_update_task": "Updating task...",
    "vikunja_delete_task": "Deleting task...",
    "vikunja_list_users": "Fetching users...",
    "vikunja_assign_user_to_task": "Assigning user to task...",
    "vikunja_remove_assignee": "Removing assignee...",
}
