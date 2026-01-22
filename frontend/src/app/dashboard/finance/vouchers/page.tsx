'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import {
  MoreHorizontal, Plus, Eye, Receipt, Trash2, CheckCircle,
  XCircle, Send, FileCheck, Loader2, Undo, Ban, ArrowLeftRight,
  CreditCard, Banknote, FileText
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
  DialogTrigger,
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import {
  vouchersApi,
  Voucher,
  VoucherCreate,
  VoucherType,
  VoucherStatus,
  VoucherLineCreate,
  PartyAccountOption,
  PaymentMode,
} from '@/lib/api/vouchers';
import { accountsApi } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';

interface Account {
  id: string;
  code: string;
  name: string;
  type: string;
}

const VOUCHER_TYPE_LABELS: Record<VoucherType, { label: string; icon: React.ReactNode; description: string }> = {
  CONTRA: { label: 'Contra', icon: <ArrowLeftRight className="h-4 w-4" />, description: 'Cash ↔ Bank transfers' },
  PAYMENT: { label: 'Payment', icon: <Banknote className="h-4 w-4" />, description: 'Outward payments to vendors' },
  RECEIPT: { label: 'Receipt', icon: <CreditCard className="h-4 w-4" />, description: 'Inward receipts from customers' },
  RCM_PAYMENT: { label: 'RCM Payment', icon: <Receipt className="h-4 w-4" />, description: 'RCM tax payment to government' },
  JOURNAL: { label: 'Journal', icon: <FileText className="h-4 w-4" />, description: 'General double-entry vouchers' },
  GST_SALE: { label: 'GST Sale', icon: <Receipt className="h-4 w-4" />, description: 'B2B/B2C sales with GST' },
  SALES: { label: 'Sales', icon: <Receipt className="h-4 w-4" />, description: 'Sales invoice voucher' },
  PURCHASE: { label: 'Purchase', icon: <Receipt className="h-4 w-4" />, description: 'Purchase invoice voucher' },
  PURCHASE_RCM: { label: 'Purchase RCM', icon: <Receipt className="h-4 w-4" />, description: 'Purchase under reverse charge' },
  CREDIT_NOTE: { label: 'Credit Note', icon: <Receipt className="h-4 w-4" />, description: 'Credit note against sales' },
  DEBIT_NOTE: { label: 'Debit Note', icon: <Receipt className="h-4 w-4" />, description: 'Debit note against purchases' },
};

const STATUS_COLORS: Record<VoucherStatus, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  REJECTED: 'bg-red-100 text-red-800',
  POSTED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-gray-100 text-gray-500',
};

const emptyLine = (): VoucherLineCreate => ({
  account_id: '',
  description: '',
  debit_amount: 0,
  credit_amount: 0,
});

