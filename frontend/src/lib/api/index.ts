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
  adminResetPassword: async (userId: string, newPassword: string) => {
    const { data } = await apiClient.post('/auth/admin-reset-password', { user_id: userId, new_password: newPassword });
    return data;
  },
};

// Roles API
// Level mapping: SUPER_ADMIN=0, DIRECTOR=1, HEAD=2, MANAGER=3, EXECUTIVE=4
const roleLevelToNumber: Record<string, number> = {
  'SUPER_ADMIN': 0,
  'DIRECTOR': 1,
  'HEAD': 2,
  'MANAGER': 3,
  'EXECUTIVE': 4,
};

export const rolesApi = {
  list: async (params?: { page?: number; size?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Role>>('/roles', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Role>(`/roles/${id}`);
    return data;
  },
  create: async (role: {
    name: string;
    code?: string;
    description?: string;
    level?: string | number;
    permission_ids?: string[];
  }) => {
    // Transform frontend fields to backend required fields
    // Backend requires: name, code, level (as number 0-4)
    const levelValue = typeof role.level === 'number'
      ? role.level
      : roleLevelToNumber[role.level || 'EXECUTIVE'] ?? 4;

    const payload = {
      name: role.name,
      code: role.code || role.name.toUpperCase().replace(/\s+/g, '_'),
      level: levelValue,
      description: role.description || undefined,
      permission_ids: role.permission_ids || [],
    };
    const { data } = await apiClient.post<Role>('/roles', payload);
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
  getByModule: async (): Promise<Record<string, Permission[]>> => {
    try {
      // Try to get permissions grouped by module from backend
      const { data } = await apiClient.get<Record<string, Permission[]>>('/permissions/by-module');
      return data;
    } catch {
      // Fallback: fetch all permissions and group by module on client
      const { data } = await apiClient.get<Permission[]>('/permissions');
      const grouped: Record<string, Permission[]> = {};
      data.forEach((permission) => {
        const module = permission.module || 'general';
        if (!grouped[module]) {
          grouped[module] = [];
        }
        grouped[module].push(permission);
      });
      return grouped;
    }
  },
};

// Products API
export const productsApi = {
  list: async (params?: { page?: number; size?: number; search?: string; category_id?: string; brand_id?: string; status?: string; is_active?: boolean; is_featured?: boolean; min_price?: number; max_price?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Product>>('/products', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Product>(`/products/${id}`);
    return data;
  },
  getBySku: async (sku: string) => {
    const { data } = await apiClient.get<Product>(`/products/sku/${sku}`);
    return data;
  },
  getBySlug: async (slug: string) => {
    const { data } = await apiClient.get<Product>(`/products/slug/${slug}`);
    return data;
  },
  getStats: async () => {
    const { data } = await apiClient.get('/products/stats');
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
  // Product Images
  addImage: async (productId: string, image: { image_url: string; thumbnail_url?: string; alt_text?: string; is_primary?: boolean; sort_order?: number }) => {
    const { data } = await apiClient.post(`/products/${productId}/images`, image);
    return data;
  },
  deleteImage: async (productId: string, imageId: string) => {
    await apiClient.delete(`/products/${productId}/images/${imageId}`);
  },
  setPrimaryImage: async (productId: string, imageId: string) => {
    const { data } = await apiClient.put(`/products/${productId}/images/${imageId}/primary`);
    return data;
  },
  // Product Variants
  addVariant: async (productId: string, variant: { name: string; sku: string; attributes?: Record<string, string>; mrp?: number; selling_price?: number; stock_quantity?: number; image_url?: string }) => {
    const { data } = await apiClient.post(`/products/${productId}/variants`, variant);
    return data;
  },
  updateVariant: async (productId: string, variantId: string, variant: Partial<{ name: string; sku: string; attributes?: Record<string, string>; mrp?: number; selling_price?: number; stock_quantity?: number; image_url?: string; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/products/${productId}/variants/${variantId}`, variant);
    return data;
  },
  deleteVariant: async (productId: string, variantId: string) => {
    await apiClient.delete(`/products/${productId}/variants/${variantId}`);
  },
  // Product Specifications
  addSpecification: async (productId: string, spec: { group_name?: string; key: string; value: string; sort_order?: number }) => {
    const { data } = await apiClient.post(`/products/${productId}/specifications`, spec);
    return data;
  },
  updateSpecification: async (productId: string, specId: string, spec: Partial<{ group_name?: string; key: string; value: string; sort_order?: number }>) => {
    const { data } = await apiClient.put(`/products/${productId}/specifications/${specId}`, spec);
    return data;
  },
  deleteSpecification: async (productId: string, specId: string) => {
    await apiClient.delete(`/products/${productId}/specifications/${specId}`);
  },
  // Product Documents
  addDocument: async (productId: string, doc: { title: string; document_type?: string; file_url: string; file_size_bytes?: number; mime_type?: string }) => {
    const { data } = await apiClient.post(`/products/${productId}/documents`, doc);
    return data;
  },
  deleteDocument: async (productId: string, docId: string) => {
    await apiClient.delete(`/products/${productId}/documents/${docId}`);
  },
};

// Categories API
export const categoriesApi = {
  list: async (params?: { page?: number; size?: number; parent_id?: string; include_inactive?: boolean }) => {
    const { data } = await apiClient.get<PaginatedResponse<Category>>('/categories', { params });
    return data;
  },
  getTree: async () => {
    const { data } = await apiClient.get('/categories/tree');
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Category>(`/categories/${id}`);
    return data;
  },
  getBySlug: async (slug: string) => {
    const { data } = await apiClient.get<Category>(`/categories/slug/${slug}`);
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
  create: async (brand: {
    name: string;
    code?: string;
    slug?: string;
    description?: string;
    logo_url?: string;
    is_active?: boolean;
  }) => {
    // Transform frontend fields to backend required fields
    // Backend requires: name and slug
    const payload = {
      name: brand.name,
      slug: brand.slug || brand.code?.toLowerCase() || brand.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
      description: brand.description || undefined,
      logo_url: brand.logo_url || undefined,
      is_active: brand.is_active ?? true,
    };
    const { data } = await apiClient.post<Brand>('/brands', payload);
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
  create: async (customer: {
    name?: string;
    first_name?: string;
    last_name?: string;
    phone: string;
    email?: string;
    customer_type?: string;
    address_line1?: string;
    address_line2?: string;
    city?: string;
    state?: string;
    pincode?: string;
    gst_number?: string;
    notes?: string;
  }) => {
    // Transform frontend fields to backend required fields
    // Backend expects first_name, not name
    const nameParts = (customer.name || '').trim().split(' ');
    const payload = {
      first_name: customer.first_name || nameParts[0] || 'Customer',
      last_name: customer.last_name || nameParts.slice(1).join(' ') || undefined,
      phone: customer.phone,
      email: customer.email || undefined,
      customer_type: customer.customer_type || 'INDIVIDUAL',
      address_line1: customer.address_line1 || undefined,
      address_line2: customer.address_line2 || undefined,
      city: customer.city || undefined,
      state: customer.state || undefined,
      pincode: customer.pincode || undefined,
      gstin: customer.gst_number || undefined,
      notes: customer.notes || undefined,
    };
    const { data } = await apiClient.post<Customer>('/customers', payload);
    return data;
  },
  update: async (id: string, customer: Partial<Customer>) => {
    const { data } = await apiClient.put<Customer>(`/customers/${id}`, customer);
    return data;
  },
  searchByPhone: async (phone: string) => {
    // Search customers by phone number
    const { data } = await apiClient.get<PaginatedResponse<Customer>>('/customers', { params: { search: phone, size: 10 } });
    return data.items;
  },
  getByPhone: async (phone: string) => {
    try {
      const { data } = await apiClient.get<Customer>(`/customers/phone/${encodeURIComponent(phone)}`);
      return data;
    } catch {
      return null;
    }
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
  create: async (warehouse: {
    name: string;
    code: string;
    type?: string;
    address?: string;
    city?: string;
    state?: string;
    pincode?: string;
    capacity?: number;
    is_active?: boolean;
  }) => {
    // Transform frontend fields to backend fields
    const payload = {
      name: warehouse.name,
      code: warehouse.code,
      warehouse_type: warehouse.type?.toLowerCase() || 'main',
      address_line1: warehouse.address || '',
      city: warehouse.city,
      state: warehouse.state,
      pincode: warehouse.pincode,
      total_capacity: warehouse.capacity || 0,
      is_active: warehouse.is_active ?? true,
    };
    const { data } = await apiClient.post<Warehouse>('/warehouses', payload);
    return data;
  },
  update: async (id: string, warehouse: Partial<{
    name: string;
    code: string;
    type: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    capacity: number;
    is_active: boolean;
  }>) => {
    // Transform frontend fields to backend fields
    const payload: Record<string, unknown> = {};
    if (warehouse.name !== undefined) payload.name = warehouse.name;
    if (warehouse.code !== undefined) payload.code = warehouse.code;
    if (warehouse.type !== undefined) payload.warehouse_type = warehouse.type.toLowerCase();
    if (warehouse.address !== undefined) payload.address_line1 = warehouse.address;
    if (warehouse.city !== undefined) payload.city = warehouse.city;
    if (warehouse.state !== undefined) payload.state = warehouse.state;
    if (warehouse.pincode !== undefined) payload.pincode = warehouse.pincode;
    if (warehouse.capacity !== undefined) payload.total_capacity = warehouse.capacity;
    if (warehouse.is_active !== undefined) payload.is_active = warehouse.is_active;
    const { data } = await apiClient.put<Warehouse>(`/warehouses/${id}`, payload);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/warehouses/${id}`);
  },
  dropdown: async () => {
    // Use dedicated dropdown endpoint for better performance
    const { data } = await apiClient.get<Array<{ id: string; name: string; code: string; warehouse_type: string }>>('/warehouses/dropdown');
    return data;
  },
};

// Channels API
export const channelsApi = {
  list: async (params?: { page?: number; size?: number; channel_type?: string; status?: string; search?: string }) => {
    const { data } = await apiClient.get('/channels', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/channels/${id}`);
    return data;
  },
  create: async (channel: { name: string; channel_type: string; description?: string }) => {
    const { data } = await apiClient.post('/channels', channel);
    return data;
  },
  update: async (id: string, channel: Partial<{ name: string; channel_type: string; description?: string; status?: string }>) => {
    const { data } = await apiClient.put(`/channels/${id}`, channel);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/channels/${id}`);
  },
  dropdown: async () => {
    // Return channels for dropdown selection
    const { data } = await apiClient.get<{ items: Array<{ id: string; channel_code: string; name: string; channel_type: string }> }>('/channels/dropdown');
    return data.items;
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
// Helper to transform vendor response from backend to frontend format
const transformVendorResponse = (vendor: Record<string, unknown>): Vendor => ({
  id: vendor.id as string,
  name: vendor.name as string,
  code: (vendor.vendor_code || vendor.code || '') as string,
  email: vendor.email as string | undefined,
  phone: vendor.phone as string | undefined,
  gst_number: (vendor.gstin || vendor.gst_number) as string | undefined,
  pan_number: (vendor.pan || vendor.pan_number) as string | undefined,
  status: (vendor.status || 'ACTIVE') as Vendor['status'],
  tier: (vendor.grade || vendor.tier || 'SILVER') as Vendor['tier'],
  created_at: vendor.created_at as string,
  contact_person: vendor.contact_person as string | undefined,
  city: vendor.city as string | undefined,
  state: vendor.state as string | undefined,
});

export const vendorsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; search?: string }) => {
    const { data } = await apiClient.get<{ items: Record<string, unknown>[]; total: number; pages: number }>('/vendors', { params });
    return {
      ...data,
      items: data.items.map(transformVendorResponse),
    };
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<Record<string, unknown>>(`/vendors/${id}`);
    return transformVendorResponse(data);
  },
  getNextCode: async (vendorType: string = 'MANUFACTURER') => {
    const { data } = await apiClient.get<{ next_code: string; prefix: string }>('/vendors/next-code', {
      params: { vendor_type: vendorType }
    });
    return data;
  },
  create: async (vendor: {
    name: string;
    code?: string;
    email?: string;
    phone?: string;
    gst_number?: string;
    pan_number?: string;
    tier?: string;
    vendor_type?: string;
    contact_person?: string;
    address_line1: string;
    city: string;
    state: string;
    pincode: string;
  }) => {
    // Transform frontend fields to backend required fields
    const payload = {
      name: vendor.name,
      legal_name: vendor.name, // Use name as legal_name
      vendor_type: vendor.vendor_type || 'MANUFACTURER',
      address_line1: vendor.address_line1,
      city: vendor.city,
      state: vendor.state,
      pincode: vendor.pincode,
      contact_person: vendor.contact_person || undefined,
      email: vendor.email || undefined,
      phone: vendor.phone || undefined,
      gstin: vendor.gst_number || undefined,
      pan: vendor.pan_number || undefined,
    };
    const { data } = await apiClient.post<Record<string, unknown>>('/vendors', payload);
    return transformVendorResponse(data);
  },
  update: async (id: string, vendor: Partial<Vendor>) => {
    const { data } = await apiClient.put<Record<string, unknown>>(`/vendors/${id}`, vendor);
    return transformVendorResponse(data);
  },
  delete: async (id: string) => {
    await apiClient.delete(`/vendors/${id}`);
  },
};

// Purchase Requisitions API
export interface PurchaseRequisition {
  id: string;
  requisition_number: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CONVERTED' | 'CANCELLED';
  requesting_department?: string;
  priority?: string;
  reason?: string;
  request_date: string;
  required_by_date?: string;
  delivery_warehouse_id: string;
  delivery_warehouse_name?: string;
  estimated_total?: number;
  approved_by?: string;
  approved_at?: string;
  items: Array<{
    id: string;
    product_id: string;
    product_name: string;
    sku: string;
    quantity_requested: number;
    estimated_unit_price?: number;
    uom?: string;
    preferred_vendor_id?: string;
    preferred_vendor_name?: string;
    notes?: string;
    monthly_quantities?: Record<string, number>;
  }>;
  created_at: string;
  updated_at: string;
}

export const purchaseRequisitionsApi = {
  getNextNumber: async () => {
    const { data } = await apiClient.get<{ next_number: string; prefix: string }>('/purchase/requisitions/next-number');
    return data;
  },
  list: async (params?: { page?: number; size?: number; status?: string; warehouse_id?: string }) => {
    const queryParams: Record<string, unknown> = {};
    if (params?.page !== undefined) queryParams.skip = (params.page) * (params.size || 50);
    if (params?.size) queryParams.limit = params.size;
    if (params?.status) queryParams.status = params.status;
    if (params?.warehouse_id) queryParams.warehouse_id = params.warehouse_id;
    const { data } = await apiClient.get<{ items: PurchaseRequisition[]; total: number }>('/purchase/requisitions', { params: queryParams });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get<PurchaseRequisition>(`/purchase/requisitions/${id}`);
    return data;
  },
  // Get open (approved but not converted) PRs for PO creation
  getOpenForPO: async () => {
    const { data } = await apiClient.get<{ items: PurchaseRequisition[]; total: number }>('/purchase/requisitions', {
      params: { status: 'APPROVED', limit: 100 }
    });
    return data.items;
  },
  create: async (pr: Partial<PurchaseRequisition>) => {
    const { data } = await apiClient.post<PurchaseRequisition>('/purchase/requisitions', pr);
    return data;
  },
  submit: async (id: string) => {
    const { data } = await apiClient.post<PurchaseRequisition>(`/purchase/requisitions/${id}/submit`);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post<PurchaseRequisition>(`/purchase/requisitions/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post<PurchaseRequisition>(`/purchase/requisitions/${id}/reject`, { reason });
    return data;
  },
  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post<PurchaseRequisition>(`/purchase/requisitions/${id}/cancel`, { reason });
    return data;
  },
  convertToPO: async (id: string, data?: { vendor_id?: string }) => {
    const { data: result } = await apiClient.post<PurchaseOrder>(`/purchase/requisitions/${id}/convert-to-po`, data);
    return result;
  },
};

// Purchase Orders API
export const purchaseOrdersApi = {
  getNextNumber: async () => {
    const { data } = await apiClient.get<{ next_number: string; prefix: string }>('/purchase/orders/next-number');
    return data;
  },
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
  delete: async (id: string) => {
    await apiClient.delete(`/purchase/orders/${id}`);
  },
  download: async (id: string) => {
    const { data } = await apiClient.get<string>(`/purchase/orders/${id}/download`);
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
  create: async (dealer: {
    name: string;
    code?: string;
    type?: string;
    email: string;
    phone: string;
    gst_number: string;
    pan: string;
    contact_person: string;
    pricing_tier?: string;
    credit_limit?: number;
    address_line1: string;
    city: string;
    district: string;
    state: string;
    state_code: string;
    pincode: string;
    region: string;
  }) => {
    // Transform frontend fields to backend required fields
    const payload = {
      name: dealer.name,
      legal_name: dealer.name,
      dealer_type: dealer.type || 'DEALER',
      gstin: dealer.gst_number,
      pan: dealer.pan,
      contact_person: dealer.contact_person || dealer.name,
      email: dealer.email,
      phone: dealer.phone,
      registered_address_line1: dealer.address_line1,
      registered_city: dealer.city,
      registered_district: dealer.district,
      registered_state: dealer.state,
      registered_state_code: dealer.state_code,
      registered_pincode: dealer.pincode,
      region: dealer.region,
      state: dealer.state,
      tier: dealer.pricing_tier || 'STANDARD',
      credit_limit: dealer.credit_limit || 0,
    };
    const { data } = await apiClient.post<Dealer>('/dealers', payload);
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

// WMS Zones API
export const zonesApi = {
  list: async (params?: { page?: number; size?: number; warehouse_id?: string }) => {
    const { data } = await apiClient.get('/wms/zones', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/wms/zones/${id}`);
    return data;
  },
  create: async (zone: { name: string; code: string; warehouse_id: string; zone_type?: string; description?: string; is_active?: boolean }) => {
    const { data } = await apiClient.post('/wms/zones', zone);
    return data;
  },
  update: async (id: string, zone: Partial<{ name: string; code: string; zone_type?: string; description?: string; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/wms/zones/${id}`, zone);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/wms/zones/${id}`);
  },
};

// WMS Bins API
export const binsApi = {
  list: async (params?: { page?: number; size?: number; warehouse_id?: string; zone_id?: string }) => {
    const { data } = await apiClient.get('/wms/bins', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/wms/bins/${id}`);
    return data;
  },
  create: async (bin: { name: string; code: string; zone_id: string; aisle?: string; rack?: string; level?: string; position?: string; capacity?: number; is_active?: boolean }) => {
    const { data } = await apiClient.post('/wms/bins', bin);
    return data;
  },
  bulkCreate: async (data: { zone_id: string; prefix: string; aisles: number; racks_per_aisle: number; levels_per_rack: number; positions_per_level: number }) => {
    const { data: response } = await apiClient.post('/wms/bins/bulk', data);
    return response;
  },
  update: async (id: string, bin: Partial<{ name: string; code: string; aisle?: string; rack?: string; level?: string; position?: string; capacity?: number; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/wms/bins/${id}`, bin);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/wms/bins/${id}`);
  },
  enquiry: async (binCode: string) => {
    const { data } = await apiClient.get(`/wms/bins/enquiry/${binCode}`);
    return data;
  },
};

// Transporters API
export const transportersApi = {
  list: async (params?: { page?: number; size?: number; is_active?: boolean }) => {
    const { data } = await apiClient.get('/transporters', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/transporters/${id}`);
    return data;
  },
  create: async (transporter: { name: string; code: string; transporter_type?: string; contact_name?: string; contact_phone?: string; contact_email?: string; address?: string; tracking_url_template?: string; is_active?: boolean }) => {
    const { data } = await apiClient.post('/transporters', transporter);
    return data;
  },
  update: async (id: string, transporter: Partial<{ name: string; code: string; transporter_type?: string; contact_name?: string; contact_phone?: string; contact_email?: string; address?: string; tracking_url_template?: string; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/transporters/${id}`, transporter);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/transporters/${id}`);
  },
};

// Shipments API
export const shipmentsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; transporter_id?: string; warehouse_id?: string }) => {
    const { data } = await apiClient.get('/shipments', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/shipments/${id}`);
    return data;
  },
  create: async (shipment: { order_id: string; warehouse_id: string; transporter_id?: string; ship_to_name: string; ship_to_phone: string; ship_to_address: string; ship_to_city: string; ship_to_state: string; ship_to_pincode: string; weight_kg?: number; no_of_boxes?: number }) => {
    const { data } = await apiClient.post('/shipments', shipment);
    return data;
  },
  update: async (id: string, shipment: Partial<{ transporter_id?: string; awb_number?: string; expected_delivery_date?: string }>) => {
    const { data } = await apiClient.put(`/shipments/${id}`, shipment);
    return data;
  },
  updateStatus: async (id: string, status: string, remarks?: string) => {
    const { data } = await apiClient.put(`/shipments/${id}/status`, { status, remarks });
    return data;
  },
  addTracking: async (id: string, tracking: { status: string; location?: string; remarks?: string; event_time?: string }) => {
    const { data } = await apiClient.post(`/shipments/${id}/tracking`, tracking);
    return data;
  },
  getTracking: async (id: string) => {
    const { data } = await apiClient.get(`/shipments/${id}/tracking`);
    return data;
  },
  markDelivered: async (id: string, podData?: { receiver_name?: string; receiver_phone?: string; pod_image_url?: string; delivery_notes?: string }) => {
    const { data } = await apiClient.post(`/shipments/${id}/deliver`, podData);
    return data;
  },
  initiateRTO: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/shipments/${id}/rto`, { reason });
    return data;
  },
  getSlaDashboard: async () => {
    const { data } = await apiClient.get('/shipments/sla/dashboard');
    return data;
  },
  getAtRiskShipments: async (daysThreshold?: number) => {
    const { data } = await apiClient.get('/shipments/sla/at-risk', { params: { days_threshold: daysThreshold } });
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/shipments/${id}`);
  },
  downloadLabel: async (id: string) => {
    const { data } = await apiClient.get<string>(`/shipments/${id}/label/download`);
    return data;
  },
  downloadInvoice: async (id: string) => {
    const { data } = await apiClient.get<string>(`/shipments/${id}/invoice/download`);
    return data;
  },
};

// Manifests API
export const manifestsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; warehouse_id?: string; transporter_id?: string }) => {
    const { data } = await apiClient.get('/manifests', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/manifests/${id}`);
    return data;
  },
  create: async (manifest: { warehouse_id: string; transporter_id: string; business_type?: string; manifest_date?: string; vehicle_number?: string; driver_name?: string; driver_phone?: string; remarks?: string }) => {
    const { data } = await apiClient.post('/manifests', manifest);
    return data;
  },
  update: async (id: string, manifest: Partial<{ vehicle_number?: string; driver_name?: string; driver_phone?: string; remarks?: string }>) => {
    const { data } = await apiClient.put(`/manifests/${id}`, manifest);
    return data;
  },
  addShipments: async (id: string, shipmentIds: string[]) => {
    const { data } = await apiClient.post(`/manifests/${id}/add-shipments`, { shipment_ids: shipmentIds });
    return data;
  },
  removeShipments: async (id: string, shipmentIds: string[]) => {
    const { data } = await apiClient.post(`/manifests/${id}/remove-shipments`, { shipment_ids: shipmentIds });
    return data;
  },
  scan: async (id: string, scanData: { awb_number?: string; shipment_id?: string; barcode?: string }) => {
    const { data } = await apiClient.post(`/manifests/${id}/scan`, scanData);
    return data;
  },
  confirm: async (id: string, confirmData?: { vehicle_number?: string; driver_name?: string; driver_phone?: string; remarks?: string }) => {
    const { data } = await apiClient.post(`/manifests/${id}/confirm`, confirmData);
    return data;
  },
  handover: async (id: string, handoverRemarks?: string) => {
    const { data } = await apiClient.post(`/manifests/${id}/handover`, { handover_remarks: handoverRemarks });
    return data;
  },
  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/manifests/${id}/cancel`, { reason });
    return data;
  },
  getPrintData: async (id: string) => {
    const { data } = await apiClient.get(`/manifests/${id}/print`);
    return data;
  },
};

// Stock Transfers API
export const transfersApi = {
  list: async (params?: { page?: number; size?: number; status?: string; from_warehouse_id?: string; to_warehouse_id?: string }) => {
    const { data } = await apiClient.get('/transfers', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/transfers/${id}`);
    return data;
  },
  create: async (transfer: { from_warehouse_id: string; to_warehouse_id: string; items: { product_id: string; quantity: number }[]; notes?: string }) => {
    const { data } = await apiClient.post('/transfers', transfer);
    return data;
  },
  submit: async (id: string) => {
    const { data } = await apiClient.post(`/transfers/${id}/submit`);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/transfers/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/transfers/${id}/reject`, { reason });
    return data;
  },
  ship: async (id: string) => {
    const { data } = await apiClient.post(`/transfers/${id}/ship`);
    return data;
  },
  receive: async (id: string, items?: { stock_item_id: string; received_quantity: number }[]) => {
    const { data } = await apiClient.post(`/transfers/${id}/receive`, { items });
    return data;
  },
};

// ============================================
// FINANCE / ACCOUNTING API
// ============================================

// Chart of Accounts API
export const accountsApi = {
  list: async (params?: { page?: number; size?: number; type?: string; is_active?: boolean }) => {
    const { data } = await apiClient.get('/accounting/accounts', { params });
    return data;
  },
  getTree: async () => {
    const { data } = await apiClient.get('/accounting/accounts/tree');
    return data;
  },
  getDropdown: async () => {
    const { data } = await apiClient.get('/accounting/accounts/dropdown');
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/accounting/accounts/${id}`);
    return data;
  },
  create: async (account: { code: string; name: string; type: string; parent_id?: string; description?: string; is_group?: boolean }) => {
    const { data } = await apiClient.post('/accounting/accounts', account);
    return data;
  },
  update: async (id: string, account: Partial<{ name: string; description?: string; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/accounting/accounts/${id}`, account);
    return data;
  },
};

// Financial Periods API
export const periodsApi = {
  list: async (params?: { page?: number; size?: number; year_id?: string }) => {
    const { data } = await apiClient.get('/accounting/periods', { params });
    return data;
  },
  listPeriods: async (yearId?: string) => {
    const { data } = await apiClient.get('/accounting/periods', { params: { year_id: yearId } });
    return data;
  },
  listYears: async () => {
    const { data } = await apiClient.get('/accounting/fiscal-years');
    return data;
  },
  getCurrent: async () => {
    const { data } = await apiClient.get('/accounting/periods/current');
    return data;
  },
  create: async (period: { name: string; code: string; financial_year: string; period_type: string; start_date: string; end_date: string }) => {
    const { data } = await apiClient.post('/accounting/periods', period);
    return data;
  },
  createYear: async (year: { name: string; code?: string; start_date: string; end_date: string }) => {
    const { data } = await apiClient.post('/accounting/fiscal-years', year);
    return data;
  },
  close: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/periods/${id}/close`);
    return data;
  },
  closePeriod: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/periods/${id}/close`);
    return data;
  },
  reopenPeriod: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/periods/${id}/reopen`);
    return data;
  },
  lockPeriod: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/periods/${id}/lock`);
    return data;
  },
};

// Cost Centers API
export const costCentersApi = {
  list: async (params?: { page?: number; size?: number; is_active?: boolean }) => {
    const { data } = await apiClient.get('/accounting/cost-centers', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/accounting/cost-centers/${id}`);
    return data;
  },
  create: async (costCenter: {
    code: string;
    name: string;
    cost_center_type: string;
    parent_id?: string;
    description?: string;
    annual_budget?: number;
  }) => {
    const { data } = await apiClient.post('/accounting/cost-centers', costCenter);
    return data;
  },
  update: async (id: string, costCenter: Partial<{
    name: string;
    description?: string;
    annual_budget?: number;
    is_active?: boolean;
  }>) => {
    const { data } = await apiClient.put(`/accounting/cost-centers/${id}`, costCenter);
    return data;
  },
};

