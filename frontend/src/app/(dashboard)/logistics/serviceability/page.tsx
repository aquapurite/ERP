'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, MapPin, CheckCircle, XCircle, Upload } from 'lucide-react';
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
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';

interface ServiceabilityZone {
  id: string;
  pincode: string;
  city: string;
  state: string;
  zone: string;
  is_serviceable: boolean;
  delivery_days: number;
  cod_available: boolean;
  prepaid_available: boolean;
  max_weight?: number;
  franchisee_id?: string;
  franchisee?: { name: string };
  created_at: string;
}

const serviceabilityApi = {
  list: async (params?: { page?: number; size?: number; is_serviceable?: boolean }) => {
    try {
      const { data } = await apiClient.get('/serviceability/warehouse', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  check: async (pincode: string) => {
    try {
      const { data } = await apiClient.get(`/serviceability/check/${pincode}`);
      return data;
    } catch {
      return { serviceable: false, message: 'Unable to check serviceability' };
    }
  },
};

const columns: ColumnDef<ServiceabilityZone>[] = [
  {
    accessorKey: 'pincode',
    header: 'Pincode',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <MapPin className="h-4 w-4 text-muted-foreground" />
        <span className="font-mono font-medium">{row.original.pincode}</span>
      </div>
    ),
  },
  {
    accessorKey: 'location',
    header: 'Location',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.city}</div>
        <div className="text-muted-foreground">{row.original.state}</div>
      </div>
    ),
  },
  {
    accessorKey: 'zone',
    header: 'Zone',
    cell: ({ row }) => (
      <span className="px-2 py-1 rounded bg-muted text-sm">{row.original.zone}</span>
    ),
  },
  {
    accessorKey: 'delivery_days',
    header: 'Delivery',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.delivery_days} days</span>
    ),
  },
  {
    accessorKey: 'payment',
    header: 'Payment Options',
    cell: ({ row }) => (
      <div className="flex gap-2">
        <span className={`px-2 py-0.5 rounded text-xs ${
          row.original.prepaid_available ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
        }`}>
          Prepaid
        </span>
        <span className={`px-2 py-0.5 rounded text-xs ${
          row.original.cod_available ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-500'
        }`}>
          COD
        </span>
      </div>
    ),
  },
  {
    accessorKey: 'franchisee',
    header: 'Franchisee',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.franchisee?.name || '-'}</span>
    ),
  },
  {
    accessorKey: 'is_serviceable',
    header: 'Status',
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        {row.original.is_serviceable ? (
          <CheckCircle className="h-4 w-4 text-green-600" />
        ) : (
          <XCircle className="h-4 w-4 text-red-600" />
        )}
        <span className={row.original.is_serviceable ? 'text-green-600' : 'text-red-600'}>
          {row.original.is_serviceable ? 'Serviceable' : 'Not Serviceable'}
        </span>
      </div>
    ),
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

export default function ServiceabilityPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [checkPincode, setCheckPincode] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['serviceability', page, pageSize],
    queryFn: () => serviceabilityApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Serviceability"
        description="Manage delivery zones and pincode serviceability"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Upload className="mr-2 h-4 w-4" />
              Bulk Upload
            </Button>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Pincode
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Check Pincode Serviceability</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Input
              placeholder="Enter pincode"
              value={checkPincode}
              onChange={(e) => setCheckPincode(e.target.value)}
              className="w-48"
            />
            <Button variant="outline" disabled={checkPincode.length !== 6}>
              Check
            </Button>
          </div>
        </CardContent>
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="pincode"
        searchPlaceholder="Search pincodes..."
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
