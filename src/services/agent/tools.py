TOOLS = [
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
            "description": "Read all sections from the user's base CV preset. This is the source of truth — always read before tailoring.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_cv_preset",
            "description": (
                "Propose a tailored CV preset based on the job offer. "
                "This will pause and ask the user to confirm before saving. "
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
                        "description": (
                            "CV sections to include. Keys: header, summary, skills, achievements, "
                            "experience, education, projects, courses. Omit sections to exclude them."
                        ),
                    },
                },
                "required": ["name", "sections"],
            },
        },
    },
]

CV_SECTIONS = ["header", "summary", "skills", "achievements", "experience", "education", "projects", "courses"]

TOOL_STATUS_MESSAGES: dict[str, str] = {
    "search_company": "Searching the web for company info...",
    "get_cv_base_preset": "Reading your base CV...",
    "create_cv_preset": "Preparing CV preset preview...",
}
