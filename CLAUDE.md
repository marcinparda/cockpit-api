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
- `/api/v1/shared` - Shared utilities (OCR, file upload)
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

The API supports intelligent OCR processing, expense tracking, and collaborative todo management while maintaining strict access controls and audit trails through the comprehensive permissions system.