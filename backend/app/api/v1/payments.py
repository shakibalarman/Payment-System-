"""Payments, transactions, refunds endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_roles
from backend.app.api.v1.helpers import get_merchant
from backend.app.models import Payment, Transaction, Refund, Merchant, User, can_transition_payment, PaymentStatus
from backend.app.schemas import PaymentCreateIn, PaymentConfirmIn, RefundCreateIn
from backend.app.services.payments import create_payment, settle_payment, create_refund
from backend.app.services.common import audit

router = APIRouter(tags=["payments"])


def paginate(q, page: int, page_size: int):
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, {"page": page, "page_size": page_size, "total": total}


@router.post("/payments")
def create(data: PaymentCreateIn, request: Request, db: Session = Depends(get_db),
           idem: str | None = Header(default=None, alias="Idempotency-Key"),
           merchant: Merchant = Depends(get_merchant)):
    if merchant.is_suspended:
        raise HTTPException(status_code=403, detail="Merchant suspended.")
    p = create_payment(db, merchant=merchant, data=data, idem_key=idem or "")
    audit(db, actor_id=merchant.user_id, action="PAYMENT_CREATED", resource="payment", resource_id=p.id)
    db.commit()
    db.refresh(p)
    return {"success": True, "data": {"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "status": p.status, "provider_code": p.provider_code, "customer_email": p.customer_email, "fee_amount": p.fee_amount, "net_amount": p.net_amount, "checkout_url": f"/checkout/{p.id}"}}


@router.get("/payments")
def list_payments(page: int = 1, page_size: int = 20, status: str | None = None, search: str | None = None,
                  db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    q = db.query(Payment).filter(Payment.merchant_id == merchant.id).order_by(Payment.created_at.desc())
    if status:
        q = q.filter(Payment.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Payment.id.like(like), Payment.customer_email.like(like), Payment.description.like(like), Payment.provider_ref.like(like)))
    items, pg = paginate(q, page, min(page_size, 100))
    return {"success": True, "data": [{"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "status": p.status, "customer_email": p.customer_email, "provider_code": p.provider_code, "created_at": p.created_at} for p in items], "pagination": pg}


@router.get("/payments/{payment_id}")
def get_payment(payment_id: str, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    p = db.query(Payment).filter(Payment.id == payment_id, Payment.merchant_id == merchant.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    txns = db.query(Transaction).filter(Transaction.payment_id == p.id).all()
    return {"success": True, "data": {"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "status": p.status, "provider_code": p.provider_code, "provider_ref": p.provider_ref, "customer_email": p.customer_email, "payment_method": p.payment_method, "fee_amount": p.fee_amount, "net_amount": p.net_amount, "created_at": p.created_at, "paid_at": p.paid_at, "transactions": [{"id": t.id, "type": t.type, "amount": t.amount, "status": t.status} for t in txns]}}


@router.post("/payments/{payment_id}/confirm")
def confirm(payment_id: str, data: PaymentConfirmIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    """DEMO endpoint for the mock provider: simulates customer completing checkout.
    Real providers confirm via server-to-server webhook, never via frontend status."""
    p = db.query(Payment).filter(Payment.id == payment_id, Payment.merchant_id == merchant.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if data.payment_method:
        p.payment_method = data.payment_method
    settle_payment(db, p, success=(data.outcome == "SUCCESS"))
    audit(db, actor_id=merchant.user_id, action="PAYMENT_CONFIRMED", resource="payment", resource_id=p.id)
    db.commit()
    return {"success": True, "data": {"id": p.id, "status": p.status}}


@router.post("/payments/{payment_id}/cancel")
def cancel(payment_id: str, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    p = db.query(Payment).filter(Payment.id == payment_id, Payment.merchant_id == merchant.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if not can_transition_payment(PaymentStatus(p.status), PaymentStatus.CANCELLED):
        raise HTTPException(status_code=409, detail=f"Cannot cancel payment in status {p.status}.")
    p.status = "CANCELLED"
    for t in db.query(Transaction).filter(Transaction.payment_id == p.id).all():
        t.status = "CANCELLED"
    db.commit()
    return {"success": True, "data": {"id": p.id, "status": p.status}}


@router.get("/transactions")
def list_txns(page: int = 1, page_size: int = 20, status: str | None = None, method: str | None = None,
              search: str | None = None, sort: str = "-created_at", db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    q = db.query(Transaction).filter(Transaction.merchant_id == merchant.id)
    if status:
        q = q.filter(Transaction.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Transaction.id.like(like), Transaction.provider_ref.like(like)))
    q = q.order_by(Transaction.created_at.desc() if sort.startswith("-") else Transaction.created_at.asc())
    items, pg = paginate(q, page, min(page_size, 100))
    out = []
    for t in items:
        p = db.query(Payment).filter(Payment.id == t.payment_id).first()
        out.append({"id": t.id, "payment_id": t.payment_id, "amount": t.amount, "currency": t.currency, "status": t.status, "fee_amount": t.fee_amount, "net_amount": t.net_amount, "provider_ref": t.provider_ref, "created_at": t.created_at, "customer_email": p.customer_email if p else "", "payment_method": p.payment_method if p else ""})
    return {"success": True, "data": out, "pagination": pg}


@router.get("/transactions/{txn_id}")
def get_txn(txn_id: str, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    t = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.merchant_id == merchant.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    p = db.query(Payment).filter(Payment.id == t.payment_id).first()
    return {"success": True, "data": {"id": t.id, "payment_id": t.payment_id, "amount": t.amount, "currency": t.currency, "status": t.status, "fee_amount": t.fee_amount, "net_amount": t.net_amount, "provider_ref": t.provider_ref, "created_at": t.created_at, "customer_email": p.customer_email if p else "", "payment_method": p.payment_method if p else "", "provider": p.provider_code if p else ""}}


@router.post("/refunds")
def create(data: RefundCreateIn, request: Request, db: Session = Depends(get_db),
           idem: str | None = Header(default=None, alias="Idempotency-Key"),
           merchant: Merchant = Depends(get_merchant)):
    r = create_refund(db, merchant=merchant, payment_id=data.payment_id, amount=data.amount, reason=data.reason, idem_key=idem or "")
    db.commit()
    return {"success": True, "data": {"id": r.id, "payment_id": r.payment_id, "amount": r.amount, "status": r.status}}


@router.get("/refunds")
def list_refunds(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    q = db.query(Refund).filter(Refund.merchant_id == merchant.id).order_by(Refund.created_at.desc())
    items, pg = paginate(q, page, min(page_size, 100))
    return {"success": True, "data": [{"id": r.id, "payment_id": r.payment_id, "amount": r.amount, "status": r.status, "created_at": r.created_at} for r in items], "pagination": pg}


@router.get("/refunds/{refund_id}")
def get_refund(refund_id: str, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    r = db.query(Refund).filter(Refund.id == refund_id, Refund.merchant_id == merchant.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Refund not found.")
    return {"success": True, "data": {"id": r.id, "payment_id": r.payment_id, "amount": r.amount, "status": r.status, "reason": r.reason, "created_at": r.created_at}}
