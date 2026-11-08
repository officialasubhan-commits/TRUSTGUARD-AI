# TrustGuard AI — Project Overview

> **Hackathon:** HackMatrix '26 | **Track:** Cybersecurity / AI  
> **Team Size:** 4 Developers | **Duration:** 48 Hours

---

## Executive Summary

TrustGuard AI is a **real-time URL threat analysis platform** that empowers everyday internet users to verify the safety of any link before they click it. By fusing traditional threat-intelligence feeds with modern machine-learning inference, TrustGuard AI produces a single, human-readable **Digital Trust Score** (0–100) that tells users, at a glance, whether a URL is safe, suspicious, or outright malicious.

### Why It Matters

Phishing attacks remain the single most common vector for credential theft, ransomware delivery, and financial fraud worldwide. Industry reports consistently show that more than 90 % of successful cyberattacks begin with a phishing link, yet most users have no accessible tool to evaluate a URL before visiting it. Browser extensions exist but require installation and trust; antivirus software is reactive rather than proactive. TrustGuard AI fills this gap by offering a **zero-install, cloud-hosted, API-driven** safety check that any user can invoke from a browser in seconds.

---

## Target Audience

| Audience | Use Case |
|---|---|
| General internet users | Verify suspicious links received via email, SMS, or social media |
| Small-business employees | Quick sanity-check before entering credentials on an unfamiliar site |
| Developers & researchers | Programmatic URL scanning via REST API |
| Security-aware students | Educational tool to learn what makes a URL suspicious |
| Hackathon judges | Demonstration of full-stack AI-driven security tooling in 48 hours |

---

## Core Value Proposition

- 🔍 **Multi-layered analysis** — Combines VirusTotal threat intelligence, URLhaus blocklists, ML-based phishing prediction, SSL/TLS certificate inspection, and URL heuristics into one unified verdict, eliminating single-point-of-failure false negatives.
- ⚡ **Real-time results in under 10 seconds** — Parallel async execution of all analysis services ensures users receive actionable information without long waits.
- 🛡️ **Transparent scoring** — Every point deducted from the Digital Trust Score is accompanied by a human-readable explanation, so users understand *why* a URL is flagged, not just *that* it was flagged.
- 🌐 **Zero-install, any-device access** — Fully web-hosted React SPA means users need only a browser; no extension, no desktop app, no account required for guest scans.
- 🤝 **Community-powered threat reporting** — Registered users can submit additional threat context, turning the platform into a crowd-sourced safety layer that improves over time.

---

## Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts | Fast dev iteration, component reuse, modern styling without custom CSS overhead |
| **Backend** | Python 3.11, FastAPI, Uvicorn | Async-native, auto-generated OpenAPI docs, Pydantic validation built-in |
| **AI / ML** | scikit-learn (Random Forest), pandas, numpy | Mature, well-documented; Random Forest handles mixed tabular features robustly |
| **Database / Auth** | Supabase (PostgreSQL + Auth + RLS) | Managed Postgres with built-in Row Level Security and JWT authentication; zero ops overhead |
| **Threat Intelligence** | VirusTotal API v3, URLhaus API | Industry-standard threat feeds; free tiers sufficient for hackathon scale |
| **Security Analysis** | Python `ssl`, `cryptography`, `socket` stdlib | Native SSL certificate inspection without heavyweight dependencies |
| **Deployment** | Render (backend), Vercel (frontend) | Free-tier friendly, GitHub-integrated CI/CD, global CDN |

---

## Key Features

1. **Real-Time URL Scanning** — Submit any URL and receive a full analysis report within seconds, powered by parallel async service execution.
2. **Digital Trust Score (0–100)** — A weighted composite score (VirusTotal 40 %, ML 30 %, SSL 15 %, URL Heuristics 15 %) that distils complex threat data into one number.
3. **VirusTotal Integration** — Queries 70+ antivirus engines and URL scanners via the VirusTotal API v3, surfacing engine-level verdicts.
4. **ML-Based Phishing Detection** — A pre-trained Random Forest classifier extracts 20+ lexical and structural URL features to predict phishing probability independent of blocklists.
5. **SSL/TLS Certificate Inspection** — Checks certificate validity, expiry, issuer trustworthiness, and protocol version to flag impersonation and expired-cert risks.
6. **URL Heuristics Engine** — Analyses URL structure for red flags: excessive subdomains, IP-literal hostnames, homograph characters, suspicious TLDs, and abnormal path depth.
7. **Scan History & Dashboard** — Authenticated users see a personal history of all scans, with trend charts and risk-category breakdowns.
8. **Community Threat Reports** — Users can annotate scans with additional context (phishing type, targeted brand, attack vector) that is shared with the whole community.
9. **Guest Access Mode** — Unauthenticated visitors can perform scans without registering, lowering the barrier to entry while still persisting results for the session.

