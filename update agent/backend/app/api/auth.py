from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.tenant import Tenant, User
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, verify_password
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, RefreshIn
from app.auth.deps import get_current_user
import re

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:64] if s else "tenant"


@router.post("/register", response_model=TokenResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    base_slug = _slug(data.tenant_name)
    slug = base_slug
    n = 0
    while db.query(Tenant).filter(Tenant.slug == slug).first():
        n += 1
        slug = f"{base_slug}-{n}"
    tenant = Tenant(name=data.tenant_name, slug=slug)
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(tenant)
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token({"sub": user.id, "tenant_id": tenant.id}),
        refresh_token=create_refresh_token({"sub": user.id}),
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant inactive")
    return TokenResponse(
        access_token=create_access_token({"sub": user.id, "tenant_id": tenant.id}),
        refresh_token=create_refresh_token({"sub": user.id}),
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant inactive")
    return TokenResponse(
        access_token=create_access_token({"sub": user.id, "tenant_id": tenant.id}),
        refresh_token=create_refresh_token({"sub": user.id}),
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
    )
