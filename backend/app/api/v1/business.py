"""Invoices, payment links, customers, payment methods."""
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.v1.helpers import get_merchant
from backend.app.core.deps import get_current_user
from backend.app.models import Invoice, InvoiceItem, PaymentLink, Customer, PaymentMethod, Merchant, User
from backend.app.schemas import InvoiceCreateIn, PaymentLinkCreateIn, PaymentMethodIn
from backend.app.services.common import audit

router = APIRouter(tags=["business"])


@router.post("/invoices")
def create_invoice(data: InvoiceCreateIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    subtotal = sum(i.quantity * i.unit_price for i in data.items)
    total = subtotal + data.tax - data.discount
    if total <= 0:
        raise HTTPException(status_code=422, detail="Invoice total must be positive.")
    import time
    inv = Invoice(merchant_id=merchant.id, invoice_no=f"INV-{int(time.time())}-{secrets.token_hex(2).upper()}", customer_name=data.customer_name, customer_email=data.customer_email, currency=data.currency, subtotal=subtotal, tax=data.tax, discount=data.discount, total=total, status="SENT", due_date=data.due_date, notes=data.notes, public_token=secrets.token_urlsafe(24))
    db.add(inv)
    db.flush()
    for i in data.items:
        db.add(InvoiceItem(invoice_id=inv.id, name=i.name, quantity=i.quantity, unit_price=i.unit_price))
    audit(db, actor_id=merchant.user_id, action="INVOICE_CREATED", resource="invoice", resource_id=inv.id)
    db.commit()
    return {"success": True, "data": {"id": inv.id, "invoice_no": inv.invoice_no, "total": total, "status": inv.status, "public_token": inv.public_token, "pay_url": f"/invoice/{inv.public_token}"}}


@router.get("/invoices")
def list_invoices(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    q = db.query(Invoice).filter(Invoice.merchant_id == merchant.id).order_by(Invoice.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"success": True, "data": [{"id": i.id, "invoice_no": i.invoice_no, "customer_email": i.customer_email, "total": i.total, "status": i.status, "created_at": i.created_at} for i in items], "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.merchant_id == merchant.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == inv.id).all()
    return {"success": True, "data": {"id": inv.id, "invoice_no": inv.invoice_no, "customer_name": inv.customer_name, "customer_email": inv.customer_email, "subtotal": inv.subtotal, "tax": inv.tax, "discount": inv.discount, "total": inv.total, "status": inv.status, "public_token": inv.public_token, "items": [{"name": x.name, "quantity": x.quantity, "unit_price": x.unit_price} for x in items]}}


@router.post("/payment-links")
def create_link(data: PaymentLinkCreateIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    pl = PaymentLink(merchant_id=merchant.id, amount=data.amount, currency=data.currency, description=data.description, public_token=secrets.token_urlsafe(20), expires_at=data.expires_at)
    db.add(pl)
    db.commit()
    return {"success": True, "data": {"id": pl.id, "url": f"/pay/{pl.public_token}", "public_token": pl.public_token, "amount": pl.amount}}


@router.get("/payment-links")
def list_links(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    items = db.query(PaymentLink).filter(PaymentLink.merchant_id == merchant.id).order_by(PaymentLink.created_at.desc()).all()
    return {"success": True, "data": [{"id": p.id, "amount": p.amount, "currency": p.currency, "description": p.description, "public_token": p.public_token, "url": f"/pay/{p.public_token}", "active": p.active} for p in items]}


@router.get("/customers")
def list_customers(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    items = db.query(Customer).filter(Customer.merchant_id == merchant.id).order_by(Customer.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": c.id, "name": c.name, "email": c.email, "created_at": c.created_at} for c in items]}


@router.get("/payment-methods")
def list_methods(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).all()
    return {"success": True, "data": [{"id": m.id, "method_type": m.method_type, "brand": m.brand, "last4": m.last4, "is_default": m.is_default} for m in items]}


@router.post("/payment-methods")
def add_method(data: PaymentMethodIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Only tokenized references stored — never raw PAN/CVV.
    if data.last4 and (len(data.last4) != 4 or not data.last4.isdigit()):
        raise HTTPException(status_code=422, detail="last4 must be 4 digits.")
    m = PaymentMethod(user_id=user.id, method_type=data.method_type, brand=data.brand, last4=data.last4, provider_token=data.provider_token, is_default=data.is_default)
    db.add(m)
    db.commit()
    return {"success": True, "data": {"id": m.id}}
