"""
TrustGuard AI - ML Intelligence & Domain Reputation Engine Test Suite
Tests:
- Shannon Entropy & Character Ratios
- Homograph and Lookalike Detection
- 30-Feature Extraction (Schema v2)
- ML Feature Adapter & Dynamic Dimensionality
- ML Detection Service Inference
- Domain Reputation Service (Verified, Impersonation, Safe DNS)
- Risk Scoring Engine Integration
"""

import pytest
import asyncio
from backend.app.utils.entropy import (
    calculate_shannon_entropy,
    calculate_char_ratios,
    detect_homograph_and_lookalikes,
)
from backend.app.services.url_analyzer import URLAnalyzer
from backend.app.services.ml_feature_adapter import (
    extract_feature_vector,
    generate_explainable_indicators,
    FEATURE_NAMES_V1,
    FEATURE_NAMES_V2,
)
from backend.app.services.ml_detection_service import MLDetectionService
from backend.app.services.domain_reputation_service import DomainReputationService
from backend.app.services.risk_scoring_service import RiskScoringService
from backend.app.core.trusted_domains import (
    extract_registered_domain,
    check_brand_impersonation,
    VERIFIED_ENTITIES,
)


def test_shannon_entropy_calculation():
    """Verify entropy bounds and high-randomness detection."""
    # Zero entropy for uniform string
    assert calculate_shannon_entropy("aaaaaaa") == 0.0

    # Normal English word has moderate entropy (~2.0 - 3.0)
    word_entropy = calculate_shannon_entropy("google")
    assert 1.5 <= word_entropy <= 3.0

    # DGA / randomized hash string has high entropy (> 3.0)
    dga_entropy = calculate_shannon_entropy("x8q9z2w1k4j7p0m5.example.com")
    assert dga_entropy > 3.0


def test_character_ratios():
    """Verify digit-to-letter and vowel-to-consonant ratios (returns tuple)."""
    # Alphabetical word "apple"
    d_l_ratio, v_c_ratio = calculate_char_ratios("apple")
    assert d_l_ratio == 0.0
    assert v_c_ratio == pytest.approx(2 / 4, 0.01)  # 2 vowels / (3 consonants + 1)

    # String with numbers "secure1234"
    num_d_l, _ = calculate_char_ratios("secure1234")
    assert num_d_l > 0.0


def test_homograph_and_lookalike_detection():
    """Verify Cyrillic / mixed-script homographs and brand lookalikes (returns tuple)."""
    # Cyrillic 'а' (U+0430) inside "paypal"
    cyrillic_paypal = "p\u0430ypal.com"
    has_homograph, reason = detect_homograph_and_lookalikes(cyrillic_paypal)
    assert has_homograph is True
    assert "NON_ASCII" in reason

    # Brand lookalike with numeral substitution: paypa1
    has_num_lookalike, num_reason = detect_homograph_and_lookalikes("paypa1.com")
    assert has_num_lookalike is True
    assert "PAYPAL" in num_reason

    # Standard ASCII domain
    normal_has, normal_reason = detect_homograph_and_lookalikes("paypal.com")
    assert normal_has is False


def test_registered_domain_extraction():
    """Verify eTLD+1 extraction with multi-part suffixes (.co.uk, .com.au, .gov.in)."""
    assert extract_registered_domain("sub.google.com") == "google.com"
    assert extract_registered_domain("login.verify.amazon.co.uk") == "amazon.co.uk"
    assert extract_registered_domain("portal.cyber.gov.in") == "cyber.gov.in"
    assert extract_registered_domain("fake-google.xyz") == "fake-google.xyz"


def test_verified_entity_registry():
    """Verify top reputable brands are identified by exact registered domain."""
    google_entity = VERIFIED_ENTITIES.get("google.com")
    assert google_entity is not None
    assert "Google" in google_entity["entity"]

    gh_entity = VERIFIED_ENTITIES.get("github.com")
    assert gh_entity is not None
    assert "GitHub" in gh_entity["entity"]

    # Malicious subdomain on another domain is NOT in verified entities
    fake_domain = extract_registered_domain("google.com.attacker.com")
    assert fake_domain == "attacker.com"
    assert fake_domain not in VERIFIED_ENTITIES


