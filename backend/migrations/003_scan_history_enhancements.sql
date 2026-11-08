-- ==============================================================================
-- TrustGuard AI — Migration 003: Scan History & Report Management Enhancements
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Extend public.scan_history with domain, score breakdown metrics, and versioning
ALTER TABLE public.scan_history
    ADD COLUMN IF NOT EXISTS domain VARCHAR(255),
    ADD COLUMN IF NOT EXISTS risk_score INTEGER CHECK (risk_score IS NULL OR (risk_score BETWEEN 0 AND 100)),
    ADD COLUMN IF NOT EXISTS assessment_status VARCHAR(32),
    ADD COLUMN IF NOT EXISTS assessment_coverage FLOAT CHECK (assessment_coverage IS NULL OR (assessment_coverage BETWEEN 0.0 AND 1.0)),
    ADD COLUMN IF NOT EXISTS scoring_version VARCHAR(32);

-- 2. Backfill domain from normalized_url for existing scan records
UPDATE public.scan_history
SET domain = substring(normalized_url from 'https?://([^/:]+)')
WHERE domain IS NULL;

-- 3. Composite and single-column indexes for fast server-side filtering, sorting & pagination
CREATE INDEX IF NOT EXISTS idx_scan_history_domain ON public.scan_history(domain);
CREATE INDEX IF NOT EXISTS idx_scan_history_risk_level ON public.scan_history(risk_level);
CREATE INDEX IF NOT EXISTS idx_scan_history_status ON public.scan_history(scan_status);
CREATE INDEX IF NOT EXISTS idx_scan_history_user_created ON public.scan_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_history_user_score ON public.scan_history(user_id, trust_score DESC);

-- 4. Row Level Security Policy for Authenticated Scan Deletion
DROP POLICY IF EXISTS "Users delete own scan history" ON public.scan_history;
CREATE POLICY "Users delete own scan history"
    ON public.scan_history
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id AND is_guest = FALSE);

