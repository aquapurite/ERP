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
  create: async (transporter: { name: string; code: string; type?: string; contact_name?: string; contact_phone?: string; contact_email?: string; website?: string; tracking_url_pattern?: string; is_active?: boolean }) => {
    const { data } = await apiClient.post('/transporters', transporter);
    return data;
  },
  update: async (id: string, transporter: Partial<{ name: string; code: string; type?: string; contact_name?: string; contact_phone?: string; contact_email?: string; is_active?: boolean }>) => {
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
  getCurrent: async () => {
    const { data } = await apiClient.get('/accounting/periods/current');
    return data;
  },
  create: async (period: { name: string; code: string; financial_year: string; period_type: string; start_date: string; end_date: string }) => {
    const { data } = await apiClient.post('/accounting/periods', period);
    return data;
  },
  close: async (id: string) => {
    const { data } = await apiClient.post(`/accounting/periods/${id}/close`);
    return data;
  },
};

// Cost Centers API
export const costCentersApi = {
  list: async (params?: { page?: number; size?: number }) => {
    const { data } = await apiClient.get('/accounting/cost-centers', { params });
    return data;
  },
  create: async (costCenter: { code: string; name: string; parent_id?: string; description?: string }) => {
    const { data } = await apiClient.post('/accounting/cost-centers', costCenter);
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
  create: async (entry: { entry_date: string; narration: string; reference?: string; lines: { account_id: string; debit: number; credit: number; narration?: string }[] }) => {
    const { data } = await apiClient.post('/accounting/journals', entry);
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
};

// Credit/Debit Notes API
export const creditDebitNotesApi = {
  list: async (params?: { page?: number; size?: number; type?: string; status?: string }) => {
    const { data } = await apiClient.get('/billing/credit-debit-notes', { params });
    return data;
  },
  create: async (note: { type: 'CREDIT' | 'DEBIT'; invoice_id?: string; customer_id: string; reason: string; items: { description: string; quantity: number; unit_price: number; tax_rate: number }[] }) => {
    const { data } = await apiClient.post('/billing/credit-debit-notes', note);
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
  generate: async (id: string) => {
    const { data } = await apiClient.post(`/billing/eway-bills/${id}/generate`);
    return data;
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

export default apiClient;
