# Testing

Run: `python -m pytest backend/tests/test_payflow.py -q` (uses throwaway sqlite `test_payflow.db`).

Covers: fee math, state transitions, full payment flow with wallet credit, idempotent payment creation (double-click), duplicate refund dedupe, over-refund rejection, excessive withdrawal rejection, webhook signature + duplicate-event protection, RBAC (customer blocked from merchant APIs) and unauthenticated access.

E2E path exercised: register → login → create payment → confirm → webhook → transaction → balance → receipt → refund → withdrawal validation.
