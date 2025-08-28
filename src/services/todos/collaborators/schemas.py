from uuid import UUID
from pydantic import BaseModel


class TodoProjectCollaboratorResponse(BaseModel):
    email: str
    id: UUID


class TodoProjectCollaboratorCreate(BaseModel):
    id: UUID
