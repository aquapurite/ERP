import apiClient from './client';
import { PaginatedResponse, User, Role, Permission, Product, Category, Brand, Order, Customer, Warehouse, StockItem, Vendor, PurchaseOrder, ServiceRequest, Dealer } from '@/types';

// Export auth API
export { authApi } from './auth';

// Users API
export const usersApi = {
  list: async (params?: { page?: number; size?: number; search?: string; is_active?: boolean }) => {
    const { data } = await apiClient.get<PaginatedResponse<User>>('/users', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<User>(`/users/${id}`);
    return data;
  },
  create: async (user: Partial<User> & { password: string }) => {
    const { data } = await apiClient.post<User>('/users', user);
    return data;
  },
  update: async (id: string, user: Partial<User>) => {
    const { data } = await apiClient.put<User>(`/users/${id}`, user);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/users/${id}`);
  },
  assignRoles: async (userId: string, roleIds: string[]) => {
    const { data } = await apiClient.put<User>(`/users/${userId}/roles`, { role_ids: roleIds });
    return data;
  },
};

// Roles API
export const rolesApi = {
  list: async (params?: { page?: number; size?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Role>>('/roles', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Role>(`/roles/${id}`);
    return data;
  },
  create: async (role: Partial<Role>) => {
    const { data } = await apiClient.post<Role>('/roles', role);
    return data;
  },
  update: async (id: string, role: Partial<Role>) => {
    const { data } = await apiClient.put<Role>(`/roles/${id}`, role);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/roles/${id}`);
  },
  assignPermissions: async (roleId: string, permissionIds: string[]) => {
    const { data } = await apiClient.put<Role>(`/roles/${roleId}/permissions`, { permission_ids: permissionIds });
    return data;
  },
};

// Permissions API
export const permissionsApi = {
  list: async (params?: { module?: string }) => {
    const { data } = await apiClient.get<Permission[]>('/permissions', { params });
    return data;
  },
  getModules: async () => {
    const { data } = await apiClient.get<string[]>('/permissions/modules');
    return data;
  },
};

// Products API
export const productsApi = {
  list: async (params?: { page?: number; size?: number; search?: string; category_id?: string; brand_id?: string; is_active?: boolean }) => {
    const { data } = await apiClient.get<PaginatedResponse<Product>>('/products', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Product>(`/products/${id}`);
    return data;
  },
  create: async (product: Partial<Product>) => {
    const { data } = await apiClient.post<Product>('/products', product);
    return data;
  },
  update: async (id: string, product: Partial<Product>) => {
    const { data } = await apiClient.put<Product>(`/products/${id}`, product);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/products/${id}`);
  },
};

// Categories API
export const categoriesApi = {
  list: async (params?: { page?: number; size?: number; is_active?: boolean }) => {
    const { data } = await apiClient.get<PaginatedResponse<Category>>('/categories', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Category>(`/categories/${id}`);
    return data;
  },
  create: async (category: Partial<Category>) => {
    const { data } = await apiClient.post<Category>('/categories', category);
    return data;
  },
  update: async (id: string, category: Partial<Category>) => {
    const { data } = await apiClient.put<Category>(`/categories/${id}`, category);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/categories/${id}`);
  },
};

