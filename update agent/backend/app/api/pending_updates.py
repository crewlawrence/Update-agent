from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.deps import get_current_user
from app.models.tenant import User
from app.models.client import Client, PendingUpdate, UpdateHistory
from app.schemas.pending_update import PendingUpdateOut, PendingUpdateEdit

router = APIRouter(prefix="/api/pending-updates", tags=["pending-updates"])


def _enrich(p: PendingUpdate, db: Session) -> PendingUpdateOut:
    client = db.query(Client).filter(Client.id == p.client_id).first()
    return PendingUpdateOut(
        id=p.id,
        tenant_id=p.tenant_id,
        client_id=p.client_id,
        subject=p.subject,
        body_html=p.body_html,
        body_plain=p.body_plain,
        change_summary=p.change_summary,
        status=p.status,
        created_at=p.created_at,
        client_display_name=client.display_name if client else None,
        client_email=client.email if client else None,
    )


@router.get("", response_model=list[PendingUpdateOut])
def list_pending(
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(PendingUpdate).filter(PendingUpdate.tenant_id == user.tenant_id)
    if status:
        q = q.filter(PendingUpdate.status == status)
    rows = q.order_by(PendingUpdate.created_at.desc()).all()
    return [_enrich(r, db) for r in rows]


@router.get("/{update_id}", response_model=PendingUpdateOut)
def get_pending(
    update_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(PendingUpdate).filter(
        PendingUpdate.id == update_id,
        PendingUpdate.tenant_id == user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(404, detail="Update not found")
    return _enrich(row, db)


@router.patch("/{update_id}", response_model=PendingUpdateOut)
def edit_pending(
    update_id: str,
    data: PendingUpdateEdit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(PendingUpdate).filter(
        PendingUpdate.id == update_id,
        PendingUpdate.tenant_id == user.tenant_id,
        PendingUpdate.status == "pending",
    ).first()
    if not row:
        raise HTTPException(404, detail="Update not found or not editable")
    if data.subject is not None:
        row.subject = data.subject
    if data.body_html is not None:
        row.body_html = data.body_html
    if data.body_plain is not None:
        row.body_plain = data.body_plain
    db.commit()
    db.refresh(row)
    return _enrich(row, db)


@router.delete("/{update_id}")
def delete_pending(
    update_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(PendingUpdate).filter(
        PendingUpdate.id == update_id,
        PendingUpdate.tenant_id == user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(404, detail="Update not found")
    row.status = "rejected"
    db.commit()
    return {"ok": True}


@router.post("/{update_id}/send")
def approve_and_send(
    update_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark as sent and record in history. (Actual email sending can be added later.)"""
    row = db.query(PendingUpdate).filter(
        PendingUpdate.id == update_id,
        PendingUpdate.tenant_id == user.tenant_id,
        PendingUpdate.status == "pending",
    ).first()
    if not row:
        raise HTTPException(404, detail="Update not found or not pending")
    row.status = "sent"
    row.sent_at = datetime.now(timezone.utc)
    history = UpdateHistory(
        tenant_id=user.tenant_id,
        client_id=row.client_id,
        pending_update_id=row.id,
        subject=row.subject,
        change_summary=row.change_summary,
    )
    db.add(history)
    db.commit()
    return {"ok": True, "message": "Update marked as sent."}
