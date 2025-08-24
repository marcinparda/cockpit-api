# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Development Rules

### Git and Commit Policy
**ALWAYS ASK BEFORE COMMITTING**: Before running `git commit`, ask the user for permission first. The user will review changes in their IDE. Never commit without explicit user approval.

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

## Database Schema

The PostgreSQL database consists of 15 main tables organized into logical domains:

### Authentication & Authorization Tables

#### `users`
Primary user table with role-based access control:
- `id` (UUID, PK) - Unique user identifier
- `email` (VARCHAR, UNIQUE) - User login email
- `password_hash` (VARCHAR) - Bcrypt hashed password
- `is_active` (BOOLEAN, DEFAULT true) - Account status
- `role_id` (UUID, FK -> user_roles.id) - User's role
- `password_changed` (BOOLEAN, DEFAULT false) - Password change flag
- `created_by` (UUID, FK -> users.id, NULL) - User who created this account
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `user_roles`
Role definitions for RBAC system:
- `id` (UUID, PK) - Role identifier  
- `name` (VARCHAR, UNIQUE) - Role name (e.g., 'ADMIN', 'USER')
- `description` (VARCHAR, NULL) - Role description
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `features`
Available system features for permission control:
- `id` (UUID, PK) - Feature identifier
- `name` (VARCHAR, UNIQUE) - Feature name (e.g., 'TODO', 'EXPENSES')
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `actions`
Available actions for permission control:
- `id` (UUID, PK) - Action identifier
- `name` (VARCHAR, UNIQUE) - Action name (e.g., 'READ', 'CREATE', 'DELETE')
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `permissions`
Feature-Action permission combinations:
- `id` (UUID, PK) - Permission identifier
- `feature_id` (UUID, FK -> features.id) - Related feature
- `action_id` (UUID, FK -> actions.id) - Related action
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `user_permissions`
User-specific permission assignments:
- `id` (UUID, PK) - Assignment identifier
- `user_id` (UUID, FK -> users.id) - User receiving permission
- `permission_id` (UUID, FK -> permissions.id) - Granted permission
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps
- UNIQUE constraint on (user_id, permission_id)

### Token Management Tables

#### `access_tokens`
JWT access token tracking:
- `id` (UUID, PK) - Token identifier
- `jti` (VARCHAR) - JWT ID claim
- `user_id` (UUID, FK -> users.id) - Token owner
- `expires_at` (TIMESTAMP) - Token expiration
- `is_revoked` (BOOLEAN) - Revocation status
- `last_used_at` (TIMESTAMP, NULL) - Last usage tracking
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `refresh_tokens`
JWT refresh token tracking:
- `id` (UUID, PK) - Token identifier
- `jti` (VARCHAR) - JWT ID claim
- `user_id` (UUID, FK -> users.id) - Token owner
- `expires_at` (TIMESTAMP) - Token expiration
- `is_revoked` (BOOLEAN) - Revocation status
- `last_used_at` (TIMESTAMP, NULL) - Last usage tracking
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

### Todo Management Tables

#### `todo_projects`
Project containers for todo items:
- `id` (INTEGER, PK, SERIAL) - Project identifier
- `name` (VARCHAR) - Project name
- `owner_id` (UUID, FK -> users.id) - Project owner
- `is_general` (BOOLEAN, DEFAULT false) - General project flag
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `todo_items`
Individual todo tasks:
- `id` (INTEGER, PK, SERIAL) - Item identifier
- `name` (VARCHAR) - Task name
- `description` (TEXT, NULL) - Detailed description
- `is_closed` (BOOLEAN, NULL) - Completion status
- `completed_at` (TIMESTAMP WITH TIME ZONE, NULL) - Completion time
- `shops` (VARCHAR, NULL) - Shopping-related data
- `project_id` (INTEGER, FK -> todo_projects.id) - Parent project
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `todo_project_collaborators`
Project collaboration permissions:
- `project_id` (INTEGER, FK -> todo_projects.id, PK) - Project reference
- `user_id` (UUID, FK -> users.id, PK) - Collaborator user
- `created_at`, `updated_at` (TIMESTAMP, DEFAULT now()) - Audit timestamps
- Composite primary key on (project_id, user_id)

### Expense Tracking Tables

#### `categories`
Hierarchical expense categories:
- `id` (INTEGER, PK, SERIAL) - Category identifier
- `name` (VARCHAR) - Category name
- `parent_id` (INTEGER, FK -> categories.id, NULL) - Parent category (self-reference)
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `payment_methods`
Available payment methods:
- `id` (INTEGER, PK, SERIAL) - Payment method identifier
- `name` (VARCHAR, UNIQUE) - Method name
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

#### `expenses`
Individual expense records:
- `id` (INTEGER, PK, SERIAL) - Expense identifier
- `amount` (NUMERIC) - Expense amount
- `date` (DATE) - Expense date
- `description` (VARCHAR, NULL) - Expense description
- `category_id` (INTEGER, FK -> categories.id) - Expense category
- `payment_method_id` (INTEGER, FK -> payment_methods.id) - Payment method used
- `created_at`, `updated_at` (TIMESTAMP) - Audit timestamps

