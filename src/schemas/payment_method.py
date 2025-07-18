from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PaymentMethodBase(BaseModel):
    name: str


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(PaymentMethodBase):
    name: str | None = None


class PaymentMethod(PaymentMethodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
