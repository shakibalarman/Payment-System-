"""Core payment flows with atomic ledger updates."""
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models import (
    Payment, Transaction, Refund, Wallet, WalletTransaction, Withdrawal,
    can_transition_payment, PaymentStatus, Customer, Merchant,
)
from backend.app.services.common import calc_fee, fanout, notify, audit
from backend.app.services.providers import get_provider
from fastapi import HTTPException


def get_or_create_wallet(db: Session, merchant_id: str, currency: str = "BDT") -> Wallet:
    w = db.query(Wallet).filter(Wallet.merchant_id == merchant_id).first()
    if not w:
        w = Wallet(merchant_id=merchant_id, available=0, pending=0, currency=currency)
        db.add(w)
        db.flush()
    return w


def ledger(db: Session, wallet: Wallet, *, kind: str, amount: int, ref_type: str = "", ref_id: str = ""):
    if kind in ("CREDIT", "RELEASE"):
        wallet.available += amount
    elif kind in ("DEBIT", "HOLD"):
        wallet.available -= amount
    elif kind == "PENDING_CREDIT":
        wallet.pending += amount
    elif kind == "PENDING_RELEASE":
        wallet.pending -= amount
    t = WalletTransaction(wallet_id=wallet.id, merchant_id=wallet.merchant_id, kind=kind, amount=amount, balance_after=wallet.available, reference_type=ref_type, reference_id=ref_id)
    db.add(t)


def create_payment(db: Session, *, merchant: Merchant, data, idem_key: str) -> Payment:
    if idem_key:
        existing = db.query(Payment).filter(Payment.merchant_id == merchant.id, Payment.idempotency_key == idem_key).first()
        if existing:
            return existing
    provider = get_provider(data.provider_code or "mock")
    res = provider.create_payment(amount=data.amount, currency=data.currency, description=data.description, customer_email=str(data.customer_email or ""), meta={})
    fee, net = calc_fee(data.amount, float(merchant.fee_percent or 1.5))
    p = Payment(
        merchant_id=merchant.id, amount=data.amount, currency=data.currency, description=data.description,
        customer_email=str(data.customer_email or ""), status="PROCESSING", provider_code=data.provider_code or "mock",
        provider_ref=res.provider_ref, payment_method=data.payment_method or "", fee_amount=fee, net_amount=net,
        idempotency_key=idem_key or secrets.token_hex(8), invoice_id=data.invoice_id, payment_link_id=data.payment_link_id,
    )
    db.add(p)
    db.flush()
    # link customer record
    if p.customer_email:
        c = db.query(Customer).filter(Customer.merchant_id == merchant.id, Customer.email == p.customer_email).first()
        if not c:
            c = Customer(merchant_id=merchant.id, email=p.customer_email, name="")
            db.add(c)
            db.flush()
        p.customer_id = c.id
    db.add(Transaction(payment_id=p.id, merchant_id=merchant.id, type="CHARGE", amount=p.amount, currency=p.currency, fee_amount=fee, net_amount=net, status="PROCESSING", provider_ref=res.provider_ref))
    audit(db, actor_id=None, action="PAYMENT_CREATED", resource="payment", resource_id=p.id, meta={"amount": p.amount})
    db.flush()
    return p


def settle_payment(db: Session, payment: Payment, success: bool):
    frm = PaymentStatus(payment.status)
    to = PaymentStatus.SUCCESS if success else PaymentStatus.FAILED
    if payment.status == to.value:
        return payment  # idempotent
    if not can_transition_payment(frm, to):
        raise HTTPException(status_code=409, detail=f"Cannot transition payment from {frm.value} to {to.value}.")
    payment.status = to.value
    if success:
        payment.paid_at = datetime.now(timezone.utc)
    for t in db.query(Transaction).filter(Transaction.payment_id == payment.id).all():
        t.status = to.value
    merchant = db.query(Merchant).filter(Merchant.id == payment.merchant_id).first()
    if success and merchant:
        w = get_or_create_wallet(db, merchant.id, payment.currency)
        ledger(db, w, kind="CREDIT", amount=payment.net_amount, ref_type="payment", ref_id=payment.id)
        fanout(db, merchant_id=merchant.id, event_type="payment.success", payload={"event_id": secrets.token_hex(12), "payment_id": payment.id, "amount": payment.amount})
        notify(db, user_id=merchant.user_id, type="PAYMENT_SUCCESS", title="Payment received", body=f"{payment.amount} {payment.currency} received.")
        # mark invoice paid
        if payment.invoice_id:
            from backend.app.models import Invoice
            inv = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
            if inv:
                inv.status = "PAID"
    elif merchant:
        fanout(db, merchant_id=merchant.id, event_type="payment.failed", payload={"event_id": secrets.token_hex(12), "payment_id": payment.id})
        notify(db, user_id=merchant.user_id, type="PAYMENT_FAILED", title="Payment failed", body=f"Payment {payment.id[:8]} failed.")
    db.flush()
    return payment


