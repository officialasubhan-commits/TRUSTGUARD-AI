"""
Automated tests for Supabase Database operations, schemas, models, and ownership checks.
"""

import uuid

import pytest

from app.core.exceptions import ForbiddenError, ScanNotFoundError
from app.database.connection import check_db_health, init_database
from app.database.repositories.report_repo import ReportRepository
from app.database.repositories.scan_repo import ScanRepository
from app.database.repositories.threat_repo import ThreatRepository
from app.database.repositories.user_repo import UserRepository
from app.schemas.report import CommunityReportCreate
from app.schemas.scan import ScanCreate, ScanResultCreate, ScanStatusUpdate
from app.schemas.threat_intel import ThreatIntelCreate
from app.schemas.user import UserCreate, UserUpdate


@pytest.fixture
def user_repo():
    return UserRepository()


@pytest.fixture
def scan_repo():
    return ScanRepository()


@pytest.fixture
def report_repo():
    return ReportRepository()


@pytest.fixture
def threat_repo():
    return ThreatRepository()


def test_database_initialization_and_health():
    """Verify that database initialisation does not crash and reports health."""
    init_database()
    health = check_db_health()
    assert health in ("connected", "unconfigured", "ready", "degraded")


@pytest.mark.asyncio
async def test_create_and_retrieve_user_profile(user_repo: UserRepository):
    """Test user profile creation, lookup, and updates."""
    user_id = uuid.uuid4()
    user_in = UserCreate(
        id=user_id,
        email="test_user@trustguard.ai",
        full_name="Alice Sentinel",
        avatar_url="https://avatar.example.com/alice.png",
    )
    created = await user_repo.create_user_profile(user_in)
    assert created.id == user_id
    assert created.email == "test_user@trustguard.ai"
    assert created.full_name == "Alice Sentinel"
    assert created.scan_count == 0

    fetched = await user_repo.get_user_profile(user_id)
    assert fetched is not None
    assert fetched.id == user_id

    # Update profile
    updated = await user_repo.update_user_profile(user_id, UserUpdate(full_name="Alice Security"))
    assert updated is not None
    assert updated.full_name == "Alice Security"


@pytest.mark.asyncio
async def test_scan_lifecycle_and_ownership(scan_repo: ScanRepository):
    """
    Test scan creation, status updating, result attachment,
    and strict ownership enforcement.
    """
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    # 1. Create scan
    scan = await scan_repo.create_scan_record(
        submitted_url="https://suspicious-test.com/login",
        normalized_url="https://suspicious-test.com/login",
        url_hash="mockhash1234567890abcdef",
        user_id=owner_id,
        is_guest=False,
    )
    assert scan.scan_status == "pending"
    assert scan.user_id == owner_id

    # 2. Update status
    updated = await scan_repo.update_scan_status(
        scan.id,
        ScanStatusUpdate(
            scan_status="complete",
            risk_level="HIGH",
            trust_score=30,
        ),
    )
    assert updated.scan_status == "complete"
    assert updated.trust_score == 30
    assert updated.risk_level == "HIGH"

    # 3. Save scan result
    result_in = ScanResultCreate(
        scan_id=scan.id,
        trust_score=30,
        overall_risk_level="HIGH",
        phishing_probability=0.88,
        ml_prediction="phishing",
        virustotal_detection_count=12,
        virustotal_total_engines=70,
        score_breakdown={"vt": 30, "ml": 12, "ssl": 50, "url": 40},
        analysis_summary="High risk phishing URL detected by ML and multiple VT engines.",
    )
    saved_result = await scan_repo.save_scan_results(result_in)
    assert saved_result.trust_score == 30
    assert saved_result.overall_risk_level == "HIGH"

    # 4. Ownership check: Owner accesses -> SUCCESS
    s_rec, r_rec = await scan_repo.get_scan_by_id_with_ownership(
        scan.id, requesting_user_id=owner_id
    )
    assert s_rec.id == scan.id
    assert r_rec is not None
    assert r_rec.trust_score == 30

    # 5. Ownership check: Other user accesses -> FORBIDDEN (403)
    with pytest.raises(ForbiddenError):
        await scan_repo.get_scan_by_id_with_ownership(scan.id, requesting_user_id=other_user_id)

    # 6. Ownership check: Unauthenticated user accesses private scan -> FORBIDDEN (403)
    with pytest.raises(ForbiddenError):
        await scan_repo.get_scan_by_id_with_ownership(scan.id, requesting_user_id=None)


