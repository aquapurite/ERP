'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Play, Pause, CheckCircle, ClipboardList, Package, User, Clock, Printer } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatDate } from '@/lib/utils';

interface Picklist {
  id: string;
  picklist_number: string;
  warehouse_id: string;
  warehouse_name: string;
  picker_id?: string;
  picker_name?: string;
  status: 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  total_orders: number;
  total_items: number;
  picked_items: number;
  total_quantity: number;
  picked_quantity: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_time_minutes?: number;
}

interface PicklistStats {
  total_picklists: number;
  pending: number;
  in_progress: number;
  completed_today: number;
  avg_pick_time_minutes: number;
}

const picklistsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; warehouse_id?: string }) => {
    try {
      const { data } = await apiClient.get('/picklists', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<PicklistStats> => {
    try {
      const { data } = await apiClient.get('/picklists/stats');
      return data;
    } catch {
      return { total_picklists: 0, pending: 0, in_progress: 0, completed_today: 0, avg_pick_time_minutes: 0 };
    }
  },
  create: async (params: { warehouse_id: string; order_ids: string[]; priority?: string }) => {
    const { data } = await apiClient.post('/picklists', params);
    return data;
  },
  assign: async (id: string, pickerId: string) => {
    const { data } = await apiClient.post(`/picklists/${id}/assign`, { picker_id: pickerId });
    return data;
  },
  start: async (id: string) => {
    const { data } = await apiClient.post(`/picklists/${id}/start`);
    return data;
  },
  complete: async (id: string) => {
    const { data } = await apiClient.post(`/picklists/${id}/complete`);
    return data;
  },
};

const statusColors: Record<string, string> = {
  PENDING: 'bg-gray-100 text-gray-800',
  ASSIGNED: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-600',
  NORMAL: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-700',
  URGENT: 'bg-red-100 text-red-700',
};

const columns: ColumnDef<Picklist>[] = [
  {
    accessorKey: 'picklist_number',
    header: 'Picklist #',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <ClipboardList className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-mono font-medium">{row.original.picklist_number}</div>
          <div className="text-sm text-muted-foreground">{row.original.warehouse_name}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'priority',
    header: 'Priority',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[row.original.priority]}`}>
        {row.original.priority}
      </span>
    ),
  },
  {
    accessorKey: 'picker_name',
    header: 'Picker',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <User className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">{row.original.picker_name || 'Unassigned'}</span>
      </div>
    ),
  },
  {
    accessorKey: 'orders_items',
    header: 'Orders / Items',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.total_orders} orders</div>
        <div className="text-muted-foreground">{row.original.total_items} items</div>
      </div>
    ),
  },
  {
    accessorKey: 'progress',
    header: 'Progress',
    cell: ({ row }) => {
      const progress = row.original.total_quantity > 0
        ? (row.original.picked_quantity / row.original.total_quantity) * 100
        : 0;
      return (
        <div className="space-y-1">
          <div className="text-sm font-medium">{progress.toFixed(0)}%</div>
          <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full ${progress === 100 ? 'bg-green-500' : 'bg-blue-500'}`}
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-xs text-muted-foreground">
            {row.original.picked_quantity} / {row.original.total_quantity} qty
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[row.original.status]}`}>
        {row.original.status.replace('_', ' ')}
      </span>
    ),
  },
  {
    accessorKey: 'time',
    header: 'Time',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3 text-muted-foreground" />
          {row.original.estimated_time_minutes ? `${row.original.estimated_time_minutes} min` : '-'}
        </div>
        {row.original.started_at && (
          <div className="text-xs text-muted-foreground">
            Started: {formatDate(row.original.started_at)}
          </div>
        )}
      </div>
    ),
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const queryClient = useQueryClient();

      const startMutation = useMutation({
        mutationFn: () => picklistsApi.start(row.original.id),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['picklists'] });
          toast.success('Picklist started');
        },
      });

      const completeMutation = useMutation({
        mutationFn: () => picklistsApi.complete(row.original.id),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['picklists'] });
          toast.success('Picklist completed');
        },
      });

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Eye className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Printer className="mr-2 h-4 w-4" />
              Print Picklist
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {row.original.status === 'ASSIGNED' && (
              <DropdownMenuItem onClick={() => startMutation.mutate()}>
                <Play className="mr-2 h-4 w-4" />
                Start Picking
              </DropdownMenuItem>
            )}
            {row.original.status === 'IN_PROGRESS' && (
              <DropdownMenuItem onClick={() => completeMutation.mutate()}>
                <CheckCircle className="mr-2 h-4 w-4" />
                Mark Complete
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

export default function PicklistsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['picklists', page, pageSize, statusFilter],
    queryFn: () => picklistsApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter !== 'all' ? statusFilter : undefined,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['picklists-stats'],
    queryFn: picklistsApi.getStats,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Picklists"
        description="Manage order picking and warehouse fulfillment"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Picklist
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Create Picklist</DialogTitle>
                <DialogDescription>
                  Select orders to include in a new picklist for warehouse picking.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Warehouse</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select warehouse" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="wh1">Mumbai Main</SelectItem>
                      <SelectItem value="wh2">Delhi Hub</SelectItem>
                      <SelectItem value="wh3">Bangalore DC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Priority</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="LOW">Low</SelectItem>
                      <SelectItem value="NORMAL">Normal</SelectItem>
                      <SelectItem value="HIGH">High</SelectItem>
                      <SelectItem value="URGENT">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Assign Picker</label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select picker (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="picker1">Ramesh K.</SelectItem>
                      <SelectItem value="picker2">Suresh M.</SelectItem>
                      <SelectItem value="picker3">Vijay S.</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button>Create Picklist</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Picklists</CardTitle>
            <ClipboardList className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_picklists || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Pause className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats?.pending || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Play className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats?.in_progress || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.completed_today || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Pick Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avg_pick_time_minutes || 0}m</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="ASSIGNED">Assigned</SelectItem>
            <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="picklist_number"
        searchPlaceholder="Search picklists..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </div>
  );
}
