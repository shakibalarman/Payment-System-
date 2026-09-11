"""Notifications + profile."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models import Notification, User

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def list_n(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50).all()
    unread = db.query(Notification).filter(Notification.user_id == user.id, Notification.read == False).count()  # noqa: E712
    return {"success": True, "data": [{"id": n.id, "type": n.type, "title": n.title, "body": n.body, "read": n.read, "created_at": n.created_at} for n in items], "unread": unread}


@router.post("/notifications/{nid}/read")
def mark_read(nid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == nid, Notification.user_id == user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")
    n.read = True
    db.commit()
    return {"success": True, "data": {"id": n.id, "read": True}}


@router.get("/users/me")
def me(user: User = Depends(get_current_user)):
    return {"success": True, "data": {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name, "is_verified": user.is_verified}}


@router.put("/users/me")
def update_me(payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if "full_name" in payload:
        user.full_name = str(payload["full_name"])[:255]
    if "phone" in payload:
        user.phone = str(payload["phone"])[:64]
    db.commit()
    return {"success": True, "data": {"id": user.id}}
