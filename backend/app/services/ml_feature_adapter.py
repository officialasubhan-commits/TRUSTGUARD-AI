"""
ML Feature Adapter for TrustGuard AI.

Ensures complete synchronization between the feature extraction logic
in URLAnalyzer and the feature vector expected by Scikit-Learn models.
Maintains exact feature ordering, handles missing keys, supports schema versioning,
and provides grounded, explainable indicator narratives for non-technical users.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Schema V1 (Legacy 23 features)
FEATURE_NAMES_V1: List[str] = [
    "url_length",
    "hostname_length",
    "path_length",
    "path_depth",
    "dot_count",
    "hyphen_count",
    "underscore_count",
    "digit_count",
    "special_char_count",
    "subdomain_count",
    "query_param_count",
    "uses_https",
    "is_ip_address",
    "is_shortened",
    "contains_suspicious_keywords",
    "suspicious_keyword_count",
    "excessive_subdomains",
    "has_at_symbol",
    "has_double_slash_in_path",
    "has_punycode",
    "has_suspicious_tld",
    "has_non_standard_port",
    "has_brand_in_subdomain",
]

# Schema V2 (Current 30 features - includes Shannon entropy and lexical ratios)
FEATURE_NAMES_V2: List[str] = FEATURE_NAMES_V1 + [
    "url_entropy",
    "hostname_entropy",
    "digit_letter_ratio",
    "vowel_consonant_ratio",
    "has_homograph",
    "has_hex_encoding",
    "tld_in_path",
]

# Default active feature names
FEATURE_NAMES: List[str] = FEATURE_NAMES_V2
FEATURE_SCHEMA_VERSION = "2.0.0"


def extract_feature_vector(
    features_dict: Dict[str, Any],
    target_feature_count: Optional[int] = None,
) -> List[float]:
    """
    Transforms the URLAnalyzer output features dictionary into a validated,
    deterministic 1D numerical feature vector matching the model's schema.
    If target_feature_count is 23, returns V1 schema; otherwise returns V2 schema.
    """
    kw_count = 0
    if "suspicious_keyword_count" in features_dict:
        kw_count = int(features_dict["suspicious_keyword_count"])
    elif "suspicious_keywords" in features_dict and isinstance(
        features_dict["suspicious_keywords"], list
    ):
        kw_count = len(features_dict["suspicious_keywords"])
    elif features_dict.get("contains_suspicious_keywords"):
        kw_count = 1

    v1_vector: List[float] = [
        float(features_dict.get("url_length", 0)),
        float(features_dict.get("hostname_length", 0)),
        float(features_dict.get("path_length", 0)),
        float(features_dict.get("path_depth", 0)),
        float(features_dict.get("dot_count", 0)),
        float(features_dict.get("hyphen_count", 0)),
        float(features_dict.get("underscore_count", 0)),
        float(features_dict.get("digit_count", 0)),
        float(features_dict.get("special_char_count", 0)),
        float(features_dict.get("subdomain_count", 0)),
        float(features_dict.get("query_param_count", 0)),
        1.0 if features_dict.get("uses_https", False) else 0.0,
        1.0 if features_dict.get("is_ip_address", False) else 0.0,
        1.0 if features_dict.get("is_shortened", False) else 0.0,
        1.0 if features_dict.get("contains_suspicious_keywords", False) else 0.0,
        float(kw_count),
        1.0 if features_dict.get("excessive_subdomains", False) else 0.0,
        1.0 if features_dict.get("has_at_symbol", False) else 0.0,
        1.0 if features_dict.get("has_double_slash_in_path", False) else 0.0,
        1.0 if features_dict.get("has_punycode", False) else 0.0,
        1.0 if features_dict.get("has_suspicious_tld", False) else 0.0,
        1.0 if features_dict.get("has_non_standard_port", False) else 0.0,
        1.0 if features_dict.get("has_brand_in_subdomain", False) else 0.0,
    ]

    if target_feature_count == 23:
        return v1_vector

    # V2 extended features
    v2_extensions: List[float] = [
        float(features_dict.get("url_entropy", 0.0)),
        float(features_dict.get("hostname_entropy", 0.0)),
        float(features_dict.get("digit_letter_ratio", 0.0)),
        float(features_dict.get("vowel_consonant_ratio", 0.0)),
        1.0 if features_dict.get("has_homograph", False) else 0.0,
        1.0 if features_dict.get("has_hex_encoding", False) else 0.0,
        1.0 if features_dict.get("tld_in_path", False) else 0.0,
    ]

    return v1_vector + v2_extensions


def generate_explainable_indicators(features_dict: Dict[str, Any]) -> List[str]:
    """
    Translates prominent raw feature triggers into concise, truthful,
    human-readable contributing explanations for end users.
    Only includes statements strictly supported by the extracted features.
    """
    indicators: List[str] = []

    if features_dict.get("is_ip_address"):
        indicators.append("Host is a raw numerical IP address instead of a registered domain name.")

    if features_dict.get("has_at_symbol"):
        indicators.append(
            "URL contains an '@' userinfo character, frequently used to mislead browser address bars."
        )

    if features_dict.get("has_brand_in_subdomain"):
        indicators.append(
            "A recognized brand keyword is embedded inside a subdomain to mimic an official service."
        )

    if features_dict.get("has_homograph"):
        reason = features_dict.get("homograph_reason", "homograph")
        indicators.append(
            f"Hostname exhibits potential visual impersonation / deceptive characters ({reason})."
        )

    if features_dict.get("has_punycode"):
        indicators.append(
            "Hostname utilizes Punycode ('xn--') encoding, which can mask visually identical deceptive characters."
        )

    if features_dict.get("contains_suspicious_keywords"):
        kw_list = features_dict.get("suspicious_keywords")
        if isinstance(kw_list, list) and kw_list:
            indicators.append(
                f"Contains security-sensitive action keywords: {', '.join(kw_list[:4])}."
            )
        else:
            indicators.append("URL contains authentication or credential-related action keywords.")

    if features_dict.get("has_suspicious_tld"):
        indicators.append("Uses a top-level domain (TLD) with statistically elevated abuse rates.")

    if features_dict.get("excessive_subdomains") or features_dict.get("subdomain_count", 0) >= 3:
        indicators.append(
            f"Unusually deep subdomain hierarchy ({features_dict.get('subdomain_count')} levels)."
        )

    if features_dict.get("url_entropy", 0.0) >= 4.5:
        indicators.append(
            f"High Shannon entropy ({features_dict.get('url_entropy')} bits/char) indicates algorithmic randomness or obfuscation."
        )

    if features_dict.get("tld_in_path"):
        indicators.append("A top-level domain suffix is embedded in the URL path, a tactic common in redirect phishing.")

    if features_dict.get("has_hex_encoding"):
        indicators.append("Contains hex percent-encoding in path, often used to bypass lexical scanners.")

    if features_dict.get("url_length", 0) > 75:
        indicators.append(f"Unusually long URL ({features_dict.get('url_length')} characters).")

    if features_dict.get("hyphen_count", 0) >= 3:
        indicators.append(
            f"Multiple hyphen separators ({features_dict.get('hyphen_count')}) often used to mimic legitimate names."
        )

    if features_dict.get("digit_count", 0) >= 6:
        indicators.append(
            f"High concentration of numerical digits ({features_dict.get('digit_count')}) in domain/path."
        )

    if features_dict.get("is_shortened"):
        indicators.append(
            "Uses a URL shortening redirector that obscures the destination destination."
        )

    if not features_dict.get("uses_https", True):
        indicators.append("Unencrypted connection (plain HTTP instead of HTTPS).")

    if features_dict.get("has_non_standard_port"):
        indicators.append("Connects to a non-standard network port rather than port 80 or 443.")

    return indicators
