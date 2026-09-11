# Deployment

- `docker compose up` starts postgres, redis, backend, frontend, nginx.
- Production: set JWT_SECRET, DATABASE_URL (postgres), REDIS_URL, provider keys, SMTP vars. Run `alembic upgrade head`. Serve backend behind nginx with TLS. Never commit `.env`.
- Health: GET /api/health. Logs include request IDs; no sensitive data logged.
