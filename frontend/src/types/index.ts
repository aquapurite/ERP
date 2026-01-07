// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  phone?: string;
  first_name: string;
  last_name?: string;
  full_name?: string;
  name?: string; // Computed name from backend (first_name + last_name)
  department?: string;
  designation?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  roles?: Role[];
}

// Helper function to get user display name
export function getUserDisplayName(user: User | null | undefined): string {
  if (!user) return 'Unknown';
  return user.name || user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email || 'Unknown';
}

export interface Role {
  id: string;
  name: string;
  code: string;
  level: RoleLevel;
  description?: string;
  permissions: Permission[];
}

export type RoleLevel = 'SUPER_ADMIN' | 'DIRECTOR' | 'HEAD' | 'MANAGER' | 'EXECUTIVE';

export interface Permission {
  id: string;
  code: string;
  name: string;
  module: string;
  action: string;
  description?: string;
}

export interface UserPermissions {
  is_super_admin: boolean;
  roles?: Role[];
  permissions_by_module?: Record<string, string[]>;
  total_permissions?: number;
  permissions: Record<string, boolean>;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Product Types
export interface Product {
  id: string;
  name: string;
  sku: string;
  description?: string;
  category_id?: string;
  brand_id?: string;
  mrp: number;
  selling_price: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category?: Category;
  brand?: Brand;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  parent_id?: string;
  image_url?: string;
  icon?: string;
  sort_order?: number;
  is_active: boolean;
  is_featured?: boolean;
}

export interface Brand {
  id: string;
  name: string;
  code: string;
  description?: string;
  logo_url?: string;
  is_active: boolean;
}

// Order Types
export type OrderStatus =
  | 'NEW'
  | 'PENDING_PAYMENT'
  | 'CONFIRMED'
  | 'ALLOCATED'
  | 'PICKLIST_CREATED'
  | 'PICKING'
  | 'PICKED'
  | 'PACKING'
  | 'PACKED'
  | 'MANIFESTED'
  | 'READY_TO_SHIP'
  | 'SHIPPED'
  | 'IN_TRANSIT'
  | 'OUT_FOR_DELIVERY'
  | 'DELIVERED'
  | 'PARTIALLY_DELIVERED'
  | 'RTO_INITIATED'
  | 'RTO_IN_TRANSIT'
  | 'RTO_DELIVERED'
  | 'RETURNED'
  | 'CANCELLED'
  | 'REFUNDED'
  | 'ON_HOLD';

export interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  status: OrderStatus;
  total_amount: number;
  discount_amount: number;
  tax_amount: number;
  grand_total: number;
  payment_status: 'PENDING' | 'PAID' | 'PARTIALLY_PAID' | 'REFUNDED';
  channel: string;
  created_at: string;
  updated_at: string;
  customer?: Customer;
  items?: OrderItem[];
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  discount: number;
  tax: number;
  total: number;
}

// Customer Types
export interface Customer {
  id: string;
  name: string;
  email?: string;
  phone: string;
  customer_type: 'INDIVIDUAL' | 'BUSINESS' | 'DEALER';
  is_active: boolean;
  created_at: string;
  addresses?: Address[];
}

export interface Address {
  id: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  is_default: boolean;
}

// Inventory Types
export interface Warehouse {
  id: string;
  name: string;
  code: string;
  type: 'MAIN' | 'REGIONAL' | 'SERVICE_CENTER' | 'DEALER' | 'VIRTUAL';
  address: string;
  city: string;
  state: string;
  pincode: string;
  is_active: boolean;
  capacity?: number;
}

export interface StockItem {
  id: string;
  product_id: string;
  warehouse_id: string;
  serial_number?: string;
  batch_number?: string;
  status: 'AVAILABLE' | 'RESERVED' | 'ALLOCATED' | 'IN_TRANSIT' | 'SHIPPED' | 'SOLD' | 'RETURNED' | 'DAMAGED' | 'DEFECTIVE' | 'QUARANTINE' | 'SCRAPPED';
  quantity: number;
  product?: Product;
  warehouse?: Warehouse;
}

// Vendor Types
export interface Vendor {
  id: string;
  name: string;
  code: string;
  email?: string;
  phone?: string;
  gst_number?: string;
  pan_number?: string;
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING' | 'BLOCKED';
  tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  created_at: string;
}

// Purchase Order Types
export type POStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'SENT_TO_VENDOR'
  | 'ACKNOWLEDGED'
  | 'PARTIALLY_RECEIVED'
  | 'FULLY_RECEIVED'
  | 'CLOSED'
  | 'CANCELLED';

export interface PurchaseOrder {
  id: string;
  po_number: string;
  vendor_id: string;
  warehouse_id: string;
  status: POStatus;
  total_amount: number;
  gst_amount: number;
  grand_total: number;
  expected_delivery_date?: string;
  created_at: string;
  vendor?: Vendor;
  warehouse?: Warehouse;
  items?: POItem[];
}

export interface POItem {
  id: string;
  po_id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity_ordered: number;
  quantity_received: number;
  unit_price: number;
  gst_rate: number;
  total: number;
}

// Service Request Types
export type ServiceRequestStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'ASSIGNED'
  | 'SCHEDULED'
  | 'EN_ROUTE'
  | 'IN_PROGRESS'
  | 'PARTS_REQUIRED'
  | 'ON_HOLD'
  | 'COMPLETED'
  | 'CLOSED'
  | 'CANCELLED'
  | 'REOPENED';

export type ServiceRequestType =
  | 'WARRANTY_REPAIR'
  | 'PAID_REPAIR'
  | 'AMC_SERVICE'
  | 'INSTALLATION'
  | 'UNINSTALLATION'
  | 'DEMO'
  | 'COMPLAINT'
  | 'INQUIRY'
  | 'FEEDBACK'
  | 'OTHER';

export interface ServiceRequest {
  id: string;
  request_number: string;
  customer_id: string;
  product_id?: string;
  type: ServiceRequestType;
  status: ServiceRequestStatus;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  description?: string;
  scheduled_date?: string;
  technician_id?: string;
  created_at: string;
  customer?: Customer;
  product?: Product;
}

// Dealer Types
export type DealerType = 'DISTRIBUTOR' | 'DEALER' | 'SUB_DEALER' | 'FRANCHISE' | 'RETAILER' | 'CORPORATE';

export interface Dealer {
  id: string;
  name: string;
  code: string;
  type: DealerType;
  email?: string;
  phone?: string;
  gst_number?: string;
  pricing_tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  credit_limit: number;
  available_credit: number;
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING' | 'SUSPENDED';
  created_at: string;
}

// Common Types
export interface SelectOption {
  label: string;
  value: string;
}

export interface TableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  render?: (value: unknown, row: T) => React.ReactNode;
}
