"""
Pydantic schemas for the Domain Reputation Intelligence Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DomainReputationCategory = Literal[
    "VERIFIED_ESTABLISHED",
    "REPUTABLE",
    "NEUTRAL_UNFAMILIAR",
    "SUSPICIOUS_PATTERN",
    "IMPERSONATION_RISK",
    "CONFIRMED_MALICIOUS",
]


class DNSIntelligence(BaseModel):
    """DNS technical intelligence summary for a domain."""

    resolves: bool = Field(default=False, description="Whether domain resolves to IP addresses")
    ip_addresses: List[str] = Field(default_factory=list, description="A/AAAA IPv4/IPv6 addresses")
    has_mx_records: bool = Field(default=False, description="Whether domain has mail exchange (MX) records")
    name_servers: List[str] = Field(default_factory=list, description="Authoritative name servers")
    is_private_or_loopback: bool = Field(default=False, description="SSRF defense: whether resolved IP is private/loopback")
    dns_sec: Optional[bool] = Field(default=None, description="DNSSEC configuration if available")


class HistoricalScanTrend(BaseModel):
    """Historical scan telemetry and reputation stability over time."""

    total_scans: int = Field(default=0, description="Total number of times this domain has been scanned")
    first_seen: Optional[datetime] = Field(default=None, description="Timestamp of first recorded scan")
    last_seen: Optional[datetime] = Field(default=None, description="Timestamp of most recent scan")
    average_trust_score: Optional[float] = Field(default=None, description="Historical average trust score")
    past_threat_detections: int = Field(default=0, description="Number of past scans where threats were detected")
    reputation_stability: Literal["STABLE_CLEAN", "NEW_UNOBSERVED", "VOLATILE", "DETERIORATING", "HISTORICALLY_MALICIOUS"] = Field(
        default="NEW_UNOBSERVED",
        description="Behavioral stability assessment based on scan history",
    )
    change_alert: Optional[str] = Field(
        default=None,
        description="Alert if domain behavior or reputation diverged from historical baseline",
    )


class DomainReputationResult(BaseModel):
    """Unified domain reputation assessment."""

    domain: str = Field(..., description="Target domain or hostname")
    registered_domain: str = Field(..., description="Effective registered domain (eTLD+1)")
    category: DomainReputationCategory = Field(
        ...,
        description="Evidence-based reputation category",
    )
    reputation_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Calibrated domain reputation subscore (0=untrusted/malicious, 100=highest verified trust)",
    )
    verified_identity: Optional[str] = Field(
        default=None,
        description="Verified organizational entity (e.g., 'Google LLC', 'Wikimedia Foundation') if verified",
    )
    is_established_authority: bool = Field(
        default=False,
        description="Whether the domain belongs to a globally established top authority",
    )
    is_lookalike_or_impersonation: bool = Field(
        default=False,
        description="Whether domain appears to impersonate a brand or uses homoglyph substitution",
    )
    impersonated_brand: Optional[str] = Field(
        default=None,
        description="Target brand name if an impersonation attempt is detected",
    )
    dns_intelligence: DNSIntelligence = Field(
        default_factory=DNSIntelligence,
        description="DNS resolution and infrastructure security attributes",
    )
    historical_trend: HistoricalScanTrend = Field(
        default_factory=HistoricalScanTrend,
        description="Historical scan comparison and change detection",
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Transparent evidence-based reasons supporting the reputation assessment",
    )
    uncertainty_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="LOW",
        description="Level of uncertainty regarding domain assessment (e.g. HIGH for brand-new domains with zero history)",
    )
    disclaimer: str = Field(
        default="Domain reputation is evaluated on verified reference data, infrastructure signals, and historical telemetry; popularity does not guarantee current safety.",
        description="Safety notice",
    )

    model_config = ConfigDict(from_attributes=True)
