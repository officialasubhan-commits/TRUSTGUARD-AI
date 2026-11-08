"""
Pydantic schemas for VirusTotal Threat Intelligence and URL Reputation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

VTStatusType = Literal[
    "MALICIOUS",
    "SUSPICIOUS",
    "NO_DETECTIONS",
    "NOT_FOUND",
    "PENDING",
    "API_UNAVAILABLE",
    "RATE_LIMITED",
    "ERROR",
]


class VirusTotalVendorStats(BaseModel):
    """Aggregate detection counts from security engines."""

    malicious: int = Field(default=0, ge=0, description="Engines classifying URL as malicious")
    suspicious: int = Field(default=0, ge=0, description="Engines classifying URL as suspicious")
    harmless: int = Field(default=0, ge=0, description="Engines classifying URL as harmless")
    undetected: int = Field(default=0, ge=0, description="Engines with no detection recorded")
    timeout: int = Field(default=0, ge=0, description="Engines that timed out")
    total_engines: int = Field(
        default=0, ge=0, description="Total engines participating in analysis"
    )


class VirusTotalThreatClassification(BaseModel):
    """Interpreted threat assessment derived from engine telemetry."""

    status: VTStatusType = Field(..., description="High-level threat status")
    detection_ratio: str = Field(
        default="0/0", description="Ratio of malicious to total engines (e.g. 8/72)"
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"] = Field(
        default="LOW",
        description="Confidence level based on engine coverage and consensus",
    )
    threat_categories: List[str] = Field(
        default_factory=list,
        description="Identified threat labels (e.g. phishing, malware)",
    )
    flagged_vendors: List[str] = Field(
        default_factory=list,
        description="Names of notable security engines flagging the target",
    )
    summary: str = Field(..., description="Human-readable assessment narrative")
    safety_disclaimer: str = Field(
        default="Notice: Absence of detections (NO_DETECTIONS) does not guarantee that a website is safe.",
        description="Security advisory regarding threat intelligence coverage limits",
    )


class VirusTotalReportResponse(BaseModel):
    """Complete VirusTotal Threat Intelligence report response."""

    source: str = Field(default="VirusTotal v3", description="Threat intelligence feed name")
    status: VTStatusType = Field(..., description="Analysis outcome status")
    url: str = Field(..., description="Target URL analyzed")
    url_identifier: str = Field(
        ..., description="Base64url or SHA256 resource identifier used in VirusTotal API"
    )
    vt_subscore: int = Field(
        default=100, ge=0, le=100, description="Normalised subscore (0-100; 100=clean)"
    )
    statistics: VirusTotalVendorStats = Field(default_factory=VirusTotalVendorStats)
    classification: VirusTotalThreatClassification
    last_analysis_date: Optional[datetime] = Field(
        None, description="Timestamp of the analysis on VirusTotal"
    )
    scan_id: Optional[uuid.UUID] = Field(None, description="Associated TrustGuard scan ID")
    cached: bool = Field(default=False, description="True if served from local cache")
    message: str = Field(default="", description="Operational status message")

    model_config = ConfigDict(from_attributes=True)