// Journal Entries API
export const journalEntriesApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    const { data } = await apiClient.get('/accounting/journals', { params });
    return data;
  },
  getPendingApproval: async () => {
    const { data } = await apiClient.get('/accounting/journals/pending-approval');
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/accounting/journals/${id}`);
    return data;
  },
  create: async (entry: { entry_date: string; narration: string; reference?: string; lines: { account_id: string; debit?: number; credit?: number; debit_amount?: number; credit_amount?: number; description?: string; narration?: string }[] }) => {
    // Map debit_amount/credit_amount to debit/credit if needed
    const mappedEntry = {
      ...entry,
      lines: entry.lines.map(l => ({
        account_id: l.account_id,
        debit: l.debit ?? l.debit_amount ?? 0,
        credit: l.credit ?? l.credit_amount ?? 0,
        narration: l.narration ?? l.description,
      })),
    };
    const { data } = await apiClient.post('/accounting/journals', mappedEntry);
    return data;
  },
  submit: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/journals/${id}/submit`);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/journals/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/accounting/journals/${id}/reject`, { reason });
    return data;
  },
  resubmit: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/journals/${id}/resubmit`);
    return data;
  },
  post: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/journals/${id}/post`);
    return data;
  },
  reverse: async (id: string, reversal_date: string, reason: string) => {
    const { data } = await apiClient.post(`/accounting/journals/${id}/reverse`, { reversal_date, reason });
    return data;
  },
};

// General Ledger API
export const ledgerApi = {
  getAccountLedger: async (accountId: string, params?: { from_date?: string; to_date?: string; page?: number; size?: number }) => {
    const { data } = await apiClient.get(`/accounting/ledger/${accountId}`, { params });
    return data;
  },
};

// Financial Reports API
export const reportsApi = {
  getTrialBalance: async (params?: { as_of_date?: string; period_id?: string }) => {
    const { data } = await apiClient.get('/accounting/reports/trial-balance', { params });
    return data;
  },
  getBalanceSheet: async (params?: { as_of_date?: string; period_id?: string }) => {
    const { data } = await apiClient.get('/accounting/reports/balance-sheet', { params });
    return data;
  },
  getProfitLoss: async (params?: { from_date?: string; to_date?: string; period_id?: string }) => {
    const { data } = await apiClient.get('/accounting/reports/profit-loss', { params });
    return data;
  },
};

// Tax Configuration API
export const taxConfigApi = {
  list: async () => {
    const { data } = await apiClient.get('/accounting/tax-configs');
    return data;
  },
  create: async (config: { name: string; rate: number; type: string; hsn_code?: string }) => {
    const { data } = await apiClient.post('/accounting/tax-configs', config);
    return data;
  },
};

// ============================================
// BILLING API
// ============================================

// Invoices API
export const invoicesApi = {
  list: async (params?: { page?: number; size?: number; status?: string; customer_id?: string }) => {
    const { data } = await apiClient.get('/billing/invoices', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/billing/invoices/${id}`);
    return data;
  },
  create: async (invoice: { customer_id: string; invoice_date: string; due_date: string; items: { product_id: string; quantity: number; unit_price: number; tax_rate: number }[]; notes?: string }) => {
    const { data } = await apiClient.post('/billing/invoices', invoice);
    return data;
  },
  generateIRN: async (id: string) => {
    const { data } = await apiClient.post(`/billing/invoices/${id}/generate-irn`);
    return data;
  },
  cancelIRN: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/billing/invoices/${id}/cancel-irn`, { reason });
    return data;
  },
  download: async (id: string) => {
    const { data } = await apiClient.get(`/billing/invoices/${id}/download`);
    return data;
  },
  print: async (id: string) => {
    const { data } = await apiClient.get(`/billing/invoices/${id}/print`);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/billing/invoices/${id}`);
  },
};

