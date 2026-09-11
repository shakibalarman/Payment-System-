"""Background delivery of merchant webhooks with retries (Redis optional)."""
import json
import time
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models import Webhook, WebhookDelivery
from backend.app.services.common import send_delivery

MAX_ATTEMPTS = 5


def deliver_pending(limit: int = 20):
    db: Session = SessionLocal()
    try:
        items = db.query(WebhookDelivery).filter(WebhookDelivery.status.in_(["PENDING", "RETRY"])).order_by(WebhookDelivery.created_at.asc()).limit(limit).all()
        for d in items:
            hook = db.query(Webhook).filter(Webhook.id == d.webhook_id).first()
            if not hook or not hook.active:
                d.status = "CANCELLED"
                continue
            d.attempts += 1
            ok, err = send_delivery(d.payload, hook.url, hook.secret)
            if ok:
                d.status = "DELIVERED"
                d.last_error = ""
            else:
                d.last_error = err
                d.status = "RETRY" if d.attempts < MAX_ATTEMPTS else "FAILED"
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    while True:
        deliver_pending()
        time.sleep(10)
