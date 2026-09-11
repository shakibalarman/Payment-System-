"""Public (unauthenticated) checkout + payment-link/invoice resolution + provider webhooks."""
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Payment, PaymentLink, Invoice, InvoiceItem, Merchant, ProcessedEvent, PaymentStatus, can_transition_payment
from backend.app.services.payments import create_payment, settle_payment, get_or_create_wallet
from backend.app.services.providers import get_provider
from backend.app.schemas import PaymentCreateIn
from types import SimpleNamespace

router = APIRouter(tags=["public"])


def public_merchant(db: Session, merchant_id: str) -> dict:
    m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not m:
        return {}
    return {"business_name": m.business_name}  # never expose private data


@router.get("/public/checkout/{payment_id}")
def checkout_info(payment_id: str, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    return {"success": True, "data": {"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "status": p.status, "fee_amount": p.fee_amount, "total": p.amount, "merchant": public_merchant(db, p.merchant_id), "demo": p.provider_code == "mock"}}


@router.get("/public/pay/{token}")
def resolve_link(token: str, db: Session = Depends(get_db)):
    pl = db.query(PaymentLink).filter(PaymentLink.public_token == token, PaymentLink.active == True).first()  # noqa: E712
    if not pl:
        raise HTTPException(status_code=404, detail="Payment link expired or invalid.")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    exp = pl.expires_at
    if exp is not None:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < now:
            raise HTTPException(status_code=410, detail="Payment link expired.")
    return {"success": True, "data": {"amount": pl.amount, "currency": pl.currency, "description": pl.description, "merchant": public_merchant(db, pl.merchant_id)}}


@router.post("/public/pay/{token}")
def pay_link(token: str, payload: dict, request: Request, db: Session = Depends(get_db)):
    pl = db.query(PaymentLink).filter(PaymentLink.public_token == token, PaymentLink.active == True).first()  # noqa: E712
    if not pl:
        raise HTTPException(status_code=404, detail="Payment link expired or invalid.")
    merchant = db.query(Merchant).filter(Merchant.id == pl.merchant_id).first()
    data = SimpleNamespace(amount=pl.amount, currency=pl.currency, description=pl.description, customer_email=payload.get("customer_email", ""), payment_method=payload.get("payment_method", ""), invoice_id=None, payment_link_id=pl.id, provider_code="mock")
    idem = request.headers.get("Idempotency-Key", f"link-{token}-{(payload.get('customer_email',''))}")
    p = create_payment(db, merchant=merchant, data=data, idem_key=idem)
    db.commit()
    return {"success": True, "data": {"id": p.id, "status": p.status, "checkout_url": f"/checkout/{p.id}"}}


@router.get("/public/invoice/{token}")
def resolve_invoice(token: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.public_token == token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == inv.id).all()
    return {"success": True, "data": {"id": inv.id, "invoice_no": inv.invoice_no, "total": inv.total, "currency": inv.currency, "status": inv.status, "merchant": public_merchant(db, inv.merchant_id), "items": [{"name": x.name, "quantity": x.quantity, "unit_price": x.unit_price} for x in items]}}


@router.post("/public/invoice/{token}/pay")
def pay_invoice(token: str, payload: dict, request: Request, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.public_token == token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    if inv.status == "PAID":
        raise HTTPException(status_code=409, detail="Invoice already paid.")
    merchant = db.query(Merchant).filter(Merchant.id == inv.merchant_id).first()
    data = SimpleNamespace(amount=inv.total, currency=inv.currency, description=f"Invoice {inv.invoice_no}", customer_email=payload.get("customer_email", inv.customer_email), payment_method=payload.get("payment_method", ""), invoice_id=inv.id, payment_link_id=None, provider_code="mock")
    idem = request.headers.get("Idempotency-Key", f"inv-{inv.id}")
    p = create_payment(db, merchant=merchant, data=data, idem_key=idem)
    inv.status = "PENDING"
    db.commit()
    return {"success": True, "data": {"id": p.id, "status": p.status, "checkout_url": f"/checkout/{p.id}"}}


@router.post("/public/checkout/{payment_id}/pay")
def public_pay(payment_id: str, payload: dict, db: Session = Depends(get_db)):
    """Simulate customer completing a DEMO/mock checkout. Real providers redirect + webhook."""
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if p.status not in ("PENDING", "PROCESSING"):
        return {"success": True, "data": {"id": p.id, "status": p.status}}
    p.payment_method = payload.get("payment_method", "card")
    outcome = payload.get("outcome", "SUCCESS")  # mock provider demo control
    settle_payment(db, p, success=(outcome == "SUCCESS"))
    db.commit()
    return {"success": True, "data": {"id": p.id, "status": p.status, "receipt_url": f"/receipt/{p.id}"}}


@router.get("/public/receipt/{payment_id}")
def receipt(payment_id: str, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found.")
    return {"success": True, "data": {"transaction_id": p.provider_ref, "payment_id": p.id, "merchant": public_merchant(db, p.merchant_id), "customer": p.customer_email, "description": p.description, "amount": p.amount, "fee": p.fee_amount, "total": p.amount, "payment_method": p.payment_method, "status": p.status, "date": p.created_at}}


@router.post("/webhooks/provider/{code}")
async def provider_webhook(code: str, request: Request, db: Session = Depends(get_db)):
    """Secure provider webhook: signature check + idempotent processing + dedupe."""
    raw = await request.body()
    sig = request.headers.get("X-Provider-Signature", "")
    event_id = request.headers.get("X-Event-Id", "")
    provider = get_provider(code)
    from backend.app.core.config import get_settings
    secret = get_settings().payment_provider_secret
    if not provider.verify_webhook(raw, sig, secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    import json
    try:
        payload = json.loads(raw.decode() or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON.")
    event_id = event_id or payload.get("event_id", "")
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing event id.")
    if db.query(ProcessedEvent).filter(ProcessedEvent.event_id == event_id).first():
        return {"success": True, "data": {"duplicate": True}}  # duplicate-event protection
    db.add(ProcessedEvent(event_id=event_id))
    # apply status update if payment ref present
    ref = payload.get("provider_ref", "")
    status = payload.get("status", "")
    if ref and status in ("SUCCESS", "FAILED"):
        p = db.query(Payment).filter(Payment.provider_ref == ref).first()
        if p:
            settle_payment(db, p, success=(status == "SUCCESS"))
    db.commit()
    return {"success": True, "data": {"processed": True}}