// Credit/Debit Notes API
export const creditDebitNotesApi = {
  list: async (params?: { page?: number; size?: number; type?: string; status?: string }) => {
    const { data } = await apiClient.get('/billing/credit-debit-notes', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/billing/credit-debit-notes/${id}`);
    return data;
  },
  create: async (note: { type: 'CREDIT' | 'DEBIT'; invoice_id?: string; customer_id: string; reason: string; credit_note_date?: string; subtotal?: number; tax_amount?: number; total_amount?: number; lines?: { description: string; quantity: number; unit_price: number; amount?: number; tax_rate?: number; tax_amount?: number }[]; items?: { description: string; quantity: number; unit_price: number; tax_rate?: number }[] }) => {
    const { data } = await apiClient.post('/billing/credit-debit-notes', note);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/billing/credit-debit-notes/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/billing/credit-debit-notes/${id}/reject`, { reason });
    return data;
  },
  apply: async (id: string, invoiceId: string) => {
    const { data } = await apiClient.post(`/billing/credit-debit-notes/${id}/apply`, { invoice_id: invoiceId });
    return data;
  },
  cancel: async (id: string) => {
    const { data } = await apiClient.post(`/billing/credit-debit-notes/${id}/cancel`);
    return data;
  },
  download: async (id: string) => {
    const { data } = await apiClient.get<string>(`/billing/credit-debit-notes/${id}/download`);
    return data;
  },
};

