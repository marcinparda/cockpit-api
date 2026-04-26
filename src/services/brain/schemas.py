from datetime import datetime
from pydantic import BaseModel


class NoteMeta(BaseModel):
    path: str
    title: str
    tags: list[str]
    type: str
    created_at: datetime
    updated_at: datetime
    aliases: list[str]


class Note(NoteMeta):
    body: str


class NoteCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []
    type: str = "note"
    aliases: list[str] = []


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    type: str | None = None
    aliases: list[str] | None = None


class NoteSearchResult(NoteMeta):
    excerpt: str


class FolderTree(BaseModel):
    folders: list[str]
