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

### Core Structure

This is a FastAPI-based personal productivity API featuring a robust permissions system. The project is structured with a modular, service-oriented architecture:

- **Service Modules**: Each business area (authentication, authorization, todos, budget, users, health) is implemented as an independent service module under `src/services/`
- **Submodule Organization**: Complex services are further organized into submodules (e.g., `todos` has `projects`, `items`, `collaborators`; `authorization` has `permissions`, `roles`, `user_permissions`)
- **Repositories**: Services that need data access include a `repository.py` file that encapsulates all database operations using SQLAlchemy's async engine
- **Models**: SQLAlchemy models use UUID-based primary keys and automatic timestamping via `BaseModel` from `src/common/models.py`
- **Schemas**: Pydantic models are used for request/response validation within each service
- **Services**: Each submodule contains its own business logic in `service.py`
- **API Endpoints**: FastAPI routers are organized by service and submodule, with a main router per service
- **Auth System**: Role-based permissions with feature-action granularity using dependency injection

### Permission System

The application uses a sophisticated role-based access control (RBAC) system:

- **Features**: Logical groupings of functionality (e.g., `CATEGORIES`, `EXPENSES`, `TODO_ITEMS`, `PAYMENT_METHODS`, `ROLES`, `USERS`)
- **Actions**: Operations that can be performed (`CREATE`, `READ`, `UPDATE`, `DELETE`)
- **Permissions**: Feature-Action pairs that define specific capabilities
- **User Roles**: Users have roles (ADMIN, USER) that determine base permissions
- **User Permissions**: Additional granular permissions can be assigned to individual users

Admin users automatically have all permissions. Regular users must have explicit permissions assigned.

### Database Design

- **Primary Keys**: All models use UUID primary keys with PostgreSQL's `uuid_generate_v4()`
- **Timestamps**: All models inherit from `BaseModel` which provides `created_at` and `updated_at` fields
- **Relationships**: Proper SQLAlchemy relationships with cascade delete where appropriate
- **Async Operations**: Fully async database operations using SQLAlchemy's async engine
- **Use Mapped for models**: SQLAlchemy's `Mapped` generic type for type-safe ORM models

## Development Guidelines

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

### Testing Strategy

TODO

### Environment Configuration

Development database connection:

- DB_USER=cockpit_user
- DB_PASSWORD=secure_dev_password
- DB_HOST=cockpit_db
- DB_NAME=cockpit_db

#### Key Architectural Decisions

1. **Service Module Structure**: Each service in `src/services/` follows a consistent pattern:

   - `router.py` - FastAPI endpoint definitions
   - `schemas.py` - Pydantic models for request/response validation
   - `service.py` - Business logic implementation
   - `models.py` - SQLAlchemy database models (where applicable)
   - `repository.py` - Data access layer (where applicable)

2. **Submodule Organization**: Complex services like `todos`, `budget`, and `authorization` are organized into submodules:

   - `todos`: `projects`, `items`, `collaborators`
   - `budget`: `categories`, `expenses`, `payment_methods`
   - `authorization`: `permissions`, `roles`, `user_permissions`
   - `authentication`: `passwords`, `sessions`, `tokens`

3. **Permission System**: Access control is handled through:
   - Feature-based permissions defined in `src/services/authorization/permissions/enums.py`
   - Role-based access with admin users having full permissions
   - Dependency injection pattern for endpoint protection
