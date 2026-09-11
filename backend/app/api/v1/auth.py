"""Auth endpoints: register/login/refresh/logout/verify/forgot/reset."""
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, generate_token
from backend.app.models import User, UserSession, EmailToken, Merchant, Wallet
from backend.app.schemas import RegisterIn, LoginIn, RefreshIn, ForgotIn, ResetIn, VerifyEmailIn
from backend.app.services.common import audit
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])

# simple in-memory rate limit for auth
_hits: dict[str, list[float]] = {}
import time


def rate_limit(key: str, limit: int = 20, window: int = 60):
    now = time.time()
    arr = [t for t in _hits.get(key, []) if now - t < window]
    if len(arr) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    arr.append(now)
    _hits[key] = arr


@router.post("/register")
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    rate_limit("register:" + (request.client.host if request.client else "x"))
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered.")
    if data.role not in ("customer", "merchant"):
        raise HTTPException(status_code=422, detail="Invalid role.")
    u = User(email=data.email.lower(), password_hash=hash_password(data.password), role=data.role, full_name=data.full_name)
    db.add(u)
    db.flush()
    if data.role == "merchant":
        db.add(Merchant(user_id=u.id, email=u.email, owner_name=data.full_name))
        db.flush()
        m = db.query(Merchant).filter(Merchant.user_id == u.id).first()
        db.add(Wallet(merchant_id=m.id, available=0, pending=0))
    # email verification token (in real life emailed via SMTP worker)
    raw = generate_token()
    db.add(EmailToken(user_id=u.id, purpose="verify_email", token_hash=hashlib.sha256(raw.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(hours=48)))
    audit(db, actor_id=u.id, action="REGISTER", resource="user", resource_id=u.id, ip=request.client.host if request.client else "")
    db.commit()
    access = create_access_token(u.id, u.role)
    refresh = create_refresh_token(u.id)
    db.add(UserSession(user_id=u.id, refresh_token_hash=hashlib.sha256(refresh.encode()).hexdigest(), ip_address=request.client.host if request.client else "", expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    db.commit()
    return {"success": True, "data": {"user": {"id": u.id, "email": u.email, "role": u.role, "full_name": u.full_name, "is_verified": u.is_verified}, "access_token": access, "refresh_token": refresh, "verify_token": raw if True else None}}


@router.post("/login")
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    rate_limit("login:" + (request.client.host if request.client else "x"))
    u = db.query(User).filter(User.email == data.email.lower()).first()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not u.is_active or u.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended or inactive.")
    access = create_access_token(u.id, u.role)
    refresh = create_refresh_token(u.id)
    db.add(UserSession(user_id=u.id, refresh_token_hash=hashlib.sha256(refresh.encode()).hexdigest(), ip_address=request.client.host if request.client else "", expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    audit(db, actor_id=u.id, action="LOGIN", resource="user", resource_id=u.id, ip=request.client.host if request.client else "")
    db.commit()
    return {"success": True, "data": {"access_token": access, "refresh_token": refresh, "user": {"id": u.id, "email": u.email, "role": u.role, "full_name": u.full_name, "is_verified": u.is_verified}}}


@router.post("/refresh")
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type.")
    h = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    sess = db.query(UserSession).filter(UserSession.refresh_token_hash == h, UserSession.revoked == False).first()  # noqa: E712
    if not sess or sess.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired.")
    u = db.query(User).filter(User.id == payload.get("sub")).first()
    if not u or not u.is_active or u.is_suspended:
        raise HTTPException(status_code=401, detail="Account unavailable.")
    return {"success": True, "data": {"access_token": create_access_token(u.id, u.role)}}


@router.post("/logout")
def logout(data: RefreshIn, db: Session = Depends(get_db)):
    h = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    sess = db.query(UserSession).filter(UserSession.refresh_token_hash == h).first()
    if sess:
        sess.revoked = True
        audit(db, actor_id=sess.user_id, action="LOGOUT", resource="user", resource_id=sess.user_id)
        db.commit()
    return {"success": True, "data": {"message": "Logged out."}}


@router.post("/verify-email")
def verify_email(data: VerifyEmailIn, db: Session = Depends(get_db)):
    h = hashlib.sha256(data.token.encode()).hexdigest()
    t = db.query(EmailToken).filter(EmailToken.token_hash == h, EmailToken.purpose == "verify_email", EmailToken.used == False).first()  # noqa: E712
    if not t:
        raise HTTPException(status_code=404, detail="Invalid verification token.")
    exp = t.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Token expired.")
    t.used = True
    u = db.query(User).filter(User.id == t.user_id).first()
    u.is_verified = True
    db.commit()
    return {"success": True, "data": {"message": "Email verified."}}


@router.post("/forgot-password")
def forgot(data: ForgotIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == data.email.lower()).first()
    # always return success to avoid enumeration
    if u:
        raw = generate_token()
        db.add(EmailToken(user_id=u.id, purpose="reset_password", token_hash=hashlib.sha256(raw.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(hours=2)))
        db.commit()
        # In production: queue email via worker. For dev, return token so UI can complete flow.
        return {"success": True, "data": {"message": "If the email exists, a reset link was sent.", "reset_token": raw}}
    return {"success": True, "data": {"message": "If the email exists, a reset link was sent."}}


@router.post("/reset-password")
def reset(data: ResetIn, db: Session = Depends(get_db)):
    h = hashlib.sha256(data.token.encode()).hexdigest()
    t = db.query(EmailToken).filter(EmailToken.token_hash == h, EmailToken.purpose == "reset_password", EmailToken.used == False).first()  # noqa: E712
    if not t:
        raise HTTPException(status_code=404, detail="Invalid reset token.")
    exp = t.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Token expired.")
    t.used = True
    u = db.query(User).filter(User.id == t.user_id).first()
    u.password_hash = hash_password(data.new_password)
    audit(db, actor_id=u.id, action="PASSWORD_CHANGED", resource="user", resource_id=u.id)
    db.commit()
    return {"success": True, "data": {"message": "Password reset. Please login."}}
