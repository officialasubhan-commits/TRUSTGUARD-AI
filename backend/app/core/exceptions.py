"""
Centralised exception classes and HTTP exception handlers.

All custom exceptions live here so that:
  - API endpoints raise typed exceptions, not raw HTTP exceptions.
  - The exception handlers in main.py convert them to consistent JSON responses.
  - Stack traces are NEVER sent to the client — only safe messages.

Usage:
    from app.core.exceptions import InvalidURLError, SSRFBlockedError
    raise InvalidURLError("URL contains a private IP address")
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

# ------------------------------------------------------------------ #
# Custom exception hierarchy                                           #
# ------------------------------------------------------------------ #


class TrustGuardBaseError(Exception):
    """Base class for all TrustGuard application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(TrustGuardBaseError):
    """Raised when an operation request is malformed or invalid."""

    status_code = 400
    error_code = "BAD_REQUEST"


class InvalidURLError(TrustGuardBaseError):
    """Raised when a submitted URL fails validation (format, scheme, length)."""

    status_code = 422
    error_code = "INVALID_URL"


class SSRFBlockedError(TrustGuardBaseError):
    """
    Raised when a submitted URL resolves to a private / loopback / reserved
    IP address — blocked to prevent Server-Side Request Forgery.
    """

    status_code = 422
    error_code = "SSRF_BLOCKED"


class RateLimitExceededError(TrustGuardBaseError):
    """Raised when a client exceeds the configured rate limit."""

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class UnauthorizedError(TrustGuardBaseError):
    """Raised when a protected endpoint is accessed without a valid JWT."""

    status_code = 401
    error_code = "UNAUTHORIZED"


class InvalidCredentialsError(TrustGuardBaseError):
    """Raised when email or password is incorrect."""

    status_code = 401
    error_code = "INVALID_CREDENTIALS"

    def __init__(self, message: str = "Invalid email or password.") -> None:
        super().__init__(message)


class UserAlreadyExistsError(TrustGuardBaseError):
    """Raised when registering an email that already exists."""

    status_code = 409
    error_code = "USER_ALREADY_EXISTS"

    def __init__(self, message: str = "A user with this email address already exists.") -> None:
        super().__init__(message)


class EmailNotConfirmedError(TrustGuardBaseError):
    """Raised when login is attempted on an account requiring email verification."""

    status_code = 403
    error_code = "EMAIL_NOT_CONFIRMED"

    def __init__(self, message: str = "Email verification required before signing in.") -> None:
        super().__init__(message)


class TokenExpiredError(TrustGuardBaseError):
    """Raised when a JWT access token has expired."""

    status_code = 401
    error_code = "TOKEN_EXPIRED"

    def __init__(
        self, message: str = "Authentication token has expired. Please log in again or refresh."
    ) -> None:
        super().__init__(message)


class InvalidTokenError(TrustGuardBaseError):
    """Raised when a JWT is malformed, has invalid signature or claims."""

    status_code = 401
    error_code = "INVALID_TOKEN"

    def __init__(self, message: str = "Invalid authentication token.") -> None:
        super().__init__(message)


class ForbiddenError(TrustGuardBaseError):
    """Raised when an authenticated user tries to access another user's data."""

    status_code = 403
    error_code = "FORBIDDEN"


class ScanNotFoundError(TrustGuardBaseError):
    """Raised when a scan_id does not exist in the database."""

    status_code = 404
    error_code = "SCAN_NOT_FOUND"


class NotFoundError(TrustGuardBaseError):
    """Raised when a requested resource is not found."""

    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(TrustGuardBaseError):
    """Raised when an operation conflicts with existing resource state (e.g. duplicate)."""

    status_code = 409
    error_code = "CONFLICT"


class DatabaseError(TrustGuardBaseError):
    """Raised when a database operation fails unexpectedly."""

    status_code = 503
    error_code = "DATABASE_ERROR"


class ExternalServiceError(TrustGuardBaseError):
    """
    Raised when an external API call (VirusTotal, URLhaus) fails in a way
    that cannot be handled gracefully (e.g., unexpected schema change).
    Normal timeouts and 429s are caught inside each service and return
    available=False rather than raising this.
    """

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


# ------------------------------------------------------------------ #
# FastAPI exception handlers                                           #
# These are registered in main.py via app.add_exception_handler().    #
# ------------------------------------------------------------------ #


def _error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    """Build a consistent JSON error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
            }
        },
    )


async def trustguard_exception_handler(
    request: Request,
    exc: TrustGuardBaseError,
) -> JSONResponse:
    """Catch all TrustGuard domain exceptions and return a safe JSON response."""
    return _error_response(exc.status_code, exc.error_code, exc.message)


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch Pydantic / FastAPI RequestValidationError and return a
    readable message without exposing internal field paths.
    """
    from fastapi.exceptions import RequestValidationError

    if isinstance(exc, RequestValidationError):
        # Extract only the first error message to keep response concise
        errors = exc.errors()
        if errors:
            first = errors[0]
            field = " → ".join(str(loc) for loc in first.get("loc", []))
            msg = first.get("msg", "Validation error")
            detail = f"{field}: {msg}" if field else msg
        else:
            detail = "Invalid request body."
        return _error_response(422, "VALIDATION_ERROR", detail)
    return _error_response(422, "VALIDATION_ERROR", "Invalid request.")


async def not_found_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a JSON 404 instead of the default HTML page."""
    return _error_response(404, "NOT_FOUND", f"Route '{request.url.path}' does not exist.")


async def method_not_allowed_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a JSON 405 instead of the default HTML page."""
    return _error_response(
        405,
        "METHOD_NOT_ALLOWED",
        f"HTTP method '{request.method}' is not allowed for '{request.url.path}'.",
    )


async def generic_server_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all for any unhandled exception.

    IMPORTANT: The traceback is logged server-side but NEVER sent to the client.
    """
    import logging
    import traceback

    log = logging.getLogger(__name__)
    log.error(
        "Unhandled exception on %s %s:\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return _error_response(500, "INTERNAL_ERROR", "An internal server error occurred.")
