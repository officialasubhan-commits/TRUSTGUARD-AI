"""
Scan History and Scan Results repository operations.
Interacts with public.scan_history and public.scan_results tables.
Enforces ownership validation and guest isolation.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.core.config import settings
from app.core.exceptions import DatabaseError, ForbiddenError, ScanNotFoundError
from app.database import connection
from app.schemas.history import (
    DailyScanActivity,
    PaginatedScanHistoryResponse,
    ScanHistorySummary,
    ScanStatisticsResponse,
)
from app.schemas.scan import (
    ScanHistoryResponse,
    ScanResultCreate,
    ScanResultResponse,
    ScanStatusUpdate,
)

logger = logging.getLogger("trustguard.repo.scan")

# In-memory stores for isolated testing / offline mode
_mock_scans_store: Dict[uuid.UUID, Dict[str, Any]] = {}
_mock_results_store: Dict[uuid.UUID, Dict[str, Any]] = {}


def _normalize_db_risk_level(level: Optional[str]) -> str:
    """
    Normalizes application-level risk classifications (e.g. 'LOW_RISK', 'MODERATE_RISK')
    to strictly match PostgreSQL CHECK constraint ('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN').
    """
    if not level:
        return "UNKNOWN"
    raw = str(level).upper().strip()
    mapping = {
        "SAFE": "SAFE",
        "MINIMAL": "SAFE",
        "LOW": "LOW",
        "LOW_RISK": "LOW",
        "MEDIUM": "MEDIUM",
        "MODERATE": "MEDIUM",
        "MODERATE_RISK": "MEDIUM",
        "HIGH": "HIGH",
        "HIGH_RISK": "HIGH",
        "CRITICAL": "CRITICAL",
        "CRITICAL_RISK": "CRITICAL",
        "UNKNOWN": "UNKNOWN",
    }
    return mapping.get(raw, "UNKNOWN")


class ScanRepository:
    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        """
        Retrieves the Supabase service-role client guaranteed to have administrative bypass privileges.
        Ensures PostgREST Authorization is set to SUPABASE_SERVICE_ROLE_KEY to prevent RLS failures.
        """
        c = self._client or connection.get_supabase_service_client()
        if c is not None and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                c.postgrest.auth(settings.SUPABASE_SERVICE_ROLE_KEY)
            except Exception:
                pass
        return c

    async def create_scan_record(
        self,
        submitted_url: str,
        normalized_url: str,
        url_hash: str,
        user_id: Optional[uuid.UUID] = None,
        is_guest: bool = False,
        ip_address: Optional[str] = None,
    ) -> ScanHistoryResponse:
        """
        Creates a new pending scan operation record.
        """
        scan_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        domain: Optional[str] = None
        try:
            domain = urlparse(normalized_url).hostname
        except Exception:
            pass

        record = {
            "id": str(scan_id),
            "user_id": str(user_id) if user_id else None,
            "submitted_url": submitted_url,
            "normalized_url": normalized_url,
            "domain": domain,
            "url_hash": url_hash,
            "scan_status": "pending",
            "risk_level": None,
            "trust_score": None,
            "risk_score": None,
            "assessment_status": None,
            "assessment_coverage": None,
            "scoring_version": None,
            "is_guest": is_guest,
            "ip_address": ip_address,
            "error_message": None,
            "created_at": now.isoformat(),
            "completed_at": None,
        }

        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("scan_history").insert(record).execute()
                )
                if res.data:
                    return ScanHistoryResponse.model_validate(res.data[0])
                raise DatabaseError("Database insert into scan_history returned empty response.")
            except Exception as e:
                logger.error("Supabase insert scan_history failed: %s", e)
                raise DatabaseError(
                    f"Failed to persist scan to database: {e}. "
                    "If using Supabase, ensure migration 000_full_schema.sql has been executed."
                ) from e

        # Local fallback (only when Supabase client is unconfigured)
        _mock_scans_store[scan_id] = {
            **record,
            "id": scan_id,
            "user_id": user_id,
            "created_at": now,
        }
        return ScanHistoryResponse.model_validate(_mock_scans_store[scan_id])

    async def update_scan_status(
        self,
        scan_id: uuid.UUID,
        status_update: ScanStatusUpdate,
    ) -> Optional[ScanHistoryResponse]:
        """
        Updates the scan status, risk level, trust score, or error message.
        """
        updates: Dict[str, Any] = {"scan_status": status_update.scan_status}
        if status_update.risk_level:
            updates["risk_level"] = _normalize_db_risk_level(status_update.risk_level)
        if status_update.trust_score is not None:
            updates["trust_score"] = status_update.trust_score
        if status_update.risk_score is not None:
            updates["risk_score"] = status_update.risk_score
        if status_update.assessment_status:
            updates["assessment_status"] = status_update.assessment_status
        if status_update.assessment_coverage is not None:
            updates["assessment_coverage"] = status_update.assessment_coverage
        if status_update.scoring_version:
            updates["scoring_version"] = status_update.scoring_version
        if status_update.error_message:
            updates["error_message"] = status_update.error_message
        if status_update.completed_at:
            updates["completed_at"] = status_update.completed_at.isoformat()
        elif status_update.scan_status in ("complete", "error"):
            updates["completed_at"] = datetime.now(timezone.utc).isoformat()

        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("scan_history").update(updates).eq("id", str(scan_id)).execute()
                )
                if res.data:
                    return ScanHistoryResponse.model_validate(res.data[0])
                raise ScanNotFoundError(f"Scan operation '{scan_id}' not found for status update.")
            except ScanNotFoundError:
                raise
            except Exception as e:
                logger.error("Supabase update scan_history failed: %s", e)
                raise DatabaseError(f"Database error updating scan status: {e}") from e

        if scan_id in _mock_scans_store:
            _mock_scans_store[scan_id].update(updates)
            if "completed_at" in updates:
                _mock_scans_store[scan_id]["completed_at"] = datetime.now(timezone.utc)
            return ScanHistoryResponse.model_validate(_mock_scans_store[scan_id])
        return None

    async def save_scan_results(
        self,
        result_in: ScanResultCreate,
    ) -> ScanResultResponse:
        """
        Persists detailed scan analysis findings into public.scan_results.
        """
        result_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        record = result_in.model_dump()
        record["id"] = str(result_id)
        record["scan_id"] = str(result_in.scan_id)
        record["created_at"] = now.isoformat()
        if record.get("ssl_expiry_date"):
            record["ssl_expiry_date"] = record["ssl_expiry_date"].isoformat()

        # Normalize overall_risk_level to match database CHECK constraint ('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN')
        record["overall_risk_level"] = _normalize_db_risk_level(record.get("overall_risk_level"))
        record["score_breakdown"] = record.get("score_breakdown") or {}

        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("scan_results").insert(record).execute()
                )
                if res.data:
                    return ScanResultResponse.model_validate(res.data[0])
                raise DatabaseError("Database insert into scan_results returned empty response.")
            except Exception as e:
                logger.error("Supabase insert scan_results failed: %s", e)
                raise DatabaseError(
                    f"Failed to persist scan results to database: {e}. "
                    "If using Supabase, ensure migration 000_full_schema.sql has been executed."
                ) from e

        # Local fallback (only when Supabase client is unconfigured)
        _mock_results_store[result_in.scan_id] = {
            **record,
            "id": result_id,
            "scan_id": result_in.scan_id,
            "created_at": now,
        }
        return ScanResultResponse.model_validate(_mock_results_store[result_in.scan_id])

    async def update_scan_results(
        self,
        scan_id: uuid.UUID,
        updates: Dict[str, Any],
    ) -> Optional[ScanResultResponse]:
        """
        Updates specific fields of an existing scan_results record
        (e.g. VirusTotal threat intel, SSL evaluation, ML predictions).
        """
        cli = self.client
        if cli is not None:
            try:
                res = await asyncio.to_thread(
                    lambda: cli.table("scan_results")
                    .update(updates)
                    .eq("scan_id", str(scan_id))
                    .execute()
                )
                if res.data:
                    return ScanResultResponse.model_validate(res.data[0])
                raise ScanNotFoundError(f"Scan results for '{scan_id}' not found for update.")
            except ScanNotFoundError:
                raise
            except Exception as e:
                logger.error("Supabase update scan_results failed: %s", e)
                raise DatabaseError(f"Database error updating scan results: {e}") from e

        # Local fallback (only when Supabase client is unconfigured)
        if scan_id in _mock_results_store:
            _mock_results_store[scan_id].update(updates)
            return ScanResultResponse.model_validate(_mock_results_store[scan_id])
        return None

    async def get_scan_by_id_with_ownership(
        self,
        scan_id: uuid.UUID,
        requesting_user_id: Optional[uuid.UUID] = None,
    ) -> Tuple[ScanHistoryResponse, Optional[ScanResultResponse]]:
        """
        Retrieves a scan and its associated result with ownership enforcement.

        Rules:
        - If scan does not exist -> ScanNotFoundError (404)
        - If scan belongs to a registered user:
            - If requesting_user_id == scan.user_id -> ALLOW
            - Otherwise -> ForbiddenError (403)
        - If scan is a guest scan (is_guest=True):
            - Anyone with the exact scan_id may access it.
            - However, guest scans are never listed in batch history queries.
        """
        scan_data: Optional[Dict[str, Any]] = None
        result_data: Optional[Dict[str, Any]] = None

        cli = self.client
        if cli is not None:
            try:
                s_res = await asyncio.to_thread(
                    lambda: cli.table("scan_history").select("*").eq("id", str(scan_id)).execute()
                )
                if not s_res.data:
                    raise ScanNotFoundError(f"Scan with ID '{scan_id}' not found.")
                scan_data = s_res.data[0]

                r_res = await asyncio.to_thread(
                    lambda: cli.table("scan_results")
                    .select("*")
                    .eq("scan_id", str(scan_id))
                    .execute()
                )
                result_data = r_res.data[0] if r_res.data else None
            except (ScanNotFoundError, ForbiddenError):
                raise
            except Exception as e:
                logger.error("Supabase error fetching scan %s: %s", scan_id, e)
                raise DatabaseError(f"Database error retrieving scan '{scan_id}': {e}") from e
        else:
            scan_data = _mock_scans_store.get(scan_id)
            result_data = _mock_results_store.get(scan_id)

        if not scan_data:
            raise ScanNotFoundError(f"Scan with ID '{scan_id}' not found.")

        scan_response = ScanHistoryResponse.model_validate(scan_data)

        # Ownership validation
        if not scan_response.is_guest:
            # Must be accessed by the owner
            if requesting_user_id is None or str(scan_response.user_id) != str(requesting_user_id):
                logger.warning(
                    "Ownership check failed for scan %s: requesting_user=%s, owner=%s",
                    scan_id,
                    requesting_user_id,
                    scan_response.user_id,
                )
                raise ForbiddenError("You do not have permission to access this private scan.")

        result_response = ScanResultResponse.model_validate(result_data) if result_data else None
        return scan_response, result_response

    async def get_user_scan_history(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ScanHistoryResponse]:
        """
        Retrieves the private scan history for an authenticated user.
        Guest scans are strictly excluded.
        """
        if self._client is not None:
            try:
                res = (
                    self._client.table("scan_history")
                    .select("*")
                    .eq("user_id", str(user_id))
                    .eq("is_guest", False)
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                return [ScanHistoryResponse.model_validate(r) for r in res.data]
            except Exception as e:
                logger.error("Supabase error fetching user history: %s", e)
                raise DatabaseError(f"Database error fetching scan history: {e}")

        # Local fallback
        user_scans = [
            ScanHistoryResponse.model_validate(s)
            for s in _mock_scans_store.values()
            if s.get("user_id") == user_id and not s.get("is_guest")
        ]
        user_scans.sort(key=lambda s: s.created_at, reverse=True)
        return user_scans[offset : offset + limit]

    async def get_all_user_scans_for_export(
        self,
        user_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all historical scans and associated threat metrics for an authenticated user
        for bulk export. Guest scans are strictly excluded.
        """
        user_id_str = str(user_id)
        if self._client is not None:
            try:
                # 1. Fetch all scan_history records for user
                res = (
                    self._client.table("scan_history")
                    .select("*")
                    .eq("user_id", user_id_str)
                    .eq("is_guest", False)
                    .order("created_at", desc=True)
                    .limit(5000)
                    .execute()
                )
                scans = res.data or []
                if not scans:
                    return []

                # 2. Fetch associated scan_results in batches of IDs
                scan_ids = [s["id"] for s in scans if "id" in s]
                results_map: Dict[str, Dict[str, Any]] = {}
                for i in range(0, len(scan_ids), 200):
                    batch_ids = scan_ids[i : i + 200]
                    r_res = (
                        self._client.table("scan_results")
                        .select("scan_id, phishing_probability, ml_prediction, ssl_status, ssl_valid")
                        .in_("scan_id", batch_ids)
                        .execute()
                    )
                    for r in (r_res.data or []):
                        results_map[str(r.get("scan_id"))] = r

                # 3. Merge metrics
                combined = []
                for s in scans:
                    s_id = str(s.get("id"))
                    r = results_map.get(s_id, {})
                    combined.append({
                        **s,
                        "phishing_probability": r.get("phishing_probability"),
                        "ml_prediction": r.get("ml_prediction"),
                        "ssl_status": r.get("ssl_status"),
                        "ssl_valid": r.get("ssl_valid"),
                    })
                return combined
            except Exception as e:
                logger.error("Supabase error fetching user export: %s", e)
                raise DatabaseError(f"Database error fetching scan export: {e}")

        # Local fallback
        scans = [
            s for s in _mock_scans_store.values()
            if str(s.get("user_id")) == user_id_str and not s.get("is_guest")
        ]
        scans.sort(key=lambda s: str(s.get("created_at", "")), reverse=True)
        combined = []
        for s in scans:
            s_id = s.get("id")
            r = _mock_results_store.get(s_id, {}) if s_id else {}
            combined.append({
                **s,
                "phishing_probability": r.get("phishing_probability"),
                "ml_prediction": r.get("ml_prediction"),
                "ssl_status": r.get("ssl_status"),
                "ssl_valid": r.get("ssl_valid"),
            })
        return combined

    async def get_user_scans_paginated(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
        assessment_status: Optional[str] = None,
        date_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "newest",
        sort_order: str = "desc",
    ) -> PaginatedScanHistoryResponse:
        """
        Retrieves paginated, filtered, and sorted private scans for an authenticated user.
        Guest scans are strictly excluded.
        """
        if self._client is not None:
            try:
                query = (
                    self._client.table("scan_history")
                    .select("*", count="exact")
                    .eq("user_id", str(user_id))
                    .eq("is_guest", False)
                )

                if search:
                    s_clean = search.strip()
                    query = query.or_(
                        f"domain.ilike.%{s_clean}%,submitted_url.ilike.%{s_clean}%,normalized_url.ilike.%{s_clean}%"
                    )

                if risk_level:
                    allowed = self._normalize_risk_filter(risk_level)
                    if allowed:
                        query = query.in_("risk_level", allowed)

                if assessment_status:
                    query = query.eq("assessment_status", assessment_status)

                dt_start, dt_end = self._resolve_date_boundaries(date_filter, start_date, end_date)
                if dt_start:
                    query = query.gte("created_at", dt_start.isoformat())
                if dt_end:
                    query = query.lte("created_at", dt_end.isoformat())

                order_col, is_desc = self._resolve_sorting(sort_by, sort_order)
                query = query.order(order_col, desc=is_desc)

                offset = (page - 1) * page_size
                query = query.range(offset, offset + page_size - 1)

                res = query.execute()
                total_items = res.count if res.count is not None else len(res.data)
                total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
                items = [self._map_to_summary(r) for r in res.data]

                return PaginatedScanHistoryResponse(
                    total_items=total_items,
                    total_pages=total_pages,
                    current_page=page,
                    page_size=page_size,
                    has_next=page < total_pages,
                    has_prev=page > 1 and total_pages > 0,
                    items=items,
                )
            except Exception as e:
                logger.error("Supabase paginated history error: %s", e)
                raise DatabaseError(f"Database error querying scan history: {e}")

        # Local fallback execution
        matched: List[Tuple[Dict[str, Any], str, datetime]] = []
        for s in _mock_scans_store.values():
            s_uid = s.get("user_id")
            if s_uid is None or str(s_uid) != str(user_id) or s.get("is_guest"):
                continue

            domain = s.get("domain")
            if not domain:
                try:
                    domain = urlparse(s.get("normalized_url", "")).hostname or ""
                except Exception:
                    domain = ""

            # 1. Search filter
            if search:
                s_lower = search.strip().lower()
                sub_lower = s.get("submitted_url", "").lower()
                norm_lower = s.get("normalized_url", "").lower()
                dom_lower = domain.lower()
                if (
                    s_lower not in sub_lower
                    and s_lower not in norm_lower
                    and s_lower not in dom_lower
                ):
                    continue

            # 2. Risk level filter
            if risk_level:
                allowed_levels = self._normalize_risk_filter(risk_level)
                if allowed_levels and s.get("risk_level") not in allowed_levels:
                    continue

            # 3. Assessment status filter
            if assessment_status:
                s_ass = s.get("assessment_status") or (
                    "COMPLETE" if s.get("scan_status") == "complete" else s.get("scan_status")
                )
                if s_ass != assessment_status:
                    continue

            # 4. Date filter
            c_at = s.get("created_at")
            if isinstance(c_at, str):
                c_at = datetime.fromisoformat(c_at)
            if c_at and c_at.tzinfo is None:
                c_at = c_at.replace(tzinfo=timezone.utc)

            dt_start, dt_end = self._resolve_date_boundaries(date_filter, start_date, end_date)
            if dt_start and c_at < dt_start:
                continue
            if dt_end and c_at > dt_end:
                continue

            matched.append((s, domain, c_at))

        # 5. Sorting
        order_col, is_desc = self._resolve_sorting(sort_by, sort_order)
        if order_col == "trust_score":
            matched.sort(
                key=lambda item: (
                    item[0].get("trust_score") is not None,
                    item[0].get("trust_score") if item[0].get("trust_score") is not None else -1,
                ),
                reverse=is_desc,
            )
        else:
            matched.sort(key=lambda item: item[2], reverse=is_desc)

        total_items = len(matched)
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
        offset = (page - 1) * page_size
        page_items = matched[offset : offset + page_size]
        items = [self._map_to_summary(m[0], m[1]) for m in page_items]

        return PaginatedScanHistoryResponse(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_prev=page > 1 and total_pages > 0,
            items=items,
        )

    async def delete_scan_record(
        self,
        scan_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> bool:
        """
        Deletes a scan record and cascades to scan_results and associated threat reports.
        Enforces strict ownership: only authenticated owners can delete their scans.
        """
        if self._client is not None:
            try:
                res = (
                    self._client.table("scan_history")
                    .select("id, user_id, is_guest")
                    .eq("id", str(scan_id))
                    .execute()
                )
                if not res.data:
                    raise ScanNotFoundError(f"Scan with ID '{scan_id}' not found.")
                record = res.data[0]
                if record.get("is_guest") or str(record.get("user_id")) != str(requesting_user_id):
                    logger.warning(
                        "Unauthorized delete attempt for scan %s by user %s",
                        scan_id,
                        requesting_user_id,
                    )
                    raise ForbiddenError("You do not have permission to delete this scan.")

                self._client.table("scan_history").delete().eq("id", str(scan_id)).eq(
                    "user_id", str(requesting_user_id)
                ).execute()
                return True
            except (ScanNotFoundError, ForbiddenError):
                raise
            except Exception as e:
                logger.error("Supabase error deleting scan %s: %s", scan_id, e)
                raise DatabaseError(f"Database error deleting scan: {e}")

        # Local fallback
        if scan_id not in _mock_scans_store:
            raise ScanNotFoundError(f"Scan with ID '{scan_id}' not found.")

        scan_item = _mock_scans_store[scan_id]
        if scan_item.get("is_guest") or str(scan_item.get("user_id")) != str(requesting_user_id):
            logger.warning(
                "Unauthorized delete attempt in mock store for scan %s by user %s",
                scan_id,
                requesting_user_id,
            )
            raise ForbiddenError("You do not have permission to delete this scan.")

        del _mock_scans_store[scan_id]
        if scan_id in _mock_results_store:
            del _mock_results_store[scan_id]

        from app.database.repositories.threat_repo import _mock_threats_store

        threats_to_del = [
            tid for tid, t in _mock_threats_store.items() if str(t.get("scan_id")) == str(scan_id)
        ]
        for tid in threats_to_del:
            del _mock_threats_store[tid]

        return True

    async def get_user_scan_statistics(
        self,
        user_id: uuid.UUID,
    ) -> ScanStatisticsResponse:
        """
        Computes aggregated security statistics for an authenticated user.
        Excludes guest scans and unauthorized records.
        """
        all_scans: List[Dict[str, Any]] = []
        if self._client is not None:
            try:
                res = (
                    self._client.table("scan_history")
                    .select("*")
                    .eq("user_id", str(user_id))
                    .eq("is_guest", False)
                    .order("created_at", desc=True)
                    .execute()
                )
                all_scans = res.data
            except Exception as e:
                logger.error("Supabase error calculating statistics: %s", e)
                raise DatabaseError(f"Database error fetching scan statistics: {e}")
        else:
            all_scans = [
                s
                for s in _mock_scans_store.values()
                if s.get("user_id")
                and str(s.get("user_id")) == str(user_id)
                and not s.get("is_guest")
            ]
            all_scans.sort(
                key=lambda s: (
                    s.get("created_at")
                    if isinstance(s.get("created_at"), datetime)
                    else datetime.fromisoformat(s.get("created_at"))
                ),
                reverse=True,
            )

        total_scans = len(all_scans)
        low_risk = 0
        moderate_risk = 0
        high_risk = 0
        critical_risk = 0
        incomplete = 0
        completed_scores: List[int] = []

        for s in all_scans:
            status = s.get("scan_status")
            level = s.get("risk_level")
            score = s.get("trust_score")
            ass_status = s.get("assessment_status")

            if (
                status in ("pending", "processing", "error")
                or score is None
                or ass_status == "INSUFFICIENT_DATA"
            ):
                incomplete += 1
            else:
                completed_scores.append(score)

            if level in ("LOW", "SAFE"):
                low_risk += 1
            elif level == "MEDIUM":
                moderate_risk += 1
            elif level == "HIGH":
                high_risk += 1
            elif level == "CRITICAL":
                critical_risk += 1

        avg_score = (
            round(sum(completed_scores) / len(completed_scores), 1) if completed_scores else None
        )
        recent_summaries = [self._map_to_summary(s) for s in all_scans[:5]]

        return ScanStatisticsResponse(
            total_scans=total_scans,
            low_risk_scans=low_risk,
            moderate_risk_scans=moderate_risk,
            high_risk_scans=high_risk,
            critical_risk_scans=critical_risk,
            incomplete_assessments=incomplete,
            average_trust_score=avg_score,
            recent_scans=recent_summaries,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_user_activity_timeline(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> List[DailyScanActivity]:
        """
        Aggregates daily scan counts and threat distributions across the specified historical window.
        Continuous calendar dates are populated with 0 counts if no scans took place.
        """
        days = max(1, min(90, days))
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days - 1)

        daily_buckets: Dict[str, Dict[str, int]] = {}
        for d in range(days):
            day_str = (start_date + timedelta(days=d)).strftime("%Y-%m-%d")
            daily_buckets[day_str] = {
                "scan_count": 0,
                "threat_count": 0,
                "safe_count": 0,
                "moderate_count": 0,
            }

        all_scans: List[Dict[str, Any]] = []
        if self._client is not None:
            try:
                res = (
                    self._client.table("scan_history")
                    .select("created_at, risk_level, scan_status")
                    .eq("user_id", str(user_id))
                    .eq("is_guest", False)
                    .gte("created_at", start_date.strftime("%Y-%m-%dT00:00:00Z"))
                    .execute()
                )
                all_scans = res.data or []
            except Exception as e:
                logger.error("Supabase error fetching activity timeline: %s", e)
                raise DatabaseError(f"Database error fetching activity timeline: {e}")
        else:
            all_scans = [
                s
                for s in _mock_scans_store.values()
                if s.get("user_id")
                and str(s.get("user_id")) == str(user_id)
                and not s.get("is_guest")
            ]

        for s in all_scans:
            c_at = s.get("created_at")
            if isinstance(c_at, str):
                try:
                    c_dt = datetime.fromisoformat(c_at.replace("Z", "+00:00"))
                except Exception:
                    continue
            elif isinstance(c_at, datetime):
                c_dt = c_at
            else:
                continue

            day_key = c_dt.strftime("%Y-%m-%d")
            if day_key in daily_buckets:
                daily_buckets[day_key]["scan_count"] += 1
                risk = str(s.get("risk_level") or "").upper()
                if risk in ("HIGH", "CRITICAL", "HIGH_RISK", "CRITICAL_RISK"):
                    daily_buckets[day_key]["threat_count"] += 1
                elif risk in ("LOW", "SAFE", "LOW_RISK"):
                    daily_buckets[day_key]["safe_count"] += 1
                elif risk in ("MEDIUM", "MODERATE", "MODERATE_RISK"):
                    daily_buckets[day_key]["moderate_count"] += 1

        return [
            DailyScanActivity(
                date=k,
                scan_count=v["scan_count"],
                threat_count=v["threat_count"],
                safe_count=v["safe_count"],
                moderate_count=v["moderate_count"],
            )
            for k, v in sorted(daily_buckets.items())
        ]

    # ---------------------------------------------------------------------- #
    # Static Data Formatting & Query Helpers                                 #
    # ---------------------------------------------------------------------- #

    @staticmethod
    def _normalize_risk_filter(risk_filter: str) -> List[str]:
        rf = risk_filter.strip().upper()
        if rf in ("LOW_RISK", "LOW", "SAFE"):
            return ["LOW", "SAFE"]
        if rf in ("MODERATE_RISK", "MEDIUM", "MODERATE"):
            return ["MEDIUM"]
        if rf in ("HIGH_RISK", "HIGH"):
            return ["HIGH"]
        if rf in ("CRITICAL_RISK", "CRITICAL"):
            return ["CRITICAL"]
        if rf in ("INSUFFICIENT_DATA", "UNKNOWN"):
            return ["UNKNOWN"]
        return [rf]

    @staticmethod
    def _resolve_date_boundaries(
        date_filter: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        now = datetime.now(timezone.utc)
        if date_filter == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, None
        if date_filter == "last_7_days":
            return now - timedelta(days=7), None
        if date_filter == "last_30_days":
            return now - timedelta(days=30), None
        s = (
            start_date.replace(tzinfo=timezone.utc)
            if start_date and start_date.tzinfo is None
            else start_date
        )
        e = (
            end_date.replace(tzinfo=timezone.utc)
            if end_date and end_date.tzinfo is None
            else end_date
        )
        return s, e

    @staticmethod
    def _resolve_sorting(sort_by: str, sort_order: str) -> Tuple[str, bool]:
        is_desc = sort_order.lower() == "desc"
        sb = sort_by.lower()
        if sb in ("newest", "created_at"):
            return "created_at", (True if sb == "newest" else is_desc)
        if sb == "oldest":
            return "created_at", False
        if sb in ("highest_score", "lowest_score", "trust_score"):
            return "trust_score", (
                True if sb == "highest_score" else (False if sb == "lowest_score" else is_desc)
            )
        return "created_at", is_desc

    @staticmethod
    def _map_to_summary(
        data: Dict[str, Any], domain_override: Optional[str] = None
    ) -> ScanHistorySummary:
        domain = domain_override or data.get("domain")
        if not domain:
            try:
                domain = urlparse(data.get("normalized_url", "")).hostname or ""
            except Exception:
                domain = ""

        trust_score = data.get("trust_score")
        risk_score = data.get("risk_score")
        if risk_score is None and trust_score is not None:
            risk_score = 100 - trust_score

        risk_level = data.get("risk_level")
        risk_label: Optional[str] = None
        if trust_score is not None:
            if trust_score >= 80:
                risk_label = "LOW RISK"
            elif trust_score >= 60:
                risk_label = "MODERATE RISK"
            elif trust_score >= 30:
                risk_label = "HIGH RISK"
            else:
                risk_label = "CRITICAL RISK"
        elif risk_level == "UNKNOWN":
            risk_label = "INSUFFICIENT DATA"

        cov = data.get("assessment_coverage")
        cov_pct = int(round(cov * 100)) if cov is not None else None

        c_at = data.get("created_at")
        if isinstance(c_at, str):
            c_at = datetime.fromisoformat(c_at)
        comp_at = data.get("completed_at")
        if isinstance(comp_at, str):
            comp_at = datetime.fromisoformat(comp_at)

        scan_id_val = data.get("id") or data.get("scan_id")
        if isinstance(scan_id_val, str):
            scan_id_val = uuid.UUID(scan_id_val)

        return ScanHistorySummary(
            scan_id=scan_id_val,
            domain=domain,
            submitted_url=data.get("submitted_url", ""),
            normalized_url=data.get("normalized_url", ""),
            scan_status=data.get("scan_status", "pending"),
            digital_trust_score=trust_score,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_label=risk_label,
            assessment_status=data.get("assessment_status"),
            assessment_coverage=cov,
            coverage_percentage=cov_pct,
            scoring_version=data.get("scoring_version"),
            created_at=c_at,
            completed_at=comp_at,
        )

    async def get_scans_by_domain(
        self, domain: str, limit: int = 20
    ) -> List[ScanHistoryResponse]:
        """
        Retrieves recent historical scans for a specific domain to compute reputation trends.
        """
        norm_domain = domain.lower().strip()
        client = self.client
        if client is not None:
            try:
                def _query():
                    return (
                        client.table("scan_history")
                        .select("*")
                        .eq("domain", norm_domain)
                        .order("created_at", desc=True)
                        .limit(limit)
                        .execute()
                    )

                res = await asyncio.to_thread(_query)
                if res and res.data:
                    return [ScanHistoryResponse.model_validate(r) for r in res.data]
            except Exception as e:
                logger.debug("Remote get_scans_by_domain query failed: %s", e)

        # In-memory fallback
        results = []
        for record in _mock_scans_store.values():
            if record.get("domain", "").lower() == norm_domain:
                try:
                    results.append(ScanHistoryResponse.model_validate(record))
                except Exception:
                    continue
        results.sort(
            key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return results[:limit]
