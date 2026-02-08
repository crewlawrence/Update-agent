from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.deps import get_current_user
from app.models.tenant import User
from app.services.agent_service import run_agent_for_tenant
from app.schemas.pending_update import PendingUpdateOut
from app.api.pending_updates import _enrich

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run", response_model=list[PendingUpdateOut])
def run_agent(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run the agent for the current tenant: sync QB, detect changes, draft updates."""
    created = run_agent_for_tenant(db, user.tenant_id)
    return [_enrich(p, db) for p in created]
