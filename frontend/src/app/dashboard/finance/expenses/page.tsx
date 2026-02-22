'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import {
  MoreHorizontal, Plus, Eye, Trash2, CheckCircle, XCircle, Send,
  BookOpen, Loader2, CreditCard, Receipt, FileText,
  TrendingUp, AlertTriangle, Clock, Settings
} from 'lucide-react';
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
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { expensesApi } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';

interface ExpenseCategory {
  id: string;
  code: string;
  name: string;
  description?: string;
  gl_account_id?: string;
  gl_account_name?: string;
  gl_account_code?: string;
  requires_receipt: boolean;
  max_amount_without_approval: number;
  is_active: boolean;
  voucher_count: number;
  created_at: string;
  updated_at: string;
}

interface ExpenseVoucher {
  id: string;
  voucher_number: string;
  voucher_date: string;
  financial_year: string;
  period?: string;
  expense_category_id: string;
  category_code?: string;
  category_name?: string;
  amount: number;
  gst_amount: number;
  tds_amount: number;
  net_amount: number;
  vendor_name?: string;
  cost_center_name?: string;
  narration: string;
  purpose?: string;
  payment_mode: string;
  status: string;
  approval_level?: string;
  rejection_reason?: string;
  journal_entry_id?: string;
  journal_entry_number?: string;
  payment_reference?: string;
  attachments?: { files?: Array<{ name: string; url: string }> };
  created_by_name?: string;
  approved_by_name?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
}

interface ExpenseDashboard {
  total_vouchers: number;
  draft_count: number;
  pending_approval_count: number;
  approved_count: number;
  posted_count: number;
  paid_count: number;
  rejected_count: number;
  total_amount_this_month: number;
  total_amount_this_year: number;
  pending_approval_amount: number;
  category_wise_spending: Array<{ category: string; amount: number }>;
  cost_center_wise_spending: Array<{ cost_center: string; amount: number }>;
  monthly_trend: Array<{ month: string; amount: number }>;
}

