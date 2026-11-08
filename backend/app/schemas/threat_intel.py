"""
Pydantic schemas for Threat Intelligence Records.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SeverityType = Literal["critical", "high", "medium", "low", "info"]
ThreatSourceType = Literal["virustotal", "urlhaus", "internal_ml", "community"]


class ThreatIntelCreate(BaseModel):
    """Schema for recording threat intelligence findings (internal use)."""

    scan_id: Optional[uuid.UUID] = None
    normalized_url: Optional[str] = Field(None, max_length=2048)
    domain: Optional[str] = Field(None, max_length=255)
    threat_source: ThreatSourceType
    threat_category: Optional[str] = Field(None, max_length=64)
    severity: SeverityType = "medium"
    verification_status: str = "verified"
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None


class ThreatIntelResponse(BaseModel):
    id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    normalized_url: Optional[str] = None
    domain: Optional[str] = None
    threat_source: str
    threat_category: Optional[str] = None
    severity: str
    verification_status: str
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
