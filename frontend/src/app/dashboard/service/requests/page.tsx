'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, UserPlus, Wrench } from 'lucide-react';
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
import { serviceRequestsApi } from '@/lib/api';
import { ServiceRequest } from '@/types';
import { formatDate } from '@/lib/utils';

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-800',
  NORMAL: 'bg-blue-100 text-blue-800',
  HIGH: 'bg-orange-100 text-orange-800',
  URGENT: 'bg-red-100 text-red-800',
  CRITICAL: 'bg-purple-100 text-purple-800',
};

const getColumns = (router: ReturnType<typeof useRouter>): ColumnDef<ServiceRequest>[] => [
  {
    accessorKey: 'request_number',
    header: 'Request #',
    cell: ({ row }) => (
      <button
        onClick={() => router.push(`/service/requests/${row.original.id}`)}
        className="flex items-center gap-2 hover:text-primary transition-colors"
      >
        <Wrench className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.request_number}</span>
      </button>
    ),
  },
  {
    accessorKey: 'customer',
    header: 'Customer',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.customer?.name || 'N/A'}</div>
        <div className="text-sm text-muted-foreground">{row.original.customer?.phone}</div>
      </div>
    ),
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => (
      <span className="text-sm capitalize">
        {row.original.type.replace(/_/g, ' ').toLowerCase()}
      </span>
    ),
  },
  {
    accessorKey: 'priority',
    header: 'Priority',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[row.original.priority]}`}>
        {row.original.priority}
      </span>
    ),
  },
  {
    accessorKey: 'scheduled_date',
    header: 'Scheduled',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.scheduled_date ? formatDate(row.original.scheduled_date) : 'Not scheduled'}
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
          <DropdownMenuItem onClick={() => router.push(`/service/requests/${row.original.id}`)}>
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
          {!row.original.technician_id && (
            <DropdownMenuItem onClick={() => router.push(`/service/requests/${row.original.id}`)}>
              <UserPlus className="mr-2 h-4 w-4" />
              Assign Technician
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function ServiceRequestsPage() {
  const router = useRouter();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['service-requests', page, pageSize],
    queryFn: () => serviceRequestsApi.list({ page: page + 1, size: pageSize }),
  });

  const columns = getColumns(router);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Service Requests"
        description="Manage customer service requests and complaints"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Request
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="request_number"
        searchPlaceholder="Search requests..."
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
