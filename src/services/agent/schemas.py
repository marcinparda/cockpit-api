from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str
    model: str


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    model: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    extra_data: Optional[Any] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str


class ModelInfo(BaseModel):
    id: str
    label: str


class ModelListResponse(BaseModel):
    models: list[ModelInfo]
    default: str
