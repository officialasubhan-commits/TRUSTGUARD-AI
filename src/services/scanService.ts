import apiClient from './api';
import { API_ENDPOINTS } from './apiConfig';
import {
  ScanResult,
  ScanCreatePayload,
  ScanStatusResponse,
  DetailedSecurityReport,
  ScanStatistics,
  PaginatedScanHistoryResponse,
  DailyScanActivity,
  ScanHistoryFilterParams,
} from '../types/scan';

export interface ScanApiError {
  code: string;
  message: string;
  status: number;
}

export const scanService = {
  /**
   * Submits a target URL to the backend for multi-layer threat analysis.
   * Supports both anonymous guests and authenticated users.
   */
  async submitScan(url: string, signal?: AbortSignal): Promise<ScanResult> {
    const payload: ScanCreatePayload = { url };
    try {
      const response = await apiClient.post<ScanResult>(API_ENDPOINTS.SCAN.SUBMIT, payload, {
        signal,
      });
      return response.data;
    } catch (error: any) {
      if (error?.name === 'CanceledError' || error?.code === 'ERR_CANCELED') {
        throw {
          code: 'SCAN_CANCELLED',
          message: 'The URL scan request was aborted by the user.',
          status: 0,
        };
      }
      throw error;
    }
  },

  /**
   * Checks the readiness status of the backend URL analysis engines.
   */
  async getScanStatus(signal?: AbortSignal): Promise<ScanStatusResponse> {
    const response = await apiClient.get<ScanStatusResponse>(API_ENDPOINTS.SCAN.STATUS, {
      signal,
    });
    return response.data;
  },

  /**
   * Retrieves full scan details and persisted findings for a specific scan ID from /scan/{id}.
   */
  async getScanById(scanId: string, signal?: AbortSignal): Promise<ScanResult> {
    const response = await apiClient.get<ScanResult>(API_ENDPOINTS.SCAN.BY_ID(scanId), {
      signal,
    });
    return response.data;
  },

  /**
   * Retrieves comprehensive security report from /scans/{id}.
   */
  async getDetailedReport(scanId: string, signal?: AbortSignal): Promise<DetailedSecurityReport> {
    const response = await apiClient.get<DetailedSecurityReport>(API_ENDPOINTS.SCANS.BY_ID(scanId), {
      signal,
    });
    return response.data;
  },

  /**
   * Exports sanitized security report from /scans/{id}/export.
   */
  async exportScanReport(scanId: string, signal?: AbortSignal): Promise<Record<string, any>> {
    const response = await apiClient.get<Record<string, any>>(API_ENDPOINTS.SCANS.EXPORT(scanId), {
      signal,
    });
    return response.data;
  },

  /**
   * Retrieves user scanning statistics from /scans/statistics.
   */
  async getStatistics(signal?: AbortSignal): Promise<ScanStatistics> {
    const response = await apiClient.get<ScanStatistics>(API_ENDPOINTS.SCANS.STATISTICS, {
      signal,
    });
    return response.data;
  },

  /**
   * Retrieves server-paginated, filtered scan history for the authenticated user from /scans.
   */
  async getHistory(
    params?: ScanHistoryFilterParams,
    signal?: AbortSignal
  ): Promise<PaginatedScanHistoryResponse> {
    const response = await apiClient.get<PaginatedScanHistoryResponse>(API_ENDPOINTS.SCANS.LIST, {
      params,
      signal,
    });
    return response.data;
  },

  /**
   * Retrieves daily scanning activity counts across 7, 30, or 90 days from /scans/activity.
   */
  async getActivityTimeline(days: number = 30, signal?: AbortSignal): Promise<DailyScanActivity[]> {
    const response = await apiClient.get<DailyScanActivity[]>(API_ENDPOINTS.SCANS.ACTIVITY, {
      params: { days },
      signal,
    });
    return response.data;
  },

  /**
   * Deletes a scan record from /scans/{id}.
   */
  async deleteScan(scanId: string, signal?: AbortSignal): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete<{ success: boolean; message: string }>(
      API_ENDPOINTS.SCANS.DELETE(scanId),
      { signal }
    );
    return response.data;
  },

  /**
   * Streams all historical scans for the authenticated user as an RFC-4180 CSV file from /scans/export/csv.
   */
  async exportHistoryCsv(signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> {
    const response = await apiClient.get<Blob>(API_ENDPOINTS.SCANS.EXPORT_CSV, {
      responseType: 'blob',
      signal,
    });

    let filename = `trustguard-scan-history-${new Date().toISOString().split('T')[0]}.csv`;
    const disposition = response.headers['content-disposition'];
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    return {
      blob: response.data,
      filename,
    };
  },
};

export default scanService;
