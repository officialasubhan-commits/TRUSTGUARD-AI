import apiClient from './api';
import { API_ENDPOINTS } from './apiConfig';
import {
  CommunityReportItem,
  CommunityReportUserItem,
  CommunityStatistics,
  PaginatedCommunityResponse,
  CommunityReportCreatePayload,
  CommunityConfirmationToggleResult,
  CommunityReportFlagPayload,
  Web3IntegrityProof,
  CommunityFilterParams,
} from '../types/community';

export const communityService = {
  /**
   * Fetch aggregate platform telemetry for community reporting.
   */
  async getStatistics(signal?: AbortSignal): Promise<CommunityStatistics> {
    const response = await apiClient.get<CommunityStatistics>(API_ENDPOINTS.COMMUNITY.STATISTICS, {
      signal,
    });
    return response.data;
  },

  /**
   * Fetch public community threat reports with category, status, search, and sort filters.
   */
  async getReports(
    params?: CommunityFilterParams,
    signal?: AbortSignal
  ): Promise<PaginatedCommunityResponse<CommunityReportItem>> {
    const response = await apiClient.get<PaginatedCommunityResponse<CommunityReportItem>>(
      API_ENDPOINTS.COMMUNITY.REPORTS,
      { params, signal }
    );
    return response.data;
  },

  /**
   * Fetch personal threat submission history for the authenticated user.
   */
  async getMyReports(
    page = 1,
    pageSize = 20,
    signal?: AbortSignal
  ): Promise<PaginatedCommunityResponse<CommunityReportUserItem>> {
    const response = await apiClient.get<PaginatedCommunityResponse<CommunityReportUserItem>>(
      API_ENDPOINTS.COMMUNITY.MY_REPORTS,
      { params: { page, page_size: pageSize }, signal }
    );
    return response.data;
  },

  /**
   * Retrieve single threat report details.
   */
  async getReportById(
    reportId: string,
    signal?: AbortSignal
  ): Promise<CommunityReportItem | CommunityReportUserItem> {
    const response = await apiClient.get(API_ENDPOINTS.COMMUNITY.BY_ID(reportId), { signal });
    return response.data;
  },

  /**
   * Submit a new threat report for moderation and community consensus.
   */
  async submitReport(payload: CommunityReportCreatePayload): Promise<CommunityReportUserItem> {
    const response = await apiClient.post<CommunityReportUserItem>(
      API_ENDPOINTS.COMMUNITY.REPORTS,
      payload
    );
    return response.data;
  },

  /**
   * Toggle confirmation of suspicious activity on a community report (one active confirmation per user).
   */
  async toggleConfirmation(reportId: string): Promise<CommunityConfirmationToggleResult> {
    const response = await apiClient.post<CommunityConfirmationToggleResult>(
      API_ENDPOINTS.COMMUNITY.CONFIRM(reportId)
    );
    return response.data;
  },

  /**
   * Flag an inaccurate, abusive, or duplicate community threat report.
   */
  async flagReport(
    reportId: string,
    payload: CommunityReportFlagPayload
  ): Promise<{ id: string; message: string }> {
    const response = await apiClient.post(API_ENDPOINTS.COMMUNITY.FLAG(reportId), payload);
    return response.data;
  },

  /**
   * Fetch verifiable cryptographic proof of canonical record integrity (Web3 proof).
   */
  async getIntegrityProof(reportId: string, signal?: AbortSignal): Promise<Web3IntegrityProof> {
    const response = await apiClient.get<Web3IntegrityProof>(
      API_ENDPOINTS.COMMUNITY.INTEGRITY(reportId),
      { signal }
    );
    return response.data;
  },
};

export default communityService;

