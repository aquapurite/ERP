'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Download, FileX } from 'lucide-react';
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

interface CreditNote {
  id: string;
  credit_note_number: string;
  credit_note_date: string;
  invoice_id?: string;
  invoice_number?: string;
  customer_id: string;
  customer?: { name: string };
  reason: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  status: 'DRAFT' | 'APPROVED' | 'APPLIED' | 'CANCELLED';
  created_at: string;
}

const creditNotesApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/billing/credit-debit-notes', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<CreditNote>[] = [
  {
    accessorKey: 'credit_note_number',
    header: 'Credit Note #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <FileX className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.credit_note_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'invoice_number',
    header: 'Against Invoice',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.invoice_number || '-'}
      </span>
    ),
  },
  {
    accessorKey: 'customer',
    header: 'Customer',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.customer?.name || 'N/A'}</span>
    ),
  },
  {
    accessorKey: 'credit_note_date',
    header: 'Date',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {formatDate(row.original.credit_note_date)}
      </span>
    ),
  },
  {
    accessorKey: 'reason',
    header: 'Reason',
    cell: ({ row }) => (
      <span className="text-sm line-clamp-1">{row.original.reason}</span>
    ),
  },
  {
    accessorKey: 'total_amount',
    header: 'Amount',
    cell: ({ row }) => (
      <span className="font-medium text-red-600">
        -{formatCurrency(row.original.total_amount)}
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
            View
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function CreditNotesPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['credit-notes', page, pageSize],
    queryFn: () => creditNotesApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Credit Notes"
        description="Manage credit notes and refunds"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Credit Note
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="credit_note_number"
        searchPlaceholder="Search credit notes..."
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
