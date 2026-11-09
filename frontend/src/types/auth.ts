export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  role: 'user' | 'admin' | string;
  created_at?: string;
  email_confirmed_at?: string | null;
}

export interface AuthSession {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
  profile?: UserProfile | null;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  threat_digest_enabled?: boolean;
  scan_count: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferences {
  threat_digest_enabled: boolean;
  email: string;
  updated_at: string;
  provider_configured: boolean;
}

export interface UserRegisterPayload {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
}

export interface UserLoginPayload {
  email: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  new_password: string;
  confirm_new_password: string;
}

export interface UserUpdatePayload {
  full_name?: string | null;
  avatar_url?: string | null;
  threat_digest_enabled?: boolean;
}

export interface OAuthUrlResponse {
  url: string;
  provider: string;
}

export interface OAuthCallbackPayload {
  code?: string;
  access_token?: string;
  refresh_token?: string;
}

export interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: UserLoginPayload, remember?: boolean) => Promise<void>;
  loginWithGoogle: (redirectTo?: string) => Promise<void>;
  handleOAuthCallback: (payload: OAuthCallbackPayload) => Promise<void>;
  register: (payload: UserRegisterPayload) => Promise<void>;
  resendVerification: (email: string) => Promise<string>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<string>;
  resetPassword: (payload: ResetPasswordPayload) => Promise<string>;
  updateProfile: (payload: UserUpdatePayload) => Promise<UserProfile>;
  refreshProfile: () => Promise<void>;
}