// E-Way Bills API
export const ewayBillsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    const { data } = await apiClient.get('/billing/eway-bills', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/billing/eway-bills/${id}`);
    return data;
  },
  create: async (ewb: { invoice_id: string; transporter_id?: string; vehicle_number?: string; distance_km: number }) => {
    const { data } = await apiClient.post('/billing/eway-bills', ewb);
    return data;
  },
  generate: async (ewbData: string | { invoice_id: string; from_gstin?: string; to_gstin?: string; from_place?: string; to_place?: string; transport_mode?: string; vehicle_type?: string; vehicle_number?: string; transporter_name?: string; distance_km?: number }) => {
    if (typeof ewbData === 'string') {
      const { data } = await apiClient.post(`/billing/eway-bills/${ewbData}/generate`);
      return data;
    } else {
      // Create and generate in one step
      const { data } = await apiClient.post('/billing/eway-bills/generate', ewbData);
      return data;
    }
  },
  updateVehicle: async (id: string, vehicleData: { vehicle_number: string; transporter_id?: string; reason?: string }) => {
    const { data } = await apiClient.put(`/billing/eway-bills/${id}/update-vehicle`, vehicleData);
    return data;
  },
  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/billing/eway-bills/${id}/cancel`, { reason });
    return data;
  },
  print: async (id: string) => {
    const { data } = await apiClient.get(`/billing/eway-bills/${id}/print`);
    return data;
  },
  extendValidity: async (id: string, extendData: { reason: string; from_place?: string; extend_by_km?: number }) => {
    const { data } = await apiClient.post(`/billing/eway-bills/${id}/extend`, extendData);
    return data;
  },
  download: async (id: string) => {
    const { data } = await apiClient.get<string>(`/billing/eway-bills/${id}/print`);
    return data;
  },
};

