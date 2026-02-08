from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.deps import get_current_user
from app.models.tenant import User
from app.models.quickbooks import QuickBooksConnection
from app.services.quickbooks_service import (
    get_authorization_url,
    exchange_code_for_tokens,
    get_valid_connection,
)
from app.services.quickbooks_service import sync_clients_from_qb

router = APIRouter(prefix="/api/qb", tags=["quickbooks"])


@router.get("/connect-url")
def get_qb_connect_url(
    user: User = Depends(get_current_user),
):
    """Return the QuickBooks OAuth URL for the buyer to connect their account."""
    url = get_authorization_url(state=user.tenant_id)
    return {"url": url}


@router.get("/callback")
def qb_oauth_callback(
    code: str = Query(...),
    realm_id: str = Query(..., alias="realmId"),
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    QuickBooks redirects here after user authorizes. In production, state should
    encode the tenant/user so we know who to attach the connection to. For now
    we require the frontend to have sent state or we use a single-tenant flow.
    """
    # State can be JWT or tenant_id so we know which tenant just connected.
    # Simplified: expect frontend to pass state=tenant_id when redirecting to connect-url
    # and we'd need to pass it through QB. Intuit allows state. So: state = tenant_id.
    if not state:
        raise HTTPException(400, detail="Missing state (tenant context)")
    tenant_id = state
    tokens = exchange_code_for_tokens(code, realm_id)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    existing = db.query(QuickBooksConnection).filter(QuickBooksConnection.tenant_id == tenant_id).first()
    if existing:
        existing.realm_id = realm_id
        existing.access_token = tokens["access_token"]
        existing.refresh_token = tokens["refresh_token"]
        existing.token_expires_at = expires_at
        db.commit()
    else:
        conn = QuickBooksConnection(
            tenant_id=tenant_id,
            realm_id=realm_id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_expires_at=expires_at,
        )
        db.add(conn)
        db.commit()
    # Redirect to frontend so user lands back in the app
    return RedirectResponse(url="http://localhost:5173/dashboard?qb=connected", status_code=302)


@router.get("/status")
def qb_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = get_valid_connection(db, user.tenant_id)
    return {"connected": conn is not None, "realm_id": conn.realm_id if conn else None}


@router.post("/sync-clients")
def sync_clients(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync clients from QuickBooks to local Client table."""
    clients = sync_clients_from_qb(db, user.tenant_id)
    return {"synced": len(clients)}
