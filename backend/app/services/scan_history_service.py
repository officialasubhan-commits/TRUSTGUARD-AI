"""
Scan History & Security Report Management Service.
Coordinates retrieval, filtering, pagination, deletion, and statistical aggregation
of historical website scans while enforcing strict ownership and historical integrity.
"""

from __future__ import annotations

import csv
import io
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from app.core.exceptions import ForbiddenError, ScanNotFoundError
from app.database.repositories.scan_repo import ScanRepository
from app.schemas.history import (
    DailyScanActivity,
    DetailedSecurityReportResponse,
    ExportableSecurityReport,
    PaginatedScanHistoryResponse,
    ScanDeleteResponse,
    ScanStatisticsResponse,
)
from app.schemas.risk_scoring import FindingItem

logger = logging.getLogger("trustguard.service.history")


class ScanHistoryService:
    def __init__(self, scan_repo: Optional[ScanRepository] = None):
        self._scan_repo = scan_repo or ScanRepository()

    async def get_user_history(
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
        Retrieves paginated, filtered, and sorted historical scans for an authenticated user.
        Guest scans are strictly excluded.
        """
        # Enforce page size guardrails
        validated_page_size = max(1, min(100, page_size))
        validated_page = max(1, page)

        logger.info(
            "Fetching scan history: user=%s page=%d size=%d search=%s risk=%s",
            user_id,
            validated_page,
            validated_page_size,
            search,
            risk_level,
        )

        return await self._scan_repo.get_user_scans_paginated(
            user_id=user_id,
            page=validated_page,
            page_size=validated_page_size,
            search=search,
            risk_level=risk_level,
            assessment_status=assessment_status,
            date_filter=date_filter,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_detailed_report(
        self,
        scan_id: uuid.UUID,
        requesting_user_id: Optional[uuid.UUID] = None,
    ) -> DetailedSecurityReportResponse:
        """
        Retrieves the complete historical security report for a specific scan.
        Enforces strict ownership:
        - If scan is registered and requesting_user != scan.user_id -> 404 (prevents enumeration).
        - If scan is guest -> accessible via direct UUID knowledge.
        - Historical scores and model metadata are preserved verbatim without recalculation.
        """
        t_report_start = time.perf_counter()
        try:
            scan_hist, scan_res = await self._scan_repo.get_scan_by_id_with_ownership(
                scan_id=scan_id,
                requesting_user_id=requesting_user_id,
            )
        except ForbiddenError:
            # Mask existence of another user's scan to prevent enumeration probes
            logger.warning(
                "Masking forbidden scan %s as 404 for requester %s", scan_id, requesting_user_id
            )
            raise ScanNotFoundError(f"Scan with ID '{scan_id}' not found.")

        domain = scan_hist.domain
        if not domain:
            try:
                domain = urlparse(scan_hist.normalized_url).hostname or ""
            except Exception:
                domain = ""

        # Extract breakdown data from persisted scan_results
        breakdown = scan_res.score_breakdown if scan_res and scan_res.score_breakdown else {}

        risk_indicators = [
            FindingItem.model_validate(i) for i in breakdown.get("risk_indicators", [])
        ]
        positive_indicators = [
            FindingItem.model_validate(i) for i in breakdown.get("positive_indicators", [])
        ]
        unknown_indicators = [
            FindingItem.model_validate(i) for i in breakdown.get("unknown_indicators", [])
        ]
        recommendations = breakdown.get("recommendations", [])
        summary = breakdown.get("summary") or (scan_res.analysis_summary if scan_res else None)
        module_scores = breakdown.get("module_scores", {})
        high_severity_override = breakdown.get("high_severity_override", False)
        override_reason = breakdown.get("override_reason")

        cov = scan_hist.assessment_coverage or breakdown.get("assessment_coverage")
        cov_pct = int(round(cov * 100)) if cov is not None else breakdown.get("coverage_percentage")

        risk_score = scan_hist.risk_score
        if risk_score is None and scan_hist.trust_score is not None:
            risk_score = 100 - scan_hist.trust_score

        # Format human-readable risk label
        risk_label = breakdown.get("risk_label")
        if not risk_label and scan_hist.trust_score is not None:
            if scan_hist.trust_score >= 80:
                risk_label = "LOW RISK"
            elif scan_hist.trust_score >= 60:
                risk_label = "MODERATE RISK"
            elif scan_hist.trust_score >= 30:
                risk_label = "HIGH RISK"
            else:
                risk_label = "CRITICAL RISK"
        elif not risk_label and scan_hist.risk_level == "UNKNOWN":
            risk_label = "INSUFFICIENT DATA"

        resp = DetailedSecurityReportResponse(
            scan_id=scan_hist.id,
            original_url=scan_hist.submitted_url,
            normalized_url=scan_hist.normalized_url,
            domain=domain,
            is_guest=scan_hist.is_guest,
            scan_status=scan_hist.scan_status,
            digital_trust_score=scan_hist.trust_score,
            risk_score=risk_score,
            risk_level=scan_hist.risk_level,
            risk_label=risk_label,
            assessment_status=scan_hist.assessment_status or breakdown.get("assessment_status"),
            assessment_coverage=cov,
            coverage_percentage=cov_pct,
            high_severity_override=high_severity_override,
            override_reason=override_reason,
            scoring_version=scan_hist.scoring_version or breakdown.get("scoring_version"),
            model_version=scan_res.ml_prediction if scan_res else None,
            submitted_at=scan_hist.created_at,
            completed_at=scan_hist.completed_at,
            summary=summary,
            recommendations=recommendations,
            risk_indicators=risk_indicators,
            positive_indicators=positive_indicators,
            unknown_indicators=unknown_indicators,
            module_scores=module_scores,
            url_analysis={
                "url_score": scan_res.url_score if scan_res else None,
                "indicators": scan_res.url_risk_indicators if scan_res else [],
            }
            if scan_res and (scan_res.url_score is not None or scan_res.url_risk_indicators)
            else None,
            virustotal_findings={
                "detection_count": scan_res.virustotal_detection_count,
                "total_engines": scan_res.virustotal_total_engines,
                "status": scan_res.threat_intelligence_status,
                "vt_score": scan_res.vt_score,
                "vt_raw": getattr(scan_res, "vt_raw", None),
            }
            if scan_res and scan_res.virustotal_total_engines
            else None,
            ml_phishing_prediction={
                "phishing_probability": scan_res.phishing_probability,
                "prediction": scan_res.ml_prediction,
                "ml_score": scan_res.ml_score,
                "features": scan_res.ml_features,
            }
            if scan_res and scan_res.ml_prediction
            else None,
            ssl_tls_validation={
                "ssl_status": scan_res.ssl_status,
                "ssl_valid": scan_res.ssl_valid,
                "ssl_issuer": scan_res.ssl_issuer,
                "ssl_expiry_date": scan_res.ssl_expiry_date,
                "ssl_days_remaining": scan_res.ssl_days_remaining,
                "ssl_score": scan_res.ssl_score,
                "ssl_raw": getattr(scan_res, "ssl_raw", None),
            }
            if scan_res and scan_res.ssl_status
            else None,
        )

        t_report_ms = (time.perf_counter() - t_report_start) * 1000
        logger.info(
            "[TIMING] Report generation & delivery: duration=%.2fms scan_id=%s is_guest=%s status=%s",
            t_report_ms,
            scan_id,
            scan_hist.is_guest,
            scan_hist.scan_status,
        )
        return resp

    async def delete_scan(
        self,
        scan_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> ScanDeleteResponse:
        """
        Deletes a scan record belonging to the authenticated user.
        Rejects deletion attempts for other users' records or guest records.
        """
        try:
            await self._scan_repo.delete_scan_record(
                scan_id=scan_id,
                requesting_user_id=requesting_user_id,
            )
        except ForbiddenError:
            # Mask existence of forbidden record
            raise ScanNotFoundError(f"Scan with ID '{scan_id}' not found.")

        logger.info("Scan deleted: scan_id=%s user_id=%s", scan_id, requesting_user_id)
        return ScanDeleteResponse(
            success=True,
            scan_id=scan_id,
            message="Scan record and associated analysis findings successfully deleted.",
            deleted_at=datetime.now(timezone.utc),
        )

    async def get_user_statistics(
        self,
        user_id: uuid.UUID,
    ) -> ScanStatisticsResponse:
        """
        Calculates aggregate scanning statistics for an authenticated user.
        Excludes other users and guest scans.
        """
        logger.info("Computing scan statistics for user: %s", user_id)
        return await self._scan_repo.get_user_scan_statistics(user_id=user_id)

    async def get_activity_timeline(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> List[DailyScanActivity]:
        """
        Retrieves continuous daily scan activity and threat distribution for the specified window.
        """
        logger.info("Computing scan activity timeline for user %s: window=%d days", user_id, days)
        return await self._scan_repo.get_user_activity_timeline(user_id=user_id, days=days)

    async def export_security_report(
        self,
        scan_id: uuid.UUID,
        requesting_user_id: Optional[uuid.UUID] = None,
    ) -> ExportableSecurityReport:
        """
        Generates a sanitized, shareable security report formatted for export.
        """
        detail = await self.get_detailed_report(
            scan_id=scan_id,
            requesting_user_id=requesting_user_id,
        )

        return ExportableSecurityReport(
            report_id=f"TGA-REP-{str(detail.scan_id)[:8].upper()}",
            target_url=detail.original_url,
            domain=detail.domain,
            digital_trust_score=detail.digital_trust_score,
            risk_level=detail.risk_level,
            risk_label=detail.risk_label,
            assessment_status=detail.assessment_status or "COMPLETE",
            coverage_percentage=detail.coverage_percentage,
            summary=detail.summary,
            recommendations=detail.recommendations,
            risk_indicators=[i.model_dump() for i in detail.risk_indicators],
            positive_indicators=[i.model_dump() for i in detail.positive_indicators],
            unknown_indicators=[i.model_dump() for i in detail.unknown_indicators],
            scan_timestamp=detail.submitted_at,
            scoring_version=detail.scoring_version,
            platform="TrustGuard AI",
        )

    async def export_user_scan_history_csv(
        self,
        user_id: uuid.UUID,
    ) -> tuple[str, str]:
        """
        Exports the authenticated user's complete scan history as RFC-4180 compliant CSV.
        Includes CSV formula-injection neutralization on user-controlled fields.
        Returns: (csv_string, filename)
        """
        scans = await self._scan_repo.get_all_user_scans_for_export(user_id)
        now_utc = datetime.now(timezone.utc)
        filename = f"trustguard-scan-history-{now_utc.strftime('%Y-%m-%d')}.csv"

        def _sanitize(val: Any) -> str:
            if val is None:
                return ""
            s = str(val)
            # Neutralize spreadsheet formula injection characters
            if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
                return "'" + s
            return s

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header Row
        writer.writerow([
            "Scan ID",
            "Original URL",
            "Normalized Domain",
            "Scan Date & Time (UTC)",
            "Trust Score",
            "Risk Classification",
            "Phishing Risk",
            "SSL/TLS Status",
            "Scan Status",
        ])

        for s in scans:
            # Parse created_at safely
            created_raw = s.get("created_at")
            if isinstance(created_raw, datetime):
                created_str = created_raw.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(created_raw, str):
                try:
                    dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                    created_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    created_str = created_raw
            else:
                created_str = ""

            # Trust score formatting (handles both trust_score and digital_trust_score keys)
            score = s.get("trust_score") if s.get("trust_score") is not None else s.get("digital_trust_score")
            score_str = f"{score}" if score is not None else ""

            # Risk classification (handles both risk_level and overall_risk_level keys)
            risk_classification = s.get("risk_level") or s.get("overall_risk_level") or ""

            # Phishing risk description
            p_prob = s.get("phishing_probability")
            ml_pred = s.get("ml_prediction")
            if p_prob is not None:
                phishing_str = f"{round(float(p_prob) * 100, 1)}% ({ml_pred or 'Predicted'})"
            elif ml_pred:
                phishing_str = str(ml_pred)
            else:
                phishing_str = ""

            # SSL/TLS status description
            ssl_st = s.get("ssl_status") or ("VALID" if s.get("ssl_valid") else "")

            writer.writerow([
                _sanitize(s.get("id")),
                _sanitize(s.get("submitted_url")),
                _sanitize(s.get("domain")),
                _sanitize(created_str),
                _sanitize(score_str),
                _sanitize(risk_classification),
                _sanitize(phishing_str),
                _sanitize(ssl_st),
                _sanitize(s.get("scan_status")),
            ])

        return output.getvalue(), filename


# Global singleton instance
_scan_history_service_instance: Optional[ScanHistoryService] = None


def get_scan_history_service() -> ScanHistoryService:
    """Returns the cached singleton instance of ScanHistoryService."""
    global _scan_history_service_instance
    if _scan_history_service_instance is None:
        _scan_history_service_instance = ScanHistoryService()
    return _scan_history_service_instance
