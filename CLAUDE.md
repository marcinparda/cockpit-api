# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in cockpit-api repository.

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

## Upstream API Documentation

Upstream API specs are in `docs/`:

- `docs/actual-budget.openapi.json` — Actual HTTP API full OpenAPI 3.1.0 spec (fetched from live raspberry instance)
- `docs/vikunja.openapi.json` — Vikunja full Swagger 2.0 spec (fetched from GitHub main)
- `docs/UPSTREAM_APIS.md` — quick endpoint index for both APIs

When proxying a new endpoint: check `docs/UPSTREAM_APIS.md` for the endpoint, then read the OpenAPI JSON for exact request/response schemas.

To refresh specs when upstream updates:
```bash
./docs/update-upstream-docs.sh
```

## Architecture Overview

### Database Design

- **Primary Keys**: All models use UUID primary keys with PostgreSQL's `uuid_generate_v4()`
- **Timestamps**: All models inherit from `BaseModel` which provides `created_at` and `updated_at` fields
- **Relationships**: Proper SQLAlchemy relationships with cascade delete where appropriate
- **Async Operations**: Fully async database operations using SQLAlchemy's async engine
- **Use Mapped for models**: SQLAlchemy's `Mapped` generic type for type-safe ORM models

### Database Changes

When adding new features:

1. Create the database model in the appropriate service submodule (e.g., `src/services/agent/models.py`)
2. Add the feature to `Features` enum in `src/services/authorization/permissions/enums.py`
3. Create migration: `alembic revision --autogenerate -m "add_new_feature"`
4. Update permissions by adding feature-action pairs to the permissions migration
5. Apply migration: `alembic upgrade head`

### Permission-Protected Endpoints

All business endpoints should use permission checks via the `require_permission` dependency. Example usage:

```python
from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features

@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(require_permission(Features.AGENT, Actions.READ))
):
    # Endpoint logic here
```

### Imports

- When importing service/repostitories modules
  - Correct: `from src.services.authentication.sessions import service`
  - Incorrect: `from src.services.authentication.sessions.service import login_user`
