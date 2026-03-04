'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Package,
  ShoppingCart,
  Users,
  RotateCcw,
  Loader2,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/data-table/data-table';
import { Checkbox } from '@/components/ui/checkbox';
import { PageHeader } from '@/components/common';
import { cjdquickApi } from '@/lib/api';

interface SyncLog {
  id: string;
  entity_type: string;
  entity_id: string;
  oms_id: string | null;
  operation: string;
  status: string;
  error_message: string | null;
  retry_count: number;
  synced_at: string | null;
  created_at: string;
}

interface SyncStats {
  total_syncs: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
  by_entity: Record<string, Record<string, number>>;
  last_sync_at: string | null;
}

interface UninvoicedOrder {
  id: string;
  order_number: string;
  customer_name: string;
  status: string;
  total_amount: number;
  shipped_at: string | null;
  created_at: string;
  item_count: number;
  has_serials: boolean;
}

const entityTypes = [
  { value: 'all', label: 'All Entities' },
  { value: 'PRODUCT', label: 'Product' },
  { value: 'ORDER', label: 'Order' },
  { value: 'CUSTOMER', label: 'Customer' },
  { value: 'PO', label: 'Purchase Order' },
  { value: 'RETURN', label: 'Return' },
  { value: 'WEBHOOK', label: 'Webhook' },
];

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'SUCCESS', label: 'Success' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'PENDING', label: 'Pending' },
];

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === 'SUCCESS'
      ? 'default'
      : status === 'FAILED'
        ? 'destructive'
        : 'secondary';
  return <Badge variant={variant}>{status}</Badge>;
}

function EntityIcon({ type }: { type: string }) {
  switch (type) {
    case 'PRODUCT':
      return <Package className="h-4 w-4" />;
    case 'ORDER':
      return <ShoppingCart className="h-4 w-4" />;
    case 'CUSTOMER':
      return <Users className="h-4 w-4" />;
    default:
      return <Zap className="h-4 w-4" />;
  }
}

