-- ==============================================================================
-- TrustGuard AI — Migration 001: Initial Database Schema
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- Ensure pgcrypto extension is available for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. TABLE: users
-- Extends Supabase auth.users with application profile data
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id           UUID         PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email        TEXT         NOT NULL UNIQUE,
    full_name    TEXT,
    avatar_url   TEXT,
    scan_count   INTEGER      NOT NULL DEFAULT 0,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Trigger: Automatically update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_users_updated_at ON public.users;
CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ==============================================================================
-- 2. TABLE: scan_history
-- Records all URL scan requests and their processing lifecycle
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.scan_history (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID         REFERENCES public.users(id) ON DELETE SET NULL,
    submitted_url  TEXT         NOT NULL,
    normalized_url TEXT         NOT NULL,
    url_hash       VARCHAR(64)  NOT NULL,
    scan_status    VARCHAR(32)  NOT NULL DEFAULT 'pending'
                                CHECK (scan_status IN ('pending', 'processing', 'complete', 'error')),
    risk_level     VARCHAR(32)  CHECK (risk_level IS NULL OR risk_level IN ('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN')),
    trust_score    INTEGER      CHECK (trust_score IS NULL OR (trust_score BETWEEN 0 AND 100)),
    is_guest       BOOLEAN      NOT NULL DEFAULT FALSE,
    ip_address     INET,
    error_message  TEXT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    completed_at   TIMESTAMPTZ
);

-- Trigger: Automatically increment user scan_count when a non-guest scan is created
CREATE OR REPLACE FUNCTION public.handle_user_scan_counter()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_id IS NOT NULL AND NEW.is_guest = FALSE THEN
        UPDATE public.users
        SET scan_count = scan_count + 1
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_scan_created_increment_counter ON public.scan_history;
CREATE TRIGGER on_scan_created_increment_counter
    AFTER INSERT ON public.scan_history
    FOR EACH ROW EXECUTE FUNCTION public.handle_user_scan_counter();

-- ==============================================================================
-- 3. TABLE: scan_results
-- Stores deep analysis metrics, model predictions, and scoring explanations
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.scan_results (
    id                          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id                     UUID         NOT NULL UNIQUE REFERENCES public.scan_history(id) ON DELETE CASCADE,
    trust_score                 INTEGER      NOT NULL CHECK (trust_score BETWEEN 0 AND 100),
    overall_risk_level          VARCHAR(32)  NOT NULL CHECK (overall_risk_level IN ('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN')),
    
    -- Machine Learning Features & Output
    phishing_probability        FLOAT        CHECK (phishing_probability IS NULL OR (phishing_probability BETWEEN 0.0 AND 1.0)),
    ml_prediction               VARCHAR(32),
    ml_score                    INTEGER      CHECK (ml_score IS NULL OR (ml_score BETWEEN 0 AND 100)),
    ml_features                 JSONB,
    
    -- Threat Intelligence
    virustotal_detection_count  INTEGER      DEFAULT 0,
    virustotal_total_engines    INTEGER      DEFAULT 0,
    threat_intelligence_status  VARCHAR(32),
    vt_score                    INTEGER      CHECK (vt_score IS NULL OR (vt_score BETWEEN 0 AND 100)),
    vt_raw                      JSONB,
    
    -- SSL/TLS Validation
    ssl_status                  VARCHAR(64),
    ssl_valid                   BOOLEAN,
    ssl_issuer                  VARCHAR(255),
    ssl_expiry_date             TIMESTAMPTZ,
    ssl_days_remaining          INTEGER,
    ssl_score                   INTEGER      CHECK (ssl_score IS NULL OR (ssl_score BETWEEN 0 AND 100)),
    ssl_raw                     JSONB,
    
    -- URL Heuristics & Scoring Breakdown
    url_score                   INTEGER      CHECK (url_score IS NULL OR (url_score BETWEEN 0 AND 100)),
    url_risk_indicators         JSONB,
    score_breakdown             JSONB        NOT NULL,
    analysis_summary            TEXT,
    
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ==============================================================================
-- 4. TABLE: community_reports
-- User-contributed threat submissions and brand impersonation annotations
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.community_reports (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id              UUID         REFERENCES public.scan_history(id) ON DELETE CASCADE,
    user_id              UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    submitted_url        TEXT         NOT NULL,
    normalized_url       TEXT         NOT NULL,
    report_reason        VARCHAR(64)  NOT NULL CHECK (report_reason IN ('phishing', 'malware', 'scam', 'spam', 'impersonation', 'other')),
    report_status        VARCHAR(32)  NOT NULL DEFAULT 'pending_review'
                                      CHECK (report_status IN ('pending_review', 'verified', 'rejected')),
    verification_status  VARCHAR(32)  NOT NULL DEFAULT 'unverified'
                                      CHECK (verification_status IN ('unverified', 'verified', 'false_positive')),
    threat_type          VARCHAR(64),
    target_brand         VARCHAR(255),
    attack_vector        VARCHAR(64)  CHECK (attack_vector IS NULL OR attack_vector IN ('email', 'sms', 'social_media', 'ad', 'other')),
    notes                TEXT         CHECK (notes IS NULL OR char_length(notes) <= 1000),
    upvotes              INTEGER      NOT NULL DEFAULT 0,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ==============================================================================
-- 5. TABLE: threat_reports
-- Verified machine-collected threat intelligence records
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.threat_reports (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id              UUID         REFERENCES public.scan_history(id) ON DELETE CASCADE,
    normalized_url       TEXT,
    domain               VARCHAR(255),
    threat_source        VARCHAR(64)  NOT NULL CHECK (threat_source IN ('virustotal', 'urlhaus', 'internal_ml', 'community')),
    threat_category      VARCHAR(64),
    severity             VARCHAR(32)  NOT NULL DEFAULT 'medium'
                                      CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    verification_status  VARCHAR(32)  NOT NULL DEFAULT 'verified'
                                      CHECK (verification_status IN ('verified', 'unverified', 'disputed')),
    first_seen_at        TIMESTAMPTZ,
    last_seen_at         TIMESTAMPTZ,
    raw_data             JSONB,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ==============================================================================
-- 6. INDEXES FOR PERFORMANCE & DEDUPLICATION
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_scan_history_user_id ON public.scan_history(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_url_hash ON public.scan_history(url_hash);
CREATE INDEX IF NOT EXISTS idx_scan_history_created_at ON public.scan_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_results_risk_level ON public.scan_results(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_scan_results_trust_score ON public.scan_results(trust_score);
CREATE INDEX IF NOT EXISTS idx_community_reports_scan_id ON public.community_reports(scan_id);
CREATE INDEX IF NOT EXISTS idx_community_reports_url ON public.community_reports(normalized_url);
CREATE INDEX IF NOT EXISTS idx_community_reports_status ON public.community_reports(report_status);
CREATE INDEX IF NOT EXISTS idx_threat_reports_url ON public.threat_reports(normalized_url);
CREATE INDEX IF NOT EXISTS idx_threat_reports_domain ON public.threat_reports(domain);

