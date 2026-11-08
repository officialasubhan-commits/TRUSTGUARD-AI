-- ==============================================================================
-- TrustGuard AI — Migration 005: Community Confirmations, Moderation Audit & Web3 Integrity
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Table: public.community_confirmations
-- Controlled consensus: one active confirmation per authenticated user per report
CREATE TABLE IF NOT EXISTS public.community_confirmations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id   UUID NOT NULL REFERENCES public.community_reports(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_report_user_confirmation UNIQUE (report_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_comm_conf_report ON public.community_confirmations(report_id);
CREATE INDEX IF NOT EXISTS idx_comm_conf_user ON public.community_confirmations(user_id);

-- 2. Table: public.community_report_flags
-- Enables community reporting of inaccurate, abusive, or duplicate submissions
CREATE TABLE IF NOT EXISTS public.community_report_flags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id   UUID NOT NULL REFERENCES public.community_reports(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    flag_reason VARCHAR(64) NOT NULL,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_report_user_flag UNIQUE (report_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_comm_flags_report ON public.community_report_flags(report_id);

-- 3. Table: public.community_moderation_logs
-- Immutable audit log for all reviewer actions
CREATE TABLE IF NOT EXISTS public.community_moderation_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES public.community_reports(id) ON DELETE CASCADE,
    moderator_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    action          VARCHAR(64) NOT NULL,
    previous_status VARCHAR(32),
    new_status      VARCHAR(32) NOT NULL,
    rationale       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comm_mod_logs_report ON public.community_moderation_logs(report_id);
CREATE INDEX IF NOT EXISTS idx_comm_mod_logs_moderator ON public.community_moderation_logs(moderator_id);

-- 4. Extend public.community_reports with Web3 proof metadata fields
ALTER TABLE public.community_reports
    ADD COLUMN IF NOT EXISTS integrity_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS integrity_network VARCHAR(64),
    ADD COLUMN IF NOT EXISTS integrity_tx_hash VARCHAR(66),
    ADD COLUMN IF NOT EXISTS integrity_timestamp TIMESTAMPTZ;

-- 5. Row Level Security Policies
ALTER TABLE public.community_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_report_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_moderation_logs ENABLE ROW LEVEL SECURITY;

-- Confirmations: Public can count confirmations; authenticated users can manage own
DROP POLICY IF EXISTS "Public can view confirmations count" ON public.community_confirmations;
CREATE POLICY "Public can view confirmations count"
    ON public.community_confirmations FOR SELECT
    TO public USING (true);

DROP POLICY IF EXISTS "Authenticated users insert confirmations" ON public.community_confirmations;
CREATE POLICY "Authenticated users insert confirmations"
    ON public.community_confirmations FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Authenticated users delete own confirmations" ON public.community_confirmations;
CREATE POLICY "Authenticated users delete own confirmations"
    ON public.community_confirmations FOR DELETE
    TO authenticated USING (auth.uid() = user_id);

-- Flags: Authenticated users can insert flags for inaccurate reports
DROP POLICY IF EXISTS "Authenticated users flag reports" ON public.community_report_flags;
CREATE POLICY "Authenticated users flag reports"
    ON public.community_report_flags FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role manages flags" ON public.community_report_flags;
CREATE POLICY "Service role manages flags"
    ON public.community_report_flags FOR ALL
    TO service_role USING (true) WITH CHECK (true);

-- Moderation logs: Admins and service role only
DROP POLICY IF EXISTS "Admins view moderation logs" ON public.community_moderation_logs;
CREATE POLICY "Admins view moderation logs"
    ON public.community_moderation_logs FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE public.users.id = auth.uid() AND public.users.role = 'admin'
        )
    );

DROP POLICY IF EXISTS "Service role manages moderation logs" ON public.community_moderation_logs;
CREATE POLICY "Service role manages moderation logs"
    ON public.community_moderation_logs FOR ALL
    TO service_role USING (true) WITH CHECK (true);

