"""
Pydantic schemas for Machine Learning Phishing Detection.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MLPredictionLabel = Literal["PHISHING", "SUSPICIOUS", "LIKELY_LEGITIMATE", "UNKNOWN", "MODEL_UNAVAILABLE"]
MLModelStatus = Literal["ACTIVE", "MODEL_UNAVAILABLE", "ERROR"]
MLConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]


class MLPredictionResponse(BaseModel):
    """Structured response for ML-based phishing detection."""

    prediction: MLPredictionLabel = Field(
        ...,
        description="Categorical ML assessment: PHISHING, SUSPICIOUS, LIKELY_LEGITIMATE, UNKNOWN, or MODEL_UNAVAILABLE",
    )
    phishing_probability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Model estimated probability that the URL is a phishing site (0.0 to 1.0)",
    )
    ml_subscore: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Normalized trust subscore derived from ML probability (0 = critical risk, 100 = clean). None when unavailable.",
    )
    confidence: MLConfidenceLevel = Field(
        default="LOW",
        description="Assessment confidence rating based on probability separation and feature clarity",
    )
    model_version: str = Field(
        default="unavailable",
        description="Identifier of the loaded ML model artifact",
    )
    model_status: MLModelStatus = Field(
        default="MODEL_UNAVAILABLE",
        description="Operational health status of the ML inference subsystem",
    )
    indicators: List[str] = Field(
        default_factory=list,
        description="Explainable, human-readable indicators that contributed to the model evaluation",
    )
    top_feature_importance: Optional[Dict[str, float]] = Field(
        default=None,
        description="Global feature importance weights from the trained Random Forest model",
    )
    summary: str = Field(
        ...,
        description="Non-technical explanation of the machine learning evaluation",
    )
    disclaimer: str = Field(
        default=(
            "Advisory Notice: Machine learning phishing probability is a predictive indicator "
            "based on structural URL patterns and does not guarantee that a website is benign or malicious."
        ),
        description="Security disclaimer regarding machine learning predictive limits",
    )

    model_config = ConfigDict(from_attributes=True)
