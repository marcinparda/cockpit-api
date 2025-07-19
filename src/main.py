from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from typing import List

from src.api.v1.endpoints import expenses, categories, payment_methods, todo_items, todo_projects, shared, auth, users, roles
from src.core.config import settings
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.jwt_validation import JWTValidationMiddleware
from src.services.cleanup_service import TokenCleanupService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    cleanup_service = TokenCleanupService()
    cleanup_task = None

    if settings.ENABLE_TOKEN_TRACKING:
        # Start the token cleanup task
        cleanup_task = asyncio.create_task(
            cleanup_service.start_periodic_cleanup())

    yield

    # Shutdown
    if cleanup_task and not cleanup_task.done():
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Cockpit API",
    version="0.1.0",
    docs_url="/api/docs",
    lifespan=lifespan
)

origins: List[str] = [str(origin) for origin in settings.CORS_ORIGINS] if isinstance(
    settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add JWT validation middleware
app.add_middleware(JWTValidationMiddleware)

app.include_router(
    expenses.router, prefix="/api/v1/expenses", tags=["ai-budget/expenses"])
app.include_router(categories.router,
                   prefix="/api/v1/categories", tags=["ai-budget/categories"])
app.include_router(
    payment_methods.router, prefix="/api/v1/payment_methods", tags=["ai-budget/payment_methods"])
app.include_router(
    todo_items.router, prefix="/api/v1/todo/items", tags=["todo/todo_items"])
app.include_router(
    todo_projects.router, prefix="/api/v1/todo/projects", tags=["todo/todo_projects"])
app.include_router(
    shared.router, prefix="/api/v1/shared", tags=["shared"])
app.include_router(
    auth.router, prefix="/api/v1/auth", tags=["shared/auth"])
app.include_router(
    users.router, prefix="/api/v1/users", tags=["shared/admin"])
app.include_router(
    roles.router, prefix="/api/v1/roles", tags=["shared/admin"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
