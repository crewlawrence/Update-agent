from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import uuid


def uuid_str():
    return str(uuid.uuid4())


class Tenant(Base):
    """Multi-tenant: each buyer organization is a tenant."""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=uuid_str)
    name = Column(String(255), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="tenant")
    qb_connection = relationship("QuickBooksConnection", back_populates="tenant", uselist=False)
    clients = relationship("Client", back_populates="tenant")
    pending_updates = relationship("PendingUpdate", back_populates="tenant")
    update_history = relationship("UpdateHistory", back_populates="tenant")


class User(Base):
    """Buyer user; belongs to a tenant. OAuth login (e.g. Google) or email/password."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=uuid_str)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # null if OAuth-only
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="users")
