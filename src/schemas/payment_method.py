from datetime import datetime
from pydantic import BaseModel


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

    class Config:
        orm_mode = True
        from_attributes = True
