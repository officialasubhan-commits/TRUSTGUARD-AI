-- ==============================================================================
-- TrustGuard AI — Complete Consolidated Production Schema (Migration 000)
-- Target Database: PostgreSQL 15+ (Supabase)
-- 
-- Consolidates Migrations 001, 002, 003, and 004 into an idempotent,
-- production-ready script for execution in the Supabase SQL Editor.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- EXTENSIONS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. TABLE: users
-- Extends Supabase auth.users with application profile data
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 2. TABLE: scan_history
-- Records all URL scan requests and their processing lifecycle
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.scan_history (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID         REFERENCES public.users(id) ON DELETE SET NULL,
    submitted_url        TEXT         NOT NULL,
    normalized_url       TEXT         NOT NULL,
    domain               VARCHAR(255),
    url_hash             VARCHAR(64)  NOT NULL,
    scan_status          VARCHAR(32)  NOT NULL DEFAULT 'pending'
                                      CHECK (scan_status IN ('pending', 'processing', 'complete', 'error')),
    risk_level           VARCHAR(32)  CHECK (risk_level IS NULL OR risk_level IN ('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN')),
    trust_score          INTEGER      CHECK (trust_score IS NULL OR (trust_score BETWEEN 0 AND 100)),
    risk_score           INTEGER      CHECK (risk_score IS NULL OR (risk_score BETWEEN 0 AND 100)),
    assessment_status    VARCHAR(32),
    assessment_coverage  FLOAT        CHECK (assessment_coverage IS NULL OR (assessment_coverage BETWEEN 0.0 AND 1.0)),
    scoring_version      VARCHAR(32),
    is_guest             BOOLEAN      NOT NULL DEFAULT FALSE,
    ip_address           INET,
    error_message        TEXT,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    completed_at         TIMESTAMPTZ
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

-- ------------------------------------------------------------------------------
-- 3. TABLE: scan_results
-- Stores deep analysis metrics, model predictions, and scoring explanations
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 4. TABLE: community_reports
-- User-contributed threat submissions and brand impersonation annotations
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.community_reports (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id              UUID         REFERENCES public.scan_history(id) ON DELETE CASCADE,
    user_id              UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    submitted_url        TEXT         NOT NULL,
    normalized_url       TEXT         NOT NULL,
    domain               VARCHAR(255),
    report_reason        VARCHAR(64)  NOT NULL,
    report_status        VARCHAR(32)  NOT NULL DEFAULT 'pending_review',
    verification_status  VARCHAR(32)  NOT NULL DEFAULT 'unverified',
    moderation_status    VARCHAR(32)  NOT NULL DEFAULT 'PENDING',
    moderation_notes     TEXT,
    moderator_id         UUID         REFERENCES public.users(id) ON DELETE SET NULL,
    reviewed_at          TIMESTAMPTZ,
    threat_type          VARCHAR(64),
    target_brand         VARCHAR(255),
    attack_vector        VARCHAR(64),
    description          TEXT,
    evidence_url         TEXT,
    notes                TEXT         CHECK (notes IS NULL OR char_length(notes) <= 1000),
    upvotes              INTEGER      NOT NULL DEFAULT 0,
    duplicate_of         UUID         REFERENCES public.community_reports(id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS set_community_reports_updated_at ON public.community_reports;
CREATE TRIGGER set_community_reports_updated_at
    BEFORE UPDATE ON public.community_reports
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 5. TABLE: threat_reports
-- Verified machine-collected threat intelligence records
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 6. PERFORMANCE & QUERY INDEXES
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

CREATE INDEX IF NOT EXISTS idx_scan_history_user_id ON public.scan_history(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_url_hash ON public.scan_history(url_hash);
CREATE INDEX IF NOT EXISTS idx_scan_history_domain ON public.scan_history(domain);
CREATE INDEX IF NOT EXISTS idx_scan_history_risk_level ON public.scan_history(risk_level);
CREATE INDEX IF NOT EXISTS idx_scan_history_status ON public.scan_history(scan_status);
CREATE INDEX IF NOT EXISTS idx_scan_history_created_at ON public.scan_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_history_user_created ON public.scan_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_history_user_score ON public.scan_history(user_id, trust_score DESC);

CREATE INDEX IF NOT EXISTS idx_scan_results_risk_level ON public.scan_results(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_scan_results_trust_score ON public.scan_results(trust_score);

CREATE INDEX IF NOT EXISTS idx_community_reports_scan_id ON public.community_reports(scan_id);
CREATE INDEX IF NOT EXISTS idx_community_reports_url ON public.community_reports(normalized_url);
CREATE INDEX IF NOT EXISTS idx_community_reports_domain ON public.community_reports(domain);
CREATE INDEX IF NOT EXISTS idx_community_reports_mod_status ON public.community_reports(moderation_status);
CREATE INDEX IF NOT EXISTS idx_community_reports_created ON public.community_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_reports_user_created ON public.community_reports(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_reports_duplicate_of ON public.community_reports(duplicate_of);

CREATE INDEX IF NOT EXISTS idx_threat_reports_url ON public.threat_reports(normalized_url);
CREATE INDEX IF NOT EXISTS idx_threat_reports_domain ON public.threat_reports(domain);

-- ------------------------------------------------------------------------------
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ------------------------------------------------------------------------------

-- Enable RLS across all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threat_reports ENABLE ROW LEVEL SECURITY;

-- 7.1 users policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT TO authenticated
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Service role manages all users" ON public.users;
CREATE POLICY "Service role manages all users"
    ON public.users FOR ALL TO service_role
    USING (TRUE) WITH CHECK (TRUE);

-- 7.2 scan_history policies
DROP POLICY IF EXISTS "Users view own scan history" ON public.scan_history;
CREATE POLICY "Users view own scan history"
    ON public.scan_history FOR SELECT TO authenticated
    USING (auth.uid() = user_id AND is_guest = FALSE);

DROP POLICY IF EXISTS "Users insert own scans" ON public.scan_history;
CREATE POLICY "Users insert own scans"
    ON public.scan_history FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id AND is_guest = FALSE);

DROP POLICY IF EXISTS "Users delete own scan history" ON public.scan_history;
CREATE POLICY "Users delete own scan history"
    ON public.scan_history FOR DELETE TO authenticated
    USING (auth.uid() = user_id AND is_guest = FALSE);

DROP POLICY IF EXISTS "Service role manages all scan history" ON public.scan_history;
CREATE POLICY "Service role manages all scan history"
    ON public.scan_history FOR ALL TO service_role
    USING (TRUE) WITH CHECK (TRUE);

-- 7.3 scan_results policies
DROP POLICY IF EXISTS "Users view own scan results" ON public.scan_results;
CREATE POLICY "Users view own scan results"
    ON public.scan_results FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.scan_history sh
            WHERE sh.id = scan_results.scan_id
              AND sh.user_id = auth.uid()
              AND sh.is_guest = FALSE
        )
    );

DROP POLICY IF EXISTS "Service role manages all scan results" ON public.scan_results;
CREATE POLICY "Service role manages all scan results"
    ON public.scan_results FOR ALL TO service_role
    USING (TRUE) WITH CHECK (TRUE);

-- 7.4 community_reports policies
DROP POLICY IF EXISTS "Public view approved community reports" ON public.community_reports;
CREATE POLICY "Public view approved community reports"
    ON public.community_reports FOR SELECT TO public
    USING (moderation_status IN ('APPROVED', 'verified') OR report_status = 'verified' OR verification_status = 'verified');

DROP POLICY IF EXISTS "Users view own community reports" ON public.community_reports;
CREATE POLICY "Users view own community reports"
    ON public.community_reports FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Authenticated users submit community reports" ON public.community_reports;
CREATE POLICY "Authenticated users submit community reports"
    ON public.community_reports FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users update own pending community reports" ON public.community_reports;
CREATE POLICY "Users update own pending community reports"
    ON public.community_reports FOR UPDATE TO authenticated
    USING (auth.uid() = user_id AND moderation_status IN ('PENDING', 'pending_review'))
    WITH CHECK (auth.uid() = user_id AND moderation_status IN ('PENDING', 'pending_review'));

DROP POLICY IF EXISTS "Service role manages community reports" ON public.community_reports;
CREATE POLICY "Service role manages community reports"
    ON public.community_reports FOR ALL TO service_role
    USING (TRUE) WITH CHECK (TRUE);

-- 7.5 threat_reports policies
DROP POLICY IF EXISTS "Public view verified threat intelligence" ON public.threat_reports;
CREATE POLICY "Public view verified threat intelligence"
    ON public.threat_reports FOR SELECT TO public
    USING (verification_status = 'verified');

DROP POLICY IF EXISTS "Service role manages threat intelligence" ON public.threat_reports;
CREATE POLICY "Service role manages threat intelligence"
    ON public.threat_reports FOR ALL TO service_role
    USING (TRUE) WITH CHECK (TRUE);

