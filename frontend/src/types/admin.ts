/**
 * TypeScript types for TrustGuard AI Admin Panel.
 */

export interface AdminUser {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  role: 'super_admin' | 'admin' | 'content_manager' | 'security_analyst' | 'moderator';
  is_active: boolean;
  last_login_at?: string;
}

export interface AdminAuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  admin_user: AdminUser;
}

export interface AdminDashboardStats {
  total_users: number;
  active_users: number;
  total_scans: number;
  total_community_reports: number;
  pending_reports: number;
  verified_reports: number;
  rejected_reports: number;
  resolved_reports: number;
  high_risk_urls: number;
  safe_scans: number;
  suspicious_scans: number;
  malicious_scans: number;
  total_contributors: number;
  published_pages: number;
  system_status: string;
  maintenance_enabled: boolean;
  maintenance_message?: string;
}

export interface DailyActivityPoint {
  date: string;
  scans: number;
  registrations: number;
  reports: number;
}

export interface ThreatCategoryPoint {
  category: string;
  count: number;
}

export interface ModerationActivityPoint {
  date: string;
  approved: number;
  rejected: number;
}

export interface AdminDashboardActivity {
  timeline: DailyActivityPoint[];
  threat_categories: ThreatCategoryPoint[];
  moderation_activity: ModerationActivityPoint[];
}

export interface AdminEventItem {
  id: string;
  event_type: string;
  title: string;
  description: string;
  timestamp: string;
  status?: string;
  severity?: 'info' | 'warning' | 'danger';
}

export interface AdminUserListItem {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  scan_count: number;
  is_active: boolean;
  role: string;
  created_at: string;
}

