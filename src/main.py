from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List

from src.services.health.router import router as health_router
from src.services.authentication.router import router as authentication_router
from src.services.authorization.router import router as authorization_router
from src.services.users.router import router as users_router
from src.services.redis_store.router import router as redis_store_router
from src.services.agent.router import router as agent_router
from src.services.vikunja.router import router as vikunja_router
from src.services.actual_budget.router import router as actual_budget_router
from src.services.brain.router import router as brain_router
from src.services.brain import search as brain_search
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
        await brain_search.init_index(settings.BRAIN_NOTES_PATH)
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
    users_router, prefix="/api/v1/users")
app.include_router(
    authentication_router, prefix="/api/v1/authentication")
app.include_router(
    authorization_router, prefix="/api/v1/authorization")
app.include_router(
    redis_store_router, prefix="/api/v1/store")
app.include_router(
    agent_router, prefix="/api/v1/agent")
app.include_router(
    vikunja_router, prefix="/api/v1/vikunja")
app.include_router(
    actual_budget_router, prefix="/api/v1/actual")
app.include_router(
    brain_router, prefix="/api/v1/brain")
app.include_router(
    health_router, prefix="/health", tags=["health"])


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Cockpit API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