def test_brand_impersonation_detection():
    """Verify brand lookalikes and phishing masquerade detection."""
    # Impersonator on suspicious domain
    reg_domain = extract_registered_domain("google-security-verify.xyz")
    is_imp, brand, details = check_brand_impersonation("google-security-verify.xyz", reg_domain)
    assert is_imp is True
    assert brand == "google"

    # Legitimate subdomains of the brand are NOT flagged as impersonators
    reg_legit = extract_registered_domain("accounts.google.com")
    is_imp_legit, _, _ = check_brand_impersonation("accounts.google.com", reg_legit)
    assert is_imp_legit is False


def test_30_features_url_analyzer():
    """Verify URLAnalyzer extracts all 30 Schema v2 features."""
    analyzer = URLAnalyzer()
    res = analyzer.analyze(
        "https://secure-login.bank-update.xyz/auth/verify?session=123",
        "https://secure-login.bank-update.xyz/auth/verify?session=123",
    )
    features = res["features"]

    assert len(features) >= 30
    assert "url_entropy" in features
    assert "hostname_entropy" in features
    assert "digit_letter_ratio" in features
    assert "vowel_consonant_ratio" in features
    assert "has_homograph" in features
    assert "special_char_count" in features
    assert features["uses_https"] is True
    assert features["has_suspicious_tld"] is True


def test_ml_feature_adapter_v2():
    """Verify MLFeatureAdapter vector output and indicators for Schema v2."""
    analyzer = URLAnalyzer()
    res = analyzer.analyze(
        "http://suspicious-paypal-verify.club/login?acc=99",
        "http://suspicious-paypal-verify.club/login?acc=99",
    )
    raw = res["features"]

    # V2 30-dim vector
    vec_v2 = extract_feature_vector(raw, target_feature_count=30)
    assert len(vec_v2) == 30
    assert len(FEATURE_NAMES_V2) == 30

    # V1 23-dim backward compatibility vector
    vec_v1 = extract_feature_vector(raw, target_feature_count=23)
    assert len(vec_v1) == 23
    assert len(FEATURE_NAMES_V1) == 23

    indicators = generate_explainable_indicators(raw)
    assert isinstance(indicators, list)
    assert len(indicators) > 0


def test_ml_detection_service_prediction():
    """Verify MLDetectionService loads champion model and outputs calibrated predictions."""
    service = MLDetectionService()
    assert service.is_available is True
    assert service.status == "ACTIVE"

    analyzer = URLAnalyzer()

    # Test legitimate URL
    legit_url = "https://www.google.com/search?q=cybersecurity"
    legit_data = analyzer.analyze(legit_url, legit_url)["features"]
    legit_result = service.predict(legit_data, raw_url=legit_url)
    assert legit_result.prediction in ["LIKELY_LEGITIMATE", "SUSPICIOUS"]
    assert legit_result.phishing_probability is not None
    assert legit_result.phishing_probability < 0.50
    assert legit_result.model_version is not None

    # Test phishing URL with raw IP and credential keywords
    phish_url = "http://192.168.1.1/update-account/banking/login.php?ref=cmd"
    phish_data = analyzer.analyze(phish_url, phish_url)["features"]
    phish_result = service.predict(phish_data, raw_url=phish_url)
    assert phish_result.phishing_probability is not None
    assert phish_result.phishing_probability > 0.50


