export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

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