@pytest.mark.asyncio
async def test_guest_scan_isolation(scan_repo: ScanRepository):
    """
    Test guest scan behavior:
    - Direct lookup with valid scan_id is allowed.
    - Guest scan is strictly excluded from user history listings.
    """
    guest_scan = await scan_repo.create_scan_record(
        submitted_url="https://public-guest-check.com",
        normalized_url="https://public-guest-check.com",
        url_hash="guesthash123",
        user_id=None,
        is_guest=True,
    )
    assert guest_scan.is_guest is True
    assert guest_scan.user_id is None

    # Allowed with scan_id
    s_rec, _ = await scan_repo.get_scan_by_id_with_ownership(guest_scan.id, requesting_user_id=None)
    assert s_rec.id == guest_scan.id

    # Not in user history
    user_id = uuid.uuid4()
    history = await scan_repo.get_user_scan_history(user_id)
    assert not any(h.id == guest_scan.id for h in history)


@pytest.mark.asyncio
async def test_nonexistent_scan_raises_404(scan_repo: ScanRepository):
    """Test that requesting an unknown scan_id raises ScanNotFoundError."""
    random_id = uuid.uuid4()
    with pytest.raises(ScanNotFoundError):
        await scan_repo.get_scan_by_id_with_ownership(random_id)


@pytest.mark.asyncio
async def test_community_threat_reporting(report_repo: ReportRepository):
    """Test submitting and querying community threat reports."""
    reporter_id = uuid.uuid4()
    report_in = CommunityReportCreate(
        submitted_url="https://phishing-scam-bank.com/login",
        report_reason="phishing",
        target_brand="TestBank",
        attack_vector="email",
        notes="Received email requesting urgent credential verification.",
    )
    created_report = await report_repo.create_community_report(
        user_id=reporter_id,
        report_in=report_in,
        normalized_url="https://phishing-scam-bank.com/login",
    )
    assert created_report.submitted_url == "https://phishing-scam-bank.com/login"
    assert created_report.report_reason == "phishing"
    assert created_report.report_status == "pending_review"

    # Query reports
    reports = await report_repo.get_community_reports(
        normalized_url="https://phishing-scam-bank.com/login"
    )
    assert len(reports) >= 1
    assert reports[0].id == created_report.id


@pytest.mark.asyncio
async def test_threat_intelligence_recording(threat_repo: ThreatRepository):
    """Test saving and retrieving threat intelligence entries."""
    intel_in = ThreatIntelCreate(
        normalized_url="https://malware-drop.com/payload.exe",
        domain="malware-drop.com",
        threat_source="virustotal",
        threat_category="trojan",
        severity="critical",
        verification_status="verified",
    )
    saved = await threat_repo.save_threat_record(intel_in)
    assert saved.domain == "malware-drop.com"
    assert saved.severity == "critical"

    # Query by domain
    domain_threats = await threat_repo.get_threat_records_by_domain("malware-drop.com")
    assert len(domain_threats) >= 1
    assert domain_threats[0].threat_source == "virustotal"


def test_invalid_input_validation():
    """Verify that Pydantic schemas reject invalid inputs."""
    # Invalid URL scheme
    with pytest.raises(ValueError):
        ScanCreate(url="ftp://invalid-ftp-site.com")

    # Invalid URL string
    with pytest.raises(ValueError):
        ScanCreate(url="not a url")

    # Invalid score (> 100)
    with pytest.raises(ValueError):
        ScanResultCreate(
            scan_id=uuid.uuid4(),
            trust_score=150,  # Invalid: max is 100
            overall_risk_level="SAFE",
            score_breakdown={},
        )

    # Invalid negative score
    with pytest.raises(ValueError):
        ScanResultCreate(
            scan_id=uuid.uuid4(),
            trust_score=-5,  # Invalid: min is 0
            overall_risk_level="CRITICAL",
            score_breakdown={},
        )
