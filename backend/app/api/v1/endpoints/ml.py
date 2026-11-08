"""
Machine Learning API Endpoints for TrustGuard AI.

Provides direct access to URL feature extraction, ML phishing inference,
explainable indicator breakdowns, and active model telemetry.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.schemas.ml import MLPredictionResponse
from app.services.ml_detection_service import MLDetectionService, get_ml_service
from app.services.ml_feature_adapter import FEATURE_NAMES_V2, FEATURE_SCHEMA_VERSION
from app.services.url_analyzer import URLAnalyzer
from app.utils.url_normalizer import normalize_url

logger = logging.getLogger("trustguard.api.ml")
router = APIRouter()


class FeatureExtractionRequest(BaseModel):
    url: str = Field(..., description="Target URL for feature extraction")


class FeatureExtractionResponse(BaseModel):
    url: str
    normalized_url: str
    feature_schema_version: str
    feature_count: int
    features: Dict[str, Any]
    feature_names: List[str]
    feature_vector: List[float]


class PredictRequest(BaseModel):
    url: str = Field(..., description="Target URL for machine learning threat prediction")


def get_analyzer() -> URLAnalyzer:
    return URLAnalyzer()


@router.post(
    "/predict",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict URL Phishing Risk",
    description="Extracts lexical/structural features and classifies URL phishing probability using the champion ML model.",
)
async def predict_url(
    payload: PredictRequest,
    analyzer: URLAnalyzer = Depends(get_analyzer),
    ml_service: MLDetectionService = Depends(get_ml_service),
) -> MLPredictionResponse:
    try:
        norm = normalize_url(payload.url)
    except Exception:
        norm = payload.url

    analysis = analyzer.analyze(raw_url=payload.url, normalized_url=norm)
    return ml_service.predict(features_dict=analysis["features"], raw_url=payload.url)


@router.post(
    "/features",
    response_model=FeatureExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Numerical Feature Vector",
    description="Extracts the full 30-feature vector (Schema v2) for a given URL without running inference.",
)
async def extract_features(
    payload: FeatureExtractionRequest,
    analyzer: URLAnalyzer = Depends(get_analyzer),
) -> FeatureExtractionResponse:
    try:
        norm = normalize_url(payload.url)
    except Exception:
        norm = payload.url

    analysis = analyzer.analyze(raw_url=payload.url, normalized_url=norm)
    from app.services.ml_feature_adapter import extract_feature_vector
    vector = extract_feature_vector(analysis["features"], target_feature_count=len(FEATURE_NAMES_V2))

    return FeatureExtractionResponse(
        url=payload.url,
        normalized_url=norm,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        feature_count=len(FEATURE_NAMES_V2),
        features=analysis["features"],
        feature_names=FEATURE_NAMES_V2,
        feature_vector=vector,
    )


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
    summary="Get Active ML Model Information & Metrics",
    description="Returns metadata, evaluation metrics, and candidate comparison for the deployed model.",
)
async def get_model_telemetry(
    ml_service: MLDetectionService = Depends(get_ml_service),
) -> Dict[str, Any]:
    return {
        "status": ml_service.status,
        "is_available": ml_service.is_available,
        "model_version": ml_service.model_version,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_count": len(FEATURE_NAMES_V2),
        "metadata": ml_service._metadata,
        "metrics": ml_service._metrics,
    }

