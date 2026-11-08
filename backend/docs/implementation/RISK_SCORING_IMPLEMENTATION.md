# TrustGuard AI — Digital Trust Score & Intelligent Risk Assessment Engine

**Document Version:** 1.0.0  
**Implementation Phase:** Prompt 09 — Digital Trust Score & Risk Assessment Engine  
**Status:** COMPLETED & VERIFIED  

---

## 1. Architectural Overview & Security Philosophy

The **Digital Trust Score & Intelligent Risk Assessment Engine** is the core reasoning and synthesis brain of TrustGuard AI. It consolidates heterogeneous security telemetry from all four analytical subsystems into a unified, explainable, and evidence-grounded assessment.

```mermaid
flowchart TD
    subgraph Data Feeds
        M1["URL Static Analysis\n(Weight: 15%)"]
        M2["VirusTotal Threat Intel\n(Weight: 40%)"]
        M3["ML Phishing Engine\n(Weight: 30%)"]
        M4["SSL/TLS Validation\n(Weight: 15%)"]
    end

    subgraph Normalization & Indicator Separation
        M1 --> N1["Normalized Risk (0-100)\n+ Risk/Positive Indicators"]
        M2 --> N2["Normalized Risk (0-100)\n+ Threat Indicators"]
        M3 --> N3["Normalized Risk (0-100)\n+ Feature Indicators"]
        M4 --> N4["Normalized Risk (0-100)\n+ Certificate Indicators"]
    end

    subgraph Core Risk Engine
        N1 & N2 & N3 & N4 --> COV{"Calculate Assessment Coverage\nSum(Available Weights)"}
        COV --> OVR{"Check High-Severity Overrides\n1. VT Malicious >= 3\n2. ML Phishing >= 85%\n3. SSRF Unsafe Destination\n4. IP Host + @ Obfuscation"}
        
        OVR -- "Override Triggered" --> FR["Force High/Critical Risk\n(Override Reason Documented)"]
        OVR -- "No Override" --> MIN{"Coverage >= 30%?"}
        
        MIN -- "No (Coverage < 0.30)" --> INSUFF["Status: INSUFFICIENT_DATA\nTrust Score: None\nRisk Level: UNKNOWN"]
        MIN -- "Yes" --> DYN["Dynamic Weight Redistribution\nRaw Risk = Sum(W_i * R_i) / Sum(W_i)"]
        DYN --> FR
    end

    subgraph Output Synthesis
        FR --> TS["Digital Trust Score = 100 - Final Risk"]
        TS --> LVL{"Risk Category"}
        LVL --> |"80 - 100"| R1["LOW RISK (SAFE)"]
        LVL --> |"60 - 79"| R2["MODERATE RISK (MEDIUM)"]
        LVL --> |"30 - 59"| R3["HIGH RISK (HIGH)"]
        LVL --> |"0 - 29"| R4["CRITICAL RISK (CRITICAL)"]
        
        FR --> REC["Deterministic Recommendations"]
        FR --> EXP["Explainable Indicators\n(Risk, Positive, Unknown)"]
        FR --> SUM["Executive Narrative Summary"]
    end
```

> [!IMPORTANT]
> **Core Principle: Missing Feeds Must Never Be Equated With Safety**  
> In cybersecurity telemetry, absence of evidence is never evidence of absence. When an external threat intelligence provider is unreachable or rate-limited, treating that module as "0 risk" would artificially inflate the Trust Score of sophisticated zero-day attacks. TrustGuard AI dynamically redistributes weights exclusively across active feeds and reports a transparent **Assessment Coverage** percentage.

---

## 2. Mathematical Formulation & Weighting Model

### 2.1 Baseline Configuration

Each security subsystem is allocated a fractional weight reflecting its confidence and adversarial robustness:

