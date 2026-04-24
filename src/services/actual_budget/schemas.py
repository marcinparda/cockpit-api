from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    balance: int | None = None
    type: str | None = None


class Transaction(BaseModel):
    id: str
    account: str
    date: str
    amount: int
    payee_name: str | None = None
    notes: str | None = None
    category: str | None = None
