'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Gift, Percent, Tag, Calendar } from 'lucide-react';
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

interface Promotion {
  id: string;
  name: string;
  code: string;
  type: 'PERCENTAGE' | 'FIXED_AMOUNT' | 'BUY_X_GET_Y' | 'FREE_SHIPPING' | 'BUNDLE';
  discount_value: number;
  min_order_value?: number;
  max_discount?: number;
  usage_limit?: number;
  usage_count: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  applicable_to: 'ALL' | 'PRODUCTS' | 'CATEGORIES' | 'CUSTOMERS';
  created_at: string;
}

const promotionsApi = {
  list: async (params?: { page?: number; size?: number; is_active?: boolean }) => {
    try {
      const { data } = await apiClient.get('/promotions', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const typeIcons: Record<string, React.ReactNode> = {
  PERCENTAGE: <Percent className="h-4 w-4" />,
  FIXED_AMOUNT: <Tag className="h-4 w-4" />,
  BUY_X_GET_Y: <Gift className="h-4 w-4" />,
  FREE_SHIPPING: <Gift className="h-4 w-4" />,
  BUNDLE: <Gift className="h-4 w-4" />,
};

const columns: ColumnDef<Promotion>[] = [
  {
    accessorKey: 'name',
    header: 'Promotion',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          {typeIcons[row.original.type] || <Gift className="h-5 w-5 text-muted-foreground" />}
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="font-mono text-sm text-muted-foreground">{row.original.code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'discount',
    header: 'Discount',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="font-medium text-green-600">
          {row.original.type === 'PERCENTAGE'
            ? `${row.original.discount_value}%`
            : formatCurrency(row.original.discount_value)}
        </div>
        {row.original.max_discount && (
          <div className="text-muted-foreground text-xs">
            Max: {formatCurrency(row.original.max_discount)}
          </div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'min_order_value',
    header: 'Min Order',
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.min_order_value
          ? formatCurrency(row.original.min_order_value)
          : 'No minimum'}
      </span>
    ),
  },
  {
    accessorKey: 'usage',
    header: 'Usage',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="font-medium">{row.original.usage_count}</div>
        <div className="text-muted-foreground text-xs">
          {row.original.usage_limit ? `of ${row.original.usage_limit}` : 'Unlimited'}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'validity',
    header: 'Valid Period',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <Calendar className="h-3 w-3 text-muted-foreground" />
        <div>
          <div>{formatDate(row.original.start_date)}</div>
          <div className="text-muted-foreground">to {formatDate(row.original.end_date)}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => {
      const now = new Date();
      const endDate = new Date(row.original.end_date);
      const isExpired = endDate < now;
      return (
        <StatusBadge
          status={isExpired ? 'EXPIRED' : row.original.is_active ? 'ACTIVE' : 'INACTIVE'}
        />
      );
    },
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
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function PromotionsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['promotions', page, pageSize],
    queryFn: () => promotionsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Promotions"
        description="Manage discount codes and promotional offers"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Promotion
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="code"
        searchPlaceholder="Search promotions..."
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
