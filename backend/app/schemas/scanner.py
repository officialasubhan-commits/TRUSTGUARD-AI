"""
Pydantic schemas for the URL Scanner API submission and preliminary security analysis.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ml import MLPredictionResponse
from app.schemas.risk_scoring import DigitalTrustAssessment
from app.schemas.ssl import SSLValidationResponse

PreliminaryRiskLevel = Literal[
    "LOW_CONCERN", "MODERATE_CONCERN", "HIGH_CONCERN", "INSUFFICIENT_INFORMATION"
]


class PreliminaryIndicator(BaseModel):
    """Structured security indicator identified during static URL analysis."""

    name: str = Field(..., description="Unique machine-readable indicator name")
    description: str = Field(..., description="Summary of the security observation")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Indicator severity level"
    )
    evidence: str = Field(
        ..., description="Extracted URL substring or value that triggered the flag"
    )
    reason: str = Field(
        ..., description="Cybersecurity explanation for why this pattern is flagged"
    )


class PreliminaryAnalysis(BaseModel):
    """Preliminary risk evaluation produced prior to heavy ML and external intelligence."""

    risk_level: PreliminaryRiskLevel = Field(
        ...,
        description="Preliminary heuristic assessment (LOW_CONCERN, MODERATE_CONCERN, HIGH_CONCERN)",
    )
    indicators: List[PreliminaryIndicator] = Field(
        default_factory=list,
        description="List of triggered security flags",
    )
    features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of extracted lexical and structural features",
    )


class URLSubmissionResponse(BaseModel):
    """Response returned upon successful URL submission to POST /api/v1/scan."""

    success: bool = Field(
        default=True, description="Indicates whether the URL was successfully accepted"
    )
    scan_id: uuid.UUID = Field(..., description="Unique identifier for the scan operation")
    original_url: str = Field(..., description="The raw URL submitted by the client")
    normalized_url: str = Field(..., description="RFC 3986 canonical normalized representation")
    validation_status: Literal["VALID", "SUSPICIOUS", "INVALID"] = Field(
        default="VALID",
        description="Syntactic and security validation outcome",
    )
    is_guest: bool = Field(default=False, description="Whether the scan was executed in guest mode")
    preliminary_analysis: PreliminaryAnalysis = Field(
        ...,
        description="Initial static heuristic evaluation",
    )
    ml_prediction: Optional[MLPredictionResponse] = Field(
        default=None,
        description="Machine learning phishing probability and risk prediction",
    )
    ssl_analysis: Optional[SSLValidationResponse] = Field(
        default=None,
        description="SSL/TLS certificate verification, validity, and protocol findings",
    )
    trust_assessment: Optional[DigitalTrustAssessment] = Field(
        default=None,
        description="Synthesized Digital Trust Score, evidence-based risk breakdown, and explainable findings",
    )
    digital_trust_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Convenience top-level access to the final Digital Trust Score (0-100)",
    )
    risk_level: Optional[str] = Field(
        default=None,
        description="Convenience top-level access to overall risk level (LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN)",
    )
    message: str = Field(
        default="URL accepted for multi-layer security analysis.",
        description="Human-readable processing status message",
    )
    submitted_at: datetime = Field(..., description="Timestamp when the scan was registered")

    model_config = ConfigDict(from_attributes=True)
