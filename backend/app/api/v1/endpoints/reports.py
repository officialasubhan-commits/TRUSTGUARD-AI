"""
Community reports endpoint module stub.
Community threat reporting and feedback will be implemented in future prompts.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ReportsStatus(BaseModel):
    message: str
    status: str


@router.get(
    "/status",
    response_model=ReportsStatus,
    summary="Reports Service Status",
    description="Check status of community reporting and threat submission service.",
)
async def reports_status() -> ReportsStatus:
    return ReportsStatus(
        message="Community reports router initialized.",
        status="ready",
    )
