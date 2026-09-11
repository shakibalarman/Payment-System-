"""Merchant helper: resolve merchant from current user."""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models import Merchant, User


def get_merchant(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Merchant:
    if user.role not in ("merchant", "admin"):
        raise HTTPException(status_code=403, detail="Merchant access required.")
    m = db.query(Merchant).filter(Merchant.user_id == user.id).first()
    if not m and user.role == "admin":
        raise HTTPException(status_code=404, detail="Admin has no merchant profile.")
    if not m:
        raise HTTPException(status_code=404, detail="Merchant profile not found.")
    return m
