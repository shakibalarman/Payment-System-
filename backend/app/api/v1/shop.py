"""Customer shop: product catalog + buy + pay with demo merchant.

Lets an authenticated customer purchase products without needing
merchant credentials. Payments are created under the Demo Store
merchant (first APPROVED merchant) so they appear in the merchant
dashboard, wallet ledger, webhooks, etc.
"""
import secrets
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models import Merchant, Payment, User
from backend.app.services.payments import create_payment, settle_payment

router = APIRouter(tags=["shop"])


# ---------- Static catalog (prices in minor units, BDT) ----------
# 50000 = ৳500.00
PRODUCTS = [
    {
        "id": "tshirt-classic",
        "name": "Classic Cotton T-Shirt",
        "category": "Apparel",
        "base_price": 129900,
        "currency": "BDT",
        "description": "100% breathable cotton, unisex fit. Perfect everyday tee.",
        "emoji": "👕",
        "rating": 4.6,
        "stock": 120,
        "colors": ["Black", "White", "Navy", "Olive"],
        "sizes": ["S", "M", "L", "XL", "XXL"],
    },
    {
        "id": "shirt-oxford",
        "name": "Premium Oxford Shirt",
        "category": "Apparel",
        "base_price": 249900,
        "currency": "BDT",
        "description": "Wrinkle-resistant oxford, slim fit. Office to dinner.",
        "emoji": "👔",
        "rating": 4.8,
        "stock": 80,
        "colors": ["White", "Light Blue", "Pink", "Charcoal"],
        "sizes": ["S", "M", "L", "XL", "XXL"],
    },
    {
        "id": "hoodie-fleece",
        "name": "Cozy Fleece Hoodie",
        "category": "Apparel",
        "base_price": 199900,
        "currency": "BDT",
        "description": "Soft fleece lining, kangaroo pocket, drawstring hood.",
        "emoji": "🧥",
        "rating": 4.7,
        "stock": 60,
        "colors": ["Grey", "Black", "Maroon"],
        "sizes": ["M", "L", "XL"],
    },
    {
        "id": "jeans-slim",
        "name": "Slim-Fit Denim Jeans",
        "category": "Apparel",
        "base_price": 279900,
        "currency": "BDT",
        "description": "Stretch denim, mid-rise slim fit. All-day comfort.",
        "emoji": "👖",
        "rating": 4.5,
        "stock": 90,
        "colors": ["Indigo", "Black", "Light Wash"],
        "sizes": ["28", "30", "32", "34", "36"],
    },
    {
        "id": "mobile-nova",
        "name": "Nova X5 Smartphone",
        "category": "Electronics",
        "base_price": 3499900,
        "currency": "BDT",
        "description": "6.7\" AMOLED 120Hz, 50MP OIS camera, 5000mAh, 5G.",
        "emoji": "📱",
        "rating": 4.7,
        "stock": 35,
        "colors": ["Midnight Black", "Ocean Blue", "Pearl White"],
        "storages": ["128GB", "256GB (+৳4,000)", "512GB (+৳8,000)"],
    },
    {
        "id": "mobile-pixel-lite",
        "name": "Pixel Lite 12",
        "category": "Electronics",
        "base_price": 2499900,
        "currency": "BDT",
        "description": "Compact 6.1\" OLED, clean Android, best camera in class.",
        "emoji": "📲",
        "rating": 4.6,
        "stock": 42,
        "colors": ["Black", "Mint", "Lavender"],
        "storages": ["128GB", "256GB (+৳3,500)"],
    },
    {
        "id": "laptop-ultrabook",
        "name": "AeroBook Ultra 14 Laptop",
        "category": "Electronics",
        "base_price": 12999900,
        "currency": "BDT",
        "description": '14" 2.8K OLED, 16GB RAM, 512GB SSD, 18hr battery, 1.2kg.',
        "emoji": "💻",
        "rating": 4.9,
        "stock": 18,
        "colors": ["Silver", "Space Grey"],
        "storages": ["512GB", "1TB (+৳12,000)"],
        "rams": ["16GB", "32GB (+৳10,000)"],
    },
    {
        "id": "laptop-gaming",
        "name": "Strike G15 Gaming Laptop",
        "category": "Electronics",
        "base_price": 15999900,
        "currency": "BDT",
        "description": '15.6" 144Hz, RTX graphics, 16GB RAM, RGB keyboard.',
        "emoji": "🎮",
        "rating": 4.8,
        "stock": 12,
        "colors": ["Black"],
        "storages": ["1TB SSD"],
        "rams": ["16GB", "32GB (+৳10,000)"],
    },
]

