"""
Security utilities — SSRF protection and JWT verification stubs.

This module contains two independent groups of functionality:

1. SSRF Guard — validates that a user-submitted URL resolves to a
   public IP address before any outbound network call is made by the backend.
   This prevents attackers from using TrustGuard as a proxy to scan
   internal services.

2. JWT Verification — a FastAPI dependency that validates Supabase-issued
   Bearer tokens on protected endpoints.  Full implementation comes in
   Prompt 03 (Authentication). The stub here is wired into routing now
   so that endpoint signatures are already correct.

Usage:
    # In an endpoint that requires authentication:
    from app.core.security import get_current_user
    async def my_endpoint(user=Depends(get_current_user)): ...

    # Before any outbound HTTP call:
    from app.core.security import validate_url_for_ssrf
    await validate_url_for_ssrf(url)
"""

from __future__ import annotations

import ipaddress
import logging
import socket
import time
import uuid
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import (
    ForbiddenError,
    InvalidTokenError,
    InvalidURLError,
    SSRFBlockedError,
    TokenExpiredError,
    UnauthorizedError,
)

log = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Private / reserved IP ranges blocked by the SSRF guard              #
# ------------------------------------------------------------------ #

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),  # RFC 1918 private
    ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918 private
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback (IPv4)
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local (APIPA)
    ipaddress.ip_network("0.0.0.0/8"),  # "This" network
    ipaddress.ip_network("100.64.0.0/10"),  # Shared address space (RFC 6598)
    ipaddress.ip_network("192.0.0.0/24"),  # IETF protocol assignments
    ipaddress.ip_network("198.18.0.0/15"),  # Benchmarking (RFC 2544)
    ipaddress.ip_network("198.51.100.0/24"),  # Documentation (TEST-NET-2)
    ipaddress.ip_network("203.0.113.0/24"),  # Documentation (TEST-NET-3)
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6 equivalents
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

_ALLOWED_SCHEMES = {"http", "https"}


def _is_private_ip(ip_str: str) -> bool:
    """
    Return True if the given IP string falls within any blocked network.

    Handles both IPv4 and IPv6. Returns True (blocked) on any parse error.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in _BLOCKED_NETWORKS)
    except ValueError:
        # Unparseable IP — treat as blocked to be safe
        return True


async def validate_url_for_ssrf(url: str) -> str:
    """
    Validate that a URL is safe to use as the target of an outbound
    backend HTTP request.  Raises an exception if the URL is blocked.

    Checks performed (in order):
      1. URL length within limit.
      2. Scheme is http or https.
      3. Hostname is present.
      4. Hostname resolves via DNS.
      5. All resolved IP addresses are public (not private/loopback/reserved).

    Args:
        url: The raw URL string submitted by the user.

    Returns:
        The validated URL string (unchanged).

    Raises:
        InvalidURLError: If the URL is malformed, too long, or has a bad scheme.
        SSRFBlockedError: If the URL resolves to a private or reserved IP.
    """
    # 1. Length guard
    if len(url) > settings.URL_MAX_LENGTH:
        raise InvalidURLError(
            f"URL exceeds maximum allowed length of {settings.URL_MAX_LENGTH} characters."
        )

    # 2. Parse and validate scheme
    try:
        parsed = urlparse(url)
    except Exception:
        raise InvalidURLError("URL could not be parsed.")

    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise InvalidURLError(
            f"URL scheme '{scheme}' is not allowed. Only 'http' and 'https' are permitted."
        )

    # 3. Hostname must be present
    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError("URL does not contain a valid hostname.")

    # 4 & 5. DNS resolution + IP check
    try:
        # getaddrinfo returns all address records for the hostname
        addr_infos = await _resolve_hostname(hostname)
    except socket.gaierror as exc:
        raise InvalidURLError(f"Hostname '{hostname}' could not be resolved: {exc}")
    except Exception as exc:
        raise InvalidURLError(f"Hostname resolution failed: {exc}")

    for _family, _type, _proto, _canon, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        if _is_private_ip(ip_str):
            log.warning(
                "SSRF blocked: hostname '%s' resolved to private IP '%s'",
                hostname,
                ip_str,
            )
            raise SSRFBlockedError(
                f"The URL hostname '{hostname}' resolves to a private or reserved IP address "
                f"and cannot be analysed for security reasons."
            )

    return url


async def _resolve_hostname(hostname: str) -> list:
    """
    Resolve a hostname to address info using the standard library socket.
    Wrapped in a helper so it can be easily mocked in tests.

    Note: socket.getaddrinfo is blocking; for a production system we would
    use asyncio's getaddrinfo. For hackathon scale this is acceptable.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: socket.getaddrinfo(hostname, None),
    )


# ------------------------------------------------------------------ #
# JWT / Authentication helpers                                         #
# ------------------------------------------------------------------ #

_bearer_scheme = HTTPBearer(auto_error=False)

# In-memory token verification cache: {token_str: (expires_at_timestamp, AuthenticatedUser)}
_verified_token_cache: Dict[str, Tuple[float, AuthenticatedUser]] = {}


