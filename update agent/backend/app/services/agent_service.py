"""
Orchestrates: sync QB clients, detect changes per client, draft updates via Agno, save pending updates.
"""
import json
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.client import Client, ClientSnapshot, PendingUpdate, UpdateHistory
from app.models.tenant import Tenant
from app.services.quickbooks_service import (
    get_valid_connection,
    fetch_invoices,
    sync_clients_from_qb,
)
from app.agents.update_agent import draft_client_update


def get_last_snapshot(db: Session, client_id: str, snapshot_type: str) -> dict | None:
    row = (
        db.query(ClientSnapshot)
        .filter(
            ClientSnapshot.client_id == client_id,
            ClientSnapshot.snapshot_type == snapshot_type,
        )
        .order_by(ClientSnapshot.created_at.desc())
        .first()
    )
    if not row or not row.payload:
        return None
    try:
        return json.loads(row.payload)
    except json.JSONDecodeError:
        return None


def save_snapshot(db: Session, client_id: str, snapshot_type: str, payload: dict) -> ClientSnapshot:
    snap = ClientSnapshot(
        client_id=client_id,
        snapshot_type=snapshot_type,
        payload=json.dumps(payload),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def invoice_summary_for_comparison(invoices: list[dict]) -> dict:
    """Normalize invoice list to a comparable summary (ids and key fields)."""
    return {
        "count": len(invoices),
        "invoices": [
            {
                "Id": inv.get("Id"),
                "DocNumber": inv.get("DocNumber"),
                "TotalAmt": inv.get("TotalAmt"),
                "Balance": inv.get("Balance"),
                "TxnDate": inv.get("TxnDate"),
            }
            for inv in (invoices or [])
        ],
    }


def detect_invoice_changes(previous: dict | None, current: dict) -> dict | None:
    """If there are new or updated invoices, return a short change summary for the agent."""
    if not current or not current.get("invoices"):
        return None
    prev_ids = set()
    if previous and previous.get("invoices"):
        prev_ids = {str(i.get("Id")) for i in previous["invoices"]}
    cur_invoices = current.get("invoices", [])
    new_ones = [i for i in cur_invoices if str(i.get("Id")) not in prev_ids]
    if not new_ones and previous and previous.get("count") == current.get("count"):
        return None
    lines = []
    if new_ones:
        for i in new_ones:
            amt = i.get("TotalAmt")
            doc = i.get("DocNumber") or i.get("Id")
            lines.append(f"New invoice {doc} (amount: {amt})")
    if not lines:
        return None
    return {"summary": "; ".join(lines), "new_invoices": new_ones}


def has_recent_pending_for_client(db: Session, client_id: str) -> bool:
    """Avoid duplicate pending updates for the same client (e.g. within same run)."""
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    exists = (
        db.query(PendingUpdate)
        .filter(
            PendingUpdate.client_id == client_id,
            PendingUpdate.status == "pending",
            PendingUpdate.created_at >= since,
        )
        .first()
    )
    return exists is not None


def run_agent_for_tenant(db: Session, tenant_id: str) -> list[PendingUpdate]:
    """
    Sync clients from QuickBooks, detect changes per client, draft updates where meaningful.
    Creates PendingUpdate rows and saves new snapshots. Returns list of created PendingUpdate.
    """
    conn = get_valid_connection(db, tenant_id)
    if not conn:
        return []

    sync_clients_from_qb(db, tenant_id)
    clients = db.query(Client).filter(Client.tenant_id == tenant_id).all()
    created: list[PendingUpdate] = []

    for client in clients:
        invoices = fetch_invoices(db, tenant_id, client.qb_customer_id)
        current = invoice_summary_for_comparison(invoices)
        previous = get_last_snapshot(db, client.id, "invoices")
        change = detect_invoice_changes(previous, current)

        if not change or has_recent_pending_for_client(db, client.id):
            # Save snapshot even if no update drafted (for next comparison)
            save_snapshot(db, client.id, "invoices", current)
            continue

        company_context = ""
        if client.company_name:
            company_context = f"Company: {client.company_name}"

        draft = draft_client_update(
            client_display_name=client.display_name,
            client_email=client.email,
            change_summary=change["summary"],
            company_context=company_context,
        )

        pending = PendingUpdate(
            tenant_id=tenant_id,
            client_id=client.id,
            subject=draft["subject"],
            body_html=draft["body_html"],
            body_plain=draft.get("body_plain") or draft["body_html"],
            change_summary=change["summary"],
            status="pending",
        )
        db.add(pending)
        created.append(pending)
        save_snapshot(db, client.id, "invoices", current)

    db.commit()
    for p in created:
        db.refresh(p)
    return created
