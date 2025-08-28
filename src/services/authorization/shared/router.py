"""Main authorization router that includes all submodule routers."""

from fastapi import APIRouter

from src.services.authorization.roles.router import router as roles_router
from src.services.authorization.permissions.router import router as permissions_router
from src.services.authorization.user_permissions.router import router as user_permissions_router

router = APIRouter()

router.include_router(
    roles_router,
    prefix="/roles",
    tags=["authorization/roles"]
)

router.include_router(
    permissions_router,
    prefix="/permissions",
    tags=["authorization/permissions"]
)

router.include_router(
    user_permissions_router,
    prefix="/permissions",
    tags=["authorization/user-permissions"]
)
