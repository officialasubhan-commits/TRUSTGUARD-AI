-- ==============================================================================
-- TrustGuard AI — Migration 002: Row Level Security (RLS) Policies
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- ==============================================================================
-- STEP 1: Enable RLS on All Tables
-- ==============================================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threat_reports ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- STEP 2: RLS Policies for 'users'
-- Users can only see and manage their own profile.
-- Service role has full administrative access.
-- ==============================================================================
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile"
    ON public.users
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile"
    ON public.users
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Service role manages all users" ON public.users;
CREATE POLICY "Service role manages all users"
    ON public.users
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

-- ==============================================================================
-- STEP 3: RLS Policies for 'scan_history'
-- 1. Authenticated users see only their own non-guest scans.
-- 2. Guest scans CANNOT be enumerated or browsed as a collection by anon users.
-- 3. Authenticated users can insert scans linked to their own account.
-- 4. Service role handles all guest scan processing & pipeline updates.
-- ==============================================================================
DROP POLICY IF EXISTS "Users view own scan history" ON public.scan_history;
CREATE POLICY "Users view own scan history"
    ON public.scan_history
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id AND is_guest = FALSE);

DROP POLICY IF EXISTS "Users insert own scans" ON public.scan_history;
CREATE POLICY "Users insert own scans"
    ON public.scan_history
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id AND is_guest = FALSE);

DROP POLICY IF EXISTS "Service role manages all scan history" ON public.scan_history;
CREATE POLICY "Service role manages all scan history"
    ON public.scan_history
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

-- ==============================================================================
-- STEP 4: RLS Policies for 'scan_results'
-- 1. Authenticated users can only view results of scans they own.
-- 2. General anon queries are blocked; guest scans are served strictly via
--    backend API with scan_id ownership verification.
-- 3. Inserts and updates restricted strictly to service role.
-- ==============================================================================
DROP POLICY IF EXISTS "Users view own scan results" ON public.scan_results;
CREATE POLICY "Users view own scan results"
    ON public.scan_results
    FOR SELECT
    TO authenticated
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
    ON public.scan_results
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

-- ==============================================================================
-- STEP 5: RLS Policies for 'community_reports'
-- 1. All users (authenticated and anonymous) can view verified community reports.
-- 2. Authenticated users can view their own submitted reports regardless of status.
-- 3. Authenticated users can insert new reports with user_id = auth.uid().
-- 4. Users can only update their own reports while pending_review.
-- 5. Service role can review, verify, or reject reports.
-- ==============================================================================
DROP POLICY IF EXISTS "Public can view verified community reports" ON public.community_reports;
CREATE POLICY "Public can view verified community reports"
    ON public.community_reports
    FOR SELECT
    TO public
    USING (report_status = 'verified' OR verification_status = 'verified');

DROP POLICY IF EXISTS "Users can view own submitted community reports" ON public.community_reports;
CREATE POLICY "Users can view own submitted community reports"
    ON public.community_reports
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Authenticated users submit community reports" ON public.community_reports;
CREATE POLICY "Authenticated users submit community reports"
    ON public.community_reports
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users update own pending community reports" ON public.community_reports;
CREATE POLICY "Users update own pending community reports"
    ON public.community_reports
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id AND report_status = 'pending_review')
    WITH CHECK (auth.uid() = user_id AND report_status = 'pending_review');

DROP POLICY IF EXISTS "Service role manages community reports" ON public.community_reports;
CREATE POLICY "Service role manages community reports"
    ON public.community_reports
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

-- ==============================================================================
-- STEP 6: RLS Policies for 'threat_reports'
-- 1. Verified threat intelligence is readable by public.
-- 2. Insert/Update/Delete operations are strictly prohibited for regular users;
--    only the backend service role or threat sync jobs can write records.
-- ==============================================================================
DROP POLICY IF EXISTS "Public view verified threat intelligence" ON public.threat_reports;
CREATE POLICY "Public view verified threat intelligence"
    ON public.threat_reports
    FOR SELECT
    TO public
    USING (verification_status = 'verified');

DROP POLICY IF EXISTS "Service role manages threat intelligence" ON public.threat_reports;
CREATE POLICY "Service role manages threat intelligence"
    ON public.threat_reports
    FOR ALL
    TO service_role
    USING (TRUE)
    WITH CHECK (TRUE);

