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
  PackageSearch,
  Handshake,
  Phone,
  UserPlus,
  FileInput,
  FileOutput,
  Clipboard,
  MapPin,
  Route,
  BadgePercent,
  Banknote,
  Building,
  Landmark,
  ScrollText,
  IndianRupee,
  CalendarCheck,
  HeartHandshake,
  ShieldCheck,
  HardHat,
  Headphones,
  UsersRound,
  GraduationCap,
  Award,
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
 * AQUAPURITE ERP - NAVIGATION STRUCTURE
 *
 * Based on Industry Best Practices (SAP, Oracle NetSuite, Zoho, Microsoft Dynamics)
 *
 * Structure:
 * 1. Dashboard - Overview & KPIs
 * 2. Intelligence - AI & analytics (prominent placement for AI-first approach)
 * 3. Sales & CRM - Customer-facing operations
 * 4. Procurement - Vendor-facing operations (P2P)
 * 5. Inventory - Stock management
 * 6. Warehouse (WMS) - Physical warehouse operations
 * 7. Logistics - Shipping & fulfillment
 * 8. Planning (S&OP) - Demand forecasting & supply planning
 * 9. Finance - Accounting, billing, tax compliance
 * 10. Service - After-sales support
 * 11. Human Resources - Employee management
 * 12. Master Data - Products & configuration
 * 13. Administration - System settings
 */

