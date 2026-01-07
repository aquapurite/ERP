'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Truck, MapPin, Package } from 'lucide-react';
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

interface Shipment {
  id: string;
  shipment_number: string;
  order_id?: string;
  order_number?: string;
  tracking_number?: string;
  transporter_id?: string;
  transporter?: { name: string };
  status: 'PENDING' | 'PICKED_UP' | 'IN_TRANSIT' | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'FAILED' | 'RETURNED';
  origin_warehouse?: string;
  destination_city: string;
  destination_state: string;
  destination_pincode: string;
  weight?: number;
  shipped_date?: string;
  expected_delivery?: string;
  delivered_date?: string;
  created_at: string;
}

const shipmentsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/shipments', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<Shipment>[] = [
  {
    accessorKey: 'shipment_number',
    header: 'Shipment #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Package className="h-4 w-4 text-muted-foreground" />
        <div>
          <div className="font-medium">{row.original.shipment_number}</div>
          {row.original.tracking_number && (
            <div className="text-xs text-muted-foreground font-mono">
              {row.original.tracking_number}
            </div>
          )}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'order_number',
    header: 'Order',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.order_number || '-'}</span>
    ),
  },
  {
    accessorKey: 'transporter',
    header: 'Transporter',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <Truck className="h-3 w-3 text-muted-foreground" />
        {row.original.transporter?.name || 'Not assigned'}
      </div>
    ),
  },
  {
    accessorKey: 'destination',
    header: 'Destination',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <MapPin className="h-3 w-3 text-muted-foreground" />
        <span>{row.original.destination_city}, {row.original.destination_pincode}</span>
      </div>
    ),
  },
  {
    accessorKey: 'dates',
    header: 'Timeline',
    cell: ({ row }) => (
      <div className="text-sm">
        {row.original.shipped_date && (
          <div className="text-muted-foreground">
            Shipped: {formatDate(row.original.shipped_date)}
          </div>
        )}
        {row.original.expected_delivery && (
          <div>
            ETA: {formatDate(row.original.expected_delivery)}
          </div>
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
            Track Shipment
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function ShipmentsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['shipments', page, pageSize],
    queryFn: () => shipmentsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Shipments"
        description="Track and manage order shipments"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Shipment
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="shipment_number"
        searchPlaceholder="Search shipments..."
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
