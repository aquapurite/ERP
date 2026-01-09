'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, User, Phone, Mail, MapPin, ShoppingBag, Wrench, Shield } from 'lucide-react';
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
import { customersApi } from '@/lib/api';
import { Customer } from '@/types';
import { formatDate } from '@/lib/utils';

const customerTypeColors: Record<string, string> = {
  INDIVIDUAL: 'bg-blue-100 text-blue-800',
  BUSINESS: 'bg-purple-100 text-purple-800',
  DEALER: 'bg-green-100 text-green-800',
};

const getColumns = (router: ReturnType<typeof useRouter>): ColumnDef<Customer>[] => [
  {
    accessorKey: 'name',
    header: 'Customer',
    cell: ({ row }) => (
      <div
        className="flex items-center gap-3 cursor-pointer hover:opacity-80"
        onClick={() => router.push(`/crm/customers/${row.original.id}`)}
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
          <User className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">
            Since {formatDate(row.original.created_at)}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'contact',
    header: 'Contact',
    cell: ({ row }) => (
      <div className="space-y-1">
        <div className="flex items-center gap-1 text-sm">
          <Phone className="h-3 w-3 text-muted-foreground" />
          {row.original.phone}
        </div>
        {row.original.email && (
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Mail className="h-3 w-3" />
            {row.original.email}
          </div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'customer_type',
    header: 'Type',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${customerTypeColors[row.original.customer_type]}`}>
        {row.original.customer_type}
      </span>
    ),
  },
  {
    accessorKey: 'address',
    header: 'Location',
    cell: ({ row }) => {
      const defaultAddress = row.original.addresses?.find((a) => a.is_default) || row.original.addresses?.[0];
      return defaultAddress ? (
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <MapPin className="h-3 w-3" />
          {defaultAddress.city}, {defaultAddress.state}
        </div>
      ) : (
        <span className="text-sm text-muted-foreground">-</span>
      );
    },
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => (
      <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />
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
          <DropdownMenuItem onClick={() => router.push(`/crm/customers/${row.original.id}`)}>
            <Eye className="mr-2 h-4 w-4" />
            View 360° Profile
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push(`/crm/customers/${row.original.id}?tab=orders`)}>
            <ShoppingBag className="mr-2 h-4 w-4" />
            Orders
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push(`/crm/customers/${row.original.id}?tab=services`)}>
            <Wrench className="mr-2 h-4 w-4" />
            Service History
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push(`/crm/customers/${row.original.id}?tab=amc`)}>
            <Shield className="mr-2 h-4 w-4" />
            AMC Contracts
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function CustomersPage() {
  const router = useRouter();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['customers', page, pageSize],
    queryFn: () => customersApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="Manage customer database and profiles"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Customer
          </Button>
        }
      />

      <DataTable
        columns={getColumns(router)}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search customers..."
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