export interface PaginatedAdminUsers {
  items: AdminUserListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminUserDetail extends AdminUserListItem {
  updated_at: string;
  recent_scans: Array<{
    id: string;
    submitted_url: string;
    domain?: string;
    trust_score?: number;
    risk_level?: string;
    scan_status: string;
    created_at: string;
  }>;
}

export interface AdminReportListItem {
  id: string;
  submitted_url: string;
  domain?: string;
  report_reason: string;
  threat_type?: string;
  target_brand?: string;
  submitter_email?: string;
  moderation_status: string;
  report_status: string;
  verification_status: string;
  upvotes: number;
  attachments_count: number;
  created_at: string;
}

export interface PaginatedAdminReports {
  items: AdminReportListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminReportDetail {
  id: string;
  submitted_url: string;
  normalized_url: string;
  domain?: string;
  report_reason: string;
  threat_type?: string;
  target_brand?: string;
  attack_vector?: string;
  description?: string;
  notes?: string;
  submitter_email?: string;
  submitter_id?: string;
  moderation_status: string;
  moderation_notes?: string;
  reviewer_id?: string;
  reviewer_username?: string;
  reviewed_at?: string;
  upvotes: number;
  confirmations_count: number;
  confirmations: Array<Record<string, any>>;
  evidence_items: Array<{
    id: string;
    filename: string;
    file_type: string;
    file_size_bytes: number;
    url: string;
    sha256_hash?: string;
    is_quarantined: boolean;
  }>;
  associated_scan?: Record<string, any>;
  created_at: string;
}

export interface MaintenanceConfig {
  maintenance_enabled: boolean;
  maintenance_message: string;
  estimated_restore_time?: string;
  internal_reason?: string;
  updated_by?: string;
  updated_at?: string;
}

export interface ServiceHealthItem {
  service_name: string;
  status: 'OPERATIONAL' | 'DEGRADED' | 'UNAVAILABLE' | 'NOT_CONFIGURED';
  latency_ms?: number;
  message?: string;
  last_checked: string;
  details?: Record<string, any>;
}

export interface SystemHealthResponse {
  overall_status: 'OPERATIONAL' | 'DEGRADED' | 'UNAVAILABLE';
  services: ServiceHealthItem[];
  checked_at: string;
}

export interface AdminAuditLogItem {
  id: string;
  admin_id?: string;
  admin_username: string;
  action: string;
  target_resource?: string;
  outcome: 'SUCCESS' | 'FAILURE' | 'DENIED';
  details?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

export interface AdminChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ThreatIntelItem {
  id: string;
  domain: string;
  threat_category: string;
  severity: string;
  source: string;
  verification_status: string;
  first_seen: string;
  evidence_count: number;
}

export interface AdminThreatIntelSummary {
  total_verified_threats: number;
  source_breakdown: Record<string, number>;
  top_threat_categories: Array<{ category: string; count: number; percentage: number }>;
  external_providers: Array<{
    name: string;
    type: string;
    status: string;
    latency_ms: number;
  }>;
  recent_threats: ThreatIntelItem[];
}

export interface PaginatedAdminAuditLogs {
  items: AdminAuditLogItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// -----------------------------------------------------------------------------
// Contributors Types
// -----------------------------------------------------------------------------
export interface ContributorSocialLinks {
  github?: string;
  linkedin?: string;
  twitter?: string;
  website?: string;
}

export interface Contributor {
  id: string;
  name: string;
  role: string;
  bio?: string;
  avatar_url?: string;
  social_links?: ContributorSocialLinks;
  display_order: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ContributorCreate {
  name: string;
  role: string;
  bio?: string;
  avatar_url?: string;
  social_links?: ContributorSocialLinks;
  display_order: number;
  is_active: boolean;
}

export interface ContributorUpdate {
  name?: string;
  role?: string;
  bio?: string;
  avatar_url?: string;
  social_links?: ContributorSocialLinks;
  display_order?: number;
  is_active?: boolean;
}

export interface ContributorReorderItem {
  id: string;
  display_order: number;
}

export interface ContributorsPageConfig {
  title: string;
  subtitle: string;
  header_banner_url?: string;
  is_published: boolean;
  show_in_navigation: boolean;
  updated_at?: string;
}

// -----------------------------------------------------------------------------
// Website Pages (CMS) Types
// -----------------------------------------------------------------------------
export interface WebsitePage {
  id: string;
  title: string;
  slug: string;
  content: string;
  meta_description?: string;
  is_published: boolean;
  show_in_navigation: boolean;
  nav_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface WebsitePageCreate {
  title: string;
  slug: string;
  content: string;
  meta_description?: string;
  is_published: boolean;
  show_in_navigation: boolean;
  nav_order: number;
}

export interface WebsitePageUpdate {
  title?: string;
  slug?: string;
  content?: string;
  meta_description?: string;
  is_published?: boolean;
  show_in_navigation?: boolean;
  nav_order?: number;
}

// -----------------------------------------------------------------------------
// Scans Management Types
// -----------------------------------------------------------------------------
export interface AdminScanItem {
  id: string;
  url: string;
  domain?: string;
  classification: string;
  trust_score: number;
  is_malicious: boolean;
  user_id?: string;
  user_email?: string;
  ip_address?: string;
  scanned_at: string;
  details?: Record<string, any>;
}

export interface PaginatedAdminScans {
  items: AdminScanItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// -----------------------------------------------------------------------------
// System Settings Types
// -----------------------------------------------------------------------------
export interface SystemSettingsConfig {
  site_name: string;
  site_tagline: string;
  site_description: string;
  logo_url?: string;
  favicon_url?: string;
  announcement_enabled: boolean;
  announcement_message?: string;
  announcement_type: 'info' | 'warning' | 'critical';
  announcement_link?: string;
  allow_registration: boolean;
  allow_guest_scans: boolean;
  allow_community_reports: boolean;
  updated_at?: string;
}

export interface SystemSettingsUpdate {
  site_name?: string;
  site_tagline?: string;
  site_description?: string;
  logo_url?: string;
  favicon_url?: string;
  announcement_enabled?: boolean;
  announcement_message?: string;
  announcement_type?: 'info' | 'warning' | 'critical';
  announcement_link?: string;
  allow_registration?: boolean;
  allow_guest_scans?: boolean;
  allow_community_reports?: boolean;
}

