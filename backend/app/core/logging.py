"""Structured logging without sensitive data."""
import logging
import sys
import uuid
from fastapi import Request

logger = logging.getLogger("payflow")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s req=%(request_id)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    adapter = logging.LoggerAdapter(logger, {"request_id": rid})
    request.state.log = adapter
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    adapter.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response
