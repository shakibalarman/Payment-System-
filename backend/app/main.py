"""PayFlow FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.v1.router import router as v1
from backend.app.core.errors import http_exception_handler, validation_exception_handler, unhandled_exception_handler
from backend.app.core.logging import request_id_middleware
from backend.app.core.config import get_settings
from backend.app.models import Base
from backend.app.core.database import engine

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # dev convenience; production uses alembic
    # ensure base providers/roles exist
    from backend.app.core.database import SessionLocal
    from backend.app.models import PaymentProvider, Role
    db = SessionLocal()
    try:
        for code, name in [("mock", "Mock Provider (DEMO)"), ("stripe", "Stripe"), ("sslcommerz", "SSLCommerz")]:
            if not db.query(PaymentProvider).filter(PaymentProvider.code == code).first():
                db.add(PaymentProvider(code=code, name=name, enabled=(code == "mock")))
        for r in ["customer", "merchant", "admin"]:
            if not db.query(Role).filter(Role.name == r).first():
                db.add(Role(name=r, description=r))
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="PayFlow API", version="1.0.0", description="Secure payment platform. Demo provider = MOCK (no real money).", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)

app.middleware("http")(request_id_middleware)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url, "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(v1)


@app.get("/api/health")
def health():
    return {"success": True, "data": {"status": "ok", "service": "payflow"}}
