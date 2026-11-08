"""
Mathematical utilities for URL feature analysis.
Provides Shannon entropy, character distribution ratios, and homograph detection.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Tuple


def calculate_shannon_entropy(text: str) -> float:
    """
    Computes Shannon entropy (base 2) of a character string.
    Higher entropy indicates random/obfuscated sequences (e.g. DGA domains or tokenized paths).
    """
    if not text:
        return 0.0
    length = len(text)
    counts = Counter(text)
    entropy = -sum((count / length) * math.log2(count / length) for count in counts.values())
    return round(entropy, 4)


def calculate_char_ratios(text: str) -> Tuple[float, float]:
    """
    Computes (digit_letter_ratio, vowel_consonant_ratio).
    Useful for detecting algorithmic randomness, domain generation algorithms (DGAs),
    and obfuscated machine-generated strings.
    """
    if not text:
        return 0.0, 0.0

    lower = text.lower()
    digits = sum(c.isdigit() for c in lower)
    letters = sum(c.isalpha() for c in lower)

    # Ratio of digits to letters
    digit_letter_ratio = round(digits / (letters + 1), 4)

    # Vowel to consonant ratio
    vowels = sum(c in "aeiou" for c in lower)
    consonants = sum(c.isalpha() and c not in "aeiou" for c in lower)
    vowel_consonant_ratio = round(vowels / (consonants + 1), 4)

    return digit_letter_ratio, vowel_consonant_ratio


def detect_homograph_and_lookalikes(hostname: str) -> Tuple[bool, str]:
    """
    Identifies potential IDN homograph attacks and visually deceptive character substitutions:
    - Punycode domains (xn--)
    - Mixed Latin and Cyrillic/Greek script lookalikes
    - Common numeral-to-letter substitutions in brand contexts (e.g., paypa1, micros0ft)
    """
    if not hostname:
        return False, "None"

    # Punycode indicator
    if "xn--" in hostname.lower():
        return True, "PUNYCODE_IDN"

    # Common brand lookalike substitutions
    deceptive_patterns = [
        ("paypa1", "paypal"),
        ("pay-pal", "paypal"),
        ("micros0ft", "microsoft"),
        ("g00gle", "google"),
        ("app1e", "apple"),
        ("arnazon", "amazon"),
        ("netf1ix", "netflix"),
        ("faceb00k", "facebook"),
        ("chase-bank", "chase"),
        ("wellsfarg0", "wellsfargo"),
    ]

    h_lower = hostname.lower()
    for pattern, brand in deceptive_patterns:
        if pattern in h_lower and not h_lower.endswith(f".{brand}.com"):
            return True, f"LOOKALIKE_{brand.upper()}"

    # Check non-ASCII characters outside punycode
    has_non_ascii = any(ord(c) > 127 for c in hostname)
    if has_non_ascii:
        return True, "NON_ASCII_HOMOGRAPH"

    return False, "None"
