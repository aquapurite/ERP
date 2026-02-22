'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { User, UserPermissions, LoginRequest } from '@/types';
import { authApi } from '@/lib/api';
import { getAccessToken } from '@/lib/api/client';

interface AuthContextType {
  user: User | null;
  permissions: UserPermissions | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasPermission: (code: string) => boolean;
  hasAnyPermission: (codes: string[]) => boolean;
  hasAllPermissions: (codes: string[]) => boolean;
}

const AUTH_CACHE_KEY = 'cached_auth';
const AUTH_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<UserPermissions | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;

  const fetchUserAndPermissions = useCallback(async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      const [userData, permissionsData] = await Promise.all([
        authApi.getCurrentUser(),
        authApi.getUserPermissions(),
      ]);

      setUser(userData);
      setPermissions(permissionsData);

      // Cache to sessionStorage for fast subsequent navigations
      try {
        sessionStorage.setItem(AUTH_CACHE_KEY, JSON.stringify({
          user: userData,
          permissions: permissionsData,
          timestamp: Date.now(),
        }));
      } catch {
        // sessionStorage may be unavailable (SSR, private mode) — ignore
      }
    } catch {
      setUser(null);
      setPermissions(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    // Check sessionStorage cache first
    try {
      const cached = sessionStorage.getItem(AUTH_CACHE_KEY);
      if (cached) {
        const { user: cachedUser, permissions: cachedPerms, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < AUTH_CACHE_TTL) {
          // Cache is fresh — render immediately, revalidate silently in background
          setUser(cachedUser);
          setPermissions(cachedPerms);
          setIsLoading(false);
          // Background revalidation (non-blocking)
          fetchUserAndPermissions();
          return;
        }
      }
    } catch {
      // Ignore cache read errors
    }

    // No valid cache — normal fetch
    fetchUserAndPermissions();
  }, [fetchUserAndPermissions]);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      await authApi.login(credentials);
      // Clear stale cache on login
      try { sessionStorage.removeItem(AUTH_CACHE_KEY); } catch { /* ignore */ }
      await fetchUserAndPermissions();
      router.push('/dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setPermissions(null);
      setIsLoading(false);
      // Clear auth cache on logout
      try { sessionStorage.removeItem(AUTH_CACHE_KEY); } catch { /* ignore */ }
      router.push('/login');
    }
  };

  const refreshUser = async () => {
    try { sessionStorage.removeItem(AUTH_CACHE_KEY); } catch { /* ignore */ }
    await fetchUserAndPermissions();
  };

  const hasPermission = useCallback(
    (code: string): boolean => {
      if (!permissions) return false;
      if (permissions.is_super_admin) return true;
      return permissions.permissions[code] === true;
    },
    [permissions]
  );

  const hasAnyPermission = useCallback(
    (codes: string[]): boolean => {
      return codes.some((code) => hasPermission(code));
    },
    [hasPermission]
  );

  const hasAllPermissions = useCallback(
    (codes: string[]): boolean => {
      return codes.every((code) => hasPermission(code));
    },
    [hasPermission]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        permissions,
        isLoading,
        isAuthenticated,
        login,
        logout,
        refreshUser,
        hasPermission,
        hasAnyPermission,
        hasAllPermissions,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
