'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, CheckCircle, Wrench, Calendar } from 'lucide-react';
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

interface Installation {
  id: string;
  installation_number: string;
  order_id?: string;
  customer_id: string;
  customer?: { name: string; phone: string };
  product_id: string;
  product?: { name: string; sku: string };
  serial_number?: string;
  status: 'PENDING' | 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  scheduled_date?: string;
  completed_date?: string;
  technician_id?: string;
  technician?: { name: string };
  address?: string;
  notes?: string;
  created_at: string;
}

const installationsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/installations', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<Installation>[] = [
  {
    accessorKey: 'installation_number',
    header: 'Installation #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Wrench className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.installation_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'customer',
    header: 'Customer',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.customer?.name || 'N/A'}</div>
        <div className="text-sm text-muted-foreground">{row.original.customer?.phone}</div>
      </div>
    ),
  },
  {
    accessorKey: 'product',
    header: 'Product',
    cell: ({ row }) => (
      <div>
        <div className="text-sm">{row.original.product?.name || 'N/A'}</div>
        <div className="text-xs text-muted-foreground font-mono">{row.original.serial_number}</div>
      </div>
    ),
  },
  {
    accessorKey: 'technician',
    header: 'Technician',
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.technician?.name || 'Not assigned'}
      </span>
    ),
  },
  {
    accessorKey: 'scheduled_date',
    header: 'Schedule',
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <Calendar className="h-3 w-3 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">
          {row.original.scheduled_date ? formatDate(row.original.scheduled_date) : 'Not scheduled'}
        </span>
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
              Mark Complete
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function InstallationsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['installations', page, pageSize],
    queryFn: () => installationsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Installations"
        description="Track and manage product installations"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Installation
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="installation_number"
        searchPlaceholder="Search installations..."
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
