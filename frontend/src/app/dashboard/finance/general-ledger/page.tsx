'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { BookText, Download, Filter, RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import apiClient from '@/lib/api/client';
import { formatDate, formatCurrency } from '@/lib/utils';

interface LedgerEntry {
  id: string;
  entry_date: string;
  entry_number: string;
  narration: string;
  debit: number;
  credit: number;
  running_balance: number;
  reference?: string;
}

interface Account {
  id: string;
  account_code: string;
  account_name: string;
  account_type: string;
}

interface RecalculateResult {
  message: string;
  accounts_processed: number;
  discrepancies_found: number;
  accounts_fixed: number;
  details?: Array<{
    account_id: string;
    account_code: string;
    account_name: string;
    old_balance: number;
    new_balance: number;
    discrepancy: number;
    status: string;
  }>;
}

const ledgerApi = {
  getAccounts: async () => {
    try {
      const { data } = await apiClient.get('/accounting/accounts');
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getLedger: async (accountId: string, params?: { page?: number; size?: number; from_date?: string; to_date?: string }) => {
    try {
      // Backend expects skip/limit, not page/size
      const backendParams: Record<string, unknown> = {};
      if (params?.size) backendParams.limit = params.size;
      if (params?.page && params?.size) backendParams.skip = (params.page - 1) * params.size;
      if (params?.from_date) backendParams.start_date = params.from_date;
      if (params?.to_date) backendParams.end_date = params.to_date;
      const { data } = await apiClient.get(`/accounting/ledger/${accountId}`, { params: backendParams });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0, opening_balance: 0, closing_balance: 0 };
    }
  },
  recalculateBalances: async (accountId?: string): Promise<RecalculateResult> => {
    const params = accountId ? { account_id: accountId } : {};
    const { data } = await apiClient.post('/accounting/recalculate-account-balances', null, { params });
    return data;
  },
};

const columns: ColumnDef<LedgerEntry>[] = [
  {
    accessorKey: 'entry_date',
    header: 'Date',
    cell: ({ row }) => (
      <span className="text-sm">{formatDate(row.original.entry_date)}</span>
    ),
  },
  {
    accessorKey: 'entry_number',
    header: 'Voucher #',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.entry_number}</span>
    ),
  },
  {
    accessorKey: 'narration',
    header: 'Particulars',
    cell: ({ row }) => (
      <div>
        <div className="text-sm">{row.original.narration}</div>
        {row.original.reference && (
          <div className="text-xs text-muted-foreground">Ref: {row.original.reference}</div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'debit',
    header: 'Debit',
    cell: ({ row }) => (
      <span className={`font-medium ${row.original.debit > 0 ? 'text-green-600' : 'text-muted-foreground'}`}>
        {row.original.debit > 0 ? formatCurrency(row.original.debit) : '-'}
      </span>
    ),
  },
  {
    accessorKey: 'credit',
    header: 'Credit',
    cell: ({ row }) => (
      <span className={`font-medium ${row.original.credit > 0 ? 'text-red-600' : 'text-muted-foreground'}`}>
        {row.original.credit > 0 ? formatCurrency(row.original.credit) : '-'}
      </span>
    ),
  },
  {
    accessorKey: 'running_balance',
    header: 'Balance',
    cell: ({ row }) => (
      <span className={`font-medium ${row.original.running_balance < 0 ? 'text-red-600' : ''}`}>
        {formatCurrency(Math.abs(row.original.running_balance))}
        <span className="text-xs ml-1 text-muted-foreground">
          {row.original.running_balance >= 0 ? 'Dr' : 'Cr'}
        </span>
      </span>
    ),
  },
];

export default function GeneralLedgerPage() {
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [recalculateDialogOpen, setRecalculateDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: accountsData } = useQuery({
    queryKey: ['accounts-list'],
    queryFn: ledgerApi.getAccounts,
  });
  const accounts = accountsData?.items || [];

  const handleExport = async () => {
    if (!selectedAccount) {
      toast.error('Please select an account first');
      return;
    }
    try {
      const allData = await ledgerApi.getLedger(selectedAccount, { page: 1, size: 500 });
      if (!allData?.items?.length) {
        toast.error('No ledger entries found for this account. If this is a group account, select a child account instead.');
        return;
      }
      const selectedAcc = accounts.find((a: Account) => a.id === selectedAccount);
      const accLabel = selectedAcc ? `${selectedAcc.account_code} ${selectedAcc.account_name}` : selectedAccount;

      const headers = ['Date', 'Voucher #', 'Particulars', 'Debit', 'Credit', 'Balance'];
      const csvRows = [headers.join(',')];

      // Opening balance row
      if (allData.opening_balance !== undefined) {
        const ob = allData.opening_balance;
        csvRows.push(`,,Opening Balance,,,${Math.abs(ob).toFixed(2)} ${ob >= 0 ? 'Dr' : 'Cr'}`);
      }

      for (const item of allData.items) {
        const row = [
          item.entry_date,
          `"${(item.entry_number || '').replace(/"/g, '""')}"`,
          `"${(item.narration || '').replace(/"/g, '""')}"`,
          item.debit ? item.debit.toFixed(2) : '',
          item.credit ? item.credit.toFixed(2) : '',
          `${Math.abs(item.running_balance).toFixed(2)} ${item.running_balance >= 0 ? 'Dr' : 'Cr'}`,
        ];
        csvRows.push(row.join(','));
      }

      // Totals row
      csvRows.push(`,,Totals,${allData.total_debit?.toFixed(2) || '0.00'},${allData.total_credit?.toFixed(2) || '0.00'},`);
      // Closing balance row
      if (allData.closing_balance !== undefined) {
        const cb = allData.closing_balance;
        csvRows.push(`,,Closing Balance,,,${Math.abs(cb).toFixed(2)} ${cb >= 0 ? 'Dr' : 'Cr'}`);
      }

      const blob = new Blob(['\uFEFF' + csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `Ledger_${accLabel.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 100);
      toast.success('Ledger exported successfully');
    } catch {
      toast.error('Failed to export ledger');
    }
  };

  const { data: ledgerData, isLoading } = useQuery({
    queryKey: ['ledger', selectedAccount, page, pageSize],
    queryFn: () => ledgerApi.getLedger(selectedAccount, { page: page + 1, size: pageSize }),
    enabled: !!selectedAccount,
  });

  // Mutation for recalculating balances
  const recalculateMutation = useMutation({
    mutationFn: (accountId?: string) => ledgerApi.recalculateBalances(accountId),
    onSuccess: (data) => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['ledger'] });
      queryClient.invalidateQueries({ queryKey: ['accounts-list'] });

      if (data.discrepancies_found > 0) {
        toast.success(
          `Balances Recalculated: Fixed ${data.accounts_fixed} accounts with discrepancies out of ${data.accounts_processed} processed.`
        );
      } else {
        toast.success(
          `Balances Verified: All ${data.accounts_processed} accounts have correct balances. No fixes needed.`
        );
      }
      setRecalculateDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'An error occurred while recalculating balances.');
    },
  });

  const handleRecalculate = (allAccounts: boolean) => {
    if (allAccounts) {
      recalculateMutation.mutate(undefined);
    } else if (selectedAccount) {
      recalculateMutation.mutate(selectedAccount);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="General Ledger"
        description="View account-wise transaction details"
        actions={
          <div className="flex gap-2">
            <AlertDialog open={recalculateDialogOpen} onOpenChange={setRecalculateDialogOpen}>
              <AlertDialogTrigger asChild>
                <Button variant="outline" className="text-orange-600 border-orange-600 hover:bg-orange-50">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Recalculate Balances
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-500" />
                    Recalculate Account Balances
                  </AlertDialogTitle>
                  <AlertDialogDescription className="space-y-2">
                    <p>
                      This will recalculate all running balances from the General Ledger entries.
                      Use this to fix any balance discrepancies caused by entries posted out of order.
                    </p>
                    <p className="font-medium">
                      Choose an option:
                    </p>
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter className="flex-col sm:flex-row gap-2">
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  {selectedAccount && (
                    <Button
                      variant="outline"
                      onClick={() => handleRecalculate(false)}
                      disabled={recalculateMutation.isPending}
                    >
                      {recalculateMutation.isPending ? (
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      ) : null}
                      Selected Account Only
                    </Button>
                  )}
                  <AlertDialogAction
                    onClick={() => handleRecalculate(true)}
                    disabled={recalculateMutation.isPending}
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    {recalculateMutation.isPending ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : null}
                    All Accounts
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
            <Button variant="outline" onClick={handleExport} disabled={!selectedAccount}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Filter className="h-5 w-5" />
            Select Account
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Select value={selectedAccount} onValueChange={setSelectedAccount}>
              <SelectTrigger className="w-[400px]">
                <SelectValue placeholder="Select an account to view ledger" />
              </SelectTrigger>
              <SelectContent>
                {accounts
                  .filter((account: Account) => account.id && String(account.id).trim() !== '')
                  .map((account: Account) => (
                    <SelectItem key={account.id} value={String(account.id)}>
                      <span className="font-mono mr-2">{account.account_code}</span>
                      {account.account_name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {selectedAccount ? (
        <DataTable
          columns={columns}
          data={ledgerData?.items ?? []}
          searchKey="narration"
          searchPlaceholder="Search transactions..."
          isLoading={isLoading}
          manualPagination
          pageCount={ledgerData?.pages ?? 0}
          pageIndex={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookText className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Select an account to view its ledger</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
