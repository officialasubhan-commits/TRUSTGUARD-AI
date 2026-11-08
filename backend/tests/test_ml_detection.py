"""
Automated test suite for Machine Learning Phishing Detection Engine.

Verifies:
1. Feature vector extraction & ordering (23 numerical features).
2. Handling of missing or malformed feature dictionaries.
3. Model loading from disk and metadata ingestion.
4. Graceful handling of missing or corrupted model artifacts (MODEL_UNAVAILABLE).
5. Threshold classification (PHISHING, SUSPICIOUS, LIKELY_LEGITIMATE).
6. Explainable contributing indicators generation.
7. Integration with the existing POST /api/v1/scan endpoint.
8. Synthetic legitimate and phishing URL fixtures without network calls.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.ml_detection_service import MLDetectionService
from app.services.ml_feature_adapter import (
    FEATURE_NAMES,
    extract_feature_vector,
    generate_explainable_indicators,
)
from app.services.url_analyzer import URLAnalyzer

# ==============================================================================
# 1. FEATURE ADAPTER & VECTOR SCHEMA TESTS
# ==============================================================================


def test_feature_vector_dimension_and_order():
    """Verify exact 23 features are extracted in deterministic order."""
    analyzer = URLAnalyzer()
    raw_url = "https://secure-login.paypal.com.verify-user.xyz:8080/signin?id=123"
    norm_url = "https://secure-login.paypal.com.verify-user.xyz:8080/signin?id=123"

    analysis = analyzer.analyze(raw_url=raw_url, normalized_url=norm_url)
    features_dict = analysis["features"]

    vector = extract_feature_vector(features_dict)

    assert len(vector) == len(FEATURE_NAMES)
    assert len(vector) == 23
    assert all(isinstance(val, float) for val in vector)


def test_feature_vector_missing_keys_handled():
    """Verify adapter supplies safe defaults for empty or partial feature dicts."""
    empty_features = {}
    vector = extract_feature_vector(empty_features)

    assert len(vector) == len(FEATURE_NAMES)
    assert all(val == 0.0 for val in vector)


def test_explainable_indicators_generation():
    """Verify human-readable explanations are created only when features are present."""
    # Fixture with specific triggers
    suspicious_features = {
        "is_ip_address": True,
        "has_at_symbol": True,
        "contains_suspicious_keywords": True,
        "suspicious_keywords": ["login", "verify"],
        "has_brand_in_subdomain": True,
        "url_length": 95,
        "uses_https": False,
    }

    indicators = generate_explainable_indicators(suspicious_features)

    assert any("raw numerical IP address" in ind for ind in indicators)
    assert any("'@' userinfo character" in ind for ind in indicators)
    assert any("login, verify" in ind for ind in indicators)
    assert any("brand keyword is embedded" in ind for ind in indicators)
    assert any("Unusually long URL" in ind for ind in indicators)
    assert any("Unencrypted connection" in ind for ind in indicators)


# ==============================================================================
# 2. MODEL LOADING & FALLBACK TESTS
# ==============================================================================


def test_ml_service_active_loading():
    """Verify default service loads the trained Random Forest model successfully."""
    service = MLDetectionService()
    assert service.is_available is True
    assert service.status == "ACTIVE"
    assert service.model_version.startswith("rf-")


def test_ml_service_missing_model_fallback():
    """Verify service gracefully enters MODEL_UNAVAILABLE when model file does not exist."""
    fake_path = Path(tempfile.gettempdir()) / "nonexistent_model_12345.joblib"
    service = MLDetectionService(model_path=fake_path)

    assert service.is_available is False
    assert service.status == "MODEL_UNAVAILABLE"

    # Inference should return MODEL_UNAVAILABLE response without raising an exception
    response = service.predict(features_dict={})
    assert response.prediction == "MODEL_UNAVAILABLE"
    assert response.model_status == "MODEL_UNAVAILABLE"
    assert response.phishing_probability is None
    assert response.ml_subscore == 100
    assert "not available" in response.summary.lower()


def test_ml_service_corrupted_model_handling():
    """Verify service gracefully enters ERROR when model file is corrupted."""
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
        f.write(b"NOT_A_VALID_JOBLIB_PICKLE_DATA")
        corrupted_path = Path(f.name)

    try:
        service = MLDetectionService(model_path=corrupted_path)
        assert service.is_available is False
        assert service.status == "ERROR"

        response = service.predict(features_dict={})
        assert response.prediction == "MODEL_UNAVAILABLE"
        assert response.model_status == "ERROR"
    finally:
        if corrupted_path.exists():
            corrupted_path.unlink()


# ==============================================================================
# 3. THRESHOLD CLASSIFICATION & PREDICTION LOGIC
# ==============================================================================


def test_threshold_classification_phishing():
    """Verify probability >= 0.70 yields PHISHING prediction and penalized subscore."""
    service = MLDetectionService()
    mock_clf = MagicMock()
    mock_clf.predict_proba.return_value = [[0.10, 0.90]]  # 90% phishing
    service._model = mock_clf
    service._status = "ACTIVE"

    response = service.predict(features_dict={"url_length": 80, "dot_count": 4})

    assert response.prediction == "PHISHING"
    assert response.phishing_probability == 0.90
    assert response.ml_subscore <= 30
    assert response.confidence == "HIGH"
    assert "High probability" in response.summary


def test_threshold_classification_suspicious():
    """Verify probability between 0.30 and 0.69 yields SUSPICIOUS prediction."""
    service = MLDetectionService()
    mock_clf = MagicMock()
    mock_clf.predict_proba.return_value = [[0.55, 0.45]]  # 45% phishing
    service._model = mock_clf
    service._status = "ACTIVE"

    response = service.predict(features_dict={"hyphen_count": 3})

    assert response.prediction == "SUSPICIOUS"
    assert response.phishing_probability == 0.45
    assert 30 <= response.ml_subscore <= 70
    assert response.confidence == "MEDIUM"
    assert "Moderate probability" in response.summary


def test_threshold_classification_legitimate():
    """Verify probability < 0.30 yields LIKELY_LEGITIMATE prediction."""
    service = MLDetectionService()
    mock_clf = MagicMock()
    mock_clf.predict_proba.return_value = [[0.95, 0.05]]  # 5% phishing
    service._model = mock_clf
    service._status = "ACTIVE"

    response = service.predict(features_dict={"uses_https": True})

    assert response.prediction == "LIKELY_LEGITIMATE"
    assert response.phishing_probability == 0.05
    assert response.ml_subscore >= 90
    assert response.confidence == "HIGH"
    assert "Low probability" in response.summary


# ==============================================================================
# 4. END-TO-END INFERENCE WITH REAL TRAINED MODEL
# ==============================================================================


def test_real_model_inference_on_legitimate_url():
    """Verify live inference against typical legitimate URL patterns."""
    service = MLDetectionService()
    analyzer = URLAnalyzer()

    legit_url = "https://www.google.com/search?q=cybersecurity+defense"
    analysis = analyzer.analyze(raw_url=legit_url, normalized_url=legit_url)

    response = service.predict(features_dict=analysis["features"])

    assert response.prediction in ("LIKELY_LEGITIMATE", "SUSPICIOUS")
    assert response.phishing_probability is not None
    assert response.phishing_probability < 0.50
    assert response.model_status == "ACTIVE"


def test_real_model_inference_on_phishing_patterns():
    """Verify live inference on synthetic deceptive phishing patterns."""
    service = MLDetectionService()
    analyzer = URLAnalyzer()

    # Synthetic suspicious phishing pattern (IP host, non-standard port, auth path)
    phish_url = "http://192.168.1.100:8080/paypal-verification/secure-update/login.php"
    analysis = analyzer.analyze(raw_url=phish_url, normalized_url=phish_url)

    response = service.predict(features_dict=analysis["features"])

    assert response.prediction in ("PHISHING", "SUSPICIOUS")
    assert response.phishing_probability is not None
    assert response.phishing_probability >= 0.30
    assert len(response.indicators) >= 1


# ==============================================================================
# 5. INTEGRATION WITH POST /api/v1/scan ENDPOINT
# ==============================================================================


def test_scan_endpoint_includes_ml_prediction():
    """Verify POST /api/v1/scan returns integrated ml_prediction schema."""
    client = TestClient(app)

    response = client.post(
        "/api/v1/scan", json={"url": "https://www.wikipedia.org/wiki/Computer_security"}
    )
    assert response.status_code == 201

    data = response.json()
    assert "ml_prediction" in data
    assert data["ml_prediction"] is not None

    ml_data = data["ml_prediction"]
    assert "prediction" in ml_data
    assert ml_data["prediction"] in (
        "PHISHING",
        "SUSPICIOUS",
        "LIKELY_LEGITIMATE",
        "MODEL_UNAVAILABLE",
    )
    assert "model_status" in ml_data
    assert "model_version" in ml_data
    assert "indicators" in ml_data
    assert "disclaimer" in ml_data
