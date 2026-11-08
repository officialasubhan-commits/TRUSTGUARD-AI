"""
Machine Learning Phishing Detection Inference Service.

Loads the versioned Random Forest model artifact, validates feature schemas,
computes phishing probabilities, applies configurable risk thresholds,
and generates explainable contributing factor narratives.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

from app.core.config import settings
from app.schemas.ml import (
    MLConfidenceLevel,
    MLModelStatus,
    MLPredictionLabel,
    MLPredictionResponse,
)
from app.services.ml_feature_adapter import (
    extract_feature_vector,
    generate_explainable_indicators,
)

logger = logging.getLogger("trustguard.service.ml_detection")


class MLDetectionService:
    """Service providing local machine-learning URL phishing risk classification."""

    _instance: Optional["MLDetectionService"] = None

    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        metrics_path: Optional[Path] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self._model_path = model_path or (base_dir / settings.ML_MODEL_PATH)
        self._metadata_path = metadata_path or (base_dir / settings.ML_METADATA_PATH)
        self._metrics_path = metrics_path or (base_dir / settings.ML_METRICS_PATH)

        self._model: Optional[Any] = None
        self._metadata: Dict[str, Any] = {}
        self._metrics: Dict[str, Any] = {}
        self._status: MLModelStatus = "MODEL_UNAVAILABLE"
        self._version: str = "unavailable"

        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Safely loads model artifact and metadata from disk without crashing on failure."""
        if not self._model_path.exists():
            logger.info(
                "ML model artifact not found at %s. ML service operating in MODEL_UNAVAILABLE state.",
                self._model_path,
            )
            self._status = "MODEL_UNAVAILABLE"
            return

        try:
            # Safe deserialization using joblib
            loaded_model = joblib.load(self._model_path)
            if not hasattr(loaded_model, "predict_proba"):
                logger.error("Loaded model object does not support predict_proba.")
                self._status = "ERROR"
                return

            self._model = loaded_model

            # Load metadata if present
            if self._metadata_path.exists():
                try:
                    with open(self._metadata_path, "r", encoding="utf-8") as f:
                        self._metadata = json.load(f)
                        self._version = self._metadata.get("model_version", "rf-v1.0.0")
                except Exception as e:
                    logger.warning("Could not read model metadata: %s", e)
                    self._version = "rf-v1.0.0"
            else:
                self._version = "rf-v1.0.0"

            # Load evaluation metrics if present
            if self._metrics_path.exists():
                try:
                    with open(self._metrics_path, "r", encoding="utf-8") as f:
                        self._metrics = json.load(f)
                except Exception as e:
                    logger.debug("Could not read metrics file: %s", e)

            self._status = "ACTIVE"
            logger.info(
                "ML Phishing Detection model %s loaded successfully (status=ACTIVE).", self._version
            )

        except Exception as e:
            logger.error("Failed to load ML model artifact from %s: %s", self._model_path, e)
            self._model = None
            self._status = "ERROR"
            self._version = "unavailable"

    @property
    def status(self) -> MLModelStatus:
        return self._status

    @property
    def model_version(self) -> str:
        return self._version

    @property
    def is_available(self) -> bool:
        return self._status == "ACTIVE" and self._model is not None

    def predict(
        self,
        features_dict: Dict[str, Any],
        raw_url: Optional[str] = None,
    ) -> MLPredictionResponse:
        """
        Generates phishing probability, classification label, subscore,
        and explainable contributing indicators from extracted URL features.
        """
        # Case 1: Model Unavailable or Loading Failed
        if not self.is_available:
            return MLPredictionResponse(
                prediction="UNKNOWN",
                phishing_probability=None,
                ml_subscore=None,
                confidence="INSUFFICIENT",
                model_version=self._version,
                model_status=self._status,
                indicators=[],
                top_feature_importance=None,
                summary="Machine learning phishing detection model is unavailable. Phishing prediction was not performed.",
            )

        # Case 2: Active Model Inference
        try:
            # 1. Extract and validate numerical feature vector matching model's expected input dimension
            n_expected = getattr(self._model, "n_features_in_", None)
            vector = extract_feature_vector(features_dict, target_feature_count=n_expected)

            # 2. Compute class probabilities [p(legitimate), p(phishing)]
            probas = self._model.predict_proba([vector])[0]
            phishing_proba = float(probas[1])

            # 3. Categorize into risk label using configurable thresholds
            if phishing_proba >= settings.ML_THRESHOLD_PHISHING:
                prediction: MLPredictionLabel = "PHISHING"
                confidence: MLConfidenceLevel = "HIGH" if phishing_proba >= 0.85 else "MEDIUM"
                summary = (
                    f"High probability ({phishing_proba:.1%}) of phishing characteristics detected. "
                    "URL lexical and structural patterns strongly resemble known attack vectors."
                )
                ml_subscore = max(0, int((1.0 - phishing_proba) * 100))

            elif phishing_proba >= settings.ML_THRESHOLD_LEGITIMATE:
                prediction = "SUSPICIOUS"
                confidence = "MEDIUM"
                summary = (
                    f"Moderate probability ({phishing_proba:.1%}) of suspicious URL structure. "
                    "Features exhibit anomalies common in phishing or social engineering attempts."
                )
                ml_subscore = max(30, int((1.0 - phishing_proba) * 100))

            else:
                prediction = "LIKELY_LEGITIMATE"
                confidence = "HIGH" if phishing_proba <= 0.15 else "MEDIUM"
                summary = (
                    f"Low probability ({phishing_proba:.1%}) of phishing patterns. "
                    "URL structure conforms closely to legitimate domain conventions."
                )
                ml_subscore = min(100, int((1.0 - phishing_proba) * 100))

            # 4. Generate explainable contributing indicators
            indicators = generate_explainable_indicators(features_dict)

            # 5. Extract top feature importances from metadata
            top_features = self._metadata.get("top_features")
            top_importance = dict(list(top_features.items())[:5]) if top_features else None

            return MLPredictionResponse(
                prediction=prediction,
                phishing_probability=round(phishing_proba, 4),
                ml_subscore=ml_subscore,
                confidence=confidence,
                model_version=self._version,
                model_status=self._status,
                indicators=indicators,
                top_feature_importance=top_importance,
                summary=summary,
            )

        except Exception as e:
            logger.error("Error during ML phishing inference: %s", e)
            return MLPredictionResponse(
                prediction="UNKNOWN",
                phishing_probability=None,
                ml_subscore=None,
                confidence="INSUFFICIENT",
                model_version=self._version,
                model_status="ERROR",
                indicators=[],
                top_feature_importance=None,
                summary=f"Inference error during ML evaluation: {e}",
            )


# Global singleton cache
_ml_service_instance: Optional[MLDetectionService] = None


def get_ml_service() -> MLDetectionService:
    """Returns the cached singleton instance of MLDetectionService."""
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLDetectionService()
    return _ml_service_instance
