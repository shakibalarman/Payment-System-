"""Pydantic v2 schemas for all resources."""
from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar
from pydantic import BaseModel, EmailStr, Field, field_validator

T = TypeVar("T")


class Ok(BaseModel):
    success: bool = True
    data: Any = None


class Paged(BaseModel):
    success: bool = True
    data: Any = None
    pagination: dict = {}


# ---------- Auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: Literal["customer", "merchant"] = "customer"

    @field_validator("password")
    @classmethod
    def strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit.")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailIn(BaseModel):
    token: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    full_name: str
    is_verified: bool

    model_config = {"from_attributes": True}


# ---------- Merchants / KYC ----------
class MerchantProfileIn(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)
    business_type: str = ""
    owner_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    trade_license: str = ""
    tin: str = ""
    nid_passport: str = ""
    bank_account: str = ""
    bank_name: str = ""


class KycDecisionIn(BaseModel):
    approve: bool
    reason: str = ""


# ---------- Payments ----------
class PaymentCreateIn(BaseModel):
    amount: int = Field(gt=0, le=100_000_000_00, description="Amount in minor units")
    currency: str = Field(default="BDT", min_length=3, max_length=8)
    description: str = Field(default="", max_length=1000)
    customer_email: EmailStr | str = ""
    payment_method: str = ""
    invoice_id: str | None = None
    payment_link_id: str | None = None
    provider_code: str = "mock"


class PaymentConfirmIn(BaseModel):
    # Demo/mock only: simulate provider outcome. Real providers use webhooks.
    outcome: Literal["SUCCESS", "FAILED"] = "SUCCESS"
    payment_method: str = "card"


class PaymentOut(BaseModel):
    id: str
    amount: int
    currency: str
    description: str
    status: str
    provider_code: str
    customer_email: str
    fee_amount: int = 0
    net_amount: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Refunds ----------
class RefundCreateIn(BaseModel):
    payment_id: str
    amount: int | None = Field(default=None, gt=0)
    reason: str = ""


# ---------- Invoices ----------
class InvoiceItemIn(BaseModel):
    name: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)


class InvoiceCreateIn(BaseModel):
    customer_name: str
    customer_email: str
    items: list[InvoiceItemIn] = Field(min_length=1)
    tax: int = 0
    discount: int = 0
    due_date: datetime | None = None
    notes: str = ""
    currency: str = "BDT"


# ---------- Payment links ----------
class PaymentLinkCreateIn(BaseModel):
    amount: int = Field(gt=0)
    currency: str = "BDT"
    description: str = ""
    expires_at: datetime | None = None


# ---------- Withdrawals ----------
class WithdrawalCreateIn(BaseModel):
    amount: int = Field(gt=0)
    destination: str = Field(min_length=4)


# ---------- API keys / webhooks ----------
class ApiKeyCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class WebhookCreateIn(BaseModel):
    url: str
    events: list[str] = Field(default_factory=lambda: ["payment.success"])
    active: bool = True


# ---------- Misc ----------
class PaymentMethodIn(BaseModel):
    method_type: str
    brand: str = ""
    last4: str = ""
    provider_token: str = ""
    is_default: bool = False


class NotifyOut(BaseModel):
    id: str
    type: str
    title: str
    body: str
    read: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
