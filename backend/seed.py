"""Development-only seed data. Never use real credentials. Run: python -m backend.seed"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./payflow.db")
from backend.app.core.database import SessionLocal, engine
from backend.app.models import Base, User, Merchant, Wallet, PaymentProvider, Role
from backend.app.core.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    for r in ["customer", "merchant", "admin"]:
        if not db.query(Role).filter(Role.name == r).first():
            db.add(Role(name=r, description=r))
    for code, name in [("mock", "Mock Provider (DEMO)"), ("stripe", "Stripe"), ("sslcommerz", "SSLCommerz")]:
        if not db.query(PaymentProvider).filter(PaymentProvider.code == code).first():
            db.add(PaymentProvider(code=code, name=name, enabled=(code == "mock")))

    def ensure(email, password, role, name):
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(email=email, password_hash=hash_password(password), role=role, full_name=name, is_verified=True)
            db.add(u)
            db.flush()
        return u

    admin = ensure("admin@payflow.local", "Admin1234", "admin", "PayFlow Admin")
    mu = ensure("merchant@payflow.local", "Merchant123", "merchant", "Demo Merchant")
    cu = ensure("customer@payflow.local", "Customer123", "customer", "Demo Customer")
    m = db.query(Merchant).filter(Merchant.user_id == mu.id).first()
    if not m:
        m = Merchant(user_id=mu.id, business_name="Demo Store", business_type="Retail", owner_name="Demo Merchant", email=mu.email, kyc_status="APPROVED")
        db.add(m)
        db.flush()
    else:
        m.kyc_status = "APPROVED"
    if not db.query(Wallet).filter(Wallet.merchant_id == m.id).first():
        db.add(Wallet(merchant_id=m.id, available=0, pending=0))
    db.commit()
    print("Seeded: admin@payflow.local/Admin1234, merchant@payflow.local/Merchant123, customer@payflow.local/Customer123")
finally:
    db.close()
