"""
Threat Intelligence API Endpoints for TrustGuard AI.

Provides access to external reputation feeds, multi-vendor security telemetry,
and VirusTotal analysis reports for scanned URLs.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, get_optional_user
from app.database.repositories.scan_repo import ScanRepository
from app.schemas.virustotal import VirusTotalReportResponse
from app.services.virustotal_service import VirusTotalService

logger = logging.getLogger("trustguard.api.threat_intel")
router = APIRouter()


def get_vt_service() -> VirusTotalService:
    """Dependency provider for VirusTotalService."""
    return VirusTotalService()


def get_scan_repo() -> ScanRepository:
    """Dependency provider for ScanRepository."""
    return ScanRepository()


@router.get(
    "/lookup",
    response_model=VirusTotalReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct Threat Intelligence Lookup by URL",
    description="Queries VirusTotal reputation for a raw or normalized URL directly.",
)
async def lookup_threat_intelligence_by_url(
    url: str = Query(..., description="Target URL to query in VirusTotal threat feed"),
    vt_service: VirusTotalService = Depends(get_vt_service),
) -> VirusTotalReportResponse:
    logger.info("Direct threat intelligence lookup requested for url='%s'", url)
    return await vt_service.lookup_url(url=url)


@router.get(
    "/{scan_id}",
    response_model=VirusTotalReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get VirusTotal Threat Intelligence by Scan ID",
    description=(
        "Retrieves the multi-engine VirusTotal reputation and threat intelligence "
        "report for a previously submitted scan, with ownership authorization."
    ),
)
async def get_threat_intelligence_by_scan_id(
    scan_id: uuid.UUID,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    vt_service: VirusTotalService = Depends(get_vt_service),
    scan_repo: ScanRepository = Depends(get_scan_repo),
) -> VirusTotalReportResponse:
    requesting_user_id = current_user.user_id if current_user else None

    # Enforce ownership rules on the associated scan
    scan_history, _ = await scan_repo.get_scan_by_id_with_ownership(
        scan_id=scan_id,
        requesting_user_id=requesting_user_id,
    )

    logger.info(
        "Threat intelligence requested for scan_id=%s, url='%s'",
        scan_id,
        scan_history.normalized_url,
    )

    return await vt_service.lookup_url(
        url=scan_history.normalized_url,
        scan_id=scan_id,
    )
