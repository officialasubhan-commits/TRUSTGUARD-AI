"""
Public Maintenance Status Endpoint for TrustGuard AI.
Allows the frontend to check whether platform maintenance mode is active.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.database.repositories.admin_repo import get_admin_repository

logger = logging.getLogger("trustguard.api.maintenance")
router = APIRouter()


class PublicMaintenanceStatus(BaseModel):
    maintenance_enabled: bool
    maintenance_message: Optional[str] = None
    estimated_restore_time: Optional[str] = None


@router.get(
    "/status",
    response_model=PublicMaintenanceStatus,
    summary="Check Public Maintenance Status",
    description="Returns whether the platform is currently undergoing scheduled maintenance.",
)
async def check_maintenance_status() -> PublicMaintenanceStatus:
    repo = get_admin_repository()
    cfg = await repo.get_maintenance_config()
    return PublicMaintenanceStatus(
        maintenance_enabled=cfg.maintenance_enabled,
        maintenance_message=cfg.maintenance_message if cfg.maintenance_enabled else None,
        estimated_restore_time=cfg.estimated_restore_time if cfg.maintenance_enabled else None,
    )

