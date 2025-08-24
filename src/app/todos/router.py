from fastapi import APIRouter
from .projects.router import router as projects_router
from .items.router import router as items_router
from .collaborators.router import router as collaborators_router

router = APIRouter()

router.include_router(projects_router, prefix="/projects",
                      tags=["todo-projects"])
router.include_router(items_router, prefix="/items", tags=["todo-items"])
router.include_router(collaborators_router, prefix="/projects/{project_id}/collaborators",
                      tags=["todo-collaborators"])
