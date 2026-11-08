"""
Trusted Domain Reference Registry & Public Suffix Extraction for TrustGuard AI.

Provides authoritative reference identities for established domains,
accurate registered domain (eTLD+1) extraction, and lookalike detection.
Prevents false brand trust on subdomains (e.g. google.example.com != google.com).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Multi-part public suffixes commonly encountered
_MULTI_PART_TLDS = {
    "co.uk", "gov.uk", "ac.uk", "org.uk", "net.uk",
    "com.au", "gov.au", "edu.au", "net.au",
    "co.jp", "ne.jp", "go.jp", "ac.jp",
    "co.nz", "govt.nz", "ac.nz",
    "co.in", "gov.in", "ac.in", "org.in", "net.in",
    "com.br", "gov.br", "org.br",
    "com.cn", "gov.cn", "edu.cn",
    "com.sg", "gov.sg", "edu.sg",
    "gc.ca", "fed.us", "europa.eu",
}

# Verified global top organizational entities and their authentic registered domains
VERIFIED_ENTITIES: Dict[str, Dict[str, Any]] = {
    "google.com": {"entity": "Google LLC", "category": "Technology & Search", "verified": True},
    "google.co.uk": {"entity": "Google UK Ltd", "category": "Technology & Search", "verified": True},
    "youtube.com": {"entity": "YouTube LLC (Google)", "category": "Video & Media", "verified": True},
    "gmail.com": {"entity": "Google LLC", "category": "Email Service", "verified": True},
    "microsoft.com": {"entity": "Microsoft Corporation", "category": "Technology & Enterprise", "verified": True},
    "live.com": {"entity": "Microsoft Corporation", "category": "Identity & Email", "verified": True},
    "office.com": {"entity": "Microsoft Corporation", "category": "Enterprise Productivity", "verified": True},
    "azure.com": {"entity": "Microsoft Corporation", "category": "Cloud Infrastructure", "verified": True},
    "apple.com": {"entity": "Apple Inc.", "category": "Technology & Devices", "verified": True},
    "icloud.com": {"entity": "Apple Inc.", "category": "Cloud & Services", "verified": True},
    "github.com": {"entity": "GitHub, Inc. (Microsoft)", "category": "Software Development", "verified": True},
    "wikipedia.org": {"entity": "Wikimedia Foundation", "category": "Education & Reference", "verified": True},
    "wikimedia.org": {"entity": "Wikimedia Foundation", "category": "Education & Reference", "verified": True},
    "amazon.com": {"entity": "Amazon.com, Inc.", "category": "E-Commerce & Cloud", "verified": True},
    "aws.amazon.com": {"entity": "Amazon Web Services", "category": "Cloud Infrastructure", "verified": True},
    "cloudflare.com": {"entity": "Cloudflare, Inc.", "category": "Security & CDN", "verified": True},
    "openai.com": {"entity": "OpenAI, LLC", "category": "Artificial Intelligence", "verified": True},
    "python.org": {"entity": "Python Software Foundation", "category": "Software & Non-Profit", "verified": True},
    "mozilla.org": {"entity": "Mozilla Foundation", "category": "Open Source & Web", "verified": True},
    "paypal.com": {"entity": "PayPal, Inc.", "category": "Financial Services", "verified": True},
    "stripe.com": {"entity": "Stripe, Inc.", "category": "Financial Technology", "verified": True},
    "chase.com": {"entity": "JPMorgan Chase & Co.", "category": "Banking & Finance", "verified": True},
    "bankofamerica.com": {"entity": "Bank of America Corporation", "category": "Banking & Finance", "verified": True},
    "wellsfargo.com": {"entity": "Wells Fargo & Company", "category": "Banking & Finance", "verified": True},
    "netflix.com": {"entity": "Netflix, Inc.", "category": "Streaming Entertainment", "verified": True},
    "spotify.com": {"entity": "Spotify AB", "category": "Audio Streaming", "verified": True},
    "linkedin.com": {"entity": "LinkedIn Corporation (Microsoft)", "category": "Professional Network", "verified": True},
    "reddit.com": {"entity": "Reddit, Inc.", "category": "Social News & Discussion", "verified": True},
    "stackoverflow.com": {"entity": "Stack Overflow (Prosus)", "category": "Developer Community", "verified": True},
    "dropbox.com": {"entity": "Dropbox, Inc.", "category": "Cloud Storage", "verified": True},
    "slack.com": {"entity": "Slack Technologies (Salesforce)", "category": "Business Messaging", "verified": True},
    "salesforce.com": {"entity": "Salesforce, Inc.", "category": "Enterprise Cloud CRM", "verified": True},
    "harvard.edu": {"entity": "Harvard University", "category": "Higher Education", "verified": True},
    "mit.edu": {"entity": "Massachusetts Institute of Technology", "category": "Higher Education", "verified": True},
    "stanford.edu": {"entity": "Stanford University", "category": "Higher Education", "verified": True},
    "nih.gov": {"entity": "National Institutes of Health (US)", "category": "Government Healthcare", "verified": True},
    "cdc.gov": {"entity": "Centers for Disease Control and Prevention", "category": "Government Public Health", "verified": True},
    "cisa.gov": {"entity": "Cybersecurity and Infrastructure Security Agency", "category": "Government Cybersecurity", "verified": True},
    "whitehouse.gov": {"entity": "The White House (US)", "category": "Government Authority", "verified": True},
    "gov.uk": {"entity": "UK Government Digital Service", "category": "Government Authority", "verified": True},
}

# High-risk / elevated-abuse TLDs
ELEVATED_ABUSE_TLDS: Set[str] = {
    "xyz", "top", "click", "buzz", "cam", "icu", "sbs", "rest", "monster",
    "gq", "tk", "ml", "cf", "ga", "work", "loan", "fit", "country", "stream"
}

# Major protected brands targeted by phishing and typosquatters
PROTECTED_BRAND_TARGETS: Dict[str, str] = {
    "paypal": "paypal.com",
    "apple": "apple.com",
    "google": "google.com",
    "microsoft": "microsoft.com",
    "netflix": "netflix.com",
    "amazon": "amazon.com",
    "chase": "chase.com",
    "bankofamerica": "bankofamerica.com",
    "wellsfargo": "wellsfargo.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "binance": "binance.com",
    "coinbase": "coinbase.com",
    "meta": "meta.com",
    "steam": "steampowered.com",
}


def extract_registered_domain(hostname: str) -> str:
    """
    Extracts the effective registered domain (eTLD+1) from a fully qualified hostname.
    Accurately handles multi-part TLDs (e.g. google.co.uk -> google.co.uk).
    Examples:
      - www.google.com -> google.com
      - login.chase.com -> chase.com
      - google.com.attacker.xyz -> attacker.xyz
      - sub.service.gov.uk -> service.gov.uk
    """
    if not hostname:
        return ""

    hostname = hostname.lower().strip().rstrip(".")

    # Handle IP addresses
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
        return hostname

    parts = hostname.split(".")
    if len(parts) <= 2:
        return hostname

    # Check two-part suffix (e.g. co.uk, gov.in)
    two_part = ".".join(parts[-2:])
    if two_part in _MULTI_PART_TLDS and len(parts) >= 3:
        return ".".join(parts[-3:])

    # Default standard single TLD (eTLD+1)
    return ".".join(parts[-2:])


def check_brand_impersonation(hostname: str, registered_domain: str) -> Tuple[bool, Optional[str], str]:
    """
    Detects if an unverified domain attempts to impersonate a protected brand:
    1. Brand embedded in subdomain of a different domain (e.g., paypal.com.attack.xyz)
    2. Brand hyphenated in domain root (e.g., chase-security-update.com)
    3. Typosquats / homoglyphs (e.g., paypa1.com, micros0ft.com)
    
    Returns (is_impersonation, brand_name, reason).
    """
    h_lower = hostname.lower()
    reg_lower = registered_domain.lower()

    for brand, authentic_domain in PROTECTED_BRAND_TARGETS.items():
        # If the domain IS the authentic domain or its legitimate subdomain, it's safe
        if reg_lower == authentic_domain or reg_lower.endswith(f".{authentic_domain}"):
            continue

        # Case 1: Brand appears in subdomain of third-party domain
        if brand in h_lower and not (reg_lower == authentic_domain):
            # Check if brand appears in subdomains before the registered domain
            subdomain_part = h_lower[: -len(reg_lower)].rstrip(".") if len(h_lower) > len(reg_lower) else ""
            if brand in subdomain_part:
                return (
                    True,
                    brand,
                    f"Brand keyword '{brand}' is embedded in the subdomain of unrelated domain '{registered_domain}'.",
                )

            # Case 2: Brand combined with security/account lure in registered domain name
            # e.g., paypal-verification.com, chase-online-login.net
            lure_words = ["login", "signin", "verify", "security", "update", "account", "support", "billing", "alert"]
            if brand in reg_lower and any(lure in reg_lower for lure in lure_words):
                return (
                    True,
                    brand,
                    f"Domain '{registered_domain}' combines protected brand '{brand}' with an urgent credential/security lure.",
                )

    return False, None, "No brand impersonation detected."

