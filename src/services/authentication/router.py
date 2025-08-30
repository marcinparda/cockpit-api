"""Main authentication router including all subdomain routers."""

from fastapi import APIRouter

from src.services.authentication.sessions.router import router as sessions_router
from src.services.authentication.tokens.router import router as tokens_router
from src.services.authentication.passwords.router import router as passwords_router


router = APIRouter()

# Include subdomain routers
router.include_router(
    sessions_router,
    prefix="/sessions",
    tags=["authentication/sessions"]
)

router.include_router(
    tokens_router,
    prefix="/tokens",
    tags=["authentication/tokens"]
)

router.include_router(
    passwords_router,
    prefix="/passwords",
    tags=["authentication/passwords"]
)