def create_refund(db: Session, *, merchant: Merchant, payment_id: str, amount: int | None, reason: str, idem_key: str):
    if idem_key:
        ex = db.query(Refund).filter(Refund.merchant_id == merchant.id, Refund.idempotency_key == idem_key).first()
        if ex:
            return ex
    payment = db.query(Payment).filter(Payment.id == payment_id, Payment.merchant_id == merchant.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if payment.status not in ("SUCCESS", "PARTIALLY_REFUNDED"):
        raise HTTPException(status_code=409, detail="Only successful payments can be refunded.")
    already = sum(r.amount for r in db.query(Refund).filter(Refund.payment_id == payment.id, Refund.status.in_(["PENDING", "PROCESSING", "COMPLETED"])).all())
    refundable = payment.amount - already
    amt = amount or refundable
    if amt <= 0 or amt > refundable:
        raise HTTPException(status_code=422, detail="Refund amount exceeds refundable amount.")
    provider = get_provider(payment.provider_code)
    pr = provider.refund_payment(payment.provider_ref, amt)
    r = Refund(payment_id=payment.id, merchant_id=merchant.id, amount=amt, currency=payment.currency, reason=reason, status="COMPLETED", provider_ref=pr.provider_ref, idempotency_key=idem_key or secrets.token_hex(8))
    db.add(r)
    db.flush()
    # update payment status
    total = already + amt
    payment.status = "REFUNDED" if total >= payment.amount else "PARTIALLY_REFUNDED"
    w = get_or_create_wallet(db, merchant.id, payment.currency)
    ledger(db, w, kind="DEBIT", amount=amt, ref_type="refund", ref_id=r.id)
    fanout(db, merchant_id=merchant.id, event_type="payment.refunded", payload={"event_id": secrets.token_hex(12), "payment_id": payment.id, "refund_id": r.id, "amount": amt})
    notify(db, user_id=merchant.user_id, type="REFUND_COMPLETED", title="Refund completed", body=f"Refunded {amt}.")
    audit(db, actor_id=None, action="REFUND_CREATED", resource="refund", resource_id=r.id, meta={"amount": amt})
    db.flush()
    return r


def request_withdrawal(db: Session, *, merchant: Merchant, amount: int, destination: str) -> Withdrawal:
    w = get_or_create_wallet(db, merchant.id)
    # row-level lock where supported
    try:
        db.query(Wallet).filter(Wallet.id == w.id).with_for_update().first()
    except Exception:
        pass
    db.refresh(w)
    if amount > w.available:
        raise HTTPException(status_code=422, detail="Insufficient available balance.")
    wd = Withdrawal(merchant_id=merchant.id, amount=amount, currency=w.currency, destination=destination, status="PENDING")
    db.add(wd)
    db.flush()
    ledger(db, w, kind="HOLD", amount=amount, ref_type="withdrawal", ref_id=wd.id)
    audit(db, actor_id=None, action="WITHDRAWAL_REQUESTED", resource="withdrawal", resource_id=wd.id, meta={"amount": amount})
    notify(db, user_id=merchant.user_id, type="WITHDRAWAL_COMPLETED", title="Withdrawal requested", body=f"Withdrawal of {amount} requested.")
    db.flush()
    return wd


def process_withdrawal(db: Session, wd: Withdrawal, approve: bool):
    if wd.status != "PENDING":
        raise HTTPException(status_code=409, detail="Withdrawal already processed.")
    merchant = db.query(Merchant).filter(Merchant.id == wd.merchant_id).first()
    w = get_or_create_wallet(db, wd.merchant_id)
    if approve:
        wd.status = "COMPLETED"
        # move from hold: available already reduced at HOLD; adjust pending bookkeeping via DEBIT record only
        db.add(WalletTransaction(wallet_id=w.id, merchant_id=w.merchant_id, kind="DEBIT", amount=0, balance_after=w.available, reference_type="withdrawal", reference_id=wd.id))
        fanout(db, merchant_id=wd.merchant_id, event_type="withdrawal.completed", payload={"event_id": secrets.token_hex(12), "withdrawal_id": wd.id, "amount": wd.amount})
        if merchant:
            notify(db, user_id=merchant.user_id, type="WITHDRAWAL_COMPLETED", title="Withdrawal completed", body=f"Withdrawal of {wd.amount} completed.")
        audit(db, actor_id=None, action="WITHDRAWAL_APPROVED", resource="withdrawal", resource_id=wd.id)
    else:
        wd.status = "CANCELLED"
        ledger(db, w, kind="RELEASE", amount=wd.amount, ref_type="withdrawal", ref_id=wd.id)
    db.flush()
    return wd
