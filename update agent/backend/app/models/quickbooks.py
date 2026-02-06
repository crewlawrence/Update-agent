from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import uuid


def uuid_str():
    return str(uuid.uuid4())


class QuickBooksConnection(Base):
    """Per-tenant QuickBooks OAuth connection (one per tenant)."""
    __tablename__ = "quickbooks_connections"

    id = Column(String(36), primary_key=True, default=uuid_str)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    realm_id = Column(String(64), nullable=False)  # QB company id
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="qb_connection")
