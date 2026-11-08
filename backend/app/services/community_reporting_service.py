"""
Community Threat Reporting & Intelligence Service for TrustGuard AI.
Handles URL validation, RFC normalisation, deduplication, privacy sanitisation,
and administrative moderation workflows.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidURLError,
    NotFoundError,
)
from app.core.security import AuthenticatedUser
from app.database.repositories.report_repo import ReportRepository
from app.schemas.report import (
    CommunityConfirmationToggleResponse,
    CommunityReportAdminResponse,
    CommunityReportCreate,
    CommunityReportFlagCreate,
    CommunityReportFlagResponse,
    CommunityReportModerationUpdate,
    CommunityReportPublicResponse,
    CommunityReportUserResponse,
    CommunityStatisticsResponse,
    PaginatedCommunityReports,
    Web3IntegrityProofResponse,
)
from app.services.url_validator import validate_url_static
from app.services.web3_integrity_service import get_web3_service
from app.utils.url_normalizer import normalize_url

logger = logging.getLogger("trustguard.service.community_reports")


class CommunityReportingService:
    """
    Business logic for community-driven threat reports and collaborative intelligence.
    """

    def __init__(self, repo: Optional[ReportRepository] = None):
        self._repo = repo or ReportRepository()

    async def submit_report(
        self,
        current_user: AuthenticatedUser,
        report_in: CommunityReportCreate,
    ) -> CommunityReportUserResponse:
        """
        Validate, normalise, check duplicates, and persist a new community threat report.
        """
        raw_url = report_in.submitted_url.strip()

        # 1. URL Static Validation
        val_result = validate_url_static(raw_url)
        if not val_result.is_valid:
            logger.warning(
                "Rejected community report URL submission: %s (reason: %s)",
                raw_url,
                val_result.error_message,
            )
            raise InvalidURLError(val_result.error_message or "Invalid URL format.")

        # 2. Canonical Normalisation & Domain Extraction
        try:
            norm_url = normalize_url(raw_url)
        except Exception as e:
            raise InvalidURLError(f"Failed to normalise URL: {e}")

        parsed = urlparse(norm_url)
        domain = (parsed.hostname or "").lower().rstrip(".")

        # 3. Deduplication & Spam Protection
        # Check if the same user has already reported this URL
        user_duplicates = await self._repo.find_duplicates(
            normalized_url=norm_url,
            user_id=current_user.user_id,
        )
        if user_duplicates:
            logger.info(
                "Duplicate report rejected for user %s on URL %s",
                current_user.user_id,
                norm_url,
            )
            raise ConflictError("You have already submitted a threat report for this website.")

        # Check if any report already exists from other users
        all_duplicates = await self._repo.find_duplicates(normalized_url=norm_url)
        duplicate_of: Optional[uuid.UUID] = None
        if all_duplicates:
            # Link to the earliest submitted report
            canonical = min(
                all_duplicates,
                key=lambda x: str(x.get("created_at")),
            )
            raw_dup_id = canonical.get("id")
            if raw_dup_id:
                duplicate_of = uuid.UUID(raw_dup_id) if isinstance(raw_dup_id, str) else raw_dup_id

        # 4. Persistence
        created_record = await self._repo.create_community_report(
            user_id=current_user.user_id,
            report_in=report_in,
            normalized_url=norm_url,
            domain=domain,
            duplicate_of=duplicate_of,
        )

        logger.info(
            "Community threat report %s submitted by user %s for domain %s (duplicate_of=%s)",
            created_record.get("id"),
            current_user.user_id,
            domain,
            duplicate_of,
        )

        return CommunityReportUserResponse.model_validate(created_record)

    async def get_public_reports(
        self,
        domain: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "newest",
        current_user: Optional[AuthenticatedUser] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedCommunityReports[CommunityReportPublicResponse]:
        """
        Retrieve approved and reviewed, publicly visible threat reports with sanitized fields.
        Excludes submitter identity and administrative internal notes.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        user_id = current_user.user_id if current_user else None

        records, total = await self._repo.get_public_reports(
            domain=domain,
            category=category,
            status=status,
            search=search,
            sort_by=sort_by,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )

        items = [CommunityReportPublicResponse.model_validate(r) for r in records]
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedCommunityReports(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_community_statistics(self) -> CommunityStatisticsResponse:
        """
        Retrieve aggregate platform community reporting metrics.
        """
        stats_dict = await self._repo.get_community_statistics()
        return CommunityStatisticsResponse.model_validate(stats_dict)

    async def toggle_confirmation(
        self,
        report_id: uuid.UUID,
        current_user: AuthenticatedUser,
    ) -> CommunityConfirmationToggleResponse:
        """
        Toggle community confirmation by an authenticated user.
        Enforces one active confirmation per user per report.
        """
        report = await self._repo.get_report_by_id(report_id)
        if not report:
            raise NotFoundError(f"Threat report '{report_id}' was not found.")

        confirmed, new_total = await self._repo.toggle_confirmation(
            report_id=report_id,
            user_id=current_user.user_id,
        )

        action_msg = "Suspicious activity confirmed." if confirmed else "Confirmation withdrawn."
        logger.info(
            "User %s toggled confirmation on report %s -> confirmed=%s, total=%s",
            current_user.user_id,
            report_id,
            confirmed,
            new_total,
        )

        return CommunityConfirmationToggleResponse(
            report_id=report_id,
            confirmed=confirmed,
            total_confirmations=new_total,
            message=action_msg,
        )

    async def flag_report(
        self,
        report_id: uuid.UUID,
        current_user: AuthenticatedUser,
        flag_in: CommunityReportFlagCreate,
    ) -> CommunityReportFlagResponse:
        """
        Record a community flag for abusive or inaccurate reports.
        """
        report = await self._repo.get_report_by_id(report_id)
        if not report:
            raise NotFoundError(f"Threat report '{report_id}' was not found.")

        rec = await self._repo.flag_report(
            report_id=report_id,
            user_id=current_user.user_id,
            flag_reason=flag_in.flag_reason,
            notes=flag_in.notes,
        )

        logger.info(
            "User %s flagged report %s for reason: %s",
            current_user.user_id,
            report_id,
            flag_in.flag_reason,
        )

        return CommunityReportFlagResponse(
            id=uuid.UUID(rec["id"]) if isinstance(rec["id"], str) else rec["id"],
            report_id=report_id,
            flag_reason=flag_in.flag_reason,
            created_at=datetime.fromisoformat(rec["created_at"]) if isinstance(rec["created_at"], str) else rec["created_at"],
            message="Flag submitted for administrative review.",
        )

    async def get_integrity_proof(
        self,
        report_id: uuid.UUID,
    ) -> Web3IntegrityProofResponse:
        """
        Produce a canonical cryptographic proof of integrity for a verified community report.
        """
        report = await self._repo.get_report_by_id(report_id)
        if not report:
            raise NotFoundError(f"Threat report '{report_id}' was not found.")

        web3_svc = get_web3_service()
        return await web3_svc.generate_or_verify_proof(report)

    async def get_report_detail(
        self,
        report_id: uuid.UUID,
        current_user: Optional[AuthenticatedUser] = None,
    ) -> Any:
        """
        Retrieve report details enforcing privacy and ownership boundaries:
        - Approved reports: accessible to anyone (anonymized for public, full for admin/owner).
        - Pending/rejected reports: accessible ONLY to submitter or admins.
        - Non-authorized requests return 404 to avoid ID enumeration.
        """
        record = await self._repo.get_report_by_id(report_id)
        if not record:
            raise NotFoundError(f"Threat report '{report_id}' was not found.")

        mod_status = str(record.get("moderation_status", "PENDING")).upper()
        record_owner_id = str(record.get("user_id"))
        is_owner = current_user is not None and str(current_user.user_id) == record_owner_id
        is_admin = current_user is not None and current_user.is_admin

        if mod_status in ("APPROVED", "VERIFIED"):
            if is_admin:
                return CommunityReportAdminResponse.model_validate(record)
            if is_owner:
                return CommunityReportUserResponse.model_validate(record)
            return CommunityReportPublicResponse.model_validate(record)

        # For non-approved reports, only owner and admin can view
        if is_admin:
            return CommunityReportAdminResponse.model_validate(record)
        if is_owner:
            return CommunityReportUserResponse.model_validate(record)

        # Unauthorized viewer trying to view an unapproved report
        raise NotFoundError(f"Threat report '{report_id}' was not found.")

    async def get_user_reports(
        self,
        current_user: AuthenticatedUser,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedCommunityReports[CommunityReportUserResponse]:
        """
        Retrieve all reports submitted by the requesting authenticated user.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        records, total = await self._repo.get_user_reports(
            user_id=current_user.user_id,
            page=page,
            page_size=page_size,
        )

        items = [CommunityReportUserResponse.model_validate(r) for r in records]
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedCommunityReports(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def admin_get_reports(
        self,
        moderator: AuthenticatedUser,
        moderation_status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedCommunityReports[CommunityReportAdminResponse]:
        """
        Administrative retrieval of all community reports for moderation.
        Requires admin privileges.
        """
        if not moderator.is_admin:
            raise ForbiddenError("Administrator privileges required.")

        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        records, total = await self._repo.get_admin_reports(
            moderation_status=moderation_status,
            category=category,
            page=page,
            page_size=page_size,
        )

        items = [CommunityReportAdminResponse.model_validate(r) for r in records]
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedCommunityReports(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def admin_moderate_report(
        self,
        moderator: AuthenticatedUser,
        report_id: uuid.UUID,
        update_in: CommunityReportModerationUpdate,
    ) -> CommunityReportAdminResponse:
        """
        Moderate a community report (Approve, Reject, Duplicate, Under Review).
        Logs audit record with moderator ID and rationale.
        """
        if not moderator.is_admin:
            raise ForbiddenError("Administrator privileges required.")

        existing = await self._repo.get_report_by_id(report_id)
        if not existing:
            raise NotFoundError(f"Community report '{report_id}' was not found.")

        old_status = existing.get("moderation_status")
        updated = await self._repo.update_report_moderation(
            report_id=report_id,
            moderator_id=moderator.user_id,
            update_in=update_in,
        )

        logger.info(
            "AUDIT: Admin %s transitioned report %s from %s to %s. Notes: %s",
            moderator.user_id,
            report_id,
            old_status,
            update_in.moderation_status,
            update_in.moderation_notes or "None",
        )

        return CommunityReportAdminResponse.model_validate(updated)

    async def upvote_report(
        self,
        report_id: uuid.UUID,
        current_user: Optional[AuthenticatedUser] = None,
    ) -> Dict[str, Any]:
        """
        Increment the upvote consensus counter on an approved community report.
        """
        report = await self._repo.get_report_by_id(report_id)
        if not report:
            raise NotFoundError(f"Community report '{report_id}' was not found.")

        mod_status = str(report.get("moderation_status", "PENDING")).upper()
        if mod_status not in ("APPROVED", "VERIFIED"):
            raise NotFoundError(f"Community report '{report_id}' is not approved for voting.")

        updated = await self._repo.upvote_report(report_id)
        logger.info(
            "Report %s upvoted. New vote count: %s",
            report_id,
            updated.get("upvotes", 0),
        )

        return {
            "id": report_id,
            "upvotes": updated.get("upvotes", 0),
            "message": "Report upvoted successfully.",
        }


# Singleton service provider
_community_service_instance: Optional[CommunityReportingService] = None


def get_community_service() -> CommunityReportingService:
    global _community_service_instance
    if _community_service_instance is None:
        _community_service_instance = CommunityReportingService()
    return _community_service_instance
