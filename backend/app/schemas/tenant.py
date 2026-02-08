from pydantic import BaseModel
from datetime import datetime


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool
    created_at: datetime | None

    class Config:
        from_attributes = True
