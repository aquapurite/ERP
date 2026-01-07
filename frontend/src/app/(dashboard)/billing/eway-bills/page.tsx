'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Download, Truck, RefreshCw } from 'lucide-react';
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

interface EWayBill {
  id: string;
  ewb_number: string;
  ewb_date: string;
  valid_upto: string;
  invoice_number?: string;
  from_gstin: string;
  to_gstin: string;
  from_place: string;
  to_place: string;
  document_value: number;
  vehicle_number?: string;
  transporter_name?: string;
  status: 'GENERATED' | 'ACTIVE' | 'CANCELLED' | 'EXPIRED';
  created_at: string;
}

const ewayBillsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/billing/eway-bills', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<EWayBill>[] = [
  {
    accessorKey: 'ewb_number',
    header: 'E-Way Bill #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Truck className="h-4 w-4 text-muted-foreground" />
        <span className="font-mono font-medium">{row.original.ewb_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'invoice_number',
    header: 'Invoice',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.invoice_number || '-'}</span>
    ),
  },
  {
    accessorKey: 'route',
    header: 'Route',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.from_place}</div>
        <div className="text-muted-foreground">→ {row.original.to_place}</div>
      </div>
    ),
  },
  {
    accessorKey: 'vehicle_number',
    header: 'Vehicle',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.vehicle_number || '-'}</span>
    ),
  },
  {
    accessorKey: 'document_value',
    header: 'Value',
    cell: ({ row }) => (
      <span className="font-medium">{formatCurrency(row.original.document_value)}</span>
    ),
  },
  {
    accessorKey: 'valid_upto',
    header: 'Valid Till',
    cell: ({ row }) => {
      const isExpired = new Date(row.original.valid_upto) < new Date();
      return (
        <span className={`text-sm ${isExpired ? 'text-red-600' : 'text-muted-foreground'}`}>
          {formatDate(row.original.valid_upto)}
        </span>
      );
    },
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
          <DropdownMenuItem>
            <Download className="mr-2 h-4 w-4" />
            Download
          </DropdownMenuItem>
          {row.original.status === 'ACTIVE' && (
            <DropdownMenuItem>
              <RefreshCw className="mr-2 h-4 w-4" />
              Extend Validity
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function EWayBillsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['eway-bills', page, pageSize],
    queryFn: () => ewayBillsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="E-Way Bills"
        description="Manage GST E-Way bills for goods transportation"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Generate E-Way Bill
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="ewb_number"
        searchPlaceholder="Search E-Way bills..."
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
