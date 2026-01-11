'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, FileText, CheckCircle, XCircle, Upload, Download, AlertTriangle, Clock, DollarSign, FileCheck } from 'lucide-react';
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
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatCurrency, formatDate } from '@/lib/utils';

interface VendorInvoice {
  id: string;
  invoice_number: string;
  vendor_id: string;
  vendor_name: string;
  vendor_code: string;
  po_number?: string;
  grn_number?: string;
  invoice_date: string;
  due_date: string;
  subtotal: number;
  gst_amount: number;
  tds_amount: number;
  total_amount: number;
  status: 'PENDING' | 'UNDER_REVIEW' | 'MATCHED' | 'PARTIAL_MATCH' | 'MISMATCH' | 'APPROVED' | 'REJECTED' | 'PAID';
  match_status: 'NOT_MATCHED' | 'MATCHED' | 'PARTIAL' | 'MISMATCH';
  payment_status: 'UNPAID' | 'PARTIAL' | 'PAID';
  days_until_due: number;
  created_at: string;
}

interface InvoiceStats {
  total_invoices: number;
  pending_review: number;
  matched: number;
  mismatch: number;
  overdue: number;
  total_pending_amount: number;
  total_overdue_amount: number;
}

const vendorInvoicesApi = {
  list: async (params?: { page?: number; size?: number; status?: string; payment_status?: string }) => {
    try {
      const { data } = await apiClient.get('/purchase/vendor-invoices', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<InvoiceStats> => {
    try {
      const { data } = await apiClient.get('/purchase/vendor-invoices/stats');
      return data;
    } catch {
      return { total_invoices: 0, pending_review: 0, matched: 0, mismatch: 0, overdue: 0, total_pending_amount: 0, total_overdue_amount: 0 };
    }
  },
  upload: async (file: File, vendorId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('vendor_id', vendorId);
    const { data } = await apiClient.post('/purchase/vendor-invoices/upload', formData);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-invoices/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-invoices/${id}/reject`, { reason });
    return data;
  },
  initiateMatch: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/vendor-invoices/${id}/match`);
    return data;
  },
};

const statusColors: Record<string, string> = {
  PENDING: 'bg-gray-100 text-gray-800',
  UNDER_REVIEW: 'bg-blue-100 text-blue-800',
  MATCHED: 'bg-green-100 text-green-800',
  PARTIAL_MATCH: 'bg-yellow-100 text-yellow-800',
  MISMATCH: 'bg-red-100 text-red-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  PAID: 'bg-purple-100 text-purple-800',
};

const matchStatusColors: Record<string, string> = {
  NOT_MATCHED: 'bg-gray-100 text-gray-600',
  MATCHED: 'bg-green-100 text-green-700',
  PARTIAL: 'bg-yellow-100 text-yellow-700',
  MISMATCH: 'bg-red-100 text-red-700',
};

const paymentStatusColors: Record<string, string> = {
  UNPAID: 'bg-red-100 text-red-700',
  PARTIAL: 'bg-yellow-100 text-yellow-700',
  PAID: 'bg-green-100 text-green-700',
};

export default function VendorInvoicesPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [paymentFilter, setPaymentFilter] = useState<string>('all');
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['vendor-invoices', page, pageSize, statusFilter, paymentFilter],
    queryFn: () => vendorInvoicesApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      payment_status: paymentFilter !== 'all' ? paymentFilter : undefined,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['vendor-invoices-stats'],
    queryFn: vendorInvoicesApi.getStats,
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => vendorInvoicesApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-invoices'] });
      toast.success('Invoice approved');
    },
  });

  const matchMutation = useMutation({
    mutationFn: (id: string) => vendorInvoicesApi.initiateMatch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-invoices'] });
      toast.success('3-Way match initiated');
    },
  });

  const columns: ColumnDef<VendorInvoice>[] = [
    {
      accessorKey: 'invoice_number',
      header: 'Invoice',
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <div className="font-mono font-medium">{row.original.invoice_number}</div>
            <div className="text-sm text-muted-foreground">
              {formatDate(row.original.invoice_date)}
            </div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'vendor_name',
      header: 'Vendor',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.vendor_name}</div>
          <div className="text-sm text-muted-foreground">{row.original.vendor_code}</div>
        </div>
      ),
    },
    {
      accessorKey: 'references',
      header: 'PO / GRN',
      cell: ({ row }) => (
        <div className="text-sm">
          <div>{row.original.po_number || '-'}</div>
          <div className="text-muted-foreground">{row.original.grn_number || '-'}</div>
        </div>
      ),
    },
    {
      accessorKey: 'total_amount',
      header: 'Amount',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{formatCurrency(row.original.total_amount)}</div>
          <div className="text-xs text-muted-foreground">
            GST: {formatCurrency(row.original.gst_amount)}
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'due_date',
      header: 'Due Date',
      cell: ({ row }) => {
        const isOverdue = row.original.days_until_due < 0;
        return (
          <div className={`flex items-center gap-2 ${isOverdue ? 'text-red-600' : ''}`}>
            {isOverdue && <AlertTriangle className="h-4 w-4" />}
            <div>
              <div className="text-sm">{formatDate(row.original.due_date)}</div>
              <div className="text-xs text-muted-foreground">
                {isOverdue
                  ? `Overdue by ${Math.abs(row.original.days_until_due)} days`
                  : `${row.original.days_until_due} days left`}
              </div>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'match_status',
      header: 'Match Status',
      cell: ({ row }) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${matchStatusColors[row.original.match_status]}`}>
          {row.original.match_status.replace('_', ' ')}
        </span>
      ),
    },
    {
      accessorKey: 'payment_status',
      header: 'Payment',
      cell: ({ row }) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${paymentStatusColors[row.original.payment_status]}`}>
          {row.original.payment_status}
        </span>
      ),
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
      id: 'actions',
      cell: ({ row }) => {
        const invoice = row.original;
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
                <Download className="mr-2 h-4 w-4" />
                Download Invoice
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {invoice.match_status === 'NOT_MATCHED' && (
                <DropdownMenuItem onClick={() => matchMutation.mutate(invoice.id)}>
                  <FileCheck className="mr-2 h-4 w-4" />
                  Initiate 3-Way Match
                </DropdownMenuItem>
              )}
              {invoice.match_status === 'MATCHED' && invoice.status !== 'APPROVED' && (
                <DropdownMenuItem onClick={() => approveMutation.mutate(invoice.id)}>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Approve for Payment
                </DropdownMenuItem>
              )}
              {invoice.match_status === 'MISMATCH' && (
                <DropdownMenuItem className="text-orange-600">
                  <AlertTriangle className="mr-2 h-4 w-4" />
                  Resolve Discrepancy
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
        title="Vendor Invoices"
        description="Manage vendor invoices and payment processing"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <a href="/dashboard/procurement/three-way-match">
                <FileCheck className="mr-2 h-4 w-4" />
                3-Way Match
              </a>
            </Button>
            <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Invoice
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Upload Vendor Invoice</DialogTitle>
                  <DialogDescription>
                    Upload an invoice PDF or image for processing
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Vendor</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select vendor" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="v1">Aqua Systems Pvt Ltd</SelectItem>
                        <SelectItem value="v2">Filter World India</SelectItem>
                        <SelectItem value="v3">Pure Flow Technologies</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Invoice File</label>
                    <div className="border-2 border-dashed rounded-lg p-6 text-center">
                      <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">
                        Drag & drop or click to upload
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        PDF, JPG, PNG (max 10MB)
                      </p>
                      <Input type="file" className="mt-2" accept=".pdf,.jpg,.jpeg,.png" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Invoice Number</label>
                      <Input placeholder="INV-001" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Invoice Date</label>
                      <Input type="date" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Link to PO (Optional)</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select PO" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="po1">PO-2026-001</SelectItem>
                        <SelectItem value="po2">PO-2026-002</SelectItem>
                        <SelectItem value="po3">PO-2026-003</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsUploadDialogOpen(false)}>Cancel</Button>
                  <Button>Upload & Process</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-7">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Invoices</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_invoices || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.pending_review || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Matched</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.matched || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mismatch</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats?.mismatch || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.overdue || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Amount</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">{formatCurrency(stats?.total_pending_amount || 0)}</div>
          </CardContent>
        </Card>
        <Card className="border-red-200 bg-red-50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-800">Overdue Amount</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-red-600">{formatCurrency(stats?.total_overdue_amount || 0)}</div>
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
            <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
            <SelectItem value="MATCHED">Matched</SelectItem>
            <SelectItem value="MISMATCH">Mismatch</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="PAID">Paid</SelectItem>
          </SelectContent>
        </Select>
        <Select value={paymentFilter} onValueChange={setPaymentFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Payment status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Payments</SelectItem>
            <SelectItem value="UNPAID">Unpaid</SelectItem>
            <SelectItem value="PARTIAL">Partial</SelectItem>
            <SelectItem value="PAID">Paid</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="invoice_number"
        searchPlaceholder="Search invoice number..."
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