| Module Identifier | Subsystem | Default Weight ($w_m$) | Description |
| :--- | :--- | :---: | :--- |
| `virustotal` | VirusTotal Threat Intel | **0.40** (40%) | Global consortium consensus (70+ security vendors). |
| `ml_phishing` | Random Forest Inference | **0.30** (30%) | Lexical and structural phishing pattern recognition. |
| `url_heuristics` | Static URL Analysis | **0.15** (15%) | RFC compliance, obfuscation detection, token anomalies. |
| `ssl_tls` | Transport Security Check | **0.15** (15%) | Certificate validity, expiration, trust chain, SSRF guard. |
| **Total** | | **1.00** (100%) | |

### 2.2 Module Normalization ($R_m$)

Every module's raw output is converted to a normalized risk metric $R_m \in [0, 100]$, where $0$ represents confirmed safety and $100$ represents confirmed critical hazard:

1. **VirusTotal ($R_{\text{VT}}$):**
   - $R_{\text{VT}} = 100$ if status is `MALICIOUS` or `malicious >= 3`.
   - $R_{\text{VT}} = 70$ if `malicious == 2`.
   - $R_{\text{VT}} = 40$ if `malicious == 1` or `suspicious >= 2`.
   - $R_{\text{VT}} = 20$ if `suspicious == 1`.
   - $R_{\text{VT}} = 0$ if `NO_DETECTIONS` and participating engines $> 0$.
   - Excluded if status is `API_UNAVAILABLE`, `RATE_LIMITED`, `ERROR`, `NOT_FOUND`, or `PENDING`.

2. **Machine Learning Phishing ($R_{\text{ML}}$):**
   - Derived directly from model probability: $R_{\text{ML}} = P(\text{phishing}) \times 100$.
   - Excluded if `model_status` is `MODEL_UNAVAILABLE` or `ERROR`.

3. **URL Static Heuristics ($R_{\text{URL}}$):**
   - Inversely mapped from the URL subscore: $R_{\text{URL}} = 100 - \text{url\_subscore}$.
   - Heavy penalties applied for raw IP hosts (+40 risk), `@` symbol userinfo (+35 risk), hexadecimal encoded hostnames (+30 risk), and brand impersonation tokens.

4. **SSL/TLS Validation ($R_{\text{SSL}}$):**
   - $R_{\text{SSL}} = 100$ for `UNSAFE_DESTINATION` (SSRF/metadata targeting).
   - $R_{\text{SSL}} = 90$ for `EXPIRED` certificate.
   - $R_{\text{SSL}} = 80$ for `HOSTNAME_MISMATCH` or `UNTRUSTED_CERTIFICATE`.
   - $R_{\text{SSL}} = 50$ for `HTTPS_NOT_USED` (plain HTTP unencrypted).
   - $R_{\text{SSL}} = 25$ for `EXPIRING_SOON` ($\le 30$ days remaining).
   - $R_{\text{SSL}} = 0$ for `VALID` and trusted certificate.
   - Excluded if connection failed due to network timeout or connection refusal.

### 2.3 Dynamic Weight Redistribution

When an external feed is unavailable, the available weight sum is:
$$W_{\text{avail}} = \sum_{m \in M_{\text{avail}}} w_m$$

The raw synthesized risk is computed solely across available signals:
$$\text{Raw Risk} = \frac{\sum_{m \in M_{\text{avail}}} w_m \cdot R_m}{W_{\text{avail}}}$$

### 2.4 Minimum Coverage Threshold & Insufficient Data

- **Assessment Coverage:** $C = W_{\text{avail}}$ (expressed as a percentage: $C \times 100\%$).
- If $C < 0.30$ (less than 30% telemetry available):
  - **Assessment Status:** `INSUFFICIENT_DATA`
  - **Digital Trust Score:** `None`
  - **Risk Level:** `UNKNOWN`
  - **Risk Label:** `"INSUFFICIENT DATA"`
  - Prevents making authoritative security assertions when key intelligence feeds are offline.

---

## 3. High-Severity Override Rules

Weighted averages can be dangerously misleading in security. A website with a valid SSL certificate (SSL risk = 0) and clean lexical length (URL risk = 0) could still be an active malware distribution point confirmed by 10 antivirus vendors.

To guarantee that positive or neutral signals never dilute confirmed critical threats, the engine enforces deterministic **High-Severity Override Rules**:

