"""
User Profile repository operations.
Interacts with public.users table in Supabase PostgreSQL.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.exceptions import DatabaseError
from app.database import connection
from app.schemas.user import UserCreate, UserProfileResponse, UserUpdate

logger = logging.getLogger("trustguard.repo.user")

# In-memory store for development/testing when live database is disconnected
_mock_users_store: Dict[uuid.UUID, Dict[str, Any]] = {}
# Resilient preference cache in case live Supabase schema cache hasn't loaded column
_threat_digest_fallback: Dict[uuid.UUID, bool] = {}


class UserRepository:
    def __init__(self, client=None):
        self._client = client or connection.supabase_client

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

        if self._client is not None:
            try:
                res = self._client.table("users").insert(record).execute()
                if not res.data:
                    raise DatabaseError("Failed to insert user profile.")
                data = res.data[0]
                if "threat_digest_enabled" not in data or data.get("threat_digest_enabled") is None:
                    data["threat_digest_enabled"] = threat_digest_pref
                return UserProfileResponse.model_validate(data)
            except Exception as e:
                err_str = str(e)
                if "threat_digest_enabled" in err_str or "PGRST204" in err_str:
                    logger.warning("Supabase schema cache lacks 'threat_digest_enabled', using resilient insert: %s", e)
                    _threat_digest_fallback[user_in.id] = threat_digest_pref
                    record_compat = {k: v for k, v in record.items() if k != "threat_digest_enabled"}
                    try:
                        res = self._client.table("users").insert(record_compat).execute()
                        if not res.data:
                            raise DatabaseError("Failed to insert user profile.")
                        data = res.data[0]
                        data["threat_digest_enabled"] = threat_digest_pref
                        return UserProfileResponse.model_validate(data)
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
        return UserProfileResponse.model_validate(_mock_users_store[user_in.id])

    async def get_user_profile(self, user_id: uuid.UUID) -> Optional[UserProfileResponse]:
        """
        Retrieves user profile by UUID.
        """
        if self._client is not None:
            try:
                res = self._client.table("users").select("*").eq("id", str(user_id)).execute()
                if res.data:
                    data = res.data[0]
                    if "threat_digest_enabled" not in data or data.get("threat_digest_enabled") is None:
                        data["threat_digest_enabled"] = _threat_digest_fallback.get(user_id, False)
                    return UserProfileResponse.model_validate(data)
                return None
            except Exception as e:
                logger.error("Supabase select user error: %s", e)
                raise DatabaseError(f"Database error fetching user: {e}")

        data = _mock_users_store.get(user_id)
        if data:
            return UserProfileResponse.model_validate(data)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserProfileResponse]:
        """
        Retrieves user profile by email address.
        """
        normalized_email = email.lower().strip()
        if self._client is not None:
            try:
                res = self._client.table("users").select("*").eq("email", normalized_email).execute()
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

        if self._client is not None:
            try:
                res = self._client.table("users").update(updates).eq("id", str(user_id)).execute()
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
                    return UserProfileResponse.model_validate(data)
                return None
            except Exception as e:
                err_str = str(e)
                if "threat_digest_enabled" in err_str or "PGRST204" in err_str:
                    logger.warning("Supabase schema lacks 'threat_digest_enabled', storing in resilient cache: %s", e)
                    if threat_digest_val is not None:
                        _threat_digest_fallback[user_id] = threat_digest_val
                    updates_compat = {k: v for k, v in updates.items() if k != "threat_digest_enabled"}
                    try:
                        res = self._client.table("users").update(updates_compat).eq("id", str(user_id)).execute()
                        if res.data:
                            data = res.data[0]
                            data["threat_digest_enabled"] = _threat_digest_fallback.get(user_id, False)
                            return UserProfileResponse.model_validate(data)
                    except Exception as update_err:
                        logger.error("Supabase update fallback error: %s", update_err)
                        raise DatabaseError(f"Database error updating user: {update_err}")
                    profile = await self.get_user_profile(user_id)
                    if profile:
                        if threat_digest_val is not None:
                            profile.threat_digest_enabled = threat_digest_val
                        return profile
                    return None
                logger.error("Supabase update user error: %s", e)
                raise DatabaseError(f"Database error updating user: {e}")

        if user_id in _mock_users_store:
            _mock_users_store[user_id].update(updates)
            _mock_users_store[user_id]["updated_at"] = datetime.now(timezone.utc)
            return UserProfileResponse.model_validate(_mock_users_store[user_id])
        return None

    async def increment_scan_count(self, user_id: uuid.UUID) -> None:
        """
        Increments user's total scan count.
        """
        if self._client is not None:
            try:
                # Direct RPC call or select + update
                profile = await self.get_user_profile(user_id)
                if profile:
                    self._client.table("users").update({"scan_count": profile.scan_count + 1}).eq(
                        "id", str(user_id)
                    ).execute()
            except Exception as e:
                logger.warning("Failed to increment user scan count: %s", e)
        else:
            if user_id in _mock_users_store:
                _mock_users_store[user_id]["scan_count"] += 1
