export type ThreatCategory =
  | 'PHISHING'
  | 'MALWARE_DISTRIBUTION'
  | 'FRAUD_OR_SCAM'
  | 'SUSPICIOUS_REDIRECT'
  | 'IMPERSONATION'
  | 'OTHER';

export type ReportModerationStatus =
  | 'PENDING'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'RESOLVED'
  | 'DUPLICATE';

export type ReportVerificationStatus =
  | 'UNVERIFIED'
  | 'COMMUNITY_SUPPORTED'
  | 'ADMIN_VERIFIED'
  | 'DISPUTED';

export interface CommunityReportItem {
  id: string;
  scan_id?: string | null;
  submitted_url: string;
  normalized_url: string;
  domain?: string | null;
  category: string;
  report_reason: string;
  threat_type?: string | null;
  target_brand?: string | null;
  attack_vector?: string | null;
  description?: string | null;
  moderation_status: string;
  verification_status: string;
  upvotes: number;
  user_confirmed?: boolean;
  integrity_hash?: string | null;
  created_at: string;
}

export interface CommunityReportUserItem {
  id: string;
  scan_id?: string | null;
  submitted_url: string;
  normalized_url: string;
  domain?: string | null;
  category: string;
  report_reason: string;
  target_brand?: string | null;
  attack_vector?: string | null;
  description?: string | null;
  notes?: string | null;
  evidence_url?: string | null;
  moderation_status: string;
  moderation_notes?: string | null;
  verification_status: string;
  upvotes: number;
  duplicate_of?: string | null;
  integrity_hash?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface CommunityStatistics {
  total_reports: number;
  pending_review: number;
  verified_reports: number;
  rejected_reports: number;
  resolved_reports: number;
  active_confirmations: number;
  generated_at: string;
}

export interface PaginatedCommunityResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CommunityReportCreatePayload {
  submitted_url: string;
  category: string;
  description: string;
  target_brand?: string;
  attack_vector?: string;
  evidence_url?: string;
  scan_id?: string;
}

export interface CommunityConfirmationToggleResult {
  report_id: string;
  confirmed: boolean;
  total_confirmations: number;
  message: string;
}

export interface CommunityReportFlagPayload {
  flag_reason: 'INACCURATE' | 'ABUSIVE_OR_SPAM' | 'DUPLICATE' | 'RESOLVED_SAFE' | 'OTHER';
  notes?: string;
}

export interface Web3IntegrityProof {
  report_id: string;
  canonical_hash: string;
  algorithm: string;
  proof_type: string;
  network: string;
  contract_address?: string | null;
  merkle_root: string;
  verified: boolean;
  verification_timestamp: string;
  canonical_payload: Record<string, any>;
}

export interface CommunityFilterParams {
  domain?: string;
  category?: string;
  status?: string;
  search?: string;
  sort_by?: 'newest' | 'most_confirmed';
  page?: number;
  page_size?: number;
}

