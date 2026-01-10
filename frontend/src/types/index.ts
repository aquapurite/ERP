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
export interface ProductImage {
  id: string;
  product_id: string;
  image_url: string;
  thumbnail_url?: string;
  alt_text?: string;
  is_primary: boolean;
  sort_order: number;
  created_at?: string;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  attributes?: Record<string, string>;
  mrp?: number;
  selling_price?: number;
  cost_price?: number;
  stock_quantity?: number;
  image_url?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProductSpecification {
  id: string;
  product_id?: string;
  group_name?: string;
  key: string;
  value: string;
  name?: string; // Alias for key
  group?: string; // Alias for group_name
  sort_order?: number;
}

export interface ProductDocument {
  id: string;
  product_id?: string;
  title: string;
  name?: string; // Alias for title
  document_type: 'MANUAL' | 'WARRANTY_CARD' | 'BROCHURE' | 'CERTIFICATE' | 'OTHER';
  file_url: string;
  file_size_bytes?: number;
  file_size?: number; // Alias
  mime_type?: string;
  sort_order?: number;
  created_at?: string;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  slug?: string;
  description?: string;
  short_description?: string;
  model_number?: string;
  fg_code?: string;
  category_id?: string;
  brand_id?: string;
  mrp: number;
  selling_price: number;
  cost_price?: number;
  gst_rate?: number;
  hsn_code?: string;
  // Dimensions
  weight?: number;
  length?: number;
  width?: number;
  height?: number;
  volumetric_weight?: number;
  // Status flags
  is_active: boolean;
  is_featured?: boolean;
  is_new_arrival?: boolean;
  is_bestseller?: boolean;
  requires_installation?: boolean;
  // Warranty
  warranty_months?: number;
  warranty_type?: string;
  // SEO
  meta_title?: string;
  meta_description?: string;
  meta_keywords?: string;
  // Stock
  min_stock_level?: number;
  max_stock_level?: number;
  reorder_point?: number;
  // Tags
  tags?: string[];
  // Timestamps
  created_at: string;
  updated_at: string;
  // Relations
  category?: Category;
  brand?: Brand;
  images?: ProductImage[];
  variants?: ProductVariant[];
  specifications?: ProductSpecification[];
  documents?: ProductDocument[];
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
  status: 'AVAILABLE' | 'RESERVED' | 'ALLOCATED' | 'IN_TRANSIT' | 'SHIPPED' | 'SOLD' | 'RETURNED' | 'DAMAGED' | 'DEFECTIVE' | 'QUARANTINE' | 'SCRAPPED' | 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK';
  quantity: number;
  reserved_quantity?: number;
  available_quantity?: number;
  reorder_level?: number;
  last_updated?: string;
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
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING' | 'BLOCKED' | 'PENDING_APPROVAL' | 'SUSPENDED' | 'BLACKLISTED';
  tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE' | 'A+' | 'A' | 'B' | 'C' | 'D';
  created_at: string;
  contact_person?: string;
  city?: string;
  state?: string;
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
  delivery_warehouse_id?: string;
  status: POStatus;
  po_date?: string;
  credit_days?: number;
  subtotal?: number;
  total_amount: number;
  gst_amount: number;
  grand_total: number;
  expected_delivery_date?: string;
  notes?: string;
  created_at: string;
  vendor?: Vendor;
  warehouse?: Warehouse;
  items?: POItem[];
}

export interface POItem {
  id?: string;
  po_id?: string;
  product_id: string;
  product_name?: string;
  sku?: string;
  quantity?: number;
  quantity_ordered?: number;
  quantity_received?: number;
  unit_price: number;
  gst_rate: number;
  total?: number;
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
  pan?: string;
  contact_person?: string;
  pricing_tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  credit_limit: number;
  available_credit: number;
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING' | 'SUSPENDED';
  // Address fields
  registered_address_line1?: string;
  registered_city?: string;
  registered_district?: string;
  registered_state?: string;
  registered_state_code?: string;
  registered_pincode?: string;
  region?: 'NORTH' | 'SOUTH' | 'EAST' | 'WEST' | 'CENTRAL';
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
