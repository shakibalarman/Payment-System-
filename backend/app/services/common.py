"""Shared helpers: fees, audit, notifications, webhook fan-out."""
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone

import httpx

from backend.app.models import AuditLog, Notification, Webhook, WebhookDelivery


def calc_fee(amount_minor: int, fee_percent: float) -> tuple[int, int]:
    fee = int(round(amount_minor * float(fee_percent) / 100.0))
    return fee, amount_minor - fee


def audit(db, *, actor_id: str | None, action: str, resource: str = "", resource_id: str = "", ip: str = "", meta: dict | None = None):
    db.add(AuditLog(actor_id=actor_id, action=action, resource=resource, resource_id=resource_id, ip_address=ip, meta=json.dumps(meta or {})))


def notify(db, *, user_id: str, type: str, title: str, body: str = ""):
    db.add(Notification(user_id=user_id, type=type, title=title, body=body))


def webhook_sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def fanout(db, *, merchant_id: str, event_type: str, payload: dict) -> list[str]:
    """Create delivery rows for matching webhooks. Actual HTTP send happens in worker/background."""
    hooks = db.query(Webhook).filter(Webhook.merchant_id == merchant_id, Webhook.active == True).all()  # noqa: E712
    ids: list[str] = []
    body = json.dumps({"event_id": payload.get("event_id"), "type": event_type, "data": payload, "created_at": datetime.now(timezone.utc).isoformat()})
    for h in hooks:
        try:
            events = json.loads(h.events) if h.events else []
        except Exception:
            events = []
        if event_type not in events and "*" not in events:
            continue
        sig = webhook_sign(body, h.secret)
        d = WebhookDelivery(webhook_id=h.id, merchant_id=merchant_id, event_id=payload.get("event_id", secrets.token_hex(8)), event_type=event_type, payload=body, status="PENDING")
        db.add(d)
        db.flush()
        ids.append(d.id)
    return ids


def send_delivery(payload: str, url: str, secret: str, timeout: float = 8.0) -> tuple[bool, str]:
    sig = webhook_sign(payload, secret)
    try:
        r = httpx.post(url, content=payload, headers={"Content-Type": "application/json", "X-PayFlow-Signature": sig, "X-PayFlow-Event": "event"}, timeout=timeout)
        if 200 <= r.status_code < 300:
            return True, ""
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)[:500]
