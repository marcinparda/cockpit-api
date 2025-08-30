# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Development Rules

## Development Commands

### Running the Application

```bash
# Start development environment with auto-reload
docker compose -f docker-compose.dev.yml up

# Run API container for one-off commands
docker compose -f docker-compose.dev.yml run --rm cockpit_api <command>
```

### Database Management

```bash
# Create new migration
docker compose -f docker-compose.dev.yml run --rm cockpit_api alembic revision --autogenerate -m "<migration_message>"

# Apply migrations
docker compose -f docker-compose.dev.yml run --rm cockpit_api alembic upgrade head

# Downgrade migration
docker compose -f docker-compose.dev.yml run --rm cockpit_api alembic downgrade -1
```

### Testing

```bash
# Run all tests (local - faster)
poetry run pytest

# Run all tests (Docker)
docker compose -f docker-compose.dev.yml run --rm cockpit_api pytest

# Run specific test file
poetry run pytest src/tests/test_auth.py

# Run with coverage
poetry run pytest --cov=src
```

### Dependencies

```bash
# Install dependencies after modifying pyproject.toml
poetry install
```

## Architecture Overview

### Database Design

- **Primary Keys**: All models use UUID primary keys with PostgreSQL's `uuid_generate_v4()`
- **Timestamps**: All models inherit from `BaseModel` which provides `created_at` and `updated_at` fields
- **Relationships**: Proper SQLAlchemy relationships with cascade delete where appropriate
- **Async Operations**: Fully async database operations using SQLAlchemy's async engine
- **Use Mapped for models**: SQLAlchemy's `Mapped` generic type for type-safe ORM models

### Core Structure

This FastAPI-based API is organized with a modular, service-oriented architecture, where each service is implemented under `src/services/`. Complex services are further split into modules.

### Services and Modules structure

Each service follows a consistent structure:

- `router.py`: FastAPI route definitions
- `schemas.py`: Pydantic models for request/response validation
- `models.py`: SQLAlchemy models (if applicable)
- `services.py`: Business logic and service layer
- `repository.py`: Data access layer (if services interact with the database)
- `dependencies.py`: Dependency injection for service/module specific dependencies

## Development Guidelines

### Router/Service/Repository Pattern

1. **Router**: Defines the API endpoints and request/response schemas. No business logic here. Add handlers, dependencies if needed.
2. **Service**: Business logic here. Here errors are raised if needed.
3. **Repository**: Using SQLAlchemy interact with the database. Only contains writes/reads to the database no other logic.

### Database Changes

When adding new features:

1. Create the database model in the appropriate service submodule (e.g., `src/services/todos/projects/models.py`)
2. Add the feature to `Features` enum in `src/services/authorization/permissions/enums.py`
3. Create migration: `alembic revision --autogenerate -m "add_new_feature"`
4. Update permissions by adding feature-action pairs to the permissions migration
5. Apply migration: `alembic upgrade head`

### Permission-Protected Endpoints

All business endpoints should use permission checks via the `require_permission` dependency. Example usage:

```python
from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features

@router.get("/protected-expense-endpoint")
async def protected_expense_endpoint(
    current_user: User = Depends(require_permission(Features.EXPENSES, Actions.READ))
):
    # Endpoint logic here
```

### Imports

- When importing a module use absolute imports from the `src` root and import always at the top of the file, not inside functions or classes.
- When importing service/repostitories modules, import whole module, not specific functions/classes from it.
  - Correct: `from src.services.authentication.sessions import service`
  - Incorrect: `from src.services.authentication.sessions.service import login_user`

### Testing Strategy

TODO

### Environment Configuration

Development database connection:

- DB_USER=cockpit_user
- DB_PASSWORD=secure_dev_password
- DB_HOST=cockpit_db
- DB_NAME=cockpit_db
