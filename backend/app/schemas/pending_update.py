from pydantic import BaseModel
from datetime import datetime


class PendingUpdateOut(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    subject: str
    body_html: str
    body_plain: str | None
    change_summary: str | None
    status: str
    created_at: datetime | None
    client_display_name: str | None = None
    client_email: str | None = None

    class Config:
        from_attributes = True


class PendingUpdateEdit(BaseModel):
    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
