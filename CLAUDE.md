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

This is a FastAPI-based personal productivity API with a sophisticated permissions system. The application is transitioning to a **Domain-Driven Design (DDD)** approach with modules defined at the app folder level, following a layered architecture with clear separation of concerns:

- **Domain Modules**: Each business domain (auth, todos, budget, users) is organized as a self-contained module in `src/app/`
- **Models**: SQLAlchemy models with UUID-based primary keys and automatic timestamping via `BaseModel`
- **Schemas**: Pydantic models for request/response validation within each domain
- **Services**: Business logic layer handling complex operations per domain
- **API Endpoints**: FastAPI routers organized by feature domain
- **Auth System**: Role-based permissions with feature-action granularity

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
2. Add the feature to `Features` enum in `src/app/auth/enums/features.py`
3. Create migration: `alembic revision --autogenerate -m "add_new_feature"`
4. Update permissions by adding feature-action pairs to the permissions migration
5. Apply migration: `alembic upgrade head`
6. **Update CLAUDE.md**: After any database schema changes, update the "Database Schema" section in this file to reflect new tables, columns, or relationships

### Permission-Protected Endpoints

All business endpoints should use permission checks:

```python
from src.app.auth.dependencies import require_permission
from src.app.auth.enums.features import Features
from src.app.auth.enums.actions import Actions

@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(require_permission(Features.TODO, Actions.READ))
):
    # Endpoint logic here
```

### Model Conventions

- All models inherit from `BaseModel` for automatic timestamps
- Use UUID primary keys with `server_default='uuid_generate_v4()'`
- Include proper `__tablename__` and `__repr__` methods
- Define relationships with appropriate cascade settings

### Testing Strategy

- Unit tests for business logic and schema validation
- Integration tests for API endpoints using test database
- Permission tests to verify RBAC implementation
- Use pytest fixtures for database setup and cleanup

### Environment Configuration

Development database connection:

- DB_USER=cockpit_user
- DB_PASSWORD=secure_dev_password
- DB_HOST=cockpit_db
- DB_NAME=cockpit_db

### File Organization

#### Project Structure (DDD Approach)

```
src/
├── main.py                          # FastAPI application entry point
├── core/                            # Core infrastructure
│   ├── config.py                    # Application configuration
│   ├── database.py                  # Database connection and session management
│   └── scheduler.py                 # Background task scheduler
├── common/                          # Shared utilities
│   ├── dependencies.py              # Common FastAPI dependencies
│   ├── exceptions.py                # Custom exception classes
│   ├── utils.py                     # Utility functions
│   └── middleware/                  # Custom middleware
│       ├── jwt_validation.py        # JWT validation middleware
│       └── rate_limit.py            # Rate limiting middleware
├── models/                          # Global SQLAlchemy models (legacy - being phased out)
├── schemas/                         # Global Pydantic schemas (legacy - being phased out)
├── tasks/                           # Background tasks
│   └── token_cleanup.py             # Token cleanup scheduler
├── app/                             # Domain modules (DDD approach)
│   ├── auth/                        # Authentication domain
│   │   ├── dependencies.py          # Auth-specific dependencies
│   │   ├── jwt.py                   # JWT token handling
│   │   ├── jwt_dependencies.py      # JWT FastAPI dependencies
│   │   ├── models.py                # Authentication database models
│   │   ├── password.py              # Password hashing utilities
│   │   ├── permissions.py           # Permission management
│   │   ├── permission_helpers.py    # Permission utility functions
│   │   ├── router.py                # Authentication API endpoints
│   │   ├── schemas.py               # Authentication Pydantic schemas
│   │   ├── service.py               # Authentication business logic
│   │   ├── token_service.py         # Token management service
│   │   └── enums/                   # Auth-related enums
│   │       ├── actions.py           # Permission actions
│   │       ├── features.py          # Feature definitions
│   │       └── roles.py             # User roles
│   ├── users/                       # User management domain
│   │   ├── router.py                # User API endpoints
│   │   ├── schemas.py               # User Pydantic schemas
│   │   ├── service.py               # User business logic
│   │   └── core/                    # User core components
│   ├── todos/                       # Todo management domain
│   │   ├── domain/                  # Domain services for cross-aggregate business rules
│   │   │   ├── __init__.py          # Domain services module
│   │   │   └── access_control_service.py # Access control domain service
│   │   ├── router.py                # Main todo router
│   │   ├── projects/                # Todo projects subdomain
│   │   │   ├── models.py            # Project database models
│   │   │   ├── repository.py        # Project data access layer
│   │   │   ├── router.py            # Project API endpoints
│   │   │   ├── schemas.py           # Project Pydantic schemas
│   │   │   └── service.py           # Project business logic (includes ownership/general checks)
│   │   ├── items/                   # Todo items subdomain
│   │   │   ├── models.py            # Item database models
│   │   │   ├── repository.py        # Item data access layer
│   │   │   ├── router.py            # Item API endpoints
│   │   │   ├── schemas.py           # Item Pydantic schemas
│   │   │   ├── dependencies.py      # Item access control dependencies
│   │   │   └── service.py           # Item business logic
│   │   └── collaborators/           # Project collaboration subdomain
│   │       ├── models.py            # Collaborator database models
│   │       ├── repository.py        # Collaborator data access layer
│   │       ├── router.py            # Collaborator API endpoints
│   │       ├── schemas.py           # Collaborator Pydantic schemas
│   │       └── service.py           # Collaborator business logic
│   └── budget/                      # Budget management domain
│       ├── router.py                # Main budget router
│       ├── expenses/                # Expense tracking subdomain
│       │   ├── router.py            # Expense API endpoints
│       │   ├── schemas.py           # Expense Pydantic schemas
│       │   └── service.py           # Expense business logic
│       ├── categories/              # Category management subdomain
│       │   ├── router.py            # Category API endpoints
│       │   ├── schemas.py           # Category Pydantic schemas
│       │   └── service.py           # Category business logic
│       └── payment_methods/         # Payment method subdomain
│           ├── router.py            # Payment method API endpoints
│           ├── schemas.py           # Payment method Pydantic schemas
│           └── service.py           # Payment method business logic
├── api/                             # API layer
│   └── v1/                          # API version 1
│       ├── deps.py                  # API dependencies
│       └── endpoints/               # API endpoints (legacy structure)
│           ├── auth.py              # Auth endpoints
│           ├── health.py            # Health check endpoints
│           └── roles.py             # Role management endpoints
├── tests/                           # Test suite
└── alembic/                         # Database migrations
    └── versions/                    # Migration files
```

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

4. **Legacy Migration**: The project has transitioned from a layered architecture to DDD:

   - Global `models/` and `schemas/` directories contain remaining legacy code
   - The `src/services/` directory has been completely removed, with all services moved to their respective domains
   - New development follows the domain module pattern in `src/app/`
   - Authentication remains centralized due to its cross-cutting nature

5. **Separation of Concerns**:
   - **Core**: Infrastructure and configuration
   - **Common**: Shared utilities and middleware
   - **App**: Business domains with clear boundaries
   - **Domain**: Cross-aggregate business rules within bounded contexts
   - **API**: External interface layer
   - **Tasks**: Background processing

The API supports expense tracking and collaborative todo management while maintaining strict access controls and audit trails through the comprehensive permissions system.
