# Payments

States: PENDING → PROCESSING → SUCCESS | FAILED | CANCELLED; SUCCESS → PARTIALLY_REFUNDED → REFUNDED. Enforced in `can_transition_payment`.

- Provider abstraction: `backend/app/services/providers_base.py` (`PaymentProvider` interface) + `providers.py` (`MockPaymentProvider`, `get_provider`). Add Stripe/SSLCommerz/bKash by implementing the interface and registering in `get_provider` — core logic unchanged.
- Idempotency: unique (merchant, idempotency_key) on payments and refunds; repeat submits return the original.
- Fees: `calc_fee` with per-merchant `fee_percent` (admin-configurable); each payment snapshots fee/net so history is immutable.
- Edge cases covered: double-click pay, duplicate webhook (processed_events), browser-close (backend-owned state), frontend-outage (receipt re-queryable), double refund, provider downtime (no false success), concurrent withdrawals (balance check + row lock + ledger).
- Mock provider is DEMO-only and labeled as such in the UI.
