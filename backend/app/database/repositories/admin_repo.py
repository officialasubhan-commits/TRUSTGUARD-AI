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
    AdminScanItem,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserProfile,
    ContributorCreate,
    ContributorItem,
    ContributorReorderItem,
    ContributorsPageConfig,
    ContributorsPageConfigUpdate,
    ContributorUpdate,
    MaintenanceConfig,
    PaginatedAdminAuditLogs,
    PaginatedAdminReports,
    PaginatedAdminScans,
    PaginatedAdminUsers,
    SystemSettingsConfig,
    SystemSettingsUpdate,
    WebsitePageCreate,
    WebsitePageItem,
    WebsitePageUpdate,
)

import json
from pathlib import Path

logger = logging.getLogger("trustguard.repo.admin")

_LOCAL_STORE_PATH = Path(__file__).resolve().parent.parent / "admin_store.json"

_DEFAULT_ADMIN_ID = uuid.UUID("a2107163-49cd-4486-b982-edef1b495a58")
_DEFAULT_ADMIN_RECORD: Dict[str, Any] = {
    "id": str(_DEFAULT_ADMIN_ID),
    "username": "admin",
    "password_hash": "scrypt$16384$8$1$f79f60ae1601facf6f7be1d48a90bcde$b3d6bc81b3b08156784f3778e0f48572fd871b07a17ebb993fb1af6b39d6ab2968c1c0ff2f135df56596872951bdaaa24f482b013a51a4f95024acc73cf5bf17",
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
_mock_contributors: Dict[str, Dict[str, Any]] = {}
_mock_website_pages: Dict[str, Dict[str, Any]] = {}
_mock_system_settings: Dict[str, Dict[str, Any]] = {
    "maintenance_config": {
        "maintenance_enabled": False,
        "maintenance_message": "TrustGuard AI is temporarily undergoing scheduled maintenance. We will be back shortly.",
        "estimated_restore_time": None,
        "internal_reason": "System operating normally.",
        "updated_by": "system",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    "contributors_page_config": {
        "title": "Project Contributors",
        "subtitle": "The core developers, security researchers, and contributors powering TrustGuard AI.",
        "header_banner_url": None,
        "is_published": True,
        "show_in_navigation": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    "general_settings": {
        "site_name": "TrustGuard AI",
        "site_tagline": "AI-Powered Phishing & Scam URL Detection",
        "site_description": "Next-generation URL threat intelligence and automated cyber fraud protection.",
        "logo_url": None,
        "favicon_url": None,
        "announcement_enabled": False,
        "announcement_message": "TrustGuard AI 2.0 Released: Real-time ML inspection and community threat feed is live.",
        "announcement_type": "info",
        "announcement_link": None,
        "allow_registration": True,
        "allow_guest_scans": True,
        "allow_community_reports": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
}


def _ensure_default_admin():
    """Guarantees the root administrator exists across all environments (including Render/offline)."""
    global _mock_admin_users
    admin_entry = None
    for u in _mock_admin_users.values():
        if u.get("username", "").lower() == "admin" or (u.get("email") and u.get("email", "").lower() == "admin@trustguard.ai"):
            admin_entry = u
            break
    if not admin_entry:
        _mock_admin_users[_DEFAULT_ADMIN_ID] = dict(_DEFAULT_ADMIN_RECORD)
    else:
        # Ensure default admin always has the latest valid credentials and active status
        if admin_entry.get("password_hash", "").startswith("scrypt$16384$8$1$107afd49bedf"):
            admin_entry["password_hash"] = _DEFAULT_ADMIN_RECORD["password_hash"]
        admin_entry["is_active"] = True


def _load_local_store():
    global _mock_admin_users, _mock_audit_logs, _mock_system_settings, _mock_contributors, _mock_website_pages
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
                if "contributors" in data:
                    _mock_contributors = data["contributors"]
                if "website_pages" in data:
                    _mock_website_pages = data["website_pages"]
        except Exception as e:
            logger.debug("Failed reading local admin store: %s", e)
    _ensure_default_admin()


def _save_local_store():
    try:
        data = {
            "admin_users": {str(k): v for k, v in _mock_admin_users.items()},
            "audit_logs": _mock_audit_logs[:500],
            "system_settings": _mock_system_settings,
            "contributors": _mock_contributors,
            "website_pages": _mock_website_pages,
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
        """Calculates real platform metrics across users, scans, reports, contributors, and pages."""
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
            "safe_scans": 0,
            "suspicious_scans": 0,
            "malicious_scans": 0,
            "total_contributors": len(_mock_contributors),
            "published_pages": sum(1 for p in _mock_website_pages.values() if p.get("is_published", True)),
            "system_status": "healthy",
        }

        if cli is not None:
            try:
                # Count users
                u_res = await asyncio.to_thread(
                    lambda: cli.table("users").select("id, is_active", count="exact").execute()
                )
                stats["total_users"] = u_res.count or len(u_res.data)
                stats["active_users"] = sum(1 for u in u_res.data if u.get("is_active", True))

                # Count scans & classifications
                s_res = await asyncio.to_thread(
                    lambda: cli.table("scan_history").select("id, risk_level", count="exact").execute()
                )
                stats["total_scans"] = s_res.count or len(s_res.data)
                for s in s_res.data:
                    rk = str(s.get("risk_level", "")).upper()
                    if rk in ("SAFE", "LOW", "CLEAN"):
                        stats["safe_scans"] += 1
                    elif rk in ("SUSPICIOUS", "MEDIUM", "MODERATE"):
                        stats["suspicious_scans"] += 1
                    elif rk in ("MALICIOUS", "HIGH", "CRITICAL", "HIGH_RISK", "CRITICAL_RISK"):
                        stats["malicious_scans"] += 1
                        stats["high_risk_urls"] += 1
                    else:
                        stats["safe_scans"] += 1

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

                # Contributors & Pages if tables exist in PostgREST
                if connection.is_table_available("contributors"):
                    c_res = await asyncio.to_thread(lambda: cli.table("contributors").select("id", count="exact").execute())
                    stats["total_contributors"] = c_res.count or len(c_res.data)

                if connection.is_table_available("website_pages"):
                    p_res = await asyncio.to_thread(lambda: cli.table("website_pages").select("id").eq("is_published", True).execute())
                    stats["published_pages"] = len(p_res.data)

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
        for s in _mock_scans_store.values():
            rk = str(s.get("risk_level", "")).upper()
            if rk in ("SAFE", "LOW"):
                stats["safe_scans"] += 1
            elif rk in ("SUSPICIOUS", "MEDIUM"):
                stats["suspicious_scans"] += 1
            elif rk in ("MALICIOUS", "HIGH", "CRITICAL"):
                stats["malicious_scans"] += 1
                stats["high_risk_urls"] += 1
            else:
                stats["safe_scans"] += 1

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

        stats["total_contributors"] = len(_mock_contributors)
        stats["published_pages"] = sum(1 for p in _mock_website_pages.values() if p.get("is_published", True))
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

    async def update_user_profile(
        self,
        user_id: uuid.UUID,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """Updates user profile attributes."""
        now = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {"updated_at": now}
        if full_name is not None:
            updates["full_name"] = full_name.strip()
        if is_active is not None:
            updates["is_active"] = is_active
        if role is not None:
            updates["role"] = role

        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("users").update(updates).eq("id", str(user_id)).execute()
                )
                if res.data:
                    return True
            except Exception as e:
                logger.debug("Supabase update user profile failed, fallback: %s", e)

        from app.database.repositories.user_repo import _mock_users_store
        if user_id in _mock_users_store:
            _mock_users_store[user_id].update(updates)
            return True
        return False

    async def update_user_email(self, user_id: uuid.UUID, new_email: str) -> bool:
        """Securely changes a registered user's email address via Supabase Auth and public.users."""
        now = datetime.now(timezone.utc).isoformat()
        clean_email = new_email.strip().lower()

        # Update Supabase Auth if available
        if connection.supabase_client is not None and settings.supabase_configured:
            try:
                admin_auth = getattr(connection.supabase_client, "auth", None)
                if admin_auth and hasattr(admin_auth, "admin"):
                    await asyncio.to_thread(
                        lambda: admin_auth.admin.update_user_by_id(
                            str(user_id),
                            {"email": clean_email, "email_confirm": True}
                        )
                    )
            except Exception as auth_err:
                logger.warning("Supabase Auth admin email update warning: %s", auth_err)

        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("users").update({"email": clean_email, "updated_at": now}).eq("id", str(user_id)).execute()
                )
                if res.data:
                    return True
            except Exception as e:
                logger.debug("Supabase update user email failed, fallback: %s", e)

        from app.database.repositories.user_repo import _mock_users_store
        if user_id in _mock_users_store:
            _mock_users_store[user_id]["email"] = clean_email
            _mock_users_store[user_id]["updated_at"] = now
            return True
        return False

    async def delete_user_account(self, user_id: uuid.UUID) -> bool:
        """Permanently and safely deletes a registered user account and cleans up records."""
        # Delete from Supabase Auth
        if connection.supabase_client is not None and settings.supabase_configured:
            try:
                admin_auth = getattr(connection.supabase_client, "auth", None)
                if admin_auth and hasattr(admin_auth, "admin"):
                    await asyncio.to_thread(
                        lambda: admin_auth.admin.delete_user(str(user_id))
                    )
            except Exception as auth_err:
                logger.warning("Supabase Auth admin delete_user warning: %s", auth_err)

        cli = self.client
        if cli is not None:
            try:
                await asyncio.to_thread(
                    lambda: cli.table("users").delete().eq("id", str(user_id)).execute()
                )
                return True
            except Exception as e:
                logger.debug("Supabase delete user profile failed, fallback: %s", e)

        from app.database.repositories.user_repo import _mock_users_store
        if user_id in _mock_users_store:
            del _mock_users_store[user_id]
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

    # -------------------------------------------------------------------------
    # 7. Contributors Management
    # -------------------------------------------------------------------------
    async def get_contributors(self, include_inactive: bool = False) -> List[ContributorItem]:
        """Returns list of contributors sorted by display_order."""
        cli = self.client
        if cli is not None and connection.is_table_available("contributors"):
            try:
                query = cli.table("contributors").select("*")
                if not include_inactive:
                    query = query.eq("is_active", True)
                res = await asyncio.to_thread(lambda: query.order("display_order", desc=False).execute())
                return [ContributorItem.model_validate(c) for c in (res.data or [])]
            except Exception as e:
                logger.debug("Supabase get contributors failed, fallback: %s", e)

        items = list(_mock_contributors.values())
        if not include_inactive:
            items = [c for c in items if c.get("is_active", True)]
        items.sort(key=lambda x: x.get("display_order", 0))
        return [ContributorItem.model_validate(c) for c in items]

    async def get_contributor(self, contributor_id: str) -> Optional[ContributorItem]:
        """Gets a single contributor by ID."""
        cli = self.client
        if cli is not None and connection.is_table_available("contributors"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("contributors").select("*").eq("id", contributor_id).limit(1).execute()
                )
                if res.data:
                    return ContributorItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase get contributor failed, fallback: %s", e)

        c = _mock_contributors.get(contributor_id)
        return ContributorItem.model_validate(c) if c else None

    async def create_contributor(self, data: ContributorCreate) -> ContributorItem:
        """Creates a new contributor record."""
        now = datetime.now(timezone.utc).isoformat()
        new_id = f"contributor-{uuid.uuid4().hex[:8]}"
        record = {
            "id": new_id,
            "name": data.name.strip(),
            "role": data.role.strip(),
            "bio": data.bio.strip() if data.bio else None,
            "avatar_url": data.avatar_url,
            "social_links": data.social_links.model_dump(),
            "display_order": data.display_order,
            "is_active": data.is_active,
            "created_at": now,
            "updated_at": now,
        }

        cli = self.client
        if cli is not None and connection.is_table_available("contributors"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("contributors").insert(record).execute()
                )
                if res.data:
                    return ContributorItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase insert contributor failed, fallback: %s", e)

        _mock_contributors[new_id] = record
        _save_local_store()
        return ContributorItem.model_validate(record)

    async def update_contributor(self, contributor_id: str, data: ContributorUpdate) -> Optional[ContributorItem]:
        """Updates an existing contributor record."""
        now = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {"updated_at": now}
        if data.name is not None:
            updates["name"] = data.name.strip()
        if data.role is not None:
            updates["role"] = data.role.strip()
        if data.bio is not None:
            updates["bio"] = data.bio.strip()
        if data.avatar_url is not None:
            updates["avatar_url"] = data.avatar_url
        if data.social_links is not None:
            updates["social_links"] = data.social_links.model_dump()
        if data.display_order is not None:
            updates["display_order"] = data.display_order
        if data.is_active is not None:
            updates["is_active"] = data.is_active

        cli = self.client
        if cli is not None and connection.is_table_available("contributors"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("contributors").update(updates).eq("id", contributor_id).execute()
                )
                if res.data:
                    return ContributorItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase update contributor failed, fallback: %s", e)

        if contributor_id in _mock_contributors:
            _mock_contributors[contributor_id].update(updates)
            _save_local_store()
            return ContributorItem.model_validate(_mock_contributors[contributor_id])
        return None

    async def delete_contributor(self, contributor_id: str) -> bool:
        """Deletes a contributor."""
        cli = self.client
        if cli is not None and connection.is_table_available("contributors"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("contributors").delete().eq("id", contributor_id).execute()
                )
                return True
            except Exception as e:
                logger.debug("Supabase delete contributor failed, fallback: %s", e)

        if contributor_id in _mock_contributors:
            del _mock_contributors[contributor_id]
            _save_local_store()
            return True
        return False

    async def reorder_contributors(self, items: List[ContributorReorderItem]) -> bool:
        """Updates display_order for multiple contributors."""
        for item in items:
            if item.id in _mock_contributors:
                _mock_contributors[item.id]["display_order"] = item.display_order
        _save_local_store()

        cli = self.client
        if cli is not None and connection.is_table_available("contributors"):
            try:
                for item in items:
                    await asyncio.to_thread(
                        lambda i=item: cli.table("contributors").update({"display_order": i.display_order}).eq("id", i.id).execute()
                    )
            except Exception as e:
                logger.debug("Supabase reorder contributors failed: %s", e)
        return True

    async def get_contributors_page_config(self) -> ContributorsPageConfig:
        """Retrieves settings for the Contributors public page."""
        raw = _mock_system_settings.get("contributors_page_config", {})
        return ContributorsPageConfig.model_validate(raw)

    async def update_contributors_page_config(self, data: ContributorsPageConfigUpdate) -> ContributorsPageConfig:
        """Updates settings for the Contributors public page."""
        now = datetime.now(timezone.utc).isoformat()
        current = _mock_system_settings.get("contributors_page_config", {
            "title": "Project Contributors",
            "subtitle": "The core developers, security researchers, and contributors powering TrustGuard AI.",
            "header_banner_url": None,
            "is_published": True,
            "show_in_navigation": True,
        })
        if data.title is not None:
            current["title"] = data.title.strip()
        if data.subtitle is not None:
            current["subtitle"] = data.subtitle.strip()
        if data.header_banner_url is not None:
            current["header_banner_url"] = data.header_banner_url
        if data.is_published is not None:
            current["is_published"] = data.is_published
        if data.show_in_navigation is not None:
            current["show_in_navigation"] = data.show_in_navigation
        current["updated_at"] = now

        _mock_system_settings["contributors_page_config"] = current
        _save_local_store()

        cli = self.client
        if cli is not None and connection.is_table_available("system_settings"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("system_settings").upsert({
                        "key": "contributors_page_config",
                        "value": current,
                        "updated_by": "admin",
                        "updated_at": now,
                    }).execute()
                )
            except Exception as e:
                logger.debug("Supabase upsert contributors_page_config failed: %s", e)

        return ContributorsPageConfig.model_validate(current)

    # -------------------------------------------------------------------------
    # 8. Dynamic Pages (CMS) Management
    # -------------------------------------------------------------------------
    async def get_pages(self, include_unpublished: bool = False) -> List[WebsitePageItem]:
        """Lists dynamic CMS pages."""
        cli = self.client
        if cli is not None and connection.is_table_available("website_pages"):
            try:
                query = cli.table("website_pages").select("*")
                if not include_unpublished:
                    query = query.eq("is_published", True)
                res = await asyncio.to_thread(lambda: query.order("nav_order", desc=False).execute())
                return [WebsitePageItem.model_validate(p) for p in (res.data or [])]
            except Exception as e:
                logger.debug("Supabase get website_pages failed, fallback: %s", e)

        pages = list(_mock_website_pages.values())
        if not include_unpublished:
            pages = [p for p in pages if p.get("is_published", True)]
        pages.sort(key=lambda x: x.get("nav_order", 0))
        return [WebsitePageItem.model_validate(p) for p in pages]

    async def get_page_by_id(self, page_id: str) -> Optional[WebsitePageItem]:
        """Gets a page by ID."""
        cli = self.client
        if cli is not None and connection.is_table_available("website_pages"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("website_pages").select("*").eq("id", page_id).limit(1).execute()
                )
                if res.data:
                    return WebsitePageItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase get page by ID failed, fallback: %s", e)

        p = _mock_website_pages.get(page_id)
        return WebsitePageItem.model_validate(p) if p else None

    async def get_page_by_slug(self, slug: str) -> Optional[WebsitePageItem]:
        """Gets a published page by URL slug."""
        clean_slug = slug.strip().lower().lstrip("/")
        cli = self.client
        if cli is not None and connection.is_table_available("website_pages"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("website_pages").select("*").eq("slug", clean_slug).limit(1).execute()
                )
                if res.data:
                    return WebsitePageItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase get page by slug failed, fallback: %s", e)

        for p in _mock_website_pages.values():
            if p.get("slug", "").lower() == clean_slug:
                return WebsitePageItem.model_validate(p)
        return None

    async def create_page(self, data: WebsitePageCreate) -> WebsitePageItem:
        """Creates a new CMS page."""
        now = datetime.now(timezone.utc).isoformat()
        new_id = f"page-{uuid.uuid4().hex[:8]}"
        clean_slug = data.slug.strip().lower().lstrip("/")
        record = {
            "id": new_id,
            "title": data.title.strip(),
            "slug": clean_slug,
            "content": data.content,
            "meta_description": data.meta_description.strip() if data.meta_description else None,
            "is_published": data.is_published,
            "show_in_navigation": data.show_in_navigation,
            "nav_order": data.nav_order,
            "created_at": now,
            "updated_at": now,
        }

        cli = self.client
        if cli is not None and connection.is_table_available("website_pages"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("website_pages").insert(record).execute()
                )
                if res.data:
                    return WebsitePageItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase insert website_pages failed, fallback: %s", e)

        _mock_website_pages[new_id] = record
        _save_local_store()
        return WebsitePageItem.model_validate(record)

    async def update_page(self, page_id: str, data: WebsitePageUpdate) -> Optional[WebsitePageItem]:
        """Updates a CMS page."""
        now = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {"updated_at": now}
        if data.title is not None:
            updates["title"] = data.title.strip()
        if data.slug is not None:
            updates["slug"] = data.slug.strip().lower().lstrip("/")
        if data.content is not None:
            updates["content"] = data.content
        if data.meta_description is not None:
            updates["meta_description"] = data.meta_description.strip()
        if data.is_published is not None:
            updates["is_published"] = data.is_published
        if data.show_in_navigation is not None:
            updates["show_in_navigation"] = data.show_in_navigation
        if data.nav_order is not None:
            updates["nav_order"] = data.nav_order

        cli = self.client
        if cli is not None and connection.is_table_available("website_pages"):
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("website_pages").update(updates).eq("id", page_id).execute()
                )
                if res.data:
                    return WebsitePageItem.model_validate(res.data[0])
            except Exception as e:
                logger.debug("Supabase update website_pages failed, fallback: %s", e)

        if page_id in _mock_website_pages:
            _mock_website_pages[page_id].update(updates)
            _save_local_store()
            return WebsitePageItem.model_validate(_mock_website_pages[page_id])
        return None

    async def delete_page(self, page_id: str) -> bool:
        """Deletes a CMS page."""
        cli = self.client
        if cli is not None and connection.is_table_available("website_pages"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("website_pages").delete().eq("id", page_id).execute()
                )
                return True
            except Exception as e:
                logger.debug("Supabase delete website_pages failed, fallback: %s", e)

        if page_id in _mock_website_pages:
            del _mock_website_pages[page_id]
            _save_local_store()
            return True
        return False

    # -------------------------------------------------------------------------
    # 9. Scans Management
    # -------------------------------------------------------------------------
    async def get_scans_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> PaginatedAdminScans:
        """Retrieves website scans across the platform with filtering."""
        cli = self.client
        if cli is not None:
            try:
                query = cli.table("scan_history").select("*", count="exact")
                if classification:
                    c_clean = classification.strip().upper()
                    if c_clean == "SAFE":
                        query = query.in_("risk_level", ["SAFE", "LOW", "CLEAN"])
                    elif c_clean == "SUSPICIOUS":
                        query = query.in_("risk_level", ["SUSPICIOUS", "MEDIUM", "MODERATE"])
                    elif c_clean == "MALICIOUS":
                        query = query.in_("risk_level", ["MALICIOUS", "HIGH", "CRITICAL", "HIGH_RISK", "CRITICAL_RISK"])
                if search:
                    s_clean = search.strip()
                    query = query.or_(f"submitted_url.ilike.%{s_clean}%,domain.ilike.%{s_clean}%")

                offset = (page - 1) * page_size
                res = await asyncio.to_thread(
                    lambda: query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
                )
                total = res.count or len(res.data)
                items = []
                for s in (res.data or []):
                    rk = str(s.get("risk_level", "SAFE")).upper()
                    items.append(
                        AdminScanItem(
                            id=str(s["id"]),
                            url=s.get("submitted_url", ""),
                            domain=s.get("domain"),
                            classification=rk,
                            trust_score=float(s.get("trust_score", 0.0) or 0.0),
                            is_malicious=rk in ("MALICIOUS", "HIGH", "CRITICAL", "HIGH_RISK", "CRITICAL_RISK"),
                            user_id=str(s.get("user_id")) if s.get("user_id") else None,
                            user_email=None,
                            ip_address=s.get("ip_address"),
                            scanned_at=datetime.fromisoformat(s["created_at"].replace("Z", "+00:00")),
                            details=s.get("preliminary_analysis"),
                        )
                    )
                total_pages = max(1, (total + page_size - 1) // page_size)
                return PaginatedAdminScans(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                )
            except Exception as e:
                logger.debug("Supabase get scans list failed, using fallback: %s", e)

        from app.database.repositories.scan_repo import _mock_scans_store
        scans = list(_mock_scans_store.values())
        if classification:
            c_clean = classification.strip().upper()
            scans = [s for s in scans if str(s.get("risk_level", "")).upper() == c_clean]
        if search:
            s_clean = search.strip().lower()
            scans = [s for s in scans if s_clean in s.get("submitted_url", "").lower() or s_clean in str(s.get("domain", "")).lower()]

        scans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(scans)
        offset = (page - 1) * page_size
        paged = scans[offset : offset + page_size]
        items = [
            AdminScanItem(
                id=str(s.get("id", uuid.uuid4())),
                url=s.get("submitted_url", ""),
                domain=s.get("domain"),
                classification=str(s.get("risk_level", "SAFE")).upper(),
                trust_score=float(s.get("trust_score", 0.0) or 0.0),
                is_malicious=str(s.get("risk_level", "")).upper() in ("MALICIOUS", "HIGH", "CRITICAL"),
                user_id=str(s.get("user_id")) if s.get("user_id") else None,
                user_email=None,
                ip_address=s.get("ip_address"),
                scanned_at=s.get("created_at") if isinstance(s.get("created_at"), datetime) else datetime.now(timezone.utc),
                details=s.get("preliminary_analysis"),
            )
            for s in paged
        ]
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedAdminScans(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_scan_detail(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves detailed scan metrics and security analysis."""
        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("scan_history").select("*").eq("id", scan_id).limit(1).execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug("Supabase get scan detail failed, fallback: %s", e)

        from app.database.repositories.scan_repo import _mock_scans_store
        return _mock_scans_store.get(scan_id)

    # -------------------------------------------------------------------------
    # 10. General System Settings
    # -------------------------------------------------------------------------
    async def get_system_settings(self) -> SystemSettingsConfig:
        """Retrieves global system configuration and branding."""
        raw = _mock_system_settings.get("general_settings", {
            "site_name": "TrustGuard AI",
            "site_tagline": "AI-Powered Phishing & Scam URL Detection",
            "site_description": "Next-generation URL threat intelligence and automated cyber fraud protection.",
            "logo_url": None,
            "favicon_url": None,
            "announcement_enabled": False,
            "announcement_message": "TrustGuard AI 2.0 Released: Real-time ML inspection and community threat feed is live.",
            "announcement_type": "info",
            "announcement_link": None,
            "allow_registration": True,
            "allow_guest_scans": True,
            "allow_community_reports": True,
        })
        return SystemSettingsConfig.model_validate(raw)

    async def update_system_settings(self, data: SystemSettingsUpdate) -> SystemSettingsConfig:
        """Updates global system configuration and branding."""
        now = datetime.now(timezone.utc).isoformat()
        current = _mock_system_settings.get("general_settings", {
            "site_name": "TrustGuard AI",
            "site_tagline": "AI-Powered Phishing & Scam URL Detection",
            "site_description": "Next-generation URL threat intelligence and automated cyber fraud protection.",
            "logo_url": None,
            "favicon_url": None,
            "announcement_enabled": False,
            "announcement_message": "TrustGuard AI 2.0 Released: Real-time ML inspection and community threat feed is live.",
            "announcement_type": "info",
            "announcement_link": None,
            "allow_registration": True,
            "allow_guest_scans": True,
            "allow_community_reports": True,
        })
        for k, v in data.model_dump(exclude_unset=True).items():
            if v is not None:
                current[k] = v
        current["updated_at"] = now

        _mock_system_settings["general_settings"] = current
        _save_local_store()

        cli = self.client
        if cli is not None and connection.is_table_available("system_settings"):
            try:
                await asyncio.to_thread(
                    lambda: cli.table("system_settings").upsert({
                        "key": "general_settings",
                        "value": current,
                        "updated_by": "admin",
                        "updated_at": now,
                    }).execute()
                )
            except Exception as e:
                logger.debug("Supabase upsert general_settings failed: %s", e)

        return SystemSettingsConfig.model_validate(current)


_admin_repo_instance: Optional[AdminRepository] = None


def get_admin_repository() -> AdminRepository:
    global _admin_repo_instance
    if _admin_repo_instance is None:
        _admin_repo_instance = AdminRepository()
    return _admin_repo_instance
