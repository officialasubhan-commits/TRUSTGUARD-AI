"""
History endpoint module stub.
Retrieval of past scans for authenticated users will be implemented in future prompts.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HistoryStatus(BaseModel):
    message: str
    status: str


@router.get(
    "/status",
    response_model=HistoryStatus,
    summary="History Service Status",
    description="Check status of scan history retrieval service.",
)
async def history_status() -> HistoryStatus:
    return HistoryStatus(
        message="Scan history and security report management service active.",
        status="ready",
    )
