'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Send, CheckCircle, XCircle, FileText, ShoppingCart, Clock, AlertCircle, ArrowRight } from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatCurrency, formatDate } from '@/lib/utils';

interface PurchaseRequisition {
  id: string;
  pr_number: string;
  requester_id: string;
  requester_name: string;
  department: string;
  warehouse_id: string;
  warehouse_name: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CONVERTED' | 'CANCELLED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  total_items: number;
  total_amount: number;
  required_by_date?: string;
  justification?: string;
  approved_by?: string;
  approved_at?: string;
  po_number?: string;
  created_at: string;
}

interface PRStats {
  total: number;
  draft: number;
  pending_approval: number;
  approved: number;
  converted_to_po: number;
  avg_approval_time_hours: number;
}

const requisitionsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/purchase/requisitions', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<PRStats> => {
    try {
      const { data } = await apiClient.get('/purchase/requisitions/stats');
      return data;
    } catch {
      return { total: 0, draft: 0, pending_approval: 0, approved: 0, converted_to_po: 0, avg_approval_time_hours: 0 };
    }
  },
  create: async (params: { warehouse_id: string; required_by_date: string; priority: string; justification: string; items: { product_id: string; quantity: number }[] }) => {
    const { data } = await apiClient.post('/purchase/requisitions', params);
    return data;
  },
  submit: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/submit`);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/reject`, { reason });
    return data;
  },
  convertToPO: async (id: string, vendorId: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/convert-to-po`, { vendor_id: vendorId });
    return data;
  },
};

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  SUBMITTED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  CONVERTED: 'bg-purple-100 text-purple-800',
  CANCELLED: 'bg-gray-100 text-gray-600',
};

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-600',
  NORMAL: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-700',
  URGENT: 'bg-red-100 text-red-700',
};

export default function PurchaseRequisitionsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedPR, setSelectedPR] = useState<PurchaseRequisition | null>(null);
  const [isConvertDialogOpen, setIsConvertDialogOpen] = useState(false);

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-requisitions', page, pageSize, statusFilter],
    queryFn: () => requisitionsApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter !== 'all' ? statusFilter : undefined,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['pr-stats'],
    queryFn: requisitionsApi.getStats,
  });

  const submitMutation = useMutation({
    mutationFn: (id: string) => requisitionsApi.submit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      toast.success('PR submitted for approval');
    },
    onError: () => toast.error('Failed to submit PR'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => requisitionsApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      toast.success('PR approved successfully');
    },
    onError: () => toast.error('Failed to approve PR'),
  });

  const columns: ColumnDef<PurchaseRequisition>[] = [
    {
      accessorKey: 'pr_number',
      header: 'PR Number',
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <div className="font-mono font-medium">{row.original.pr_number}</div>
            <div className="text-sm text-muted-foreground">{row.original.department}</div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'requester_name',
      header: 'Requester',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.requester_name}</div>
          <div className="text-sm text-muted-foreground">
            {formatDate(row.original.created_at)}
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'warehouse_name',
      header: 'Warehouse',
      cell: ({ row }) => (
        <span className="text-sm">{row.original.warehouse_name}</span>
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
      accessorKey: 'items_amount',
      header: 'Items / Amount',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.total_items} items</div>
          <div className="text-sm text-muted-foreground">{formatCurrency(row.original.total_amount)}</div>
        </div>
      ),
    },
    {
      accessorKey: 'required_by_date',
      header: 'Required By',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">
            {row.original.required_by_date ? formatDate(row.original.required_by_date) : '-'}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[row.original.status]}`}>
            {row.original.status.replace('_', ' ')}
          </span>
          {row.original.po_number && (
            <div className="text-xs text-muted-foreground mt-1">
              PO: {row.original.po_number}
            </div>
          )}
        </div>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const pr = row.original;
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
              {pr.status === 'DRAFT' && (
                <DropdownMenuItem onClick={() => submitMutation.mutate(pr.id)}>
                  <Send className="mr-2 h-4 w-4" />
                  Submit for Approval
                </DropdownMenuItem>
              )}
              {pr.status === 'SUBMITTED' && (
                <>
                  <DropdownMenuItem onClick={() => approveMutation.mutate(pr.id)}>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Approve
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-red-600">
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject
                  </DropdownMenuItem>
                </>
              )}
              {pr.status === 'APPROVED' && (
                <DropdownMenuItem onClick={() => { setSelectedPR(pr); setIsConvertDialogOpen(true); }}>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  Convert to PO
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Requisitions"
        description="Manage purchase requests and approval workflow"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create PR
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Purchase Requisition</DialogTitle>
                <DialogDescription>
                  Request items for procurement. This will go through an approval workflow.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
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
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Required By Date</label>
                  <Input type="date" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Justification</label>
                  <Textarea placeholder="Explain why these items are needed..." rows={3} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Items</label>
                  <div className="border rounded-lg p-4 space-y-3">
                    <div className="grid grid-cols-12 gap-2 items-center">
                      <div className="col-span-6">
                        <Select>
                          <SelectTrigger>
                            <SelectValue placeholder="Select product" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="p1">AquaPure UV Compact</SelectItem>
                            <SelectItem value="p2">AquaPure RO Premium</SelectItem>
                            <SelectItem value="p3">Membrane Filter 75GPD</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-3">
                        <Input type="number" placeholder="Qty" />
                      </div>
                      <div className="col-span-3">
                        <Button variant="outline" size="sm" className="w-full">
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground text-center py-2">
                      Add items to this requisition
                    </div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button variant="secondary">Save as Draft</Button>
                <Button>Submit for Approval</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PRs</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft</CardTitle>
            <FileText className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats?.draft || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.pending_approval || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.approved || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Converted to PO</CardTitle>
            <ShoppingCart className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats?.converted_to_po || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Approval Time</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avg_approval_time_hours || 0}h</div>
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
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="SUBMITTED">Submitted</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
            <SelectItem value="CONVERTED">Converted</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="pr_number"
        searchPlaceholder="Search PR number..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Convert to PO Dialog */}
      <Dialog open={isConvertDialogOpen} onOpenChange={setIsConvertDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Convert to Purchase Order</DialogTitle>
            <DialogDescription>
              Select a vendor to create a Purchase Order from PR {selectedPR?.pr_number}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Vendor</label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Choose vendor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="v1">Aqua Systems Pvt Ltd</SelectItem>
                  <SelectItem value="v2">Filter World India</SelectItem>
                  <SelectItem value="v3">Pure Flow Technologies</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Items:</span>
                  <span className="font-medium">{selectedPR?.total_items || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount:</span>
                  <span className="font-medium">{formatCurrency(selectedPR?.total_amount || 0)}</span>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConvertDialogOpen(false)}>Cancel</Button>
            <Button>Create Purchase Order</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