export default function OMSSyncPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [entityFilter, setEntityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedUninvoiced, setSelectedUninvoiced] = useState<string[]>([]);
  const [showReconciliation, setShowReconciliation] = useState(false);

  // Fetch sync stats
  const { data: stats, isLoading: statsLoading } = useQuery<SyncStats>({
    queryKey: ['sync-stats'],
    queryFn: () => cjdquickApi.getSyncStats(),
    refetchInterval: 30000,
  });

  // Fetch sync logs
  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ['sync-logs', page, pageSize, entityFilter, statusFilter],
    queryFn: () =>
      cjdquickApi.listSyncLogs({
        page,
        page_size: pageSize,
        entity_type: entityFilter !== 'all' ? entityFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      }),
  });

  // Mutations
  const bulkSyncProducts = useMutation({
    mutationFn: () => cjdquickApi.bulkSyncProducts(),
    onSuccess: (data) => {
      toast.success(`Products synced: ${data.success} success, ${data.failed} failed out of ${data.total}`);
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
      queryClient.invalidateQueries({ queryKey: ['sync-logs'] });
    },
    onError: () => toast.error('Bulk product sync failed'),
  });

  const bulkSyncOrders = useMutation({
    mutationFn: () => cjdquickApi.bulkSyncOrders('CONFIRMED'),
    onSuccess: (data) => {
      toast.success(`Orders synced: ${data.success} success, ${data.failed} failed out of ${data.total}`);
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
      queryClient.invalidateQueries({ queryKey: ['sync-logs'] });
    },
    onError: () => toast.error('Bulk order sync failed'),
  });

  const retryAllFailed = useMutation({
    mutationFn: () => cjdquickApi.retryAllFailed(),
    onSuccess: (data) => {
      toast.success(`Retry complete: ${data.success} success, ${data.failed} failed out of ${data.retried} retried`);
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
      queryClient.invalidateQueries({ queryKey: ['sync-logs'] });
    },
    onError: () => toast.error('Retry all failed'),
  });

  const retrySingle = useMutation({
    mutationFn: (logId: string) => cjdquickApi.retrySyncLog(logId),
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Retry successful');
      } else {
        toast.error(data.message || 'Retry failed');
      }
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
      queryClient.invalidateQueries({ queryKey: ['sync-logs'] });
    },
    onError: () => toast.error('Retry failed'),
  });

  // Reconciliation: uninvoiced orders
  const { data: uninvoicedData, isLoading: uninvoicedLoading, refetch: refetchUninvoiced } = useQuery<{
    orders: UninvoicedOrder[];
    total: number;
  }>({
    queryKey: ['uninvoiced-orders'],
    queryFn: () => cjdquickApi.getUninvoicedOrders(30),
    enabled: showReconciliation,
  });

  const generateMissingInvoices = useMutation({
    mutationFn: (orderIds: string[]) => cjdquickApi.generateMissingInvoices(orderIds),
    onSuccess: (data: { total: number; success: number; failed: number; errors: string[] }) => {
      toast.success(`Invoices generated: ${data.success} success, ${data.failed} failed`);
      if (data.errors.length > 0) {
        data.errors.forEach((err: string) => toast.error(err));
      }
      setSelectedUninvoiced([]);
      refetchUninvoiced();
    },
    onError: () => toast.error('Failed to generate missing invoices'),
  });

  const columns: ColumnDef<SyncLog>[] = [
    {
      accessorKey: 'entity_type',
      header: 'Entity Type',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <EntityIcon type={row.original.entity_type} />
          <span className="font-medium">{row.original.entity_type}</span>
        </div>
      ),
    },
    {
      accessorKey: 'entity_id',
      header: 'Entity ID',
      cell: ({ row }) => (
        <span className="font-mono text-xs">{row.original.entity_id.slice(0, 8)}...</span>
      ),
    },
    {
      accessorKey: 'oms_id',
      header: 'OMS ID',
      cell: ({ row }) => row.original.oms_id || '-',
    },
    {
      accessorKey: 'operation',
      header: 'Operation',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <StatusBadge status={row.original.status} />,
    },
    {
      accessorKey: 'error_message',
      header: 'Error',
      cell: ({ row }) =>
        row.original.error_message ? (
          <span className="text-xs text-red-500 max-w-[200px] truncate block" title={row.original.error_message}>
            {row.original.error_message}
          </span>
        ) : (
          '-'
        ),
    },
    {
      accessorKey: 'retry_count',
      header: 'Retries',
    },
    {
      accessorKey: 'synced_at',
      header: 'Synced At',
      cell: ({ row }) =>
        row.original.synced_at
          ? new Date(row.original.synced_at).toLocaleString()
          : '-',
    },
    {
      accessorKey: 'created_at',
      header: 'Created At',
      cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) =>
        row.original.status === 'FAILED' ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => retrySingle.mutate(row.original.id)}
            disabled={retrySingle.isPending}
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            Retry
          </Button>
        ) : null,
    },
  ];

  const logs: SyncLog[] = logsData?.items || [];
  const totalLogs = logsData?.total || 0;
  const totalPages = Math.ceil(totalLogs / pageSize);

  const isAnyBulkRunning =
    bulkSyncProducts.isPending || bulkSyncOrders.isPending || retryAllFailed.isPending;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="OMS Sync Dashboard"
        description="CJDQuick OMS integration status, sync logs, and bulk operations"
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Syncs</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsLoading ? '...' : stats?.total_syncs ?? 0}
            </div>
            {stats?.last_sync_at && (
              <p className="text-xs text-muted-foreground">
                Last: {new Date(stats.last_sync_at).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {statsLoading ? '...' : stats?.success_count ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats && stats.total_syncs > 0
                ? `${((stats.success_count / stats.total_syncs) * 100).toFixed(1)}% success rate`
                : 'No syncs yet'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {statsLoading ? '...' : stats?.failed_count ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {statsLoading ? '...' : stats?.pending_count ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">In progress</p>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <Button
          onClick={() => bulkSyncProducts.mutate()}
          disabled={isAnyBulkRunning}
        >
          {bulkSyncProducts.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Package className="h-4 w-4 mr-2" />
          )}
          Bulk Sync Products
        </Button>
        <Button
          onClick={() => bulkSyncOrders.mutate()}
          disabled={isAnyBulkRunning}
          variant="outline"
        >
          {bulkSyncOrders.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <ShoppingCart className="h-4 w-4 mr-2" />
          )}
          Bulk Sync Orders
        </Button>
        <Button
          onClick={() => retryAllFailed.mutate()}
          disabled={isAnyBulkRunning || (stats?.failed_count ?? 0) === 0}
          variant="secondary"
        >
          {retryAllFailed.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Retry All Failed
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
            queryClient.invalidateQueries({ queryKey: ['sync-logs'] });
          }}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Invoice Reconciliation Section */}
      <Card className="border-yellow-200 bg-yellow-50/50">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <CardTitle className="text-sm font-medium">Invoice Reconciliation</CardTitle>
            {uninvoicedData && uninvoicedData.total > 0 && (
              <Badge variant="destructive">{uninvoicedData.total} uninvoiced</Badge>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setShowReconciliation(!showReconciliation);
              if (!showReconciliation) refetchUninvoiced();
            }}
          >
            {showReconciliation ? 'Hide' : 'Check for Missed Invoices'}
          </Button>
        </CardHeader>
        {showReconciliation && (
          <CardContent>
            <p className="text-xs text-muted-foreground mb-4">
              Orders that were shipped/delivered but have no active TAX_INVOICE. These may have been missed
              during CJDQuick webhook processing or manifest confirmation.
            </p>
            {uninvoicedLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : uninvoicedData && uninvoicedData.orders.length > 0 ? (
              <>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-muted-foreground">
                    {selectedUninvoiced.length} of {uninvoicedData.orders.length} selected
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (selectedUninvoiced.length === uninvoicedData.orders.length) {
                          setSelectedUninvoiced([]);
                        } else {
                          setSelectedUninvoiced(uninvoicedData.orders.map((o) => o.id));
                        }
                      }}
                    >
                      {selectedUninvoiced.length === uninvoicedData.orders.length ? 'Deselect All' : 'Select All'}
                    </Button>
                    <Button
                      size="sm"
                      disabled={selectedUninvoiced.length === 0 || generateMissingInvoices.isPending}
                      onClick={() => generateMissingInvoices.mutate(selectedUninvoiced)}
                    >
                      {generateMissingInvoices.isPending ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <FileText className="h-4 w-4 mr-2" />
                      )}
                      Generate {selectedUninvoiced.length} Invoice(s)
                    </Button>
                  </div>
                </div>
                <div className="border rounded-md">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 w-10"></th>
                        <th className="p-2 text-left">Order</th>
                        <th className="p-2 text-left">Customer</th>
                        <th className="p-2 text-left">Status</th>
                        <th className="p-2 text-right">Amount</th>
                        <th className="p-2 text-center">Serials</th>
                        <th className="p-2 text-left">Shipped</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uninvoicedData.orders.map((order) => (
                        <tr key={order.id} className="border-b hover:bg-muted/30">
                          <td className="p-2">
                            <Checkbox
                              checked={selectedUninvoiced.includes(order.id)}
                              onCheckedChange={(checked) => {
                                setSelectedUninvoiced((prev) =>
                                  checked
                                    ? [...prev, order.id]
                                    : prev.filter((id) => id !== order.id)
                                );
                              }}
                            />
                          </td>
                          <td className="p-2 font-mono text-xs font-medium">{order.order_number}</td>
                          <td className="p-2">{order.customer_name || '-'}</td>
                          <td className="p-2">
                            <Badge variant="secondary" className="text-xs">{order.status}</Badge>
                          </td>
                          <td className="p-2 text-right font-mono">
                            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(order.total_amount)}
                          </td>
                          <td className="p-2 text-center">
                            {order.has_serials ? (
                              <CheckCircle className="h-4 w-4 text-green-500 inline" />
                            ) : (
                              <XCircle className="h-4 w-4 text-gray-300 inline" />
                            )}
                          </td>
                          <td className="p-2 text-xs text-muted-foreground">
                            {order.shipped_at ? new Date(order.shipped_at).toLocaleDateString() : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                <p className="text-sm font-medium">All clear! No uninvoiced orders found.</p>
                <p className="text-xs">All shipped orders have active invoices.</p>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Entity Breakdown */}
      {stats?.by_entity && Object.keys(stats.by_entity).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Sync by Entity Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(stats.by_entity).map(([entity, statuses]) => (
                <div key={entity} className="text-center p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <EntityIcon type={entity} />
                    <span className="text-xs font-medium">{entity}</span>
                  </div>
                  <div className="flex justify-center gap-2 text-xs">
                    {(statuses as Record<string, number>).SUCCESS && (
                      <span className="text-green-600">{(statuses as Record<string, number>).SUCCESS} ok</span>
                    )}
                    {(statuses as Record<string, number>).FAILED && (
                      <span className="text-red-600">{(statuses as Record<string, number>).FAILED} fail</span>
                    )}
                    {(statuses as Record<string, number>).PENDING && (
                      <span className="text-yellow-600">{(statuses as Record<string, number>).PENDING} pending</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={entityFilter} onValueChange={(val) => { setEntityFilter(val); setPage(1); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Entity Type" />
          </SelectTrigger>
          <SelectContent>
            {entityTypes.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={(val) => { setStatusFilter(val); setPage(1); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Sync Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Sync Logs ({totalLogs} total)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {logsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <DataTable columns={columns} data={logs} />
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page <= 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
