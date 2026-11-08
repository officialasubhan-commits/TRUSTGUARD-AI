import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  API_BASE_URL,
  API_TIMEOUT,
  TOKEN_STORAGE_KEY,
  REFRESH_TOKEN_STORAGE_KEY,
  API_ENDPOINTS,
} from './apiConfig';
import { ApiErrorResponse } from '../types/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request Interceptor: Attach Bearer JWT if available
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Centralized error handling and silent token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized (expired token) for authenticated requests
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Don't retry refresh endpoint or login endpoint
      if (
        originalRequest.url?.includes(API_ENDPOINTS.AUTH.LOGIN) ||
        originalRequest.url?.includes(API_ENDPOINTS.AUTH.REFRESH)
      ) {
        return Promise.reject(formatApiError(error));
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
      if (!refreshToken) {
        isRefreshing = false;
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        return Promise.reject(formatApiError(error));
      }

      try {
        const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.AUTH.REFRESH}`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = response.data.access_token;
        localStorage.setItem(TOKEN_STORAGE_KEY, newAccessToken);
        if (response.data.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, response.data.refresh_token);
        }

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
        return Promise.reject(formatApiError(refreshErr as AxiosError<ApiErrorResponse>));
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(formatApiError(error));
  }
);

export function formatApiError(error: any): {
  code: string;
  message: string;
  status: number;
} {
  // If already formatted by response interceptor, preserve the original typed error
  if (
    error &&
    typeof error === 'object' &&
    typeof error.code === 'string' &&
    typeof error.message === 'string' &&
    typeof error.status === 'number'
  ) {
    return error;
  }

  if (error?.response?.data?.error) {
    return {
      code: error.response.data.error.code || 'UNKNOWN_ERROR',
      message: error.response.data.error.message || 'An unexpected error occurred.',
      status: error.response.status,
    };
  }

  if (error?.code === 'ECONNABORTED' || error?.message?.toLowerCase().includes('timeout')) {
    return {
      code: 'TIMEOUT_ERROR',
      message: 'Analysis timed out. The target server or threat intelligence feeds are taking longer than expected.',
      status: 408,
    };
  }

  if (error?.message === 'Network Error' || (error && !error.response)) {
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the TrustGuard AI backend. Check server status.',
      status: 0,
    };
  }

  return {
    code: 'CLIENT_ERROR',
    message: error?.message || 'An error occurred during request processing.',
    status: error?.response ? error.response.status : 500,
  };
}

export default apiClient;

