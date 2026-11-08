export type RiskLevel =
  | 'CRITICAL'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'SAFE'
  | 'MINIMAL'
  | 'UNKNOWN'
  | 'CRITICAL_RISK'
  | 'HIGH_RISK'
  | 'MODERATE_RISK'
  | 'LOW_RISK'
  | 'SAFE_RISK';

export interface ScanIndicator {
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  evidence?: string;
  reason?: string;
}

export interface ScanFeatures {
  url_length: number;
  hostname_length: number;
  path_length?: number;
  path_depth: number;
  dot_count: number;
  hyphen_count: number;
  digit_count?: number;
  uses_https: boolean;
  is_ip_address: boolean;
  is_shortened: boolean;
  contains_suspicious_keywords: boolean;
  suspicious_keywords?: string[];
}

export interface MLPrediction {
  prediction: 'PHISHING' | 'SUSPICIOUS' | 'LIKELY_LEGITIMATE' | 'UNKNOWN' | 'MODEL_UNAVAILABLE' | string;
  phishing_probability: number | null;
  ml_subscore: number | null;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT' | string;
  model_version: string;
  model_status: 'ACTIVE' | 'MODEL_UNAVAILABLE' | 'ERROR' | string;
  indicators?: string[];
  summary?: string;
}

export interface SSLAnalysis {
  status:
    | 'VALID'
    | 'EXPIRING_SOON'
    | 'EXPIRED'
    | 'HOSTNAME_MISMATCH'
    | 'UNTRUSTED_CERTIFICATE'
    | 'TLS_HANDSHAKE_FAILED'
    | 'DNS_RESOLUTION_FAILED'
    | 'UNSAFE_DESTINATION'
    | 'HTTPS_NOT_USED'
    | 'TIMEOUT'
    | 'CONNECTION_ERROR'
    | 'UNKNOWN'
    | string;
  https_enabled: boolean;
  hostname: string;
  certificate_subject?: string | null;
  certificate_issuer?: string | null;
  days_remaining?: number | null;
  tls_version?: string | null;
  ssl_subscore: number;
  message?: string;
}

export interface TrustAssessment {
  digital_trust_score: number | null;
  risk_score: number | null;
  risk_level: RiskLevel;
  risk_label: string;
  assessment_status: 'COMPLETE' | 'PARTIAL' | 'INSUFFICIENT_DATA';
  assessment_coverage: number;
  coverage_percentage: number;
  scoring_version: string;
  high_severity_override: boolean;
  override_reason?: string | null;
  recommendations: string[];
  summary?: string;
}

export interface FindingItem {
  title: string;
  description: string;
  source_module: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  evidence?: string | null;
  affects_score: boolean;
  explanation?: string | null;
}

export interface DetailedSecurityReport {
  scan_id: string;
  original_url: string;
  normalized_url: string;
  domain: string;
  is_guest: boolean;
  scan_status: string;
  digital_trust_score?: number | null;
  risk_score?: number | null;
  risk_level?: RiskLevel;
  risk_label?: string | null;
  assessment_status?: string | null;
  assessment_coverage?: number | null;
  coverage_percentage?: number | null;
  high_severity_override: boolean;
  override_reason?: string | null;
  scoring_version?: string | null;
  model_version?: string | null;
  submitted_at: string;
  completed_at?: string | null;
  summary?: string | null;
  recommendations: string[];
  risk_indicators: FindingItem[];
  positive_indicators: FindingItem[];
  unknown_indicators: FindingItem[];
  module_scores?: Record<string, any>;
  url_analysis?: Record<string, any> | null;
  virustotal_findings?: Record<string, any> | null;
  ml_phishing_prediction?: Record<string, any> | null;
  ssl_tls_validation?: Record<string, any> | null;
}

export interface ScanResult {
  success: boolean;
  scan_id: string;
  original_url: string;
  normalized_url: string;
  validation_status: string;
  is_guest: boolean;
  preliminary_analysis?: {
    risk_level: string;
    indicators: ScanIndicator[];
    features: ScanFeatures;
  };
  ml_prediction?: MLPrediction;
  ssl_analysis?: SSLAnalysis;
  trust_assessment?: TrustAssessment;
  digital_trust_score?: number | null;
  risk_level?: RiskLevel;
  message: string;
  submitted_at: string;
}

export interface ScanCreatePayload {
  url: string;
  guest?: boolean;
}

export interface ScanStatusResponse {
  message: string;
  status: string;
}

export interface ScanHistorySummary {
  scan_id: string;
  domain?: string | null;
  submitted_url: string;
  normalized_url: string;
  scan_status: 'pending' | 'processing' | 'complete' | 'error';
  digital_trust_score?: number | null;
  risk_score?: number | null;
  risk_level?: RiskLevel;
  risk_label?: string | null;
  assessment_status?: string | null;
  assessment_coverage?: number | null;
  coverage_percentage?: number | null;
  scoring_version?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface PaginatedScanHistoryResponse {
  total_items: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
  items: ScanHistorySummary[];
}

export interface ScanStatistics {
  total_scans: number;
  low_risk_scans: number;
  moderate_risk_scans: number;
  high_risk_scans: number;
  critical_risk_scans: number;
  incomplete_assessments: number;
  average_trust_score?: number | null;
  recent_scans: ScanHistorySummary[];
  generated_at: string;
}

export interface DailyScanActivity {
  date: string;
  scan_count: number;
  threat_count: number;
  safe_count: number;
  moderate_count: number;
}

export interface ScanHistoryFilterParams {
  page?: number;
  page_size?: number;
  search?: string;
  risk_level?: string;
  assessment_status?: string;
  date_filter?: string;
  start_date?: string;
  end_date?: string;
  sort_by?: 'newest' | 'oldest' | 'highest_score' | 'lowest_score' | 'created_at' | 'trust_score';
  sort_order?: 'asc' | 'desc';
}
