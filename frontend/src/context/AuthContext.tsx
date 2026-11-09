import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import {
  AuthContextType,
  OAuthCallbackPayload,
  ResetPasswordPayload,
  User,
  UserLoginPayload,
  UserProfile,
  UserRegisterPayload,
  UserUpdatePayload,
} from '../types/auth';
import {
  authService,
  TOKEN_STORAGE_KEY,
  REFRESH_TOKEN_STORAGE_KEY,
  USER_STORAGE_KEY,
  PROFILE_STORAGE_KEY,
} from '../services';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem(USER_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [profile, setProfile] = useState<UserProfile | null>(() => {
    try {
      const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  // Fast initialization: If credentials exist in local storage, render immediately (< 5ms)
  // Guest mode (no token) also renders immediately
  // Only wait if a token exists without any cached user identity
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);
    return !!token && !storedUser;
  });

  const isAuthenticated = useMemo(() => !!user && !!localStorage.getItem(TOKEN_STORAGE_KEY), [user]);

  // Synchronize authenticated identity and profile on mount (Stale-While-Revalidate)
  const refreshProfile = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setUser(null);
      setProfile(null);
      return;
    }

    try {
      const [userData, profileData] = await Promise.all([
        authService.getMe().catch((err) => {
          if (err?.status === 401 || err?.response?.status === 401) throw err;
          return null;
        }),
        authService.getUserProfile().catch((err) => {
          if (err?.status === 401 || err?.response?.status === 401) throw err;
          return null;
        }),
      ]);

      if (userData) {
        setUser(userData);
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
      }

      if (profileData) {
        setProfile(profileData);
        localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profileData));
      }
    } catch (err: any) {
      if (err?.status === 401 || err?.response?.status === 401) {
        console.warn('Session verification failed (401 Unauthorized), clearing session.');
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
        localStorage.removeItem(PROFILE_STORAGE_KEY);
        setUser(null);
        setProfile(null);
      } else {
        console.warn('Background profile refresh deferred:', err);
      }
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (token) {
        await refreshProfile();
      }
      setIsLoading(false);
    };

    initAuth();
  }, [refreshProfile]);

  const login = useCallback(async (payload: UserLoginPayload) => {
    setIsLoading(true);
    try {
      const session = await authService.login(payload);
      localStorage.setItem(TOKEN_STORAGE_KEY, session.access_token);
      if (session.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, session.refresh_token);
      }
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(session.user));
      setUser(session.user);

      // Instant preliminary profile to prevent skeleton lag
      const defaultProfile: UserProfile = {
        id: session.user.id,
        email: session.user.email,
        full_name: session.user.full_name || null,
        avatar_url: session.user.avatar_url || null,
        scan_count: 0,
        is_active: true,
        threat_digest_enabled: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setProfile(defaultProfile);
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(defaultProfile));

      // Asynchronously fetch complete profile in background without blocking navigation
      authService
        .getUserProfile()
        .then((profileData) => {
          setProfile(profileData);
          localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profileData));
        })
        .catch(() => {});
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (payload: UserRegisterPayload) => {
    setIsLoading(true);
    try {
      const session = await authService.register(payload);
      localStorage.setItem(TOKEN_STORAGE_KEY, session.access_token);
      if (session.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, session.refresh_token);
      }
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(session.user));
      setUser(session.user);

      // Instant preliminary profile
      const defaultProfile: UserProfile = {
        id: session.user.id,
        email: session.user.email,
        full_name: session.user.full_name || null,
        avatar_url: session.user.avatar_url || null,
        scan_count: 0,
        is_active: true,
        threat_digest_enabled: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setProfile(defaultProfile);
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(defaultProfile));

      authService
        .getUserProfile()
        .then((profileData) => {
          setProfile(profileData);
          localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profileData));
        })
        .catch(() => {});
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async (redirectTo?: string) => {
    setIsLoading(true);
    try {
      const res = await authService.getGoogleOAuthUrl(redirectTo);
      if (res?.url) {
        window.location.href = res.url;
      } else {
        throw new Error('No authorization URL returned from identity provider.');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleOAuthCallback = useCallback(async (payload: OAuthCallbackPayload) => {
    setIsLoading(true);
    try {
      const session = await authService.handleOAuthCallback(payload);
      localStorage.setItem(TOKEN_STORAGE_KEY, session.access_token);
      if (session.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, session.refresh_token);
      }
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(session.user));
      setUser(session.user);

      const defaultProfile: UserProfile = {
        id: session.user.id,
        email: session.user.email,
        full_name: session.user.full_name || null,
        avatar_url: session.user.avatar_url || null,
        scan_count: 0,
        is_active: true,
        threat_digest_enabled: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setProfile(defaultProfile);
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(defaultProfile));

      authService
        .getUserProfile()
        .then((profileData) => {
          setProfile(profileData);
          localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profileData));
        })
        .catch(() => {});
    } finally {
      setIsLoading(false);
    }
  }, []);

  const resendVerification = useCallback(async (email: string): Promise<string> => {
    const res = await authService.resendVerification(email);
    return res.message;
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
      localStorage.removeItem(USER_STORAGE_KEY);
      localStorage.removeItem(PROFILE_STORAGE_KEY);
      setUser(null);
      setProfile(null);
      setIsLoading(false);
    }
  }, []);

  const forgotPassword = useCallback(async (email: string): Promise<string> => {
    const res = await authService.forgotPassword(email);
    return res.message;
  }, []);

  const resetPassword = useCallback(async (payload: ResetPasswordPayload): Promise<string> => {
    const res = await authService.resetPassword(payload);
    return res.message;
  }, []);

  const updateProfile = useCallback(async (payload: UserUpdatePayload): Promise<UserProfile> => {
    const updated = await authService.updateUserProfile(payload);
    setProfile(updated);
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(updated));
    if (user) {
      const updatedUser: User = {
        ...user,
        full_name: updated.full_name,
        avatar_url: updated.avatar_url,
      };
      setUser(updatedUser);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updatedUser));
    }
    return updated;
  }, [user]);

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      profile,
      isAuthenticated,
      isLoading,
      login,
      loginWithGoogle,
      handleOAuthCallback,
      register,
      resendVerification,
      logout,
      forgotPassword,
      resetPassword,
      updateProfile,
      refreshProfile,
    }),
    [
      user,
      profile,
      isAuthenticated,
      isLoading,
      login,
      loginWithGoogle,
      handleOAuthCallback,
      register,
      resendVerification,
      logout,
      forgotPassword,
      resetPassword,
      updateProfile,
      refreshProfile,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
