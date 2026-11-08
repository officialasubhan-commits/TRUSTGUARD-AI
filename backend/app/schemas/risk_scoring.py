"""
Pydantic schemas for Digital Trust Score & Intelligent Risk Assessment Engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

RiskLevelType = Literal["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
AssessmentStatusType = Literal["COMPLETE", "PARTIAL", "INSUFFICIENT_DATA", "ASSESSMENT_INCOMPLETE"]
ModuleSourceType = Literal["url_heuristics", "virustotal", "ml_phishing", "ssl_tls"]
FindingSeverityType = Literal["info", "low", "medium", "high", "critical"]


class FindingItem(BaseModel):
    """Explainable security indicator item (risk, positive, or unknown)."""

    title: str = Field(..., description="Short headline of the finding")
    description: str = Field(..., description="Detailed description of the observation")
    source_module: ModuleSourceType = Field(
        ..., description="Detection module that produced the finding"
    )
    severity: FindingSeverityType = Field(
        default="info", description="Severity category of the finding"
    )
    evidence: Optional[str] = Field(None, description="Concrete technical evidence or metric")
    affects_score: bool = Field(
        default=True, description="Whether this finding influenced score calculations"
    )
    explanation: str = Field(
        ..., description="Non-technical rationale explaining why this matters to the user"
    )


class ModuleScoreDetail(BaseModel):
    """Breakdown of an individual detection module's risk contribution."""

    module_name: str = Field(..., description="Name of the security module")
    status: str = Field(..., description="Availability status (e.g. AVAILABLE, UNAVAILABLE, ERROR)")
    weight: float = Field(..., description="Configured fractional weight (e.g. 0.40)")
    raw_subscore: Optional[int] = Field(
        None, ge=0, le=100, description="Raw 0-100 module trust subscore"
    )
    normalized_risk: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Derived 0-100 risk score"
    )
    included_in_calculation: bool = Field(
        default=True, description="Whether this module contributed to the final score"
    )
    reason_if_excluded: Optional[str] = Field(
        None, description="Reason if module was excluded from calculation"
    )


class DigitalTrustAssessment(BaseModel):
    """Unified evidence-based Digital Trust Score and risk assessment report."""

    digital_trust_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Calculated Digital Trust Score (0-100; 100=highest trust, 0=critical threat)",
    )
    risk_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Internal aggregated risk score (0-100; 100=maximum risk)",
    )
    risk_level: RiskLevelType = Field(
        ...,
        description="Database-compatible risk level category (SAFE, LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN)",
    )
    risk_label: str = Field(
        ...,
        description="Human-friendly risk category label (e.g. 'LOW RISK', 'CRITICAL RISK', 'INSUFFICIENT DATA')",
    )
    assessment_status: AssessmentStatusType = Field(
        ...,
        description="Completeness status of the overall multi-module assessment",
    )
    assessment_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fractional assessment coverage based on successfully evaluated module weights (0.0 to 1.0)",
    )
    coverage_percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="Coverage formatted as integer percentage (0-100%)",
    )
    scoring_version: str = Field(
        ...,
        description="Version identifier of the risk scoring methodology algorithm",
    )
    high_severity_override: bool = Field(
        default=False,
        description="True if a high-severity finding triggered an override capping the trust score",
    )
    override_reason: Optional[str] = Field(
        None,
        description="Explanation if a critical security override was applied",
    )
    module_scores: Dict[str, ModuleScoreDetail] = Field(
        default_factory=dict,
        description="Detailed telemetry and weighting breakdown for each detection component",
    )
    risk_indicators: List[FindingItem] = Field(
        default_factory=list,
        description="Negative security findings that raised the overall risk score",
    )
    positive_indicators: List[FindingItem] = Field(
        default_factory=list,
        description="Affirmative security characteristics detected during inspection",
    )
    unknown_indicators: List[FindingItem] = Field(
        default_factory=list,
        description="Services, feeds, or checks that were unavailable, rate-limited, or inconclusive",
    )
    summary: str = Field(
        ...,
        description="Comprehensive executive summary of the website trust evaluation",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable, evidence-based security guidance tailored to the scan findings",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this trust evaluation was calculated",
    )

    model_config = ConfigDict(from_attributes=True)
