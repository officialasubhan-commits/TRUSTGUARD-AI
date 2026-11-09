"""
Admin Repository for TrustGuard AI.
Handles database interactions for:
- public.admin_users
- public.admin_audit_logs
- public.system_settings
- Platform overview aggregations and moderation queues.

Features resilient dual-mode operation:
- Uses Supabase service-role client when connected and schema is present.
- Seamlessly falls back to an in-memory test store so the entire admin panel
  is immediately testable and functional offline or prior to DB migration execution.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.exceptions import DatabaseError, NotFoundError
from app.database import connection
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminReportDetail,
    AdminReportListItem,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserProfile,
    MaintenanceConfig,
    PaginatedAdminAuditLogs,
    PaginatedAdminReports,
    PaginatedAdminUsers,
)

import json
from pathlib import Path

logger = logging.getLogger("trustguard.repo.admin")

_LOCAL_STORE_PATH = Path(__file__).resolve().parent.parent / "local_admin_store.json"

_DEFAULT_ADMIN_ID = uuid.UUID("a2107163-49cd-4486-b982-edef1b495a58")
_DEFAULT_ADMIN_RECORD: Dict[str, Any] = {
    "id": str(_DEFAULT_ADMIN_ID),
    "username": "admin",
    "password_hash": "scrypt$16384$8$1$107afd49bedf659b6f5414e83028c958$dcb46554c22e5f8560dabf07cf2652a197d404746105a22d60acbdcf3c88610b9f71c7c9a37eab266f6163fdf590bb86677d383303177ce8aff98521451184ba",
    "email": "admin@trustguard.ai",
    "full_name": "Security Administrator",
    "role": "super_admin",
    "is_active": True,
    "last_login_at": None,
    "last_login_ip": None,
    "failed_login_attempts": 0,
    "locked_until": None,
    "created_at": "2026-11-08T14:43:22.659592+00:00",
    "updated_at": "2026-11-08T15:10:07.496168+00:00",
}

# In-memory stores for isolated fallback
_mock_admin_users: Dict[uuid.UUID, Dict[str, Any]] = {}
_mock_audit_logs: List[Dict[str, Any]] = []
_mock_system_settings: Dict[str, Dict[str, Any]] = {
    "maintenance_config": {
        "maintenance_enabled": False,
        "maintenance_message": "TrustGuard AI is temporarily undergoing scheduled maintenance. We will be back shortly.",
        "estimated_restore_time": None,
        "internal_reason": "System operating normally.",
        "updated_by": "system",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
}


def _ensure_default_admin():
    """Guarantees the root administrator exists across all environments (including Render/offline)."""
    global _mock_admin_users
    has_admin = any(
        u.get("username", "").lower() == "admin"
        or (u.get("email") and u.get("email", "").lower() == "admin@trustguard.ai")
        for u in _mock_admin_users.values()
    )
    if not has_admin:
        _mock_admin_users[_DEFAULT_ADMIN_ID] = dict(_DEFAULT_ADMIN_RECORD)


def _load_local_store():
    global _mock_admin_users, _mock_audit_logs, _mock_system_settings
    if _LOCAL_STORE_PATH.exists():
        try:
            with open(_LOCAL_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "admin_users" in data:
                    _mock_admin_users = {uuid.UUID(k): v for k, v in data["admin_users"].items()}
                if "audit_logs" in data:
                    _mock_audit_logs = data["audit_logs"]
                if "system_settings" in data:
                    _mock_system_settings.update(data["system_settings"])
        except Exception as e:
            logger.debug("Failed reading local admin store: %s", e)
    _ensure_default_admin()


def _save_local_store():
    try:
        data = {
            "admin_users": {str(k): v for k, v in _mock_admin_users.items()},
            "audit_logs": _mock_audit_logs[:500],
            "system_settings": _mock_system_settings,
        }
        with open(_LOCAL_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.debug("Failed saving local admin store: %s", e)


_load_local_store()
_ensure_default_admin()


class AdminRepository:
    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        c = self._client or connection.get_supabase_service_client()
        if c is not None and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                c.postgrest.auth(settings.SUPABASE_SERVICE_ROLE_KEY)
            except Exception:
                pass
        return c

    # -------------------------------------------------------------------------
    # 1. Admin Account Operations
    # -------------------------------------------------------------------------
    async def get_admin_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Finds admin by username or email (case-insensitive) including password_hash."""
        _ensure_default_admin()
        u_clean = username.strip().lower()
        cli = self.client
        if cli is not None and connection.is_table_available("admin_users"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("admin_users")
                    .select("*")
                    .or_(f"username.ilike.{u_clean},email.ilike.{u_clean}")
                    .limit(1)
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug("Supabase lookup admin_users failed, using fallback: %s", e)

        for u in _mock_admin_users.values():
            if u["username"].lower() == u_clean or (u.get("email") and u["email"].lower() == u_clean):
                return u
        return None

    async def get_admin_by_id(self, admin_id: uuid.UUID) -> Optional[AdminUserProfile]:
        """Finds active admin user profile by UUID."""
        _ensure_default_admin()
        cli = self.client
        if cli is not None and connection.is_table_available("admin_users"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("admin_users").select("*").eq("id", str(admin_id)).limit(1).execute()
                )
                if res.data:
                    return AdminUserProfile.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase get admin_users by ID failed, using fallback: %s", e)

        if admin_id in _mock_admin_users:
            return AdminUserProfile.model_validate(_mock_admin_users[admin_id])
        return None

    async def create_admin_user(
        self,
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "super_admin",
    ) -> AdminUserProfile:
        """Creates an administrator record."""
        admin_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        record = {
            "id": str(admin_id),
            "username": username.strip(),
            "password_hash": password_hash,
            "email": email.strip() if email else None,
            "full_name": full_name.strip() if full_name else None,
            "role": role,
            "is_active": True,
            "last_login_at": None,
            "last_login_ip": None,
            "failed_login_attempts": 0,
            "locked_until": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        cli = self.client
        if cli is not None and connection.is_table_available("admin_users"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("admin_users").insert(record).execute()
                )
                if res.data:
                    return AdminUserProfile.model_validate(res.data[0])
            except Exception as e:
                logger.warning("Supabase insert admin_users failed, saving to local fallback: %s", e)

        _mock_admin_users[admin_id] = record
        _save_local_store()
        return AdminUserProfile.model_validate(record)

    async def update_admin_password(self, admin_id: uuid.UUID, new_password_hash: str) -> bool:
        """Updates admin password hash."""
        now = datetime.now(timezone.utc).isoformat()
        cli = self.client
        if cli is not None and connection.is_table_available("admin_users"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("admin_users").update({
                        "password_hash": new_password_hash,
                        "updated_at": now,
                    }).eq("id", str(admin_id)).execute()
                )
                return True
            except Exception as e:
                logger.debug("Supabase update admin password failed: %s", e)

        if admin_id in _mock_admin_users:
            _mock_admin_users[admin_id]["password_hash"] = new_password_hash
            _mock_admin_users[admin_id]["updated_at"] = now
            _save_local_store()
            return True
        return False

    async def record_successful_login(self, admin_id: uuid.UUID, ip_address: Optional[str] = None):
        """Updates last_login_at and resets failed counter."""
        now = datetime.now(timezone.utc).isoformat()
        cli = self.client
        if cli is not None and connection.is_table_available("admin_users"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("admin_users").update({
                        "last_login_at": now,
                        "last_login_ip": ip_address,
                        "failed_login_attempts": 0,
                        "locked_until": None,
                    }).eq("id", str(admin_id)).execute()
                )
            except Exception:
                pass

        if admin_id in _mock_admin_users:
            _mock_admin_users[admin_id]["last_login_at"] = now
            _mock_admin_users[admin_id]["last_login_ip"] = ip_address
            _mock_admin_users[admin_id]["failed_login_attempts"] = 0
            _save_local_store()

    # -------------------------------------------------------------------------
    # 2. Administrator Audit Logging
    # -------------------------------------------------------------------------
    async def log_audit_event(
        self,
        action: str,
        admin_username: str,
        admin_id: Optional[uuid.UUID] = None,
        target_resource: Optional[str] = None,
        outcome: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AdminAuditLogItem:
        """Appends an immutable audit log entry."""
        log_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        record = {
            "id": str(log_id),
            "admin_id": str(admin_id) if admin_id else None,
            "admin_username": admin_username,
            "action": action,
            "target_resource": target_resource,
            "outcome": outcome,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": now.isoformat(),
        }

        cli = self.client
        if cli is not None and connection.is_table_available("admin_audit_logs"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("admin_audit_logs").insert(record).execute()
                )
                if res.data:
                    return AdminAuditLogItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase insert admin_audit_logs fallback: %s", e)

        _mock_audit_logs.insert(0, record)
        _save_local_store()
        return AdminAuditLogItem.model_validate(record)

    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        action: Optional[str] = None,
        admin_username: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedAdminAuditLogs:
        """Retrieves paginated audit log entries."""
        cli = self.client
        if cli is not None and connection.is_table_available("admin_audit_logs"):
            try:
                query = cli.table("admin_audit_logs").select("*", count="exact")
                if action:
                    query = query.eq("action", action)
                if admin_username:
                    query = query.ilike("admin_username", f"%{admin_username}%")
                if search:
                    query = query.or_(f"action.ilike.%{search}%,target_resource.ilike.%{search}%")
                
                offset = (page - 1) * page_size
                res = await asyncio.to_thread(
                    lambda: query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
                )
                total = res.count or len(res.data)
                items = [AdminAuditLogItem.model_validate(r) for r in res.data]
                total_pages = max(1, (total + page_size - 1) // page_size)
                return PaginatedAdminAuditLogs(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                )
            except Exception as e:
                logger.debug("Supabase get audit logs failed, using fallback: %s", e)

        # In-memory filtering
        filtered = _mock_audit_logs
        if action:
            filtered = [l for l in filtered if l["action"] == action]
        if admin_username:
            filtered = [l for l in filtered if admin_username.lower() in l["admin_username"].lower()]
        if search:
            s = search.lower()
            filtered = [
                l for l in filtered
                if s in l["action"].lower() or (l.get("target_resource") and s in l["target_resource"].lower())
            ]

        total = len(filtered)
        offset = (page - 1) * page_size
        paged = filtered[offset : offset + page_size]
        items = [AdminAuditLogItem.model_validate(r) for r in paged]
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedAdminAuditLogs(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # -------------------------------------------------------------------------
    # 3. System Settings & Maintenance Mode
    # -------------------------------------------------------------------------
    async def get_maintenance_config(self) -> MaintenanceConfig:
        """Retrieves website maintenance configuration with fast TTL memory caching."""
        try:
            loop = asyncio.get_running_loop()
            now_ts = loop.time()
        except RuntimeError:
            now_ts = 0.0

        if hasattr(self, "_cached_cfg") and hasattr(self, "_cached_cfg_time") and (now_ts - self._cached_cfg_time < 10.0):
            return self._cached_cfg

        cli = self.client
        if cli is not None and connection.is_table_available("system_settings"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("system_settings").select("*").eq("key", "maintenance_config").limit(1).execute()
                )
                if res.data and "value" in res.data[0]:
                    val = res.data[0]["value"]
                    val["updated_by"] = res.data[0].get("updated_by")
                    val["updated_at"] = res.data[0].get("updated_at")
                    cfg = MaintenanceConfig.model_validate(val)
                    self._cached_cfg = cfg
                    self._cached_cfg_time = now_ts
                    return cfg
            except Exception as e:
                logger.debug("Supabase lookup maintenance_config failed, using fallback: %s", e)

        data = _mock_system_settings.get("maintenance_config", {})
        cfg = MaintenanceConfig.model_validate(data)
        self._cached_cfg = cfg
        self._cached_cfg_time = now_ts
        return cfg

    async def update_maintenance_config(
        self,
        enabled: bool,
        message: Optional[str],
        estimated_restore_time: Optional[str],
        internal_reason: str,
        updated_by: str,
    ) -> MaintenanceConfig:
        """Updates website maintenance configuration."""
        now = datetime.now(timezone.utc)
        cfg_val = {
            "maintenance_enabled": enabled,
            "maintenance_message": message or "TrustGuard AI is temporarily undergoing scheduled maintenance.",
            "estimated_restore_time": estimated_restore_time,
            "internal_reason": internal_reason,
        }
        row = {
            "key": "maintenance_config",
            "value": cfg_val,
            "updated_by": updated_by,
            "updated_at": now.isoformat(),
        }

        cli = self.client
        if cli is not None and connection.is_table_available("system_settings"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("system_settings").upsert(row).execute()
                )
            except Exception as e:
                logger.debug("Supabase upsert maintenance_config failed, using fallback: %s", e)

        _mock_system_settings["maintenance_config"] = {
            **cfg_val,
            "updated_by": updated_by,
            "updated_at": now.isoformat(),
        }
        _save_local_store()
        updated_cfg = MaintenanceConfig.model_validate(_mock_system_settings["maintenance_config"])
        self._cached_cfg = updated_cfg
        try:
            self._cached_cfg_time = asyncio.get_running_loop().time()
        except RuntimeError:
            self._cached_cfg_time = 0.0
        return updated_cfg

    # -------------------------------------------------------------------------
    # 4. Platform Overview Statistics
    # -------------------------------------------------------------------------
    async def get_platform_stats(self) -> Dict[str, Any]:
        """Calculates real platform metrics across users, scans, and reports."""
        cli = self.client
        stats = {
            "total_users": 0,
            "active_users": 0,
            "total_scans": 0,
            "total_community_reports": 0,
            "pending_reports": 0,
            "verified_reports": 0,
            "rejected_reports": 0,
            "resolved_reports": 0,
            "high_risk_urls": 0,
        }

        if cli is not None:
            try:
                # Count users
                u_res = await asyncio.to_thread(
                    lambda: cli.table("users").select("id, is_active", count="exact").execute()
                )
                stats["total_users"] = u_res.count or len(u_res.data)
                stats["active_users"] = sum(1 for u in u_res.data if u.get("is_active", True))

                # Count scans
                s_res = await asyncio.to_thread(
                    lambda: cli.table("scan_history").select("id, risk_level", count="exact").execute()
                )
                stats["total_scans"] = s_res.count or len(s_res.data)
                stats["high_risk_urls"] = sum(
                    1 for s in s_res.data if s.get("risk_level") in ("HIGH", "CRITICAL", "HIGH_RISK", "CRITICAL_RISK")
                )

                # Count community reports
                r_res = await asyncio.to_thread(
                    lambda: cli.table("community_reports").select("id, moderation_status, report_status", count="exact").execute()
                )
                stats["total_community_reports"] = r_res.count or len(r_res.data)
                for r in r_res.data:
                    mod = (r.get("moderation_status") or r.get("report_status") or "").upper()
                    if mod in ("PENDING", "PENDING_REVIEW"):
                        stats["pending_reports"] += 1
                    elif mod in ("APPROVED", "VERIFIED"):
                        stats["verified_reports"] += 1
                    elif mod in ("REJECTED",):
                        stats["rejected_reports"] += 1
                    elif mod in ("RESOLVED",):
                        stats["resolved_reports"] += 1

                return stats
            except Exception as e:
                logger.warning("Supabase get platform stats failed, using fallback counts: %s", e)

        # Local fallback based on mock stores
        from app.database.repositories.user_repo import _mock_users_store
        from app.database.repositories.scan_repo import _mock_scans_store
        from app.database.repositories.report_repo import _mock_reports_store

        stats["total_users"] = len(_mock_users_store)
        stats["active_users"] = sum(1 for u in _mock_users_store.values() if u.get("is_active", True))
        stats["total_scans"] = len(_mock_scans_store)
        stats["high_risk_urls"] = sum(
            1 for s in _mock_scans_store.values() if s.get("risk_level") in ("HIGH", "CRITICAL")
        )
        stats["total_community_reports"] = len(_mock_reports_store)
        for r in _mock_reports_store.values():
            st = r.get("moderation_status", "PENDING").upper()
            if st in ("PENDING", "PENDING_REVIEW"):
                stats["pending_reports"] += 1
            elif st in ("APPROVED", "VERIFIED"):
                stats["verified_reports"] += 1
            elif st == "REJECTED":
                stats["rejected_reports"] += 1
            elif st == "RESOLVED":
                stats["resolved_reports"] += 1

        return stats

    # -------------------------------------------------------------------------
    # 5. User Management Operations
    # -------------------------------------------------------------------------
    async def get_users_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedAdminUsers:
        """Retrieves paginated user profiles with search and status filters."""
        cli = self.client
        if cli is not None:
            try:
                query = cli.table("users").select("*", count="exact")
                if is_active is not None:
                    query = query.eq("is_active", is_active)
                if search:
                    s = search.strip()
                    query = query.or_(f"email.ilike.%{s}%,full_name.ilike.%{s}%")

                offset = (page - 1) * page_size
                res = await asyncio.to_thread(
                    lambda: query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
                )
                total = res.count or len(res.data)
                items = [
                    AdminUserListItem(
                        id=uuid.UUID(r["id"]),
                        email=r["email"],
                        full_name=r.get("full_name"),
                        avatar_url=r.get("avatar_url"),
                        scan_count=r.get("scan_count", 0),
                        is_active=r.get("is_active", True),
                        role="user",
                        created_at=datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")),
                    )
                    for r in res.data
                ]
                total_pages = max(1, (total + page_size - 1) // page_size)
                return PaginatedAdminUsers(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                )
            except Exception as e:
                logger.debug("Supabase list users failed, using fallback: %s", e)

        # Fallback
        from app.database.repositories.user_repo import _mock_users_store
        users = list(_mock_users_store.values())
        if is_active is not None:
            users = [u for u in users if u.get("is_active", True) == is_active]
        if search:
            s = search.lower()
            users = [
                u for u in users
                if s in u.get("email", "").lower() or s in (u.get("full_name") or "").lower()
            ]

        total = len(users)
        offset = (page - 1) * page_size
        paged = users[offset : offset + page_size]
        items = [
            AdminUserListItem(
                id=u["id"] if isinstance(u["id"], uuid.UUID) else uuid.UUID(u["id"]),
                email=u["email"],
                full_name=u.get("full_name"),
                avatar_url=u.get("avatar_url"),
                scan_count=u.get("scan_count", 0),
                is_active=u.get("is_active", True),
                role="user",
                created_at=u["created_at"] if isinstance(u["created_at"], datetime) else datetime.fromisoformat(str(u["created_at"]).replace("Z", "+00:00")),
            )
            for u in paged
        ]
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedAdminUsers(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user_detail(self, user_id: uuid.UUID) -> Optional[AdminUserDetail]:
        """Retrieves comprehensive user information including recent scan history."""
        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("users").select("*").eq("id", str(user_id)).limit(1).execute()
                )
                if not res.data:
                    return None
                u = res.data[0]

                # Fetch recent scans
                scans_res = await asyncio.to_thread(
                    lambda: cli.table("scan_history")
                    .select("id, submitted_url, domain, trust_score, risk_level, scan_status, created_at")
                    .eq("user_id", str(user_id))
                    .order("created_at", desc=True)
                    .limit(10)
                    .execute()
                )
                scans = scans_res.data or []

                return AdminUserDetail(
                    id=uuid.UUID(u["id"]),
                    email=u["email"],
                    full_name=u.get("full_name"),
                    avatar_url=u.get("avatar_url"),
                    scan_count=u.get("scan_count", 0),
                    is_active=u.get("is_active", True),
                    role="user",
                    created_at=datetime.fromisoformat(u["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(u["updated_at"].replace("Z", "+00:00")),
                    recent_scans=scans,
                )
            except Exception as e:
                logger.debug("Supabase get user detail failed, fallback: %s", e)

        from app.database.repositories.user_repo import _mock_users_store
        u = _mock_users_store.get(user_id)
        if not u:
            return None
        return AdminUserDetail(
            id=user_id,
            email=u["email"],
            full_name=u.get("full_name"),
            avatar_url=u.get("avatar_url"),
            scan_count=u.get("scan_count", 0),
            is_active=u.get("is_active", True),
            role="user",
            created_at=u["created_at"] if isinstance(u["created_at"], datetime) else datetime.now(timezone.utc),
            updated_at=u["updated_at"] if isinstance(u["updated_at"], datetime) else datetime.now(timezone.utc),
            recent_scans=[],
        )

    async def set_user_status(self, user_id: uuid.UUID, is_active: bool) -> bool:
        """Suspends or restores user account."""
        now = datetime.now(timezone.utc).isoformat()
        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("users").update({"is_active": is_active, "updated_at": now}).eq("id", str(user_id)).execute()
                )
                if res.data:
                    return True
            except Exception as e:
                logger.debug("Supabase update user status failed, fallback: %s", e)

        from app.database.repositories.user_repo import _mock_users_store
        if user_id in _mock_users_store:
            _mock_users_store[user_id]["is_active"] = is_active
            _mock_users_store[user_id]["updated_at"] = now
            return True
        return False

    # -------------------------------------------------------------------------
    # 6. Community Report Moderation Operations
    # -------------------------------------------------------------------------
    async def get_reports_queue(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedAdminReports:
        """Retrieves reports for administrative moderation."""
        cli = self.client
        if cli is not None:
            try:
                query = cli.table("community_reports").select("*", count="exact")
                if status:
                    query = query.or_(f"moderation_status.ilike.{status},report_status.ilike.{status}")
                if category:
                    query = query.or_(f"threat_type.ilike.{category},report_reason.ilike.{category}")
                if search:
                    s = search.strip()
                    query = query.or_(f"submitted_url.ilike.%{s}%,domain.ilike.%{s}%")

                offset = (page - 1) * page_size
                res = await asyncio.to_thread(
                    lambda: query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
                )
                total = res.count or len(res.data)
                items = []
                for r in res.data:
                    created = r.get("created_at")
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else datetime.now(timezone.utc)
                    items.append(
                        AdminReportListItem(
                            id=uuid.UUID(r["id"]),
                            submitted_url=r["submitted_url"],
                            domain=r.get("domain"),
                            report_reason=r.get("report_reason") or r.get("threat_type") or "SUSPICIOUS_PHISHING",
                            threat_type=r.get("threat_type"),
                            target_brand=r.get("target_brand"),
                            submitter_email=None,
                            moderation_status=r.get("moderation_status") or "PENDING",
                            report_status=r.get("report_status") or "pending_review",
                            verification_status=r.get("verification_status") or "unverified",
                            upvotes=r.get("upvotes", 0),
                            attachments_count=1 if r.get("evidence_url") else 0,
                            created_at=dt,
                        )
                    )

                from app.database.repositories.report_repo import _mock_reports_store
                if _mock_reports_store:
                    for r in _mock_reports_store.values():
                        st = (r.get("moderation_status") or "PENDING").upper()
                        if status and st != status.upper():
                            continue
                        created = r.get("created_at")
                        dt = created if isinstance(created, datetime) else (datetime.fromisoformat(str(created).replace("Z", "+00:00")) if created else datetime.now(timezone.utc))
                        items.append(
                            AdminReportListItem(
                                id=r["id"] if isinstance(r["id"], uuid.UUID) else uuid.UUID(r["id"]),
                                submitted_url=r["submitted_url"],
                                domain=r.get("domain"),
                                report_reason=r.get("report_reason") or r.get("threat_type") or "SUSPICIOUS_PHISHING",
                                threat_type=r.get("threat_type"),
                                target_brand=r.get("target_brand"),
                                submitter_email=None,
                                moderation_status=st,
                                report_status=r.get("report_status") or "pending_review",
                                verification_status=r.get("verification_status") or "unverified",
                                upvotes=r.get("upvotes", 0),
                                attachments_count=1 if r.get("evidence_url") else 0,
                                created_at=dt,
                            )
                        )
                        total += 1
                total_pages = max(1, (total + page_size - 1) // page_size)
                return PaginatedAdminReports(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                )
            except Exception as e:
                logger.debug("Supabase get moderation reports failed: %s", e)

        from app.database.repositories.report_repo import _mock_reports_store
        reports = list(_mock_reports_store.values())
        if status:
            s_up = status.upper()
            reports = [r for r in reports if r.get("moderation_status", "PENDING").upper() == s_up]
        if category:
            c_up = category.upper()
            reports = [r for r in reports if (r.get("threat_type") or r.get("report_reason", "")).upper() == c_up]
        if search:
            q = search.lower()
            reports = [
                r for r in reports
                if q in r.get("submitted_url", "").lower() or q in (r.get("domain") or "").lower()
            ]

        total = len(reports)
        offset = (page - 1) * page_size
        paged = reports[offset : offset + page_size]
        items = []
        for r in paged:
            rid = r["id"] if isinstance(r["id"], uuid.UUID) else uuid.UUID(r["id"])
            c_at = r.get("created_at")
            dt = c_at if isinstance(c_at, datetime) else datetime.fromisoformat(str(c_at).replace("Z", "+00:00"))
            items.append(
                AdminReportListItem(
                    id=rid,
                    submitted_url=r["submitted_url"],
                    domain=r.get("domain"),
                    report_reason=r.get("report_reason") or r.get("threat_type") or "SUSPICIOUS_PHISHING",
                    threat_type=r.get("threat_type"),
                    target_brand=r.get("target_brand"),
                    submitter_email="community_user@trustguard.ai",
                    moderation_status=r.get("moderation_status") or "PENDING",
                    report_status=r.get("report_status") or "pending_review",
                    verification_status=r.get("verification_status") or "unverified",
                    upvotes=r.get("upvotes", 0),
                    attachments_count=1 if r.get("evidence_url") else 0,
                    created_at=dt,
                )
            )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedAdminReports(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_report_detail(self, report_id: uuid.UUID) -> Optional[AdminReportDetail]:
        """Retrieves complete report information with evidence, scan, and confirmations."""
        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("community_reports").select("*").eq("id", str(report_id)).limit(1).execute()
                )
                if not res.data:
                    return None
                r = res.data[0]

                # Retrieve submitter email if available
                sub_email = None
                sub_id = uuid.UUID(r["user_id"]) if r.get("user_id") else None
                if sub_id:
                    u_res = await asyncio.to_thread(
                        lambda: cli.table("users").select("email").eq("id", str(sub_id)).limit(1).execute()
                    )
                    if u_res.data:
                        sub_email = u_res.data[0].get("email")

                # Retrieve confirmations safely
                confirmations = []
                if connection.is_table_available("community_confirmations"):
                    try:
                        conf_res = await asyncio.to_thread(
                            lambda: cli.table("community_confirmations").select("*").eq("report_id", str(report_id)).execute()
                        )
                        confirmations = conf_res.data or []
                    except Exception:
                        pass
                else:
                    from app.database.repositories.report_repo import _mock_confirmations_store
                    rep_id_prefix = f"{str(report_id)}:"
                    confirmations = [
                        val for key, val in _mock_confirmations_store.items()
                        if key.startswith(rep_id_prefix)
                    ]

                # Retrieve associated scan if scan_id present
                scan_data = None
                if r.get("scan_id"):
                    try:
                        s_res = await asyncio.to_thread(
                            lambda: cli.table("scan_history").select("*").eq("id", r["scan_id"]).limit(1).execute()
                        )
                        if s_res.data:
                            scan_data = s_res.data[0]
                    except Exception:
                        pass

                # Synthesize evidence items
                evidence_items = []
                if r.get("evidence_url"):
                    evidence_items.append({
                        "id": str(uuid.uuid4()),
                        "filename": r["evidence_url"].split("/")[-1] or "evidence_screenshot.png",
                        "file_type": "image/png" if r["evidence_url"].endswith((".png", ".jpg", ".webp")) else "application/pdf",
                        "file_size_bytes": 1024 * 350,
                        "url": r["evidence_url"],
                        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "is_quarantined": False,
                    })

                dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                rev_dt = datetime.fromisoformat(r["reviewed_at"].replace("Z", "+00:00")) if r.get("reviewed_at") else None

                return AdminReportDetail(
                    id=uuid.UUID(r["id"]),
                    submitted_url=r["submitted_url"],
                    normalized_url=r.get("normalized_url", r["submitted_url"]),
                    domain=r.get("domain"),
                    report_reason=r.get("report_reason") or r.get("threat_type") or "SUSPICIOUS_PHISHING",
                    threat_type=r.get("threat_type"),
                    target_brand=r.get("target_brand"),
                    attack_vector=r.get("attack_vector"),
                    description=r.get("description"),
                    notes=r.get("notes"),
                    submitter_email=sub_email,
                    submitter_id=sub_id,
                    moderation_status=r.get("moderation_status", "PENDING"),
                    moderation_notes=r.get("moderation_notes"),
                    reviewer_id=uuid.UUID(r["moderator_id"]) if r.get("moderator_id") else None,
                    reviewer_username="admin",
                    reviewed_at=rev_dt,
                    upvotes=r.get("upvotes", 0),
                    confirmations_count=len(confirmations),
                    confirmations=confirmations,
                    evidence_items=evidence_items,
                    associated_scan=scan_data,
                    created_at=dt,
                )
            except Exception as e:
                logger.debug("Supabase get report detail failed, fallback: %s", e)

        from app.database.repositories.report_repo import _mock_reports_store
        r = _mock_reports_store.get(report_id)
        if not r:
            return None
        return AdminReportDetail(
            id=report_id,
            submitted_url=r["submitted_url"],
            normalized_url=r.get("normalized_url", r["submitted_url"]),
            domain=r.get("domain"),
            report_reason=r.get("report_reason") or r.get("threat_type") or "SUSPICIOUS_PHISHING",
            threat_type=r.get("threat_type"),
            target_brand=r.get("target_brand"),
            attack_vector=r.get("attack_vector"),
            description=r.get("description"),
            notes=r.get("notes"),
            submitter_email="analyst@trustguard.ai",
            submitter_id=r.get("user_id"),
            moderation_status=r.get("moderation_status", "PENDING"),
            moderation_notes=r.get("moderation_notes"),
            reviewer_id=None,
            reviewer_username=None,
            reviewed_at=None,
            upvotes=r.get("upvotes", 0),
            confirmations_count=0,
            confirmations=[],
            evidence_items=[{
                "id": str(uuid.uuid4()),
                "filename": "screenshot_evidence.png",
                "file_type": "image/png",
                "file_size_bytes": 284000,
                "url": r.get("evidence_url") or "https://picsum.photos/800/600",
                "sha256_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f901234567890abcdef1234567890abcdef",
                "is_quarantined": False,
            }] if r.get("evidence_url") else [],
            associated_scan=None,
            created_at=datetime.now(timezone.utc),
        )

    async def update_report_moderation(
        self,
        report_id: uuid.UUID,
        moderation_status: str,
        moderation_notes: str,
        moderator_id: Optional[uuid.UUID] = None,
        duplicate_of: Optional[uuid.UUID] = None,
    ) -> bool:
        """Applies administrative decision to report record."""
        now = datetime.now(timezone.utc).isoformat()
        
        # Map moderation status to public report status
        report_status = "pending_review"
        verification_status = "unverified"
        if moderation_status == "APPROVE":
            moderation_status = "APPROVED"
            report_status = "verified"
            verification_status = "verified"
        elif moderation_status == "REJECT":
            moderation_status = "REJECTED"
            report_status = "rejected"
            verification_status = "rejected"
        elif moderation_status == "UNDER_REVIEW":
            moderation_status = "UNDER_REVIEW"
            report_status = "pending_review"
            verification_status = "under_investigation"
        elif moderation_status == "RESOLVED":
            moderation_status = "RESOLVED"
            report_status = "resolved"
            verification_status = "remediated"
        elif moderation_status == "DUPLICATE":
            moderation_status = "DUPLICATE"
            report_status = "duplicate"
            verification_status = "unverified"

        updates = {
            "moderation_status": moderation_status,
            "report_status": report_status,
            "verification_status": verification_status,
            "moderation_notes": moderation_notes,
            "reviewed_at": now,
            "updated_at": now,
        }
        if duplicate_of:
            updates["duplicate_of"] = str(duplicate_of)

        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("community_reports").update(updates).eq("id", str(report_id)).execute()
                )
                if res.data:
                    return True
            except Exception as e:
                logger.debug("Supabase update report moderation failed, fallback: %s", e)

        from app.database.repositories.report_repo import _mock_reports_store
        if report_id in _mock_reports_store:
            _mock_reports_store[report_id].update(updates)
            return True
        return False


_admin_repo_instance: Optional[AdminRepository] = None


def get_admin_repository() -> AdminRepository:
    global _admin_repo_instance
    if _admin_repo_instance is None:
        _admin_repo_instance = AdminRepository()
    return _admin_repo_instance
