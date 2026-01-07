'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Download, FileStack, Truck } from 'lucide-react';
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

interface Manifest {
  id: string;
  manifest_number: string;
  transporter_id: string;
  transporter?: { name: string };
  warehouse_id: string;
  warehouse?: { name: string };
  status: 'DRAFT' | 'FINALIZED' | 'HANDED_OVER' | 'IN_TRANSIT' | 'COMPLETED';
  shipments_count: number;
  total_weight?: number;
  vehicle_number?: string;
  driver_name?: string;
  driver_phone?: string;
  handover_date?: string;
  created_at: string;
}

const manifestsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/manifests', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<Manifest>[] = [
  {
    accessorKey: 'manifest_number',
    header: 'Manifest #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <FileStack className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.manifest_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'transporter',
    header: 'Transporter',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <Truck className="h-3 w-3 text-muted-foreground" />
        {row.original.transporter?.name || 'N/A'}
      </div>
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
    accessorKey: 'shipments_count',
    header: 'Shipments',
    cell: ({ row }) => (
      <span className="font-medium">{row.original.shipments_count}</span>
    ),
  },
  {
    accessorKey: 'vehicle',
    header: 'Vehicle',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="font-mono">{row.original.vehicle_number || '-'}</div>
        {row.original.driver_name && (
          <div className="text-muted-foreground text-xs">{row.original.driver_name}</div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'handover_date',
    header: 'Handover Date',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.handover_date ? formatDate(row.original.handover_date) : '-'}
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
          <DropdownMenuItem>
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function ManifestsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['manifests', page, pageSize],
    queryFn: () => manifestsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Manifests"
        description="Manage shipping manifests and handover documents"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Manifest
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="manifest_number"
        searchPlaceholder="Search manifests..."
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
