'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Download, QrCode, Barcode, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatDate } from '@/lib/utils';

interface SerialItem {
  id: string;
  serial_number: string;
  barcode: string;
  product_id: string;
  product?: { name: string; sku: string };
  po_id?: string;
  po_number?: string;
  warehouse_id?: string;
  warehouse?: { name: string };
  status: 'GENERATED' | 'IN_STOCK' | 'ALLOCATED' | 'SHIPPED' | 'DELIVERED' | 'INSTALLED' | 'RETURNED' | 'SCRAPPED';
  manufactured_date?: string;
  warranty_start_date?: string;
  warranty_end_date?: string;
  created_at: string;
}

const serializationApi = {
  list: async (params?: { page?: number; size?: number; status?: string; product_id?: string }) => {
    try {
      // Use inventory stock-items as the source for serial data
      const { data } = await apiClient.get('/inventory/stock-items', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  validate: async (barcode: string) => {
    try {
      const { data } = await apiClient.get(`/serialization/validate/${barcode}`);
      return data;
    } catch {
      return { valid: false, message: 'Barcode not found or invalid' };
    }
  },
};

const columns: ColumnDef<SerialItem>[] = [
  {
    accessorKey: 'serial_number',
    header: 'Serial Number',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Barcode className="h-4 w-4 text-muted-foreground" />
        <div>
          <div className="font-mono font-medium">{row.original.serial_number}</div>
          <div className="text-xs text-muted-foreground font-mono">
            {row.original.barcode}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'product',
    header: 'Product',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.product?.name || 'N/A'}</div>
        <div className="text-muted-foreground font-mono text-xs">
          {row.original.product?.sku}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'po_number',
    header: 'PO Reference',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.po_number || '-'}</span>
    ),
  },
  {
    accessorKey: 'warehouse',
    header: 'Location',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.warehouse?.name || '-'}</span>
    ),
  },
  {
    accessorKey: 'warranty',
    header: 'Warranty',
    cell: ({ row }) => (
      row.original.warranty_end_date ? (
        <div className="text-sm">
          <div>Till {formatDate(row.original.warranty_end_date)}</div>
        </div>
      ) : (
        <span className="text-sm text-muted-foreground">-</span>
      )
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
            View History
          </DropdownMenuItem>
          <DropdownMenuItem>
            <QrCode className="mr-2 h-4 w-4" />
            Print Barcode
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function SerializationPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [validateBarcode, setValidateBarcode] = useState('');
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message: string;
    item?: SerialItem;
  } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['serial-items', page, pageSize],
    queryFn: () => serializationApi.list({ page: page + 1, size: pageSize }),
  });

  const handleValidate = async () => {
    if (!validateBarcode.trim()) return;
    try {
      const result = await serializationApi.validate(validateBarcode);
      setValidationResult(result);
    } catch (error) {
      setValidationResult({
        valid: false,
        message: 'Barcode not found or invalid',
      });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Serialization"
        description="Manage product serial numbers and barcodes"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Generate Serials
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <QrCode className="h-5 w-5" />
            Barcode Validation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <Input
                placeholder="Scan or enter barcode"
                value={validateBarcode}
                onChange={(e) => setValidateBarcode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleValidate()}
              />
            </div>
            <Button onClick={handleValidate}>Validate</Button>
          </div>
          {validationResult && (
            <div className={`mt-4 p-4 rounded-lg ${
              validationResult.valid ? 'bg-green-50' : 'bg-red-50'
            }`}>
              <div className="flex items-center gap-2">
                {validationResult.valid ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
                <span className={validationResult.valid ? 'text-green-800' : 'text-red-800'}>
                  {validationResult.message}
                </span>
              </div>
              {validationResult.item && (
                <div className="mt-2 text-sm text-muted-foreground">
                  <div>Product: {validationResult.item.product?.name}</div>
                  <div>Status: {validationResult.item.status}</div>
                  {validationResult.item.warehouse && (
                    <div>Location: {validationResult.item.warehouse.name}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="serial_number"
        searchPlaceholder="Search serial numbers..."
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
