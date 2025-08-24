from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import List

from src.app.health.router import router as health_router
from src.app.auth.router import router as auth_router
from src.app.todos.router import router as todos_router
from src.app.users.router import router as users_router
from src.app.budget.router import router as budget_router
from src.core.config import settings
from src.common.middleware.rate_limit import RateLimitMiddleware
from src.common.middleware.jwt_validation import JWTValidationMiddleware
from src.core.scheduler import task_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up FastAPI application")
    try:
        await task_scheduler.start()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application")
    try:
        await task_scheduler.stop()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(
            f"Error during application shutdown: {str(e)}", exc_info=True)


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
    budget_router, prefix="/api/v1/budget", tags=["budget"])
app.include_router(
    todos_router, prefix="/api/v1/todos", tags=["todos"])
app.include_router(
    users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(
    auth_router, prefix="/api/v1/auth", tags=["shared/auth"])
app.include_router(
    health_router, prefix="/health", tags=["health"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
