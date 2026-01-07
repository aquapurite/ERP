import apiClient, { setTokens, clearTokens } from './client';
import { LoginRequest, LoginResponse, User, UserPermissions, Role } from '@/types';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', credentials);
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      clearTokens();
    }
  },

  getCurrentUser: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },

  getUserPermissions: async (): Promise<UserPermissions> => {
    const { data } = await apiClient.get<{
      is_super_admin?: boolean;
      roles?: Role[];
      permissions_by_module?: Record<string, string[]>;
      total_permissions?: number;
    }>('/access-control/access/user-access-summary');
    // Transform API response to expected format
    const permissions: Record<string, boolean> = {};
    if (data.permissions_by_module) {
      Object.values(data.permissions_by_module).forEach((perms) => {
        perms.forEach((perm) => {
          permissions[perm] = true;
        });
      });
    }
    return {
      is_super_admin: data.is_super_admin || false,
      roles: data.roles,
      permissions_by_module: data.permissions_by_module,
      total_permissions: data.total_permissions,
      permissions,
    };
  },

  refreshToken: async (refreshToken: string): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    setTokens(data.access_token, data.refresh_token);
    return data;
  },
};