// Payment Receipts API
export const receiptsApi = {
  list: async (params?: { page?: number; size?: number; customer_id?: string }) => {
    const { data } = await apiClient.get('/billing/receipts', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/billing/receipts/${id}`);
    return data;
  },
  create: async (receipt: { customer_id: string; invoice_id?: string; amount: number; payment_mode: string; reference_number?: string; payment_date: string; notes?: string }) => {
    const { data } = await apiClient.post('/billing/receipts', receipt);
    return data;
  },
};

// GST Reports API
export const gstReportsApi = {
  getGSTR1: async (params: { return_period: string }) => {
    const { data } = await apiClient.get('/billing/reports/gstr1', { params });
    return data;
  },
  getGSTR3B: async (params: { return_period: string }) => {
    const { data } = await apiClient.get('/billing/reports/gstr3b', { params });
    return data;
  },
};

// ============================================
// PROCUREMENT API
// ============================================

// GRN (Goods Receipt Note) API
export const grnApi = {
  list: async (params?: { page?: number; size?: number; status?: string; po_id?: string; warehouse_id?: string }) => {
    const { data } = await apiClient.get('/purchase/grn', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/grn/${id}`);
    return data;
  },
  create: async (grn: {
    purchase_order_id: string;
    warehouse_id: string;
    grn_date: string;
    vendor_challan_number?: string;
    vendor_challan_date?: string;
    transporter_name?: string;
    vehicle_number?: string;
    lr_number?: string;
    e_way_bill_number?: string;
    qc_required?: boolean;
    receiving_remarks?: string;
    items: {
      po_item_id: string;
      product_id: string;
      variant_id?: string;
      product_name: string;
      sku: string;
      quantity_expected: number;
      quantity_received: number;
      quantity_accepted?: number;
      quantity_rejected?: number;
      uom?: string;
      batch_number?: string;
      serial_numbers?: string[];
      remarks?: string;
    }[];
  }) => {
    const { data } = await apiClient.post('/purchase/grn', grn);
    return data;
  },
  scanSerial: async (id: string, scanData: { serial_number: string }) => {
    const { data } = await apiClient.post(`/purchase/grn/${id}/scan`, scanData);
    return data;
  },
  addItem: async (id: string, item: { product_id: string; received_quantity: number; rejected_quantity?: number; rejection_reason?: string }) => {
    const { data } = await apiClient.post(`/purchase/grn/${id}/items`, item);
    return data;
  },
  updateItem: async (id: string, itemId: string, item: { received_quantity?: number; rejected_quantity?: number; rejection_reason?: string; qc_status?: string }) => {
    const { data } = await apiClient.put(`/purchase/grn/${id}/items/${itemId}`, item);
    return data;
  },
  complete: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/grn/${id}/complete`);
    return data;
  },
  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/grn/${id}/cancel`, { reason });
    return data;
  },
  getSerials: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/grn/${id}/serials`);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/purchase/grn/${id}`);
  },
  download: async (id: string) => {
    const { data } = await apiClient.get<string>(`/purchase/grn/${id}/download`);
    return data;
  },
};

