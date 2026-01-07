'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, ChevronRight, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';

interface Account {
  id: string;
  code: string;
  name: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  parent_id?: string;
  is_active: boolean;
  is_group: boolean;
  balance: number;
  created_at: string;
}

const accountsApi = {
  list: async (params?: { page?: number; size?: number; type?: string }) => {
    try {
      const { data } = await apiClient.get('/accounting/accounts', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const typeColors: Record<string, string> = {
  ASSET: 'bg-blue-100 text-blue-800',
  LIABILITY: 'bg-red-100 text-red-800',
  EQUITY: 'bg-purple-100 text-purple-800',
  REVENUE: 'bg-green-100 text-green-800',
  EXPENSE: 'bg-orange-100 text-orange-800',
};

const columns: ColumnDef<Account>[] = [
  {
    accessorKey: 'code',
    header: 'Code',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.code}</span>
    ),
  },
  {
    accessorKey: 'name',
    header: 'Account Name',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        {row.original.is_group && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
        <span className={row.original.is_group ? 'font-medium' : ''}>
          {row.original.name}
        </span>
      </div>
    ),
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeColors[row.original.type]}`}>
        {row.original.type}
      </span>
    ),
  },
  {
    accessorKey: 'balance',
    header: 'Balance',
    cell: ({ row }) => (
      <span className={`font-medium ${row.original.balance < 0 ? 'text-red-600' : ''}`}>
        ₹{Math.abs(row.original.balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        {row.original.balance < 0 ? ' Cr' : ' Dr'}
      </span>
    ),
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
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function ChartOfAccountsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  const { data, isLoading } = useQuery({
    queryKey: ['accounts', page, pageSize],
    queryFn: () => accountsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Chart of Accounts"
        description="Manage accounting structure and ledger accounts"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Account
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search accounts..."
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
