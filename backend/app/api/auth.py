import re
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.tenant import Tenant, User
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.cookies import (
    set_refresh_cookie,
    clear_refresh_cookie,
    create_and_store_refresh_token,
    consume_refresh_token,
)
from app.schemas.auth import UserCreate, UserLogin, TokenResponse


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/logout")
def logout():
    """Clear the HttpOnly refresh cookie so the client is logged out."""
    response = JSONResponse(content={"detail": "Logged out"})
    clear_refresh_cookie(response)
    return response


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:64] if s else "tenant"


def _token_response(access_token: str, user_id: str, tenant_id: str, email: str) -> dict:
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "email": email,
    }


@router.post("/register")
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
    access_token = create_access_token({"sub": user.id, "tenant_id": tenant.id})
    refresh_token = create_and_store_refresh_token(db, user.id)
    response = JSONResponse(content=_token_response(access_token, user.id, tenant.id, user.email))
    set_refresh_cookie(response, refresh_token)
    return response


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant inactive")
    access_token = create_access_token({"sub": user.id, "tenant_id": tenant.id})
    refresh_token = create_and_store_refresh_token(db, user.id)
    response = JSONResponse(content=_token_response(access_token, user.id, tenant.id, user.email))
    set_refresh_cookie(response, refresh_token)
    return response


@router.post("/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    from app.config import get_settings
    settings = get_settings()
    cookie_token = request.cookies.get(settings.refresh_cookie_name)
    if not cookie_token:
        response = JSONResponse(content={"detail": "Missing refresh token"}, status_code=401)
        clear_refresh_cookie(response)
        return response
    result = consume_refresh_token(db, cookie_token)
    if not result:
        response = JSONResponse(content={"detail": "Invalid or expired refresh token"}, status_code=401)
        clear_refresh_cookie(response)
        return response
    new_refresh_token, user_id = result
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        response = JSONResponse(content={"detail": "User not found"}, status_code=401)
        clear_refresh_cookie(response)
        return response
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        response = JSONResponse(content={"detail": "Tenant inactive"}, status_code=403)
        clear_refresh_cookie(response)
        return response
    access_token = create_access_token({"sub": user.id, "tenant_id": tenant.id})
    response = JSONResponse(content=_token_response(access_token, user.id, tenant.id, user.email))
    set_refresh_cookie(response, new_refresh_token)
    return response
