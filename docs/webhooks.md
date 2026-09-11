# Webhooks

Inbound (provider → PayFlow): POST /api/v1/webhooks/provider/{code} with `X-Provider-Signature` (HMAC-SHA256 of raw body) and `X-Event-Id`. Verified, deduped via `processed_events`, applied idempotently.

Outbound (PayFlow → merchant): merchant registers URL + events. Each event gets `event_id`, HMAC-SHA256 signature (`X-PayFlow-Signature`), delivery rows with attempts/status, retry up to 5 times via worker (`python -m backend.app.workers.webhooks` loop or scheduler).

Events: payment.created, payment.success, payment.failed, payment.refunded, payment.cancelled, withdrawal.completed.
