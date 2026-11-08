"""
URL Feature Extraction & Preliminary Security Analysis Engine.
Extracts measurable structural, lexical, and security-relevant features from URLs.
Computes rule-based preliminary threat indicators without declaring a final verdict.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any, Dict
from urllib.parse import parse_qsl, urlparse

from app.utils.entropy import (
    calculate_char_ratios,
    calculate_shannon_entropy,
    detect_homograph_and_lookalikes,
)

# Suspicious keywords commonly exploited in phishing and social engineering URLs
_SUSPICIOUS_KEYWORDS = [
    "login",
    "signin",
    "sign-in",
    "verify",
    "verification",
    "account",
    "banking",
    "bank",
    "secure",
    "security",
    "update",
    "confirm",
    "confirmation",
    "wallet",
    "crypto",
    "credential",
    "password",
    "auth",
    "authenticate",
    "billing",
    "invoice",
    "paypal",
    "apple",
    "microsoft",
    "google",
    "netflix",
    "amazon",
    "chase",
    "wellsfargo",
]

# Recognised URL shortening services
_SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "is.gd",
    "buff.ly",
    "ow.ly",
    "rebrand.ly",
    "cutt.ly",
    "goo.gl",
    "qr.ae",
    "trib.al",
    "tiny.cc",
    "shorte.st",
}

# TLDs frequently observed in malicious campaigns due to low acquisition cost
_SUSPICIOUS_TLDS = {
    ".xyz",
    ".top",
    ".click",
    ".gq",
    ".tk",
    ".ml",
    ".cf",
    ".ga",
    ".buzz",
    ".cam",
    ".work",
    ".icu",
    ".sbs",
    ".rest",
    ".monster",
}

_COMMON_BRAND_NAMES = [
    "paypal",
    "apple",
    "google",
    "microsoft",
    "amazon",
    "netflix",
    "facebook",
    "instagram",
    "chase",
    "bankofamerica",
]


class URLAnalyzer:
    """
    Extracts structural/lexical features and produces preliminary risk indicators.
    """

    def analyze(self, raw_url: str, normalized_url: str) -> Dict[str, Any]:
        """
        Executes static feature extraction and preliminary security indicator generation.
        """
        parsed = urlparse(normalized_url)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path or ""
        query = parsed.query or ""

        # --- 1. Basic Measurable Features ---
        url_length = len(normalized_url)
        hostname_length = len(hostname)
        path_length = len(path)
        path_depth = path.count("/") - 1 if path.startswith("/") else path.count("/")
        path_depth = max(0, path_depth)

        dot_count = normalized_url.count(".")
        hyphen_count = normalized_url.count("-")
        underscore_count = normalized_url.count("_")
        digit_count = sum(c.isdigit() for c in normalized_url)
        special_chars = sum(not c.isalnum() and c not in "/:." for c in normalized_url)

        query_params = parse_qsl(query, keep_blank_values=True)
        query_param_count = len(query_params)

        # Hostname subdomains
        host_parts = hostname.split(".")
        subdomain_count = max(0, len(host_parts) - 2) if len(host_parts) > 2 else 0

        # --- 2. Security-Relevant Features ---
        is_ip_address = self._check_is_ip(hostname)
        uses_https = parsed.scheme.lower() == "https"

        # Suspicious keywords in hostname or path
        found_keywords = [kw for kw in _SUSPICIOUS_KEYWORDS if kw in normalized_url.lower()]
        has_suspicious_keywords = len(found_keywords) > 0

        # URL shortener detection
        is_shortened = hostname in _SHORTENER_DOMAINS

        # Excessive subdomains (>= 3 subdomains)
        excessive_subdomains = subdomain_count >= 3

        # Suspicious use of '@' sign (RFC 3986 userinfo trick)
        has_at_symbol = "@" in raw_url or "@" in normalized_url

        # Double slash in path outside scheme
        has_double_slash = "//" in path

        # Punycode detection
        has_punycode = "xn--" in hostname

        # Suspicious TLD check
        has_suspicious_tld = any(hostname.endswith(tld) for tld in _SUSPICIOUS_TLDS)

        # Non-standard port check
        has_non_standard_port = False
        port = parsed.port
        if port is not None and port not in (80, 443):
            has_non_standard_port = True

        # Brand name inside subdomains (e.g. paypal.com.evil.com)
        has_brand_in_subdomain = False
        if subdomain_count > 0:
            subdomain_str = ".".join(host_parts[:-2])
            has_brand_in_subdomain = any(brand in subdomain_str for brand in _COMMON_BRAND_NAMES)

        # Extended Information-Theoretic & Lexical Features
        url_entropy = calculate_shannon_entropy(normalized_url)
        hostname_entropy = calculate_shannon_entropy(hostname)
        digit_letter_ratio, vowel_consonant_ratio = calculate_char_ratios(hostname)
        has_homograph, homograph_reason = detect_homograph_and_lookalikes(hostname)
        has_hex_encoding = bool(re.search(r"%[0-9a-fA-F]{2}", normalized_url))
        
        common_tlds = [".com", ".net", ".org", ".edu", ".gov", ".xyz", ".top"]
        tld_in_path = any(f"{tld}/" in path.lower() or path.lower().endswith(tld) for tld in common_tlds)
        tokens = [t for t in re.split(r"[^a-zA-Z0-9]", normalized_url) if t]
        longest_token_length = max((len(t) for t in tokens), default=0)

        features = {
            "url_length": url_length,
            "hostname_length": hostname_length,
            "path_length": path_length,
            "path_depth": path_depth,
            "dot_count": dot_count,
            "hyphen_count": hyphen_count,
            "underscore_count": underscore_count,
            "digit_count": digit_count,
            "special_char_count": special_chars,
            "subdomain_count": subdomain_count,
            "query_param_count": query_param_count,
            "uses_https": uses_https,
            "is_ip_address": is_ip_address,
            "is_shortened": is_shortened,
            "contains_suspicious_keywords": has_suspicious_keywords,
            "suspicious_keywords": found_keywords,
            "suspicious_keyword_count": len(found_keywords),
            "excessive_subdomains": excessive_subdomains,
            "has_at_symbol": has_at_symbol,
            "has_double_slash_in_path": has_double_slash,
            "has_punycode": has_punycode,
            "has_suspicious_tld": has_suspicious_tld,
            "has_non_standard_port": has_non_standard_port,
            "has_brand_in_subdomain": has_brand_in_subdomain,
            "url_entropy": url_entropy,
            "hostname_entropy": hostname_entropy,
            "digit_letter_ratio": digit_letter_ratio,
            "vowel_consonant_ratio": vowel_consonant_ratio,
            "has_homograph": has_homograph,
            "homograph_reason": homograph_reason,
            "has_hex_encoding": has_hex_encoding,
            "tld_in_path": tld_in_path,
            "longest_token_length": longest_token_length,
        }

        # --- 3. Generate Preliminary Risk Indicators ---
        indicators = []

        if is_ip_address:
            indicators.append(
                {
                    "name": "IP_BASED_HOSTNAME",
                    "description": "The URL uses a raw IP address instead of a domain name.",
                    "severity": "high",
                    "evidence": hostname,
                    "reason": "Legitimate organizations rarely host public websites on raw IP addresses; commonly used to bypass domain reputation blocklists.",
                }
            )

        if has_at_symbol:
            indicators.append(
                {
                    "name": "AT_SYMBOL_OBFUSCATION",
                    "description": "The URL contains an '@' character in the authority portion.",
                    "severity": "high",
                    "evidence": "@",
                    "reason": "The '@' symbol causes browsers to ignore all preceding authority text and navigate only to what follows, deceiving users into seeing a fake brand.",
                }
            )

        if has_punycode:
            indicators.append(
                {
                    "name": "PUNYCODE_HOMOGRAPH",
                    "description": "The hostname utilizes Punycode ('xn--') encoding.",
                    "severity": "medium",
                    "evidence": hostname,
                    "reason": "Internationalized domain names can display visually identical characters (homoglyphs) to impersonate trusted brands.",
                }
            )

        if has_brand_in_subdomain:
            indicators.append(
                {
                    "name": "BRAND_NAME_IN_SUBDOMAIN",
                    "description": "A well-known brand keyword was found in the subdomain structure.",
                    "severity": "high",
                    "evidence": hostname,
                    "reason": "Phishing sites frequently embed trusted brand names (e.g. paypal.com.attacker.com) to deceive mobile users viewing truncated address bars.",
                }
            )

        if has_suspicious_keywords:
            indicators.append(
                {
                    "name": "SUSPICIOUS_KEYWORDS",
                    "description": f"URL contains security-sensitive action keywords: {', '.join(found_keywords)}",
                    "severity": "medium" if len(found_keywords) > 1 else "low",
                    "evidence": ", ".join(found_keywords),
                    "reason": "Keywords related to authentication, credentials, and verification are prevalent in phishing and social engineering URLs.",
                }
            )

        if has_suspicious_tld:
            indicators.append(
                {
                    "name": "SUSPICIOUS_TOP_LEVEL_DOMAIN",
                    "description": "The URL uses a top-level domain frequently associated with spam or low-cost malicious operations.",
                    "severity": "medium",
                    "evidence": host_parts[-1] if host_parts else "",
                    "reason": "Certain TLDs have disproportionately high abuse rates according to global threat intelligence telemetry.",
                }
            )

        if excessive_subdomains:
            indicators.append(
                {
                    "name": "EXCESSIVE_SUBDOMAINS",
                    "description": f"Hostname contains {subdomain_count} subdomain levels.",
                    "severity": "medium",
                    "evidence": hostname,
                    "reason": "Unusual subdomain depth is often employed in dynamic DNS phishing networks.",
                }
            )

        if is_shortened:
            indicators.append(
                {
                    "name": "URL_SHORTENER_DETECTED",
                    "description": "URL relies on a shortening redirection service.",
                    "severity": "low",
                    "evidence": hostname,
                    "reason": "Shorteners mask the true final destination from the user prior to navigation.",
                }
            )

        if not uses_https:
            indicators.append(
                {
                    "name": "INSECURE_HTTP_SCHEME",
                    "description": "The website uses plain unencrypted HTTP.",
                    "severity": "low",
                    "evidence": "http://",
                    "reason": "Modern legitimate websites use HTTPS to protect user traffic from interception.",
                }
            )

        if has_non_standard_port:
            indicators.append(
                {
                    "name": "NON_STANDARD_PORT",
                    "description": f"URL connects to custom port {port}.",
                    "severity": "medium",
                    "evidence": str(port),
                    "reason": "Web traffic is standard on ports 80/443; non-standard ports can indicate backdoors, testing servers, or alternate hosts.",
                }
            )

        # Preliminary concern categorization
        high_severity_count = sum(1 for i in indicators if i["severity"] in ("high", "critical"))
        medium_severity_count = sum(1 for i in indicators if i["severity"] == "medium")

        if high_severity_count >= 1 or medium_severity_count >= 3:
            preliminary_level = "HIGH_CONCERN"
        elif medium_severity_count >= 1 or len(indicators) >= 2:
            preliminary_level = "MODERATE_CONCERN"
        elif len(indicators) > 0:
            preliminary_level = "LOW_CONCERN"
        else:
            preliminary_level = "LOW_CONCERN"

        return {
            "risk_level": preliminary_level,
            "indicators": indicators,
            "features": features,
        }

    @staticmethod
    def _check_is_ip(hostname: str) -> bool:
        """Determines if a hostname string is an IPv4 or IPv6 literal."""
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False
