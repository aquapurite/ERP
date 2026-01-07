'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, BookOpen } from 'lucide-react';
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
import { formatDate, formatCurrency } from '@/lib/utils';

interface JournalEntry {
  id: string;
  entry_number: string;
  entry_date: string;
  reference?: string;
  narration: string;
  total_debit: number;
  total_credit: number;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'POSTED' | 'REJECTED';
  created_by?: { full_name: string };
  approved_by?: { full_name: string };
  created_at: string;
}

const journalApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/accounting/journals', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<JournalEntry>[] = [
  {
    accessorKey: 'entry_number',
    header: 'Entry #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <BookOpen className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.entry_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'entry_date',
    header: 'Date',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {formatDate(row.original.entry_date)}
      </span>
    ),
  },
  {
    accessorKey: 'narration',
    header: 'Narration',
    cell: ({ row }) => (
      <span className="text-sm line-clamp-1">{row.original.narration}</span>
    ),
  },
  {
    accessorKey: 'total_debit',
    header: 'Debit',
    cell: ({ row }) => (
      <span className="font-medium text-green-600">
        {formatCurrency(row.original.total_debit)}
      </span>
    ),
  },
  {
    accessorKey: 'total_credit',
    header: 'Credit',
    cell: ({ row }) => (
      <span className="font-medium text-blue-600">
        {formatCurrency(row.original.total_credit)}
      </span>
    ),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
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
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function JournalEntriesPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['journal-entries', page, pageSize],
    queryFn: () => journalApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Journal Entries"
        description="Record and manage accounting journal entries"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Journal Entry
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="entry_number"
        searchPlaceholder="Search entries..."
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
