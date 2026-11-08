"""
Automated test suite for URL Validation, Normalisation, Feature Extraction,
and Scanner API endpoints.
Verifies RFC compliance, SSRF static blocking, feature extraction, and database persistence.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.services.auth_service import _generate_mock_jwt
from app.services.url_analyzer import URLAnalyzer
from app.services.url_validator import validate_url_static
from app.utils.url_normalizer import compute_url_hash, normalize_url

# ==============================================================================
# 1. URL NORMALISATION TESTS
# ==============================================================================


def test_url_normalizer_canonical_forms():
    """Verify standard canonical normalisation rules."""
    # 1. Lowercase scheme and host
    assert normalize_url("HTTPS://EXAMPLE.COM/PATH") == "https://example.com/PATH"

    # 2. Add root slash if path empty
    assert normalize_url("https://example.com") == "https://example.com/"

    # 3. Strip default ports
    assert normalize_url("http://example.com:80/home") == "http://example.com/home"
    assert normalize_url("https://example.com:443/home") == "https://example.com/home"

    # 4. Retain non-default ports
    assert normalize_url("https://example.com:8443/home") == "https://example.com:8443/home"

    # 5. Strip trailing dot in host
    assert normalize_url("https://example.com./") == "https://example.com/"

    # 6. Remove fragments
    assert normalize_url("https://example.com/page#section1") == "https://example.com/page"

    # 7. Preserve query parameters
    norm_query = normalize_url("https://example.com/login?b=2&a=1")
    assert "a=1" in norm_query and "b=2" in norm_query


def test_url_normalizer_idna():
    """Verify internationalised domain names are converted to IDNA ASCII."""
    normalized = normalize_url("http://münchen.de/")
    assert "xn--" in normalized


def test_url_hash_computation():
    """Verify SHA-256 hash generation is deterministic."""
    url1 = "https://example.com/login"
    hash1 = compute_url_hash(url1)
    hash2 = compute_url_hash(url1)
    assert len(hash1) == 64
    assert hash1 == hash2


# ==============================================================================
# 2. STATIC VALIDATION & SSRF TESTS
# ==============================================================================


def test_validator_accepts_valid_urls():
    """Verify legitimate website URLs pass validation."""
    valid_samples = [
        "https://example.com",
        "http://example.com/login",
        "https://sub.portal.example.com/dashboard?view=summary",
        "https://example.org:8080/app/",
        "http://news.bbc.co.uk/world",
    ]
    for url in valid_samples:
        result = validate_url_static(url)
        assert result.is_valid, f"Expected '{url}' to be valid, got: {result.error_message}"


def test_validator_rejects_invalid_inputs():
    """Verify malformed and empty URLs are rejected with clear codes."""
    assert not validate_url_static("")
    assert not validate_url_static("    ")
    assert not validate_url_static("not_a_url")
    assert not validate_url_static("http://")
    assert not validate_url_static("https://example.com:9999999")  # Port out of range
    assert not validate_url_static("https://example.com/%zz")  # Malformed percent-encoding
    assert not validate_url_static("https://example .com")  # Whitespace in URL


def test_validator_rejects_unsupported_schemes():
    """Verify dangerous schemes (file, javascript, data, ftp) are rejected."""
    dangerous = [
        "file:///etc/passwd",
        "file:///C:/Windows/System32",
        "javascript:alert(document.cookie)",
        "data:text/html,<script>alert(1)</script>",
        "ftp://ftp.example.com/files",
        "gopher://gopher.example.com",
        "ws://echo.websocket.org",
    ]
    for url in dangerous:
        res = validate_url_static(url)
        assert not res.is_valid
        assert res.error_code == "UNSUPPORTED_SCHEME"


def test_validator_statically_blocks_ssrf_targets():
    """Verify loopback, private IPs, and cloud metadata targets are rejected."""
    blocked_targets = [
        "http://localhost/admin",
        "http://localhost:8080/",
        "http://127.0.0.1/status",
        "http://127.0.0.2/",
        "http://10.0.0.1/config",
        "http://192.168.1.1/router",
        "http://172.16.0.5/api",
        "http://169.254.169.254/latest/meta-data/",  # AWS/Azure/GCP metadata IP
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://0.0.0.0/",
    ]
    for target in blocked_targets:
        res = validate_url_static(target)
        assert not res.is_valid
        assert res.error_code in ("BLOCKED_HOSTNAME_SSRF", "PRIVATE_IP_SSRF")


# ==============================================================================
# 3. FEATURE EXTRACTION & PRELIMINARY RISK ANALYSIS TESTS
# ==============================================================================


def test_feature_extractor_metrics():
    """Verify measurable features are correctly counted."""
    analyzer = URLAnalyzer()
    raw = "http://secure-login.paypal.com.evil.xyz/account/verify?token=123"
    norm = normalize_url(raw)
    result = analyzer.analyze(raw_url=raw, normalized_url=norm)

    features = result["features"]
    assert features["uses_https"] is False
    assert features["subdomain_count"] >= 3
    assert features["contains_suspicious_keywords"] is True
    assert "login" in features["suspicious_keywords"]
    assert features["has_brand_in_subdomain"] is True
    assert features["has_suspicious_tld"] is True

    # High concern categorization
    assert result["risk_level"] == "HIGH_CONCERN"
    assert len(result["indicators"]) >= 3


def test_feature_extractor_at_symbol_detection():
    """Verify userinfo trick with '@' is flagged with high severity."""
    analyzer = URLAnalyzer()
    raw = "http://google.com@attacker-site.com/login"
    result = analyzer.analyze(raw_url=raw, normalized_url=raw)

    indicator_names = [i["name"] for i in result["indicators"]]
    assert "AT_SYMBOL_OBFUSCATION" in indicator_names
    assert result["risk_level"] == "HIGH_CONCERN"


def test_feature_extractor_clean_url():
    """Verify standard legitimate URL produces LOW_CONCERN with minimal flags."""
    analyzer = URLAnalyzer()
    raw = "https://www.google.com/search?q=python"
    norm = normalize_url(raw)
    result = analyzer.analyze(raw_url=raw, normalized_url=norm)

    assert result["risk_level"] == "LOW_CONCERN"
    # Should not have high or critical severity indicators
    severities = [i["severity"] for i in result["indicators"]]
    assert "critical" not in severities
    assert "high" not in severities


# ==============================================================================
# 4. SCANNER API ENDPOINT TESTS (POST /api/v1/scan)
# ==============================================================================


def test_guest_scan_submission(client: TestClient):
    """Verify anonymous guest user can submit a URL and receive structured response."""
    payload = {"url": "https://wikipedia.org/wiki/Computer_security"}
    response = client.post("/api/v1/scan", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert "scan_id" in data
    assert data["original_url"] == payload["url"]
    assert data["is_guest"] is True
    assert "preliminary_analysis" in data
    assert "features" in data["preliminary_analysis"]
    assert "indicators" in data["preliminary_analysis"]


def test_authenticated_scan_submission(client: TestClient):
    """Verify authenticated user's scan is linked to their user_id."""
    user_id = uuid.uuid4()
    token = _generate_mock_jwt(user_id, "scanner_test@trustguard.ai")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"url": "https://github.com/trending"}
    response = client.post("/api/v1/scan", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["is_guest"] is False
    scan_id = data["scan_id"]

    # Verify retrieval via GET /api/v1/scan/{scan_id}
    get_res = client.get(f"/api/v1/scan/{scan_id}", headers=headers)
    assert get_res.status_code == 200
    scan_data = get_res.json()["scan"]
    assert scan_data["id"] == scan_id
    assert scan_data["user_id"] == str(user_id)


def test_scan_submission_rejected_for_invalid_url(client: TestClient):
    """Verify malformed or dangerous URLs return 422 error."""
    # 1. Invalid scheme
    res_scheme = client.post("/api/v1/scan", json={"url": "ftp://malicious.com"})
    assert res_scheme.status_code == 422

    # 2. SSRF Loopback target
    res_ssrf = client.post("/api/v1/scan", json={"url": "http://127.0.0.1:8080/admin"})
    assert res_ssrf.status_code == 422
    assert "error" in res_ssrf.json()


def test_scanner_status_endpoint(client: TestClient):
    """Verify GET /api/v1/scan/status returns 200 ready status."""
    res = client.get("/api/v1/scan/status")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"
