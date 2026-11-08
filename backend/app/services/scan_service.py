"""
Scan Service for TrustGuard AI.
Orchestrates URL validation, normalisation, feature extraction, database persistence,
and preliminary risk assessment.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Optional, Tuple
from urllib.parse import urlparse

from app.core.exceptions import InvalidURLError
from app.database.repositories.scan_repo import ScanRepository
from app.schemas.scan import (
    ScanHistoryResponse,
    ScanResultCreate,
    ScanResultResponse,
    ScanStatusUpdate,
)
from app.schemas.scanner import PreliminaryAnalysis, URLSubmissionResponse
from app.schemas.ssl import SSLValidationResponse
from app.schemas.virustotal import VirusTotalReportResponse
from app.services.domain_reputation_service import DomainReputationService
from app.services.ml_detection_service import MLDetectionService, get_ml_service
from app.services.risk_scoring_service import (
    RiskScoringService,
    get_risk_scoring_service,
)
from app.services.ssl_tls_service import SSLValidationService, get_ssl_service
from app.services.url_analyzer import URLAnalyzer
from app.services.url_validator import validate_url_static
from app.services.virustotal_service import VirusTotalService
from app.utils.url_normalizer import compute_url_hash, normalize_url

logger = logging.getLogger("trustguard.service.scan")


class ScanService:
    def __init__(
        self,
        scan_repo: Optional[ScanRepository] = None,
        analyzer: Optional[URLAnalyzer] = None,
        vt_service: Optional[VirusTotalService] = None,
        ml_service: Optional[MLDetectionService] = None,
        ssl_service: Optional[SSLValidationService] = None,
        risk_service: Optional[RiskScoringService] = None,
        reputation_service: Optional[DomainReputationService] = None,
    ):
        self._scan_repo = scan_repo or ScanRepository()
        self._analyzer = analyzer or URLAnalyzer()
        self._vt_service = vt_service or VirusTotalService()
        self._ml_service = ml_service or get_ml_service()
        self._ssl_service = ssl_service or get_ssl_service()
        self._risk_service = risk_service or get_risk_scoring_service()
        self._reputation_service = reputation_service or DomainReputationService(self._scan_repo)

    async def submit_url(
        self,
        raw_url: str,
        user_id: Optional[uuid.UUID] = None,
        is_guest: bool = False,
        client_ip: Optional[str] = None,
    ) -> URLSubmissionResponse:
        """
        Processes a URL submission from authenticated or guest users:
        1. Statically validates URL structure, scheme, host, and port.
        2. Normalises the URL to RFC 3986 canonical form.
        3. Computes the SHA-256 hash for deduplication.
        4. Extracts features and identifies preliminary security indicators.
        5. Persists the scan into the database (scan_history).
        6. Runs concurrent multi-engine inspection (ML, SSL, VirusTotal).
        7. Synthesizes Digital Trust Score and risk assessment.
        8. Persists findings and updates scan status in parallel.
        9. Returns structured URLSubmissionResponse with complete telemetry.
        """
        t_pipeline_start = time.perf_counter()

        # 1. Static Validation & Normalization
        t_val_start = time.perf_counter()
        validation = validate_url_static(raw_url)
        if not validation.is_valid:
            logger.warning(
                "URL validation failed for input '%s': %s", raw_url, validation.error_message
            )
            raise InvalidURLError(validation.error_message or "Invalid URL provided.")

        try:
            canonical_url = normalize_url(raw_url)
        except Exception as e:
            logger.error("URL normalisation failed for '%s': %s", raw_url, e)
            raise InvalidURLError(f"Failed to normalise URL: {e}")

        url_hash = compute_url_hash(canonical_url)
        analysis_data = self._analyzer.analyze(raw_url=raw_url, normalized_url=canonical_url)
        preliminary_analysis = PreliminaryAnalysis.model_validate(analysis_data)
        t_val_ms = (time.perf_counter() - t_val_start) * 1000

        validation_status = (
            "SUSPICIOUS" if preliminary_analysis.risk_level == "HIGH_CONCERN" else "VALID"
        )
        logger.info(
            "[TIMING] URL validation & heuristics: duration=%.2fms indicators=%d",
            t_val_ms,
            len(preliminary_analysis.indicators),
        )

        # 2. Database Persistence — Register initial scan
        t_db_init_start = time.perf_counter()
        scan_record = await self._scan_repo.create_scan_record(
            submitted_url=raw_url,
            normalized_url=canonical_url,
            url_hash=url_hash,
            user_id=user_id,
            is_guest=is_guest,
            ip_address=client_ip,
        )
        t_db_init_ms = (time.perf_counter() - t_db_init_start) * 1000
        logger.info(
            "[TIMING] Database persistence (initial registration): duration=%.2fms scan_id=%s is_guest=%s",
            t_db_init_ms,
            scan_record.id,
            is_guest,
        )

        # 3. Security Inspection Engines — Concurrent Execution
        # Engine A: ML Phishing Detection
        async def _eval_ml():
            t0 = time.perf_counter()
            pred = self._ml_service.predict(
                features_dict=preliminary_analysis.features,
                raw_url=raw_url,
            )
            t_ms = (time.perf_counter() - t0) * 1000
            prob = pred.phishing_probability if pred else 0.0
            logger.info("[TIMING] ML phishing prediction: duration=%.2fms probability=%.4f", t_ms, prob)
            return pred

        # Engine B: SSL/TLS Certificate Audit
        async def _eval_ssl() -> SSLValidationResponse:
            t0 = time.perf_counter()
            try:
                res = await self._ssl_service.validate_url_ssl(canonical_url)
            except Exception as e:
                logger.warning("SSL validation failed for %s: %s", canonical_url, e)
                parsed_host = urlparse(canonical_url).hostname or ""
                res = SSLValidationResponse(
                    status="UNKNOWN",
                    https_enabled=canonical_url.startswith("https"),
                    hostname=parsed_host,
                    findings=[f"SSL validation check error: {e}"],
                    message="SSL check could not be completed.",
                )
            t_ms = (time.perf_counter() - t0) * 1000
            logger.info("[TIMING] SSL/TLS certificate audit: duration=%.2fms status=%s", t_ms, res.status)
            return res

        # Engine C: VirusTotal Threat Intelligence
        async def _eval_vt() -> Optional[VirusTotalReportResponse]:
            t0 = time.perf_counter()
            try:
                res = await self._vt_service.lookup_url(
                    url=canonical_url,
                    scan_id=scan_record.id,
                )
            except Exception as e:
                logger.warning(
                    "VirusTotal lookup deferred or failed for scan %s: %s", scan_record.id, e
                )
                res = None
            t_ms = (time.perf_counter() - t0) * 1000
            vt_status = res.status if res else "UNAVAILABLE"
            logger.info("[TIMING] VirusTotal threat intelligence: duration=%.2fms status=%s", t_ms, vt_status)
            return res

        # Engine D: Domain Reputation Intelligence
        async def _eval_reputation():
            t0 = time.perf_counter()
            current_threats = [
                getattr(i, "name", i.get("name") if isinstance(i, dict) else "")
                for i in preliminary_analysis.indicators
                if getattr(i, "severity", i.get("severity") if isinstance(i, dict) else "") in ("high", "medium")
            ]
            try:
                res = await self._reputation_service.evaluate_domain(
                    canonical_url, current_threat_signals=current_threats
                )
            except Exception as e:
                logger.warning("Domain reputation evaluation failed: %s", e)
                from app.schemas.domain_reputation import DomainReputationResult
                res = DomainReputationResult(
                    domain=urlparse(canonical_url).hostname or "",
                    registered_domain=urlparse(canonical_url).hostname or "",
                    category="NEUTRAL_UNFAMILIAR",
                    reputation_score=50,
                    uncertainty_level="HIGH",
                    reasons=["Reputation evaluation timed out or encountered an error."],
                )
            t_ms = (time.perf_counter() - t0) * 1000
            logger.info("[TIMING] Domain reputation: duration=%.2fms category=%s score=%s", t_ms, res.category, res.reputation_score)
            return res

        # Run independent analysis engines concurrently
        ml_prediction, ssl_analysis, vt_report, domain_reputation = await asyncio.gather(
            _eval_ml(), _eval_ssl(), _eval_vt(), _eval_reputation()
        )

        # 4. Centralized Digital Trust Score & Risk Assessment Synthesis
        t_risk_start = time.perf_counter()
        trust_assessment = self._risk_service.evaluate(
            url=canonical_url,
            url_analysis=preliminary_analysis,
            vt_report=vt_report,
            ml_prediction=ml_prediction,
            ssl_analysis=ssl_analysis,
            domain_reputation=domain_reputation,
        )
        t_risk_ms = (time.perf_counter() - t_risk_start) * 1000
        logger.info(
            "[TIMING] Risk-score calculation: duration=%.2fms trust_score=%s risk_level=%s",
            t_risk_ms,
            trust_assessment.digital_trust_score,
            trust_assessment.risk_level,
        )

        # 5. Database Persistence — Final Findings & Scan Status Completion
        trust_score_val = (
            trust_assessment.digital_trust_score
            if trust_assessment.digital_trust_score is not None
            else 0
        )
        scan_result_in = ScanResultCreate(
            scan_id=scan_record.id,
            trust_score=trust_score_val,
            overall_risk_level=trust_assessment.risk_level,
            # Machine Learning
            phishing_probability=ml_prediction.phishing_probability if ml_prediction else None,
            ml_prediction=ml_prediction.prediction if ml_prediction else None,
            ml_score=ml_prediction.ml_subscore if ml_prediction else None,
            ml_features=preliminary_analysis.features,
            # Threat Intelligence
            virustotal_detection_count=vt_report.statistics.malicious if vt_report else None,
            virustotal_total_engines=vt_report.statistics.total_engines if vt_report else None,
            threat_intelligence_status=vt_report.status if vt_report else None,
            vt_score=vt_report.vt_subscore if vt_report else None,
            vt_raw=vt_report.model_dump() if vt_report else None,
            # SSL/TLS
            ssl_status=ssl_analysis.status if ssl_analysis else None,
            ssl_valid=(ssl_analysis.status in ("VALID", "EXPIRING_SOON")) if ssl_analysis else None,
            ssl_issuer=ssl_analysis.certificate_issuer if ssl_analysis else None,
            ssl_expiry_date=ssl_analysis.valid_until if ssl_analysis else None,
            ssl_days_remaining=ssl_analysis.days_remaining if ssl_analysis else None,
            ssl_score=ssl_analysis.ssl_subscore if ssl_analysis else None,
            ssl_raw=ssl_analysis.model_dump() if ssl_analysis else None,
            # URL Heuristics
            url_score=(
                trust_assessment.module_scores["url_heuristics"].raw_subscore
                if "url_heuristics" in trust_assessment.module_scores
                else None
            ),
            url_risk_indicators=[ind.model_dump() for ind in preliminary_analysis.indicators],
            # Scoring & Breakdown
            score_breakdown=trust_assessment.model_dump(),
            analysis_summary=trust_assessment.summary,
        )

        t_db_final_start = time.perf_counter()

        # Sequentially persist scan_results then mark scan_history complete to ensure HTTP/2 stream safety
        try:
            await self._scan_repo.save_scan_results(scan_result_in)
        except Exception as e:
            logger.warning("Failed to save scan_results for scan %s: %s", scan_record.id, e)

        try:
            await self._scan_repo.update_scan_status(
                scan_id=scan_record.id,
                status_update=ScanStatusUpdate(
                    scan_status="complete",
                    risk_level=trust_assessment.risk_level,
                    trust_score=trust_assessment.digital_trust_score,
                    risk_score=trust_assessment.risk_score,
                    assessment_status=trust_assessment.assessment_status,
                    assessment_coverage=trust_assessment.assessment_coverage,
                    scoring_version=trust_assessment.scoring_version,
                ),
            )
        except Exception as e:
            logger.warning("Failed to update scan_history for scan %s: %s", scan_record.id, e)

        t_db_final_ms = (time.perf_counter() - t_db_final_start) * 1000
        logger.info(
            "[TIMING] Database persistence (results & completion): duration=%.2fms scan_id=%s",
            t_db_final_ms,
            scan_record.id,
        )

        # Non-blocking background task: Retroactively link pre-existing community threat reports
        async def _link_community_reports():
            try:
                from app.services.community_reporting_service import get_community_service
                comm_service = get_community_service()
                if comm_service._repo.client is not None:
                    await asyncio.to_thread(
                        lambda: comm_service._repo.client.table("community_reports").update({
                            "scan_id": str(scan_record.id)
                        }).eq("normalized_url", canonical_url).is_("scan_id", "null").execute()
                    )
            except Exception:
                pass

        asyncio.create_task(_link_community_reports())

        # 6. Response Construction & Delivery
        t_total_ms = (time.perf_counter() - t_pipeline_start) * 1000
        logger.info(
            "[TIMING] Total scan pipeline: duration=%.2fms is_guest=%s user_id=%s scan_id=%s",
            t_total_ms,
            is_guest,
            user_id,
            scan_record.id,
        )

        return URLSubmissionResponse(
            success=True,
            scan_id=scan_record.id,
            original_url=raw_url,
            normalized_url=canonical_url,
            validation_status=validation_status,
            is_guest=is_guest,
            preliminary_analysis=preliminary_analysis,
            ml_prediction=ml_prediction,
            ssl_analysis=ssl_analysis,
            trust_assessment=trust_assessment,
            digital_trust_score=trust_assessment.digital_trust_score,
            risk_level=trust_assessment.risk_level,
            domain_reputation=domain_reputation,
            message="URL accepted and complete multi-layer security analysis conducted.",
            submitted_at=scan_record.created_at,
        )

    async def get_scan_details(
        self,
        scan_id: uuid.UUID,
        requesting_user_id: Optional[uuid.UUID] = None,
    ) -> Tuple[ScanHistoryResponse, Optional[ScanResultResponse]]:
        """
        Retrieves scan status and detailed results with strict ownership enforcement.
        """
        return await self._scan_repo.get_scan_by_id_with_ownership(
            scan_id=scan_id,
            requesting_user_id=requesting_user_id,
        )
