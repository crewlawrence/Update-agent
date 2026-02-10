"""HttpOnly refresh cookie helpers."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.refresh_token import RefreshToken

settings = get_settings()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_opaque_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def set_refresh_cookie(response: Response, token: str) -> None:
    max_age = settings.refresh_cookie_max_age_days * 24 * 3600
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path="/api/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/api/auth",
    )


def create_and_store_refresh_token(db: Session, user_id: str) -> str:
    """Create opaque token, store hash in DB, return raw token for cookie."""
    token = create_opaque_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_cookie_max_age_days)
    row = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    return token


def consume_refresh_token(db: Session, token: str) -> tuple[str, str] | None:
    """
    Validate token, delete it (rotate), create new token and row.
    Returns (new_token, user_id) or None if invalid/expired. Caller should clear cookie and 401.
    """
    token_hash = hash_token(token)
    row = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.expires_at > datetime.now(timezone.utc),
    ).first()
    if not row:
        return None
    user_id = row.user_id
    db.delete(row)
    db.commit()
    new_token = create_and_store_refresh_token(db, user_id)
    return (new_token, user_id)
