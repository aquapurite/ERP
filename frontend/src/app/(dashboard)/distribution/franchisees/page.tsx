'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Pencil, Building2, MapPin, Phone } from 'lucide-react';
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

interface Franchisee {
  id: string;
  name: string;
  code: string;
  owner_name: string;
  phone: string;
  email?: string;
  territory?: string;
  city: string;
  state: string;
  status: 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'TERMINATED';
  agreement_start_date?: string;
  agreement_end_date?: string;
  royalty_percentage?: number;
  serviceable_pincodes_count?: number;
  created_at: string;
}

const franchiseesApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/franchisees', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<Franchisee>[] = [
  {
    accessorKey: 'name',
    header: 'Franchisee',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Building2 className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'owner_name',
    header: 'Owner',
    cell: ({ row }) => (
      <div>
        <div className="text-sm">{row.original.owner_name}</div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Phone className="h-3 w-3" />
          {row.original.phone}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'location',
    header: 'Location',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <MapPin className="h-3 w-3 text-muted-foreground" />
        <span>{row.original.city}, {row.original.state}</span>
      </div>
    ),
  },
  {
    accessorKey: 'territory',
    header: 'Territory',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.territory || '-'}</div>
        {row.original.serviceable_pincodes_count && (
          <div className="text-xs text-muted-foreground">
            {row.original.serviceable_pincodes_count} pincodes
          </div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'agreement',
    header: 'Agreement',
    cell: ({ row }) => (
      <div className="text-sm">
        {row.original.agreement_end_date ? (
          <>
            <div>Till {formatDate(row.original.agreement_end_date)}</div>
            {row.original.royalty_percentage && (
              <div className="text-xs text-muted-foreground">
                {row.original.royalty_percentage}% royalty
              </div>
            )}
          </>
        ) : (
          <span className="text-muted-foreground">No agreement</span>
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
            View Details
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function FranchiseesPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['franchisees', page, pageSize],
    queryFn: () => franchiseesApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Franchisees"
        description="Manage franchise partners and territories"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Franchisee
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search franchisees..."
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
