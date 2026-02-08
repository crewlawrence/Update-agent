from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import uuid


def uuid_str():
    return str(uuid.uuid4())


class Client(Base):
    """Client/customer per tenant; maps to QuickBooks Customer + optional contact email."""
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True, default=uuid_str)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    qb_customer_id = Column(String(64), nullable=False, index=True)  # QuickBooks Customer.Id
    display_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)  # primary contact for updates
    company_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="clients")
    snapshots = relationship("ClientSnapshot", back_populates="client", order_by="ClientSnapshot.created_at.desc()")
    pending_updates = relationship("PendingUpdate", back_populates="client")
    update_history = relationship("UpdateHistory", back_populates="client")


class ClientSnapshot(Base):
    """Last known state for a client (invoices, etc.) so we can detect changes."""
    __tablename__ = "client_snapshots"

    id = Column(String(36), primary_key=True, default=uuid_str)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False, index=True)
    snapshot_type = Column(String(32), nullable=False)  # e.g. "invoices", "milestones"
    payload = Column(Text, nullable=False)  # JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="snapshots")


class PendingUpdate(Base):
    """Agent-drafted email update; buyer can approve (send), edit, or delete."""
    __tablename__ = "pending_updates"

    id = Column(String(36), primary_key=True, default=uuid_str)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False, index=True)
    subject = Column(String(512), nullable=False)
    body_html = Column(Text, nullable=False)
    body_plain = Column(Text, nullable=True)
    change_summary = Column(Text, nullable=True)  # what changed (for buyer context)
    status = Column(String(32), default="pending")  # pending | approved | rejected | sent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="pending_updates")
    client = relationship("Client", back_populates="pending_updates")


class UpdateHistory(Base):
    """Record of sent updates so we don't repeat and can track what was sent to whom."""
    __tablename__ = "update_history"

    id = Column(String(36), primary_key=True, default=uuid_str)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False, index=True)
    pending_update_id = Column(String(36), nullable=True)  # if created from PendingUpdate
    subject = Column(String(512), nullable=False)
    change_summary = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    snapshot_version = Column(String(64), nullable=True)  # link to snapshot used

    tenant = relationship("Tenant", back_populates="update_history")
    client = relationship("Client", back_populates="update_history")
