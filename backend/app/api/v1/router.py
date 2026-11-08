"""
Central API v1 router consolidating all endpoint modules.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    authentication,
    community,
    domain_reputation,
    health,
    history,
    maintenance,
    ml,
    reports,
    scanner,
    scans,
    threat_intel,
    users,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(authentication.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(scanner.router, prefix="/scan", tags=["Scanner"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scan History & Reports"])
api_router.include_router(
    threat_intel.router, prefix="/threat-intelligence", tags=["Threat Intelligence"]
)
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
api_router.include_router(
    domain_reputation.router, prefix="/domain-reputation", tags=["Domain Reputation"]
)
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(community.router, prefix="/community", tags=["Community Threat Reports"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Moderation"])