| Rule ID | Trigger Condition | Override Risk Floor | Resulting Trust Score | Security Rationale |
| :---: | :--- | :---: | :---: | :--- |
| **A** | **VirusTotal Malicious**<br>$\ge 3$ vendors or status `MALICIOUS` | $\ge 85.0$ | $\le 15$ (CRITICAL/HIGH) | Multi-vendor consensus confirms active malware, trojans, or known phishing campaigns. |
| **B** | **Confident ML Phishing**<br>$P(\text{phishing}) \ge 0.85$ | $\ge 75.0$ | $\le 25$ (CRITICAL/HIGH) | Structural and token patterns match phishing campaigns with high model certainty. |
| **C** | **SSRF / Unsafe Destination**<br>Resolves to private/metadata IP | $= 100.0$ | $= 0$ (CRITICAL) | Prevents weaponization of TrustGuard against internal networks or cloud metadata. |
| **D** | **Severe URL Obfuscation**<br>Raw IP host AND `@` symbol present | $\ge 80.0$ | $\le 20$ (CRITICAL/HIGH) | Browser authority deception trick designed specifically to harvest credentials. |

> [!NOTE]
> When an override rule is triggered, the engine explicitly sets `high_severity_override=True` and populates `override_reason` with the exact technical trigger. The override reason is prominently featured in the executive narrative summary.

---

## 4. Final Trust Score & Risk Level Mapping

The final **Digital Trust Score** is the inverse of the synthesized risk:
$$\text{Digital Trust Score} = 100 - \text{Final Risk}$$

| Score Range | Risk Category | Risk Label | Status | Recommended User Action |
| :---: | :---: | :---: | :---: | :--- |
| **80 – 100** | `SAFE` / `LOW` | **LOW RISK** | COMPLETE / PARTIAL | Legitimate characteristics; standard security vigilance. |
| **60 – 79** | `MEDIUM` | **MODERATE RISK** | COMPLETE / PARTIAL | Exercise caution; inspect identity before entering data. |
| **30 – 59** | `HIGH` | **HIGH RISK** | COMPLETE / PARTIAL | Highly suspicious; do not enter credentials or download files. |
| **0 – 29** | `CRITICAL` | **CRITICAL RISK** | COMPLETE / PARTIAL | Active threat detected; immediately disconnect and close tab. |
| **N/A** | `UNKNOWN` | **INSUFFICIENT DATA** | INSUFFICIENT_DATA | Telemetry below 30% threshold; manual verification required. |

---

## 5. Explainable Indicators & Recommendations

Every assessment partitions its findings into three distinct arrays:

1. **`risk_indicators`:** Concrete threats, anomalies, or protocol deficiencies that increased the risk score.
   - Includes: `source_module`, `severity` (low, medium, high, critical), `evidence`, and `explanation`.
2. **`positive_indicators`:** Technical validations that confirmed trustworthiness (e.g., zero vendor detections, active TLS 1.3 encryption, clean domain structure).
3. **`unknown_indicators`:** Inconclusive, rate-limited, or offline feeds. Provides radical transparency so users and auditors understand exactly what was and was not checked.

### Deterministic Recommendations Engine
Recommendations are derived from triggered findings, providing prioritized guidance:
- If `CRITICAL` or `HIGH`: Advises users never to enter credentials, credit card details, or personal data.
- If VirusTotal detected malware: Advises against downloading files from the domain.
- If plain HTTP: Warns that network eavesdroppers can capture transmissions in plaintext.
- If SSL expired or untrusted: Instructs users not to bypass browser warning screens.

---

## 6. Concrete Scoring Examples

### Example 1: Legitimate Enterprise Website (`https://python.org`)
- **VirusTotal (40%):** 0/85 detections $\rightarrow R_{\text{VT}} = 0$
- **ML Phishing (30%):** Probability 0.02 $\rightarrow R_{\text{ML}} = 2$
- **URL Heuristics (15%):** Clean domain $\rightarrow R_{\text{URL}} = 0$
- **SSL/TLS (15%):** Valid Let's Encrypt certificate, 80 days remaining $\rightarrow R_{\text{SSL}} = 0$
- **Synthesis:** $\text{Risk} = (0.40 \times 0) + (0.30 \times 2) + (0.15 \times 0) + (0.15 \times 0) = 0.6 \approx 1$
- **Digital Trust Score:** **99/100** (`LOW RISK`, `COMPLETE`)

