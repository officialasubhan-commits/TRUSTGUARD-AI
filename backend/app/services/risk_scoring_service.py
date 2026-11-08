"""
Digital Trust Score & Intelligent Risk Assessment Engine for TrustGuard AI.

Aggregates findings from all four security modules:
1. URL Static Analysis (15% weight)
2. VirusTotal Threat Intelligence (40% weight)
3. ML Phishing Detection (30% weight)
4. SSL/TLS Certificate Validation (15% weight)

Implements dynamic weight redistribution for missing/rate-limited services,
evaluates assessment coverage, applies critical high-severity override policies,
and generates explainable positive, risk, and unknown indicator breakdowns.

Design Principle:
Zero network activity inside this service; operates deterministically on
collected security telemetry.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas.ml import MLPredictionResponse
from app.schemas.risk_scoring import (
    AssessmentStatusType,
    DigitalTrustAssessment,
    FindingItem,
    ModuleScoreDetail,
    RiskLevelType,
)
from app.schemas.scanner import PreliminaryAnalysis
from app.schemas.ssl import SSLValidationResponse
from app.schemas.virustotal import VirusTotalReportResponse

logger = logging.getLogger("trustguard.service.risk_scoring")


class RiskScoringService:
    """Core evidence-based risk synthesis and Digital Trust Score engine."""

    def evaluate(
        self,
        url: str,
        url_analysis: Optional[PreliminaryAnalysis] = None,
        vt_report: Optional[VirusTotalReportResponse] = None,
        ml_prediction: Optional[MLPredictionResponse] = None,
        ssl_analysis: Optional[SSLValidationResponse] = None,
    ) -> DigitalTrustAssessment:
        """
        Synthesizes telemetry from all active security inspection modules into
        a unified Digital Trust Score, risk classification, and explainable findings.
        """
        module_scores: Dict[str, ModuleScoreDetail] = {}
        risk_indicators: List[FindingItem] = []
        positive_indicators: List[FindingItem] = []
        unknown_indicators: List[FindingItem] = []

        # ------------------------------------------------------------------ #
        # 1. Evaluate VirusTotal Threat Intelligence (Weight: 40%)           #
        # ------------------------------------------------------------------ #
        vt_risk, vt_detail = self._evaluate_virustotal(
            vt_report=vt_report,
            risk_indicators=risk_indicators,
            positive_indicators=positive_indicators,
            unknown_indicators=unknown_indicators,
        )
        module_scores["virustotal"] = vt_detail

        # ------------------------------------------------------------------ #
        # 2. Evaluate ML Phishing Detection (Weight: 30%)                    #
        # ------------------------------------------------------------------ #
        ml_risk, ml_detail = self._evaluate_ml(
            ml_prediction=ml_prediction,
            risk_indicators=risk_indicators,
            positive_indicators=positive_indicators,
            unknown_indicators=unknown_indicators,
        )
        module_scores["ml_phishing"] = ml_detail

        # ------------------------------------------------------------------ #
        # 3. Evaluate URL Static Analysis (Weight: 15%)                      #
        # ------------------------------------------------------------------ #
        url_risk, url_detail = self._evaluate_url_heuristics(
            url_analysis=url_analysis,
            risk_indicators=risk_indicators,
            positive_indicators=positive_indicators,
            unknown_indicators=unknown_indicators,
        )
        module_scores["url_heuristics"] = url_detail

        # ------------------------------------------------------------------ #
        # 4. Evaluate SSL/TLS Certificate Validation (Weight: 15%)           #
        # ------------------------------------------------------------------ #
        ssl_risk, ssl_detail = self._evaluate_ssl(
            ssl_analysis=ssl_analysis,
            risk_indicators=risk_indicators,
            positive_indicators=positive_indicators,
            unknown_indicators=unknown_indicators,
        )
        module_scores["ssl_tls"] = ssl_detail

        # ------------------------------------------------------------------ #
        # 5. Coverage Calculation & Dynamic Weight Redistribution            #
        # ------------------------------------------------------------------ #
        available_weights_sum = 0.0
        weighted_risk_sum = 0.0

        for key, detail in module_scores.items():
            if detail.included_in_calculation and detail.normalized_risk is not None:
                available_weights_sum += detail.weight
                weighted_risk_sum += detail.weight * detail.normalized_risk

        assessment_coverage = round(available_weights_sum, 2)
        coverage_percentage = int(round(assessment_coverage * 100))

        # Baseline weighted average risk (normalized over available weight)
        raw_risk = weighted_risk_sum / available_weights_sum if available_weights_sum > 0 else 50.0

        # ------------------------------------------------------------------ #
        # 6. Apply High-Severity Override Rules                              #
        # ------------------------------------------------------------------ #
        high_severity_override = False
        override_reason: Optional[str] = None

        # Rule A: VirusTotal Confirmed Malicious
        if vt_report and (vt_report.status == "MALICIOUS" or vt_report.statistics.malicious >= 3):
            high_severity_override = True
            override_reason = f"VirusTotal threat intelligence confirmed active malware or phishing ({vt_report.statistics.malicious} engines)."
            raw_risk = max(raw_risk, 85.0)

        # Rule B: Confident ML Phishing Prediction
        elif (
            ml_prediction
            and ml_prediction.prediction == "PHISHING"
            and (ml_prediction.phishing_probability or 0) >= 0.85
        ):
            high_severity_override = True
            override_reason = f"High-confidence machine learning phishing detection ({ml_prediction.phishing_probability:.1%})."
            raw_risk = max(raw_risk, 75.0)

        # Rule C: Blocked SSRF Destination
        elif ssl_analysis and ssl_analysis.status == "UNSAFE_DESTINATION":
            high_severity_override = True
            override_reason = (
                "Target hostname resolves to private, loopback, or cloud metadata network space."
            )
            raw_risk = 100.0

        # Rule D: Deceptive Credential Harvesting Obfuscation
        elif (
            url_analysis
            and any(i.name == "IP_BASED_HOSTNAME" for i in url_analysis.indicators)
            and any(i.name == "AT_SYMBOL_OBFUSCATION" for i in url_analysis.indicators)
        ):
            high_severity_override = True
            override_reason = "Multiple severe deception mechanisms detected (raw IP host combined with userinfo @ sign)."
            raw_risk = max(raw_risk, 80.0)

        # Check for insufficient data (only if no high-severity override was triggered)
        if (
            not high_severity_override
            and assessment_coverage < settings.MIN_COVERAGE_FOR_ASSESSMENT
        ):
            logger.warning(
                "Assessment coverage (%.2f) below minimum required threshold (%.2f) for %s",
                assessment_coverage,
                settings.MIN_COVERAGE_FOR_ASSESSMENT,
                url,
            )
            return DigitalTrustAssessment(
                digital_trust_score=None,
                risk_score=None,
                risk_level="UNKNOWN",
                risk_label="INSUFFICIENT DATA",
                assessment_status="INSUFFICIENT_DATA",
                assessment_coverage=assessment_coverage,
                coverage_percentage=coverage_percentage,
                scoring_version=settings.SCORING_VERSION,
                high_severity_override=False,
                override_reason=None,
                module_scores=module_scores,
                risk_indicators=risk_indicators,
                positive_indicators=positive_indicators,
                unknown_indicators=unknown_indicators,
                summary=(
                    "Insufficient security evidence to formulate an accurate Digital Trust Score. "
                    "Multiple critical security evaluation feeds were unavailable."
                ),
                recommendations=[
                    "Exercise extreme caution; the system could not obtain sufficient threat intelligence.",
                    "Verify the domain name manually before interacting or submitting credentials.",
                ],
            )

        # ------------------------------------------------------------------ #
        # 7. Final Trust Score & Risk Level Mapping                          #
        # ------------------------------------------------------------------ #
        final_risk = int(round(min(100.0, max(0.0, raw_risk))))
        digital_trust_score = 100 - final_risk

        # Uncertainty Calibration: Cap maximum achievable trust if major telemetry is missing
        vt_detail = module_scores.get("virustotal")
        ml_detail = module_scores.get("ml_phishing")
        vt_available = vt_detail and vt_detail.included_in_calculation
        ml_available = ml_detail and ml_detail.included_in_calculation

        if not vt_available and digital_trust_score > 70:
            logger.info("Capping trust score from %s to 70 due to absent VirusTotal intelligence.", digital_trust_score)
            digital_trust_score = 70
            final_risk = 30
        elif not ml_available and digital_trust_score > 75:
            logger.info("Capping trust score from %s to 75 due to absent ML phishing inference.", digital_trust_score)
            digital_trust_score = 75
            final_risk = 25

        if digital_trust_score >= settings.TRUST_SCORE_LOW_RISK_MIN:
            risk_level: RiskLevelType = "LOW"
            risk_label = "LOW RISK"
        elif digital_trust_score >= settings.TRUST_SCORE_MODERATE_RISK_MIN:
            risk_level = "MEDIUM"
            risk_label = "MODERATE RISK"
        elif digital_trust_score >= settings.TRUST_SCORE_HIGH_RISK_MIN:
            risk_level = "HIGH"
            risk_label = "HIGH RISK"
        else:
            risk_level = "CRITICAL"
            risk_label = "CRITICAL RISK"

        assessment_status: AssessmentStatusType = (
            "COMPLETE" if assessment_coverage >= 1.0 else "PARTIAL"
        )

        # ------------------------------------------------------------------ #
        # 8. Generate Summary Narrative & Recommendations                    #
        # ------------------------------------------------------------------ #
        summary = self._generate_summary(
            digital_trust_score=digital_trust_score,
            risk_label=risk_label,
            coverage_percentage=coverage_percentage,
            high_severity_override=high_severity_override,
            override_reason=override_reason,
            risk_count=len(risk_indicators),
            positive_count=len(positive_indicators),
        )

        recommendations = self._generate_recommendations(
            risk_level=risk_level,
            url_analysis=url_analysis,
            vt_report=vt_report,
            ml_prediction=ml_prediction,
            ssl_analysis=ssl_analysis,
        )

        return DigitalTrustAssessment(
            digital_trust_score=digital_trust_score,
            risk_score=final_risk,
            risk_level=risk_level,
            risk_label=risk_label,
            assessment_status=assessment_status,
            assessment_coverage=assessment_coverage,
            coverage_percentage=coverage_percentage,
            scoring_version=settings.SCORING_VERSION,
            high_severity_override=high_severity_override,
            override_reason=override_reason,
            module_scores=module_scores,
            risk_indicators=risk_indicators,
            positive_indicators=positive_indicators,
            unknown_indicators=unknown_indicators,
            summary=summary,
            recommendations=recommendations,
        )

    # ---------------------------------------------------------------------- #
    # Helper Module Evaluators                                                #
    # ---------------------------------------------------------------------- #

    def _evaluate_virustotal(
        self,
        vt_report: Optional[VirusTotalReportResponse],
        risk_indicators: List[FindingItem],
        positive_indicators: List[FindingItem],
        unknown_indicators: List[FindingItem],
    ) -> Tuple[Optional[float], ModuleScoreDetail]:
        weight = settings.WEIGHT_VIRUSTOTAL

        if not vt_report or vt_report.status in (
            "API_UNAVAILABLE",
            "RATE_LIMITED",
            "ERROR",
            "NOT_FOUND",
            "PENDING",
        ):
            status_desc = vt_report.status if vt_report else "UNAVAILABLE"
            unknown_indicators.append(
                FindingItem(
                    title="VirusTotal Threat Intelligence Inconclusive",
                    description=f"External security vendor feed returned status: {status_desc}.",
                    source_module="virustotal",
                    severity="info",
                    evidence=vt_report.message if vt_report else "Feed not queried",
                    affects_score=False,
                    explanation=(
                        "External threat vendor telemetry could not be retrieved. "
                        "The evaluation proceeded without this feed; absence of threat data is not evidence of safety."
                    ),
                )
            )
            return None, ModuleScoreDetail(
                module_name="virustotal",
                status=status_desc,
                weight=weight,
                raw_subscore=None,
                normalized_risk=None,
                included_in_calculation=False,
                reason_if_excluded=f"Feed status '{status_desc}' is inconclusive.",
            )

        # Active report
        raw_subscore = vt_report.vt_subscore
        malicious = vt_report.statistics.malicious
        suspicious = vt_report.statistics.suspicious
        total = vt_report.statistics.total_engines

        if total == 0:
            unknown_indicators.append(
                FindingItem(
                    title="VirusTotal Telemetry Inconclusive",
                    description="No participating security vendors have evaluated this URL yet.",
                    source_module="virustotal",
                    severity="info",
                    evidence="0 engines evaluated",
                    affects_score=False,
                    explanation="The URL is unindexed or newly discovered in the vendor ecosystem.",
                )
            )
            return None, ModuleScoreDetail(
                module_name="virustotal",
                status="INCONCLUSIVE",
                weight=weight,
                raw_subscore=None,
                normalized_risk=None,
                included_in_calculation=False,
                reason_if_excluded="No security engines have evaluated this URL.",
            )

        if vt_report.status == "MALICIOUS" or malicious >= 3:
            normalized_risk = 100.0
            risk_indicators.append(
                FindingItem(
                    title="Confirmed Malicious Security Detections",
                    description=f"{malicious} of {total} independent security vendors flagged this URL as malicious.",
                    source_module="virustotal",
                    severity="critical",
                    evidence=f"{malicious}/{total} engines; flagged: {', '.join(vt_report.classification.flagged_vendors[:3])}",
                    affects_score=True,
                    explanation="Multiple reputable antivirus and cybersecurity vendors confirmed active threats on this URL.",
                )
            )
        elif vt_report.status == "SUSPICIOUS" or malicious >= 1 or suspicious >= 2:
            normalized_risk = min(100.0, 50.0 + (malicious * 20.0) + (suspicious * 10.0))
            risk_indicators.append(
                FindingItem(
                    title="Suspicious Threat Intelligence Verdict",
                    description=f"{malicious} vendor(s) flagged malicious and {suspicious} flagged suspicious out of {total} engines.",
                    source_module="virustotal",
                    severity="high",
                    evidence=f"{malicious} malicious, {suspicious} suspicious out of {total}",
                    affects_score=True,
                    explanation="Security engines detect anomalous patterns or low-consensus threat activity associated with this URL.",
                )
            )
        else:
            # Calibrated baseline residual risk: 0 detections across engines does NOT guarantee 0% threat
            normalized_risk = 10.0
            positive_indicators.append(
                FindingItem(
                    title="Zero Security Vendor Detections",
                    description=f"0 out of {total} security engines currently flag this URL.",
                    source_module="virustotal",
                    severity="info",
                    evidence=f"0/{total} detections",
                    affects_score=True,
                    explanation=(
                        f"None of the {total} participating antivirus engines currently list this URL. "
                        "Baseline unindexed risk is retained because zero-day campaigns may temporarily evade signatures."
                    ),
                )
            )

        return normalized_risk, ModuleScoreDetail(
            module_name="virustotal",
            status="AVAILABLE",
            weight=weight,
            raw_subscore=raw_subscore,
            normalized_risk=normalized_risk,
            included_in_calculation=True,
        )

    def _evaluate_ml(
        self,
        ml_prediction: Optional[MLPredictionResponse],
        risk_indicators: List[FindingItem],
        positive_indicators: List[FindingItem],
        unknown_indicators: List[FindingItem],
    ) -> Tuple[Optional[float], ModuleScoreDetail]:
        weight = settings.WEIGHT_ML_PHISHING

        if (
            not ml_prediction
            or ml_prediction.model_status != "ACTIVE"
            or ml_prediction.prediction in ("MODEL_UNAVAILABLE", "UNKNOWN")
            or ml_prediction.phishing_probability is None
        ):
            status_desc = ml_prediction.model_status if ml_prediction else "UNAVAILABLE"
            unknown_indicators.append(
                FindingItem(
                    title="Machine Learning Classifier Unavailable",
                    description="Offline AI phishing classification model was not available during this scan.",
                    source_module="ml_phishing",
                    severity="info",
                    evidence=status_desc,
                    affects_score=False,
                    explanation="The ML inference service did not participate in this assessment; risk was calculated from other signals.",
                )
            )
            return None, ModuleScoreDetail(
                module_name="ml_phishing",
                status=status_desc,
                weight=weight,
                raw_subscore=None,
                normalized_risk=None,
                included_in_calculation=False,
                reason_if_excluded=f"Model status is '{status_desc}'.",
            )

        proba = ml_prediction.phishing_probability
        normalized_risk = round(proba * 100.0, 1)
        raw_subscore = ml_prediction.ml_subscore

        if proba >= settings.ML_THRESHOLD_PHISHING:
            risk_indicators.append(
                FindingItem(
                    title="Machine Learning Phishing Alert",
                    description=f"Model classified URL as PHISHING with {proba:.1%} estimated probability.",
                    source_module="ml_phishing",
                    severity="high" if proba >= 0.85 else "medium",
                    evidence=f"Probability: {proba:.4f}",
                    affects_score=True,
                    explanation="The machine learning model identified structural and lexical patterns strongly characteristic of phishing websites.",
                )
            )
        elif proba >= settings.ML_THRESHOLD_LEGITIMATE:
            risk_indicators.append(
                FindingItem(
                    title="Machine Learning Suspicious Patterns",
                    description=f"Model identified borderline structural anomalies ({proba:.1%} probability).",
                    source_module="ml_phishing",
                    severity="medium",
                    evidence=f"Probability: {proba:.4f}",
                    affects_score=True,
                    explanation="URL structural characteristics deviate moderately from standard legitimate domain benchmarks.",
                )
            )
        else:
            positive_indicators.append(
                FindingItem(
                    title="Machine Learning Legitimate Profile",
                    description=f"Model evaluated low phishing probability ({proba:.1%}).",
                    source_module="ml_phishing",
                    severity="info",
                    evidence=f"Probability: {proba:.4f}",
                    affects_score=True,
                    explanation="URL structure, length, and token distributions align closely with legitimate domain distributions.",
                )
            )

        return normalized_risk, ModuleScoreDetail(
            module_name="ml_phishing",
            status="AVAILABLE",
            weight=weight,
            raw_subscore=raw_subscore,
            normalized_risk=normalized_risk,
            included_in_calculation=True,
        )

    def _evaluate_url_heuristics(
        self,
        url_analysis: Optional[PreliminaryAnalysis],
        risk_indicators: List[FindingItem],
        positive_indicators: List[FindingItem],
        unknown_indicators: List[FindingItem],
    ) -> Tuple[Optional[float], ModuleScoreDetail]:
        weight = settings.WEIGHT_URL_HEURISTICS

        if not url_analysis:
            unknown_indicators.append(
                FindingItem(
                    title="URL Static Analysis Missing",
                    description="Preliminary lexical feature extraction data was not provided.",
                    source_module="url_heuristics",
                    severity="info",
                    evidence=None,
                    affects_score=False,
                    explanation="Static heuristic indicators were not evaluated.",
                )
            )
            return None, ModuleScoreDetail(
                module_name="url_heuristics",
                status="UNAVAILABLE",
                weight=weight,
                raw_subscore=None,
                normalized_risk=None,
                included_in_calculation=False,
                reason_if_excluded="No preliminary analysis data.",
            )

        high_flags = [i for i in url_analysis.indicators if i.severity in ("high", "critical")]
        med_flags = [i for i in url_analysis.indicators if i.severity == "medium"]
        low_flags = [i for i in url_analysis.indicators if i.severity == "low"]

        if high_flags:
            normalized_risk = min(100.0, 50.0 + (len(high_flags) * 25.0) + (len(med_flags) * 10.0))
        elif med_flags:
            normalized_risk = min(65.0, 30.0 + (len(med_flags) * 15.0))
        elif low_flags:
            normalized_risk = min(20.0, len(low_flags) * 5.0)
        else:
            normalized_risk = 0.0

        raw_subscore = int(round(100.0 - normalized_risk))

        for ind in url_analysis.indicators:
            risk_indicators.append(
                FindingItem(
                    title=ind.name.replace("_", " ").title(),
                    description=ind.description,
                    source_module="url_heuristics",
                    severity=ind.severity,
                    evidence=ind.evidence,
                    affects_score=True,
                    explanation=ind.reason,
                )
            )

        if not url_analysis.indicators:
            positive_indicators.append(
                FindingItem(
                    title="Clean Lexical URL Structure",
                    description="No suspicious patterns, obfuscation tricks, or abnormal lengths detected.",
                    source_module="url_heuristics",
                    severity="info",
                    evidence="0 heuristic flags",
                    affects_score=True,
                    explanation="URL adheres to standard formatting conventions without deceptive authority tricks.",
                )
            )

        return normalized_risk, ModuleScoreDetail(
            module_name="url_heuristics",
            status="AVAILABLE",
            weight=weight,
            raw_subscore=raw_subscore,
            normalized_risk=normalized_risk,
            included_in_calculation=True,
        )

    def _evaluate_ssl(
        self,
        ssl_analysis: Optional[SSLValidationResponse],
        risk_indicators: List[FindingItem],
        positive_indicators: List[FindingItem],
        unknown_indicators: List[FindingItem],
    ) -> Tuple[Optional[float], ModuleScoreDetail]:
        weight = settings.WEIGHT_SSL_TLS

        if not ssl_analysis or ssl_analysis.status in (
            "TIMEOUT",
            "CONNECTION_ERROR",
            "DNS_RESOLUTION_FAILED",
            "UNKNOWN",
        ):
            status_desc = ssl_analysis.status if ssl_analysis else "UNAVAILABLE"
            unknown_indicators.append(
                FindingItem(
                    title="SSL/TLS Certificate Check Inconclusive",
                    description=f"Transport security check returned status: {status_desc}.",
                    source_module="ssl_tls",
                    severity="info",
                    evidence=ssl_analysis.message if ssl_analysis else "Not queried",
                    affects_score=False,
                    explanation=(
                        "Could not verify SSL/TLS certificate due to network timeout or connection refusal. "
                        "This does not necessarily mean the site is malicious, but security could not be verified."
                    ),
                )
            )
            return None, ModuleScoreDetail(
                module_name="ssl_tls",
                status=status_desc,
                weight=weight,
                raw_subscore=None,
                normalized_risk=None,
                included_in_calculation=False,
                reason_if_excluded=f"Connection status '{status_desc}' is inconclusive.",
            )

        raw_subscore = ssl_analysis.ssl_subscore

        if ssl_analysis.status == "VALID":
            normalized_risk = 5.0  # Encryption active, but does not guarantee business legitimacy
            positive_indicators.append(
                FindingItem(
                    title="Valid SSL/TLS Encryption Certificate",
                    description=f"Trusted certificate issued by {ssl_analysis.certificate_issuer or 'recognized CA'}.",
                    source_module="ssl_tls",
                    severity="info",
                    evidence=f"Valid until {ssl_analysis.valid_until.strftime('%Y-%m-%d') if ssl_analysis.valid_until else 'N/A'}",
                    affects_score=True,
                    explanation="Browser connection is encrypted with a publicly trusted certificate. Note: transport encryption alone does not prove site legitimacy.",
                )
            )
        elif ssl_analysis.status == "EXPIRING_SOON":
            normalized_risk = 25.0
            risk_indicators.append(
                FindingItem(
                    title="SSL Certificate Approaching Expiry",
                    description=f"Certificate expires in {ssl_analysis.days_remaining} days.",
                    source_module="ssl_tls",
                    severity="medium",
                    evidence=f"{ssl_analysis.days_remaining} days remaining",
                    affects_score=True,
                    explanation="The site's certificate will expire soon and will trigger browser security warnings if not renewed.",
                )
            )
        elif ssl_analysis.status == "HTTPS_NOT_USED":
            normalized_risk = 50.0
            risk_indicators.append(
                FindingItem(
                    title="Plain Unencrypted HTTP Protocol",
                    description="The site uses plain HTTP rather than encrypted HTTPS.",
                    source_module="ssl_tls",
                    severity="medium",
                    evidence="http://",
                    affects_score=True,
                    explanation="User credentials and traffic sent to this site can be intercepted by intermediate network eavesdroppers.",
                )
            )
        elif ssl_analysis.status == "UNSAFE_DESTINATION":
            normalized_risk = 100.0
            risk_indicators.append(
                FindingItem(
                    title="Restricted Internal Destination Blocked",
                    description="Hostname resolved to private, loopback, or cloud metadata address space.",
                    source_module="ssl_tls",
                    severity="critical",
                    evidence="SSRF Guard Triggered",
                    affects_score=True,
                    explanation="Target attempts to reference private network resources; blocked to prevent server-side exploitation.",
                )
            )
        elif ssl_analysis.status in ("EXPIRED", "HOSTNAME_MISMATCH"):
            normalized_risk = 85.0
            risk_indicators.append(
                FindingItem(
                    title=f"SSL Certificate Failure ({ssl_analysis.status})",
                    description=ssl_analysis.message,
                    source_module="ssl_tls",
                    severity="high",
                    evidence=ssl_analysis.error_code or ssl_analysis.status,
                    affects_score=True,
                    explanation="Browsers will block access with security warning screens. Common in abandoned or deceptive domains.",
                )
            )
        elif ssl_analysis.status == "UNTRUSTED_CERTIFICATE":
            normalized_risk = 75.0
            risk_indicators.append(
                FindingItem(
                    title="Untrusted Certificate Authority Root",
                    description="Certificate is self-signed or not signed by a recognized Certificate Authority.",
                    source_module="ssl_tls",
                    severity="high",
                    evidence=ssl_analysis.error_code or "UNTRUSTED_ROOT",
                    affects_score=True,
                    explanation="Certificate identity cannot be verified against the global public trust anchor.",
                )
            )
        else:
            normalized_risk = 65.0
            risk_indicators.append(
                FindingItem(
                    title="TLS Handshake Failed",
                    description=ssl_analysis.message,
                    source_module="ssl_tls",
                    severity="medium",
                    evidence=ssl_analysis.status,
                    affects_score=True,
                    explanation="Could not complete a secure cryptographic handshake with the destination host.",
                )
            )

        return normalized_risk, ModuleScoreDetail(
            module_name="ssl_tls",
            status="AVAILABLE",
            weight=weight,
            raw_subscore=raw_subscore,
            normalized_risk=normalized_risk,
            included_in_calculation=True,
        )

    # ---------------------------------------------------------------------- #
    # Narrative & Recommendation Generators                                  #
    # ---------------------------------------------------------------------- #

    def _generate_summary(
        self,
        digital_trust_score: int,
        risk_label: str,
        coverage_percentage: int,
        high_severity_override: bool,
        override_reason: Optional[str],
        risk_count: int,
        positive_count: int,
    ) -> str:
        override_note = (
            f" (Critical override applied: {override_reason})" if high_severity_override else ""
        )
        return (
            f"TrustGuard AI assigned this website a Digital Trust Score of {digital_trust_score}/100 "
            f"({risk_label}){override_note}. The evaluation achieved {coverage_percentage}% assessment coverage, "
            f"identifying {risk_count} security risk indicator(s) and {positive_count} positive security signal(s)."
        )

    def _generate_recommendations(
        self,
        risk_level: RiskLevelType,
        url_analysis: Optional[PreliminaryAnalysis],
        vt_report: Optional[VirusTotalReportResponse],
        ml_prediction: Optional[MLPredictionResponse],
        ssl_analysis: Optional[SSLValidationResponse],
    ) -> List[str]:
        recommendations: List[str] = []

        if risk_level in ("CRITICAL", "HIGH"):
            recommendations.append(
                "Do NOT submit login credentials, passwords, credit card numbers, or personal identity details on this website."
            )
            recommendations.append(
                "Close the browser tab and verify whether the intended organization uses an alternative official domain."
            )

        if vt_report and vt_report.status == "MALICIOUS":
            recommendations.append(
                "Security engines have actively blacklisted this URL; avoid navigating to or downloading files from this domain."
            )

        if ml_prediction and ml_prediction.prediction == "PHISHING":
            recommendations.append(
                "This URL displays lexical characteristics typical of social engineering clones; double-check the exact address bar spelling."
            )

        if ssl_analysis and ssl_analysis.status == "HTTPS_NOT_USED":
            recommendations.append(
                "Avoid entering sensitive information because this website transmits data over unencrypted HTTP."
            )

        if ssl_analysis and ssl_analysis.status in (
            "EXPIRED",
            "HOSTNAME_MISMATCH",
            "UNTRUSTED_CERTIFICATE",
        ):
            recommendations.append(
                "Do not ignore or bypass browser SSL certificate warning screens."
            )

        if not recommendations and risk_level == "LOW":
            recommendations.append(
                "Standard automated technical checks passed without major flags."
            )
            recommendations.append(
                "Always remain alert for spear-phishing and ensure the website identity matches your expected destination."
            )

        return recommendations[:4]


# Global singleton instance
_risk_scoring_service_instance: Optional[RiskScoringService] = None


def get_risk_scoring_service() -> RiskScoringService:
    """Returns the cached singleton instance of RiskScoringService."""
    global _risk_scoring_service_instance
    if _risk_scoring_service_instance is None:
        _risk_scoring_service_instance = RiskScoringService()
    return _risk_scoring_service_instance
