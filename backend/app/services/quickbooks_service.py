"""QuickBooks OAuth and API access. Uses intuit-oauth for tokens and requests for API calls."""
import json
from datetime import datetime, timedelta
from typing import Any
import requests
from intuitlib.client import AuthClient
from intuitlib.exceptions import AuthClientError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.quickbooks import QuickBooksConnection
from app.models.tenant import Tenant
from app.models.client import Client

settings = get_settings()
QB_BASE_SANDBOX = "https://sandbox-quickbooks.api.intuit.com"
QB_BASE_PROD = "https://quickbooks.api.intuit.com"


def get_auth_client() -> AuthClient:
    return AuthClient(
        settings.qb_client_id,
        settings.qb_client_secret,
        settings.qb_redirect_uri,
        settings.qb_environment,
    )


def get_authorization_url(state: str = "qb_connect") -> str:
    auth_client = get_auth_client()
    return auth_client.get_authorization_url(
        scopes=["com.intuit.quickbooks.accounting"],
        state=state,
    )


def exchange_code_for_tokens(code: str, realm_id: str) -> dict[str, Any]:
    auth_client = get_auth_client()
    auth_client.get_bearer_token(code, realm_id=realm_id)
    return {
        "access_token": auth_client.access_token,
        "refresh_token": auth_client.refresh_token,
        "expires_in": auth_client.expires_in,
    }


def get_base_url() -> str:
    return QB_BASE_SANDBOX if settings.qb_environment == "sandbox" else QB_BASE_PROD


def get_valid_connection(db: Session, tenant_id: str) -> QuickBooksConnection | None:
    conn = db.query(QuickBooksConnection).filter(QuickBooksConnection.tenant_id == tenant_id).first()
    if not conn:
        return None
    # Refresh if expiring within 5 minutes
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if conn.token_expires_at and (conn.token_expires_at - now) < timedelta(minutes=5):
        conn = refresh_connection(db, conn)
    return conn


def refresh_connection(db: Session, conn: QuickBooksConnection) -> QuickBooksConnection | None:
    auth_client = get_auth_client()
    auth_client.refresh_token = conn.refresh_token
    try:
        auth_client.refresh()
    except AuthClientError:
        return None
    conn.access_token = auth_client.access_token
    conn.token_expires_at = datetime.utcnow() + timedelta(seconds=auth_client.expires_in)
    db.commit()
    db.refresh(conn)
    return conn


def qb_request(
    method: str,
    path: str,
    access_token: str,
    realm_id: str,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict[str, Any]:
    base = get_base_url()
    url = f"{base}/v3/company/{realm_id}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    if json_data is not None:
        headers["Content-Type"] = "application/json"
    resp = requests.request(
        method,
        url,
        headers=headers,
        json=json_data,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def fetch_customers(db: Session, tenant_id: str) -> list[dict]:
    conn = get_valid_connection(db, tenant_id)
    if not conn:
        return []
    data = qb_request("GET", "query", conn.access_token, conn.realm_id, params={
        "query": "SELECT * FROM Customer WHERE Active = true MAXRESULTS 1000"
    })
    return data.get("QueryResponse", {}).get("Customer", [])


def fetch_invoices(db: Session, tenant_id: str, customer_id: str | None = None) -> list[dict]:
    conn = get_valid_connection(db, tenant_id)
    if not conn:
        return []
    query = "SELECT * FROM Invoice ORDER BY TxnDate DESC MAXRESULTS 500"
    if customer_id:
        query = f"SELECT * FROM Invoice WHERE CustomerRef = '{customer_id}' ORDER BY TxnDate DESC MAXRESULTS 500"
    data = qb_request("GET", "query", conn.access_token, conn.realm_id, params={"query": query})
    return data.get("QueryResponse", {}).get("Invoice", [])


def sync_clients_from_qb(db: Session, tenant_id: str) -> list[Client]:
    """Ensure Client rows exist for each QB Customer; update display name / company."""
    customers = fetch_customers(db, tenant_id)
    clients = []
    for c in customers:
        qb_id = str(c.get("Id", ""))
        display = c.get("DisplayName") or c.get("FullyQualifiedName") or "Unknown"
        company = (c.get("CompanyName") or "").strip() or None
        primary_email = None
        if c.get("PrimaryEmailAddr"):
            primary_email = c.get("PrimaryEmailAddr", {}).get("Address")
        existing = db.query(Client).filter(
            Client.tenant_id == tenant_id,
            Client.qb_customer_id == qb_id,
        ).first()
        if existing:
            existing.display_name = display
            existing.company_name = company
            if primary_email:
                existing.email = primary_email
            clients.append(existing)
        else:
            client = Client(
                tenant_id=tenant_id,
                qb_customer_id=qb_id,
                display_name=display,
                company_name=company,
                email=primary_email,
            )
            db.add(client)
            clients.append(client)
    db.commit()
    for c in clients:
        db.refresh(c)
    return clients
