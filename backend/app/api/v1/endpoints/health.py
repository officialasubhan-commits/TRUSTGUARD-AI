"""
Health check endpoints for system status and monitoring.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.database.connection import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API v1 Health Check",
    description="Returns current status of API v1, environment, version, and database readiness.",
)
async def get_v1_health() -> HealthResponse:
    return HealthResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        status="healthy",
        environment=settings.APP_ENV,
        database=check_db_health(),
    )
