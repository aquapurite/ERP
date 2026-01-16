import {
  LayoutDashboard,
  Users,
  Shield,
  Package,
  ShoppingCart,
  Warehouse,
  Truck,
  DollarSign,
  FileText,
  Wrench,
  Store,
  MapPin,
  UserCircle,
  Megaphone,
  Barcode,
  CheckSquare,
  History,
  Settings,
  Building2,
  FolderTree,
  Tag,
  LucideIcon,
  Layers,
  Grid3X3,
  ArrowRightLeft,
  ClipboardList,
  BarChart3,
  TrendingUp,
  Scale,
  Calculator,
  Receipt,
  FileCheck,
  Clock,
  AlertTriangle,
  Gauge,
  Network,
  Briefcase,
  Calendar,
  CreditCard,
  Bell,
  Brain,
  Lightbulb,
  Target,
  LineChart,
  Boxes,
  GitBranch,
  Cog,
} from 'lucide-react';

export interface NavItem {
  title: string;
  href?: string;
  icon?: LucideIcon;
  permissions?: string[];
  children?: NavItem[];
  badge?: string;
}

/**
 * CONSOLIDATED NAVIGATION - Industry Standard (SAP/Oracle/NetSuite Pattern)
 *
 * Structure: 8 Main Modules instead of 23+ scattered sections
 * 1. Dashboard & Intelligence - Overview, KPIs, AI Insights
 * 2. Sales & Distribution - Orders, Channels, CRM, Marketing, Dealers
 * 3. Supply Chain - Inventory, Warehouses, WMS, Procurement, Logistics, S&OP
 * 4. Finance & Accounting - GL, AP/AR, Reports, Billing, Compliance
 * 5. Service Management - Service, Installations, AMC, Technicians
 * 6. Human Resources - Employees, Payroll, Attendance
 * 7. Product Management - Catalog, Serialization
 * 8. Administration - Users, Roles, Settings, Audit
 */

