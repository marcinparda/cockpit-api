from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.config import settings
from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features
from src.services.brain import service
from src.services.brain.schemas import FolderTree, Note, NoteCreate, NoteMeta, NoteSearchResult, NoteUpdate
from src.services.users.models import User

router = APIRouter(tags=["brain"])


def _notes_path() -> str:
    return settings.BRAIN_NOTES_PATH


@router.get("/notes", response_model=list[NoteMeta])
async def list_notes(
    path: str | None = Query(default=None),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    _: User = Depends(require_permission(Features.BRAIN, Actions.READ)),
):
    return await service.list_notes(_notes_path(), path, type, tag)


@router.get("/notes/{path:path}", response_model=Note)
async def get_note(
    path: str,
    _: User = Depends(require_permission(Features.BRAIN, Actions.READ)),
):
    try:
        return await service.get_note(_notes_path(), path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.post("/notes", response_model=Note, status_code=201)
async def create_note(
    path: str = Query(..., description="Relative path for new note, e.g. folder/my-note.md"),
    content: NoteCreate = ...,
    _: User = Depends(require_permission(Features.BRAIN, Actions.CREATE)),
):
    try:
        return await service.create_note(_notes_path(), path, content)
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Note already exists")


@router.put("/notes/{path:path}", response_model=Note)
async def update_note(
    path: str,
    content: NoteUpdate,
    _: User = Depends(require_permission(Features.BRAIN, Actions.UPDATE)),
):
    try:
        return await service.update_note(_notes_path(), path, content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.delete("/notes/{path:path}", status_code=204)
async def delete_note(
    path: str,
    _: User = Depends(require_permission(Features.BRAIN, Actions.DELETE)),
):
    try:
        await service.delete_note(_notes_path(), path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.get("/search", response_model=list[NoteSearchResult])
async def search_notes(
    q: str = Query(..., description="Full-text search query"),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    _: User = Depends(require_permission(Features.BRAIN, Actions.READ)),
):
    return await service.search_notes(_notes_path(), q, type, tag)


@router.get("/folders", response_model=FolderTree)
async def list_folders(
    _: User = Depends(require_permission(Features.BRAIN, Actions.READ)),
):
    folders = await service.list_folders(_notes_path())
    return FolderTree(folders=folders)
