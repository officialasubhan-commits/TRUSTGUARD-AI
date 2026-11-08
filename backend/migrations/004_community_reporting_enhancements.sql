-- ==============================================================================
-- TrustGuard AI — Migration 004: Community Threat Reporting & Moderation Enhancements
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Extend public.community_reports with domain, moderation workflow, and evidence tracking
ALTER TABLE public.community_reports
    ADD COLUMN IF NOT EXISTS domain VARCHAR(255),
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS evidence_url TEXT,
    ADD COLUMN IF NOT EXISTS moderation_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS moderation_notes TEXT,
    ADD COLUMN IF NOT EXISTS moderator_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS duplicate_of UUID REFERENCES public.community_reports(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- 2. Relax legacy check constraints to allow new standard enum values
DO $$
BEGIN
    ALTER TABLE public.community_reports DROP CONSTRAINT IF EXISTS community_reports_report_reason_check;
    ALTER TABLE public.community_reports DROP CONSTRAINT IF EXISTS community_reports_report_status_check;
    ALTER TABLE public.community_reports DROP CONSTRAINT IF EXISTS community_reports_verification_status_check;
EXCEPTION
    WHEN undefined_object THEN NULL;
END $$;

-- 3. Backfill existing records: populate domain, description, and sync moderation_status
UPDATE public.community_reports
SET domain = substring(normalized_url from 'https?://([^/:]+)')
WHERE domain IS NULL AND normalized_url IS NOT NULL;

UPDATE public.community_reports
SET description = notes
WHERE description IS NULL AND notes IS NOT NULL;

UPDATE public.community_reports
SET moderation_status = CASE
    WHEN report_status = 'verified' THEN 'APPROVED'
    WHEN report_status = 'rejected' THEN 'REJECTED'
    ELSE 'PENDING'
END
WHERE moderation_status = 'PENDING' AND report_status IS NOT NULL;

-- 4. Fast lookup and filtering indexes
CREATE INDEX IF NOT EXISTS idx_community_reports_domain ON public.community_reports(domain);
CREATE INDEX IF NOT EXISTS idx_community_reports_mod_status ON public.community_reports(moderation_status);
CREATE INDEX IF NOT EXISTS idx_community_reports_norm_url ON public.community_reports(normalized_url);
CREATE INDEX IF NOT EXISTS idx_community_reports_created ON public.community_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_reports_user_created ON public.community_reports(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_reports_duplicate_of ON public.community_reports(duplicate_of);

-- 5. Row Level Security Policies
-- Enable RLS
ALTER TABLE public.community_reports ENABLE ROW LEVEL SECURITY;

-- Public can read approved / verified reports (anonymized via views or API layer)
DROP POLICY IF EXISTS "Public view approved community reports" ON public.community_reports;
CREATE POLICY "Public view approved community reports"
    ON public.community_reports
    FOR SELECT
    TO public
    USING (moderation_status IN ('APPROVED', 'verified'));

-- Authenticated users can view all their own submissions (regardless of moderation status)
DROP POLICY IF EXISTS "Users view own community reports" ON public.community_reports;
CREATE POLICY "Users view own community reports"
    ON public.community_reports
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Authenticated users can insert their own reports
DROP POLICY IF EXISTS "Authenticated users submit community reports" ON public.community_reports;
CREATE POLICY "Authenticated users submit community reports"
    ON public.community_reports
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Authenticated users can edit notes on own pending reports
DROP POLICY IF EXISTS "Users update own pending community reports" ON public.community_reports;
CREATE POLICY "Users update own pending community reports"
    ON public.community_reports
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id AND moderation_status IN ('PENDING', 'pending_review'))
    WITH CHECK (auth.uid() = user_id AND moderation_status IN ('PENDING', 'pending_review'));

-- Service role and admin full management
DROP POLICY IF EXISTS "Service role manages community reports" ON public.community_reports;
CREATE POLICY "Service role manages community reports"
    ON public.community_reports
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

