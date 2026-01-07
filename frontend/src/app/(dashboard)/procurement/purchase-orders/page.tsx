'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, FileText, Send, CheckCircle } from 'lucide-react';
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
import { purchaseOrdersApi } from '@/lib/api';
import { PurchaseOrder } from '@/types';
import { formatCurrency, formatDate } from '@/lib/utils';

const columns: ColumnDef<PurchaseOrder>[] = [
  {
    accessorKey: 'po_number',
    header: 'PO Number',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.po_number}</span>
      </div>
    ),
  },
  {
    accessorKey: 'vendor',
    header: 'Vendor',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.vendor?.name || 'N/A'}</div>
        <div className="text-sm text-muted-foreground">{row.original.vendor?.code}</div>
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
    accessorKey: 'grand_total',
    header: 'Amount',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{formatCurrency(row.original.grand_total)}</div>
        <div className="text-xs text-muted-foreground">
          GST: {formatCurrency(row.original.gst_amount)}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'expected_delivery_date',
    header: 'Expected Delivery',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.expected_delivery_date
          ? formatDate(row.original.expected_delivery_date)
          : '-'}
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
          {row.original.status === 'DRAFT' && (
            <DropdownMenuItem>
              <Send className="mr-2 h-4 w-4" />
              Submit for Approval
            </DropdownMenuItem>
          )}
          {row.original.status === 'APPROVED' && (
            <DropdownMenuItem>
              <CheckCircle className="mr-2 h-4 w-4" />
              Send to Vendor
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function PurchaseOrdersPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', page, pageSize],
    queryFn: () => purchaseOrdersApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Orders"
        description="Manage purchase orders and vendor procurement"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create PO
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="po_number"
        searchPlaceholder="Search PO number..."
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
