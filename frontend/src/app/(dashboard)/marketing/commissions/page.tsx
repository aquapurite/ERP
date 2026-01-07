'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Pencil, Coins, Calculator, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatDate, formatCurrency } from '@/lib/utils';

interface CommissionPlan {
  id: string;
  name: string;
  type: 'DEALER' | 'SALES_REP' | 'REFERRAL' | 'TECHNICIAN';
  rate_type: 'PERCENTAGE' | 'FIXED';
  rate: number;
  min_threshold?: number;
  max_cap?: number;
  is_active: boolean;
  created_at: string;
}

interface CommissionPayout {
  id: string;
  beneficiary_type: 'DEALER' | 'USER' | 'TECHNICIAN';
  beneficiary_id: string;
  beneficiary_name: string;
  plan_id: string;
  plan_name: string;
  amount: number;
  status: 'PENDING' | 'APPROVED' | 'PAID' | 'CANCELLED';
  period_start: string;
  period_end: string;
  payout_date?: string;
  created_at: string;
}

const commissionsApi = {
  listPlans: async (params?: { page?: number; size?: number }) => {
    try {
      const { data } = await apiClient.get('/commissions/plans', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  listPayouts: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/commissions/payouts', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
};

const planColumns: ColumnDef<CommissionPlan>[] = [
  {
    accessorKey: 'name',
    header: 'Plan Name',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Calculator className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.name}</span>
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
    accessorKey: 'rate',
    header: 'Rate',
    cell: ({ row }) => (
      <span className="font-medium text-green-600">
        {row.original.rate_type === 'PERCENTAGE'
          ? `${row.original.rate}%`
          : formatCurrency(row.original.rate)}
      </span>
    ),
  },
  {
    accessorKey: 'threshold',
    header: 'Threshold',
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.min_threshold
          ? formatCurrency(row.original.min_threshold)
          : 'No minimum'}
      </span>
    ),
  },
  {
    accessorKey: 'cap',
    header: 'Cap',
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.max_cap
          ? formatCurrency(row.original.max_cap)
          : 'No limit'}
      </span>
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

const payoutColumns: ColumnDef<CommissionPayout>[] = [
  {
    accessorKey: 'beneficiary_name',
    header: 'Beneficiary',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Users className="h-4 w-4 text-muted-foreground" />
        <div>
          <div className="font-medium">{row.original.beneficiary_name}</div>
          <div className="text-xs text-muted-foreground capitalize">
            {row.original.beneficiary_type.toLowerCase()}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'plan_name',
    header: 'Plan',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.plan_name}</span>
    ),
  },
  {
    accessorKey: 'period',
    header: 'Period',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{formatDate(row.original.period_start)}</div>
        <div className="text-muted-foreground">to {formatDate(row.original.period_end)}</div>
      </div>
    ),
  },
  {
    accessorKey: 'amount',
    header: 'Amount',
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <Coins className="h-4 w-4 text-yellow-600" />
        <span className="font-medium">{formatCurrency(row.original.amount)}</span>
      </div>
    ),
  },
  {
    accessorKey: 'payout_date',
    header: 'Payout Date',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.payout_date ? formatDate(row.original.payout_date) : '-'}
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
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function CommissionsPage() {
  const [plansPage, setPlansPage] = useState(0);
  const [payoutsPage, setPayoutsPage] = useState(0);
  const [pageSize] = useState(10);

  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: ['commission-plans', plansPage],
    queryFn: () => commissionsApi.listPlans({ page: plansPage + 1, size: pageSize }),
  });

  const { data: payoutsData, isLoading: payoutsLoading } = useQuery({
    queryKey: ['commission-payouts', payoutsPage],
    queryFn: () => commissionsApi.listPayouts({ page: payoutsPage + 1, size: pageSize }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Commissions"
        description="Manage commission plans and payouts"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Plan
          </Button>
        }
      />

      <Tabs defaultValue="plans">
        <TabsList>
          <TabsTrigger value="plans">Commission Plans</TabsTrigger>
          <TabsTrigger value="payouts">Payouts</TabsTrigger>
        </TabsList>
        <TabsContent value="plans" className="mt-4">
          <DataTable
            columns={planColumns}
            data={plansData?.items ?? []}
            searchKey="name"
            searchPlaceholder="Search plans..."
            isLoading={plansLoading}
            manualPagination
            pageCount={plansData?.pages ?? 0}
            pageIndex={plansPage}
            pageSize={pageSize}
            onPageChange={setPlansPage}
            onPageSizeChange={() => {}}
          />
        </TabsContent>
        <TabsContent value="payouts" className="mt-4">
          <DataTable
            columns={payoutColumns}
            data={payoutsData?.items ?? []}
            searchKey="beneficiary_name"
            searchPlaceholder="Search payouts..."
            isLoading={payoutsLoading}
            manualPagination
            pageCount={payoutsData?.pages ?? 0}
            pageIndex={payoutsPage}
            pageSize={pageSize}
            onPageChange={setPayoutsPage}
            onPageSizeChange={() => {}}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
