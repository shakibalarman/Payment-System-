from fastapi import APIRouter
from backend.app.api.v1 import auth, payments, business, money, developer, merchant, admin, public, notifications, customer

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(payments.router)
router.include_router(business.router)
router.include_router(money.router)
router.include_router(developer.router)
router.include_router(merchant.router)
router.include_router(admin.router)
router.include_router(public.router)
router.include_router(notifications.router)
router.include_router(customer.router)