// Brands API
export const brandsApi = {
  list: async (params?: { page?: number; size?: number; is_active?: boolean }) => {
    const { data } = await apiClient.get<PaginatedResponse<Brand>>('/brands', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Brand>(`/brands/${id}`);
    return data;
  },
  create: async (brand: Partial<Brand>) => {
    const { data } = await apiClient.post<Brand>('/brands', brand);
    return data;
  },
  update: async (id: string, brand: Partial<Brand>) => {
    const { data } = await apiClient.put<Brand>(`/brands/${id}`, brand);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/brands/${id}`);
  },
};

// Orders API
export const ordersApi = {
  list: async (params?: { page?: number; size?: number; status?: string; search?: string; channel?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<Order>>('/orders', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Order>(`/orders/${id}`);
    return data;
  },
  create: async (order: Partial<Order>) => {
    const { data } = await apiClient.post<Order>('/orders', order);
    return data;
  },
  updateStatus: async (id: string, status: string, notes?: string) => {
    const { data } = await apiClient.put<Order>(`/orders/${id}/status`, { status, notes });
    return data;
  },
  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post<Order>(`/orders/${id}/cancel`, { reason });
    return data;
  },
};

// Customers API
export const customersApi = {
  list: async (params?: { page?: number; size?: number; search?: string; customer_type?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<Customer>>('/customers', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Customer>(`/customers/${id}`);
    return data;
  },
  get360View: async (id: string) => {
    const { data } = await apiClient.get(`/customers/${id}/360`);
    return data;
  },
  create: async (customer: Partial<Customer>) => {
    const { data } = await apiClient.post<Customer>('/customers', customer);
    return data;
  },
  update: async (id: string, customer: Partial<Customer>) => {
    const { data } = await apiClient.put<Customer>(`/customers/${id}`, customer);
    return data;
  },
};

// Warehouses API
export const warehousesApi = {
  list: async (params?: { page?: number; size?: number; type?: string; is_active?: boolean }) => {
    const { data } = await apiClient.get<PaginatedResponse<Warehouse>>('/warehouses', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Warehouse>(`/warehouses/${id}`);
    return data;
  },
  create: async (warehouse: Partial<Warehouse>) => {
    const { data } = await apiClient.post<Warehouse>('/warehouses', warehouse);
    return data;
  },
  update: async (id: string, warehouse: Partial<Warehouse>) => {
    const { data } = await apiClient.put<Warehouse>(`/warehouses/${id}`, warehouse);
    return data;
  },
};

// Inventory API
export const inventoryApi = {
  getStock: async (params?: { page?: number; size?: number; warehouse_id?: string; product_id?: string; status?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<StockItem>>('/inventory/stock-items', { params });
    return data;
  },
  getStockSummary: async () => {
    const { data } = await apiClient.get('/inventory/summary');
    return data;
  },
  getLowStock: async () => {
    const { data } = await apiClient.get('/inventory/low-stock');
    return data;
  },
  getStats: async () => {
    const { data } = await apiClient.get('/inventory/stats');
    return data;
  },
  adjustStock: async (adjustment: { product_id: string; warehouse_id: string; quantity: number; reason: string }) => {
    const { data } = await apiClient.post('/inventory/adjust', adjustment);
    return data;
  },
};

// Vendors API
export const vendorsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; search?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<Vendor>>('/vendors', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Vendor>(`/vendors/${id}`);
    return data;
  },
  create: async (vendor: Partial<Vendor>) => {
    const { data } = await apiClient.post<Vendor>('/vendors', vendor);
    return data;
  },
  update: async (id: string, vendor: Partial<Vendor>) => {
    const { data } = await apiClient.put<Vendor>(`/vendors/${id}`, vendor);
    return data;
  },
};

// Purchase Orders API
export const purchaseOrdersApi = {
  list: async (params?: { page?: number; size?: number; status?: string; vendor_id?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<PurchaseOrder>>('/purchase/orders', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<PurchaseOrder>(`/purchase/orders/${id}`);
    return data;
  },
  create: async (po: Partial<PurchaseOrder>) => {
    const { data } = await apiClient.post<PurchaseOrder>('/purchase/orders', po);
    return data;
  },
  update: async (id: string, po: Partial<PurchaseOrder>) => {
    const { data } = await apiClient.put<PurchaseOrder>(`/purchase/orders/${id}`, po);
    return data;
  },
  submit: async (id: string) => {
    const { data } = await apiClient.post<PurchaseOrder>(`/purchase/orders/${id}/submit`);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post<PurchaseOrder>(`/purchase/orders/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post<PurchaseOrder>(`/purchase/orders/${id}/reject`, { reason });
    return data;
  },
};

// Service Requests API
export const serviceRequestsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; type?: string; priority?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<ServiceRequest>>('/service-requests', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<ServiceRequest>(`/service-requests/${id}`);
    return data;
  },
  create: async (request: Partial<ServiceRequest>) => {
    const { data } = await apiClient.post<ServiceRequest>('/service-requests', request);
    return data;
  },
  update: async (id: string, request: Partial<ServiceRequest>) => {
    const { data } = await apiClient.put<ServiceRequest>(`/service-requests/${id}`, request);
    return data;
  },
  assignTechnician: async (id: string, technicianId: string) => {
    const { data } = await apiClient.post<ServiceRequest>(`/service-requests/${id}/assign`, { technician_id: technicianId });
    return data;
  },
  updateStatus: async (id: string, status: string, notes?: string) => {
    const { data } = await apiClient.put<ServiceRequest>(`/service-requests/${id}/status`, { status, notes });
    return data;
  },
};

