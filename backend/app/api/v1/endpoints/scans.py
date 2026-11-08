"""
Scan History, Detailed Reporting, and Report Management API Endpoints.
Provides server-side paginated history, multi-factor filtering, statistics aggregation,
exportable security reports, and secure record deletion.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.security import AuthenticatedUser, get_current_user, get_optional_user
from app.schemas.history import (
    DailyScanActivity,
    DetailedSecurityReportResponse,
    ExportableSecurityReport,
    PaginatedScanHistoryResponse,
    ScanDeleteResponse,
    ScanStatisticsResponse,
)
from app.services.scan_history_service import ScanHistoryService, get_scan_history_service

logger = logging.getLogger("trustguard.api.scans")
router = APIRouter()


@router.get(
    "",
    response_model=PaginatedScanHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User Scan History",
    description=(
        "Retrieves a server-side paginated list of previous scans for the authenticated user. "
        "Supports domain/URL search, risk classification filtering, date range constraints, "
        "and multi-attribute sorting."
    ),
)
async def get_user_scan_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(
        default=None, max_length=255, description="Search term for domain or URL"
    ),
    risk_level: Optional[str] = Query(
        default=None,
        description="Filter by risk category: LOW_RISK, MODERATE_RISK, HIGH_RISK, CRITICAL_RISK, INSUFFICIENT_DATA",
    ),
    assessment_status: Optional[str] = Query(
        default=None,
        description="Filter by assessment completeness: COMPLETE, PARTIAL, INSUFFICIENT_DATA",
    ),
    date_filter: Optional[str] = Query(
        default=None,
        description="Convenience date filter: 'today', 'last_7_days', 'last_30_days'",
    ),
    start_date: Optional[datetime] = Query(
        default=None, description="ISO-8601 custom start boundary"
    ),
    end_date: Optional[datetime] = Query(default=None, description="ISO-8601 custom end boundary"),
    sort_by: str = Query(
        default="newest",
        description="Sort attribute: 'newest', 'oldest', 'highest_score', 'lowest_score', 'created_at', 'trust_score'",
    ),
    sort_order: str = Query(default="desc", description="Sort direction: 'asc' or 'desc'"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> PaginatedScanHistoryResponse:
    return await history_service.get_user_history(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        search=search,
        risk_level=risk_level,
        assessment_status=assessment_status,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/statistics",
    response_model=ScanStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Scanning Statistics",
    description=(
        "Returns aggregated scan metrics for the authenticated user, including total scans, "
        "risk distribution counts, incomplete assessments, and average Digital Trust Score."
    ),
)
async def get_user_statistics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> ScanStatisticsResponse:
    return await history_service.get_user_statistics(user_id=current_user.user_id)


@router.get(
    "/activity",
    response_model=List[DailyScanActivity],
    status_code=status.HTTP_200_OK,
    summary="Get User Scanning Activity Timeline",
    description=(
        "Returns daily scan counts and threat distributions across the specified historical window (7, 30, or 90 days)."
    ),
)
async def get_user_activity_timeline(
    days: int = Query(default=30, ge=1, le=90, description="Historical lookback window in days"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> List[DailyScanActivity]:
    return await history_service.get_activity_timeline(user_id=current_user.user_id, days=days)


@router.get(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    summary="Export Complete User Scan History as CSV",
    description=(
        "Streams all historical scans for the authenticated user as an RFC-4180 CSV file. "
        "Includes formula injection protection, UTC timestamps, and comprehensive risk/TLS metrics."
    ),
)
async def export_user_history_csv(
    current_user: AuthenticatedUser = Depends(get_current_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> Response:
    csv_content, filename = await history_service.export_user_scan_history_csv(
        user_id=current_user.user_id
    )
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get(
    "/{scan_id}",
    response_model=DetailedSecurityReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Security Report by Scan ID",
    description=(
        "Retrieves the comprehensive, evidence-based security report for a specific scan. "
        "Enforces strict ownership: inaccessible private scans return 404 to avoid leaking existence."
    ),
)
async def get_scan_report(
    scan_id: uuid.UUID,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> DetailedSecurityReportResponse:
    requesting_user_id = current_user.user_id if current_user else None
    return await history_service.get_detailed_report(
        scan_id=scan_id,
        requesting_user_id=requesting_user_id,
    )


@router.get(
    "/{scan_id}/export",
    response_model=ExportableSecurityReport,
    status_code=status.HTTP_200_OK,
    summary="Export Sanitized Security Report",
    description=(
        "Returns a sanitized, portable JSON security report suitable for sharing or export, "
        "without exposing internal database IDs or credentials."
    ),
)
async def export_scan_report(
    scan_id: uuid.UUID,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> ExportableSecurityReport:
    requesting_user_id = current_user.user_id if current_user else None
    return await history_service.export_security_report(
        scan_id=scan_id,
        requesting_user_id=requesting_user_id,
    )


@router.delete(
    "/{scan_id}",
    response_model=ScanDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Scan Record",
    description=(
        "Permanently deletes a scan record and all associated results. "
        "Only the authenticated owner of the scan is authorized to perform this operation."
    ),
)
async def delete_scan(
    scan_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    history_service: ScanHistoryService = Depends(get_scan_history_service),
) -> ScanDeleteResponse:
    return await history_service.delete_scan(
        scan_id=scan_id,
        requesting_user_id=current_user.user_id,
    )
