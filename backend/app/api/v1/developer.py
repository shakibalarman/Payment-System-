"""Developer platform: API keys + merchant webhooks + delivery logs."""
import hashlib
import json
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.v1.helpers import get_merchant
from backend.app.models import ApiKey, Webhook, WebhookDelivery, Merchant
from backend.app.schemas import ApiKeyCreateIn, WebhookCreateIn
from backend.app.services.common import audit

router = APIRouter(tags=["developer"])

ALLOWED_EVENTS = {"payment.created", "payment.success", "payment.failed", "payment.refunded", "payment.cancelled", "withdrawal.completed"}


@router.post("/api-keys")
def create_key(data: ApiKeyCreateIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    raw = "pk_" + secrets.token_urlsafe(32)
    prefix = raw[:8]
    h = hashlib.sha256(raw.encode()).hexdigest()
    k = ApiKey(merchant_id=merchant.id, name=data.name, prefix=prefix, key_hash=h)
    db.add(k)
    audit(db, actor_id=merchant.user_id, action="API_KEY_CREATED", resource="api_key", resource_id=k.id)
    db.commit()
    return {"success": True, "data": {"id": k.id, "prefix": prefix, "secret": raw, "warning": "Store this secret now. It will not be shown again."}}


@router.get("/api-keys")
def list_keys(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    items = db.query(ApiKey).filter(ApiKey.merchant_id == merchant.id).order_by(ApiKey.created_at.desc()).all()
    return {"success": True, "data": [{"id": k.id, "name": k.name, "prefix": k.prefix, "revoked": k.revoked, "last_used_at": k.last_used_at, "created_at": k.created_at} for k in items]}


@router.post("/api-keys/{key_id}/revoke")
def revoke_key(key_id: str, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    k = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.merchant_id == merchant.id).first()
    if not k:
        raise HTTPException(status_code=404, detail="API key not found.")
    k.revoked = True
    audit(db, actor_id=merchant.user_id, action="API_KEY_REVOKED", resource="api_key", resource_id=k.id)
    db.commit()
    return {"success": True, "data": {"id": k.id, "revoked": True}}


@router.post("/webhooks")
def create_hook(data: WebhookCreateIn, db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    for e in data.events:
        if e not in ALLOWED_EVENTS and e != "*":
            raise HTTPException(status_code=422, detail=f"Unsupported event: {e}")
    if not data.url.startswith("https://") and not data.url.startswith("http://localhost"):
        raise HTTPException(status_code=422, detail="Webhook URL must be https (localhost http allowed for dev).")
    h = Webhook(merchant_id=merchant.id, url=data.url, secret=secrets.token_urlsafe(24), events=json.dumps(data.events), active=data.active)
    db.add(h)
    db.commit()
    return {"success": True, "data": {"id": h.id, "url": h.url, "secret": h.secret, "events": data.events}}


@router.get("/webhooks")
def list_hooks(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    items = db.query(Webhook).filter(Webhook.merchant_id == merchant.id).all()
    out = []
    for h in items:
        try:
            ev = json.loads(h.events)
        except Exception:
            ev = []
        out.append({"id": h.id, "url": h.url, "events": ev, "active": h.active, "created_at": h.created_at})
    return {"success": True, "data": out}


@router.get("/webhooks/deliveries")
def list_deliveries(db: Session = Depends(get_db), merchant: Merchant = Depends(get_merchant)):
    items = db.query(WebhookDelivery).filter(WebhookDelivery.merchant_id == merchant.id).order_by(WebhookDelivery.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": d.id, "event_type": d.event_type, "status": d.status, "attempts": d.attempts, "last_error": d.last_error, "created_at": d.created_at} for d in items]}
