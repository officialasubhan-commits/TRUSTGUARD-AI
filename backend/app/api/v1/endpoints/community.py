"""
Community Threat Reporting endpoints for TrustGuard AI.
Allows authenticated users to submit suspicious URLs, view their own submission history,
and provides public access to community-verified threat intelligence.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.security import (
    AuthenticatedUser,
    get_current_user,
    get_optional_user,
)
from app.schemas.report import (
    CommunityConfirmationToggleResponse,
    CommunityReportCreate,
    CommunityReportFlagCreate,
    CommunityReportFlagResponse,
    CommunityReportPublicResponse,
    CommunityReportUserResponse,
    CommunityStatisticsResponse,
    PaginatedCommunityReports,
    Web3IntegrityProofResponse,
)
from app.services.community_reporting_service import (
    CommunityReportingService,
    get_community_service,
)

logger = logging.getLogger("trustguard.api.community")

router = APIRouter()


@router.get(
    "/statistics",
    response_model=CommunityStatisticsResponse,
    summary="Community Overview Statistics",
    description="Retrieve aggregate platform telemetry: total, pending, verified, resolved, and active confirmations.",
)
async def get_community_statistics(
    service: CommunityReportingService = Depends(get_community_service),
) -> CommunityStatisticsResponse:
    """Aggregate statistics for public community overview dashboard."""
    return await service.get_community_statistics()


@router.post(
    "/reports",
    response_model=CommunityReportUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Community Threat Report",
    description=(
        "Submit a suspicious website URL with threat category and evidence for community review. "
        "Requires authenticated user session."
    ),
)
async def submit_report(
    report_in: CommunityReportCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> CommunityReportUserResponse:
    """Submit a new threat report for moderation and community consensus."""
    return await service.submit_report(current_user=current_user, report_in=report_in)


@router.get(
    "/reports",
    response_model=PaginatedCommunityReports[CommunityReportPublicResponse],
    summary="List Public Threat Reports",
    description=(
        "Public endpoint returning community threat reports. "
        "Supports filtering by domain, category, status, and search query. "
        "Sensitive reporter identity and internal reviewer notes are strictly redacted."
    ),
)
async def list_public_reports(
    domain: Optional[str] = Query(None, description="Filter by target domain or subdomain"),
    category: Optional[str] = Query(None, description="Filter by threat category"),
    status: Optional[str] = Query(None, description="Filter by report status (ALL, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED)"),
    search: Optional[str] = Query(None, description="Search term in URL, description, or brand"),
    sort_by: Optional[str] = Query("newest", description="Sort order (newest, most_confirmed)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> PaginatedCommunityReports[CommunityReportPublicResponse]:
    """Query verified/approved community threat intelligence."""
    return await service.get_public_reports(
        domain=domain,
        category=category,
        status=status,
        search=search,
        sort_by=sort_by,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/my-reports",
    response_model=PaginatedCommunityReports[CommunityReportUserResponse],
    summary="List Submitting User's Threat Reports",
    description="Retrieve all threat reports submitted by the current authenticated user.",
)
async def list_my_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> PaginatedCommunityReports[CommunityReportUserResponse]:
    """Retrieve personal submission history and moderation statuses."""
    return await service.get_user_reports(
        current_user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/reports/{report_id}",
    response_model=Any,
    summary="Get Threat Report Details",
    description=(
        "Fetch detailed information for a specific threat report. "
        "Public users can only view approved reports (sanitized). "
        "Submitting users and admins can view pending or rejected reports."
    ),
)
async def get_report_detail(
    report_id: uuid.UUID,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> Any:
    """Retrieve detailed report metadata with privacy boundary enforcement."""
    return await service.get_report_detail(
        report_id=report_id,
        current_user=current_user,
    )


@router.post(
    "/reports/{report_id}/confirm",
    response_model=CommunityConfirmationToggleResponse,
    summary="Toggle Community Confirmation",
    description="Confirm suspicious activity or withdraw previous confirmation on a community threat report.",
)
async def toggle_confirmation(
    report_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> CommunityConfirmationToggleResponse:
    """One confirmation per authenticated user per report."""
    return await service.toggle_confirmation(
        report_id=report_id,
        current_user=current_user,
    )


@router.post(
    "/reports/{report_id}/flag",
    response_model=CommunityReportFlagResponse,
    summary="Flag Threat Report",
    description="Flag an inaccurate, abusive, duplicate, or outdated community threat report.",
)
async def flag_report(
    report_id: uuid.UUID,
    flag_in: CommunityReportFlagCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> CommunityReportFlagResponse:
    """Flag a community report for administrative moderation review."""
    return await service.flag_report(
        report_id=report_id,
        current_user=current_user,
        flag_in=flag_in,
    )


@router.get(
    "/reports/{report_id}/integrity-proof",
    response_model=Web3IntegrityProofResponse,
    summary="Cryptographic Web3 Integrity Proof",
    description="Retrieve canonical cryptographic SHA-256 hash and verifiable on-chain proof metadata.",
)
async def get_integrity_proof(
    report_id: uuid.UUID,
    service: CommunityReportingService = Depends(get_community_service),
) -> Web3IntegrityProofResponse:
    """Verify cryptographic audit trail of the report record."""
    return await service.get_integrity_proof(report_id=report_id)


@router.post(
    "/reports/{report_id}/upvote",
    summary="Legacy Upvote Threat Report",
    description="Legacy support endpoint: upvotes an approved threat report.",
)
async def upvote_report(
    report_id: uuid.UUID,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: CommunityReportingService = Depends(get_community_service),
) -> Any:
    """Upvote an approved community report."""
    return await service.upvote_report(
        report_id=report_id,
        current_user=current_user,
    )
