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


class TodoProjectCollaboratorBase(BaseModel):
    user_id: UUID


class TodoProjectCollaboratorCreate(TodoProjectCollaboratorBase):
    pass


class TodoProjectCollaboratorResponse(TodoProjectCollaboratorBase):
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TodoProjectInDBBase(TodoProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: UUID
    is_general: bool

    model_config = ConfigDict(from_attributes=True)


class TodoProject(TodoProjectInDBBase):
    # Set a default empty list instead of trying to load the relationship
    collaborators: List[TodoProjectCollaboratorResponse] = Field(
        default_factory=list)

    # This serializer ensures we always return a list even if the field is None
    @field_serializer('collaborators')
    def serialize_collaborators(self, collaborators: Optional[List[TodoProjectCollaboratorResponse]]) -> List[TodoProjectCollaboratorResponse]:
        return collaborators or []
