"""
Health check and system status response schemas.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health check responses."""

    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application version")
    status: str = Field(
        default="healthy", description="Current health status (e.g. healthy, degraded)"
    )
    environment: str = Field(
        ..., description="Application environment (development, staging, production)"
    )
    database: Optional[str] = Field(default="configured", description="Database connection status")
