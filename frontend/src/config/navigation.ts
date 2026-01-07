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
} from 'lucide-react';

export interface NavItem {
  title: string;
  href?: string;
  icon?: LucideIcon;
  permissions?: string[];
  children?: NavItem[];
  badge?: string;
}

export const navigation: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    permissions: [],
  },
  {
    title: 'Sales Channels',
    icon: Network,
    permissions: ['channels:view'],
    children: [
      { title: 'All Channels', href: '/channels', permissions: ['channels:view'] },
      { title: 'Channel Pricing', href: '/channels/pricing', permissions: ['channels:view'] },
      { title: 'Channel Inventory', href: '/channels/inventory', permissions: ['channels:view'] },
      { title: 'Marketplace Orders', href: '/channels/orders', permissions: ['channels:view'] },
      { title: 'Channel Reports', href: '/channels/reports', permissions: ['channels:view'] },
    ],
  },
  {
    title: 'Orders',
    icon: ShoppingCart,
    permissions: ['orders:view'],
    children: [
      { title: 'All Orders', href: '/orders', permissions: ['orders:view'] },
      { title: 'Picklists', href: '/orders/picklists', icon: ClipboardList, permissions: ['orders:view'] },
      { title: 'Order Allocation', href: '/orders/allocation', permissions: ['orders:view'] },
    ],
  },
  {
    title: 'Inventory',
    icon: Warehouse,
    permissions: ['inventory:view', 'warehouses:view', 'transfers:view', 'wms:view'],
    children: [
      { title: 'Stock Summary', href: '/inventory', permissions: ['inventory:view'] },
      { title: 'Warehouses', href: '/inventory/warehouses', permissions: ['warehouses:view'] },
      { title: 'Transfers', href: '/inventory/transfers', permissions: ['transfers:view'] },
    ],
  },
  {
    title: 'WMS',
    icon: Grid3X3,
    permissions: ['wms:view'],
    children: [
      { title: 'Zones', href: '/wms/zones', icon: Layers, permissions: ['wms:view'] },
      { title: 'Bins', href: '/wms/bins', icon: Grid3X3, permissions: ['wms:view'] },
      { title: 'Putaway Rules', href: '/wms/putaway-rules', icon: ArrowRightLeft, permissions: ['wms:view'] },
      { title: 'Bin Enquiry', href: '/wms/bin-enquiry', permissions: ['wms:view'] },
    ],
  },
  {
    title: 'Logistics',
    icon: Truck,
    permissions: ['shipments:view'],
    children: [
      { title: 'Shipments', href: '/logistics/shipments', permissions: ['shipments:view'] },
      { title: 'SLA Dashboard', href: '/logistics/sla-dashboard', icon: Gauge, permissions: ['shipments:view'] },
      { title: 'Manifests', href: '/logistics/manifests', permissions: ['shipments:view'] },
      { title: 'Transporters', href: '/logistics/transporters', permissions: ['shipments:view'] },
      { title: 'Rate Cards', href: '/logistics/rate-cards', icon: Calculator, permissions: ['shipments:view'] },
      { title: 'Serviceability', href: '/logistics/serviceability', icon: MapPin, permissions: ['shipments:view'] },
      { title: 'Allocation Rules', href: '/logistics/allocation-rules', icon: Network, permissions: ['shipments:view'] },
    ],
  },
  {
    title: 'Procurement',
    icon: Building2,
    permissions: ['vendors:view', 'purchase:view'],
    children: [
      { title: 'Vendors', href: '/procurement/vendors', permissions: ['vendors:view'] },
      { title: 'Requisitions', href: '/procurement/requisitions', icon: FileText, permissions: ['purchase:view'] },
      { title: 'Purchase Orders', href: '/procurement/purchase-orders', permissions: ['purchase:view'] },
      { title: 'GRN', href: '/procurement/grn', permissions: ['grn:view'] },
      { title: 'Vendor Invoices', href: '/procurement/vendor-invoices', icon: Receipt, permissions: ['purchase:view'] },
      { title: '3-Way Match', href: '/procurement/three-way-match', icon: FileCheck, permissions: ['purchase:view'] },
    ],
  },
  {
    title: 'Finance',
    icon: DollarSign,
    permissions: ['accounting:view'],
    children: [
      { title: 'Chart of Accounts', href: '/finance/chart-of-accounts', permissions: ['accounting:view'] },
      { title: 'Financial Periods', href: '/finance/periods', icon: Clock, permissions: ['accounting:view'] },
      { title: 'Journal Entries', href: '/finance/journal-entries', permissions: ['accounting:view'] },
      { title: 'General Ledger', href: '/finance/general-ledger', permissions: ['accounting:view'] },
      { title: 'Cost Centers', href: '/finance/cost-centers', permissions: ['accounting:view'] },
    ],
  },
  {
    title: 'Reports',
    icon: BarChart3,
    permissions: ['accounting:view'],
    children: [
      { title: 'Trial Balance', href: '/reports/trial-balance', icon: Scale, permissions: ['accounting:view'] },
      { title: 'Profit & Loss', href: '/reports/profit-loss', icon: TrendingUp, permissions: ['accounting:view'] },
      { title: 'Balance Sheet', href: '/reports/balance-sheet', icon: BarChart3, permissions: ['accounting:view'] },
      { title: 'Channel P&L', href: '/reports/channel-pl', permissions: ['accounting:view'] },
      { title: 'Channel Balance Sheet', href: '/reports/channel-balance-sheet', permissions: ['accounting:view'] },
    ],
  },
  {
    title: 'Billing',
    icon: FileText,
    permissions: ['billing:view'],
    children: [
      { title: 'Invoices', href: '/billing/invoices', permissions: ['billing:view'] },
      { title: 'E-Way Bills', href: '/billing/eway-bills', permissions: ['billing:view'] },
      { title: 'Credit Notes', href: '/billing/credit-notes', permissions: ['billing:view'] },
    ],
  },
  {
    title: 'Service',
    icon: Wrench,
    permissions: ['service:view', 'technicians:view'],
    children: [
      { title: 'Service Requests', href: '/service/requests', permissions: ['service:view'] },
      { title: 'Installations', href: '/service/installations', permissions: ['service:view'] },
      { title: 'Warranty Claims', href: '/service/warranty-claims', icon: AlertTriangle, permissions: ['service:view'] },
      { title: 'AMC Contracts', href: '/service/amc', permissions: ['service:view'] },
      { title: 'Technicians', href: '/service/technicians', permissions: ['technicians:view'] },
    ],
  },
  {
    title: 'Distribution',
    icon: Store,
    permissions: ['dealers:view'],
    children: [
      { title: 'Dealers', href: '/distribution/dealers', permissions: ['dealers:view'] },
      { title: 'Pricing Tiers', href: '/distribution/pricing-tiers', permissions: ['dealers:view'] },
      { title: 'Franchisees', href: '/distribution/franchisees', permissions: ['dealers:view'] },
      { title: 'Franchisee Serviceability', href: '/distribution/franchisee-serviceability', icon: MapPin, permissions: ['dealers:view'] },
    ],
  },
  {
    title: 'Products',
    icon: Package,
    permissions: ['products:view', 'categories:view', 'brands:view'],
    children: [
      { title: 'All Products', href: '/products', permissions: ['products:view'] },
      { title: 'Categories', href: '/products/categories', icon: FolderTree, permissions: ['categories:view'] },
      { title: 'Brands', href: '/products/brands', icon: Tag, permissions: ['brands:view'] },
    ],
  },
  {
    title: 'CRM',
    icon: UserCircle,
    permissions: ['customers:view', 'leads:view'],
    children: [
      { title: 'Customers', href: '/crm/customers', permissions: ['customers:view'] },
      { title: 'Customer 360', href: '/crm/customer-360', permissions: ['customers:view'] },
      { title: 'Leads', href: '/crm/leads', permissions: ['leads:view'] },
      { title: 'Call Center', href: '/crm/call-center', permissions: ['customers:view'] },
      { title: 'Escalations', href: '/crm/escalations', permissions: ['customers:view'] },
    ],
  },
  {
    title: 'Marketing',
    icon: Megaphone,
    permissions: ['campaigns:view'],
    children: [
      { title: 'Campaigns', href: '/marketing/campaigns', permissions: ['campaigns:view'] },
      { title: 'Promotions', href: '/marketing/promotions', permissions: ['campaigns:view'] },
      { title: 'Commissions', href: '/marketing/commissions', permissions: ['campaigns:view'] },
    ],
  },
  {
    title: 'Access Control',
    icon: Shield,
    permissions: ['users:view', 'roles:view'],
    children: [
      { title: 'Users', href: '/access-control/users', permissions: ['users:view'] },
      { title: 'Roles', href: '/access-control/roles', permissions: ['roles:view'] },
    ],
  },
  {
    title: 'Serialization',
    href: '/serialization',
    icon: Barcode,
    permissions: ['products:view'],
  },
  {
    title: 'Approvals',
    href: '/approvals',
    icon: CheckSquare,
    permissions: ['approvals:view'],
    badge: 'pending',
  },
  {
    title: 'Audit Logs',
    href: '/audit-logs',
    icon: History,
    permissions: ['audit:view'],
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
    permissions: [],
  },
];
