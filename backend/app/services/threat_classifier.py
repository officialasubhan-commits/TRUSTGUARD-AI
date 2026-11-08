"""
Threat Classifier for VirusTotal Vendor Telemetry.

Interprets raw security vendor counts and verdicts into transparent,
human-readable threat classifications with detection ratios and confidence ratings.

Design Principle:
Absence of detections (NO_DETECTIONS) != SAFE.
Threat intelligence feeds lag behind zero-day phishing infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.virustotal import (
    VirusTotalThreatClassification,
    VirusTotalVendorStats,
    VTStatusType,
)

logger = logging.getLogger("trustguard.service.threat_classifier")

# Reputable, high-weight security vendors often associated with active feeds
PRIORITY_VENDORS = {
    "google safebrowsing",
    "kaspersky",
    "sophos",
    "microsoft",
    "bitdefender",
    "eset",
    "fortinet",
    "crdf",
    "avira",
}


class ThreatClassifier:
    """Classifies multi-engine threat vendor results into human-comprehensible verdicts."""

    @classmethod
    def classify(
        cls,
        stats: VirusTotalVendorStats,
        engine_results: Optional[Dict[str, Any]] = None,
        status_override: Optional[VTStatusType] = None,
        override_message: Optional[str] = None,
    ) -> Tuple[VirusTotalThreatClassification, int]:
        """
        Evaluates vendor statistics and individual engine verdicts.

        Returns:
            Tuple of (VirusTotalThreatClassification, subscore_0_to_100)
        """
        engine_results = engine_results or {}

        # 1. Handle overrides (e.g. rate limit, api error, pending, not found)
        if status_override:
            return cls._handle_override(status_override, stats, override_message)

        # 2. Extract flagged vendors and unique threat categories
        flagged_vendors: List[str] = []
        threat_categories_set = set()
        has_priority_flag = False

        for vendor_name, result_data in engine_results.items():
            if not isinstance(result_data, dict):
                continue

            category = result_data.get("category", "").lower()
            verdict = result_data.get("result", "")

            if category in ("malicious", "suspicious"):
                flagged_vendors.append(vendor_name)
                if vendor_name.lower() in PRIORITY_VENDORS:
                    has_priority_flag = True

                if verdict:
                    threat_categories_set.add(verdict.lower())
                else:
                    threat_categories_set.add(category)

        # If stats indicate malicious/suspicious but engine_results dict was empty
        if not threat_categories_set and stats.malicious > 0:
            threat_categories_set.add("malicious")
        if not threat_categories_set and stats.suspicious > 0:
            threat_categories_set.add("suspicious")

        sorted_categories = sorted(list(threat_categories_set))
        sorted_vendors = sorted(flagged_vendors)

        detection_ratio = (
            f"{stats.malicious}/{stats.total_engines}" if stats.total_engines > 0 else "0/0"
        )

        # 3. Decision Logic for Threat Status & Confidence
        if stats.total_engines == 0:
            status: VTStatusType = "NOT_FOUND"
            confidence = "INSUFFICIENT"
            summary = "URL has not been previously analyzed by any VirusTotal security engines."
            subscore = 100

        elif stats.malicious >= 3 or (stats.malicious >= 1 and has_priority_flag):
            status = "MALICIOUS"
            confidence = "HIGH" if (stats.malicious >= 5 or has_priority_flag) else "MEDIUM"
            summary = (
                f"High-confidence threat: {stats.malicious} of {stats.total_engines} independent "
                f"security vendors classified this URL as active malicious or phishing."
            )
            # Severe score penalty
            subscore = max(0, 100 - (stats.malicious * 20 + stats.suspicious * 5 + 30))

        elif stats.malicious >= 1 or stats.suspicious >= 2:
            status = "SUSPICIOUS"
            confidence = "MEDIUM"
            summary = (
                f"Potential security risk: {stats.malicious} vendor(s) flagged as malicious and "
                f"{stats.suspicious} vendor(s) flagged as suspicious out of {stats.total_engines} engines."
            )
            subscore = max(20, 100 - (stats.malicious * 25 + stats.suspicious * 10))

        else:
            # 0 malicious and at most 1 suspicious
            status = "NO_DETECTIONS"
            confidence = "HIGH" if stats.total_engines >= 50 else "MEDIUM"
            summary = (
                f"Zero security vendors ({stats.malicious}/{stats.total_engines}) flagged this URL. "
                f"Note that newly registered attack sites may temporarily evade vendor signatures."
            )
            subscore = 100

        classification = VirusTotalThreatClassification(
            status=status,
            detection_ratio=detection_ratio,
            confidence=confidence,  # type: ignore[arg-type]
            threat_categories=sorted_categories,
            flagged_vendors=sorted_vendors[:15],
            summary=summary,
            safety_disclaimer=(
                "Notice: Absence of detections (NO_DETECTIONS) does not guarantee that a website is safe. "
                "Zero-day threats and new phishing domains may not yet be listed in vendor databases."
            ),
        )

        return classification, subscore

    @classmethod
    def _handle_override(
        cls,
        status: VTStatusType,
        stats: VirusTotalVendorStats,
        message: Optional[str] = None,
    ) -> Tuple[VirusTotalThreatClassification, int]:
        """Produces classification for exceptional or non-standard status codes."""
        detection_ratio = (
            f"{stats.malicious}/{stats.total_engines}" if stats.total_engines > 0 else "0/0"
        )

        if status == "RATE_LIMITED":
            summary = (
                message
                or "VirusTotal free tier API request quota exceeded (4 requests/minute). "
                "Threat intelligence lookup is temporarily deferred."
            )
            confidence = "INSUFFICIENT"
            subscore = 100
        elif status == "API_UNAVAILABLE":
            summary = (
                message
                or "VirusTotal API service is unavailable or credentials are not configured. "
                "Analysis performed without external vendor reputation."
            )
            confidence = "INSUFFICIENT"
            subscore = 100
        elif status == "NOT_FOUND":
            summary = (
                message
                or "URL not found in VirusTotal threat repository. The URL has been queued for indexing."
            )
            confidence = "INSUFFICIENT"
            subscore = 100
        elif status == "PENDING":
            summary = (
                message
                or "VirusTotal analysis scan is currently queued or in progress with external security engines."
            )
            confidence = "INSUFFICIENT"
            subscore = 100
        else:
            summary = (
                message or f"VirusTotal threat intelligence query encountered status '{status}'."
            )
            confidence = "INSUFFICIENT"
            subscore = 100

        classification = VirusTotalThreatClassification(
            status=status,
            detection_ratio=detection_ratio,
            confidence=confidence,
            threat_categories=[],
            flagged_vendors=[],
            summary=summary,
            safety_disclaimer=(
                "Notice: Threat intelligence is currently incomplete or unavailable for this URL."
            ),
        )
        return classification, subscore