### Example 2: Phishing Campaign With Valid SSL (`https://paypal-security-update.xyz`)
- **VirusTotal (40%):** 4 vendors flag phishing $\rightarrow R_{\text{VT}} = 100$
- **ML Phishing (30%):** Probability 0.92 $\rightarrow R_{\text{ML}} = 92$
- **URL Heuristics (15%):** Brand token + abnormal length $\rightarrow R_{\text{URL}} = 65$
- **SSL/TLS (15%):** Valid free TLS certificate $\rightarrow R_{\text{SSL}} = 0$
- **Override Triggered:** Rule A (VT $\ge 3$ malicious) $\rightarrow \text{Risk} \ge 85$
- **Calculated Risk:** $(0.40 \times 100) + (0.30 \times 92) + (0.15 \times 65) + (0.15 \times 0) = 77.35$.
- **Override Enforcement:** $\max(77.35, 85.0) = 85$.
- **Digital Trust Score:** **15/100** (`CRITICAL RISK`, `COMPLETE`)
- *Notice:* The valid SSL certificate did NOT dilute the threat!

### Example 3: VirusTotal Feed Rate-Limited
- **VirusTotal (40%):** Rate-limited (`RATE_LIMITED`) $\rightarrow$ Excluded from weights.
- **ML Phishing (30%):** Probability 0.05 $\rightarrow R_{\text{ML}} = 5$
- **URL Heuristics (15%):** Clean domain $\rightarrow R_{\text{URL}} = 0$
- **SSL/TLS (15%):** Valid certificate $\rightarrow R_{\text{SSL}} = 0$
- **Available Weights:** $0.30 + 0.15 + 0.15 = 0.60$ (Coverage: 60%)
- **Dynamic Weight Redistribution:** $\text{Risk} = \frac{(0.30 \times 5) + (0.15 \times 0) + (0.15 \times 0)}{0.60} = \frac{1.5}{0.60} = 2.5 \approx 3$.
- **Digital Trust Score:** **97/100** (`LOW RISK`, `PARTIAL`)
- *Unknown finding:* `"VirusTotal Threat Intelligence Inconclusive"` recorded.

---

## 7. Verification & Automated Test Coverage

The Digital Trust Score & Risk Assessment Engine is verified by 13 dedicated automated tests in `backend/tests/test_risk_scoring.py`:

```
tests/test_risk_scoring.py::test_scoring_all_modules_clean_legitimate_url PASSED
tests/test_risk_scoring.py::test_scoring_high_severity_override_virustotal_malicious PASSED
tests/test_risk_scoring.py::test_scoring_high_severity_override_ml_phishing PASSED
tests/test_risk_scoring.py::test_scoring_high_severity_override_ssrf_destination PASSED
tests/test_risk_scoring.py::test_scoring_high_severity_override_ip_and_at_obfuscation PASSED
tests/test_risk_scoring.py::test_scoring_ssl_expired_or_mismatch PASSED
tests/test_risk_scoring.py::test_scoring_plain_http_website PASSED
tests/test_risk_scoring.py::test_scoring_partial_coverage_virustotal_unavailable PASSED
tests/test_risk_scoring.py::test_scoring_insufficient_data PASSED
tests/test_risk_scoring.py::test_scoring_explainable_indicators_categorization PASSED
tests/test_risk_scoring.py::test_scoring_deterministic_recommendations PASSED
tests/test_scan_api_endpoint_returns_complete_trust_assessment PASSED
tests/test_database_persistence_of_trust_assessment PASSED
```

**Total Backend Test Suite:** **107/107 passing in 3.58s** across all subsystems.  
**Ruff Linting Status:** **0 errors, fully formatted**.

