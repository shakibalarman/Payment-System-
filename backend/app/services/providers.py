"""Mock provider for local development/testing ONLY. Clearly DEMO, never real money."""
import uuid
from backend.app.services.providers_base import (
    PaymentProvider, ProviderPaymentResult, ProviderRefundResult,
)
import hmac, hashlib


class MockPaymentProvider(PaymentProvider):
    code = "mock"
    _store: dict = {}

    def create_payment(self, *, amount, currency, description, customer_email, meta):
        ref = f"mock_{uuid.uuid4().hex[:12]}"
        self._store[ref] = {"status": "PROCESSING", "amount": amount, "currency": currency}
        return ProviderPaymentResult(provider_ref=ref, status="PROCESSING", raw={"demo": True})

    def get_payment(self, provider_ref: str) -> ProviderPaymentResult:
        rec = self._store.get(provider_ref, {"status": "PROCESSING"})
        return ProviderPaymentResult(provider_ref=provider_ref, status=rec["status"], raw={"demo": True})

    def refund_payment(self, provider_ref: str, amount=None) -> ProviderRefundResult:
        return ProviderRefundResult(provider_ref=f"ref_{uuid.uuid4().hex[:10]}", status="COMPLETED", raw={"demo": True})

    def verify_webhook(self, raw_body: bytes, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


def get_provider(code: str) -> PaymentProvider:
    if code == "mock":
        return MockPaymentProvider()
    # Future: stripe, sslcommerz, bkash... registered here without touching core logic.
    return MockPaymentProvider()
