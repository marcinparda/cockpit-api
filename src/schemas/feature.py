from pydantic import BaseModel
from datetime import datetime


class FeatureBase(BaseModel):
    name: str


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(FeatureBase):
    pass


class FeatureInDBBase(FeatureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Feature(FeatureInDBBase):
    pass
