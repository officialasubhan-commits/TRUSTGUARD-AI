"""
Public CMS and Content Delivery Endpoints for TrustGuard AI.
Exposes public contributors, CMS dynamic pages, and public site configuration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.repositories.admin_repo import AdminRepository, get_admin_repository
from app.schemas.admin import (
    ContributorItem,
    ContributorsPageConfig,
    SystemSettingsConfig,
    WebsitePageItem,
)

logger = logging.getLogger("trustguard.api.public_cms")
router = APIRouter()


@router.get(
    "/contributors",
    response_model=List[ContributorItem],
    summary="Get Public Active Contributors",
    description="Returns public list of active contributors ordered by display priority.",
)
async def get_public_contributors(
    repo: AdminRepository = Depends(get_admin_repository),
) -> List[ContributorItem]:
    return await repo.get_contributors(include_inactive=False)


@router.get(
    "/contributors/page-config",
    response_model=ContributorsPageConfig,
    summary="Get Contributors Page Header & Visibility Settings",
)
async def get_public_contributors_page_config(
    repo: AdminRepository = Depends(get_admin_repository),
) -> ContributorsPageConfig:
    return await repo.get_contributors_page_config()


@router.get(
    "/pages/{slug}",
    response_model=WebsitePageItem,
    summary="Get Public Dynamic CMS Page by Slug",
)
async def get_public_page_by_slug(
    slug: str,
    repo: AdminRepository = Depends(get_admin_repository),
) -> WebsitePageItem:
    page = await repo.get_page_by_slug(slug)
    if not page or not page.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page '{slug}' is unavailable or not found.",
        )
    return page


@router.get(
    "/settings/public",
    response_model=SystemSettingsConfig,
    summary="Get Public System Configuration, Announcement & Branding",
)
async def get_public_settings(
    repo: AdminRepository = Depends(get_admin_repository),
) -> SystemSettingsConfig:
    return await repo.get_system_settings()
