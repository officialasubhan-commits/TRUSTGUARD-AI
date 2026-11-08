"""
Domain Reputation Intelligence Engine for TrustGuard AI.

Provides multi-signal domain reputation analysis:
1. Authoritative Verified Top Entities (Google, Microsoft, Wikipedia, etc.)
2. Effective Registered Domain (eTLD+1) extraction
3. Protected Brand Lookalike & Impersonation Detection
4. Safe DNS Resolution & SSRF / Rebinding Defenses
5. Historical Scan Telemetry & Behavior Stability Tracking
6. Calibrated Uncertainty Modeling (unfamiliar != malicious)
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.core.trusted_domains import (
    ELEVATED_ABUSE_TLDS,
    VERIFIED_ENTITIES,
    check_brand_impersonation,
    extract_registered_domain,
)
from app.database.repositories.scan_repo import ScanRepository
from app.schemas.domain_reputation import (
    DNSIntelligence,
    DomainReputationCategory,
    DomainReputationResult,
    HistoricalScanTrend,
)

logger = logging.getLogger("trustguard.service.domain_reputation")


class DomainReputationService:
    """Evidence-based Domain Reputation Intelligence Engine."""

    def __init__(self, scan_repo: Optional[ScanRepository] = None):
        self._scan_repo = scan_repo or ScanRepository()

    async def evaluate_domain(
        self,
        domain_or_url: str,
        current_threat_signals: Optional[List[str]] = None,
    ) -> DomainReputationResult:
        """
        Synthesizes multiple independent reputation signals for a domain or URL.
        """
        # Parse hostname
        if "://" in domain_or_url:
            parsed = urlparse(domain_or_url)
            hostname = (parsed.hostname or "").lower().strip()
        else:
            hostname = domain_or_url.split("/")[0].split(":")[0].lower().strip()

        registered_domain = extract_registered_domain(hostname)
        tld = registered_domain.split(".")[-1] if "." in registered_domain else ""

        reasons: List[str] = []
        is_lookalike = False
        impersonated_brand: Optional[str] = None
        verified_identity: Optional[str] = None
        is_established_authority = False

        # ------------------------------------------------------------------ #
        # Signal 1: Verified Top Entity Check                               #
        # ------------------------------------------------------------------ #
        if registered_domain in VERIFIED_ENTITIES:
            entity_info = VERIFIED_ENTITIES[registered_domain]
            verified_identity = entity_info["entity"]
            is_established_authority = True
            reasons.append(
                f"Domain is verified as authentic infrastructure belonging to {verified_identity} ({entity_info['category']})."
            )

        # ------------------------------------------------------------------ #
        # Signal 2: Impersonation & Lookalike Detection                     #
        # ------------------------------------------------------------------ #
        is_impersonation, target_brand, imp_reason = check_brand_impersonation(hostname, registered_domain)
        if is_impersonation:
            is_lookalike = True
            impersonated_brand = target_brand
            reasons.append(imp_reason)

        # ------------------------------------------------------------------ #
        # Signal 3: DNS & Technical Infrastructure Resolution (SSRF Defenses)#
        # ------------------------------------------------------------------ #
        dns_intel = await self._resolve_dns_safely(hostname)
        if dns_intel.is_private_or_loopback:
            reasons.append("Security Violation: Host resolves to a private, loopback, or cloud-metadata IP address (SSRF boundary).")
        elif not dns_intel.resolves:
            reasons.append("DNS Resolution Notice: Host could not be resolved to an active public IP address.")

        # ------------------------------------------------------------------ #
        # Signal 4: TLD Abuse Risk Categorization                           #
        # ------------------------------------------------------------------ #
        has_elevated_abuse_tld = tld in ELEVATED_ABUSE_TLDS
        if has_elevated_abuse_tld:
            reasons.append(f"Top-level domain (.{tld}) has elevated industry abuse rates.")

        # ------------------------------------------------------------------ #
        # Signal 5: Historical Scan Telemetry & Drift Detection             #
        # ------------------------------------------------------------------ #
        historical_trend = await self._analyze_history(registered_domain, current_threat_signals)
        if historical_trend.change_alert:
            reasons.append(historical_trend.change_alert)

        # ------------------------------------------------------------------ #
        # Signal 6: Calibrated Score & Category Synthesis                    #
        # ------------------------------------------------------------------ #
        category, score, uncertainty = self._synthesize_reputation(
            is_established=is_established_authority,
            is_lookalike=is_lookalike,
            is_ssrf=dns_intel.is_private_or_loopback,
            resolves=dns_intel.resolves,
            has_elevated_abuse_tld=has_elevated_abuse_tld,
            historical_trend=historical_trend,
            has_active_threat_signals=bool(current_threat_signals and len(current_threat_signals) > 0),
        )

        return DomainReputationResult(
            domain=hostname,
            registered_domain=registered_domain,
            category=category,
            reputation_score=score,
            verified_identity=verified_identity,
            is_established_authority=is_established_authority,
            is_lookalike_or_impersonation=is_lookalike,
            impersonated_brand=impersonated_brand,
            dns_intelligence=dns_intel,
            historical_trend=historical_trend,
            reasons=reasons,
            uncertainty_level=uncertainty,
        )

    async def _resolve_dns_safely(self, hostname: str) -> DNSIntelligence:
        """Resolves DNS in threadpool with strict SSRF and private-network checks."""
        # Handle raw IP addresses
        try:
            ip_obj = ipaddress.ip_address(hostname)
            is_private = ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
            return DNSIntelligence(
                resolves=True,
                ip_addresses=[str(ip_obj)],
                is_private_or_loopback=is_private,
            )
        except ValueError:
            pass

        loop = asyncio.get_running_loop()
        try:
            # Safe async DNS resolution
            addr_info = await asyncio.wait_for(
                loop.run_in_executor(None, socket.getaddrinfo, hostname, None),
                timeout=2.5,
            )
            ips = list({res[4][0] for res in addr_info if res and len(res) >= 5})
            is_private = False
            for ip_str in ips:
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                        is_private = True
                        break
                except ValueError:
                    continue

            return DNSIntelligence(
                resolves=len(ips) > 0,
                ip_addresses=ips[:4],
                is_private_or_loopback=is_private,
            )
        except Exception:
            return DNSIntelligence(
                resolves=False,
                ip_addresses=[],
                is_private_or_loopback=False,
            )

    async def _analyze_history(
        self,
        registered_domain: str,
        current_threat_signals: Optional[List[str]] = None,
    ) -> HistoricalScanTrend:
        """Queries historical scan records to evaluate domain behavior stability."""
        try:
            records = await self._scan_repo.get_scans_by_domain(registered_domain, limit=20)
            if not records:
                return HistoricalScanTrend(
                    total_scans=0,
                    reputation_stability="NEW_UNOBSERVED",
                )

            total = len(records)
            scores = [r.trust_score for r in records if r.trust_score is not None]
            avg_score = round(sum(scores) / len(scores), 1) if scores else None
            threat_count = sum(1 for r in records if r.risk_level in ("HIGH", "CRITICAL"))

            timestamps = [r.created_at for r in records if r.created_at]
            first_seen = min(timestamps) if timestamps else None
            last_seen = max(timestamps) if timestamps else None

            # Change detection: check if previously clean but currently alerting
            change_alert: Optional[str] = None
            if threat_count > 0:
                stability = "HISTORICALLY_MALICIOUS" if threat_count >= (total // 2) else "VOLATILE"
            elif total >= 3 and avg_score and avg_score >= 80:
                stability = "STABLE_CLEAN"
            else:
                stability = "NEW_UNOBSERVED"

            # Alert if domain was historically clean, but new scan triggered threat signals
            if stability == "STABLE_CLEAN" and current_threat_signals and len(current_threat_signals) > 0:
                stability = "DETERIORATING"
                change_alert = (
                    "Behavioral Shift Detected: Domain has a previously clean scan history, "
                    "but current scan displays active phishing indicators. Investigating potential account takeover or new malicious campaign."
                )

            return HistoricalScanTrend(
                total_scans=total,
                first_seen=first_seen,
                last_seen=last_seen,
                average_trust_score=avg_score,
                past_threat_detections=threat_count,
                reputation_stability=stability,
                change_alert=change_alert,
            )
        except Exception as e:
            logger.debug("Could not retrieve domain scan history: %s", e)
            return HistoricalScanTrend(total_scans=0, reputation_stability="NEW_UNOBSERVED")

    def _synthesize_reputation(
        self,
        is_established: bool,
        is_lookalike: bool,
        is_ssrf: bool,
        resolves: bool,
        has_elevated_abuse_tld: bool,
        historical_trend: HistoricalScanTrend,
        has_active_threat_signals: bool,
    ) -> Tuple[DomainReputationCategory, int, str]:
        """Synthesizes signals into a calibrated reputation score and category."""
        # 1. SSRF boundary violation: immediate critical risk
        if is_ssrf:
            return "CONFIRMED_MALICIOUS", 0, "LOW"

        # 2. Lookalike / Brand Impersonation
        if is_lookalike:
            return "IMPERSONATION_RISK", 15, "LOW"

        # 3. Established Verified Top Authority
        if is_established:
            # Notice: Never assign 100 automatically; capped at 95 to allow technical inspection
            base_score = 95
            if not resolves:
                base_score -= 20
            if has_active_threat_signals:
                base_score -= 25
            return "VERIFIED_ESTABLISHED", base_score, "LOW"

        # 4. Historically Malicious
        if historical_trend.past_threat_detections > 0 and historical_trend.past_threat_detections >= (historical_trend.total_scans // 2):
            return "CONFIRMED_MALICIOUS", 20, "LOW"

        # 5. Stable Clean Historical Track Record
        if historical_trend.reputation_stability == "STABLE_CLEAN":
            return "REPUTABLE", 82, "LOW"

        # 6. Suspicious Pattern (elevated abuse TLD + non-resolving or threat signals)
        if has_elevated_abuse_tld and (not resolves or has_active_threat_signals):
            return "SUSPICIOUS_PATTERN", 35, "MEDIUM"

        # 7. Default: Unfamiliar / Neutral Domain
        # Not automatically malicious; expresses high uncertainty and neutral 60 score
        base_unfamiliar = 60
        if has_elevated_abuse_tld:
            base_unfamiliar -= 10
        if not resolves:
            base_unfamiliar -= 15

        return "NEUTRAL_UNFAMILIAR", max(25, base_unfamiliar), "HIGH"
