-- ==============================================================================
-- TrustGuard AI — Migration 008: Admin CMS, Dynamic Pages & Contributors System
-- Target Database: PostgreSQL 15+ (Supabase)
-- ==============================================================================

-- 1. Dedicated Administrator Accounts Table
CREATE TABLE IF NOT EXISTS public.admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'super_admin' CHECK (role IN ('super_admin', 'admin', 'content_manager', 'moderator', 'security_analyst')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Administrator Audit Logs Table
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

-- 4. Project Contributors Table
CREATE TABLE IF NOT EXISTS public.contributors (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    role VARCHAR(120) NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    social_links JSONB DEFAULT '{}'::jsonb,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Dynamic Website CMS Pages Table
CREATE TABLE IF NOT EXISTS public.website_pages (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    content TEXT NOT NULL,
    meta_description TEXT,
    is_published BOOLEAN NOT NULL DEFAULT true,
    show_in_navigation BOOLEAN NOT NULL DEFAULT false,
    nav_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. Indexes for High-Speed Queries
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON public.admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON public.admin_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON public.admin_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contributors_order ON public.contributors(display_order);
CREATE INDEX IF NOT EXISTS idx_contributors_active ON public.contributors(is_active);
CREATE INDEX IF NOT EXISTS idx_website_pages_slug ON public.website_pages(slug);
CREATE INDEX IF NOT EXISTS idx_website_pages_published ON public.website_pages(is_published);

-- 7. Row Level Security Policies
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contributors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.website_pages ENABLE ROW LEVEL SECURITY;

-- Service role full access on all administrative tables
CREATE POLICY "Service role full access on admin_users" ON public.admin_users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on admin_audit_logs" ON public.admin_audit_logs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on system_settings" ON public.system_settings FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on contributors" ON public.contributors FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on website_pages" ON public.website_pages FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Public Read Policies
CREATE POLICY "Public read active contributors" ON public.contributors FOR SELECT TO anon, authenticated USING (is_active = true);
CREATE POLICY "Public read published pages" ON public.website_pages FOR SELECT TO anon, authenticated USING (is_published = true);
CREATE POLICY "Public read general settings" ON public.system_settings FOR SELECT TO anon, authenticated USING (key IN ('maintenance_config', 'contributors_page_config', 'general_settings'));

-- 8. Seed Initial Default Data
-- Super Admin User: admin / Ratul@2007##
INSERT INTO public.admin_users (id, username, password_hash, email, full_name, role, is_active)
VALUES (
    'a2107163-49cd-4486-b982-edef1b495a58',
    'admin',
    'scrypt$16384$8$1$f79f60ae1601facf6f7be1d48a90bcde$b3d6bc81b3b08156784f3778e0f48572fd871b07a17ebb993fb1af6b39d6ab2968c1c0ff2f135df56596872951bdaaa24f482b013a51a4f95024acc73cf5bf17',
    'admin@trustguard.ai',
    'Security Administrator',
    'super_admin',
    true
)
ON CONFLICT (username) DO NOTHING;

-- Initial Settings
INSERT INTO public.system_settings (key, value, updated_by)
VALUES
    ('maintenance_config', '{"maintenance_enabled": false, "maintenance_message": "TrustGuard AI is temporarily undergoing scheduled maintenance.", "estimated_restore_time": null, "internal_reason": "System operating normally."}'::jsonb, 'initial_setup'),
    ('contributors_page_config', '{"title": "Project Contributors", "subtitle": "The core developers, security researchers, and contributors powering TrustGuard AI.", "header_banner_url": null, "is_published": true, "show_in_navigation": true}'::jsonb, 'initial_setup'),
    ('general_settings', '{"site_name": "TrustGuard AI", "site_tagline": "AI-Powered Phishing & Scam URL Detection", "site_description": "Next-generation URL threat intelligence and automated cyber fraud protection.", "announcement_enabled": false, "allow_registration": true, "allow_guest_scans": true, "allow_community_reports": true}'::jsonb, 'initial_setup')
ON CONFLICT (key) DO NOTHING;

-- Initial Contributors
INSERT INTO public.contributors (id, name, role, bio, avatar_url, social_links, display_order, is_active)
VALUES
    ('contributor-1', 'Ratul Saha', 'Lead Architect & Security Researcher', 'Cybersecurity specialist focused on adversarial AI models, heuristic phishing analysis, and real-time defense architectures.', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80', '{"github": "https://github.com", "linkedin": "https://linkedin.com", "website": "https://trustguard-ai-xi.vercel.app"}'::jsonb, 1, true),
    ('contributor-2', 'TrustGuard Core Research Team', 'Threat Intelligence & Detection Engineering', 'Specialized group engineering the TrustGuard ML classifier, entropy calculators, and continuous SSL validation pipeline.', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80', '{"github": "https://github.com", "twitter": "https://twitter.com"}'::jsonb, 2, true),
    ('contributor-3', 'Alex Rivera', 'Full-Stack Security Engineer', 'Front-end and API architect leading the pixel-frame design system and high-throughput dashboard telemetry.', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80', '{"github": "https://github.com", "linkedin": "https://linkedin.com"}'::jsonb, 3, true)
ON CONFLICT (id) DO NOTHING;

-- Initial Pages
INSERT INTO public.website_pages (id, title, slug, content, meta_description, is_published, show_in_navigation, nav_order)
VALUES
    ('page-about', 'About TrustGuard AI', 'about', '# About TrustGuard AI\n\nTrustGuard AI is an advanced, multi-layered threat detection platform engineered to protect individuals and organizations from cyber fraud, phishing campaigns, deceptive redirects, and malicious web resources.\n\n## Multi-Layer Detection Architecture\n1. **Static Heuristic Engine**: Scans for homograph attacks, typosquatting, suspicious top-level domains, excessive entropy, and obscured redirects.\n2. **AI & Machine Learning Inference**: Real-time classification utilizing lightweight threat intelligence classifiers trained on millions of legitimate and malicious URLs.\n3. **SSL/TLS & Domain Trust Verification**: Deep inspection of certificate authorities, validity lifespans, issuer trust, and domain age.\n4. **Decentralized Community Intelligence**: Real-time threat reports reviewed and confirmed by security analysts worldwide.\n\n## Our Mission\nWe believe the modern web should be verifiable and secure for everyone. TrustGuard AI empowers users with instant, transparent trust ratings before they ever click or submit sensitive information.', 'Discover how TrustGuard AI defends users and enterprises against online fraud, phishing, and scam domains.', true, true, 1),
    ('page-privacy', 'Privacy Policy', 'privacy', '# Privacy Policy\n\n**Effective Date:** November 2026\n\nAt TrustGuard AI, we prioritize user anonymity and privacy. This Privacy Policy details what information we process and how we protect your rights.\n\n## 1. URL Submissions\n- When you submit a URL for analysis, the URL is processed by our automated heuristic and machine learning pipeline.\n- Users may choose to scan anonymously in Guest Mode without logging in.\n- URLs identified as malicious may be aggregated anonymously into our threat intelligence database to protect other users.\n\n## 2. User Accounts\n- If you create an account, we store your email and authentication credentials securely via Supabase Auth with industry-standard bcrypt/Argon2id encryption.\n- We will never sell, lease, or monetize your personal information or browsing history.\n\n## 3. Data Retention\n- Authenticated scan history is accessible only by the account owner protected by Row-Level Security (RLS).\n- You can request complete deletion of your account and associated scan history at any time through our settings.', 'TrustGuard AI Privacy Policy and data handling disclosures.', true, true, 2),
    ('page-terms', 'Terms of Service', 'terms', '# Terms of Service\n\n**Effective Date:** November 2026\n\nBy accessing or using TrustGuard AI, you agree to comply with and be bound by these Terms of Service.\n\n## 1. Permitted Use\n- TrustGuard AI is designed for cyber defense, security research, and personal browsing safety.\n- You may not use TrustGuard AI to conduct automated denial-of-service attacks, reverse-engineer proprietary detection algorithms, or probe targets without authorization.\n\n## 2. Disclaimer of Warranties\n- While TrustGuard AI utilizes cutting-edge heuristics, machine learning, and threat intelligence feeds, no security scanner can guarantee 100% accuracy.\n- We provide our analysis as an informational aid and accept no liability for damages resulting from user actions taken based on scan ratings.\n\n## 3. Community Conduct\n- Threat reports submitted by community members must be accurate and submitted in good faith. False reporting or malicious reputation manipulation is grounds for immediate account termination.', 'Terms of service and acceptable use guidelines for TrustGuard AI.', true, true, 3)
ON CONFLICT (slug) DO NOTHING;
