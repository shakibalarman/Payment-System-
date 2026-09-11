"""Consistent API error envelope. Never expose internals."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(status: int, code: str, message: str):
    return JSONResponse(status_code=status, content={"success": False, "error": {"code": code, "message": message}})


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 409:
        code = "CONFLICT"
    elif exc.status_code == 429:
        code = "RATE_LIMITED"
    msg = str(exc.detail) if isinstance(exc.detail, str) else "Request failed."
    return error_response(exc.status_code, code, msg)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = exc.errors()
    msg = "; ".join(f"{'.'.join(map(str, e.get('loc', [])))}: {e.get('msg')}" for e in details[:3])
    return error_response(422, "VALIDATION_ERROR", msg or "Validation failed.")


async def unhandled_exception_handler(request: Request, exc: Exception):
    # Do NOT leak stack traces / db errors
    return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred.")
