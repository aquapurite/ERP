'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Truck, Phone, Mail, Globe } from 'lucide-react';
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

interface Transporter {
  id: string;
  name: string;
  code: string;
  type: 'COURIER' | 'LOGISTICS' | 'SELF';
  contact_person?: string;
  phone?: string;
  email?: string;
  website?: string;
  tracking_url_template?: string;
  api_integrated: boolean;
  serviceable_states?: string[];
  is_active: boolean;
  created_at: string;
}

const transportersApi = {
  list: async (params?: { page?: number; size?: number }) => {
    try {
      const { data } = await apiClient.get('/transporters', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const typeLabels: Record<string, string> = {
  COURIER: 'Courier Partner',
  LOGISTICS: 'Logistics Provider',
  SELF: 'Self-Delivery',
};

const columns: ColumnDef<Transporter>[] = [
  {
    accessorKey: 'name',
    header: 'Transporter',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Truck className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => (
      <span className="text-sm">{typeLabels[row.original.type] || row.original.type}</span>
    ),
  },
  {
    accessorKey: 'contact',
    header: 'Contact',
    cell: ({ row }) => (
      <div className="space-y-1">
        {row.original.contact_person && (
          <div className="text-sm">{row.original.contact_person}</div>
        )}
        {row.original.phone && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Phone className="h-3 w-3" />
            {row.original.phone}
          </div>
        )}
        {row.original.email && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Mail className="h-3 w-3" />
            {row.original.email}
          </div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'api_integrated',
    header: 'Integration',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        row.original.api_integrated
          ? 'bg-green-100 text-green-800'
          : 'bg-gray-100 text-gray-800'
      }`}>
        {row.original.api_integrated ? 'API Integrated' : 'Manual'}
      </span>
    ),
  },
  {
    accessorKey: 'website',
    header: 'Website',
    cell: ({ row }) => (
      row.original.website ? (
        <a
          href={row.original.website}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          <Globe className="h-3 w-3" />
          Visit
        </a>
      ) : (
        <span className="text-sm text-muted-foreground">-</span>
      )
    ),
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
          <DropdownMenuItem>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function TransportersPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['transporters', page, pageSize],
    queryFn: () => transportersApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transporters"
        description="Manage courier and logistics partners"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Transporter
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search transporters..."
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
