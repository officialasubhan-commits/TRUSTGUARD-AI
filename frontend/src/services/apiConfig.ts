const DEFAULT_PROD_API_URL = 'https://trustguard-ai-a154.onrender.com/api/v1';
const DEFAULT_DEV_API_URL = 'http://localhost:8000/api/v1';

function resolveApiBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();
  const rawUrl = envUrl || (import.meta.env.PROD ? DEFAULT_PROD_API_URL : DEFAULT_DEV_API_URL);
  let cleaned = rawUrl.replace(/\/+$/, '');

  // Normalize: ensure the API base URL has the /api/v1 prefix if missing
  if (!cleaned.endsWith('/api/v1')) {
    if (cleaned.endsWith('/api')) {
      cleaned = `${cleaned}/v1`;
    } else {
      cleaned = `${cleaned}/api/v1`;
    }
  }

  return cleaned;
}

export const API_BASE_URL: string = resolveApiBaseUrl();

export const API_TIMEOUT: number = 30000; // 30 seconds for deep multi-engine security scans

export const TOKEN_STORAGE_KEY = 'trustguard_access_token';
export const REFRESH_TOKEN_STORAGE_KEY = 'trustguard_refresh_token';
export const USER_STORAGE_KEY = 'trustguard_user';

export const API_ENDPOINTS = {
  HEALTH: '/health',
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    RESEND_VERIFICATION: '/auth/resend-verification',
    GOOGLE_OAUTH: '/auth/oauth/google',
    OAUTH_CALLBACK: '/auth/oauth/callback',
  },
  USERS: {
    ME: '/users/me',
    NOTIFICATIONS: '/users/me/notifications',
  },
  SCAN: {
    SUBMIT: '/scan',
    STATUS: '/scan/status',
    BY_ID: (id: string) => `/scan/${id}`,
  },
  SCANS: {
    LIST: '/scans',
    EXPORT_CSV: '/scans/export/csv',
    STATISTICS: '/scans/statistics',
    ACTIVITY: '/scans/activity',
    BY_ID: (id: string) => `/scans/${id}`,
    EXPORT: (id: string) => `/scans/${id}/export`,
    DELETE: (id: string) => `/scans/${id}`,
  },
  COMMUNITY: {
    STATISTICS: '/community/statistics',
    REPORTS: '/community/reports',
    MY_REPORTS: '/community/my-reports',
    BY_ID: (id: string) => `/community/reports/${id}`,
    CONFIRM: (id: string) => `/community/reports/${id}/confirm`,
    FLAG: (id: string) => `/community/reports/${id}/flag`,
    INTEGRITY: (id: string) => `/community/reports/${id}/integrity-proof`,
    UPVOTE: (id: string) => `/community/reports/${id}/upvote`,
  },
  ADMIN: {
    REPORTS: '/admin/community/reports',
    MODERATE: (id: string) => `/admin/community/reports/${id}`,
  },
} as const;
