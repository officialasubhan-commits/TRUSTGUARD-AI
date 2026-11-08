-- ==============================================================================
-- TrustGuard AI — Migration 006: User Email Notification Preferences
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Add threat_digest_enabled to public.users table with safe default FALSE
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS threat_digest_enabled BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Create index on threat_digest_enabled for fast digest query filtering
CREATE INDEX IF NOT EXISTS idx_users_threat_digest_enabled 
    ON public.users(threat_digest_enabled) 
    WHERE threat_digest_enabled = TRUE;

-- 3. Ensure authenticated users can update their own notification preferences
DROP POLICY IF EXISTS "Users can update own notification preferences" ON public.users;
CREATE POLICY "Users can update own notification preferences"
    ON public.users
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

