"""Customer self-service: own payments, refunds view, profile already in notifications router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_roles
from backend.app.models import Payment, User

router = APIRouter(tags=["customer"])
Customer = require_roles("customer", "merchant", "admin")


@router.get("/customer/payments")
def my_payments(db: Session = Depends(get_db), user: User = Depends(Customer)):
    items = db.query(Payment).filter(Payment.customer_email == user.email).order_by(Payment.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "status": p.status, "created_at": p.created_at} for p in items]}


@router.get("/customer/payments/{pid}")
def my_payment(pid: str, db: Session = Depends(get_db), user: User = Depends(Customer)):
    p = db.query(Payment).filter(Payment.id == pid, Payment.customer_email == user.email).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    return {"success": True, "data": {"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "status": p.status, "fee_amount": p.fee_amount, "created_at": p.created_at, "paid_at": p.paid_at}}
