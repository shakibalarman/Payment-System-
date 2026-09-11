# PayFlow — Full-Stack Payment Platform

Accept Payments. Get Paid Faster. A secure payment platform for businesses of every size.

## 1. Overview
Complete monorepo: public website, customer app, merchant dashboard, admin dashboard, REST API, KYC, mock/demo provider abstraction, idempotent payments, signed webhooks, wallet ledger, refunds, withdrawals, invoices, payment links, API keys, notifications, audit logs, RBAC, tests, Docker.

## 2. Architecture
See `docs/architecture.md`. `frontend/` (Next.js 14 + TanStack Query) talks to `backend/` (FastAPI) → PostgreSQL + Redis, fronted by Nginx in Docker.

## 3. Tech stack
Next.js, React, TypeScript, Tailwind, React Hook Form/Zod patterns, TanStack Query, Recharts · Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic · PostgreSQL · Redis · Docker/Compose/Nginx.

## 4. Prerequisites
Python 3.12+, Node 20+, Docker (optional but recommended for Postgres/Redis).

## 5. Installation
```bash
cp .env.example .env
pip install -r backend/requirements.txt
cd frontend && npm install
```

## 6. Environment variables
All documented in `.env.example`: DATABASE_URL, JWT_SECRET, JWT_ALGORITHM, ACCESS/REFRESH expiries, REDIS_URL, PAYMENT_PROVIDER_SECRET/PUBLIC_KEY/DEFAULT, PLATFORM_FEE_PERCENT, SMTP_*, FRONTEND_URL, ENV. Also `.env.development` / `.env.test` provided. Never commit real secrets.

## 7. Database setup
Docker: `docker compose up postgres redis`. Local without Docker: default `sqlite:///./payflow.db` works out of the box.

## 8. Migration
```bash
alembic -c backend/alembic.ini upgrade head
```
(Tables also auto-create on backend startup for dev.)

## 9. Seed data (dev only)
```bash
python -m backend.seed
```
Accounts: `admin@payflow.local` / `Admin1234` (admin), `merchant@payflow.local` / `Merchant123` (merchant, KYC approved), `customer@payflow.local` / `Customer123` (customer).

## 10. Running backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```
Docs: http://localhost:8000/api/docs

## 11. Running frontend
```bash
cd frontend && npm run dev
```
App: http://localhost:3000

## 12. Docker setup
```bash
docker compose up
```
Starts postgres, redis, backend (:8000), frontend (:3000), nginx (:80).

## 13. Testing
```bash
python -m pytest backend/tests/test_payflow.py -q
```
Covers fees, state transitions, idempotent payments, duplicate webhooks/refunds, withdrawal limits, RBAC. See `docs/testing.md`.

## 14. API documentation
FastAPI OpenAPI at `/api/docs`; summary in `docs/api.md`.

## 15. Payment provider configuration
Implement `PaymentProvider` (`backend/app/services/providers_base.py`), register in `get_provider()`. Set `PAYMENT_PROVIDER_*` env vars. Local dev uses `MockPaymentProvider` — always labeled DEMO/MOCK, never real money.

## 16. Security considerations
See `docs/security.md`: no card storage, hashed secrets, signed webhooks, idempotency, RBAC + ownership checks, rate limits, safe error envelope.

## 17. Production deployment notes
See `docs/deployment.md`.

## Completed features
Auth (register/login/refresh/logout/verify/forgot/reset) · roles + RBAC · merchants + KYC + admin approval · payments + checkout + mock provider · transactions with search/filter/pagination · refunds (full/partial, deduped) · wallet ledger · withdrawals + admin processing · invoices with pay links · payment links · API keys · webhooks + delivery logs + retries · notifications · disputes · providers mgmt · platform fees per merchant · audit logs · receipts · responsive + accessible UI · tests · Docker · docs.

## Known limitations
- Mock provider only; no live-money provider wired (by design — plug in via the abstraction).
- Email sending is stubbed (tokens returned in dev); wire SMTP worker for production.
- SQLite fallback lacks true row-level locking (Postgres used in Docker/prod).
- Alembic baseline is a marker; run `--autogenerate` for schema diffs in production flows.
