"""
Community Threat Reports repository operations.
Interacts with public.community_reports table in Supabase PostgreSQL with local mock fallback.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.exceptions import DatabaseError, NotFoundError
from app.database import connection
from app.schemas.report import (
    CommunityReportCreate,
    CommunityReportModerationUpdate,
)

logger = logging.getLogger("trustguard.repo.report")

_mock_reports_store: Dict[uuid.UUID, Dict[str, Any]] = {}
_mock_confirmations_store: Dict[str, Dict[str, Any]] = {}
_mock_flags_store: Dict[uuid.UUID, Dict[str, Any]] = {}


class ReportRecord(dict):
    """Dictionary supporting attribute access for backwards compatibility."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ReportRecord' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class ReportRepository:
    """
    Data access layer for community threat reports.
    Dual-engine: Supabase client with in-memory store fallback.
    """

    def __init__(self, client=None):
        self._client = client or connection.supabase_client

    async def create_community_report(
        self,
        user_id: uuid.UUID,
        report_in: CommunityReportCreate,
        normalized_url: str,
        domain: Optional[str] = None,
        duplicate_of: Optional[uuid.UUID] = None,
    ) -> ReportRecord:
        """
        Creates a new community threat report submission by an authenticated user.
        """
        report_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        raw_reason = report_in.report_reason or report_in.category or "phishing"
        cat = raw_reason.upper()
        desc = report_in.description or report_in.notes or ""

        # Auto-link existing scan if scan_id not explicitly provided
        linked_scan_id = report_in.scan_id
        if not linked_scan_id and self._client is not None:
            try:
                scan_res = (
                    self._client.table("scan_history")
                    .select("id")
                    .eq("normalized_url", normalized_url)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if scan_res.data:
                    raw_sid = scan_res.data[0]["id"]
                    linked_scan_id = uuid.UUID(raw_sid) if isinstance(raw_sid, str) else raw_sid
            except Exception:
                pass

        record: Dict[str, Any] = {
            "id": str(report_id),
            "scan_id": str(linked_scan_id) if linked_scan_id else None,
            "user_id": str(user_id),
            "submitted_url": report_in.submitted_url,
            "normalized_url": normalized_url,
            "domain": domain,
            "report_reason": raw_reason,
            "threat_type": cat,
            "target_brand": report_in.target_brand,
            "attack_vector": report_in.attack_vector,
            "description": desc,
            "notes": desc,
            "evidence_url": report_in.evidence_url,
            "moderation_status": "PENDING",
            "report_status": "pending_review",
            "verification_status": "UNVERIFIED",
            "moderation_notes": None,
            "moderator_id": None,
            "reviewed_at": None,
            "duplicate_of": str(duplicate_of) if duplicate_of else None,
            "upvotes": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        if self._client is not None:
            try:
                res = self._client.table("community_reports").insert(record).execute()
                if not res.data:
                    raise DatabaseError("Failed to submit community report.")
                rec_data = dict(res.data[0])
                rec_data["id"] = report_id
                rec_data["category"] = cat
                return ReportRecord(rec_data)
            except Exception as e:
                logger.error("Supabase insert community_reports error: %s", e)
                raise DatabaseError(f"Database error submitting report: {e}")

        # Local fallback
        mock_rec = ReportRecord(
            {
                **record,
                "id": report_id,
                "user_id": user_id,
                "scan_id": report_in.scan_id,
                "duplicate_of": duplicate_of,
                "created_at": now,
                "updated_at": now,
            }
        )
        _mock_reports_store[report_id] = mock_rec
        return mock_rec

    async def get_report_by_id(self, report_id: uuid.UUID) -> Optional[ReportRecord]:
        """Fetch a single report by ID."""
        if self._client is not None:
            try:
                res = (
                    self._client.table("community_reports")
                    .select("*")
                    .eq("id", str(report_id))
                    .execute()
                )
                if res.data:
                    rec = dict(res.data[0])
                    rec["id"] = report_id
                    return ReportRecord(rec)
                return None
            except Exception as e:
                logger.error("Supabase get_report_by_id error: %s", e)
                raise DatabaseError(f"Database error fetching report: {e}")

        found = _mock_reports_store.get(report_id)
        return ReportRecord(found) if found else None

    async def find_duplicates(
        self,
        normalized_url: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[ReportRecord]:
        """
        Find existing reports matching a normalized URL.
        Used for deduplication and spam prevention.
        """
        if self._client is not None:
            try:
                query = (
                    self._client.table("community_reports")
                    .select("*")
                    .eq("normalized_url", normalized_url)
                )
                if user_id:
                    query = query.eq("user_id", str(user_id))
                res = query.execute()
                return [ReportRecord(r) for r in (res.data or [])]
            except Exception as e:
                logger.error("Supabase find_duplicates error: %s", e)
                raise DatabaseError(f"Database error checking duplicates: {e}")

        matches = [
            r for r in _mock_reports_store.values() if r.get("normalized_url") == normalized_url
        ]
        if user_id:
            matches = [r for r in matches if str(r.get("user_id")) == str(user_id)]
        return [ReportRecord(r) for r in matches]

    async def get_public_reports(
        self,
        domain: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "newest",
        user_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReportRecord], int]:
        """
        Query public approved/reviewed threat reports with pagination, filtering, and sorting.
        Optionally decorates records with user confirmation status.
        """
        offset = (page - 1) * page_size

        # Determine target moderation statuses
        target_statuses = ["APPROVED", "verified"]
        if status:
            s_upper = status.strip().upper()
            if s_upper in ("UNDER_REVIEW", "PENDING"):
                target_statuses = ["PENDING", "UNDER_REVIEW", "pending_review"]
            elif s_upper in ("VERIFIED", "APPROVED"):
                target_statuses = ["APPROVED", "VERIFIED", "verified"]
            elif s_upper == "REJECTED":
                target_statuses = ["REJECTED", "rejected"]
            elif s_upper == "RESOLVED":
                target_statuses = ["RESOLVED", "resolved"]
            elif s_upper == "ALL":
                target_statuses = ["APPROVED", "VERIFIED", "verified", "UNDER_REVIEW", "PENDING", "pending_review", "REJECTED", "RESOLVED"]

        if self._client is not None:
            try:
                query = (
                    self._client.table("community_reports")
                    .select("*", count="exact")
                    .in_("moderation_status", target_statuses)
                )
                if domain:
                    query = query.ilike("domain", f"%{domain}%")
                if category and category.upper() != "ALL":
                    query = query.or_(f"report_reason.ilike.{category},threat_type.ilike.{category}")
                if search:
                    query = query.or_(
                        f"submitted_url.ilike.%{search}%,description.ilike.%{search}%,target_brand.ilike.%{search}%"
                    )

                if sort_by in ("most_confirmed", "upvotes", "most_supported"):
                    query = query.order("upvotes", desc=True).order("created_at", desc=True)
                else:
                    query = query.order("created_at", desc=True)

                res = query.range(offset, offset + page_size - 1).execute()
                items = []
                for r in (res.data or []):
                    rec_dict = dict(r)
                    rec_dict.setdefault("category", rec_dict.get("threat_type") or rec_dict.get("report_reason"))
                    items.append(ReportRecord(rec_dict))
                total = res.count if res.count is not None else len(items)

                # Decorate with user confirmation status if authenticated
                if user_id and items:
                    rep_ids = [str(r.get("id")) for r in items if r.get("id")]
                    try:
                        conf_res = (
                            self._client.table("community_confirmations")
                            .select("report_id")
                            .eq("user_id", str(user_id))
                            .in_("report_id", rep_ids)
                            .execute()
                        )
                        confirmed_set = {str(c.get("report_id")) for c in (conf_res.data or [])}
                        for r in items:
                            r["user_confirmed"] = str(r.get("id")) in confirmed_set
                    except Exception:
                        pass

                return items, total
            except Exception as e:
                logger.warning("Supabase get_public_reports error, falling back to local store: %s", e)

        # Local fallback
        items = [
            r
            for r in _mock_reports_store.values()
            if str(r.get("moderation_status", "")).upper() in [ts.upper() for ts in target_statuses]
            or str(r.get("report_status", "")) in target_statuses
        ]
        if domain:
            items = [r for r in items if domain.lower() in (r.get("domain") or "").lower()]
        if category and category.upper() != "ALL":
            cat_target = category.strip().lower()
            items = [
                r
                for r in items
                if (r.get("report_reason") or "").lower() == cat_target
                or (r.get("category") or "").lower() == cat_target
            ]
        if search:
            s = search.lower()
            items = [
                r
                for r in items
                if s in (r.get("submitted_url") or "").lower()
                or s in (r.get("description") or "").lower()
                or s in (r.get("target_brand") or "").lower()
            ]

        total = len(items)
        if sort_by in ("most_confirmed", "upvotes", "most_supported"):
            items.sort(key=lambda x: int(x.get("upvotes", 0)), reverse=True)
        else:
            items.sort(
                key=lambda x: (
                    x.get("created_at") if isinstance(x.get("created_at"), datetime) else datetime.min
                ),
                reverse=True,
            )

        paginated = [ReportRecord(r) for r in items[offset : offset + page_size]]
        if user_id:
            for r in paginated:
                r["user_confirmed"] = f"{r.get('id')}:{user_id}" in _mock_confirmations_store
        return paginated, total

    async def get_community_statistics(self) -> Dict[str, Any]:
        """
        Compute live platform statistics across community threat reports.
        """
        now = datetime.now(timezone.utc)
        if self._client is not None:
            try:
                total_res = self._client.table("community_reports").select("id", count="exact").execute()
                total = total_res.count if total_res.count is not None else len(total_res.data or [])

                pending_res = (
                    self._client.table("community_reports")
                    .select("id", count="exact")
                    .in_("moderation_status", ["PENDING", "UNDER_REVIEW", "pending_review"])
                    .execute()
                )
                pending = pending_res.count if pending_res.count is not None else len(pending_res.data or [])

                verified_res = (
                    self._client.table("community_reports")
                    .select("id", count="exact")
                    .in_("moderation_status", ["APPROVED", "VERIFIED", "verified"])
                    .execute()
                )
                verified = verified_res.count if verified_res.count is not None else len(verified_res.data or [])

                rejected_res = (
                    self._client.table("community_reports")
                    .select("id", count="exact")
                    .in_("moderation_status", ["REJECTED", "rejected"])
                    .execute()
                )
                rejected = rejected_res.count if rejected_res.count is not None else len(rejected_res.data or [])

                resolved_res = (
                    self._client.table("community_reports")
                    .select("id", count="exact")
                    .in_("moderation_status", ["RESOLVED", "resolved"])
                    .execute()
                )
                resolved = resolved_res.count if resolved_res.count is not None else len(resolved_res.data or [])

                conf_count = 0
                try:
                    conf_res = self._client.table("community_confirmations").select("id", count="exact").execute()
                    conf_count = conf_res.count if conf_res.count is not None else len(conf_res.data or [])
                except Exception:
                    pass

                return {
                    "total_reports": total,
                    "pending_review": pending,
                    "verified_reports": verified,
                    "rejected_reports": rejected,
                    "resolved_reports": resolved,
                    "active_confirmations": conf_count,
                    "generated_at": now.isoformat(),
                }
            except Exception as e:
                logger.error("Supabase get_community_statistics error: %s", e)

        # Local fallback
        all_reps = list(_mock_reports_store.values())
        total = len(all_reps)
        pending = sum(1 for r in all_reps if str(r.get("moderation_status", "")).upper() in ("PENDING", "UNDER_REVIEW", "PENDING_REVIEW"))
        verified = sum(1 for r in all_reps if str(r.get("moderation_status", "")).upper() in ("APPROVED", "VERIFIED"))
        rejected = sum(1 for r in all_reps if str(r.get("moderation_status", "")).upper() in ("REJECTED",))
        resolved = sum(1 for r in all_reps if str(r.get("moderation_status", "")).upper() in ("RESOLVED",))
        conf_count = sum(int(r.get("upvotes", 0)) for r in all_reps)

        return {
            "total_reports": total,
            "pending_review": pending,
            "verified_reports": verified,
            "rejected_reports": rejected,
            "resolved_reports": resolved,
            "active_confirmations": conf_count,
            "generated_at": now.isoformat(),
        }

    async def toggle_confirmation(
        self,
        report_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Tuple[bool, int]:
        """
        Toggle community confirmation:
        - If confirmed: removes confirmation and decrements upvotes. Returns (False, count)
        - If not confirmed: adds confirmation and increments upvotes. Returns (True, count)
        """
        rep_id_str = str(report_id)
        user_id_str = str(user_id)
        mock_key = f"{rep_id_str}:{user_id_str}"

        if self._client is not None:
            try:
                curr_report = await self.get_report_by_id(report_id)
                curr_upvotes = int(curr_report.get("upvotes", 0)) if curr_report else 0

                existing = (
                    self._client.table("community_confirmations")
                    .select("id")
                    .eq("report_id", rep_id_str)
                    .eq("user_id", user_id_str)
                    .execute()
                )

                if existing.data:
                    self._client.table("community_confirmations").delete().eq("report_id", rep_id_str).eq("user_id", user_id_str).execute()
                    new_votes = max(0, curr_upvotes - 1)
                    self._client.table("community_reports").update({"upvotes": new_votes}).eq("id", rep_id_str).execute()
                    return False, new_votes
                else:
                    self._client.table("community_confirmations").insert({
                        "report_id": rep_id_str,
                        "user_id": user_id_str,
                    }).execute()
                    new_votes = curr_upvotes + 1
                    self._client.table("community_reports").update({"upvotes": new_votes}).eq("id", rep_id_str).execute()
                    return True, new_votes
            except Exception as e:
                logger.error("Supabase toggle_confirmation error: %s", e)

        # Local fallback
        curr_report = _mock_reports_store.get(report_id)
        curr_upvotes = int(curr_report.get("upvotes", 0)) if curr_report else 0
        if mock_key in _mock_confirmations_store:
            del _mock_confirmations_store[mock_key]
            new_votes = max(0, curr_upvotes - 1)
            if curr_report:
                curr_report["upvotes"] = new_votes
            return False, new_votes
        else:
            _mock_confirmations_store[mock_key] = {
                "report_id": report_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
            }
            new_votes = curr_upvotes + 1
            if curr_report:
                curr_report["upvotes"] = new_votes
            return True, new_votes

    async def is_confirmed_by_user(self, report_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        rep_id_str = str(report_id)
        user_id_str = str(user_id)
        if self._client is not None:
            try:
                res = (
                    self._client.table("community_confirmations")
                    .select("id")
                    .eq("report_id", rep_id_str)
                    .eq("user_id", user_id_str)
                    .execute()
                )
                return bool(res.data)
            except Exception:
                pass
        return f"{rep_id_str}:{user_id_str}" in _mock_confirmations_store

    async def flag_report(
        self,
        report_id: uuid.UUID,
        user_id: uuid.UUID,
        flag_reason: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record community flag for abusive, inaccurate, or outdated threat submissions.
        """
        flag_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        record = {
            "id": str(flag_id),
            "report_id": str(report_id),
            "user_id": str(user_id),
            "flag_reason": flag_reason,
            "notes": notes,
            "created_at": now.isoformat(),
        }
        if self._client is not None:
            try:
                self._client.table("community_report_flags").insert(record).execute()
                return record
            except Exception as e:
                logger.error("Supabase insert community_report_flags error: %s", e)

        _mock_flags_store[flag_id] = record
        return record

    async def get_user_reports(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReportRecord], int]:
        """
        Query all reports submitted by a specific user.
        """
        offset = (page - 1) * page_size

        if self._client is not None:
            try:
                res = (
                    self._client.table("community_reports")
                    .select("*", count="exact")
                    .eq("user_id", str(user_id))
                    .order("created_at", desc=True)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
                items = [ReportRecord(r) for r in (res.data or [])]
                total = res.count if res.count is not None else len(items)
                return items, total
            except Exception as e:
                logger.error("Supabase get_user_reports error: %s", e)
                raise DatabaseError(f"Database error querying user reports: {e}")

        items = [r for r in _mock_reports_store.values() if str(r.get("user_id")) == str(user_id)]
        total = len(items)
        items.sort(
            key=lambda x: (
                x.get("created_at") if isinstance(x.get("created_at"), datetime) else datetime.min
            ),
            reverse=True,
        )
        return [ReportRecord(r) for r in items[offset : offset + page_size]], total

    async def get_admin_reports(
        self,
        moderation_status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReportRecord], int]:
        """
        Query reports for admin moderation with filtering and pagination.
        """
        offset = (page - 1) * page_size

        if self._client is not None:
            try:
                query = self._client.table("community_reports").select("*", count="exact")
                if moderation_status:
                    query = query.eq("moderation_status", moderation_status.upper())
                if category:
                    query = query.or_(f"report_reason.ilike.{category},threat_type.ilike.{category}")

                res = (
                    query.order("created_at", desc=True)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
                items = [ReportRecord(r) for r in (res.data or [])]
                total = res.count if res.count is not None else len(items)
                return items, total
            except Exception as e:
                logger.error("Supabase get_admin_reports error: %s", e)
                raise DatabaseError(f"Database error querying admin reports: {e}")

        items = list(_mock_reports_store.values())
        if moderation_status:
            target_status = moderation_status.strip().upper()
            items = [
                r for r in items if (r.get("moderation_status") or "").upper() == target_status
            ]
        if category:
            cat_target = category.strip().lower()
            items = [
                r
                for r in items
                if (r.get("report_reason") or "").lower() == cat_target
                or (r.get("category") or "").lower() == cat_target
            ]

        total = len(items)
        items.sort(
            key=lambda x: (
                x.get("created_at") if isinstance(x.get("created_at"), datetime) else datetime.min
            ),
            reverse=True,
        )
        return [ReportRecord(r) for r in items[offset : offset + page_size]], total

    async def update_report_moderation(
        self,
        report_id: uuid.UUID,
        moderator_id: uuid.UUID,
        update_in: CommunityReportModerationUpdate,
    ) -> ReportRecord:
        """
        Updates the moderation status and notes of a report.
        """
        now = datetime.now(timezone.utc)
        mod_status = update_in.moderation_status.upper()

        # Sync legacy report_status and default verification status
        legacy_status = "pending_review"
        verif_status = update_in.verification_status
        if mod_status == "APPROVED":
            legacy_status = "verified"
            if not verif_status:
                verif_status = "ADMIN_VERIFIED"
        elif mod_status == "REJECTED":
            legacy_status = "rejected"
            if not verif_status:
                verif_status = "DISPUTED"
        elif not verif_status:
            verif_status = "UNVERIFIED"

        patch_data: Dict[str, Any] = {
            "moderation_status": mod_status,
            "report_status": legacy_status,
            "verification_status": verif_status,
            "moderation_notes": update_in.moderation_notes,
            "moderator_id": str(moderator_id),
            "reviewed_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        if update_in.duplicate_of:
            patch_data["duplicate_of"] = str(update_in.duplicate_of)

        if self._client is not None:
            try:
                res = (
                    self._client.table("community_reports")
                    .update(patch_data)
                    .eq("id", str(report_id))
                    .execute()
                )
                if not res.data:
                    raise NotFoundError(f"Community report {report_id} not found.")
                rec_dict = dict(res.data[0])
                rec_dict["id"] = report_id
                return ReportRecord(rec_dict)
            except NotFoundError:
                raise
            except Exception as e:
                logger.error("Supabase update_report_moderation error: %s", e)
                raise DatabaseError(f"Database error updating moderation: {e}")

        # Local fallback
        if report_id not in _mock_reports_store:
            raise NotFoundError(f"Community report {report_id} not found.")

        rec = _mock_reports_store[report_id]
        rec.update(patch_data)
        rec["moderator_id"] = moderator_id
        rec["reviewed_at"] = now
        rec["updated_at"] = now
        if update_in.duplicate_of:
            rec["duplicate_of"] = update_in.duplicate_of
        return ReportRecord(rec)

    async def upvote_report(self, report_id: uuid.UUID) -> ReportRecord:
        """Increment upvotes count for an approved report."""
        if self._client is not None:
            try:
                curr = await self.get_report_by_id(report_id)
                if not curr:
                    raise NotFoundError(f"Community report {report_id} not found.")
                new_votes = int(curr.get("upvotes", 0)) + 1
                res = (
                    self._client.table("community_reports")
                    .update({"upvotes": new_votes})
                    .eq("id", str(report_id))
                    .execute()
                )
                rec = dict(res.data[0])
                rec["id"] = report_id
                return ReportRecord(rec)
            except NotFoundError:
                raise
            except Exception as e:
                logger.error("Supabase upvote_report error: %s", e)
                raise DatabaseError(f"Database error upvoting report: {e}")

        if report_id not in _mock_reports_store:
            raise NotFoundError(f"Community report {report_id} not found.")
        rec = _mock_reports_store[report_id]
        rec["upvotes"] = int(rec.get("upvotes", 0)) + 1
        return ReportRecord(rec)

    # ------------------------------------------------------------------ #
    # Legacy compatibility methods                                       #
    # ------------------------------------------------------------------ #

    async def get_community_reports(
        self,
        scan_id: Optional[uuid.UUID] = None,
        normalized_url: Optional[str] = None,
        limit: int = 50,
    ) -> List[ReportRecord]:
        """Legacy helper returning matching reports."""
        if self._client is not None:
            try:
                query = self._client.table("community_reports").select("*")
                if scan_id:
                    query = query.eq("scan_id", str(scan_id))
                elif normalized_url:
                    query = query.eq("normalized_url", normalized_url)
                res = query.order("created_at", desc=True).limit(limit).execute()
                return [ReportRecord(r) for r in (res.data or [])]
            except Exception as e:
                logger.error("Supabase select community_reports error: %s", e)
                raise DatabaseError(f"Database error fetching reports: {e}")

        results = list(_mock_reports_store.values())
        if scan_id:
            results = [r for r in results if r.get("scan_id") == scan_id]
        elif normalized_url:
            results = [r for r in results if r.get("normalized_url") == normalized_url]
        results.sort(key=lambda r: r.get("created_at", datetime.min), reverse=True)
        return [ReportRecord(r) for r in results[:limit]]

    async def get_verified_reports(self, limit: int = 50) -> List[ReportRecord]:
        items, _ = await self.get_public_reports(page=1, page_size=limit)
        return items