export default function VouchersPage() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const urlType = searchParams.get('type');

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>(urlType || 'all');

  // Update filter when URL changes
  useEffect(() => {
    if (urlType) {
      setTypeFilter(urlType);
    }
  }, [urlType]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [isReverseDialogOpen, setIsReverseDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedVoucher, setSelectedVoucher] = useState<Voucher | null>(null);
  const [voucherToDelete, setVoucherToDelete] = useState<Voucher | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [cancellationReason, setCancellationReason] = useState('');
  const [reversalReason, setReversalReason] = useState('');
  const [reversalDate, setReversalDate] = useState(new Date().toISOString().split('T')[0]);

  const [formData, setFormData] = useState({
    voucher_type: (urlType || 'CONTRA') as VoucherType,
    voucher_date: new Date().toISOString().split('T')[0],
    narration: '',
    payment_mode: '' as string,
    bank_account_id: '',
    cheque_number: '',
    transaction_reference: '',
    lines: [emptyLine(), emptyLine()],
  });

  // Update form voucher type when URL changes
  useEffect(() => {
    if (urlType && urlType !== 'all') {
      setFormData(prev => ({ ...prev, voucher_type: urlType as VoucherType }));
    }
  }, [urlType]);

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['vouchers', page, pageSize, statusFilter, typeFilter],
    queryFn: () => vouchersApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter === 'all' ? undefined : statusFilter as VoucherStatus,
      voucher_type: typeFilter === 'all' ? undefined : typeFilter as VoucherType,
    }),
  });

  const { data: summaryData } = useQuery({
    queryKey: ['vouchers-summary'],
    queryFn: () => vouchersApi.getSummary(),
  });

  const { data: accountsData } = useQuery({
    queryKey: ['accounts-dropdown'],
    queryFn: () => accountsApi.getDropdown(),
  });

  const { data: partyAccountsData } = useQuery({
    queryKey: ['party-accounts'],
    queryFn: () => vouchersApi.getPartyAccounts(),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: VoucherCreate) => vouchersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Voucher created as draft');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create voucher'),
  });

  const submitMutation = useMutation({
    mutationFn: (id: string) => vouchersApi.submit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Voucher submitted for approval');
      setIsViewOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to submit'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => vouchersApi.approve(id, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Voucher approved and posted');
      setIsViewOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to approve'),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => vouchersApi.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Voucher rejected');
      setIsViewOpen(false);
      setIsRejectDialogOpen(false);
      setRejectionReason('');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to reject'),
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => vouchersApi.cancel(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Voucher cancelled');
      setIsViewOpen(false);
      setIsCancelDialogOpen(false);
      setCancellationReason('');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to cancel'),
  });

  const reverseMutation = useMutation({
    mutationFn: ({ id, date, reason }: { id: string; date: string; reason: string }) =>
      vouchersApi.reverse(id, date, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Reversal voucher created and posted');
      setIsViewOpen(false);
      setIsReverseDialogOpen(false);
      setReversalReason('');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to reverse'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => vouchersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      queryClient.invalidateQueries({ queryKey: ['vouchers-summary'] });
      toast.success('Voucher deleted');
      setIsDeleteDialogOpen(false);
      setVoucherToDelete(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete'),
  });

  const resetForm = () => {
    setFormData({
      voucher_type: 'CONTRA' as VoucherType,
      voucher_date: new Date().toISOString().split('T')[0],
      narration: '',
      payment_mode: '',
      bank_account_id: '',
      cheque_number: '',
      transaction_reference: '',
      lines: [emptyLine(), emptyLine()],
    });
    setIsDialogOpen(false);
  };

  const handleViewVoucher = async (voucher: Voucher) => {
    try {
      const detail = await vouchersApi.getById(voucher.id);
      setSelectedVoucher(detail);
    } catch {
      setSelectedVoucher(voucher);
    }
    setIsViewOpen(true);
  };

  const handleDelete = (voucher: Voucher) => {
    if (voucher.status !== 'DRAFT') {
      toast.error('Only draft vouchers can be deleted');
      return;
    }
    setVoucherToDelete(voucher);
    setIsDeleteDialogOpen(true);
  };

  const addLine = () => {
    setFormData({ ...formData, lines: [...formData.lines, emptyLine()] });
  };

  const removeLine = (index: number) => {
    if (formData.lines.length > 2) {
      const newLines = formData.lines.filter((_, i) => i !== index);
      setFormData({ ...formData, lines: newLines });
    }
  };

  const updateLine = (index: number, field: keyof VoucherLineCreate, value: string | number | boolean) => {
    const newLines = [...formData.lines];
    newLines[index] = { ...newLines[index], [field]: value };
    if (field === 'debit_amount' && value) {
      newLines[index].credit_amount = 0;
    } else if (field === 'credit_amount' && value) {
      newLines[index].debit_amount = 0;
    }
    setFormData({ ...formData, lines: newLines });
  };

  const getTotals = () => {
    const totalDebit = formData.lines.reduce((sum, line) => sum + (line.debit_amount || 0), 0);
    const totalCredit = formData.lines.reduce((sum, line) => sum + (line.credit_amount || 0), 0);
    return { totalDebit, totalCredit, isBalanced: totalDebit === totalCredit && totalDebit > 0 };
  };

  const handleSubmit = () => {
    const { totalDebit, totalCredit } = getTotals();

    if (!formData.voucher_date || !formData.narration.trim()) {
      toast.error('Date and narration are required');
      return;
    }

    if (totalDebit !== totalCredit) {
      toast.error('Debit and credit must be equal');
      return;
    }

    if (totalDebit === 0) {
      toast.error('Voucher amounts cannot be zero');
      return;
    }

    const validLines = formData.lines.filter(l => l.account_id && (l.debit_amount || l.credit_amount));
    if (validLines.length < 2) {
      toast.error('At least 2 account lines are required');
      return;
    }

    const voucherData: VoucherCreate = {
      voucher_type: formData.voucher_type,
      voucher_date: formData.voucher_date,
      narration: formData.narration,
      payment_mode: formData.payment_mode ? (formData.payment_mode as PaymentMode) : undefined,
      bank_account_id: formData.bank_account_id || undefined,
      cheque_number: formData.cheque_number || undefined,
      transaction_reference: formData.transaction_reference || undefined,
      lines: validLines.map(l => ({
        account_id: l.account_id,
        description: l.description || undefined,
        debit_amount: l.debit_amount,
        credit_amount: l.credit_amount,
      })),
    };

    createMutation.mutate(voucherData);
  };

  const columns: ColumnDef<Voucher>[] = [
    {
      accessorKey: 'voucher_number',
      header: 'Voucher #',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          {VOUCHER_TYPE_LABELS[row.original.voucher_type]?.icon}
          <span className="font-medium">{row.original.voucher_number}</span>
        </div>
      ),
    },
    {
      accessorKey: 'voucher_type',
      header: 'Type',
      cell: ({ row }) => (
        <span className="text-sm">
          {VOUCHER_TYPE_LABELS[row.original.voucher_type]?.label || row.original.voucher_type}
        </span>
      ),
    },
    {
      accessorKey: 'voucher_date',
      header: 'Date',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.voucher_date)}
        </span>
      ),
    },
    {
      accessorKey: 'narration',
      header: 'Narration',
      cell: ({ row }) => (
        <span className="text-sm line-clamp-1 max-w-xs">{row.original.narration}</span>
      ),
    },
    {
      accessorKey: 'party_name',
      header: 'Party',
      cell: ({ row }) => (
        <span className="text-sm">{row.original.party_name || '-'}</span>
      ),
    },
    {
      accessorKey: 'total_debit',
      header: 'Amount',
      cell: ({ row }) => (
        <span className="font-medium">
          {formatCurrency(row.original.total_debit)}
        </span>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[row.original.status]}`}>
          {row.original.status.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => handleViewVoucher(row.original)}>
              <Eye className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            {row.original.status === 'DRAFT' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => handleDelete(row.original)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const accounts = Array.isArray(accountsData) ? accountsData : [];
  const bankAccounts = partyAccountsData?.bank_accounts || [];
  const { totalDebit, totalCredit, isBalanced } = getTotals();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vouchers"
        description="Unified voucher system for all accounting transactions"
        actions={
          <div className="flex items-center gap-2">
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {Object.entries(VOUCHER_TYPE_LABELS).map(([type, { label }]) => (
                  <SelectItem key={type} value={type}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="PENDING_APPROVAL">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="POSTED">Posted</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) resetForm(); else setIsDialogOpen(true); }}>
              <DialogTrigger asChild>
                <Button onClick={() => setIsDialogOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  New Voucher
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Voucher</DialogTitle>
                  <DialogDescription>
                    Record a new accounting voucher with debit and credit lines
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Voucher Type *</Label>
                      <Select
                        value={formData.voucher_type}
                        onValueChange={(value) => setFormData({ ...formData, voucher_type: value as VoucherType })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(VOUCHER_TYPE_LABELS).map(([type, { label, description }]) => (
                            <SelectItem key={type} value={type}>
                              <div>
                                <div>{label}</div>
                                <div className="text-xs text-muted-foreground">{description}</div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Voucher Date *</Label>
                      <Input
                        type="date"
                        value={formData.voucher_date}
                        onChange={(e) => setFormData({ ...formData, voucher_date: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Payment Mode</Label>
                      <Select
                        value={formData.payment_mode}
                        onValueChange={(value) => setFormData({ ...formData, payment_mode: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select mode" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="CASH">Cash</SelectItem>
                          <SelectItem value="CHEQUE">Cheque</SelectItem>
                          <SelectItem value="RTGS">RTGS</SelectItem>
                          <SelectItem value="NEFT">NEFT</SelectItem>
                          <SelectItem value="UPI">UPI</SelectItem>
                          <SelectItem value="BANK_TRANSFER">Bank Transfer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {formData.payment_mode && formData.payment_mode !== 'CASH' && (
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>Bank Account</Label>
                        <Select
                          value={formData.bank_account_id}
                          onValueChange={(value) => setFormData({ ...formData, bank_account_id: value })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select bank" />
                          </SelectTrigger>
                          <SelectContent>
                            {bankAccounts.map((acc: PartyAccountOption) => (
                              <SelectItem key={acc.id} value={acc.id}>
                                {acc.full_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      {formData.payment_mode === 'CHEQUE' && (
                        <div className="space-y-2">
                          <Label>Cheque Number</Label>
                          <Input
                            placeholder="Enter cheque number"
                            value={formData.cheque_number}
                            onChange={(e) => setFormData({ ...formData, cheque_number: e.target.value })}
                          />
                        </div>
                      )}
                      <div className="space-y-2">
                        <Label>Transaction Ref</Label>
                        <Input
                          placeholder="UTR / Reference"
                          value={formData.transaction_reference}
                          onChange={(e) => setFormData({ ...formData, transaction_reference: e.target.value })}
                        />
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>Narration *</Label>
                    <Textarea
                      placeholder="Description of this voucher"
                      value={formData.narration}
                      onChange={(e) => setFormData({ ...formData, narration: e.target.value })}
                    />
                  </div>

                  <Separator />

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="text-base font-medium">Voucher Lines</Label>
                      <Button type="button" variant="outline" size="sm" onClick={addLine}>
                        <Plus className="mr-1 h-3 w-3" /> Add Line
                      </Button>
                    </div>

                    <div className="grid gap-2 text-xs font-medium text-muted-foreground px-1" style={{ gridTemplateColumns: '1fr 150px 100px 100px 40px' }}>
                      <div>Account</div>
                      <div>Description</div>
                      <div className="text-right">Debit</div>
                      <div className="text-right">Credit</div>
                      <div></div>
                    </div>

                    {formData.lines.map((line, idx) => (
                      <div key={idx} className="grid gap-2 items-center" style={{ gridTemplateColumns: '1fr 150px 100px 100px 40px' }}>
                        <div className="min-w-0">
                          <Select
                            value={line.account_id || 'select'}
                            onValueChange={(value) => updateLine(idx, 'account_id', value === 'select' ? '' : value)}
                          >
                            <SelectTrigger className="h-9 w-full">
                              <SelectValue placeholder="Select account" className="truncate" />
                            </SelectTrigger>
                            <SelectContent className="max-w-[400px]">
                              <SelectItem value="select" disabled>Select account</SelectItem>
                              {accounts
                                .filter((acc: Account) => acc.id && acc.id.trim() !== '')
                                .map((acc: Account) => (
                                  <SelectItem key={acc.id} value={acc.id}>
                                    <span className="truncate">{acc.code} - {acc.name}</span>
                                  </SelectItem>
                                ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Input
                            className="h-9 w-full"
                            placeholder="Line desc"
                            value={line.description || ''}
                            onChange={(e) => updateLine(idx, 'description', e.target.value)}
                          />
                        </div>
                        <div>
                          <Input
                            className="h-9 w-full text-right"
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder="0.00"
                            value={line.debit_amount || ''}
                            onChange={(e) => updateLine(idx, 'debit_amount', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div>
                          <Input
                            className="h-9 w-full text-right"
                            type="number"
                            min="0"
                            step="0.01"
                            placeholder="0.00"
                            value={line.credit_amount || ''}
                            onChange={(e) => updateLine(idx, 'credit_amount', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="flex justify-center">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => removeLine(idx)}
                            disabled={formData.lines.length <= 2}
                          >
                            <Trash2 className="h-4 w-4 text-muted-foreground" />
                          </Button>
                        </div>
                      </div>
                    ))}

                    <Separator />

                    <div className="grid gap-2 items-center font-medium" style={{ gridTemplateColumns: '1fr 150px 100px 100px 40px' }}>
                      <div className="text-right">Totals:</div>
                      <div></div>
                      <div className={`text-right ${isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(totalDebit)}
                      </div>
                      <div className={`text-right ${isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(totalCredit)}
                      </div>
                      <div></div>
                    </div>

                    {!isBalanced && totalDebit !== totalCredit && (
                      <div className="text-sm text-red-600 text-center">
                        Difference: {formatCurrency(Math.abs(totalDebit - totalCredit))}
                      </div>
                    )}
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={resetForm}>Cancel</Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={createMutation.isPending || !isBalanced}
                  >
                    {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save as Draft
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      {/* Summary Cards */}
      {summaryData && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-xs text-muted-foreground">Total Vouchers</div>
              <div className="text-2xl font-bold">{summaryData.total_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-xs text-muted-foreground">Draft</div>
              <div className="text-2xl font-bold text-gray-600">{summaryData.draft_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-xs text-muted-foreground">Pending Approval</div>
              <div className="text-2xl font-bold text-yellow-600">{summaryData.pending_approval_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-xs text-muted-foreground">Posted</div>
              <div className="text-2xl font-bold text-green-600">{summaryData.posted_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-xs text-muted-foreground">Total Amount</div>
              <div className="text-2xl font-bold">{formatCurrency(summaryData.total_debit)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="voucher_number"
        searchPlaceholder="Search vouchers..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Voucher Detail Sheet */}
      <Sheet open={isViewOpen} onOpenChange={setIsViewOpen}>
        <SheetContent className="w-[700px] sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Receipt className="h-5 w-5" />
              {selectedVoucher?.voucher_number}
            </SheetTitle>
            <SheetDescription>
              {VOUCHER_TYPE_LABELS[selectedVoucher?.voucher_type as VoucherType]?.label || selectedVoucher?.voucher_type}
            </SheetDescription>
          </SheetHeader>
          {selectedVoucher && (
            <div className="mt-6 space-y-6">
              <div className="flex items-center gap-3">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[selectedVoucher.status]}`}>
                  {selectedVoucher.status.replace(/_/g, ' ')}
                </span>
                <span className="text-sm text-muted-foreground">
                  {formatDate(selectedVoucher.voucher_date)}
                </span>
                {selectedVoucher.is_reversed && (
                  <span className="text-xs text-red-600 font-medium">REVERSED</span>
                )}
              </div>

              <Card>
                <CardContent className="pt-4">
                  <div className="text-xs text-muted-foreground">Narration</div>
                  <div className="text-sm mt-1">{selectedVoucher.narration}</div>
                </CardContent>
              </Card>

              {selectedVoucher.party_name && (
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-xs text-muted-foreground">Party</div>
                    <div className="text-sm mt-1">
                      <span className="font-medium">{selectedVoucher.party_name}</span>
                      <span className="text-muted-foreground ml-2">({selectedVoucher.party_type})</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {selectedVoucher.lines && selectedVoucher.lines.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Voucher Lines</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {selectedVoucher.lines.map((line, idx) => (
                        <div key={idx} className="flex justify-between items-center text-sm py-2 border-b last:border-0">
                          <div>
                            <div className="font-medium">{line.account_code} - {line.account_name}</div>
                            {line.description && (
                              <div className="text-xs text-muted-foreground">{line.description}</div>
                            )}
                          </div>
                          <div className="text-right">
                            {line.debit_amount > 0 && (
                              <div className="text-green-600">{formatCurrency(line.debit_amount)} Dr</div>
                            )}
                            {line.credit_amount > 0 && (
                              <div className="text-blue-600">{formatCurrency(line.credit_amount)} Cr</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="grid grid-cols-2 gap-4">
                <Card className="bg-green-50">
                  <CardContent className="pt-4">
                    <div className="text-xs text-green-600">Total Debit</div>
                    <div className="text-xl font-bold text-green-700">
                      {formatCurrency(selectedVoucher.total_debit)}
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-blue-50">
                  <CardContent className="pt-4">
                    <div className="text-xs text-blue-600">Total Credit</div>
                    <div className="text-xl font-bold text-blue-700">
                      {formatCurrency(selectedVoucher.total_credit)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {selectedVoucher.rejection_reason && (
                <Card className="bg-red-50">
                  <CardContent className="pt-4">
                    <div className="text-xs text-red-600">Rejection Reason</div>
                    <div className="text-sm text-red-700">{selectedVoucher.rejection_reason}</div>
                  </CardContent>
                </Card>
              )}

              {selectedVoucher.creator_name && (
                <div className="text-xs text-muted-foreground">
                  Created by: {selectedVoucher.creator_name}
                </div>
              )}

              {/* Workflow Actions */}
              <Separator />
              <div className="flex flex-wrap gap-2">
                {selectedVoucher.status === 'DRAFT' && (
                  <Button
                    onClick={() => submitMutation.mutate(selectedVoucher.id)}
                    disabled={submitMutation.isPending}
                  >
                    {submitMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                    Submit for Approval
                  </Button>
                )}

                {selectedVoucher.status === 'PENDING_APPROVAL' && (
                  <>
                    <Button
                      onClick={() => approveMutation.mutate(selectedVoucher.id)}
                      disabled={approveMutation.isPending}
                    >
                      {approveMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle className="mr-2 h-4 w-4" />}
                      Approve & Post
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => setIsRejectDialogOpen(true)}
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </>
                )}

                {(selectedVoucher.status === 'DRAFT' || selectedVoucher.status === 'REJECTED') && (
                  <Button
                    variant="outline"
                    onClick={() => setIsCancelDialogOpen(true)}
                  >
                    <Ban className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                )}

                {selectedVoucher.status === 'POSTED' && !selectedVoucher.is_reversed && (
                  <Button
                    variant="outline"
                    onClick={() => setIsReverseDialogOpen(true)}
                  >
                    <Undo className="mr-2 h-4 w-4" />
                    Reverse
                  </Button>
                )}

                {selectedVoucher.status === 'POSTED' && (
                  <div className="text-sm text-green-600 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    Posted to General Ledger
                  </div>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Rejection Dialog */}
      <AlertDialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reject Voucher</AlertDialogTitle>
            <AlertDialogDescription>
              Please provide a reason for rejecting this voucher.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Enter rejection reason..."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => selectedVoucher && rejectMutation.mutate({ id: selectedVoucher.id, reason: rejectionReason })}
              disabled={!rejectionReason.trim() || rejectMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {rejectMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Reject Voucher
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Cancel Dialog */}
      <AlertDialog open={isCancelDialogOpen} onOpenChange={setIsCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Voucher</AlertDialogTitle>
            <AlertDialogDescription>
              Please provide a reason for cancelling this voucher.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Enter cancellation reason..."
              value={cancellationReason}
              onChange={(e) => setCancellationReason(e.target.value)}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Back</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => selectedVoucher && cancelMutation.mutate({ id: selectedVoucher.id, reason: cancellationReason })}
              disabled={!cancellationReason.trim() || cancelMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {cancelMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Cancel Voucher
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reverse Dialog */}
      <AlertDialog open={isReverseDialogOpen} onOpenChange={setIsReverseDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reverse Voucher</AlertDialogTitle>
            <AlertDialogDescription>
              This will create a reversal entry to undo this voucher.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label>Reversal Date</Label>
              <Input
                type="date"
                value={reversalDate}
                onChange={(e) => setReversalDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Reason</Label>
              <Textarea
                placeholder="Enter reversal reason..."
                value={reversalReason}
                onChange={(e) => setReversalReason(e.target.value)}
              />
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => selectedVoucher && reverseMutation.mutate({
                id: selectedVoucher.id,
                date: reversalDate,
                reason: reversalReason
              })}
              disabled={!reversalReason.trim() || !reversalDate || reverseMutation.isPending}
            >
              {reverseMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Reversal
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Voucher</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete voucher{' '}
              <span className="font-medium">{voucherToDelete?.voucher_number}</span>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => voucherToDelete && deleteMutation.mutate(voucherToDelete.id)}
              disabled={deleteMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete Voucher
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
