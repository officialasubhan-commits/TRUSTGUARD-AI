"""
User Profile repository operations.
Interacts with public.users table in Supabase PostgreSQL.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.database import connection
from app.schemas.user import UserCreate, UserProfileResponse, UserUpdate

logger = logging.getLogger("trustguard.repo.user")

# In-memory store for development/testing when live database is disconnected
_mock_users_store: Dict[uuid.UUID, Dict[str, Any]] = {}
# Resilient preference cache in case live Supabase schema cache hasn't loaded column
_threat_digest_fallback: Dict[uuid.UUID, bool] = {}

# High-performance TTL cache to eliminate duplicate roundtrips to Supabase for the same user profile
_user_profile_cache: Dict[str, Tuple[UserProfileResponse, float]] = {}
_USER_CACHE_TTL_SECONDS = 60.0


def _get_cached_profile(user_id: uuid.UUID) -> Optional[UserProfileResponse]:
    cached = _user_profile_cache.get(str(user_id))
    if cached is not None:
        profile, ts = cached
        if (time.time() - ts) < _USER_CACHE_TTL_SECONDS:
            return profile.model_copy()
        _user_profile_cache.pop(str(user_id), None)
    return None


def _set_cached_profile(user_id: uuid.UUID, profile: UserProfileResponse) -> None:
    _user_profile_cache[str(user_id)] = (profile.model_copy(), time.time())


def _invalidate_cached_profile(user_id: uuid.UUID) -> None:
    _user_profile_cache.pop(str(user_id), None)



class UserRepository:
    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        """
        Retrieves the Supabase service-role client guaranteed to have administrative bypass privileges.
        Ensures PostgREST Authorization is set to SUPABASE_SERVICE_ROLE_KEY to prevent RLS failures.
        """
        c = self._client or connection.get_supabase_service_client() or connection.supabase_client
        if c is not None and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                c.postgrest.auth(settings.SUPABASE_SERVICE_ROLE_KEY)
            except Exception:
                pass
        return c

    async def create_user_profile(self, user_in: UserCreate) -> UserProfileResponse:
        """
        Creates an application profile row linked to auth.users.id.
        """
        now = datetime.now(timezone.utc)
        threat_digest_pref = getattr(user_in, "threat_digest_enabled", False)
        record = {
            "id": str(user_in.id),
            "email": user_in.email,
            "full_name": user_in.full_name,
            "avatar_url": user_in.avatar_url,
            "scan_count": 0,
            "is_active": True,
            "threat_digest_enabled": threat_digest_pref,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        cli = self.client
        if cli is not None:
            try:
                res = cli.table("users").insert(record).execute()
                if not res.data:
                    raise DatabaseError("Failed to insert user profile.")
                data = res.data[0]
                if "threat_digest_enabled" not in data or data.get("threat_digest_enabled") is None:
                    data["threat_digest_enabled"] = threat_digest_pref
                profile = UserProfileResponse.model_validate(data)
                _set_cached_profile(user_in.id, profile)
                return profile
            except Exception as e:
                err_str = str(e)
                if "threat_digest_enabled" in err_str or "PGRST204" in err_str:
                    logger.warning("Supabase schema cache lacks 'threat_digest_enabled', using resilient insert: %s", e)
                    _threat_digest_fallback[user_in.id] = threat_digest_pref
                    record_compat = {k: v for k, v in record.items() if k != "threat_digest_enabled"}
                    try:
                        res = cli.table("users").insert(record_compat).execute()
                        if not res.data:
                            raise DatabaseError("Failed to insert user profile.")
                        data = res.data[0]
                        data["threat_digest_enabled"] = threat_digest_pref
                        profile = UserProfileResponse.model_validate(data)
                        _set_cached_profile(user_in.id, profile)
                        return profile
                    except Exception as fallback_err:
                        logger.error("Supabase insert user fallback error: %s", fallback_err)
                        raise DatabaseError(f"Database error creating user profile: {fallback_err}")
                logger.error("Supabase insert user error: %s", e)
                raise DatabaseError(f"Database error creating user profile: {e}")

        # Local fallback
        _mock_users_store[user_in.id] = {
            **record,
            "id": user_in.id,
            "created_at": now,
            "updated_at": now,
        }
        profile = UserProfileResponse.model_validate(_mock_users_store[user_in.id])
        _set_cached_profile(user_in.id, profile)
        return profile

    async def get_user_profile(self, user_id: uuid.UUID) -> Optional[UserProfileResponse]:
        """
        Retrieves user profile by UUID with in-memory caching.
        """
        cached = _get_cached_profile(user_id)
        if cached is not None:
            return cached

        cli = self.client
        if cli is not None:
            try:
                res = cli.table("users").select("*").eq("id", str(user_id)).execute()
                if res.data:
                    data = res.data[0]
                    if "threat_digest_enabled" not in data or data.get("threat_digest_enabled") is None:
                        data["threat_digest_enabled"] = _threat_digest_fallback.get(user_id, False)
                    profile = UserProfileResponse.model_validate(data)
                    _set_cached_profile(user_id, profile)
                    return profile
                return None
            except Exception as e:
                logger.error("Supabase select user error: %s", e)
                raise DatabaseError(f"Database error fetching user: {e}")

        data = _mock_users_store.get(user_id)
        if data:
            profile = UserProfileResponse.model_validate(data)
            _set_cached_profile(user_id, profile)
            return profile
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserProfileResponse]:
        """
        Retrieves user profile by email address.
        """
        normalized_email = email.lower().strip()
        cli = self.client
        if cli is not None:
            try:
                res = cli.table("users").select("*").eq("email", normalized_email).execute()
                if res.data:
                    data = res.data[0]
                    uid = uuid.UUID(data["id"])
                    if "threat_digest_enabled" not in data or data.get("threat_digest_enabled") is None:
                        data["threat_digest_enabled"] = _threat_digest_fallback.get(uid, False)
                    return UserProfileResponse.model_validate(data)
                return None
            except Exception as e:
                logger.error("Supabase select user by email error: %s", e)
                raise DatabaseError(f"Database error fetching user by email: {e}")

        for uid, user_data in _mock_users_store.items():
            if user_data.get("email", "").lower().strip() == normalized_email:
                return UserProfileResponse.model_validate(user_data)
        return None

    async def update_user_profile(
        self, user_id: uuid.UUID, update_in: UserUpdate
    ) -> Optional[UserProfileResponse]:
        """
        Updates profile details (display name, avatar, active status, threat_digest_enabled).
        """
        updates = {k: v for k, v in update_in.model_dump(exclude_unset=True).items() if v is not None}
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        threat_digest_val = updates.get("threat_digest_enabled")

        cli = self.client
        if cli is not None:
            try:
                res = cli.table("users").update(updates).eq("id", str(user_id)).execute()
                if res.data:
                    data = res.data[0]
                    if "threat_digest_enabled" not in data or data.get("threat_digest_enabled") is None:
                        data["threat_digest_enabled"] = (
                            threat_digest_val
                            if threat_digest_val is not None
                            else _threat_digest_fallback.get(user_id, False)
                        )
                    if threat_digest_val is not None:
                        _threat_digest_fallback[user_id] = threat_digest_val
                    profile = UserProfileResponse.model_validate(data)
                    _set_cached_profile(user_id, profile)
                    return profile
                return None
            except Exception as e:
                err_str = str(e)
                if "threat_digest_enabled" in err_str or "PGRST204" in err_str:
                    logger.warning("Supabase schema lacks 'threat_digest_enabled', storing in resilient cache: %s", e)
                    if threat_digest_val is not None:
                        _threat_digest_fallback[user_id] = threat_digest_val
                    updates_compat = {k: v for k, v in updates.items() if k != "threat_digest_enabled"}
                    try:
                        res = cli.table("users").update(updates_compat).eq("id", str(user_id)).execute()
                        if res.data:
                            data = res.data[0]
                            data["threat_digest_enabled"] = _threat_digest_fallback.get(user_id, False)
                            profile = UserProfileResponse.model_validate(data)
                            _set_cached_profile(user_id, profile)
                            return profile
                    except Exception as update_err:
                        logger.error("Supabase update fallback error: %s", update_err)
                        raise DatabaseError(f"Database error updating user: {update_err}")
                    _invalidate_cached_profile(user_id)
                    profile = await self.get_user_profile(user_id)
                    if profile:
                        if threat_digest_val is not None:
                            profile.threat_digest_enabled = threat_digest_val
                        _set_cached_profile(user_id, profile)
                        return profile
                    return None
                logger.error("Supabase update user error: %s", e)
                raise DatabaseError(f"Database error updating user: {e}")

        if user_id in _mock_users_store:
            _mock_users_store[user_id].update(updates)
            _mock_users_store[user_id]["updated_at"] = datetime.now(timezone.utc)
            profile = UserProfileResponse.model_validate(_mock_users_store[user_id])
            _set_cached_profile(user_id, profile)
            return profile
        return None

    async def increment_scan_count(self, user_id: uuid.UUID) -> None:
        """
        Increments user's total scan count.
        """
        _invalidate_cached_profile(user_id)
        cli = self.client
        if cli is not None:
            try:
                profile = await self.get_user_profile(user_id)
                if profile:
                    cli.table("users").update({"scan_count": profile.scan_count + 1}).eq(
                        "id", str(user_id)
                    ).execute()
            except Exception as e:
                logger.warning("Failed to increment user scan count: %s", e)
        else:
            if user_id in _mock_users_store:
                _mock_users_store[user_id]["scan_count"] += 1
