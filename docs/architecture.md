# Architecture

Monorepo: `frontend/` (Next.js 14, React Query) + `backend/` (FastAPI, SQLAlchemy) + Postgres + Redis + Nginx.

- All APIs under `/api/v1/`. Frontend never decides payment success; backend + provider webhooks do.
- Payment flow: merchant creates payment (idempotency key) → provider abstraction (`PaymentProvider`) → customer checkout → backend confirms → transaction + wallet ledger + receipt + webhook fan-out + notification.
- Money in integer minor units. Wallet changes only via ledger entries.
- Redis optional; webhook retries run via worker (`backend/app/workers/webhooks.py`).
