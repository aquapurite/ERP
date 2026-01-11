'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { Package, Warehouse, AlertTriangle, ArrowLeftRight, Filter } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { inventoryApi, warehousesApi, productsApi } from '@/lib/api';
import { StockItem } from '@/types';

interface WarehouseOption {
  id: string;
  name: string;
  code: string;
}

const statusColors: Record<string, string> = {
  IN_STOCK: 'bg-green-100 text-green-800',
  LOW_STOCK: 'bg-yellow-100 text-yellow-800',
  OUT_OF_STOCK: 'bg-red-100 text-red-800',
  RESERVED: 'bg-blue-100 text-blue-800',
};

export default function StockItemsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [warehouseFilter, setWarehouseFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data, isLoading } = useQuery({
    queryKey: ['stock-items', page, pageSize, warehouseFilter, statusFilter],
    queryFn: () =>
      inventoryApi.getStock({
        page: page + 1,
        size: pageSize,
        warehouse_id: warehouseFilter !== 'all' ? warehouseFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      }),
  });

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses-dropdown'],
    queryFn: () => warehousesApi.list({ size: 100 }),
  });

  const { data: stats } = useQuery({
    queryKey: ['inventory-stats'],
    queryFn: inventoryApi.getStats,
  });

  const columns: ColumnDef<StockItem>[] = [
    {
      accessorKey: 'product',
      header: 'Product',
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <Package className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <div className="font-medium">{row.original.product?.name || 'Unknown'}</div>
            <div className="text-sm text-muted-foreground font-mono">
              {row.original.product?.sku || '-'}
            </div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'warehouse',
      header: 'Warehouse',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Warehouse className="h-4 w-4 text-muted-foreground" />
          <div>
            <div className="text-sm font-medium">{row.original.warehouse?.name || 'Unknown'}</div>
            <div className="text-xs text-muted-foreground">{row.original.warehouse?.code}</div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'quantity',
      header: 'Total Qty',
      cell: ({ row }) => (
        <span className="font-mono text-sm font-medium">{row.original.quantity}</span>
      ),
    },
    {
      accessorKey: 'reserved_quantity',
      header: 'Reserved',
      cell: ({ row }) => (
        <span className="font-mono text-sm text-orange-600">{row.original.reserved_quantity}</span>
      ),
    },
    {
      accessorKey: 'available_quantity',
      header: 'Available',
      cell: ({ row }) => {
        const qty = row.original.available_quantity ?? 0;
        const color = qty > 10 ? 'text-green-600' : qty > 0 ? 'text-yellow-600' : 'text-red-600';
        return <span className={`font-mono text-sm font-medium ${color}`}>{qty}</span>;
      },
    },
    {
      accessorKey: 'reorder_level',
      header: 'Reorder Level',
      cell: ({ row }) => {
        const availableQty = row.original.available_quantity ?? 0;
        const reorderLevel = row.original.reorder_level ?? 0;
        const isLow = availableQty <= reorderLevel;
        return (
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm">{reorderLevel}</span>
            {isLow && <AlertTriangle className="h-4 w-4 text-yellow-500" />}
          </div>
        );
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[row.original.status] || 'bg-gray-100'}`}
        >
          {row.original.status.replace('_', ' ')}
        </span>
      ),
    },
  ];

  const warehouses: WarehouseOption[] = warehousesData?.items ?? [];
  const stockItems = data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stock Items"
        description="View and manage inventory stock levels across warehouses"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href="/dashboard/inventory/adjustments">
                <Package className="mr-2 h-4 w-4" />
                Stock Adjustments
              </Link>
            </Button>
            <Button asChild>
              <Link href="/dashboard/inventory/transfers/new">
                <ArrowLeftRight className="mr-2 h-4 w-4" />
                Create Transfer
              </Link>
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total SKUs</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_skus ?? 0}</div>
            <p className="text-xs text-muted-foreground">Unique products in stock</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Stock</CardTitle>
            <Package className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.in_stock ?? 0}</div>
            <p className="text-xs text-muted-foreground">Items available</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats?.low_stock ?? 0}</div>
            <p className="text-xs text-muted-foreground">Need reordering</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Out of Stock</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats?.out_of_stock ?? 0}</div>
            <p className="text-xs text-muted-foreground">Urgent attention needed</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters:</span>
        </div>
        <Select value={warehouseFilter} onValueChange={setWarehouseFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Warehouses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Warehouses</SelectItem>
            {warehouses.map((wh) => (
              <SelectItem key={wh.id} value={wh.id}>
                {wh.name} ({wh.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="IN_STOCK">In Stock</SelectItem>
            <SelectItem value="LOW_STOCK">Low Stock</SelectItem>
            <SelectItem value="OUT_OF_STOCK">Out of Stock</SelectItem>
            <SelectItem value="RESERVED">Reserved</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={stockItems}
        searchKey="product"
        searchPlaceholder="Search products..."
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
