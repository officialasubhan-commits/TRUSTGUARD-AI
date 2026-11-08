"""
VirusTotal v3 API Threat Intelligence Service.

Integrates with the official VirusTotal API v3 to retrieve URL reputation data,
manage multi-engine verdicts, handle asynchronous URL submissions, cache responses
to respect free-tier rate limits, and persist findings to the database.
"""

from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.database.repositories.scan_repo import ScanRepository
from app.database.repositories.threat_repo import ThreatRepository
from app.schemas.threat_intel import ThreatIntelCreate
from app.schemas.virustotal import (
    VirusTotalReportResponse,
    VirusTotalVendorStats,
)
from app.services.threat_classifier import ThreatClassifier

logger = logging.getLogger("trustguard.service.virustotal")


class VirusTotalService:
    """Service managing VirusTotal v3 URL reputation and threat intelligence."""

    # In-memory response cache: {url_identifier: (cached_at_datetime, response_object)}
    _cache: Dict[str, Tuple[datetime, VirusTotalReportResponse]] = {}

    def __init__(
        self,
        api_key: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        threat_repo: Optional[ThreatRepository] = None,
        scan_repo: Optional[ScanRepository] = None,
    ):
        self._api_key = (api_key if api_key is not None else settings.VIRUSTOTAL_API_KEY).strip()
        self._base_url = settings.VIRUSTOTAL_BASE_URL.rstrip("/")
        self._http_client = http_client
        self._threat_repo = threat_repo or ThreatRepository()
        self._scan_repo = scan_repo or ScanRepository()

    @staticmethod
    def get_url_identifier(url: str) -> str:
        """
        Computes the VirusTotal v3 URL resource identifier.
        According to VT v3 docs, the URL identifier is base64url encoded without '=' padding.
        """
        encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8")
        return encoded.rstrip("=")

    def _is_api_key_configured(self) -> bool:
        """Validates if a realistic, non-placeholder API key is set."""
        if not self._api_key:
            return False
        placeholder_indicators = ["placeholder", "your-", "xxx", "change_me", "test_key_dummy"]
        return not any(p in self._api_key.lower() for p in placeholder_indicators)

    def _get_from_cache(self, url_id: str) -> Optional[VirusTotalReportResponse]:
        """Retrieves unexpired cached report if present."""
        if url_id in self._cache:
            cached_at, report = self._cache[url_id]
            ttl = timedelta(seconds=settings.VIRUSTOTAL_CACHE_TTL_SECONDS)
            if datetime.now(timezone.utc) - cached_at < ttl:
                logger.debug("VirusTotal cache hit for URL ID: %s", url_id)
                # Return a copy with cached=True
                return report.model_copy(update={"cached": True})
            # Expired
            del self._cache[url_id]
        return None

    def _store_in_cache(self, url_id: str, report: VirusTotalReportResponse) -> None:
        """Stores report in cache with current UTC timestamp."""
        self._cache[url_id] = (datetime.now(timezone.utc), report)

    async def lookup_url(
        self,
        url: str,
        scan_id: Optional[uuid.UUID] = None,
    ) -> VirusTotalReportResponse:
        """
        Queries VirusTotal v3 for the reputation and threat profile of a given URL.

        Features:
        - Transparent in-memory caching to observe 4 req/min rate limit
        - Automatic fallback on missing credentials or quota exhaustion
        - Asynchronous URL submission when URL is unknown to VirusTotal (404)
        - Database persistence for scan results and threat reports
        """
        url_identifier = self.get_url_identifier(url)

        # 1. Check local cache first
        cached_result = self._get_from_cache(url_identifier)
        if cached_result:
            if scan_id and cached_result.scan_id != scan_id:
                # Update with current scan_id and save to db if needed
                cached_result = cached_result.model_copy(update={"scan_id": scan_id})
                await self._persist_findings(cached_result, scan_id, url)
            return cached_result

        # 2. Check if API key is configured
        if not self._is_api_key_configured():
            logger.info(
                "VirusTotal API key not configured or using placeholder. Returning API_UNAVAILABLE."
            )
            classification, subscore = ThreatClassifier.classify(
                stats=VirusTotalVendorStats(),
                status_override="API_UNAVAILABLE",
                override_message="VirusTotal API key is not configured. Reputation lookup was skipped.",
            )
            report = VirusTotalReportResponse(
                source="VirusTotal v3",
                status="API_UNAVAILABLE",
                url=url,
                url_identifier=url_identifier,
                vt_subscore=subscore,
                statistics=VirusTotalVendorStats(),
                classification=classification,
                scan_id=scan_id,
                cached=False,
                message="VirusTotal API key is not configured.",
            )
            self._store_in_cache(url_identifier, report)
            if scan_id:
                await self._persist_findings(report, scan_id, url)
            return report

        # 3. Perform HTTP request to VirusTotal API v3
        headers = {
            "x-apikey": self._api_key,
            "Accept": "application/json",
        }
        url_endpoint = f"{self._base_url}/urls/{url_identifier}"

        client = self._http_client or httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT_SECONDS,
            follow_redirects=False,
        )
        should_close = self._http_client is None

        try:
            logger.info("Querying VirusTotal v3 reputation for URL identifier: %s", url_identifier)
            response = await client.get(url_endpoint, headers=headers)

            # --- CASE 1: 200 OK (Existing analysis) ---
            if response.status_code == 200:
                data = response.json().get("data", {})
                attributes = data.get("attributes", {})

                raw_stats = attributes.get("last_analysis_stats", {})
                stats = VirusTotalVendorStats(
                    malicious=raw_stats.get("malicious", 0),
                    suspicious=raw_stats.get("suspicious", 0),
                    harmless=raw_stats.get("harmless", 0),
                    undetected=raw_stats.get("undetected", 0),
                    timeout=raw_stats.get("timeout", 0),
                    total_engines=sum(raw_stats.values()) if raw_stats else 0,
                )

                engine_results = attributes.get("last_analysis_results", {})
                classification, subscore = ThreatClassifier.classify(
                    stats=stats,
                    engine_results=engine_results,
                )

                # Parse last analysis date
                epoch_date = attributes.get("last_analysis_date")
                last_analysis_date = (
                    datetime.fromtimestamp(epoch_date, tz=timezone.utc) if epoch_date else None
                )

                report = VirusTotalReportResponse(
                    source="VirusTotal v3",
                    status=classification.status,
                    url=url,
                    url_identifier=url_identifier,
                    vt_subscore=subscore,
                    statistics=stats,
                    classification=classification,
                    last_analysis_date=last_analysis_date,
                    scan_id=scan_id,
                    cached=False,
                    message="Threat intelligence retrieved successfully from VirusTotal.",
                )

            # --- CASE 2: 404 Not Found (URL not previously scanned) ---
            elif response.status_code == 404:
                logger.info("URL not found in VirusTotal. Submitting for initial analysis...")
                report = await self._submit_and_poll_url(
                    client=client,
                    headers=headers,
                    url=url,
                    url_identifier=url_identifier,
                    scan_id=scan_id,
                )

            # --- CASE 3: 429 Too Many Requests (Rate limit exceeded) ---
            elif response.status_code == 429:
                logger.warning("VirusTotal API rate limit exceeded (429).")
                classification, subscore = ThreatClassifier.classify(
                    stats=VirusTotalVendorStats(),
                    status_override="RATE_LIMITED",
                    override_message="VirusTotal API rate limit reached (free tier: 4 requests/min).",
                )
                report = VirusTotalReportResponse(
                    source="VirusTotal v3",
                    status="RATE_LIMITED",
                    url=url,
                    url_identifier=url_identifier,
                    vt_subscore=subscore,
                    statistics=VirusTotalVendorStats(),
                    classification=classification,
                    scan_id=scan_id,
                    cached=False,
                    message="Rate limit exceeded on VirusTotal API.",
                )

            # --- CASE 4: 401 / 403 (Invalid credentials) ---
            elif response.status_code in (401, 403):
                logger.error(
                    "VirusTotal API authentication failed with HTTP %d.", response.status_code
                )
                classification, subscore = ThreatClassifier.classify(
                    stats=VirusTotalVendorStats(),
                    status_override="API_UNAVAILABLE",
                    override_message=f"VirusTotal authentication failed (HTTP {response.status_code}).",
                )
                report = VirusTotalReportResponse(
                    source="VirusTotal v3",
                    status="API_UNAVAILABLE",
                    url=url,
                    url_identifier=url_identifier,
                    vt_subscore=subscore,
                    statistics=VirusTotalVendorStats(),
                    classification=classification,
                    scan_id=scan_id,
                    cached=False,
                    message="VirusTotal authentication failed. Check API key.",
                )

            # --- CASE 5: Other HTTP errors ---
            else:
                logger.warning(
                    "VirusTotal returned unexpected HTTP status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                classification, subscore = ThreatClassifier.classify(
                    stats=VirusTotalVendorStats(),
                    status_override="ERROR",
                    override_message=f"VirusTotal returned unexpected status {response.status_code}.",
                )
                report = VirusTotalReportResponse(
                    source="VirusTotal v3",
                    status="ERROR",
                    url=url,
                    url_identifier=url_identifier,
                    vt_subscore=subscore,
                    statistics=VirusTotalVendorStats(),
                    classification=classification,
                    scan_id=scan_id,
                    cached=False,
                    message=f"VirusTotal query failed with HTTP {response.status_code}.",
                )

        except httpx.TimeoutException:
            logger.warning("Timeout connecting to VirusTotal v3 API.")
            classification, subscore = ThreatClassifier.classify(
                stats=VirusTotalVendorStats(),
                status_override="ERROR",
                override_message="VirusTotal API connection timed out.",
            )
            report = VirusTotalReportResponse(
                source="VirusTotal v3",
                status="ERROR",
                url=url,
                url_identifier=url_identifier,
                vt_subscore=subscore,
                statistics=VirusTotalVendorStats(),
                classification=classification,
                scan_id=scan_id,
                cached=False,
                message="VirusTotal request timed out.",
            )

        except Exception as e:
            logger.error("Unexpected error querying VirusTotal: %s", e)
            classification, subscore = ThreatClassifier.classify(
                stats=VirusTotalVendorStats(),
                status_override="ERROR",
                override_message=f"Error connecting to VirusTotal: {str(e)}",
            )
            report = VirusTotalReportResponse(
                source="VirusTotal v3",
                status="ERROR",
                url=url,
                url_identifier=url_identifier,
                vt_subscore=subscore,
                statistics=VirusTotalVendorStats(),
                classification=classification,
                scan_id=scan_id,
                cached=False,
                message=f"Error connecting to VirusTotal: {str(e)}",
            )

        finally:
            if should_close:
                await client.aclose()

        # Cache valid responses
        self._store_in_cache(url_identifier, report)

        # Persist findings if scan_id provided
        if scan_id:
            await self._persist_findings(report, scan_id, url)

        return report

    async def _submit_and_poll_url(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        url: str,
        url_identifier: str,
        scan_id: Optional[uuid.UUID],
    ) -> VirusTotalReportResponse:
        """
        Submits an unknown URL to VirusTotal v3 and returns a pending or newly indexed report.
        Never blocks the backend indefinitely.
        """
        submit_endpoint = f"{self._base_url}/urls"
        try:
            submit_resp = await client.post(
                submit_endpoint,
                headers=headers,
                data={"url": url},
            )

            if submit_resp.status_code in (200, 201):
                resp_json = submit_resp.json()
                analysis_id = resp_json.get("data", {}).get("id")
                logger.info("Submitted URL to VirusTotal. Analysis ID: %s", analysis_id)

                classification, subscore = ThreatClassifier.classify(
                    stats=VirusTotalVendorStats(),
                    status_override="PENDING",
                    override_message="URL submitted to VirusTotal for analysis. Scan is currently queued.",
                )
                return VirusTotalReportResponse(
                    source="VirusTotal v3",
                    status="PENDING",
                    url=url,
                    url_identifier=url_identifier,
                    vt_subscore=subscore,
                    statistics=VirusTotalVendorStats(),
                    classification=classification,
                    scan_id=scan_id,
                    cached=False,
                    message="URL submitted to VirusTotal; analysis queued.",
                )
            else:
                logger.warning(
                    "Failed to submit URL to VirusTotal: HTTP %d", submit_resp.status_code
                )
        except Exception as e:
            logger.error("Exception submitting URL to VirusTotal: %s", e)

        # Fallback to NOT_FOUND
        classification, subscore = ThreatClassifier.classify(
            stats=VirusTotalVendorStats(),
            status_override="NOT_FOUND",
            override_message="URL was not found in VirusTotal and submission could not be completed.",
        )
        return VirusTotalReportResponse(
            source="VirusTotal v3",
            status="NOT_FOUND",
            url=url,
            url_identifier=url_identifier,
            vt_subscore=subscore,
            statistics=VirusTotalVendorStats(),
            classification=classification,
            scan_id=scan_id,
            cached=False,
            message="URL not found in VirusTotal repository.",
        )

    async def _persist_findings(
        self,
        report: VirusTotalReportResponse,
        scan_id: uuid.UUID,
        url: str,
    ) -> None:
        """Saves VirusTotal intelligence to scan_results and threat_reports tables."""
        domain: Optional[str] = None
        try:
            parsed = urlparse(url)
            domain = parsed.hostname
        except Exception:
            pass

        # 1. If malicious or suspicious engines detected, record in threat_reports
        if report.statistics.malicious > 0 or report.statistics.suspicious > 0:
            severity = (
                "critical"
                if report.statistics.malicious >= 5
                else (
                    "high"
                    if report.statistics.malicious >= 3
                    else ("medium" if report.statistics.malicious >= 1 else "low")
                )
            )
            threat_cat = (
                report.classification.threat_categories[0]
                if report.classification.threat_categories
                else "malicious"
            )

            threat_in = ThreatIntelCreate(
                scan_id=scan_id,
                normalized_url=url,
                domain=domain,
                threat_source="virustotal",
                threat_category=threat_cat,
                severity=severity,
                verification_status="verified",
                first_seen_at=report.last_analysis_date or datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc),
                raw_data={
                    "detection_ratio": report.classification.detection_ratio,
                    "statistics": report.statistics.model_dump(),
                    "flagged_vendors": report.classification.flagged_vendors,
                    "categories": report.classification.threat_categories,
                },
            )
            try:
                await self._threat_repo.save_threat_record(threat_in)
                logger.info(
                    "Persisted threat record for scan %s (category=%s, severity=%s)",
                    scan_id,
                    threat_cat,
                    severity,
                )
            except Exception as e:
                logger.error("Failed to save threat record: %s", e)

        # 2. Update scan_results record if it exists
        try:
            updates = {
                "virustotal_detection_count": report.statistics.malicious,
                "virustotal_total_engines": report.statistics.total_engines,
                "threat_intelligence_status": report.classification.status,
                "vt_score": report.vt_subscore,
                "vt_raw": {
                    "statistics": report.statistics.model_dump(),
                    "detection_ratio": report.classification.detection_ratio,
                    "confidence": report.classification.confidence,
                    "flagged_vendors": report.classification.flagged_vendors,
                    "threat_categories": report.classification.threat_categories,
                    "last_analysis_date": (
                        report.last_analysis_date.isoformat() if report.last_analysis_date else None
                    ),
                    "cached": report.cached,
                },
            }
            await self._scan_repo.update_scan_results(scan_id, updates)
            logger.info("Updated scan_results for scan %s with VT data", scan_id)
        except Exception as e:
            logger.debug("Scan result update skipped or pending for scan %s: %s", scan_id, e)