### Database Relationships Summary

**User Management:**
- users.role_id -> user_roles.id
- users.created_by -> users.id (self-reference)
- user_permissions.user_id -> users.id
- user_permissions.permission_id -> permissions.id

**Permission System:**
- permissions.feature_id -> features.id  
- permissions.action_id -> actions.id

**Token Management:**
- access_tokens.user_id -> users.id
- refresh_tokens.user_id -> users.id

**Todo System:**
- todo_projects.owner_id -> users.id
- todo_items.project_id -> todo_projects.id
- todo_project_collaborators.project_id -> todo_projects.id
- todo_project_collaborators.user_id -> users.id

**Expense System:**
- categories.parent_id -> categories.id (self-reference)
- expenses.category_id -> categories.id
- expenses.payment_method_id -> payment_methods.id

### Key Design Patterns

1. **UUID Primary Keys**: Core entities (users, roles, permissions, tokens) use UUIDs
2. **Serial Integer Keys**: Domain entities (todos, expenses, categories) use auto-incrementing integers
3. **Audit Timestamps**: All tables have created_at/updated_at for change tracking
4. **Soft Relationships**: Foreign keys maintain referential integrity
5. **Hierarchical Data**: Categories support parent-child relationships
6. **Many-to-Many**: User permissions and project collaborators use junction tables
7. **Self-References**: Users can create other users; categories can have parent categories

### API Organization
Endpoints are organized by feature domains using DDD modules:
- `/api/v1/auth` - Authentication and token management
- `/api/v1/users` - User management (admin-only operations)
- `/api/v1/roles` - Role management
- `/api/v1/todo/projects` - Todo project management
- `/api/v1/todo/items` - Todo item management  
- `/api/v1/todo/collaborators` - Todo project collaboration management
- `/api/v1/budget/expenses` - Expense tracking
- `/api/v1/budget/categories` - Category management
- `/api/v1/budget/payment_methods` - Payment method management
- `/health` - Health check endpoints

### Authentication Flow
1. **Login**: POST to `/api/v1/auth/login` with credentials
2. **Token Generation**: JWT access and refresh tokens are created
3. **Token Storage**: Tokens stored in database with expiration tracking
4. **Request Authentication**: JWT middleware validates tokens on protected routes
5. **Permission Checking**: Each endpoint validates user permissions for the required feature-action combination

### Key Services
- **AuthService**: Handles login, token generation, and user authentication
- **UserService**: User management operations including password changes
- **TokenService**: JWT token creation, validation, and cleanup
- **TodoAccessService**: Manages todo project access permissions and collaboration

## Development Guidelines

### Database Changes
When adding new features following the DDD approach:
1. Create the database model in the appropriate domain module (e.g., `src/app/todos/projects/models.py`)
2. Add the feature to `Features` enum in `src/app/auth/enums/features.py`
3. Create migration: `alembic revision --autogenerate -m "add_new_feature"`
4. Update permissions by adding feature-action pairs to the permissions migration
5. Apply migration: `alembic upgrade head`
6. **Update CLAUDE.md**: After any database schema changes, update the "Database Schema" section in this file to reflect new tables, columns, or relationships

**Note**: For legacy models still in `src/models/`, follow the existing pattern, but prefer creating new models within domain modules.

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
├── services/                        # Global services (legacy - being phased out)
├── tasks/                           # Background tasks
│   └── token_cleanup.py             # Token cleanup scheduler
├── app/                             # Domain modules (DDD approach)
│   ├── auth/                        # Authentication domain
│   │   ├── dependencies.py          # Auth-specific dependencies
│   │   ├── jwt.py                   # JWT token handling
│   │   ├── jwt_dependencies.py      # JWT FastAPI dependencies
│   │   ├── password.py              # Password hashing utilities
│   │   ├── permissions.py           # Permission management
│   │   ├── permission_helpers.py    # Permission utility functions
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
│   │   ├── router.py                # Main todo router
│   │   ├── projects/                # Todo projects subdomain
│   │   │   ├── models.py            # Project database models
│   │   │   ├── repository.py        # Project data access layer
│   │   │   ├── router.py            # Project API endpoints
│   │   │   ├── schemas.py           # Project Pydantic schemas
│   │   │   └── service.py           # Project business logic
│   │   ├── items/                   # Todo items subdomain
│   │   │   ├── models.py            # Item database models
│   │   │   ├── repository.py        # Item data access layer
│   │   │   ├── router.py            # Item API endpoints
│   │   │   ├── schemas.py           # Item Pydantic schemas
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

3. **Legacy Migration**: The project is transitioning from a layered architecture to DDD:
   - Global `models/`, `schemas/`, and `services/` directories contain legacy code
   - New development follows the domain module pattern in `src/app/`
   - Authentication remains centralized due to its cross-cutting nature

4. **Separation of Concerns**:
   - **Core**: Infrastructure and configuration
   - **Common**: Shared utilities and middleware
   - **App**: Business domains with clear boundaries
   - **API**: External interface layer
   - **Tasks**: Background processing

The API supports expense tracking and collaborative todo management while maintaining strict access controls and audit trails through the comprehensive permissions system.