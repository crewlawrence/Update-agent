from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.deps import get_current_user
from app.models.tenant import User
from app.models.client import Client
from app.schemas.client import ClientOut, ClientUpdateIn

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Client).filter(Client.tenant_id == user.tenant_id).order_by(Client.display_name).all()
    return [ClientOut.model_validate(r) for r in rows]


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(404, detail="Client not found")
    return ClientOut.model_validate(row)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
  client_id: str,
  data: ClientUpdateIn,
  user: User = Depends(get_current_user),
  db: Session = Depends(get_db),
):
    row = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == user.tenant_id,
    ).first()
    if not row:
        raise HTTPException(404, detail="Client not found")
    if data.email is not None:
        row.email = data.email
    if data.display_name is not None:
        row.display_name = data.display_name
    db.commit()
    db.refresh(row)
    return ClientOut.model_validate(row)