class AuthenticatedUser:
    """
    Represents a verified Supabase user extracted from a validated JWT.
    """

    def __init__(
        self,
        user_id: uuid.UUID,
        email: Optional[str] = None,
        role: str = "user",
        token: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.token = token

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"

    def __repr__(self) -> str:
        return f"<AuthenticatedUser id={self.user_id} email={self.email} role={self.role}>"


def verify_jwt_token(token: str) -> AuthenticatedUser:
    """
    Validates a Supabase JWT token against signature, expiration, and audience claims.
    Supports Supabase secret and JWKS verification, with fallback to test secret.

    Raises:
        TokenExpiredError: If the token expiration time (exp) has passed.
        InvalidTokenError: If the token signature is invalid, malformed, or missing sub.
    """
    if not token or not isinstance(token, str):
        raise InvalidTokenError("Missing or malformed token.")

    t_start = time.perf_counter()
    now_ts = time.time()

    # Check cache first for rapid verification (<0.01ms)
    cached = _verified_token_cache.get(token)
    if cached:
        exp_ts, cached_user = cached
        if now_ts < exp_ts:
            duration_ms = (time.perf_counter() - t_start) * 1000
            log.debug(
                "[TIMING] Auth token validation (cache hit): duration=%.2fms user_id=%s role=%s",
                duration_ms,
                cached_user.user_id,
                cached_user.role,
            )
            return cached_user
        else:
            del _verified_token_cache[token]

    secret = settings.SUPABASE_JWT_SECRET
    if not secret or secret.startswith("your-") or len(secret) < 32:
        secret = "trustguard-test-jwt-secret-key-32chars-minimum!"

    # Supabase signs HMAC-SHA256 JWTs with the base64-decoded binary bytes of SUPABASE_JWT_SECRET.
    # We test decoded binary bytes first, then fallback to literal string secret.
    candidate_secrets = []
    if secret:
        try:
            import base64
            decoded_bytes = base64.b64decode(secret, validate=True)
            if len(decoded_bytes) >= 32:
                candidate_secrets.append(decoded_bytes)
        except Exception:
            pass
        candidate_secrets.append(secret)

    payload = None
    decode_error = None
    for cand in candidate_secrets:
        try:
            payload = jwt.decode(
                token,
                cand,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": True},
                audience=["authenticated", "anon"],
            )
            break
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Authentication token has expired. Please log in again.")
        except jwt.PyJWTError as err:
            decode_error = err
            continue

    if payload is None:
        # In test / dev environments, check if the client can verify via Supabase Auth API
        from app.database import connection

        if connection.supabase_client is not None and settings.supabase_configured:
            try:
                res = connection.supabase_client.auth.get_user(token)
                if res and res.user:
                    u_id = uuid.UUID(res.user.id)
                    u_email = res.user.email
                    u_role = (
                        res.user.app_metadata.get("role", "user")
                        if res.user.app_metadata
                        else "user"
                    )
                    user = AuthenticatedUser(user_id=u_id, email=u_email, role=u_role, token=token)
                    # Cache user validation for 120s to avoid repeated network hops
                    _verified_token_cache[token] = (now_ts + 120, user)
                    duration_ms = (time.perf_counter() - t_start) * 1000
                    log.info(
                        "[TIMING] Auth token validation (remote auth.get_user): duration=%.2fms user_id=%s role=%s",
                        duration_ms,
                        u_id,
                        u_role,
                    )
                    return user
            except Exception as sb_err:
                log.warning("Supabase get_user verification failed: %s", sb_err)

        log.warning("JWT verification error: %s", decode_error)
        raise InvalidTokenError("Invalid authentication token.")

    # Validate subject (User UUID)
    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token payload missing subject identifier.")

    try:
        user_uuid = uuid.UUID(str(sub))
    except ValueError:
        raise InvalidTokenError("Token subject is not a valid UUID.")

    email = payload.get("email")
    # Extract role from app_metadata or claim
    app_meta = payload.get("app_metadata", {})
    role = app_meta.get("role") or payload.get("role", "user")

    user = AuthenticatedUser(
        user_id=user_uuid,
        email=email,
        role=str(role),
        token=token,
    )
    # Cache for either remaining token validity or max 300 seconds
    exp_claim = payload.get("exp", now_ts + 300)
    cache_until = min(exp_claim, now_ts + 300)
    _verified_token_cache[token] = (cache_until, user)

    duration_ms = (time.perf_counter() - t_start) * 1000
    log.info(
        "[TIMING] Auth token validation (local JWT decode): duration=%.2fms user_id=%s role=%s",
        duration_ms,
        user_uuid,
        role,
    )
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """
    FastAPI dependency: verifies the Bearer JWT and returns the AuthenticatedUser.

    Raises:
        UnauthorizedError: If no Bearer token is provided.
        TokenExpiredError: If the token has expired.
        InvalidTokenError: If the token is invalid or tampered with.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Authentication required. Please provide a Bearer token.")

    token = credentials.credentials.strip()
    return verify_jwt_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[AuthenticatedUser]:
    """
    FastAPI dependency: returns an AuthenticatedUser if a valid token is provided,
    or None for unauthenticated (guest) requests.

    If an invalid or expired token is provided, raises 401.
    """
    if credentials is None or not credentials.credentials:
        log.debug("[TIMING] Request authorization (guest mode): duration=0.01ms is_guest=True")
        return None

    token = credentials.credentials.strip()
    return verify_jwt_token(token)


async def require_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """
    FastAPI dependency: ensures the requesting user has the 'admin' role.

    Raises:
        ForbiddenError: If the user is not an administrator.
    """
    if not current_user.is_admin:
        log.warning(
            "Admin access denied for user %s (role=%s)", current_user.user_id, current_user.role
        )
        raise ForbiddenError("Administrator privileges required.")
    return current_user
