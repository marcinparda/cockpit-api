from pydantic import BaseModel
from typing import Dict, List
from src.permissions import Resources, Actions


class APIKeyBase(BaseModel):
    permissions: Dict[Resources, List[Actions]]


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyUpdate(APIKeyBase):
    pass


class APIKeyInDB(APIKeyBase):
    key: str
