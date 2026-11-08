import React, { createContext, useContext, useEffect, useState } from 'react';
import { AdminUser } from '../types/admin';
import { ADMIN_TOKEN_KEY, ADMIN_USER_KEY, adminService } from '../services/adminService';

interface AdminAuthContextType {
  adminUser: AdminUser | null;
  adminToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAdmin: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export const AdminAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [adminUser, setAdminUser] = useState<AdminUser | null>(() => {
    const saved = localStorage.getItem(ADMIN_USER_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [adminToken, setAdminToken] = useState<string | null>(() =>
    localStorage.getItem(ADMIN_TOKEN_KEY)
  );
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyToken = async () => {
      const token = localStorage.getItem(ADMIN_TOKEN_KEY);
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const user = await adminService.getMe();
        setAdminUser(user);
        setAdminToken(token);
        localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(user));
      } catch {
        // Token invalid or expired
        localStorage.removeItem(ADMIN_TOKEN_KEY);
        localStorage.removeItem(ADMIN_USER_KEY);
        setAdminUser(null);
        setAdminToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    verifyToken();
  }, []);

  const login = async (username: string, password: string) => {
    const res = await adminService.login(username, password);
    setAdminUser(res.admin_user);
    setAdminToken(res.access_token);
  };

  const logout = async () => {
    await adminService.logout();
    setAdminUser(null);
    setAdminToken(null);
  };

  const refreshAdmin = async () => {
    try {
      const user = await adminService.getMe();
      setAdminUser(user);
      localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(user));
    } catch {
      // Ignored
    }
  };

  return (
    <AdminAuthContext.Provider
      value={{
        adminUser,
        adminToken,
        isAuthenticated: !!adminToken && !!adminUser,
        isLoading,
        login,
        logout,
        refreshAdmin,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
};

export const useAdminAuth = (): AdminAuthContextType => {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
};
