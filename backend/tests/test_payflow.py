"""Unit + integration tests for critical payment edge cases."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_payflow.db"
import hashlib, hmac, json

from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal, engine
from backend.app.models import Base
from backend.app.main import app
from backend.app.services.common import calc_fee, webhook_sign
from backend.app.models import can_transition_payment, PaymentStatus

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app, raise_server_exceptions=False)


def register(email, pw, role, name="T User"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": pw, "full_name": name, "role": role})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def auth(email, pw):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def test_fee_and_transitions():
    fee, net = calc_fee(500000, 1.5)
    assert fee == 7500 and net == 492500
    assert can_transition_payment(PaymentStatus.PENDING, PaymentStatus.PROCESSING)
    assert can_transition_payment(PaymentStatus.PROCESSING, PaymentStatus.SUCCESS)
    assert not can_transition_payment(PaymentStatus.SUCCESS, PaymentStatus.PENDING)


def test_full_payment_flow_idempotent():
    register("m1@example.com", "Merchant123", "merchant", "M One")
    m = auth("m1@example.com", "Merchant123")
    h = {"Authorization": f"Bearer {m['access_token']}", "Idempotency-Key": "pay-key-1"}
    r1 = client.post("/api/v1/payments", json={"amount": 500000, "currency": "BDT", "description": "Website Development", "customer_email": "c1@example.com"}, headers=h)
    assert r1.status_code == 200, r1.text
    pid = r1.json()["data"]["id"]
    # Case 1: double-click Pay with same idempotency key -> ONE payment
    r2 = client.post("/api/v1/payments", json={"amount": 500000, "currency": "BDT", "description": "Website Development", "customer_email": "c1@example.com"}, headers=h)
    assert r2.json()["data"]["id"] == pid
    # confirm success
    r3 = client.post(f"/api/v1/payments/{pid}/confirm", json={"outcome": "SUCCESS", "payment_method": "card"}, headers={"Authorization": f"Bearer {m['access_token']}"})
    assert r3.json()["data"]["status"] == "SUCCESS"
    # wallet credited
    w = client.get("/api/v1/wallet", headers={"Authorization": f"Bearer {m['access_token']}"}).json()["data"]
    assert w["available"] > 0
    # Case 5: duplicate refund -> single refund
    rh = {"Authorization": f"Bearer {m['access_token']}", "Idempotency-Key": "ref-key-1"}
    f1 = client.post("/api/v1/refunds", json={"payment_id": pid, "amount": 10000, "reason": "test"}, headers=rh)
    assert f1.status_code == 200, f1.text
    f2 = client.post("/api/v1/refunds", json={"payment_id": pid, "amount": 10000, "reason": "test"}, headers=rh)
    assert f2.json()["data"]["id"] == f1.json()["data"]["id"]
    # over-refund rejected
    f3 = client.post("/api/v1/refunds", json={"payment_id": pid, "amount": 999999999}, headers={"Authorization": f"Bearer {m['access_token']}"})
    assert f3.status_code in (409, 422)
    # Case 7: excessive withdrawal rejected
    wd = client.post("/api/v1/withdrawals", json={"amount": 99999999999, "destination": "bank-123"}, headers={"Authorization": f"Bearer {m['access_token']}"})
    assert wd.status_code == 422


def test_webhook_security_and_dedupe():
    from backend.app.core.config import get_settings
    secret = get_settings().payment_provider_secret
    body = json.dumps({"event_id": "evt-dedupe-1", "provider_ref": "x", "status": "SUCCESS"}).encode()
    sig = hmac.new(secret.encode(), body, __import__("hashlib").sha256).hexdigest()
    r1 = client.post("/api/v1/webhooks/provider/mock", content=body, headers={"X-Provider-Signature": sig, "X-Event-Id": "evt-dedupe-1", "Content-Type": "application/json"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/webhooks/provider/mock", content=body, headers={"X-Provider-Signature": sig, "X-Event-Id": "evt-dedupe-1", "Content-Type": "application/json"})
    assert r2.json()["data"].get("duplicate") is True
    bad = client.post("/api/v1/webhooks/provider/mock", content=body, headers={"X-Provider-Signature": "bad", "X-Event-Id": "evt-x", "Content-Type": "application/json"})
    assert bad.status_code == 401
    assert webhook_sign("a", "k") == hmac.new(b"k", b"a", hashlib.sha256).hexdigest()


def test_rbac_and_ownership():
    register("cust9@example.com", "Customer123", "customer", "C Nine")
    c = auth("cust9@example.com", "Customer123")
    r = client.get("/api/v1/payments", headers={"Authorization": f"Bearer {c['access_token']}"})
    assert r.status_code == 403  # customer cannot access merchant resources
    # unauthenticated
    assert client.get("/api/v1/payments").status_code in (401, 403)
