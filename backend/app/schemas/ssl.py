"""
Pydantic schemas for SSL/TLS Certificate Validation and Security Assessment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SSLStatusType = Literal[
    "VALID",
    "EXPIRING_SOON",
    "EXPIRED",
    "HOSTNAME_MISMATCH",
    "UNTRUSTED_CERTIFICATE",
    "TLS_HANDSHAKE_FAILED",
    "DNS_RESOLUTION_FAILED",
    "UNSAFE_DESTINATION",
    "HTTPS_NOT_USED",
    "TIMEOUT",
    "CONNECTION_ERROR",
    "UNKNOWN",
]


class SSLValidationResponse(BaseModel):
    """Structured certificate security assessment and protocol information."""

    status: SSLStatusType = Field(
        ...,
        description="High-level certificate validity and connection outcome",
    )
    https_enabled: bool = Field(
        default=True,
        description="Whether the URL scheme utilizes HTTPS encryption",
    )
    hostname: str = Field(
        ...,
        description="Target domain or hostname validated during TLS handshake",
    )
    certificate_subject: Optional[str] = Field(
        None,
        description="Common Name or distinguished name of the certificate subject",
    )
    certificate_issuer: Optional[str] = Field(
        None,
        description="Entity / Certificate Authority that issued and signed the certificate",
    )
    valid_from: Optional[datetime] = Field(
        None,
        description="Certificate activation not-before timestamp (UTC)",
    )
    valid_until: Optional[datetime] = Field(
        None,
        description="Certificate expiration not-after timestamp (UTC)",
    )
    days_remaining: Optional[int] = Field(
        None,
        description="Calculated days until expiration (negative if expired)",
    )
    hostname_verified: bool = Field(
        default=False,
        description="Whether certificate SAN/CN strictly matches the target hostname",
    )
    certificate_trusted: bool = Field(
        default=False,
        description="Whether the certificate chain anchors to a recognized root CA",
    )
    tls_version: Optional[str] = Field(
        None,
        description="Negotiated TLS protocol version (e.g. TLSv1.3, TLSv1.2)",
    )
    cipher: Optional[str] = Field(
        None,
        description="Negotiated cryptographic cipher suite name",
    )
    ssl_subscore: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Normalized trust subscore for SSL/TLS security (0-100; 100=clean)",
    )
    findings: List[str] = Field(
        default_factory=list,
        description="Specific security findings, flags, or warnings identified during validation",
    )
    error_code: Optional[str] = Field(
        None,
        description="Technical error classification code when validation fails",
    )
    message: str = Field(
        default="",
        description="Human-readable summary of the certificate validation outcome",
    )
    cached: bool = Field(
        default=False,
        description="True if served from the local certificate cache",
    )
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the TLS validation check was completed",
    )
    safety_advisory: str = Field(
        default=(
            "Security Notice: A valid SSL/TLS certificate confirms encrypted data transit "
            "and domain validation, but does NOT prove that a website is trustworthy or legitimate."
        ),
        description="Advisory reminding users that phishing sites frequently utilize valid HTTPS certificates",
    )

    model_config = ConfigDict(from_attributes=True)
