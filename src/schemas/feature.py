from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)


class Feature(FeatureInDBBase):
    pass
