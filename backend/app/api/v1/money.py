"""Wallet + withdrawals."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.v1.helpers import get_merchant
from backend.app.models import Wallet, WalletTransaction, Withdrawal, Merchant
from backend.app.schemas import WithdrawalCreateIn
from backend.app.services.payments import get_or_create_wallet, request_withdrawal

router = APIRouter(tags=["money"])


@router.get("/wallet")
def get_wallet(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    w = get_or_create_wallet(db, merchant.id)
    db.commit()
    txns = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == w.id).order_by(WalletTransaction.created_at.desc()).limit(50).all()
    return {"success": True, "data": {"available": w.available, "pending": w.pending, "total": w.available + w.pending, "currency": w.currency, "ledger": [{"id": t.id, "kind": t.kind, "amount": t.amount, "balance_after": t.balance_after, "reference_type": t.reference_type, "created_at": t.created_at} for t in txns]}}


@router.post("/withdrawals")
def create_wd(data: WithdrawalCreateIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    wd = request_withdrawal(db, merchant=merchant, amount=data.amount, destination=data.destination)
    db.commit()
    return {"success": True, "data": {"id": wd.id, "amount": wd.amount, "status": wd.status}}


@router.get("/withdrawals")
def list_wd(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    items = db.query(Withdrawal).filter(Withdrawal.merchant_id == merchant.id).order_by(Withdrawal.created_at.desc()).all()
    return {"success": True, "data": [{"id": w.id, "amount": w.amount, "status": w.status, "destination": w.destination, "created_at": w.created_at} for w in items]}
