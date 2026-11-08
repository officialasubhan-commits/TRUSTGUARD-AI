# TrustGuard AI — Security Architecture & Threat Model

**Version:** 1.0.0  
**Last Updated:** 2026-11-07  
**Scope:** TrustGuard AI Backend API, Analysis Engines, and Database Layers

---

## 1. Security Architecture & Core Tenets

TrustGuard AI is designed with **defense-in-depth**, **least privilege**, and **fail-safe defaults**:
1. **Never Execute Target Content:** The backend statically analyzes URLs and extracts cryptographic/lexical telemetry. It NEVER renders HTML, downloads client-side scripts, executes JavaScript, or uses headless browsers to browse untrusted websites.
2. **Untrusted User Telemetry Decoupling:** Crowdsourced community threat reports are treated as non-authoritative evidence. They can never autonomously alter Digital Trust Scores or classify domains as malicious without administrative verification.
3. **Strict Boundaries on Outbound Traffic:** Outbound network requests are limited to port 443 for TLS certificate handshakes and trusted third-party APIs (VirusTotal, Supabase).

---

## 2. Server-Side Request Forgery (SSRF) Defenses

To prevent malicious actors from using TrustGuard AI as a proxy to port-scan or exfiltrate sensitive cloud metadata:

### A. Static IP and Hostname Validation
All submitted URLs pass through `validate_url_static()` in `app/services/url_validator.py` before any network activity:
- **Private IP Networks Blocked:**
  - RFC 1918 Private IPv4: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
  - Loopback: `127.0.0.0/8`, `::1/128`
  - APIPA / Link-Local: `169.254.0.0/16`, `fe80::/10`
  - Shared & Carrier-Grade NAT: `100.64.0.0/10`
  - Documentation Networks: `198.51.100.0/24`, `203.0.113.0/24`
  - Multicast & Reserved: `224.0.0.0/4`, `240.0.0.0/4`
- **Cloud Metadata & Internal Hostnames Blocked:**
  - `169.254.169.254` (AWS, GCP, Azure, OpenStack instance metadata)
  - `metadata.google.internal`
  - `metadata.azure.com`
  - `localhost`, `localhost.localdomain`

### B. DNS Resolution & Rebinding Prevention
In `app/services/ssl_tls_service.py`:
1. The hostname is resolved via `socket.getaddrinfo()`.
2. Every resolved IP address is verified against private IP filters.
3. The socket connects directly to the validated IP address, with the original domain supplied exclusively in the TLS Server Name Indication (SNI) extension. This eliminates Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks.

---

## 3. Authentication & Authorization (RBAC)

### A. Cryptographic JWT Verification
- Bearer tokens are validated for signature integrity (`HS256`), expiration (`exp`), and audience (`aud`).
- User identities are derived strictly from token payload (`sub` claim). Client-supplied user IDs in request bodies are ignored.

### B. Role-Based Access Control
- **`user`:** Accesses personal scan history, submits reports, queries public verified reports.
- **`admin`:** Moderates community reports, updates verification states, accesses administrative review queues. Enforced via `require_admin_user` dependency (raises `403 Forbidden` on non-admin users).

### C. Insecure Direct Object Reference (IDOR) Mitigation
- **Private Scan Isolation:** Authenticated users can only retrieve, view, or delete scans where `scan.user_id == current_user.user_id`.
- **Anti-Enumeration 404s:** Attempting to query an unapproved community report or another user's scan returns `404 Not Found` (rather than `403 Forbidden`) to prevent attackers from mapping valid resource identifiers.

---

## 4. Secrets Management & Operational Security

- **Repository Hygiene:** All `.env` and credential files are strictly excluded via `.gitignore`.
- **Placeholder Templates:** `.env.example` contains only benign placeholders and descriptive instructions.
- **Log Sanitization:** API keys, database connection strings, and authorization tokens are redacted from application log files.
- **Error Envelopes:** Centralized exception handlers catch all internal server errors and return clean JSON envelopes (`{"error": {"code": ..., "message": ...}}`). Stack traces, line numbers, and file paths are NEVER returned to HTTP clients.

---

## 5. Known Security Limitations & Future Hardening

1. **In-Memory Caching in Decoupled Mode:** In local development mode without Redis, rate-limiting and VirusTotal response caches reside in memory and reset on process restart. Production deployment should configure Redis for distributed rate-limiting.
2. **Third-Party API Rate Limits:** VirusTotal free-tier is restricted to 4 req/min. When exhausted, the system transparently marks the feed `RATE_LIMITED` and dynamically recalculates weights across available telemetry without failing the scan.
3. **Email Verification:** In local decoupled testing, email confirmation checks are bypassed for rapid developer iteration. Production Supabase Auth should enforce mandatory email confirmation.