export default function ExpensesPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('vouchers');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isPayDialogOpen, setIsPayDialogOpen] = useState(false);
  const [isCategoryDialogOpen, setIsCategoryDialogOpen] = useState(false);

  // Selected items
  const [selectedVoucher, setSelectedVoucher] = useState<ExpenseVoucher | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<ExpenseCategory | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [paymentReference, setPaymentReference] = useState('');

  // Form data
  const [voucherForm, setVoucherForm] = useState({
    voucher_date: new Date().toISOString().split('T')[0],
    expense_category_id: '',
    amount: '',
    gst_amount: '0',
    tds_amount: '0',
    narration: '',
    purpose: '',
    payment_mode: 'BANK',
    cost_center_id: '',
  });

  const [categoryForm, setCategoryForm] = useState({
    code: '',
    name: '',
    description: '',
    gl_account_id: '',
    requires_receipt: true,
    max_amount_without_approval: '0',
  });

  // Queries
  const { data: dashboardData } = useQuery({
    queryKey: ['expense-dashboard'],
    queryFn: () => expensesApi.getDashboard(),
    enabled: activeTab === 'dashboard',
  });

  const { data: vouchersData, isLoading: vouchersLoading } = useQuery({
    queryKey: ['expense-vouchers', page, pageSize, statusFilter],
    queryFn: () => expensesApi.listVouchers({
      page: page + 1,
      size: pageSize,
      status: statusFilter === 'all' ? undefined : statusFilter
    }),
    enabled: activeTab === 'vouchers',
  });

  const { data: categoriesData, isLoading: categoriesLoading } = useQuery({
    queryKey: ['expense-categories'],
    queryFn: () => expensesApi.listCategories(),
    enabled: activeTab === 'categories',
  });

  const { data: categoryDropdown } = useQuery({
    queryKey: ['expense-categories-dropdown'],
    queryFn: () => expensesApi.getCategoryDropdown(),
  });

  // Mutations
  const createVoucherMutation = useMutation({
    mutationFn: expensesApi.createVoucher,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['expense-dashboard'] });
      toast.success('Expense voucher created');
      resetVoucherForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create voucher'),
  });

  const submitMutation = useMutation({
    mutationFn: (id: string) => expensesApi.submitVoucher(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['expense-dashboard'] });
      toast.success('Voucher submitted for approval');
      setIsViewOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to submit'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => expensesApi.approveVoucher(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['expense-dashboard'] });
      toast.success('Voucher approved');
      setIsViewOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to approve'),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      expensesApi.rejectVoucher(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['expense-dashboard'] });
      toast.success('Voucher rejected');
      setIsViewOpen(false);
      setIsRejectDialogOpen(false);
      setRejectionReason('');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to reject'),
  });

  const postMutation = useMutation({
    mutationFn: (id: string) => expensesApi.postVoucher(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['expense-dashboard'] });
      toast.success('Voucher posted to GL');
      setIsViewOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to post'),
  });

  const payMutation = useMutation({
    mutationFn: ({ id, reference }: { id: string; reference: string }) =>
      expensesApi.payVoucher(id, reference),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['expense-dashboard'] });
      toast.success('Voucher marked as paid');
      setIsViewOpen(false);
      setIsPayDialogOpen(false);
      setPaymentReference('');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to mark as paid'),
  });

  const deleteVoucherMutation = useMutation({
    mutationFn: (id: string) => expensesApi.deleteVoucher(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-vouchers'] });
      toast.success('Voucher deleted');
      setIsDeleteDialogOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete'),
  });

  const createCategoryMutation = useMutation({
    mutationFn: expensesApi.createCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-categories'] });
      queryClient.invalidateQueries({ queryKey: ['expense-categories-dropdown'] });
      toast.success('Category created');
      resetCategoryForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create category'),
  });

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ExpenseCategory> }) =>
      expensesApi.updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-categories'] });
      toast.success('Category updated');
      resetCategoryForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to update category'),
  });

  // Form handlers
  const resetVoucherForm = () => {
    setVoucherForm({
      voucher_date: new Date().toISOString().split('T')[0],
      expense_category_id: '',
      amount: '',
      gst_amount: '0',
      tds_amount: '0',
      narration: '',
      purpose: '',
      payment_mode: 'BANK',
      cost_center_id: '',
    });
    setIsCreateDialogOpen(false);
  };

  const resetCategoryForm = () => {
    setCategoryForm({
      code: '',
      name: '',
      description: '',
      gl_account_id: '',
      requires_receipt: true,
      max_amount_without_approval: '0',
    });
    setSelectedCategory(null);
    setIsCategoryDialogOpen(false);
  };

  const handleCreateVoucher = () => {
    if (!voucherForm.expense_category_id || !voucherForm.amount || !voucherForm.narration) {
      toast.error('Please fill in all required fields');
      return;
    }
    createVoucherMutation.mutate({
      voucher_date: voucherForm.voucher_date,
      expense_category_id: voucherForm.expense_category_id,
      amount: parseFloat(voucherForm.amount),
      gst_amount: parseFloat(voucherForm.gst_amount || '0'),
      tds_amount: parseFloat(voucherForm.tds_amount || '0'),
      narration: voucherForm.narration,
      purpose: voucherForm.purpose,
      payment_mode: voucherForm.payment_mode,
    });
  };

  const handleCreateCategory = () => {
    if (!categoryForm.code || !categoryForm.name) {
      toast.error('Please fill in code and name');
      return;
    }
    if (selectedCategory) {
      updateCategoryMutation.mutate({
        id: selectedCategory.id,
        data: {
          name: categoryForm.name,
          description: categoryForm.description,
          requires_receipt: categoryForm.requires_receipt,
          max_amount_without_approval: parseFloat(categoryForm.max_amount_without_approval || '0'),
        },
      });
    } else {
      createCategoryMutation.mutate({
        code: categoryForm.code,
        name: categoryForm.name,
        description: categoryForm.description,
        requires_receipt: categoryForm.requires_receipt,
        max_amount_without_approval: parseFloat(categoryForm.max_amount_without_approval || '0'),
      });
    }
  };

  const handleEditCategory = (category: ExpenseCategory) => {
    setSelectedCategory(category);
    setCategoryForm({
      code: category.code,
      name: category.name,
      description: category.description || '',
      gl_account_id: category.gl_account_id || '',
      requires_receipt: category.requires_receipt,
      max_amount_without_approval: category.max_amount_without_approval.toString(),
    });
    setIsCategoryDialogOpen(true);
  };

  // Voucher columns
  const voucherColumns: ColumnDef<ExpenseVoucher>[] = [
    {
      accessorKey: 'voucher_number',
      header: 'Voucher #',
      cell: ({ row }) => (
        <span className="font-medium text-primary">{row.original.voucher_number}</span>
      ),
    },
    {
      accessorKey: 'voucher_date',
      header: 'Date',
      cell: ({ row }) => formatDate(row.original.voucher_date),
    },
    {
      accessorKey: 'category_name',
      header: 'Category',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.category_name}</div>
          <div className="text-xs text-muted-foreground">{row.original.category_code}</div>
        </div>
      ),
    },
    {
      accessorKey: 'narration',
      header: 'Description',
      cell: ({ row }) => (
        <div className="max-w-[200px] truncate">{row.original.narration}</div>
      ),
    },
    {
      accessorKey: 'net_amount',
      header: 'Net Amount',
      cell: ({ row }) => formatCurrency(row.original.net_amount),
    },
    {
      accessorKey: 'payment_mode',
      header: 'Payment',
      cell: ({ row }) => (
        <span className="text-xs bg-muted px-2 py-1 rounded">
          {row.original.payment_mode}
        </span>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge status={row.original.status} />
      ),
    },
    {
      id: 'journal_entry',
      header: 'JV #',
      cell: ({ row }) => {
        const jeNumber = row.original.journal_entry_number;
        if (!jeNumber) return <span className="text-muted-foreground">-</span>;
        return (
          <a
            href="/dashboard/finance/journal-entries"
            className="font-mono text-xs text-primary hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            {jeNumber}
          </a>
        );
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => {
              setSelectedVoucher(row.original);
              setIsViewOpen(true);
            }}>
              <Eye className="mr-2 h-4 w-4" /> View Details
            </DropdownMenuItem>
            {row.original.status === 'DRAFT' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => submitMutation.mutate(row.original.id)}>
                  <Send className="mr-2 h-4 w-4" /> Submit for Approval
                </DropdownMenuItem>
              </>
            )}
            {row.original.status === 'PENDING_APPROVAL' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => approveMutation.mutate(row.original.id)}>
                  <CheckCircle className="mr-2 h-4 w-4 text-green-600" /> Approve
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => {
                  setSelectedVoucher(row.original);
                  setIsRejectDialogOpen(true);
                }}>
                  <XCircle className="mr-2 h-4 w-4 text-red-600" /> Reject
                </DropdownMenuItem>
              </>
            )}
            {row.original.status === 'DRAFT' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={() => {
                    setSelectedVoucher(row.original);
                    setIsDeleteDialogOpen(true);
                  }}
                >
                  <Trash2 className="mr-2 h-4 w-4" /> Delete
                </DropdownMenuItem>
              </>
            )}
            {row.original.status === 'APPROVED' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => postMutation.mutate(row.original.id)}>
                  <BookOpen className="mr-2 h-4 w-4" /> Post to GL
                </DropdownMenuItem>
              </>
            )}
            {row.original.status === 'POSTED' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => {
                  setSelectedVoucher(row.original);
                  setIsPayDialogOpen(true);
                }}>
                  <CreditCard className="mr-2 h-4 w-4" /> Mark as Paid
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  // Category columns
  const categoryColumns: ColumnDef<ExpenseCategory>[] = [
    {
      accessorKey: 'code',
      header: 'Code',
      cell: ({ row }) => (
        <span className="font-mono font-medium">{row.original.code}</span>
      ),
    },
    {
      accessorKey: 'name',
      header: 'Name',
    },
    {
      accessorKey: 'gl_account_name',
      header: 'GL Account',
      cell: ({ row }) => row.original.gl_account_name || '-',
    },
    {
      accessorKey: 'requires_receipt',
      header: 'Receipt Required',
      cell: ({ row }) => row.original.requires_receipt ? 'Yes' : 'No',
    },
    {
      accessorKey: 'max_amount_without_approval',
      header: 'Auto-Approve Limit',
      cell: ({ row }) => formatCurrency(row.original.max_amount_without_approval),
    },
    {
      accessorKey: 'voucher_count',
      header: 'Vouchers',
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <Button variant="ghost" size="icon" onClick={() => handleEditCategory(row.original)}>
          <Settings className="h-4 w-4" />
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Expense Management"
        description="Manage expense vouchers, categories, and approvals"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="vouchers">Vouchers</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {dashboardData && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">This Month</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(dashboardData.total_amount_this_month)}
                    </div>
                    <p className="text-xs text-muted-foreground">Total expenses this month</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">This Year</CardTitle>
                    <Receipt className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(dashboardData.total_amount_this_year)}
                    </div>
                    <p className="text-xs text-muted-foreground">Total expenses YTD</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
                    <Clock className="h-4 w-4 text-yellow-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {dashboardData.pending_approval_count}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatCurrency(dashboardData.pending_approval_amount)} pending
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">Rejected</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.rejected_count}</div>
                    <p className="text-xs text-muted-foreground">Need attention</p>
                  </CardContent>
                </Card>
              </div>

              {/* Status Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Voucher Status Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                    <div className="text-center p-3 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{dashboardData.total_vouchers}</div>
                      <div className="text-xs text-muted-foreground">Total</div>
                    </div>
                    <div className="text-center p-3 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold">{dashboardData.draft_count}</div>
                      <div className="text-xs text-muted-foreground">Draft</div>
                    </div>
                    <div className="text-center p-3 bg-yellow-50 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-700">
                        {dashboardData.pending_approval_count}
                      </div>
                      <div className="text-xs text-muted-foreground">Pending</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-700">
                        {dashboardData.approved_count}
                      </div>
                      <div className="text-xs text-muted-foreground">Approved</div>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-700">
                        {dashboardData.posted_count}
                      </div>
                      <div className="text-xs text-muted-foreground">Posted</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-700">
                        {dashboardData.paid_count}
                      </div>
                      <div className="text-xs text-muted-foreground">Paid</div>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-700">
                        {dashboardData.rejected_count}
                      </div>
                      <div className="text-xs text-muted-foreground">Rejected</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Category-wise and Monthly Trend */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Category-wise Spending</CardTitle>
                    <CardDescription>This financial year</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {dashboardData.category_wise_spending.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center">
                          <span className="text-sm">{item.category}</span>
                          <span className="font-medium">{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                      {dashboardData.category_wise_spending.length === 0 && (
                        <p className="text-sm text-muted-foreground">No data available</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Monthly Trend</CardTitle>
                    <CardDescription>Last 6 months</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {dashboardData.monthly_trend.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center">
                          <span className="text-sm">{item.month}</span>
                          <span className="font-medium">{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Vouchers Tab */}
        <TabsContent value="vouchers" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="POSTED">Posted</SelectItem>
                  <SelectItem value="PAID">Paid</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> New Expense
            </Button>
          </div>

          <DataTable
            columns={voucherColumns}
            data={vouchersData?.items || []}
            isLoading={vouchersLoading}
            manualPagination
            pageIndex={page}
            pageSize={pageSize}
            pageCount={vouchersData?.pages || 0}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setIsCategoryDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> New Category
            </Button>
          </div>

          <DataTable
            columns={categoryColumns}
            data={categoriesData?.items || []}
            isLoading={categoriesLoading}
          />
        </TabsContent>
      </Tabs>

      {/* Create Voucher Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create Expense Voucher</DialogTitle>
            <DialogDescription>
              Create a new expense voucher. It will be saved as draft.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Date *</Label>
                <Input
                  type="date"
                  value={voucherForm.voucher_date}
                  onChange={(e) => setVoucherForm({ ...voucherForm, voucher_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select
                  value={voucherForm.expense_category_id}
                  onValueChange={(v) => setVoucherForm({ ...voucherForm, expense_category_id: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categoryDropdown?.map((cat: { id: string; name: string; code: string }) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.code} - {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Amount *</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={voucherForm.amount}
                  onChange={(e) => setVoucherForm({ ...voucherForm, amount: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>GST Amount</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={voucherForm.gst_amount}
                  onChange={(e) => setVoucherForm({ ...voucherForm, gst_amount: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>TDS Amount</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={voucherForm.tds_amount}
                  onChange={(e) => setVoucherForm({ ...voucherForm, tds_amount: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Payment Mode</Label>
              <Select
                value={voucherForm.payment_mode}
                onValueChange={(v) => setVoucherForm({ ...voucherForm, payment_mode: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CASH">Cash</SelectItem>
                  <SelectItem value="BANK">Bank Transfer</SelectItem>
                  <SelectItem value="PETTY_CASH">Petty Cash</SelectItem>
                  <SelectItem value="CREDIT_CARD">Credit Card</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Description *</Label>
              <Textarea
                placeholder="Enter expense description..."
                value={voucherForm.narration}
                onChange={(e) => setVoucherForm({ ...voucherForm, narration: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Business Purpose</Label>
              <Textarea
                placeholder="Enter business purpose/justification..."
                value={voucherForm.purpose}
                onChange={(e) => setVoucherForm({ ...voucherForm, purpose: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetVoucherForm}>Cancel</Button>
            <Button
              onClick={handleCreateVoucher}
              disabled={createVoucherMutation.isPending}
            >
              {createVoucherMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Voucher
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Voucher Sheet */}
      <Sheet open={isViewOpen} onOpenChange={setIsViewOpen}>
        <SheetContent className="w-[500px] sm:w-[600px]">
          <SheetHeader>
            <SheetTitle>Expense Voucher Details</SheetTitle>
            <SheetDescription>{selectedVoucher?.voucher_number}</SheetDescription>
          </SheetHeader>
          {selectedVoucher && (
            <div className="mt-6 space-y-6">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <StatusBadge status={selectedVoucher.status} />
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Net Amount</p>
                  <p className="text-2xl font-bold">{formatCurrency(selectedVoucher.net_amount)}</p>
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Date</p>
                  <p className="font-medium">{formatDate(selectedVoucher.voucher_date)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Category</p>
                  <p className="font-medium">{selectedVoucher.category_name}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Amount</p>
                  <p className="font-medium">{formatCurrency(selectedVoucher.amount)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">GST</p>
                  <p className="font-medium">{formatCurrency(selectedVoucher.gst_amount)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">TDS</p>
                  <p className="font-medium">{formatCurrency(selectedVoucher.tds_amount)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Payment Mode</p>
                  <p className="font-medium">{selectedVoucher.payment_mode}</p>
                </div>
              </div>

              <div className="text-sm">
                <p className="text-muted-foreground">Description</p>
                <p className="font-medium">{selectedVoucher.narration}</p>
              </div>

              {selectedVoucher.purpose && (
                <div className="text-sm">
                  <p className="text-muted-foreground">Purpose</p>
                  <p className="font-medium">{selectedVoucher.purpose}</p>
                </div>
              )}

              {selectedVoucher.rejection_reason && (
                <div className="text-sm bg-red-50 p-3 rounded-lg">
                  <p className="text-red-600 font-medium">Rejection Reason</p>
                  <p className="text-red-700">{selectedVoucher.rejection_reason}</p>
                </div>
              )}

              <Separator />

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Created By</p>
                  <p className="font-medium">{selectedVoucher.created_by_name || '-'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created At</p>
                  <p className="font-medium">{formatDate(selectedVoucher.created_at)}</p>
                </div>
                {selectedVoucher.approved_by_name && (
                  <>
                    <div>
                      <p className="text-muted-foreground">Approved By</p>
                      <p className="font-medium">{selectedVoucher.approved_by_name}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Approved At</p>
                      <p className="font-medium">
                        {selectedVoucher.approved_at ? formatDate(selectedVoucher.approved_at) : '-'}
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Action buttons based on status */}
              <div className="flex gap-2 pt-4">
                {selectedVoucher.status === 'DRAFT' && (
                  <Button
                    className="flex-1"
                    onClick={() => submitMutation.mutate(selectedVoucher.id)}
                    disabled={submitMutation.isPending}
                  >
                    {submitMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Send className="mr-2 h-4 w-4" /> Submit for Approval
                  </Button>
                )}
                {selectedVoucher.status === 'PENDING_APPROVAL' && (
                  <>
                    <Button
                      className="flex-1"
                      onClick={() => approveMutation.mutate(selectedVoucher.id)}
                      disabled={approveMutation.isPending}
                    >
                      {approveMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      <CheckCircle className="mr-2 h-4 w-4" /> Approve
                    </Button>
                    <Button
                      variant="destructive"
                      className="flex-1"
                      onClick={() => setIsRejectDialogOpen(true)}
                    >
                      <XCircle className="mr-2 h-4 w-4" /> Reject
                    </Button>
                  </>
                )}
                {selectedVoucher.status === 'APPROVED' && (
                  <Button
                    className="flex-1"
                    onClick={() => postMutation.mutate(selectedVoucher.id)}
                    disabled={postMutation.isPending}
                  >
                    {postMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <BookOpen className="mr-2 h-4 w-4" /> Post to GL
                  </Button>
                )}
                {selectedVoucher.status === 'POSTED' && (
                  <Button
                    className="flex-1"
                    onClick={() => setIsPayDialogOpen(true)}
                  >
                    <CreditCard className="mr-2 h-4 w-4" /> Mark as Paid
                  </Button>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Reject Dialog */}
      <AlertDialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reject Expense Voucher</AlertDialogTitle>
            <AlertDialogDescription>
              Please provide a reason for rejecting this expense voucher.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Textarea
            placeholder="Enter rejection reason (min 10 characters)..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
          />
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setIsRejectDialogOpen(false);
              setRejectionReason('');
            }}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={rejectionReason.length < 10 || rejectMutation.isPending}
              onClick={() => {
                if (selectedVoucher) {
                  rejectMutation.mutate({ id: selectedVoucher.id, reason: rejectionReason });
                }
              }}
            >
              {rejectMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Reject
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Expense Voucher</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this expense voucher? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteVoucherMutation.isPending}
              onClick={() => {
                if (selectedVoucher) {
                  deleteVoucherMutation.mutate(selectedVoucher.id);
                }
              }}
            >
              {deleteVoucherMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Pay Dialog */}
      <AlertDialog open={isPayDialogOpen} onOpenChange={setIsPayDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Mark as Paid</AlertDialogTitle>
            <AlertDialogDescription>
              Enter the payment reference (cheque number, UTR, etc.)
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Input
            placeholder="Payment reference..."
            value={paymentReference}
            onChange={(e) => setPaymentReference(e.target.value)}
          />
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setIsPayDialogOpen(false);
              setPaymentReference('');
            }}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={!paymentReference || payMutation.isPending}
              onClick={() => {
                if (selectedVoucher) {
                  payMutation.mutate({ id: selectedVoucher.id, reference: paymentReference });
                }
              }}
            >
              {payMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Confirm Payment
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Category Dialog */}
      <Dialog open={isCategoryDialogOpen} onOpenChange={(open) => {
        if (!open) resetCategoryForm();
        setIsCategoryDialogOpen(open);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedCategory ? 'Edit Category' : 'Create Category'}
            </DialogTitle>
            <DialogDescription>
              {selectedCategory ? 'Update expense category details' : 'Create a new expense category'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Code *</Label>
              <Input
                placeholder="e.g., TRAVEL, OFFICE"
                value={categoryForm.code}
                onChange={(e) => setCategoryForm({ ...categoryForm, code: e.target.value.toUpperCase() })}
                disabled={!!selectedCategory}
              />
            </div>
            <div className="space-y-2">
              <Label>Name *</Label>
              <Input
                placeholder="Category name"
                value={categoryForm.name}
                onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Category description..."
                value={categoryForm.description}
                onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="requires_receipt"
                checked={categoryForm.requires_receipt}
                onChange={(e) => setCategoryForm({ ...categoryForm, requires_receipt: e.target.checked })}
                className="h-4 w-4"
              />
              <Label htmlFor="requires_receipt">Requires Receipt/Invoice</Label>
            </div>
            <div className="space-y-2">
              <Label>Auto-Approve Limit</Label>
              <Input
                type="number"
                placeholder="0"
                value={categoryForm.max_amount_without_approval}
                onChange={(e) => setCategoryForm({
                  ...categoryForm,
                  max_amount_without_approval: e.target.value
                })}
              />
              <p className="text-xs text-muted-foreground">
                Expenses below this amount will be auto-approved
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetCategoryForm}>Cancel</Button>
            <Button
              onClick={handleCreateCategory}
              disabled={createCategoryMutation.isPending || updateCategoryMutation.isPending}
            >
              {(createCategoryMutation.isPending || updateCategoryMutation.isPending) &&
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              }
              {selectedCategory ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
