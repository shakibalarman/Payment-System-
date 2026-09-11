# Security

- bcrypt password hashing (72-byte cap), email verification, access (30m) + refresh (7d) JWT, revocable sessions.
- RBAC: customer/merchant/admin enforced server-side; every merchant query filters by merchant_id (ownership at service layer).
- No raw card storage; API secrets hashed (sha256), shown once; webhook HMAC verification; idempotency; rate limiting on auth; consistent error envelope (no stack traces/secrets).
- All secrets from env (.env.example documents every variable). CORS restricted to frontend origin.