// Vendor Proformas API
export const vendorProformasApi = {
  list: async (params?: { page?: number; size?: number; status?: string; vendor_id?: string }) => {
    const { data } = await apiClient.get('/purchase/vendor-proformas', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/vendor-proformas/${id}`);
    return data;
  },
  create: async (proforma: { vendor_id: string; proforma_number: string; proforma_date: string; due_date: string; items: { product_id: string; quantity: number; unit_price: number; gst_rate: number }[]; notes?: string }) => {
    const { data } = await apiClient.post('/purchase/vendor-proformas', proforma);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-proformas/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-proformas/${id}/reject`, { reason });
    return data;
  },
  convertToPO: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-proformas/${id}/convert-to-po`);
    return data;
  },
};

// Vendor Invoices API
export const vendorInvoicesApi = {
  list: async (params?: { page?: number; size?: number; status?: string; vendor_id?: string }) => {
    const { data } = await apiClient.get('/purchase/vendor-invoices', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/vendor-invoices/${id}`);
    return data;
  },
  create: async (invoice: { vendor_id: string; po_id: string; grn_id: string; invoice_number: string; invoice_date: string; due_date: string; items: { grn_item_id: string; quantity: number; unit_price: number; gst_rate: number }[]; notes?: string }) => {
    const { data } = await apiClient.post('/purchase/vendor-invoices', invoice);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-invoices/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-invoices/${id}/reject`, { reason });
    return data;
  },
  markPaid: async (id: string, paymentData: { payment_date: string; payment_reference: string; payment_mode: string }) => {
    const { data } = await apiClient.post(`/purchase/vendor-invoices/${id}/mark-paid`, paymentData);
    return data;
  },
};

// Three-Way Match API
export const threeWayMatchApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    const { data } = await apiClient.get('/purchase/three-way-match', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/three-way-match/${id}`);
    return data;
  },
  match: async (matchData: { po_id: string; grn_id: string; vendor_invoice_id: string }) => {
    const { data } = await apiClient.post('/purchase/three-way-match', matchData);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/three-way-match/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/three-way-match/${id}/reject`, { reason });
    return data;
  },
};

// ============================================
// LOGISTICS API
// ============================================

// Rate Cards API
export const rateCardsApi = {
  list: async (params?: { page?: number; size?: number; transporter_id?: string; is_active?: boolean }) => {
    const { data } = await apiClient.get('/logistics/rate-cards', { params });
    return data;
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/logistics/rate-cards/${id}`);
    return data;
  },
  create: async (rateCard: { transporter_id: string; name: string; source_zone?: string; destination_zone?: string; weight_slab: string; rate_per_kg: number; min_charge: number; fuel_surcharge_percent?: number; cod_charges?: number; rto_charges?: number; effective_from: string; effective_to?: string; is_active?: boolean }) => {
    const { data } = await apiClient.post('/logistics/rate-cards', rateCard);
    return data;
  },
  update: async (id: string, rateCard: Partial<{ name: string; source_zone?: string; destination_zone?: string; weight_slab: string; rate_per_kg: number; min_charge: number; fuel_surcharge_percent?: number; cod_charges?: number; rto_charges?: number; effective_from: string; effective_to?: string; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/logistics/rate-cards/${id}`, rateCard);
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/logistics/rate-cards/${id}`);
  },
  calculate: async (params: { transporter_id: string; source_pincode: string; destination_pincode: string; weight_kg: number; is_cod?: boolean }) => {
    const { data } = await apiClient.post('/logistics/rate-cards/calculate', params);
    return data;
  },
};

