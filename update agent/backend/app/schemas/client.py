from pydantic import BaseModel
from datetime import datetime


class ClientOut(BaseModel):
    id: str
    tenant_id: str
    qb_customer_id: str
    display_name: str
    email: str | None
    company_name: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class ClientUpdateIn(BaseModel):
    email: str | None = None
    display_name: str | None = None
