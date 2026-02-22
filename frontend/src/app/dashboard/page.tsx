'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import {
  ShoppingCart,
  Package,
  Users,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Wrench,
  Truck,
  Building2,
  Briefcase,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  ArrowRight,
  Info,
  CreditCard,
  X,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { dashboardApi, notificationsApi } from '@/lib/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  isLoading?: boolean;
  href?: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const STATUS_COLORS: Record<string, string> = {
  DELIVERED: '#10B981',
  SHIPPED: '#3B82F6',
  PROCESSING: '#F59E0B',
  PENDING: '#EF4444',
  CONFIRMED: '#8B5CF6',
  CANCELLED: '#6B7280',
};

const announcementTypeColors: Record<string, string> = {
  INFO: 'bg-blue-50 border-blue-200 text-blue-800',
  WARNING: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  SUCCESS: 'bg-green-50 border-green-200 text-green-800',
  ERROR: 'bg-red-50 border-red-200 text-red-800',
};

const announcementTypeIcons: Record<string, typeof Info> = {
  INFO: Info,
  WARNING: AlertTriangle,
  SUCCESS: CheckCircle,
  ERROR: AlertCircle,
};

function StatCard({ title, value, change, icon, isLoading, href }: StatCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-4" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    );
  }

  const content = (
    <Card className={href ? 'hover:shadow-md transition-shadow cursor-pointer' : ''}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <p className="flex items-center text-xs text-muted-foreground mt-1">
            {change >= 0 ? (
              <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
            ) : (
              <TrendingDown className="mr-1 h-3 w-3 text-red-500" />
            )}
            <span className={change >= 0 ? 'text-green-500' : 'text-red-500'}>
              {change >= 0 ? '+' : ''}{change}%
            </span>
            <span className="ml-1">from last period</span>
          </p>
        )}
      </CardContent>
    </Card>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}

