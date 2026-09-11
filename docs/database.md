# Database

PostgreSQL (SQLite fallback for local dev without Docker). All tables in `backend/app/models/__init__.py`.

Tables: roles, users, user_sessions, email_tokens, merchants, merchant_documents, customers, payment_methods (tokenized refs only — never PAN/CVV), payment_providers, payments (unique merchant+idempotency_key), transactions, refunds (unique merchant+idempotency_key), invoices, invoice_items, payment_links, wallets, wallet_transactions (ledger), withdrawals, api_keys (sha256 hash stored), webhooks, webhook_deliveries (unique webhook+event), processed_events (dedupe), notifications, disputes, audit_logs.

Migrations: `backend/alembic/` — run `alembic upgrade head` (DATABASE_URL env). App also creates tables on startup for dev.
