'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, RefreshCw, Shield, AlertTriangle } from 'lucide-react';
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

interface AMCContract {
  id: string;
  contract_number: string;
  customer_id: string;
  customer?: { name: string; phone: string };
  product_id: string;
  product?: { name: string };
  serial_number?: string;
  plan_name: string;
  start_date: string;
  end_date: string;
  amount: number;
  visits_included: number;
  visits_used: number;
  status: 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'PENDING_RENEWAL';
  auto_renew: boolean;
  created_at: string;
}

const amcApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      // AMC contracts would typically be fetched from service-requests or a dedicated endpoint
      const { data } = await apiClient.get('/service-requests', { params: { ...params, type: 'AMC' } });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<AMCContract>[] = [
  {
    accessorKey: 'contract_number',
    header: 'Contract #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Shield className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.contract_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'customer',
    header: 'Customer',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.customer?.name || 'N/A'}</div>
        <div className="text-sm text-muted-foreground">{row.original.product?.name}</div>
      </div>
    ),
  },
  {
    accessorKey: 'plan_name',
    header: 'Plan',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.plan_name}</span>
    ),
  },
  {
    accessorKey: 'validity',
    header: 'Validity',
    cell: ({ row }) => {
      const isExpiringSoon = new Date(row.original.end_date) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
      return (
        <div className="flex items-center gap-1">
          {isExpiringSoon && row.original.status === 'ACTIVE' && (
            <AlertTriangle className="h-3 w-3 text-orange-500" />
          )}
          <div className="text-sm">
            <div>{formatDate(row.original.start_date)}</div>
            <div className="text-muted-foreground">to {formatDate(row.original.end_date)}</div>
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: 'visits',
    header: 'Visits',
    cell: ({ row }) => (
      <div className="text-sm">
        <span className="font-medium">{row.original.visits_used}</span>
        <span className="text-muted-foreground"> / {row.original.visits_included}</span>
      </div>
    ),
  },
  {
    accessorKey: 'amount',
    header: 'Amount',
    cell: ({ row }) => (
      <span className="font-medium">{formatCurrency(row.original.amount)}</span>
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
          {(row.original.status === 'EXPIRED' || row.original.status === 'PENDING_RENEWAL') && (
            <DropdownMenuItem>
              <RefreshCw className="mr-2 h-4 w-4" />
              Renew Contract
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function AMCPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['amc', page, pageSize],
    queryFn: () => amcApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="AMC Contracts"
        description="Annual Maintenance Contract management"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New AMC Contract
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="contract_number"
        searchPlaceholder="Search contracts..."
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
