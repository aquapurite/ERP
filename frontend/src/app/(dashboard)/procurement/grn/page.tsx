'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Package, CheckCircle } from 'lucide-react';
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
import { formatDate } from '@/lib/utils';

interface GRN {
  id: string;
  grn_number: string;
  po_id: string;
  po_number?: string;
  warehouse_id: string;
  status: 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  received_date: string;
  total_received: number;
  total_rejected: number;
  notes?: string;
  created_at: string;
  warehouse?: { name: string; code: string };
  vendor?: { name: string };
}

const grnApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/purchase/grn', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<GRN>[] = [
  {
    accessorKey: 'grn_number',
    header: 'GRN Number',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Package className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.grn_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'po_number',
    header: 'PO Reference',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.po_number || row.original.po_id?.slice(0, 8)}
      </span>
    ),
  },
  {
    accessorKey: 'warehouse',
    header: 'Warehouse',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.warehouse?.name || 'N/A'}</span>
    ),
  },
  {
    accessorKey: 'received_date',
    header: 'Received Date',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {formatDate(row.original.received_date)}
      </span>
    ),
  },
  {
    accessorKey: 'quantities',
    header: 'Quantities',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="text-green-600">Received: {row.original.total_received}</div>
        {row.original.total_rejected > 0 && (
          <div className="text-red-600">Rejected: {row.original.total_rejected}</div>
        )}
      </div>
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
          {row.original.status === 'IN_PROGRESS' && (
            <DropdownMenuItem>
              <CheckCircle className="mr-2 h-4 w-4" />
              Complete GRN
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function GRNPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['grn', page, pageSize],
    queryFn: () => grnApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goods Receipt Notes"
        description="Process and track incoming goods from vendors"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create GRN
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="grn_number"
        searchPlaceholder="Search GRN..."
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