// Dealers API
export const dealersApi = {
  list: async (params?: { page?: number; size?: number; type?: string; status?: string }) => {
    const { data } = await apiClient.get<PaginatedResponse<Dealer>>('/dealers', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Dealer>(`/dealers/${id}`);
    return data;
  },
  create: async (dealer: Partial<Dealer>) => {
    const { data } = await apiClient.post<Dealer>('/dealers', dealer);
    return data;
  },
  update: async (id: string, dealer: Partial<Dealer>) => {
    const { data } = await apiClient.put<Dealer>(`/dealers/${id}`, dealer);
    return data;
  },
};

// Dashboard API - aggregates data from multiple real endpoints
export const dashboardApi = {
  getStats: async () => {
    // Aggregate stats from multiple real endpoints
    try {
      const [ordersRes, productsRes, inventoryRes, serviceRes] = await Promise.allSettled([
        apiClient.get('/orders/stats'),
        apiClient.get('/products/stats'),
        apiClient.get('/inventory/stats'),
        apiClient.get('/service-requests/stats'),
      ]);

      const ordersData = ordersRes.status === 'fulfilled' ? ordersRes.value.data : {};
      const productsData = productsRes.status === 'fulfilled' ? productsRes.value.data : {};
      const inventoryData = inventoryRes.status === 'fulfilled' ? inventoryRes.value.data : {};
      const serviceData = serviceRes.status === 'fulfilled' ? serviceRes.value.data : {};

      return {
        total_orders: ordersData.total || 0,
        total_revenue: ordersData.total_revenue || 0,
        pending_orders: ordersData.pending || 0,
        total_products: productsData.total || 0,
        total_customers: ordersData.total_customers || 0,
        low_stock_items: inventoryData.low_stock_count || 0,
        pending_service_requests: serviceData.pending || 0,
        shipments_in_transit: ordersData.in_transit || 0,
        orders_change: ordersData.change_percent || 0,
        revenue_change: ordersData.revenue_change_percent || 0,
        customers_change: ordersData.customers_change_percent || 0,
      };
    } catch {
      // Return defaults if APIs fail
      return {
        total_orders: 0,
        total_revenue: 0,
        pending_orders: 0,
        total_products: 0,
        total_customers: 0,
        low_stock_items: 0,
        pending_service_requests: 0,
        shipments_in_transit: 0,
        orders_change: 0,
        revenue_change: 0,
        customers_change: 0,
      };
    }
  },
  getOrderStats: async () => {
    const { data } = await apiClient.get('/orders/stats');
    return data;
  },
  getRevenueStats: async () => {
    const { data } = await apiClient.get('/orders/stats');
    return data;
  },
};

// Approvals API
export const approvalsApi = {
  getPending: async () => {
    try {
      const { data } = await apiClient.get('/approvals/pending');
      return data;
    } catch {
      return { items: [], total: 0 };
    }
  },
  getDashboard: async () => {
    try {
      const { data } = await apiClient.get('/approvals/dashboard');
      return data;
    } catch {
      return { pending: 0, approved: 0, rejected: 0 };
    }
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/approvals/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/approvals/${id}/reject`, { reason });
    return data;
  },
};

// Audit Logs API - Note: No dedicated audit-logs endpoint in backend
export const auditLogsApi = {
  list: async (params?: { page?: number; size?: number; entity_type?: string; user_id?: string; action?: string }) => {
    try {
      // Try to get from access-control activity logs
      const { data } = await apiClient.get('/access-control/access/user-access-summary', { params });
      return { items: data.activity || [], total: 0, pages: 0 };
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

export default apiClient;