export const navigation: NavItem[] = [
  // ==================== 1. DASHBOARD ====================
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    permissions: [],
  },

  // ==================== 2. INTELLIGENCE (AI) ====================
  {
    title: 'Intelligence',
    icon: Brain,
    permissions: [],
    badge: 'AI',
    children: [
      { title: 'AI Hub', href: '/dashboard/ai', icon: Lightbulb, permissions: [] },
      { title: 'Insights Dashboard', href: '/dashboard/insights', icon: TrendingUp, permissions: [] },
      { title: 'Reorder Suggestions', href: '/dashboard/insights/reorder', icon: PackageSearch, permissions: [] },
      { title: 'Churn Risk Analysis', href: '/dashboard/insights/churn-risk', icon: AlertTriangle, permissions: [] },
      { title: 'Slow Moving Stock', href: '/dashboard/insights/slow-moving', icon: Clock, permissions: [] },
      { title: 'Campaigns', href: '/dashboard/marketing/campaigns', icon: Megaphone, permissions: ['CAMPAIGNS_VIEW'] },
    ],
  },

  // ==================== 3. SALES & CRM ====================
  {
    title: 'Sales & CRM',
    icon: ShoppingCart,
    permissions: ['ORDERS_VIEW', 'CUSTOMERS_VIEW', 'LEADS_VIEW', 'CHANNELS_VIEW', 'DEALERS_VIEW'],
    children: [
      // Orders
      { title: 'All Orders', href: '/dashboard/orders', icon: ShoppingCart, permissions: ['ORDERS_VIEW'] },
      { title: 'New Order', href: '/dashboard/orders/new', icon: FileInput, permissions: ['ORDERS_CREATE'] },
      // Customers
      { title: 'Customers', href: '/dashboard/crm/customers', icon: UserCircle, permissions: ['CUSTOMERS_VIEW'] },
      { title: 'Customer 360', href: '/dashboard/crm/customer-360', icon: Target, permissions: ['CUSTOMERS_VIEW'] },
      // Leads & Pipeline
      { title: 'Leads', href: '/dashboard/crm/leads', icon: UserPlus, permissions: ['LEADS_VIEW'] },
      // Channels
      { title: 'Sales Channels', href: '/dashboard/channels', icon: Network, permissions: ['CHANNELS_VIEW'] },
      { title: 'Marketplaces', href: '/dashboard/channels/marketplaces', icon: Store, permissions: ['CHANNELS_VIEW'] },
      { title: 'Channel Pricing', href: '/dashboard/channels/pricing', permissions: ['CHANNELS_VIEW'] },
      // Distribution Network
      { title: 'Dealers', href: '/dashboard/distribution/dealers', icon: Handshake, permissions: ['DEALERS_VIEW'] },
      { title: 'Franchisees', href: '/dashboard/distribution/franchisees', icon: Building2, permissions: ['DEALERS_VIEW'] },
      { title: 'Pricing Tiers', href: '/dashboard/distribution/pricing-tiers', permissions: ['DEALERS_VIEW'] },
      // Promotions
      { title: 'Promotions', href: '/dashboard/marketing/promotions', icon: BadgePercent, permissions: ['CAMPAIGNS_VIEW'] },
      { title: 'Commissions', href: '/dashboard/marketing/commissions', icon: Banknote, permissions: ['CAMPAIGNS_VIEW'] },
      // Support
      { title: 'Call Center', href: '/dashboard/crm/call-center', icon: Phone, permissions: ['CUSTOMERS_VIEW'] },
    ],
  },

  // ==================== 4. PROCUREMENT (P2P) ====================
  {
    title: 'Procurement',
    icon: FileInput,
    permissions: ['VENDORS_VIEW', 'PURCHASE_VIEW', 'GRN_VIEW'],
    children: [
      { title: 'Vendors', href: '/dashboard/procurement/vendors', icon: Building2, permissions: ['VENDORS_VIEW'] },
      { title: 'Purchase Requisitions', href: '/dashboard/procurement/requisitions', icon: FileText, permissions: ['PURCHASE_VIEW'] },
      { title: 'Purchase Orders', href: '/dashboard/procurement/purchase-orders', icon: Clipboard, permissions: ['PURCHASE_VIEW'] },
      { title: 'Goods Receipt (GRN)', href: '/dashboard/procurement/grn', icon: PackageSearch, permissions: ['GRN_VIEW'] },
      { title: 'Vendor Invoices', href: '/dashboard/procurement/vendor-invoices', icon: Receipt, permissions: ['PURCHASE_VIEW'] },
      { title: 'Vendor Proformas', href: '/dashboard/procurement/vendor-proformas', icon: FileCheck, permissions: ['PURCHASE_VIEW'] },
      { title: 'Sales Returns (SRN)', href: '/dashboard/procurement/sales-returns', icon: FileOutput, permissions: ['PURCHASE_VIEW'] },
      { title: '3-Way Matching', href: '/dashboard/procurement/three-way-match', icon: Scale, permissions: ['PURCHASE_VIEW'] },
    ],
  },

  // ==================== 5. INVENTORY ====================
  {
    title: 'Inventory',
    icon: Boxes,
    permissions: ['INVENTORY_VIEW', 'WAREHOUSES_VIEW', 'TRANSFERS_VIEW'],
    children: [
      { title: 'Stock Summary', href: '/dashboard/inventory', icon: BarChart3, permissions: ['INVENTORY_VIEW'] },
      { title: 'Stock Items', href: '/dashboard/inventory/stock-items', icon: Package, permissions: ['INVENTORY_VIEW'] },
      { title: 'Warehouses', href: '/dashboard/inventory/warehouses', icon: Warehouse, permissions: ['WAREHOUSES_VIEW'] },
      { title: 'Stock Transfers', href: '/dashboard/inventory/transfers', icon: ArrowRightLeft, permissions: ['TRANSFERS_VIEW'] },
      { title: 'Stock Adjustments', href: '/dashboard/inventory/adjustments', icon: Calculator, permissions: ['INVENTORY_VIEW'] },
    ],
  },

  // ==================== 6. WAREHOUSE (WMS) ====================
  {
    title: 'Warehouse (WMS)',
    icon: Grid3X3,
    permissions: ['WMS_VIEW', 'ORDERS_VIEW'],
    children: [
      { title: 'Zones', href: '/dashboard/wms/zones', icon: Layers, permissions: ['WMS_VIEW'] },
      { title: 'Bins & Locations', href: '/dashboard/wms/bins', icon: Grid3X3, permissions: ['WMS_VIEW'] },
      { title: 'Bin Enquiry', href: '/dashboard/wms/bin-enquiry', icon: PackageSearch, permissions: ['WMS_VIEW'] },
      { title: 'Putaway Rules', href: '/dashboard/wms/putaway-rules', icon: Route, permissions: ['WMS_VIEW'] },
      { title: 'Picklists', href: '/dashboard/orders/picklists', icon: ClipboardList, permissions: ['ORDERS_VIEW'] },
    ],
  },

  // ==================== 7. LOGISTICS & SHIPPING ====================
  {
    title: 'Logistics',
    icon: Truck,
    permissions: ['SHIPMENTS_VIEW'],
    children: [
      { title: 'Shipments', href: '/dashboard/logistics/shipments', icon: Truck, permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Manifests', href: '/dashboard/logistics/manifests', icon: FileText, permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Order Allocation', href: '/dashboard/orders/allocation', icon: GitBranch, permissions: ['ORDERS_VIEW'] },
      { title: 'Allocation Rules', href: '/dashboard/logistics/allocation-rules', permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Transporters', href: '/dashboard/logistics/transporters', icon: Building2, permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Rate Cards', href: '/dashboard/logistics/rate-cards', icon: IndianRupee, permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Rate Cards - B2B', href: '/dashboard/logistics/rate-cards/b2b', permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Rate Cards - FTL', href: '/dashboard/logistics/rate-cards/ftl', permissions: ['SHIPMENTS_VIEW'] },
      { title: 'Serviceability', href: '/dashboard/logistics/serviceability', icon: MapPin, permissions: ['SHIPMENTS_VIEW'] },
      { title: 'E-Way Bills', href: '/dashboard/billing/eway-bills', icon: ScrollText, permissions: ['BILLING_VIEW'] },
      { title: 'SLA Dashboard', href: '/dashboard/logistics/sla-dashboard', icon: Gauge, permissions: ['SHIPMENTS_VIEW'] },
    ],
  },

  // ==================== 8. PLANNING (S&OP) ====================
  {
    title: 'Planning (S&OP)',
    icon: Target,
    permissions: ['SNOP_VIEW'],
    badge: 'NEW',
    children: [
      { title: 'S&OP Dashboard', href: '/dashboard/snop', icon: Target, permissions: ['SNOP_VIEW'] },
      { title: 'Demand Forecasting', href: '/dashboard/snop/forecasts', icon: LineChart, permissions: ['SNOP_VIEW'] },
      { title: 'Supply Planning', href: '/dashboard/snop/supply-plans', icon: GitBranch, permissions: ['SNOP_VIEW'] },
      { title: 'Scenario Analysis', href: '/dashboard/snop/scenarios', icon: Layers, permissions: ['SNOP_VIEW'] },
      { title: 'Inventory Optimization', href: '/dashboard/snop/inventory-optimization', icon: TrendingUp, permissions: ['SNOP_VIEW'] },
    ],
  },

  // ==================== 9. FINANCE & ACCOUNTING ====================
  {
    title: 'Finance',
    icon: DollarSign,
    permissions: ['ACCOUNTING_VIEW', 'BILLING_VIEW', 'REPORTS_VIEW'],
    children: [
      // Core Accounting
      { title: 'Chart of Accounts', href: '/dashboard/finance/chart-of-accounts', icon: FolderTree, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Journal Entries', href: '/dashboard/finance/journal-entries', icon: FileText, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Auto Journal', href: '/dashboard/finance/auto-journal', icon: Cog, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'General Ledger', href: '/dashboard/finance/general-ledger', icon: ScrollText, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Cost Centers', href: '/dashboard/finance/cost-centers', icon: Building, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'Financial Periods', href: '/dashboard/finance/periods', icon: Calendar, permissions: ['ACCOUNTING_VIEW'] },
      // Billing & AR
      { title: 'Invoices', href: '/dashboard/billing/invoices', icon: Receipt, permissions: ['BILLING_VIEW'] },
      { title: 'Credit Notes', href: '/dashboard/billing/credit-notes', icon: FileOutput, permissions: ['BILLING_VIEW'] },
      { title: 'Receipts', href: '/dashboard/billing/receipts', icon: Banknote, permissions: ['BILLING_VIEW'] },
      // Banking
      { title: 'Bank Reconciliation', href: '/dashboard/finance/bank-reconciliation', icon: Landmark, permissions: ['ACCOUNTING_VIEW'] },
      // Assets
      { title: 'Fixed Assets', href: '/dashboard/finance/fixed-assets', icon: Building2, permissions: ['ACCOUNTING_VIEW'] },
      // Tax Compliance
      { title: 'TDS Management', href: '/dashboard/finance/tds', icon: IndianRupee, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'GSTR-1', href: '/dashboard/finance/gstr1', icon: FileCheck, permissions: ['ACCOUNTING_VIEW'] },
      { title: 'GSTR-2A', href: '/dashboard/finance/gstr2a', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'GSTR-3B', href: '/dashboard/finance/gstr3b', permissions: ['ACCOUNTING_VIEW'] },
      { title: 'HSN Summary', href: '/dashboard/finance/hsn-summary', permissions: ['ACCOUNTING_VIEW'] },
      // Reports
      { title: 'Trial Balance', href: '/dashboard/reports/trial-balance', icon: BarChart3, permissions: ['REPORTS_VIEW'] },
      { title: 'Profit & Loss', href: '/dashboard/reports/profit-loss', icon: TrendingUp, permissions: ['REPORTS_VIEW'] },
      { title: 'Balance Sheet', href: '/dashboard/reports/balance-sheet', icon: Scale, permissions: ['REPORTS_VIEW'] },
      { title: 'Channel P&L', href: '/dashboard/reports/channel-pl', icon: Network, permissions: ['REPORTS_VIEW'] },
      { title: 'Channel Balance Sheet', href: '/dashboard/reports/channel-balance-sheet', icon: Landmark, permissions: ['REPORTS_VIEW'] },
    ],
  },

  // ==================== 10. SERVICE & SUPPORT ====================
  {
    title: 'Service',
    icon: Wrench,
    permissions: ['SERVICE_VIEW', 'TECHNICIANS_VIEW'],
    children: [
      { title: 'Service Requests', href: '/dashboard/service/requests', icon: Headphones, permissions: ['SERVICE_VIEW'] },
      { title: 'New Request', href: '/dashboard/service/requests/new', icon: FileInput, permissions: ['SERVICE_VIEW'] },
      { title: 'Installations', href: '/dashboard/service/installations', icon: CalendarCheck, permissions: ['SERVICE_VIEW'] },
      { title: 'Warranty Claims', href: '/dashboard/service/warranty-claims', icon: ShieldCheck, permissions: ['SERVICE_VIEW'] },
      { title: 'AMC Contracts', href: '/dashboard/service/amc', icon: HeartHandshake, permissions: ['SERVICE_VIEW'] },
      { title: 'Technicians', href: '/dashboard/service/technicians', icon: HardHat, permissions: ['TECHNICIANS_VIEW'] },
      { title: 'Escalations', href: '/dashboard/crm/escalations', icon: AlertTriangle, permissions: ['SERVICE_VIEW'] },
    ],
  },

  // ==================== 11. HUMAN RESOURCES ====================
  {
    title: 'Human Resources',
    icon: Briefcase,
    permissions: ['HR_VIEW'],
    children: [
      { title: 'HR Dashboard', href: '/dashboard/hr', icon: BarChart3, permissions: ['HR_VIEW'] },
      { title: 'Employees', href: '/dashboard/hr/employees', icon: UsersRound, permissions: ['HR_VIEW'] },
      { title: 'Departments', href: '/dashboard/hr/departments', icon: Building2, permissions: ['HR_VIEW'] },
      { title: 'Attendance', href: '/dashboard/hr/attendance', icon: CalendarCheck, permissions: ['ATTENDANCE_VIEW'] },
      { title: 'Leave Management', href: '/dashboard/hr/leaves', icon: Calendar, permissions: ['LEAVE_VIEW'] },
      { title: 'Payroll', href: '/dashboard/hr/payroll', icon: CreditCard, permissions: ['PAYROLL_VIEW'] },
      { title: 'Performance', href: '/dashboard/hr/performance', icon: Award, permissions: ['HR_VIEW'] },
      { title: 'HR Reports', href: '/dashboard/hr/reports', icon: BarChart3, permissions: ['HR_VIEW'] },
    ],
  },

  // ==================== 12. MASTER DATA ====================
  {
    title: 'Master Data',
    icon: Package,
    permissions: ['PRODUCTS_VIEW', 'CATEGORIES_VIEW', 'BRANDS_VIEW'],
    children: [
      { title: 'Products', href: '/dashboard/catalog', icon: Package, permissions: ['PRODUCTS_VIEW'] },
      { title: 'New Product', href: '/dashboard/catalog/new', icon: FileInput, permissions: ['PRODUCTS_CREATE'] },
      { title: 'Categories', href: '/dashboard/catalog/categories', icon: FolderTree, permissions: ['CATEGORIES_VIEW'] },
      { title: 'Brands', href: '/dashboard/catalog/brands', icon: Tag, permissions: ['BRANDS_VIEW'] },
      { title: 'Serialization', href: '/dashboard/serialization', icon: Barcode, permissions: ['PRODUCTS_VIEW'] },
    ],
  },

  // ==================== 13. ADMINISTRATION ====================
  {
    title: 'Administration',
    icon: Cog,
    permissions: ['USERS_VIEW', 'ROLES_VIEW', 'AUDIT_VIEW'],
    children: [
      { title: 'Users', href: '/dashboard/access-control/users', icon: Users, permissions: ['USERS_VIEW'] },
      { title: 'Roles', href: '/dashboard/access-control/roles', icon: Shield, permissions: ['ROLES_VIEW'] },
      { title: 'Permissions', href: '/dashboard/access-control/permissions', icon: ShieldCheck, permissions: ['ROLES_VIEW'] },
      { title: 'Approvals', href: '/dashboard/approvals', icon: CheckSquare, permissions: ['APPROVALS_VIEW'] },
      { title: 'Audit Logs', href: '/dashboard/audit-logs', icon: History, permissions: ['AUDIT_VIEW'] },
      { title: 'Notifications', href: '/dashboard/notifications', icon: Bell, permissions: [] },
      { title: 'Settings', href: '/dashboard/settings', icon: Settings, permissions: [] },
    ],
  },
];
