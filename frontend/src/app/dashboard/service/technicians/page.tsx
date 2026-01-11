'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Pencil, UserCog, Phone, MapPin, Star } from 'lucide-react';
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

interface Technician {
  id: string;
  employee_code: string;
  name: string;
  phone: string;
  email?: string;
  specialization?: string;
  experience_years?: number;
  rating?: number;
  total_jobs: number;
  completed_jobs: number;
  current_location?: string;
  is_available: boolean;
  is_active: boolean;
  created_at: string;
}

const techniciansApi = {
  list: async (params?: { page?: number; size?: number; is_available?: boolean }) => {
    try {
      const { data } = await apiClient.get('/technicians', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const columns: ColumnDef<Technician>[] = [
  {
    accessorKey: 'name',
    header: 'Technician',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
          <UserCog className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.employee_code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'contact',
    header: 'Contact',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <Phone className="h-3 w-3 text-muted-foreground" />
        {row.original.phone}
      </div>
    ),
  },
  {
    accessorKey: 'specialization',
    header: 'Specialization',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.specialization || 'General'}</span>
    ),
  },
  {
    accessorKey: 'performance',
    header: 'Performance',
    cell: ({ row }) => (
      <div className="text-sm">
        <div className="flex items-center gap-1">
          <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
          <span className="font-medium">{row.original.rating?.toFixed(1) || 'N/A'}</span>
        </div>
        <div className="text-muted-foreground">
          {row.original.completed_jobs}/{row.original.total_jobs} jobs
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'current_location',
    header: 'Location',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm text-muted-foreground">
        <MapPin className="h-3 w-3" />
        {row.original.current_location || 'Unknown'}
      </div>
    ),
  },
  {
    accessorKey: 'availability',
    header: 'Availability',
    cell: ({ row }) => (
      <div className="flex flex-col gap-1">
        <StatusBadge status={row.original.is_available ? 'AVAILABLE' : 'BUSY'} />
        {!row.original.is_active && (
          <span className="text-xs text-red-600">Inactive</span>
        )}
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
            <Eye className="mr-2 h-4 w-4" />
            View Profile
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

export default function TechniciansPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['technicians', page, pageSize],
    queryFn: () => techniciansApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Technicians"
        description="Manage service technicians and field engineers"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Technician
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search technicians..."
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