def test_domain_reputation_service_evaluation():
    """Verify DomainReputationService reputation categories and safety safeguards."""
    from unittest.mock import AsyncMock, MagicMock
    from app.schemas.domain_reputation import DNSIntelligence

    async def _run():
        mock_repo = MagicMock()
        mock_repo.get_scans_by_domain = AsyncMock(return_value=[])

        service = DomainReputationService(scan_repo=mock_repo)

        # Fast offline mock for DNS to run instantly without external network
        async def mock_dns(hostname: str):
            return DNSIntelligence(
                resolves=True,
                ip_addresses=["142.250.190.46"] if "google" in hostname else ["198.51.100.1"],
                is_private_or_loopback=False,
            )

        service._resolve_dns_safely = mock_dns

        # 1. Verified entity (Google)
        rep_google = await service.evaluate_domain("google.com")
        assert rep_google.category == "VERIFIED_ESTABLISHED"
        assert rep_google.is_established_authority is True
        assert rep_google.verified_identity is not None
        assert rep_google.reputation_score >= 90

        # 2. Impersonation (lookalike)
        rep_fake = await service.evaluate_domain("google-login-security.xyz")
        assert rep_fake.category == "IMPERSONATION_RISK"
        assert rep_fake.reputation_score <= 25
        assert rep_fake.is_lookalike_or_impersonation is True
        assert rep_fake.impersonated_brand == "google"

    asyncio.run(_run())


def test_risk_scoring_service_with_reputation():
    """Verify RiskScoringService synthesizes domain reputation signals correctly."""
    from app.schemas.domain_reputation import DomainReputationResult, DNSIntelligence, HistoricalScanTrend
    from app.schemas.ml import MLPredictionResponse
    from app.schemas.scanner import PreliminaryAnalysis
    from app.schemas.ssl import SSLValidationResponse

    scorer = RiskScoringService()

    # Base low-risk verified entity with valid technical telemetry
    google_rep = DomainReputationResult(
        domain="google.com",
        registered_domain="google.com",
        category="VERIFIED_ESTABLISHED",
        reputation_score=95,
        verified_identity="Google LLC",
        is_established_authority=True,
        is_lookalike_or_impersonation=False,
        dns_intelligence=DNSIntelligence(resolves=True, ip_addresses=["142.250.190.46"]),
        historical_trend=HistoricalScanTrend(total_scans=10, reputation_stability="STABLE_CLEAN"),
        reasons=["Domain is verified as authentic infrastructure belonging to Google LLC."],
        uncertainty_level="LOW",
    )

    url_analysis = PreliminaryAnalysis(risk_level="LOW_CONCERN", indicators=[], features={})
    ssl_analysis = SSLValidationResponse(status="VALID", valid=True, hostname="google.com")
    ml_pred = MLPredictionResponse(
        prediction="LIKELY_LEGITIMATE",
        phishing_probability=0.02,
        ml_subscore=98,
        confidence="HIGH",
        model_version="v2.0.0",
        model_status="ACTIVE",
        indicators=[],
        summary="Legitimate URL patterns.",
    )

    assessment_low = scorer.evaluate(
        url="https://google.com",
        url_analysis=url_analysis,
        ssl_analysis=ssl_analysis,
        ml_prediction=ml_pred,
        domain_reputation=google_rep,
    )
    assert assessment_low.digital_trust_score is not None
    assert assessment_low.digital_trust_score >= 70
    assert assessment_low.risk_level in ["LOW", "SAFE", "MEDIUM"]
    assert any("verified" in ind.title.lower() or "authority" in ind.title.lower() for ind in assessment_low.positive_indicators)

    # High-risk impersonation override
    fake_rep = DomainReputationResult(
        domain="google-login-verify.xyz",
        registered_domain="google-login-verify.xyz",
        category="IMPERSONATION_RISK",
        reputation_score=15,
        is_established_authority=False,
        is_lookalike_or_impersonation=True,
        impersonated_brand="google",
        dns_intelligence=DNSIntelligence(resolves=True, ip_addresses=["198.51.100.1"]),
        historical_trend=HistoricalScanTrend(total_scans=0, reputation_stability="NEW_UNOBSERVED"),
        reasons=["Domain combines protected brand 'google' with an urgent credential/security lure."],
        uncertainty_level="LOW",
    )

    assessment_high = scorer.evaluate(
        url="http://google-login-verify.xyz/login",
        domain_reputation=fake_rep,
    )
    assert assessment_high.risk_score is not None
    assert assessment_high.risk_score >= 80
    assert assessment_high.risk_level in ["HIGH", "CRITICAL"]
    assert any("impersonat" in ind.title.lower() or "lookalike" in ind.title.lower() for ind in assessment_high.risk_indicators)
