# TrustGuard AI — Dataset Documentation & Provenance

**Document Version:** 1.0.0  
**Dataset Artifact:** `backend/ml/data/phishing_dataset.csv`  
**Creation Date:** November 2026  
**License:** Open / Non-Commercial Research & Educational Use  

---

## 1. Overview & Objective

The primary objective of this dataset is to train and benchmark the machine-learning component of TrustGuard AI to distinguish between **legitimate web destinations** and **phishing / credential harvesting attacks** based strictly on structural and lexical URL characteristics.

---

## 2. Dataset Sources & Provenance

The dataset comprises **1,636 verified URL records** divided into two ground-truth classes:

### 2.1 Class 1 — Phishing (566 records, 34.6%)
- **Source A — OpenPhish Free Community Feed:** 300 live, verified active zero-day phishing URLs fetched dynamically from OpenPhish (`https://openphish.com/feed.txt`).
- **Source B — Security Research Benchmarks & PhishTank Verified Targets:** Verified credential harvesting domains, homoglyph punycode attacks, raw IP address hosts, userinfo `@` obfuscations, and dynamic DNS subdomains impersonating financial and cloud platforms (Chase, Bank of America, Apple ID, PayPal, Netflix, Microsoft Office 365, Google Accounts).

### 2.2 Class 0 — Legitimate (1,070 records, 65.4%)
- **Source A — Verified Global Top Infrastructure:** Highly authoritative government (`.gov`, `.gov.uk`), educational (`.edu`, `.ac.jp`, `.ac.uk`), scientific (`nih.gov`, `cdc.gov`, `arxiv.org`, `nist.gov`), and developer documentation sites (`developer.mozilla.org`, `docs.python.org`, `docs.pydantic.dev`).
- **Source B — Top Commercial & Financial Services:** Authorized domains for major tech platforms, payment networks, and banks (`google.com`, `apple.com`, `microsoft.com`, `chase.com`, `paypal.com`, `amazon.com`).

---

## 3. Data Preprocessing & Hygiene

1. **RFC 3986 Canonical Normalization:** Every URL is processed through `app.utils.url_normalizer.normalize_url` (lowercasing schemes and hostnames, stripping default ports `:80` and `:443`, stripping trailing host dots).
2. **Deduplication:** Duplicates are strictly removed using a unique URL set.
3. **Collision Elimination:** No URL is permitted to exist in both the legitimate and phishing classes.
4. **Binary Label Encoding:**
   - `0 = legitimate`
   - `1 = phishing`
5. **No Data Leakage:** Target labels are stored separately from input features. Feature extraction relies exclusively on `URLAnalyzer` from Prompt 05.

---

## 4. Class Balance & Sampling Strategy

- **Total records:** 1,636
- **Legitimate:** 1,070 (65.4%)
- **Phishing:** 566 (34.6%)
- **Evaluation Strategy:** Stratified $k$-fold cross-validation or stratified train/test split ($80\%$ train, $20\%$ test) is applied to ensure proportional class representation across splits.

---

## 5. Limitations & Ethical Safeguards

1. **Lexical Domain Only:** The model evaluates URL structure and domain heuristics. It does not inspect HTTP response bodies, DOM contents, or dynamic JavaScript execution.
2. **Lag Against Novel TLDs:** Newly registered phishing domains utilizing obscure TLDs not captured in training data may produce false negatives, which is why VirusTotal threat intelligence and SSL validation run concurrently in the TrustGuard AI defense pipeline.
3. **No Direct Navigation:** Training scripts process URLs offline without visiting live target servers.

