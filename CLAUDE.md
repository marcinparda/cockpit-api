# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
This is a FastAPI-based personal productivity API with a sophisticated permissions system. The application follows a layered architecture with clear separation of concerns:

- **Models**: SQLAlchemy models with UUID-based primary keys and automatic timestamping via `BaseModel`
- **Schemas**: Pydantic models for request/response validation
- **Services**: Business logic layer handling complex operations
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
Endpoints are organized by feature domains:
- `/api/v1/auth` - Authentication and token management
- `/api/v1/users` - User management (admin-only operations)
- `/api/v1/roles` - Role management
- `/api/v1/todo/projects` - Todo project management
- `/api/v1/todo/items` - Todo item management  
- `/api/v1/expenses` - Expense tracking
- `/api/v1/categories` - Category management
- `/api/v1/payment_methods` - Payment method management
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
When adding new features:
1. Create the database model in `src/models/`
2. Add the feature to `Features` enum in `src/auth/enums/features.py`
3. Create migration: `alembic revision --autogenerate -m "add_new_feature"`
4. Update permissions by adding feature-action pairs to the permissions migration
5. Apply migration: `alembic upgrade head`
6. **Update CLAUDE.md**: After any database schema changes, update the "Database Schema" section in this file to reflect new tables, columns, or relationships

### Permission-Protected Endpoints
All business endpoints should use permission checks:
```python
from src.auth.dependencies import require_permission
from src.auth.enums.features import Features
from src.auth.enums.actions import Actions

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
- `src/models/` - SQLAlchemy database models
- `src/schemas/` - Pydantic request/response schemas
- `src/services/` - Business logic services
- `src/api/v1/endpoints/` - FastAPI route handlers
- `src/auth/` - Authentication, authorization, and permissions
- `src/middleware/` - Custom FastAPI middleware
- `src/tests/` - Test suite
- `alembic/versions/` - Database migration files

The API supports expense tracking and collaborative todo management while maintaining strict access controls and audit trails through the comprehensive permissions system.