"""
Domain Reputation API Endpoints for TrustGuard AI.

Provides access to domain intelligence, verified organizational identities,
brand lookalike checks, safe DNS records, and historical scan stability.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.schemas.domain_reputation import DomainReputationResult
from app.services.domain_reputation_service import DomainReputationService

logger = logging.getLogger("trustguard.api.domain_reputation")
router = APIRouter()


def get_reputation_service() -> DomainReputationService:
    return DomainReputationService()


@router.get(
    "/{domain:path}",
    response_model=DomainReputationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Domain Reputation",
    description=(
        "Analyzes domain reputation, checks verified authoritative identities, "
        "detects brand lookalikes/homoglyphs, executes safe DNS resolution with SSRF guards, "
        "and retrieves historical scan stability."
    ),
)
async def evaluate_domain_reputation(
    domain: str = Path(..., description="Target domain name or hostname (e.g., google.com, example.xyz)"),
    reputation_service: DomainReputationService = Depends(get_reputation_service),
) -> DomainReputationResult:
    logger.info("Domain reputation evaluation requested for domain='%s'", domain)
    return await reputation_service.evaluate_domain(domain)
