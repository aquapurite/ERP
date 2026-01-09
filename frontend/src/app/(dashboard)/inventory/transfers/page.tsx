'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, ArrowRightLeft, Warehouse } from 'lucide-react';
import Link from 'next/link';
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

interface StockTransfer {
  id: string;
  transfer_number: string;
  source_warehouse_id: string;
  destination_warehouse_id: string;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'IN_TRANSIT' | 'RECEIVED' | 'CANCELLED';
  total_quantity: number;
  transfer_date: string;
  notes?: string;
  created_at: string;
  source_warehouse?: { name: string; code: string };
  destination_warehouse?: { name: string; code: string };
}

const transfersApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/transfers', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<StockTransfer>[] = [
  {
    accessorKey: 'transfer_number',
    header: 'Transfer #',
    cell: ({ row }) => (
      <div className="font-medium">{row.original.transfer_number}</div>
    ),
  },
  {
    accessorKey: 'source',
    header: 'From',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Warehouse className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">
          {row.original.source_warehouse?.name || 'N/A'}
        </span>
      </div>
    ),
  },
  {
    accessorKey: 'destination',
    header: 'To',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">
          {row.original.destination_warehouse?.name || 'N/A'}
        </span>
      </div>
    ),
  },
  {
    accessorKey: 'total_quantity',
    header: 'Quantity',
    cell: ({ row }) => (
      <span className="font-medium">{row.original.total_quantity}</span>
    ),
  },
  {
    accessorKey: 'transfer_date',
    header: 'Transfer Date',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {formatDate(row.original.transfer_date)}
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

export default function TransfersPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['transfers', page, pageSize],
    queryFn: () => transfersApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stock Transfers"
        description="Manage inventory transfers between warehouses"
        actions={
          <Button asChild>
            <Link href="/inventory/transfers/new">
              <Plus className="mr-2 h-4 w-4" />
              New Transfer
            </Link>
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="transfer_number"
        searchPlaceholder="Search transfers..."
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
