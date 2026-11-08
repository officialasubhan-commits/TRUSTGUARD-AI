# TrustGuard AI — Developer Contributing Guide

Welcome to **TrustGuard AI**! This guide outlines the development standards, code quality checks, and collaboration workflows for our 48-hour hackathon team.

---

## 1. Team Roles & Module Ownership

| Role | Primary Responsibilities | Core File Paths |
| :--- | :--- | :--- |
| **Backend & DB Architect** | FastAPI architecture, Supabase connection, RLS migrations, scan repositories | `app/main.py`, `app/database/`, `migrations/`, `app/api/v1/router.py` |
| **Security & Threat Intel Engineer** | SSRF defenses, VirusTotal v3 integration, SSL/TLS validator, rate limiting | `app/services/virustotal_service.py`, `app/services/ssl_tls_service.py`, `app/core/security.py` |
| **ML & Risk Scoring Engineer** | Random forest classifier, dataset curation, Digital Trust Score engine | `app/services/ml_detection_service.py`, `app/services/risk_scoring_service.py`, `ml/` |
| **Integration & QA Engineer** | Automated Pytest suites, API schemas, OpenAPI documentation, frontend handoff | `tests/`, `app/schemas/`, `docs/`, `backend/README.md` |

---

## 2. Local Development Setup (Windows PowerShell)

```powershell
# 1. Activate virtual environment
cd D:\HackMatrix'26\backend
.\.venv\Scripts\Activate.ps1

# 2. Verify dependencies
python -m pip install -r requirements.txt

# 3. Verify linting & code formatting
python -m ruff check .
python -m ruff format --check .

# 4. Run automated test suite
python -m pytest tests -v
```

---

## 3. Git & Branching Conventions

- **Main Branch:** `main` (always protected, must pass all 145 tests).
- **Feature Branches:** Use descriptive names:
  - `feat/ml-phishing-enhancement`
  - `feat/community-reporting-ui`
  - `fix/ssrf-dns-timeout`
  - `docs/api-specification-update`
- **Commit Messages:** Follow Conventional Commits:
  - `feat: implement parallel SSL and VirusTotal analysis`
  - `fix: resolve IDOR boundary on scan history endpoint`
  - `test: add end-to-end integration and security test suite`
  - `docs: update API documentation with complete schema examples`

---

## 4. Code Quality & Formatting Standards

- **Python Version:** 3.11+
- **Linter & Formatter:** [Ruff](https://github.com/astral-sh/ruff)
  ```powershell
  # Format code automatically
  python -m ruff format .

  # Run static analysis
  python -m ruff check .
  ```
- **Zero-Warning Policy:** Code must produce 0 errors on `ruff check .` before committing.
- **Type Annotations:** All endpoint handlers, service methods, and repository operations must include explicit Python type hints and Pydantic models.

---

## 5. Testing Requirements

- Every new feature or endpoint must include automated test coverage in `backend/tests/`.
- Mock external network calls (VirusTotal, Supabase) using repository fallbacks or mocks.
- **Pre-Push Command:**
  ```powershell
  python -m pytest tests -v
  ```
  Ensure all tests pass and execution time remains under 10 seconds.