export default function DashboardPage() {
  const queryClient = useQueryClient();

  // Single combined query — replaces 7+ individual queries
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard-combined'],
    queryFn: () => dashboardApi.getCombined(30),
    staleTime: 5 * 60 * 1000,
  });

  // Announcements kept separate (different module, already fast)
  const { data: announcements } = useQuery({
    queryKey: ['dashboard-announcements'],
    queryFn: async () => {
      try {
        const result = await notificationsApi.getActiveAnnouncements();
        return result.announcements || [];
      } catch {
        return [];
      }
    },
  });

  const dismissAnnouncementMutation = useMutation({
    mutationFn: notificationsApi.dismissAnnouncement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-announcements'] });
    },
  });

  const stats = dashboard?.stats;
  const hrDashboard = dashboard?.hr_dashboard as Record<string, number> | null | undefined;
  const fixedAssets = dashboard?.fixed_assets as Record<string, number> | null | undefined;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Real chart data from API
  const salesTrendData = (dashboard?.sales_trend?.labels ?? []).map((label, i) => ({
    date: label,
    revenue: (dashboard?.sales_trend?.revenue ?? [])[i] ?? 0,
    orders: (dashboard?.sales_trend?.orders ?? [])[i] ?? 0,
  }));

  const orderStatusData = (dashboard?.order_status?.items ?? []).map((item) => ({
    name: item.status.charAt(0) + item.status.slice(1).toLowerCase(),
    value: item.count,
    color: STATUS_COLORS[item.status] ?? '#6B7280',
  }));

  const categoryData = (dashboard?.category_sales?.items ?? []).map((item) => ({
    name: item.name,
    sales: item.revenue,
  }));

  const topProducts = dashboard?.top_products?.items ?? [];
  const recentActivity = dashboard?.recent_activity ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to your ERP Control Panel. Here&apos;s an overview of your business.
        </p>
      </div>

      {/* Active Announcements */}
      {announcements && announcements.length > 0 && (
        <div className="space-y-2">
          {announcements.slice(0, 2).map((announcement) => {
            const Icon = announcementTypeIcons[announcement.announcement_type] || Info;
            const colorClass = announcementTypeColors[announcement.announcement_type] || announcementTypeColors.INFO;
            return (
              <div
                key={announcement.id}
                className={`flex items-center justify-between p-3 rounded-lg border ${colorClass}`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5" />
                  <div>
                    <span className="font-medium">{announcement.title}</span>
                    <span className="mx-2">-</span>
                    <span>{announcement.message}</span>
                  </div>
                </div>
                {announcement.is_dismissible && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => dismissAnnouncementMutation.mutate(announcement.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Main Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Revenue"
          value={formatCurrency(stats?.total_revenue ?? 0)}
          change={stats?.revenue_change}
          icon={<DollarSign className="h-4 w-4" />}
          isLoading={isLoading}
          href="/dashboard/reports/profit-loss"
        />
        <StatCard
          title="Total Orders"
          value={(stats?.total_orders ?? 0).toLocaleString()}
          change={stats?.orders_change}
          icon={<ShoppingCart className="h-4 w-4" />}
          isLoading={isLoading}
          href="/dashboard/orders"
        />
        <StatCard
          title="Total Customers"
          value={(stats?.total_customers ?? 0).toLocaleString()}
          change={stats?.customers_change}
          icon={<Users className="h-4 w-4" />}
          isLoading={isLoading}
          href="/dashboard/crm/customers"
        />
        <StatCard
          title="Products"
          value={(stats?.total_products ?? 0).toLocaleString()}
          icon={<Package className="h-4 w-4" />}
          isLoading={isLoading}
          href="/dashboard/catalog"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Revenue Trend Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Revenue Trend</CardTitle>
            <CardDescription>Last 7 days revenue and orders</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              {isLoading ? (
                <Skeleton className="h-full w-full" />
              ) : salesTrendData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={salesTrendData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis yAxisId="left" className="text-xs" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis yAxisId="right" orientation="right" className="text-xs" />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))' }}
                      formatter={(value, name) => [
                        name === 'Revenue' ? formatCurrency(value as number) : value,
                        name
                      ]}
                    />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} name="Revenue" />
                    <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#10B981" strokeWidth={2} dot={{ fill: '#10B981' }} name="Orders" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                  No sales data for the last 7 days
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Order Status Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Order Status</CardTitle>
            <CardDescription>Distribution by status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              {isLoading ? (
                <Skeleton className="h-full w-full" />
              ) : orderStatusData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={orderStatusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                      {orderStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))' }}
                      formatter={(value) => [value, 'Orders']}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                  No order data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Required */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="/dashboard/orders?status=PENDING">
          <Card className="border-orange-200 dark:border-orange-800 hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Orders</CardTitle>
              <ShoppingCart className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.pending_orders ?? 0)}
              </div>
              <p className="text-xs text-muted-foreground">Requires attention</p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/service/requests?status=PENDING">
          <Card className="border-blue-200 dark:border-blue-800 hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Service Requests</CardTitle>
              <Wrench className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.pending_service_requests ?? 0)}
              </div>
              <p className="text-xs text-muted-foreground">Pending assignment</p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/inventory?low_stock=true">
          <Card className="border-red-200 dark:border-red-800 hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Low Stock Items</CardTitle>
              <Package className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.low_stock_items ?? 0)}
              </div>
              <p className="text-xs text-muted-foreground">Below reorder level</p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/logistics/shipments?status=IN_TRANSIT">
          <Card className="border-green-200 dark:border-green-800 hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Transit</CardTitle>
              <Truck className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.shipments_in_transit ?? 0)}
              </div>
              <p className="text-xs text-muted-foreground">Shipments on the way</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Category Sales & HR/Assets Summary */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Category Sales Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sales by Category</CardTitle>
            <CardDescription>Top performing categories</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              {isLoading ? (
                <Skeleton className="h-full w-full" />
              ) : categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis type="number" className="text-xs" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="name" className="text-xs" width={100} />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))' }}
                      formatter={(value) => [formatCurrency(value as number), 'Sales']}
                    />
                    <Bar dataKey="sales" radius={[0, 4, 4, 0]}>
                      {categoryData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                  No category data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* HR Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">HR Overview</CardTitle>
              <CardDescription>Employee & attendance summary</CardDescription>
            </div>
            <Link href="/dashboard/hr">
              <Button variant="ghost" size="sm">
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {hrDashboard ? (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Active Employees</span>
                  </div>
                  <span className="font-semibold">{hrDashboard.active_employees ?? 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Present Today</span>
                  </div>
                  <span className="font-semibold text-green-600">{hrDashboard.present_today ?? 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-orange-500" />
                    <span className="text-sm">Pending Leaves</span>
                  </div>
                  <Badge variant="secondary">{hrDashboard.pending_leave_requests ?? 0}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Pending Payroll</span>
                  </div>
                  <Badge variant="secondary">{hrDashboard.pending_payroll_approval ?? 0}</Badge>
                </div>
              </>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                <Briefcase className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">HR module not configured</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Fixed Assets Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">Fixed Assets</CardTitle>
              <CardDescription>Asset value summary</CardDescription>
            </div>
            <Link href="/dashboard/finance/fixed-assets">
              <Button variant="ghost" size="sm">
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {fixedAssets ? (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Total Assets</span>
                  </div>
                  <span className="font-semibold">{fixedAssets.total_assets ?? 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Book Value</span>
                  </div>
                  <span className="font-semibold">
                    {formatCurrency(fixedAssets.total_current_book_value ?? 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wrench className="h-4 w-4 text-orange-500" />
                    <span className="text-sm">Under Maintenance</span>
                  </div>
                  <Badge variant="secondary">{fixedAssets.under_maintenance ?? 0}</Badge>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Depreciation Progress</span>
                    <span>
                      {fixedAssets.total_capitalized_value
                        ? Math.round(
                            ((fixedAssets.total_accumulated_depreciation ?? 0) /
                              fixedAssets.total_capitalized_value) * 100
                          )
                        : 0}%
                    </span>
                  </div>
                  <Progress
                    value={
                      fixedAssets.total_capitalized_value
                        ? ((fixedAssets.total_accumulated_depreciation ?? 0) /
                            fixedAssets.total_capitalized_value) * 100
                        : 0
                    }
                    className="h-2"
                  />
                </div>
              </>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                <Building2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No assets registered</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity, Products & Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {isLoading ? (
                <>
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="flex items-center gap-4">
                      <Skeleton className="h-2 w-2 rounded-full" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-48 mb-1" />
                        <Skeleton className="h-3 w-24" />
                      </div>
                    </div>
                  ))}
                </>
              ) : recentActivity.length > 0 ? (
                recentActivity.map((activity, i) => (
                  <div key={activity.id ?? i} className="flex items-center gap-4">
                    <div className="h-2 w-2 rounded-full bg-blue-500" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {activity.timestamp
                          ? formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })
                          : 'recently'}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">No recent activity</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Selling Products</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {isLoading ? (
                <>
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Skeleton className="h-6 w-6 rounded-full" />
                        <Skeleton className="h-4 w-32" />
                      </div>
                      <Skeleton className="h-4 w-16" />
                    </div>
                  ))}
                </>
              ) : topProducts.length > 0 ? (
                topProducts.map((product, i) => (
                  <div key={product.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span
                        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
                          i === 0 ? 'bg-yellow-100 text-yellow-800'
                          : i === 1 ? 'bg-gray-100 text-gray-800'
                          : i === 2 ? 'bg-orange-100 text-orange-800'
                          : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {i + 1}
                      </span>
                      <span className="text-sm font-medium truncate max-w-[150px]">{product.name}</span>
                    </div>
                    <Badge variant="secondary">{product.sales} units</Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">No sales data yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'New Order', href: '/dashboard/orders/new', icon: ShoppingCart },
                { label: 'Add Product', href: '/dashboard/catalog/new', icon: Package },
                { label: 'Create PO', href: '/dashboard/procurement/purchase-orders?create=true', icon: DollarSign },
                { label: 'Service Req', href: '/dashboard/service/requests/new', icon: Wrench },
                { label: 'New Employee', href: '/dashboard/hr/employees/new', icon: Users },
                { label: 'Add Asset', href: '/dashboard/finance/fixed-assets', icon: Building2 },
              ].map((action, i) => {
                const Icon = action.icon;
                return (
                  <Link
                    key={i}
                    href={action.href}
                    className="flex items-center justify-center gap-2 rounded-lg border p-3 text-sm font-medium transition-colors hover:bg-accent"
                  >
                    <Icon className="h-4 w-4" />
                    {action.label}
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
