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

This is a FastAPI-based personal productivity API featuring a robust permissions system. The project is structured with a modular, service-oriented architecture inspired by microservices principles:

- **Service Modules**: Each business area (auth, todos, budget, users) is implemented as an independent service module under `src/services/`. Services are designed to operate independently and can interact with each other when necessary.
- **Repositories**: Each service module includes a `repository.py` file that encapsulates all data access logic, providing a clear separation between business logic and database operations. Repositories use SQLAlchemy for async database interactions and are responsible for CRUD operations on domain models.
- **Models**: SQLAlchemy models use UUID-based primary keys and automatic timestamping via `BaseModel`.
- **Schemas**: Pydantic models are used for request/response validation within each service.
- **Services**: Each module contains its own business logic, aiming for separation and independence.
- **API Endpoints**: FastAPI routers are organized by service domain.
- **Auth System**: Role-based permissions with feature-action granularity.
- **Service Communication**: While services are currently separated at the folder structure level, further transition to true microservices is planned. Inter-service calls are possible but minimized to maintain independence.

### Permission System

The application uses a sophisticated role-based access control (RBAC) system:

- **Features**: Logical groupings of functionality (e.g., `TODO`, `EXPENSES`)
- **Actions**: Operations that can be performed (e.g., `READ`, `CREATE`, `DELETE`)
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

When adding new features following the DDD approach:

1. Create the database model in the appropriate domain module (e.g., `src/app/todos/projects/models.py`)
2. Add the feature to `Features` enum in `src.app.authorization.permissions.enums`
3. Create migration: `alembic revision --autogenerate -m "add_new_feature"`
4. Update permissions by adding feature-action pairs to the permissions migration
5. Apply migration: `alembic upgrade head`
6. **Update CLAUDE.md**: After any database schema changes, update the "Database Schema" section in this file to reflect new tables, columns, or relationships

### Permission-Protected Endpoints

All business endpoints should use permission checks from `feature_permission_service.py`. Example usage:

```python
from src.app.authorization.domain.feature_permission_service import get_expenses_permissions
from src.app.authorization.permissions.enums import Actions

@router.get("/protected-expense-endpoint")
async def protected_expense_endpoint(
    _: None = Depends(get_expenses_permissions(Actions.READ))
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

1. **Domain Module Structure**: Each domain in `src/app/` follows a consistent pattern:

   - `router.py` - FastAPI endpoint definitions
   - `schemas.py` - Pydantic models for request/response validation
   - `service.py` - Business logic implementation
   - `models.py` - SQLAlchemy database models (domain-specific)
   - `repository.py` - Data access layer (where applicable)

2. **Subdomain Organization**: Complex domains like `todos` and `budget` are further organized into subdomains (projects, items, collaborators, expenses, etc.)

3. **Domain Services**: Cross-aggregate business rules are handled by domain services within each bounded context:

   - Todo domain uses `domain/access_control_service.py` for access control spanning projects, collaborators, and items
   - Single-aggregate business rules remain in their respective subdomain services
   - This follows DDD principles while maintaining clear boundaries
