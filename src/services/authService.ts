import apiClient from './api';
import { API_ENDPOINTS } from './apiConfig';
import {
  AuthSession,
  ForgotPasswordPayload,
  NotificationPreferences,
  OAuthCallbackPayload,
  OAuthUrlResponse,
  ResetPasswordPayload,
  User,
  UserLoginPayload,
  UserProfile,
  UserRegisterPayload,
  UserUpdatePayload,
} from '../types/auth';

export const authService = {
  /**
   * Authenticate user with email and password via backend FastAPI /auth/login.
   */
  async login(payload: UserLoginPayload): Promise<AuthSession> {
    const response = await apiClient.post<AuthSession>(
      API_ENDPOINTS.AUTH.LOGIN,
      payload
    );
    return response.data;
  },

  /**
   * Register a new user via backend FastAPI /auth/register.
   */
  async register(payload: UserRegisterPayload): Promise<AuthSession> {
    const response = await apiClient.post<AuthSession>(
      API_ENDPOINTS.AUTH.REGISTER,
      payload
    );
    return response.data;
  },

  /**
   * Revoke active session on backend FastAPI /auth/logout.
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
    } catch (error) {
      // If token is already invalid, proceed with client logout
      console.warn('Backend logout warning:', error);
    }
  },

  /**
   * Exchange refresh token for fresh access token via /auth/refresh.
   */
  async refreshToken(refreshToken: string): Promise<AuthSession> {
    const response = await apiClient.post<AuthSession>(
      API_ENDPOINTS.AUTH.REFRESH,
      { refresh_token: refreshToken }
    );
    return response.data;
  },

  /**
   * Request password reset instructions via /auth/forgot-password.
   */
  async forgotPassword(email: string): Promise<{ message: string; success: boolean }> {
    const payload: ForgotPasswordPayload = { email };
    const response = await apiClient.post<{ message: string; success: boolean }>(
      API_ENDPOINTS.AUTH.FORGOT_PASSWORD,
      payload
    );
    return response.data;
  },

  /**
   * Set new password via /auth/reset-password.
   */
  async resetPassword(payload: ResetPasswordPayload): Promise<{ message: string; success: boolean }> {
    const response = await apiClient.post<{ message: string; success: boolean }>(
      API_ENDPOINTS.AUTH.RESET_PASSWORD,
      payload
    );
    return response.data;
  },

  /**
   * Retrieve current authenticated user identity via /auth/me.
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    return response.data;
  },

  /**
   * Retrieve user profile and scan statistics via /users/me.
   */
  async getUserProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>(API_ENDPOINTS.USERS.ME);
    return response.data;
  },

  /**
   * Update editable profile fields (full_name, avatar_url, threat_digest_enabled) via /users/me.
   */
  async updateUserProfile(payload: UserUpdatePayload): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>(
      API_ENDPOINTS.USERS.ME,
      payload
    );
    return response.data;
  },

  /**
   * Retrieve notification preferences via /users/me/notifications.
   */
  async getNotificationPreferences(): Promise<NotificationPreferences> {
    const response = await apiClient.get<NotificationPreferences>(
      API_ENDPOINTS.USERS.NOTIFICATIONS
    );
    return response.data;
  },

  /**
   * Request resending account confirmation email.
   */
  async resendVerification(email: string): Promise<{ message: string; success: boolean }> {
    const response = await apiClient.post<{ message: string; success: boolean }>(
      API_ENDPOINTS.AUTH.RESEND_VERIFICATION,
      { email }
    );
    return response.data;
  },

  /**
   * Obtain the Supabase Google OAuth authorization redirection URL.
   */
  async getGoogleOAuthUrl(redirectTo?: string): Promise<OAuthUrlResponse> {
    const response = await apiClient.get<OAuthUrlResponse>(
      API_ENDPOINTS.AUTH.GOOGLE_OAUTH,
      {
        params: redirectTo ? { redirect_to: redirectTo } : undefined,
      }
    );
    return response.data;
  },

  /**
   * Complete Google OAuth session by submitting authorization code or hash tokens.
   */
  async handleOAuthCallback(payload: OAuthCallbackPayload): Promise<AuthSession> {
    const response = await apiClient.post<AuthSession>(
      API_ENDPOINTS.AUTH.OAUTH_CALLBACK,
      payload
    );
    return response.data;
  },

  /**
   * Update notification preferences via /users/me/notifications.
   */
  async updateNotificationPreferences(
    threat_digest_enabled: boolean
  ): Promise<NotificationPreferences> {
    const response = await apiClient.patch<NotificationPreferences>(
      API_ENDPOINTS.USERS.NOTIFICATIONS,
      { threat_digest_enabled }
    );
    return response.data;
  },
};

export default authService;

