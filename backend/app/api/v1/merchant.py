"""Merchant profile, KYC, dashboard stats."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.api.v1.helpers import get_merchant
from backend.app.models import Merchant, MerchantDocument, Payment, Refund, Wallet, User
from backend.app.schemas import MerchantProfileIn
from backend.app.services.common import audit, notify
from backend.app.services.payments import get_or_create_wallet

router = APIRouter(tags=["merchant"])


@router.get("/merchants/me")
def me(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    return {"success": True, "data": {"id": merchant.id, "business_name": merchant.business_name, "kyc_status": merchant.kyc_status, "fee_percent": float(merchant.fee_percent), "is_suspended": merchant.is_suspended}}


@router.put("/merchants/me")
def update_profile(data: MerchantProfileIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    for k, v in data.model_dump().items():
        setattr(merchant, k, v)
    audit(db, actor_id=merchant.user_id, action="MERCHANT_PROFILE_UPDATED", resource="merchant", resource_id=merchant.id)
    db.commit()
    return {"success": True, "data": {"id": merchant.id}}


@router.post("/merchants/kyc")
def submit_kyc(data: MerchantProfileIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    for k, v in data.model_dump().items():
        setattr(merchant, k, v)
    merchant.kyc_status = "UNDER_REVIEW"
    db.add(MerchantDocument(merchant_id=merchant.id, doc_type="kyc_bundle", file_path="stored-securely"))
    audit(db, actor_id=merchant.user_id, action="KYC_SUBMITTED", resource="merchant", resource_id=merchant.id)
    db.commit()
    return {"success": True, "data": {"kyc_status": merchant.kyc_status}}


@router.get("/merchants/dashboard")
def dashboard(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    base = db.query(Payment).filter(Payment.merchant_id == merchant.id)
    total_rev = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.merchant_id == merchant.id, Payment.status == "SUCCESS").scalar() or 0
    today_rev = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.merchant_id == merchant.id, Payment.status == "SUCCESS", Payment.created_at >= today).scalar() or 0
    ok = base.filter(Payment.status == "SUCCESS").count()
    failed = base.filter(Payment.status == "FAILED").count()
    refunds = db.query(func.coalesce(func.sum(Refund.amount), 0)).filter(Refund.merchant_id == merchant.id).scalar() or 0
    w = get_or_create_wallet(db, merchant.id)
    # 14-day revenue series from real data
    series = []
    for i in range(13, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        nxt = day + timedelta(days=1)
        s = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.merchant_id == merchant.id, Payment.status == "SUCCESS", Payment.created_at >= day, Payment.created_at < nxt).scalar() or 0
        series.append({"date": day.date().isoformat(), "revenue": int(s)})
    db.commit()
    return {"success": True, "data": {"total_revenue": int(total_rev), "today_revenue": int(today_rev), "successful_payments": ok, "failed_payments": failed, "refunds": int(refunds), "available_balance": w.available, "pending_balance": w.pending, "series": series}}