_STORAGE_SURCHARGE = {
    "256GB (+৳4,000)": 400000,
    "512GB (+৳8,000)": 800000,
    "256GB (+৳3,500)": 350000,
    "1TB (+৳12,000)": 1200000,
    "32GB (+৳10,000)": 1000000,
}

_SIZE_SURCHARGE = {"XXL": 20000, "36": 15000}


def _find_product(pid: str) -> dict | None:
    return next((p for p in PRODUCTS if p["id"] == pid), None)


def _get_demo_merchant(db: Session) -> Merchant:
    m = db.query(Merchant).filter(Merchant.kyc_status == "APPROVED").first()
    if not m:
        m = db.query(Merchant).first()
    if not m:
        raise HTTPException(status_code=503, detail="Shop is not ready: no merchant found. Ask admin to run seed.")
    return m


class BuyIn(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=10)
    color: str = ""
    size: str = ""
    storage: str = ""
    ram: str = ""
    payment_method: str = "card"


class PayIn(BaseModel):
    outcome: str = "SUCCESS"  # SUCCESS | FAILED (demo control)
    payment_method: str = ""


@router.get("/shop/products")
def list_products():
    return {"success": True, "data": PRODUCTS}


@router.post("/shop/buy")
def shop_buy(
    data: BuyIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    idem: str | None = Header(default=None, alias="Idempotency-Key"),
):
    prod = _find_product(data.product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")
    if data.quantity > prod["stock"]:
        raise HTTPException(status_code=422, detail="Not enough stock.")

    unit = prod["base_price"]
    unit += _STORAGE_SURCHARGE.get(data.storage, 0)
    unit += _STORAGE_SURCHARGE.get(data.ram, 0)
    unit += _SIZE_SURCHARGE.get(data.size, 0)
    total = unit * data.quantity

    opts = " / ".join(x for x in [data.color, data.size, data.storage, data.ram] if x)
    desc = f"{prod['name']} x{data.quantity}" + (f" ({opts})" if opts else "")

    merchant = _get_demo_merchant(db)
    payload = SimpleNamespace(
        amount=total,
        currency=prod["currency"],
        description=desc,
        customer_email=user.email,
        payment_method=data.payment_method or "card",
        invoice_id=None,
        payment_link_id=None,
        provider_code="mock",
    )
    p = create_payment(db, merchant=merchant, data=payload, idem_key=idem or f"shop-{user.id}-{prod['id']}-{secrets.token_hex(4)}")
    db.commit()
    db.refresh(p)
    return {
        "success": True,
        "data": {
            "id": p.id,
            "product": prod["name"],
            "amount": p.amount,
            "currency": p.currency,
            "description": p.description,
            "status": p.status,
            "fee_amount": p.fee_amount,
            "net_amount": p.net_amount,
            "checkout_url": f"/checkout/{p.id}",
            "receipt_url": f"/receipt/{p.id}",
        },
    }


@router.post("/shop/pay/{payment_id}")
def shop_pay(
    payment_id: str,
    data: PayIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if p.customer_email != user.email and user.role != "admin":
        raise HTTPException(status_code=403, detail="This order belongs to another customer.")
    if data.payment_method:
        p.payment_method = data.payment_method
    settle_payment(db, p, success=(data.outcome == "SUCCESS"))
    db.commit()
    return {"success": True, "data": {"id": p.id, "status": p.status, "receipt_url": f"/receipt/{p.id}"}}
