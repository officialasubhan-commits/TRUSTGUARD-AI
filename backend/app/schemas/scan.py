"""
Pydantic schemas for Scan submissions, status tracking, and detailed results.
Enforces strict validation on URLs, risk levels, and trust scores.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RiskCategory = Literal["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
ScanStatusType = Literal["pending", "processing", "complete", "error"]


class ScanCreate(BaseModel):
    """Client request schema for submitting a URL to scan."""

    url: str = Field(
        ...,
        min_length=4,
        max_length=2048,
        description="Target URL to analyze (must begin with http:// or https://)",
    )
    guest: bool = Field(
        default=False,
        description="True if initiated without authentication",
    )

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        url_str = v.strip()
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", url_str, re.IGNORECASE):
            raise ValueError("URL must be a valid HTTP or HTTPS address.")
        return url_str


class ScanStatusUpdate(BaseModel):
    """Internal model for updating scan lifecycle status."""

    scan_status: ScanStatusType
    risk_level: Optional[RiskCategory] = None
    trust_score: Optional[int] = Field(None, ge=0, le=100)
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    assessment_status: Optional[str] = None
    assessment_coverage: Optional[float] = Field(None, ge=0.0, le=1.0)
    scoring_version: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class ScanResultCreate(BaseModel):
    """
    Internal model used exclusively by the backend scoring engine
    to persist validated analysis results. Clients cannot submit this.
    """

    scan_id: uuid.UUID
    trust_score: int = Field(
        ..., ge=0, le=100, description="Calculated Digital Trust Score (0-100)"
    )
    overall_risk_level: RiskCategory

    # Machine Learning
    phishing_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    ml_prediction: Optional[str] = Field(None, max_length=32)
    ml_score: Optional[int] = Field(None, ge=0, le=100)
    ml_features: Optional[Dict[str, Any]] = None

    # Threat Intelligence
    virustotal_detection_count: Optional[int] = Field(None, ge=0)
    virustotal_total_engines: Optional[int] = Field(None, ge=0)
    threat_intelligence_status: Optional[str] = Field(None, max_length=32)
    vt_score: Optional[int] = Field(None, ge=0, le=100)
    vt_raw: Optional[Dict[str, Any]] = None

    # SSL/TLS
    ssl_status: Optional[str] = Field(None, max_length=64)
    ssl_valid: Optional[bool] = None
    ssl_issuer: Optional[str] = Field(None, max_length=255)
    ssl_expiry_date: Optional[datetime] = None
    ssl_days_remaining: Optional[int] = None
    ssl_score: Optional[int] = Field(None, ge=0, le=100)
    ssl_raw: Optional[Dict[str, Any]] = None

    # URL Heuristics & Breakdown
    url_score: Optional[int] = Field(None, ge=0, le=100)
    url_risk_indicators: Optional[List[Dict[str, Any]]] = None
    score_breakdown: Dict[str, Any] = Field(..., description="Weighting breakdown & explanations")
    analysis_summary: Optional[str] = None


class ScanResultResponse(BaseModel):
    """Client-facing schema for completed detailed scan results."""

    id: uuid.UUID
    scan_id: uuid.UUID
    trust_score: int
    overall_risk_level: RiskCategory

    phishing_probability: Optional[float] = None
    ml_prediction: Optional[str] = None
    ml_score: Optional[int] = None
    ml_features: Optional[Dict[str, Any]] = None

    virustotal_detection_count: Optional[int] = None
    virustotal_total_engines: Optional[int] = None
    threat_intelligence_status: Optional[str] = None
    vt_score: Optional[int] = None
    vt_raw: Optional[Dict[str, Any]] = None

    ssl_status: Optional[str] = None
    ssl_valid: Optional[bool] = None
    ssl_issuer: Optional[str] = None
    ssl_expiry_date: Optional[datetime] = None
    ssl_days_remaining: Optional[int] = None
    ssl_score: Optional[int] = None
    ssl_raw: Optional[Dict[str, Any]] = None

    url_score: Optional[int] = None
    url_risk_indicators: Optional[List[Dict[str, Any]]] = None
    score_breakdown: Dict[str, Any]
    analysis_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanHistoryResponse(BaseModel):
    """Schema for scan summary in user history lists."""

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    submitted_url: str
    normalized_url: str
    domain: Optional[str] = None
    scan_status: ScanStatusType
    risk_level: Optional[RiskCategory] = None
    trust_score: Optional[int] = None
    risk_score: Optional[int] = None
    assessment_status: Optional[str] = None
    assessment_coverage: Optional[float] = None
    scoring_version: Optional[str] = None
    is_guest: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScanDetailResponse(BaseModel):
    """Composite schema containing both scan history status and full result details."""

    scan: ScanHistoryResponse
    result: Optional[ScanResultResponse] = None