// Serviceability API
export const serviceabilityApi = {
  list: async (params?: { page?: number; size?: number; transporter_id?: string; is_active?: boolean }) => {
    const { data } = await apiClient.get('/serviceability', { params });
    return data;
  },
  check: async (pincode: string) => {
    const { data } = await apiClient.get(`/serviceability/check/${pincode}`);
    return data;
  },
  bulkCheck: async (pincodes: string[]) => {
    const { data } = await apiClient.post('/serviceability/bulk-check', { pincodes });
    return data;
  },
  create: async (serviceability: { pincode: string; city: string; state: string; region?: string; transporter_ids?: string[]; prepaid_available?: boolean; cod_available?: boolean; is_active?: boolean }) => {
    const { data } = await apiClient.post('/serviceability', serviceability);
    return data;
  },
  update: async (id: string, serviceability: Partial<{ city: string; state: string; region?: string; transporter_ids?: string[]; prepaid_available?: boolean; cod_available?: boolean; is_active?: boolean }>) => {
    const { data } = await apiClient.put(`/serviceability/${id}`, serviceability);
    return data;
  },
  bulkImport: async (file: FormData) => {
    const { data } = await apiClient.post('/serviceability/bulk-import', file, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  getDashboard: async () => {
    const { data } = await apiClient.get('/serviceability/dashboard');
    return data;
  },
};

// ============================================
// SERIALIZATION API (Barcode Generation)
// ============================================

// Serial Number Types
export interface SerialPreview {
  supplier_code: string;
  model_code: string;
  year_code: string;
  month_code: string;
  current_last_serial: number;
  preview_barcodes: string[];
}

export interface GeneratedSerialSummary {
  model_code: string;
  quantity: number;
  start_serial: number;
  end_serial: number;
  start_barcode: string;
  end_barcode: string;
}

export interface POSerialsResponse {
  po_id: string;
  total: number;
  by_status: Record<string, number>;
  serials: Array<{
    id: string;
    barcode: string;
    model_code: string;
    serial_number: number;
    status: string;
    product_sku?: string;
  }>;
}

export interface ModelCodeReference {
  id: string;
  fg_code: string;
  model_code: string;
  item_type: string;
  product_id?: string;
  product_sku?: string;
  description?: string;
  is_active: boolean;
}

export interface SupplierCode {
  id: string;
  code: string;
  name: string;
  vendor_id?: string;
  is_active: boolean;
}

// Serialization API
export const serializationApi = {
  // Preview codes without saving
  preview: async (params: { supplier_code: string; model_code: string; quantity?: number }): Promise<SerialPreview> => {
    const { data } = await apiClient.post<SerialPreview>('/serialization/preview', params);
    return data;
  },

  // Generate serial numbers for a PO (when PO is sent to vendor)
  generate: async (params: {
    po_id: string;
    supplier_code: string;
    items: Array<{
      po_item_id?: string;
      product_id?: string;
      product_sku?: string;
      model_code: string;
      quantity: number;
      item_type?: string;
    }>;
  }) => {
    const { data } = await apiClient.post('/serialization/generate', params);
    return data;
  },

  // Get serials for a PO
  getByPO: async (poId: string, params?: { status?: string; limit?: number; offset?: number }): Promise<POSerialsResponse> => {
    const { data } = await apiClient.get<POSerialsResponse>(`/serialization/po/${poId}`, { params });
    return data;
  },

  // Export serials for a PO as CSV
  exportPOSerials: async (poId: string, format: 'csv' | 'txt' = 'csv') => {
    const { data } = await apiClient.get(`/serialization/po/${poId}/export`, { params: { format } });
    return data;
  },

  // Mark serials as sent to vendor
  markSentToVendor: async (poId: string) => {
    const { data } = await apiClient.post(`/serialization/po/${poId}/send-to-vendor`);
    return data;
  },

  // Get sequence status (to know next available serial)
  getSequenceStatus: async (modelCode: string, supplierCode: string) => {
    const { data } = await apiClient.get(`/serialization/sequence/${modelCode}`, { params: { supplier_code: supplierCode } });
    return data;
  },

  // Lookup a serial by barcode
  lookup: async (barcode: string) => {
    const { data } = await apiClient.get(`/serialization/lookup/${barcode}`);
    return data;
  },

  // Validate a barcode
  validate: async (barcode: string) => {
    const { data } = await apiClient.post(`/serialization/validate/${barcode}`);
    return data;
  },

  // Get dashboard stats
  getDashboard: async () => {
    const { data } = await apiClient.get('/serialization/dashboard');
    return data;
  },

  // Supplier codes management
  getSupplierCodes: async (activeOnly: boolean = true): Promise<SupplierCode[]> => {
    const { data } = await apiClient.get<SupplierCode[]>('/serialization/suppliers', { params: { active_only: activeOnly } });
    return data;
  },
  createSupplierCode: async (supplierCode: { code: string; name: string; vendor_id?: string; description?: string }) => {
    const { data } = await apiClient.post('/serialization/suppliers', supplierCode);
    return data;
  },

  // Model codes management
  getModelCodes: async (activeOnly: boolean = true, itemType?: string): Promise<ModelCodeReference[]> => {
    const { data } = await apiClient.get<ModelCodeReference[]>('/serialization/model-codes', { params: { active_only: activeOnly, item_type: itemType } });
    return data;
  },
  createModelCode: async (modelCode: { fg_code: string; model_code: string; item_type?: string; product_id?: string; product_sku?: string; description?: string }) => {
    const { data } = await apiClient.post('/serialization/model-codes', modelCode);
    return data;
  },

  // Generate FG code
  generateFGCode: async (params: { category_code: string; subcategory_code: string; brand_code: string; model_name: string }) => {
    const { data } = await apiClient.post('/serialization/fg-code/generate', params);
    return data;
  },
};

// Company API
export interface Company {
  id: string;
  legal_name: string;
  trade_name?: string;
  code: string;
  company_type: string;
  gstin: string;
  gst_registration_type: string;
  state_code: string;
  pan: string;
  tan?: string;
  cin?: string;
  llpin?: string;
  msme_registered: boolean;
  udyam_number?: string;
  msme_category?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  district?: string;
  state: string;
  pincode: string;
  country: string;
  email: string;
  phone: string;
  mobile?: string;
  fax?: string;
  website?: string;
  bank_name?: string;
  bank_branch?: string;
  bank_account_number?: string;
  bank_ifsc?: string;
  bank_account_type?: string;
  bank_account_name?: string;
  logo_url?: string;
  logo_small_url?: string;
  favicon_url?: string;
  signature_url?: string;
  invoice_prefix?: string;
  invoice_suffix?: string;
  invoice_terms?: string;
  invoice_notes?: string;
  invoice_footer?: string;
  po_prefix?: string;
  po_terms?: string;
  currency_code: string;
  currency_symbol: string;
  is_active: boolean;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export const companyApi = {
  // Get primary company (most commonly used for documents)
  getPrimary: async (): Promise<Company> => {
    const { data } = await apiClient.get<Company>('/companies/primary');
    return data;
  },

  // List all companies
  list: async (params?: { is_active?: boolean }) => {
    const { data } = await apiClient.get<{ items: Company[]; total: number }>('/companies', { params });
    return data;
  },

  // Get company by ID
  getById: async (id: string): Promise<Company> => {
    const { data } = await apiClient.get<Company>(`/companies/${id}`);
    return data;
  },

  // Update company
  update: async (id: string, company: Partial<Company>) => {
    const { data } = await apiClient.put<Company>(`/companies/${id}`, company);
    return data;
  },
};

export default apiClient;
