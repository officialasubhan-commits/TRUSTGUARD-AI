"""
Cryptographic authentication and authorization security primitives for the TrustGuard AI Admin Panel.
Implements:
- Argon2id password hashing and constant-time verification.
- Isolated administrator JWT issuance and validation.
- Rate-limiting and brute-force protection tracking.
- Server-side dependency: get_current_admin.
"""

from __future__ import annotations

import logging
import secrets
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.schemas.admin import AdminUserProfile

logger = logging.getLogger("trustguard.admin.security")

_bearer_scheme = HTTPBearer(auto_error=False)

# -----------------------------------------------------------------------------
# 1. Argon2id Password Hashing (with scrypt fallback)
# -----------------------------------------------------------------------------
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, type=2)  # type 2 is Argon2id
    _HAS_ARGON2 = True
except Exception:
    _ph = None
    _HAS_ARGON2 = False


def hash_admin_password(password: str) -> str:
    """
    Hashes administrator password using Argon2id with OWASP-recommended parameters.
    Falls back to memory-hard scrypt if argon2-cffi native bindings fail.
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    
    if _HAS_ARGON2 and _ph:
        return _ph.hash(password)
    
    # Cryptographic scrypt fallback (standard library)
    import hashlib
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"scrypt$16384$8$1${salt.hex()}${key.hex()}"


def verify_admin_password(stored_hash: str, candidate_password: str) -> bool:
    """
    Verifies an administrator password in constant time.
    """
    if not stored_hash or not candidate_password:
        return False
    
    try:
        if stored_hash.startswith("$argon2"):
            if _HAS_ARGON2 and _ph:
                _ph.verify(stored_hash, candidate_password)
                return True
            return False
        
        if stored_hash.startswith("scrypt$"):
            import hashlib
            parts = stored_hash.split("$")
            if len(parts) != 6:
                return False
            _, n_str, r_str, p_str, salt_hex, expected_hex = parts
            salt = bytes.fromhex(salt_hex)
            key = hashlib.scrypt(
                candidate_password.encode("utf-8"),
                salt=salt,
                n=int(n_str),
                r=int(r_str),
                p=int(p_str),
            )
            return secrets.compare_digest(key.hex(), expected_hex)
    except Exception as e:
        logger.warning("Password verification failed with exception: %s", e)
        return False
    
    return False


# -----------------------------------------------------------------------------
# 2. Administrator JWT Token Architecture
# -----------------------------------------------------------------------------
ADMIN_TOKEN_EXPIRATION_SECONDS = 28800  # 8 hours


def _get_admin_jwt_secret() -> str:
    base = settings.SUPABASE_JWT_SECRET
    if not base or len(base) < 32:
        base = "trustguard-test-jwt-secret-key-32chars-minimum!"
    return f"admin_signing_root_{base}"


def create_admin_access_token(admin_user: AdminUserProfile) -> Tuple[str, int]:
    """
    Issues a dedicated signed JWT for an administrator session.
    Tagged explicitly with claim 'admin_session' to reject any non-admin JWTs.
    """
    now = int(time.time())
    exp = now + ADMIN_TOKEN_EXPIRATION_SECONDS
    payload = {
        "sub": str(admin_user.id),
        "username": admin_user.username,
        "email": admin_user.email,
        "role": admin_user.role,
        "type": "admin_session",
        "iat": now,
        "exp": exp,
        "iss": "trustguard-ai-admin-authority",
    }
    token = jwt.encode(payload, _get_admin_jwt_secret(), algorithm="HS256")
    return token, ADMIN_TOKEN_EXPIRATION_SECONDS


def decode_admin_access_token(token: str) -> Dict[str, any]:
    """
    Decodes and strictly validates an administrator access token.
    """
    try:
        payload = jwt.decode(
            token,
            _get_admin_jwt_secret(),
            algorithms=["HS256"],
            issuer="trustguard-ai-admin-authority",
            options={"require": ["sub", "username", "role", "exp", "type"]},
        )
        if payload.get("type") != "admin_session":
            raise UnauthorizedError("Token is not an authorized administrator session.")
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Administrator session has expired. Please log in again.")
    except jwt.PyJWTError as e:
        raise UnauthorizedError(f"Invalid administrator token: {e}")


# -----------------------------------------------------------------------------
# 3. Brute Force Protection & Rate Limiting
# -----------------------------------------------------------------------------
# Tracks (count, first_attempt_timestamp, locked_until_timestamp)
_ip_failures: Dict[str, Dict[str, float]] = {}
_username_failures: Dict[str, Dict[str, float]] = {}

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes


def is_login_rate_limited(ip: str, username: str) -> Tuple[bool, int]:
    """
    Checks if login attempts from this IP or username have exceeded threshold.
    Returns (is_locked, seconds_remaining).
    """
    now = time.time()
    
    # Check IP
    ip_data = _ip_failures.get(ip)
    if ip_data:
        locked_until = ip_data.get("locked_until", 0)
        if now < locked_until:
            return True, int(locked_until - now)
    
    # Check Username
    user_data = _username_failures.get(username.lower())
    if user_data:
        locked_until = user_data.get("locked_until", 0)
        if now < locked_until:
            return True, int(locked_until - now)
        
    return False, 0


def record_login_failure(ip: str, username: str):
    """
    Records a failed login attempt and applies temporary lockout if threshold reached.
    """
    now = time.time()
    
    for key, tracker in [(ip, _ip_failures), (username.lower(), _username_failures)]:
        entry = tracker.get(key, {"count": 0, "first_ts": now, "locked_until": 0})
        # Reset window if > 15 minutes since first failure
        if now - entry["first_ts"] > LOCKOUT_DURATION_SECONDS:
            entry = {"count": 1, "first_ts": now, "locked_until": 0}
        else:
            entry["count"] += 1
        
        if entry["count"] >= MAX_FAILED_ATTEMPTS:
            entry["locked_until"] = now + LOCKOUT_DURATION_SECONDS
            logger.warning("Administrator login locked out for %s due to repeated failures.", key)
            
        tracker[key] = entry


def clear_login_failures(ip: str, username: str):
    """
    Clears failure counters upon successful authentication.
    """
    _ip_failures.pop(ip, None)
    _username_failures.pop(username.lower(), None)


# -----------------------------------------------------------------------------
# 4. Server-Side Dependency: get_current_admin
# -----------------------------------------------------------------------------
async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> AdminUserProfile:
    """
    FastAPI dependency: strictly verifies that the request possesses a valid
    administrator JWT and that the admin account is active.
    Rejects standard users with 403 Forbidden.
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("Administrator authentication required. Missing Bearer token.")
    
    token = credentials.credentials.strip()

    # 1. First check if it is a standard authenticated user JWT
    try:
        from app.core.security import verify_jwt_token
        auth_user = verify_jwt_token(token)
        if not auth_user.is_admin:
            raise ForbiddenError("Administrator privileges required. Your account lacks administrative authorization.")
        
        from app.database.repositories.admin_repo import get_admin_repository
        repo = get_admin_repository()
        admin = await repo.get_admin_by_id(auth_user.user_id)
        if admin:
            if not admin.is_active:
                raise ForbiddenError("This administrator account has been deactivated.")
            return admin

        return AdminUserProfile(
            id=auth_user.user_id,
            username=auth_user.email or "admin",
            role="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
        )
    except ForbiddenError:
        raise
    except Exception:
        pass

    # 2. Check dedicated administrator authority JWT
    payload = decode_admin_access_token(token)
    
    admin_id_str = payload.get("sub")
    
    try:
        admin_id = uuid.UUID(admin_id_str)
    except Exception:
        raise UnauthorizedError("Malformed administrator token identifier.")
    
    # Verify admin status against repository
    from app.database.repositories.admin_repo import get_admin_repository
    repo = get_admin_repository()
    admin = await repo.get_admin_by_id(admin_id)
    if not admin:
        raise UnauthorizedError("Administrator account no longer exists.")
    
    if not admin.is_active:
        raise ForbiddenError("This administrator account has been deactivated.")
    
    return admin

