from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_serializer, Field


class TodoProjectBase(BaseModel):
    name: str


class TodoProjectCreate(TodoProjectBase):
    pass


class TodoProjectUpdate(TodoProjectBase):
    pass


class TodoProjectCollaboratorResponse(BaseModel):
    email: str


class TodoProjectCollaboratorCreate(BaseModel):
    id: str


class TodoProjectInDBBase(TodoProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: UUID
    is_general: bool

    model_config = ConfigDict(from_attributes=True)


class TodoProject(TodoProjectInDBBase):
    collaborators: List[str] = Field(default_factory=list)

    @field_serializer('collaborators')
    def serialize_collaborators(self, collaborators: Optional[List[str]]) -> List[str]:
        return collaborators or []
