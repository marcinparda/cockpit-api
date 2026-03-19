from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StoreMeta(BaseModel):
    key: str
    type: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []


class StoreEnvelope(BaseModel):
    meta: StoreMeta
    data: Any


class StoreKeyCreate(BaseModel):
    type: str
    tags: list[str] = []
    data: Any


class StoreKeyPatch(BaseModel):
    data: dict[str, Any]
