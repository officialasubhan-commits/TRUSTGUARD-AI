import axios from 'axios';
import { API_BASE_URL, API_TIMEOUT } from './apiConfig';
import {
  AdminAuthResponse,
  AdminChangePasswordRequest,
  AdminDashboardActivity,
  AdminDashboardStats,
  AdminEventItem,
  AdminReportDetail,
  AdminThreatIntelSummary,
  AdminUser,
  AdminUserDetail,
  MaintenanceConfig,
  PaginatedAdminAuditLogs,
  PaginatedAdminReports,
  PaginatedAdminUsers,
  SystemHealthResponse,
} from '../types/admin';

export const ADMIN_TOKEN_KEY = 'tg_admin_token';
export const ADMIN_USER_KEY = 'tg_admin_user';

export const adminApiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Attach Admin Token
adminApiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ADMIN_TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const adminService = {
  // 1. Auth
  async login(username: string, password: string): Promise<AdminAuthResponse> {
    const res = await adminApiClient.post<AdminAuthResponse>('/admin/auth/login', {
      username,
      password,
    });
    localStorage.setItem(ADMIN_TOKEN_KEY, res.data.access_token);
    localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(res.data.admin_user));
    return res.data;
  },

  async getMe(): Promise<AdminUser> {
    const res = await adminApiClient.get<AdminUser>('/admin/auth/me');
    return res.data;
  },

  async logout(): Promise<void> {
    try {
      await adminApiClient.post('/admin/auth/logout');
    } catch {
      // Ignore network failures on logout
    } finally {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      localStorage.removeItem(ADMIN_USER_KEY);
    }
  },

  async changePassword(data: AdminChangePasswordRequest): Promise<void> {
    await adminApiClient.post('/admin/settings/change-password', data);
  },

  // 2. Dashboard
  async getDashboardStats(): Promise<AdminDashboardStats> {
    const res = await adminApiClient.get<AdminDashboardStats>('/admin/dashboard/stats');
    return res.data;
  },

  async getDashboardActivity(days: number = 30): Promise<AdminDashboardActivity> {
    const res = await adminApiClient.get<AdminDashboardActivity>('/admin/dashboard/activity', {
      params: { days },
    });
    return res.data;
  },

  async getRecentEvents(limit: number = 15): Promise<AdminEventItem[]> {
    const res = await adminApiClient.get<AdminEventItem[]>('/admin/dashboard/events', {
      params: { limit },
    });
    return res.data;
  },

  // 3. Users
  async getUsers(
    page: number = 1,
    pageSize: number = 20,
    search?: string,
    isActive?: boolean
  ): Promise<PaginatedAdminUsers> {
    const res = await adminApiClient.get<PaginatedAdminUsers>('/admin/users', {
      params: {
        page,
        page_size: pageSize,
        search: search || undefined,
        is_active: isActive !== undefined ? isActive : undefined,
      },
    });
    return res.data;
  },

  async getUserDetail(userId: string): Promise<AdminUserDetail> {
    const res = await adminApiClient.get<AdminUserDetail>(`/admin/users/${userId}`);
    return res.data;
  },

  async suspendUser(userId: string, reason: string): Promise<void> {
    await adminApiClient.post(`/admin/users/${userId}/suspend`, { is_active: false, reason });
  },

  async restoreUser(userId: string, reason: string): Promise<void> {
    await adminApiClient.post(`/admin/users/${userId}/restore`, { is_active: true, reason });
  },

  // 4. Reports Moderation
  async getReports(
    page: number = 1,
    pageSize: number = 20,
    status?: string,
    category?: string,
    search?: string
  ): Promise<PaginatedAdminReports> {
    const res = await adminApiClient.get<PaginatedAdminReports>('/admin/reports', {
      params: {
        page,
        page_size: pageSize,
        status: status || undefined,
        category: category || undefined,
        search: search || undefined,
      },
    });
    return res.data;
  },

  async getReportDetail(reportId: string): Promise<AdminReportDetail> {
    const res = await adminApiClient.get<AdminReportDetail>(`/admin/reports/${reportId}`);
    return res.data;
  },

  async moderateReport(
    reportId: string,
    action: string,
    reason: string,
    internalNotes?: string,
    duplicateOf?: string
  ): Promise<void> {
    await adminApiClient.post(`/admin/reports/${reportId}/moderate`, {
      action,
      reason,
      internal_notes: internalNotes || undefined,
      duplicate_of: duplicateOf || undefined,
    });
  },

  async bulkModerateReports(
    reportIds: string[],
    action: string,
    reason: string,
    internalNotes?: string
  ): Promise<{ succeeded: number; failed: number }> {
    const res = await adminApiClient.post('/admin/reports/bulk-moderate', {
      report_ids: reportIds,
      action,
      reason,
      internal_notes: internalNotes || undefined,
    });
    return res.data;
  },

  // 5. Threat Intelligence
  async getThreatIntelSummary(): Promise<AdminThreatIntelSummary> {
    const res = await adminApiClient.get<AdminThreatIntelSummary>('/admin/threat-intelligence/summary');
    return res.data;
  },

  // 6. Maintenance Mode
  async getMaintenanceConfig(): Promise<MaintenanceConfig> {
    const res = await adminApiClient.get<MaintenanceConfig>('/admin/maintenance');
    return res.data;
  },

  async updateMaintenanceConfig(data: {
    maintenance_enabled: boolean;
    maintenance_message?: string;
    estimated_restore_time?: string;
    internal_reason: string;
  }): Promise<MaintenanceConfig> {
    const res = await adminApiClient.post<MaintenanceConfig>('/admin/maintenance', data);
    return res.data;
  },

  async getPublicMaintenanceStatus(): Promise<{
    maintenance_enabled: boolean;
    maintenance_message?: string;
    estimated_restore_time?: string;
  }> {
    const res = await axios.get(`${API_BASE_URL}/maintenance/status`);
    return res.data;
  },

  // 7. System Health
  async getSystemHealth(): Promise<SystemHealthResponse> {
    const res = await adminApiClient.get<SystemHealthResponse>('/admin/system/health');
    return res.data;
  },

  // 8. Audit Logs
  async getAuditLogs(
    page: number = 1,
    pageSize: number = 20,
    action?: string,
    adminUsername?: string,
    search?: string
  ): Promise<PaginatedAdminAuditLogs> {
    const res = await adminApiClient.get<PaginatedAdminAuditLogs>('/admin/audit-logs', {
      params: {
        page,
        page_size: pageSize,
        action: action || undefined,
        admin_username: adminUsername || undefined,
        search: search || undefined,
      },
    });
    return res.data;
  },
};