---

## Hackathon Scope

### ✅ Mandatory (Must Ship in 48 Hours)

- [ ] User registration and login via Supabase Auth
- [ ] URL submission form with validation
- [ ] VirusTotal API integration
- [ ] ML phishing predictor (pre-trained model loaded at startup)
- [ ] SSL/TLS certificate checker
- [ ] URL heuristics feature extractor
- [ ] Digital Trust Score calculation engine
- [ ] Scan result persistence in PostgreSQL (via Supabase)
- [ ] Scan history page for authenticated users
- [ ] Guest scan support (no login required)
- [ ] Responsive UI (desktop + mobile)
- [ ] Deployment: Render backend + Vercel frontend

### 🌟 Optional (Nice-to-Have, If Time Permits)

- [ ] URLhaus integration (secondary threat feed)
- [ ] Community reports module (submit + browse)
- [ ] Dashboard with Recharts visualisations (pie chart, line chart)
- [ ] Export report as PDF
- [ ] Email alert when a previously-safe URL is later flagged
- [ ] Dark mode toggle
- [ ] Admin panel for reviewing community reports

---

## Team Composition

| Role | Developer | Key Skills | Primary Ownership |
|---|---|---|---|
| Backend & API Lead | Developer 1 | FastAPI, Python, DevOps | `backend/app/api/`, `backend/app/core/`, deployment |
| AI / ML Engineer | Developer 2 | scikit-learn, pandas, feature engineering | `backend/app/services/ml_service.py`, `backend/app/ml/` |
| Frontend Engineer | Developer 3 | React, Tailwind, Supabase JS | Entire `frontend/` directory |
| Threat Intelligence & Integration | Developer 4 | APIs, SSL, scoring logic, DB | `backend/app/services/` (VT, URLhaus, SSL, scoring), Supabase schema |

> **Experience Level:** All team members are at beginner-to-intermediate level. Architecture decisions deliberately favour simplicity, well-documented libraries, and avoid premature optimisation.

---

## Architecture Philosophy

### 1. Modular by Design
Every analysis capability (VirusTotal, ML, SSL, Heuristics) lives in its own service module with a clearly defined async interface. Services are independently testable, deployable, and replaceable. If the VirusTotal API goes down, the other three services still produce a partial score.

### 2. Beginner-Friendly Patterns
- No microservices — single FastAPI monolith simplifies debugging and deployment.
- No message queues — synchronous async/await with `asyncio.gather` is sufficient for hackathon concurrency needs.
- Supabase eliminates the need to manage Postgres, Auth, or RLS configuration from scratch.
- React with Vite and Tailwind requires minimal boilerplate.

### 3. Secure by Design
Security is not an afterthought. SSRF protection, input validation, JWT verification, and Row Level Security are planned and implemented from hour zero, not bolted on at the end. See [SECURITY_DESIGN.md](./SECURITY_DESIGN.md) for the full threat model.

### 4. Independently Testable Modules
Each service module has a corresponding test file in `backend/tests/`. Unit tests use mocked external API responses so tests do not require live API keys or network access. This allows Developer 2 to test ML logic while Developer 4 tests SSL logic without coordination.

### 5. API-First
The backend exposes a versioned REST API (`/api/v1/`) documented in [API_SPECIFICATION.md](./API_SPECIFICATION.md). The frontend is a pure consumer of this API. This separation means the frontend and backend can be developed, tested, and deployed independently.

---

## Related Documentation

| Document | Contents |
|---|---|
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | Full system diagram, component hierarchy, folder structure |
| [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) | Schema, ERD, DDL, RLS policies |
| [API_SPECIFICATION.md](./API_SPECIFICATION.md) | Endpoint contracts, request/response models |
| [SECURITY_DESIGN.md](./SECURITY_DESIGN.md) | Threat model, SSRF guard, security checklist |
| [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) | 48-hour sprint plan, team matrix, scoring methodology |