export const navigation: NavItem[] = [
  // ==================== 1. DASHBOARD & INTELLIGENCE ====================
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    permissions: [],
  },
  {
    title: 'Intelligence',
    icon: Brain,
    permissions: [],
    badge: 'AI',
    children: [
      { title: 'AI Hub', href: '/dashboard/ai', icon: Lightbulb, permissions: [], badge: 'NEW' },
      { title: 'Insights Overview', href: '/dashboard/insights', icon: TrendingUp, permissions: [] },
      { title: 'Reorder Suggestions', href: '/dashboard/insights/reorder', permissions: [] },
      { title: 'Churn Risk Analysis', href: '/dashboard/insights/churn-risk', permissions: [] },
      { title: 'Slow Moving Stock', href: '/dashboard/insights/slow-moving', permissions: [] },
    ],
  },

  // ==================== 2. SALES & DISTRIBUTION ====================
  {
    title: 'Sales & Distribution',
    icon: ShoppingCart,
    permissions: ['ORDERS_VIEW', 'CHANNELS_VIEW', 'CUSTOMERS_VIEW', 'DEALERS_VIEW'],
    children: [
      // Orders
      { title: 'All Orders', href: '/dashboard/orders', icon: ShoppingCart, permissions: ['ORDERS_VIEW'] },
      { title: 'Picklists', href: '/dashboard/orders/picklists', icon: ClipboardList, permissions: ['ORDERS_VIEW'] },
      { title: 'Order Allocation', href: '/dashboard/orders/allocation', permissions: ['ORDERS_VIEW'] },
      // Channels
      { title: 'Sales Channels', href: '/dashboard/channels', icon: Network, permissions: ['CHANNELS_VIEW'] },
      { title: 'Marketplaces', href: '/dashboard/channels/marketplaces', icon: Store, permissions: ['CHANNELS_VIEW'], badge: 'NEW' },
      { title: 'Channel Pricing', href: '/dashboard/channels/pricing', permissions: ['CHANNELS_VIEW'] },
      // CRM
      { title: 'Customers', href: '/dashboard/crm/customers', icon: UserCircle, permissions: ['CUSTOMERS_VIEW'] },
      { title: 'Customer 360', href: '/dashboard/crm/customer-360', permissions: ['CUSTOMERS_VIEW'] },
      { title: 'Leads', href: '/dashboard/crm/leads', permissions: ['LEADS_VIEW'] },
      { title: 'Call Center', href: '/dashboard/crm/call-center', permissions: ['CUSTOMERS_VIEW'] },
      // Distribution
      { title: 'Dealers', href: '/dashboard/distribution/dealers', icon: Store, permissions: ['DEALERS_VIEW'] },
      { title: 'Franchisees', href: '/dashboard/distribution/franchisees', permissions: ['DEALERS_VIEW'] },
      { title: 'Pricing Tiers', href: '/dashboard/distribution/pricing-tiers', permissions: ['DEALERS_VIEW'] },
      // Marketing
      { title: 'Campaigns', href: '/dashboard/marketing/campaigns', icon: Megaphone, permissions: ['CAMPAIGNS_VIEW'] },
      { title: 'Promotions', href: '/dashboard/marketing/promotions', permissions: ['CAMPAIGNS_VIEW'] },
    ],
  },

  // ==================== 3. SUPPLY CHAIN ====================
  {
    title: 'Supply Chain',
    icon: Boxes,
    permissions: ['INVENTORY_VIEW', 'PURCHASE_VIEW', 'SHIPMENTS_VIEW', 'SNOP_VIEW'],
    children: [
      // S&OP / Planning (NEW - was missing!)
      { title: 'S&OP Dashboard', href: '/dashboard/snop', icon: Target, permissions: ['SNOP_VIEW'], badge: 'NEW' },
      { title: 'Demand Forecasting', href: '/dashboard/snop/forecasts', icon: LineChart, permissions: ['SNOP_VIEW'], badge: 'NEW' },
      { title: 'Supply Planning', href: '/dashboard/snop/supply-plans', icon: GitBranch, permissions: ['SNOP_VIEW'] },
      { title: 'Scenario Analysis', href: '/dashboard/snop/scenarios', permissions: ['SNOP_VIEW'] },
      { title: 'Inventory Optimization', href: '/dashboard/snop/inventory-optimization', permissions: ['SNOP_VIEW'] },
      // Inventory
      { title: 'Stock Summary', href: '/dashboard/inventory', icon: Warehouse, permissions: ['INVENTORY_VIEW'] },
      { title: 'Stock Items', href: '/dashboard/inventory/stock-items', permissions: ['INVENTORY_VIEW'] },
      { title: 'Warehouses', href: '/dashboard/inventory/warehouses', permissions: ['WAREHOUSES_VIEW'] },
      { title: 'Stock Transfers', href: '/dashboard/inventory/transfers', permissions: ['TRANSFERS_VIEW'] },
      { title: 'Adjustments', href: '/dashboard/inventory/adjustments', permissions: ['INVENTORY_VIEW'] },
      // WMS
      { title: 'WMS Zones', href: '/dashboard/wms/zones', icon: Grid3X3, permissions: ['WMS_VIEW'] },
      { title: 'WMS Bins', href: '/dashboard/wms/bins', permissions: ['WMS_VIEW'] },
      { title: 'Putaway Rules', href: '/dashboard/wms/putaway-rules', permissions: ['WMS_VIEW'] },
      // Procurement
      { title: 'Vendors', href: '/dashboard/procurement/vendors', icon: Building2, permissions: ['VENDORS_VIEW'] },
      { title: 'Purchase Requisitions', href: '/dashboard/procurement/requisitions', permissions: ['PURCHASE_VIEW'] },
      { title: 'Purchase Orders', href: '/dashboard/procurement/purchase-orders', permissions: ['PURCHASE_VIEW'] },
      { title: 'GRN', href: '/dashboard/procurement/grn', permissions: ['GRN_VIEW'] },
      { title: 'Vendor Invoices', href: '/dashboard/procurement/vendor-invoices', permissions: ['PURCHASE_VIEW'] },
      { title: '3-Way Match', href: '/dashboard/procurement/three-way-match', permissions: ['PURCHASE_VIEW'] },
      // Logistics
      { title: 'Shipments', href: '/dashboard/logistics/shipments', icon: Truck, permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Manifests', href: '/dashboard/logistics/manifests', permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Transporters', href: '/dashboard/logistics/transporters', permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Rate Cards', href: '/dashboard/logistics/rate-cards', permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Serviceability', href: '/dashboard/logistics/serviceability', permissions: ['SHIPMENTS_VIEW'] },
    ],
  },

  // ==================== 4. FINANCE & ACCOUNTING ====================
  {
    title: 'Finance',
    icon: DollarSign,
    permissions: ['ACCOUNTING_VIEW', 'BILLING_VIEW', 'REPORTS_VIEW'],
    children: [
      // Core Accounting
      { title: 'Chart of Accounts', href: '/dashboard/finance/chart-of-accounts', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Journal Entries', href: '/dashboard/finance/journal-entries', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Auto Journal', href: '/dashboard/finance/auto-journal', permissions: ['ACCOUNTING_VIEW'], badge: 'NEW' },
      { title: 'General Ledger', href: '/dashboard/finance/general-ledger', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Cost Centers', href: '/dashboard/finance/cost-centers', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Financial Periods', href: '/dashboard/finance/periods', permissions: ['ACCOUNTING_VIEW'] },
      // Banking
      { title: 'Bank Reconciliation', href: '/dashboard/finance/bank-reconciliation', permissions: ['ACCOUNTING_VIEW'] },
      // Billing & AR
      { title: 'Invoices', href: '/dashboard/billing/invoices', icon: FileText, permissions: ['BILLING_VIEW'] },
      { title: 'E-Way Bills', href: '/dashboard/billing/eway-bills', permissions: ['BILLING_VIEW'] },
      { title: 'Credit Notes', href: '/dashboard/billing/credit-notes', permissions: ['BILLING_VIEW'] },
      { title: 'Receipts', href: '/dashboard/billing/receipts', permissions: ['BILLING_VIEW'] },
      // Tax & Compliance
      { title: 'TDS Management', href: '/dashboard/finance/tds', permissions: ['ACCOUNTING_VIEW'], badge: 'NEW' },
      { title: 'GSTR-1', href: '/dashboard/finance/gstr1', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'GSTR-2A', href: '/dashboard/finance/gstr2a', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'GSTR-3B', href: '/dashboard/finance/gstr3b', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'HSN Summary', href: '/dashboard/finance/hsn-summary', permissions: ['ACCOUNTING_VIEW'] },
      // Assets
      { title: 'Fixed Assets', href: '/dashboard/finance/fixed-assets', permissions: ['ACCOUNTING_VIEW'] },
      // Reports
      { title: 'Trial Balance', href: '/dashboard/reports/trial-balance', icon: BarChart3, permissions: ['REPORTS_VIEW'] },
      { title: 'Profit & Loss', href: '/dashboard/reports/profit-loss', permissions: ['REPORTS_VIEW'] },
      { title: 'Balance Sheet', href: '/dashboard/reports/balance-sheet', permissions: ['REPORTS_VIEW'] },
      { title: 'Channel P&L', href: '/dashboard/reports/channel-pl', permissions: ['REPORTS_VIEW'] },
    ],
  },

  // ==================== 5. SERVICE MANAGEMENT ====================
  {
    title: 'Service',
    icon: Wrench,
    permissions: ['SERVICE_VIEW', 'TECHNICIANS_VIEW'],
    children: [
      { title: 'Service Requests', href: '/dashboard/service/requests', permissions: ['SERVICE_VIEW'] },
      { title: 'Installations', href: '/dashboard/service/installations', permissions: ['SERVICE_VIEW'] },
      { title: 'Warranty Claims', href: '/dashboard/service/warranty-claims', icon: AlertTriangle, permissions: ['SERVICE_VIEW'] },
      { title: 'AMC Contracts', href: '/dashboard/service/amc', permissions: ['SERVICE_VIEW'] },
      { title: 'Technicians', href: '/dashboard/service/technicians', icon: Users, permissions: ['TECHNICIANS_VIEW'] },
      { title: 'Escalations', href: '/dashboard/crm/escalations', permissions: ['SERVICE_VIEW'] },
    ],
  },

  // ==================== 6. HUMAN RESOURCES ====================
  {
    title: 'Human Resources',
    icon: Briefcase,
    permissions: ['HR_VIEW'],
    children: [
      { title: 'HR Dashboard', href: '/dashboard/hr', permissions: ['HR_VIEW'] },
      { title: 'Employees', href: '/dashboard/hr/employees', icon: Users, permissions: ['HR_VIEW'] },
      { title: 'Departments', href: '/dashboard/hr/departments', permissions: ['HR_VIEW'] },
      { title: 'Attendance', href: '/dashboard/hr/attendance', icon: Calendar, permissions: ['ATTENDANCE_VIEW'] },
      { title: 'Leave Management', href: '/dashboard/hr/leaves', permissions: ['LEAVE_VIEW'] },
      { title: 'Payroll', href: '/dashboard/hr/payroll', icon: CreditCard, permissions: ['PAYROLL_VIEW'] },
      { title: 'Performance', href: '/dashboard/hr/performance', permissions: ['HR_VIEW'] },
      { title: 'HR Reports', href: '/dashboard/hr/reports', permissions: ['HR_VIEW'] },
    ],
  },

  // ==================== 7. PRODUCT MANAGEMENT ====================
  {
    title: 'Products',
    icon: Package,
    permissions: ['PRODUCTS_VIEW', 'CATEGORIES_VIEW', 'BRANDS_VIEW'],
    children: [
      { title: 'All Products', href: '/dashboard/catalog', permissions: ['PRODUCTS_VIEW'] },
      { title: 'Categories', href: '/dashboard/catalog/categories', icon: FolderTree, permissions: ['CATEGORIES_VIEW'] },
      { title: 'Brands', href: '/dashboard/catalog/brands', icon: Tag, permissions: ['BRANDS_VIEW'] },
      { title: 'Serialization', href: '/dashboard/serialization', icon: Barcode, permissions: ['PRODUCTS_VIEW'] },
    ],
  },

  // ==================== 8. ADMINISTRATION ====================
  {
    title: 'Administration',
    icon: Cog,
    permissions: ['USERS_VIEW', 'ROLES_VIEW', 'AUDIT_VIEW'],
    children: [
      { title: 'Users', href: '/dashboard/access-control/users', icon: Users, permissions: ['USERS_VIEW'] },
      { title: 'Roles', href: '/dashboard/access-control/roles', icon: Shield, permissions: ['ROLES_VIEW'] },
      { title: 'Permissions', href: '/dashboard/access-control/permissions', permissions: ['ROLES_VIEW'] },
      { title: 'Approvals', href: '/dashboard/approvals', icon: CheckSquare, permissions: ['APPROVALS_VIEW'], badge: 'pending' },
      { title: 'Audit Logs', href: '/dashboard/audit-logs', icon: History, permissions: ['AUDIT_VIEW'] },
      { title: 'Settings', href: '/dashboard/settings', icon: Settings, permissions: [] },
    ],
  },

  // Quick Access Items (always visible)
  {
    title: 'Notifications',
    href: '/dashboard/notifications',
    icon: Bell,
    permissions: [],
  },
];
