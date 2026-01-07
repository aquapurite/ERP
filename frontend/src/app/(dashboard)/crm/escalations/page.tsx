'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, AlertTriangle, Clock, UserCog } from 'lucide-react';
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

interface Escalation {
  id: string;
  escalation_number: string;
  type: 'SERVICE' | 'BILLING' | 'DELIVERY' | 'QUALITY' | 'OTHER';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  level: number;
  source_type: string;
  source_id?: string;
  customer_id?: string;
  customer?: { name: string; phone: string };
  subject: string;
  description?: string;
  status: 'OPEN' | 'ASSIGNED' | 'IN_PROGRESS' | 'PENDING' | 'RESOLVED' | 'CLOSED';
  assigned_to_id?: string;
  assigned_to?: { full_name: string };
  sla_breach_at?: string;
  resolved_at?: string;
  created_at: string;
}

const escalationsApi = {
  list: async (params?: { page?: number; size?: number; status?: string; priority?: string }) => {
    try {
      const { data } = await apiClient.get('/escalations', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-800',
  MEDIUM: 'bg-blue-100 text-blue-800',
  HIGH: 'bg-orange-100 text-orange-800',
  CRITICAL: 'bg-red-100 text-red-800',
};

const typeLabels: Record<string, string> = {
  SERVICE: 'Service Issue',
  BILLING: 'Billing Issue',
  DELIVERY: 'Delivery Issue',
  QUALITY: 'Quality Issue',
  OTHER: 'Other',
};

const columns: ColumnDef<Escalation>[] = [
  {
    accessorKey: 'escalation_number',
    header: 'Escalation #',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <AlertTriangle className={`h-4 w-4 ${
          row.original.priority === 'CRITICAL' ? 'text-red-600' :
          row.original.priority === 'HIGH' ? 'text-orange-600' :
          'text-muted-foreground'
        }`} />
        <div>
          <div className="font-medium">{row.original.escalation_number}</div>
          <div className="text-xs text-muted-foreground">L{row.original.level}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'subject',
    header: 'Subject',
    cell: ({ row }) => (
      <div>
        <div className="text-sm line-clamp-1">{row.original.subject}</div>
        <div className="text-xs text-muted-foreground">
          {typeLabels[row.original.type]}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'customer',
    header: 'Customer',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.customer?.name || 'N/A'}</div>
        <div className="text-muted-foreground">{row.original.customer?.phone}</div>
      </div>
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
    accessorKey: 'assigned_to',
    header: 'Assigned To',
    cell: ({ row }) => (
      <div className="flex items-center gap-1 text-sm">
        <UserCog className="h-3 w-3 text-muted-foreground" />
        {row.original.assigned_to?.full_name || 'Unassigned'}
      </div>
    ),
  },
  {
    accessorKey: 'sla',
    header: 'SLA',
    cell: ({ row }) => {
      const slaBreachAt = row.original.sla_breach_at ? new Date(row.original.sla_breach_at) : null;
      const isBreached = slaBreachAt && slaBreachAt < new Date();
      return (
        <div className={`flex items-center gap-1 text-sm ${isBreached ? 'text-red-600' : ''}`}>
          <Clock className="h-3 w-3" />
          {slaBreachAt ? (
            isBreached ? 'Breached' : formatDate(row.original.sla_breach_at!)
          ) : '-'}
        </div>
      );
    },
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
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function EscalationsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const { data, isLoading } = useQuery({
    queryKey: ['escalations', page, pageSize],
    queryFn: () => escalationsApi.list({ page: page + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Escalations"
        description="Manage escalated issues and SLA tracking"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Escalation
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="escalation_number"
        searchPlaceholder="Search escalations..."
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
