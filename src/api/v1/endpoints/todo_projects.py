from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from src.core.database import get_db
from src.models.todo_project import TodoProject as TodoProjectModel
from src.schemas.todo_project import TodoProject, TodoProjectCreate, TodoProjectUpdate
from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_categories_permissions

router = APIRouter()


@router.get("/", response_model=list[TodoProject])
async def list_todo_projects(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    result = await db.execute(select(TodoProjectModel))
    return result.scalars().all()


@router.post("/", response_model=TodoProject, status_code=status.HTTP_201_CREATED)
async def create_todo_project(
    todo_project: TodoProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.CREATE))
):
    now = datetime.now()
    db_todo_project = TodoProjectModel(
        **todo_project.dict(),
        created_at=now,
        updated_at=now
    )
    db.add(db_todo_project)
    await db.commit()
    await db.refresh(db_todo_project)
    return db_todo_project


@router.get("/{todo_project_id}", response_model=TodoProject)
async def get_todo_project(
    todo_project_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")
    return todo_project


@router.put("/{todo_project_id}", response_model=TodoProject)
async def update_todo_project(
    todo_project_id: int,
    todo_project_update: TodoProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")
    for key, value in todo_project_update.dict(exclude_unset=True).items():
        setattr(todo_project, key, value)
    todo_project.updated_at = datetime.now()
    await db.commit()
    await db.refresh(todo_project)
    return todo_project


@router.delete("/{todo_project_id}", status_code=204)
async def delete_todo_project(
    todo_project_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")
    await db.delete(todo_project)
    await db.commit()
