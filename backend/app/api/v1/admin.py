"""Admin: users, merchants, KYC, transactions, refunds, withdrawals, disputes, providers, fees, audit."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from backend.app.core.database import get_db
from backend.app.core.deps import require_roles
from backend.app.models import User, Merchant, Payment, Refund, Withdrawal, Dispute, AuditLog, PaymentProvider, Transaction
from backend.app.schemas import KycDecisionIn
from backend.app.services.common import audit, notify
from backend.app.services.payments import process_withdrawal

router = APIRouter(prefix="/admin", tags=["admin"])
Admin = require_roles("admin")


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(Admin)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return {"success": True, "data": {
        "total_users": db.query(User).count(),
        "total_merchants": db.query(Merchant).count(),
        "today_transactions": db.query(Transaction).filter(Transaction.created_at >= today).count(),
        "today_volume": int(db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.created_at >= today, Payment.status == "SUCCESS").scalar() or 0),
        "today_fees": int(db.query(func.coalesce(func.sum(Payment.fee_amount), 0)).filter(Payment.created_at >= today, Payment.status == "SUCCESS").scalar() or 0),
        "pending_kyc": db.query(Merchant).filter(Merchant.kyc_status == "UNDER_REVIEW").count(),
        "pending_withdrawals": db.query(Withdrawal).filter(Withdrawal.status == "PENDING").count(),
        "pending_disputes": db.query(Dispute).filter(Dispute.status == "OPEN").count(),
    }}


@router.get("/users")
def users(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: User = Depends(Admin)):
    q = db.query(User).order_by(User.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"success": True, "data": [{"id": u.id, "email": u.email, "role": u.role, "is_suspended": u.is_suspended, "is_verified": u.is_verified} for u in items], "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.post("/users/{uid}/suspend")
def suspend(uid: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(Admin)):
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    suspend_flag = bool(payload.get("suspend", True))
    u.is_suspended = suspend_flag
    m = db.query(Merchant).filter(Merchant.user_id == uid).first()
    if m:
        m.is_suspended = suspend_flag
    audit(db, actor_id=user.id, action="MERCHANT_SUSPENDED" if suspend_flag else "MERCHANT_UNSUSPENDED", resource="user", resource_id=uid)
    db.commit()
    return {"success": True, "data": {"id": uid, "is_suspended": suspend_flag}}


@router.get("/merchants")
def merchants(db: Session = Depends(get_db), user: User = Depends(Admin)):
    items = db.query(Merchant).order_by(Merchant.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": m.id, "business_name": m.business_name, "email": m.email, "kyc_status": m.kyc_status, "is_suspended": m.is_suspended} for m in items]}


@router.get("/kyc")
def kyc_queue(db: Session = Depends(get_db), user: User = Depends(Admin)):
    items = db.query(Merchant).filter(Merchant.kyc_status.in_(["PENDING", "UNDER_REVIEW"])).all()
    return {"success": True, "data": [{"id": m.id, "business_name": m.business_name, "owner_name": m.owner_name, "kyc_status": m.kyc_status} for m in items]}


@router.post("/kyc/{mid}")
def kyc_decide(mid: str, data: KycDecisionIn, db: Session = Depends(get_db), user: User = Depends(Admin)):
    m = db.query(Merchant).filter(Merchant.id == mid).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found.")
    m.kyc_status = "APPROVED" if data.approve else "REJECTED"
    m.kyc_rejection_reason = "" if data.approve else data.reason
    audit(db, actor_id=user.id, action="KYC_APPROVED" if data.approve else "KYC_REJECTED", resource="merchant", resource_id=mid)
    notify(db, user_id=m.user_id, type="KYC_APPROVED" if data.approve else "KYC_REJECTED", title="KYC approved" if data.approve else "KYC rejected", body=data.reason)
    db.commit()
    return {"success": True, "data": {"id": mid, "kyc_status": m.kyc_status}}


@router.get("/payments")
def all_payments(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: User = Depends(Admin)):
    q = db.query(Payment).order_by(Payment.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"success": True, "data": [{"id": p.id, "merchant_id": p.merchant_id, "amount": p.amount, "status": p.status} for p in items], "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/refunds")
def all_refunds(db: Session = Depends(get_db), user: User = Depends(Admin)):
    items = db.query(Refund).order_by(Refund.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": r.id, "payment_id": r.payment_id, "amount": r.amount, "status": r.status} for r in items]}


@router.get("/withdrawals")
def all_wd(db: Session = Depends(get_db), user: User = Depends(Admin)):
    items = db.query(Withdrawal).order_by(Withdrawal.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": w.id, "merchant_id": w.merchant_id, "amount": w.amount, "status": w.status} for w in items]}


@router.post("/withdrawals/{wid}")
def decide_wd(wid: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(Admin)):
    wd = db.query(Withdrawal).filter(Withdrawal.id == wid).first()
    if not wd:
        raise HTTPException(status_code=404, detail="Withdrawal not found.")
    process_withdrawal(db, wd, approve=bool(payload.get("approve", True)))
    audit(db, actor_id=user.id, action="WITHDRAWAL_APPROVED", resource="withdrawal", resource_id=wid)
    db.commit()
    return {"success": True, "data": {"id": wid, "status": wd.status}}


@router.get("/disputes")
def disputes(db: Session = Depends(get_db), user: User = Depends(Admin)):
    items = db.query(Dispute).order_by(Dispute.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": d.id, "payment_id": d.payment_id, "status": d.status, "reason": d.reason} for d in items]}


@router.get("/providers")
def providers(db: Session = Depends(get_db), user: User = Depends(Admin)):
    items = db.query(PaymentProvider).all()
    return {"success": True, "data": [{"id": p.id, "code": p.code, "name": p.name, "enabled": p.enabled} for p in items]}


@router.post("/providers")
def upsert_provider(payload: dict, db: Session = Depends(get_db), user: User = Depends(Admin)):
    p = db.query(PaymentProvider).filter(PaymentProvider.code == payload.get("code")).first()
    if not p:
        p = PaymentProvider(code=payload.get("code"), name=payload.get("name", payload.get("code")), enabled=bool(payload.get("enabled", True)))
        db.add(p)
    else:
        p.enabled = bool(payload.get("enabled", p.enabled))
        p.name = payload.get("name", p.name)
    db.commit()
    return {"success": True, "data": {"code": p.code, "enabled": p.enabled}}


@router.get("/audit-logs")
def logs(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: User = Depends(Admin)):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"success": True, "data": [{"id": a.id, "actor": a.actor_id, "action": a.action, "resource": a.resource, "created_at": a.created_at} for a in items], "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.post("/fees/{merchant_id}")
def set_fee(merchant_id: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(Admin)):
    m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found.")
    fee = float(payload.get("fee_percent", 1.5))
    if not (0 <= fee <= 10):
        raise HTTPException(status_code=422, detail="Fee must be between 0 and 10 percent.")
    m.fee_percent = fee  # stored per merchant; each payment snapshots its fee so history is immutable
    db.commit()
    return {"success": True, "data": {"id": m.id, "fee_percent": float(m.fee_percent)}}
