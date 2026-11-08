-- ==============================================================================
-- TrustGuard AI — Migration 007: Dedicated Admin Panel, Audit Logs & System Settings
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Dedicated Administrator Accounts Table
-- Completely independent from ordinary users and auth.users
CREATE TABLE IF NOT EXISTS public.admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'super_admin' CHECK (role IN ('super_admin', 'security_analyst', 'moderator')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trigger for admin_users updated_at
DROP TRIGGER IF EXISTS set_admin_users_updated_at ON public.admin_users;
CREATE TRIGGER set_admin_users_updated_at
    BEFORE UPDATE ON public.admin_users
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- 2. Administrator Audit Logs Table
-- Immutable record of all administrative decisions, access, and configuration changes
CREATE TABLE IF NOT EXISTS public.admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
    admin_username VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    target_resource VARCHAR(255),
    outcome VARCHAR(32) NOT NULL DEFAULT 'SUCCESS' CHECK (outcome IN ('SUCCESS', 'FAILURE', 'DENIED')),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. System Configuration & Maintenance Mode Table
CREATE TABLE IF NOT EXISTS public.system_settings (
    key VARCHAR(64) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_by VARCHAR(64) DEFAULT 'system',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed initial default maintenance configuration if absent
INSERT INTO public.system_settings (key, value, updated_by)
VALUES (
    'maintenance_config',
    jsonb_build_object(
        'maintenance_enabled', false,
        'maintenance_message', 'TrustGuard AI is temporarily undergoing scheduled maintenance. We are optimizing our threat detection engines and will be back shortly.',
        'estimated_restore_time', null,
        'internal_reason', 'System online and operational.'
    ),
    'initial_setup'
)
ON CONFLICT (key) DO NOTHING;

-- 4. Indexes for rapid lookups and search
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON public.admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_active ON public.admin_users(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON public.admin_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_id ON public.admin_audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON public.admin_audit_logs(created_at DESC);

-- 5. Row Level Security Policies
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;

-- Block public and ordinary authenticated access entirely from direct Supabase API access
DROP POLICY IF EXISTS "Service role manages admin_users" ON public.admin_users;
CREATE POLICY "Service role manages admin_users"
    ON public.admin_users
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Service role manages admin_audit_logs" ON public.admin_audit_logs;
CREATE POLICY "Service role manages admin_audit_logs"
    ON public.admin_audit_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "Service role manages system_settings" ON public.system_settings;
CREATE POLICY "Service role manages system_settings"
    ON public.system_settings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anonymous read on system_settings only for maintenance status verification
DROP POLICY IF EXISTS "Public can view system maintenance status" ON public.system_settings;
CREATE POLICY "Public can view system maintenance status"
    ON public.system_settings
    FOR SELECT
    TO public
    USING (key = 'maintenance_config');

