"""
Scanner API Endpoints for TrustGuard AI.
Handles URL submission, validation, preliminary security analysis, and status retrieval.
Supports authenticated and guest users securely.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, status

from app.core.security import AuthenticatedUser, get_optional_user
from app.schemas.scan import ScanCreate, ScanDetailResponse
from app.schemas.scanner import URLSubmissionResponse
from app.services.scan_service import ScanService

logger = logging.getLogger("trustguard.api.scanner")
router = APIRouter()


def get_scan_service() -> ScanService:
    """Dependency provider for ScanService."""
    return ScanService()


@router.get(
    "/status",
    summary="Scanner Engine Status",
    description="Check status of the multi-layer URL analysis engine.",
)
async def scanner_status():
    return {
        "message": "Scanner engine online. URL validation, normalisation, and static feature extraction active.",
        "status": "ready",
    }


@router.post(
    "",
    response_model=URLSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit URL for Threat Analysis",
    description=(
        "Accepts a URL from authenticated or guest users, performs static validation, "
        "normalises the URL, extracts lexical/structural features, identifies preliminary "
        "risk indicators, and registers the scan operation."
    ),
)
async def submit_scan(
    scan_in: ScanCreate,
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    scan_service: ScanService = Depends(get_scan_service),
) -> URLSubmissionResponse:
    # Determine user identity securely from verified JWT (prevents client spoofing)
    if current_user is not None:
        user_id = current_user.user_id
        is_guest = False
    else:
        user_id = None
        is_guest = True

    client_ip = request.client.host if request.client else None

    logger.info(
        "URL scan submission received: url='%s' user_id=%s is_guest=%s",
        scan_in.url,
        user_id,
        is_guest,
    )

    return await scan_service.submit_url(
        raw_url=scan_in.url,
        user_id=user_id,
        is_guest=is_guest,
        client_ip=client_ip,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Scan Details by ID",
    description="Retrieves scan lifecycle status and analysis results with strict ownership enforcement.",
)
async def get_scan_by_id(
    scan_id: uuid.UUID,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    scan_service: ScanService = Depends(get_scan_service),
) -> ScanDetailResponse:
    requesting_user_id = current_user.user_id if current_user else None

    scan_history, scan_result = await scan_service.get_scan_details(
        scan_id=scan_id,
        requesting_user_id=requesting_user_id,
    )

    return ScanDetailResponse(
        scan=scan_history,
        result=scan_result,
    )
