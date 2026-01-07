'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, UserPlus, Phone, Target } from 'lucide-react';
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

interface Lead {
  id: string;
  name: string;
  phone: string;
  email?: string;
  source: string;
  status: 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';
  stage: string;
  assigned_to_id?: string;
  assigned_to?: { full_name: string };
  expected_value?: number;
  expected_close_date?: string;
  notes?: string;
  created_at: string;
  last_contacted_at?: string;
}

const leadsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/leads', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const sourceColors: Record<string, string> = {
  WEBSITE: 'bg-blue-100 text-blue-800',
  REFERRAL: 'bg-green-100 text-green-800',
  SOCIAL_MEDIA: 'bg-purple-100 text-purple-800',
  CALL_CENTER: 'bg-orange-100 text-orange-800',
  WALK_IN: 'bg-gray-100 text-gray-800',
};

const columns: ColumnDef<Lead>[] = [
  {
    accessorKey: 'name',
    header: 'Lead',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
          <Target className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Phone className="h-3 w-3" />
            {row.original.phone}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'source',
    header: 'Source',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${sourceColors[row.original.source] || 'bg-gray-100'}`}>
        {row.original.source.replace(/_/g, ' ')}
      </span>
    ),
  },
  {
    accessorKey: 'assigned_to',
    header: 'Assigned To',
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.assigned_to?.full_name || 'Unassigned'}
      </span>
    ),
  },
  {
    accessorKey: 'expected_value',
    header: 'Value',
    cell: ({ row }) => (
      <span className="font-medium">
        {row.original.expected_value
          ? `₹${row.original.expected_value.toLocaleString('en-IN')}`
          : '-'}
      </span>
    ),
  },
  {
    accessorKey: 'last_contacted_at',
    header: 'Last Contact',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.last_contacted_at
          ? formatDate(row.original.last_contacted_at)
          : 'Never'}
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
          {row.original.status === 'WON' && (
            <DropdownMenuItem>
              <UserPlus className="mr-2 h-4 w-4" />
              Convert to Customer
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function LeadsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['leads', page, pageSize],
    queryFn: () => leadsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leads"
        description="Manage sales leads and pipeline"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Lead
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search leads..."
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
