"""Payment provider abstraction. Real providers plug in here."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderPaymentResult:
    provider_ref: str
    status: str  # PENDING | PROCESSING | SUCCESS | FAILED
    redirect_url: str = ""
    raw: dict | None = None


@dataclass
class ProviderRefundResult:
    provider_ref: str
    status: str
    raw: dict | None = None


class PaymentProvider(ABC):
    code: str = "base"

    @abstractmethod
    def create_payment(self, *, amount: int, currency: str, description: str, customer_email: str, meta: dict) -> ProviderPaymentResult:
        ...

    @abstractmethod
    def get_payment(self, provider_ref: str) -> ProviderPaymentResult:
        ...

    @abstractmethod
    def refund_payment(self, provider_ref: str, amount: int | None) -> ProviderRefundResult:
        ...

    @abstractmethod
    def verify_webhook(self, raw_body: bytes, signature: str, secret: str) -> bool:
        ...

    def handle_webhook(self, payload: dict) -> dict:
        return payload
