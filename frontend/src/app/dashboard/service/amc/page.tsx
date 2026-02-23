'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import {
  MoreHorizontal,
  Plus,
  Eye,
  RefreshCw,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Download,
  Wrench,
  IndianRupee,
  TrendingUp,
  FileText,
  Bell,
  Settings,
  Search,
  Globe,
  Store,
  User,
  Clipboard,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import apiClient from '@/lib/api/client';
import { formatDate, formatCurrency } from '@/lib/utils';

// ==================== Interfaces ====================

interface AMCPlan {
  id: string;
  name: string;
  code: string;
  amc_type: string;
  contract_type: string;
  duration_months: number;
  base_price: number;
  tax_rate: number;
  services_included: number;
  parts_covered: boolean;
  labor_covered: boolean;
  emergency_support: boolean;
  priority_service: boolean;
  discount_on_parts: number;
  features_included: { name: string; quantity: number; frequency: string }[];
  parts_included: { part_name: string; covered: boolean }[];
  tenure_options: { months: number; price: number; discount_pct: number }[];
  response_sla_hours: number;
  resolution_sla_hours: number;
  grace_period_days: number;
  description: string;
  is_active: boolean;
}

interface AMCContract {
  id: string;
  contract_number: string;
  amc_type: string;
  contract_type: string;
  status: string;
  customer_id: string;
  customer_name: string;
  product_name: string;
  plan_id: string;
  plan_name: string;
  serial_number: string;
  start_date: string;
  end_date: string;
  days_remaining: number;
  total_services: number;
  services_used: number;
  services_remaining: number;
  total_amount: number;
  payment_status: string;
  next_service_due: string;
  sales_channel: string;
  sold_by_type: string;
  grace_end_date: string;
  requires_inspection: boolean;
  inspection_status: string;
  commission_amount: number;
  commission_paid: boolean;
  revenue_recognized: number;
  revenue_pending: number;
}

interface AMCStats {
  total: number;
  active_contracts: number;
  active_value: number;
  expiring_in_30_days: number;
  services_due_this_month: number;
  by_status: Record<string, number>;
  by_channel: Record<string, { count: number; value: number }>;
  commission_pending: number;
  pending_inspections: number;
}

// ==================== API ====================

const amcPageApi = {
  getStats: async (): Promise<AMCStats> => {
    try {
      const { data } = await apiClient.get('/api/v1/amc/contracts/stats');
      return data;
    } catch {
      return {
        total: 0, active_contracts: 0, active_value: 0, expiring_in_30_days: 0,
        services_due_this_month: 0, by_status: {}, by_channel: {},
        commission_pending: 0, pending_inspections: 0,
      };
    }
  },
  listPlans: async (): Promise<{ items: AMCPlan[]; total: number }> => {
    try {
      const { data } = await apiClient.get('/api/v1/amc/plans');
      return { items: data.items || [], total: data.total || 0 };
    } catch {
      return { items: [], total: 0 };
    }
  },
  listContracts: async (params?: Record<string, unknown>): Promise<{ items: AMCContract[]; total: number; pages: number }> => {
    try {
      const { data } = await apiClient.get('/api/v1/amc/contracts', { params });
      return {
        items: data.items || [],
        total: data.total || 0,
        pages: Math.ceil((data.total || 0) / ((params?.size as number) || 20)),
      };
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  createContract: async (data: Record<string, unknown>) => {
    const { data: result } = await apiClient.post('/api/v1/amc/contracts', data);
    return result;
  },
  createPlan: async (data: Record<string, unknown>) => {
    const { data: result } = await apiClient.post('/api/v1/amc/plans', data);
    return result;
  },
  activateContract: async (contractId: string, paymentMode: string = 'ONLINE', paymentReference?: string) => {
    const { data: result } = await apiClient.post(`/api/v1/amc/contracts/${contractId}/activate`, null, {
      params: { payment_mode: paymentMode, payment_reference: paymentReference }
    });
    return result;
  },
  renewContract: async (contractId: string, params?: Record<string, unknown>) => {
    const { data: result } = await apiClient.post(`/api/v1/amc/contracts/${contractId}/renew`, null, { params });
    return result;
  },
  requestInspection: async (contractId: string, params?: Record<string, unknown>) => {
    const { data: result } = await apiClient.post(`/api/v1/amc/contracts/${contractId}/request-inspection`, null, { params });
    return result;
  },
  completeInspection: async (contractId: string, data: Record<string, unknown>) => {
    const { data: result } = await apiClient.post(`/api/v1/amc/contracts/${contractId}/complete-inspection`, data);
    return result;
  },
};

// ==================== Constants ====================

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  PENDING_PAYMENT: 'bg-yellow-100 text-yellow-800',
  PENDING_INSPECTION: 'bg-purple-100 text-purple-800',
  ACTIVE: 'bg-green-100 text-green-800',
  EXPIRED: 'bg-gray-100 text-gray-800',
  CANCELLED: 'bg-red-100 text-red-800',
  RENEWED: 'bg-blue-100 text-blue-800',
};

const channelIcons: Record<string, typeof Globe> = {
  ONLINE: Globe,
  OFFLINE: Store,
  DEALER: Store,
  TECHNICIAN: Wrench,
};

const channelLabels: Record<string, string> = {
  ONLINE: 'Online',
  OFFLINE: 'Offline',
  DEALER: 'Dealer',
  TECHNICIAN: 'Technician',
};

// ==================== Component ====================

export default function AMCPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [channelFilter, setChannelFilter] = useState<string>('all');

  // Dialogs
  const [isCreateContractOpen, setIsCreateContractOpen] = useState(false);
  const [isCreatePlanOpen, setIsCreatePlanOpen] = useState(false);
  const [isRenewOpen, setIsRenewOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<AMCContract | null>(null);

  // Form states
  const [contractForm, setContractForm] = useState({
    customer_id: '',
    product_id: '',
    serial_number: '',
    plan_id: '',
    start_date: new Date().toISOString().split('T')[0],
    duration_months: '12',
    base_price: '',
    sales_channel: 'OFFLINE',
    sold_by_type: '',
    notes: '',
  });

  const [planForm, setPlanForm] = useState({
    name: '',
    code: '',
    amc_type: 'STANDARD',
    contract_type: 'COMPREHENSIVE',
    duration_months: '12',
    services_included: '2',
    base_price: '',
    tax_rate: '18',
    parts_covered: false,
    labor_covered: true,
    emergency_support: false,
    priority_service: false,
    response_sla_hours: '48',
    resolution_sla_hours: '72',
    grace_period_days: '15',
    description: '',
    // Tenure options
    tenure_1yr: '',
    tenure_2yr: '',
    tenure_3yr: '',
    tenure_4yr: '',
  });

  // Queries
  const { data: stats } = useQuery({
    queryKey: ['amc-stats'],
    queryFn: amcPageApi.getStats,
  });

  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: ['amc-plans'],
    queryFn: amcPageApi.listPlans,
  });

  const { data: contractsData, isLoading: contractsLoading } = useQuery({
    queryKey: ['amc-contracts', page, statusFilter, channelFilter],
    queryFn: () => amcPageApi.listContracts({
      page: page + 1,
      size: pageSize,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      sales_channel: channelFilter !== 'all' ? channelFilter : undefined,
    }),
  });

  // Mutations
  const createContractMutation = useMutation({
    mutationFn: async (data: typeof contractForm) => {
      return amcPageApi.createContract({
        customer_id: data.customer_id,
        product_id: data.product_id,
        serial_number: data.serial_number,
        plan_id: data.plan_id || undefined,
        start_date: data.start_date,
        duration_months: parseInt(data.duration_months),
        base_price: parseFloat(data.base_price),
        sales_channel: data.sales_channel,
        sold_by_type: data.sold_by_type || undefined,
        notes: data.notes || undefined,
        amc_type: 'STANDARD',
        total_services: 2,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amc-contracts'] });
      queryClient.invalidateQueries({ queryKey: ['amc-stats'] });
      toast.success('AMC contract created');
      setIsCreateContractOpen(false);
      setContractForm({
        customer_id: '', product_id: '', serial_number: '', plan_id: '',
        start_date: new Date().toISOString().split('T')[0], duration_months: '12',
        base_price: '', sales_channel: 'OFFLINE', sold_by_type: '', notes: '',
      });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create AMC contract');
    },
  });

  const createPlanMutation = useMutation({
    mutationFn: async (data: typeof planForm) => {
      const tenureOptions = [];
      if (data.tenure_1yr) tenureOptions.push({ months: 12, price: parseFloat(data.tenure_1yr), discount_pct: 0 });
      if (data.tenure_2yr) tenureOptions.push({ months: 24, price: parseFloat(data.tenure_2yr), discount_pct: data.tenure_1yr ? Math.round((1 - parseFloat(data.tenure_2yr) / (parseFloat(data.tenure_1yr) * 2)) * 100) : 0 });
      if (data.tenure_3yr) tenureOptions.push({ months: 36, price: parseFloat(data.tenure_3yr), discount_pct: data.tenure_1yr ? Math.round((1 - parseFloat(data.tenure_3yr) / (parseFloat(data.tenure_1yr) * 3)) * 100) : 0 });
      if (data.tenure_4yr) tenureOptions.push({ months: 48, price: parseFloat(data.tenure_4yr), discount_pct: data.tenure_1yr ? Math.round((1 - parseFloat(data.tenure_4yr) / (parseFloat(data.tenure_1yr) * 4)) * 100) : 0 });

      return amcPageApi.createPlan({
        name: data.name,
        code: data.code,
        amc_type: data.amc_type,
        contract_type: data.contract_type,
        duration_months: parseInt(data.duration_months),
        services_included: parseInt(data.services_included),
        base_price: parseFloat(data.base_price),
        tax_rate: parseFloat(data.tax_rate),
        parts_covered: data.parts_covered,
        labor_covered: data.labor_covered,
        emergency_support: data.emergency_support,
        priority_service: data.priority_service,
        response_sla_hours: parseInt(data.response_sla_hours),
        resolution_sla_hours: parseInt(data.resolution_sla_hours),
        grace_period_days: parseInt(data.grace_period_days),
        tenure_options: tenureOptions.length > 0 ? tenureOptions : undefined,
        description: data.description,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amc-plans'] });
      toast.success('AMC plan created');
      setIsCreatePlanOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create AMC plan');
    },
  });

  const activateContractMutation = useMutation({
    mutationFn: async (contractId: string) => {
      return amcPageApi.activateContract(contractId, 'ONLINE');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amc-contracts'] });
      queryClient.invalidateQueries({ queryKey: ['amc-stats'] });
      toast.success('Contract activated');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to activate contract');
    },
  });

  const renewContractMutation = useMutation({
    mutationFn: async (data: { contractId: string; planId?: string }) => {
      return amcPageApi.renewContract(data.contractId, {
        new_plan_id: data.planId || undefined,
        duration_months: 12,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amc-contracts'] });
      queryClient.invalidateQueries({ queryKey: ['amc-stats'] });
      toast.success('Contract renewed successfully');
      setIsRenewOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to renew contract');
    },
  });

  const requestInspectionMutation = useMutation({
    mutationFn: async (contractId: string) => {
      return amcPageApi.requestInspection(contractId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amc-contracts'] });
      toast.success('Inspection requested');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to request inspection');
    },
  });

  // ==================== Columns ====================

  const getColumns = (): ColumnDef<AMCContract>[] => [
    {
      accessorKey: 'contract_number',
      header: 'Contract',
      cell: ({ row }) => (
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80"
          onClick={() => router.push(`/dashboard/service/amc/${row.original.id}`)}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <div className="font-medium">{row.original.contract_number}</div>
            <div className="text-xs text-muted-foreground">
              {row.original.plan_name}
              {row.original.contract_type === 'NON_COMPREHENSIVE' && (
                <Badge variant="outline" className="ml-1 text-[10px] px-1">Non-Comp</Badge>
              )}
            </div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'customer_name',
      header: 'Customer',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.customer_name}</div>
          <div className="text-xs text-muted-foreground font-mono">{row.original.serial_number}</div>
        </div>
      ),
    },
    {
      accessorKey: 'product_name',
      header: 'Product',
      cell: ({ row }) => (
        <div className="text-sm">{row.original.product_name}</div>
      ),
    },
    {
      accessorKey: 'validity',
      header: 'Validity',
      cell: ({ row }) => {
        const isExpiringSoon = row.original.days_remaining <= 30 && row.original.status === 'ACTIVE';
        return (
          <div className="flex items-center gap-1">
            {isExpiringSoon && <AlertTriangle className="h-3 w-3 text-orange-500" />}
            <div className="text-sm">
              <div>{formatDate(row.original.end_date)}</div>
              <div className={`text-xs ${isExpiringSoon ? 'text-orange-600 font-medium' : 'text-muted-foreground'}`}>
                {row.original.days_remaining > 0 ? `${row.original.days_remaining} days left` : 'Expired'}
              </div>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'visits',
      header: 'Visits',
      cell: ({ row }) => {
        const total = row.original.total_services || 1;
        const percentage = (row.original.services_used / total) * 100;
        return (
          <div className="space-y-1">
            <div className="text-sm">
              <span className="font-medium">{row.original.services_used}</span>
              <span className="text-muted-foreground"> / {total}</span>
            </div>
            <Progress value={percentage} className="h-1.5 w-16" />
          </div>
        );
      },
    },
    {
      accessorKey: 'sales_channel',
      header: 'Channel',
      cell: ({ row }) => {
        const channel = row.original.sales_channel || 'OFFLINE';
        const ChannelIcon = channelIcons[channel] || Store;
        return (
          <div className="flex items-center gap-1 text-sm">
            <ChannelIcon className="h-3 w-3 text-muted-foreground" />
            <span>{channelLabels[channel] || channel}</span>
          </div>
        );
      },
    },
    {
      accessorKey: 'amount',
      header: 'Amount',
      cell: ({ row }) => (
        <div className="font-medium">{formatCurrency(row.original.total_amount)}</div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge className={statusColors[row.original.status] ?? 'bg-gray-100 text-gray-800'}>
          {row.original.status?.replace(/_/g, ' ') ?? '-'}
        </Badge>
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
            <DropdownMenuItem onClick={() => router.push(`/dashboard/service/amc/${row.original.id}`)}>
              <Eye className="mr-2 h-4 w-4" /> View Details
            </DropdownMenuItem>
            {row.original.status === 'DRAFT' && (
              <DropdownMenuItem onClick={() => activateContractMutation.mutate(row.original.id)}>
                <CheckCircle className="mr-2 h-4 w-4" /> Activate
              </DropdownMenuItem>
            )}
            {row.original.status === 'ACTIVE' && (
              <DropdownMenuItem>
                <Wrench className="mr-2 h-4 w-4" /> Schedule Service
              </DropdownMenuItem>
            )}
            {(row.original.status === 'EXPIRED' || row.original.status === 'ACTIVE') && (
              <DropdownMenuItem onClick={() => {
                setSelectedContract(row.original);
                setIsRenewOpen(true);
              }}>
                <RefreshCw className="mr-2 h-4 w-4" /> Renew Contract
              </DropdownMenuItem>
            )}
            {row.original.requires_inspection && row.original.inspection_status !== 'COMPLETED' && (
              <DropdownMenuItem onClick={() => requestInspectionMutation.mutate(row.original.id)}>
                <Search className="mr-2 h-4 w-4" /> Request Inspection
              </DropdownMenuItem>
            )}
            <DropdownMenuItem>
              <FileText className="mr-2 h-4 w-4" /> Download Contract
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const planColumns: ColumnDef<AMCPlan>[] = [
    {
      accessorKey: 'name',
      header: 'Plan',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-xs text-muted-foreground">{row.original.code}</div>
        </div>
      ),
    },
    {
      accessorKey: 'contract_type',
      header: 'Type',
      cell: ({ row }) => (
        <Badge variant="outline" className="text-xs">
          {row.original.contract_type === 'NON_COMPREHENSIVE' ? 'Non-Comp' : 'Comprehensive'}
        </Badge>
      ),
    },
    {
      accessorKey: 'duration_months',
      header: 'Duration',
      cell: ({ row }) => `${row.original.duration_months} months`,
    },
    {
      accessorKey: 'services_included',
      header: 'Visits',
    },
    {
      accessorKey: 'base_price',
      header: 'Price',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{formatCurrency(row.original.base_price)}</div>
          {row.original.tenure_options?.length > 0 && (
            <div className="text-xs text-muted-foreground">
              {row.original.tenure_options.length} tenure options
            </div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'sla',
      header: 'SLA',
      cell: ({ row }) => (
        <div className="text-xs">
          <div>Response: {row.original.response_sla_hours}h</div>
          <div>Resolution: {row.original.resolution_sla_hours}h</div>
        </div>
      ),
    },
    {
      accessorKey: 'coverage',
      header: 'Coverage',
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.parts_covered && <Badge variant="outline" className="text-xs">Parts</Badge>}
          {row.original.labor_covered && <Badge variant="outline" className="text-xs">Labor</Badge>}
          {row.original.emergency_support && <Badge className="text-xs bg-orange-100 text-orange-800">Emergency</Badge>}
          {row.original.priority_service && <Badge className="text-xs bg-purple-100 text-purple-800">Priority</Badge>}
        </div>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? 'default' : 'secondary'}>
          {row.original.is_active ? 'Active' : 'Inactive'}
        </Badge>
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
            <DropdownMenuItem><Eye className="mr-2 h-4 w-4" /> View Details</DropdownMenuItem>
            <DropdownMenuItem><Settings className="mr-2 h-4 w-4" /> Edit Plan</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="AMC Management"
        description="Annual Maintenance Contracts - Online & Offline Sales"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setIsCreatePlanOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> New Plan
            </Button>
            <Button onClick={() => setIsCreateContractOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> New Contract
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Contracts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_contracts || 0}</div>
            <div className="text-sm text-muted-foreground">of {stats?.total || 0} total</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(stats?.active_value || 0)}</div>
            <div className="text-sm text-muted-foreground">Total contract value</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Expiring Soon</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.expiring_in_30_days || 0}</div>
            <div className="text-sm text-muted-foreground">Within 30 days</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Commission Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(stats?.commission_pending || 0)}</div>
            <div className="text-sm text-muted-foreground">Unpaid commissions</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending Inspections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats?.pending_inspections || 0}</div>
            <div className="text-sm text-muted-foreground">Lapsed contracts</div>
          </CardContent>
        </Card>
      </div>

      {/* Channel-wise Breakdown */}
      {stats?.by_channel && Object.keys(stats.by_channel).length > 0 && (
        <div className="grid gap-4 md:grid-cols-4">
          {Object.entries(stats.by_channel).map(([channel, data]) => {
            const ChannelIcon = channelIcons[channel] || Store;
            return (
              <Card key={channel}>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <ChannelIcon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{channelLabels[channel] || channel}</span>
                  </div>
                  <div className="mt-2 flex justify-between">
                    <span className="text-lg font-bold">{data.count}</span>
                    <span className="text-sm text-muted-foreground">{formatCurrency(data.value)}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Main Tabs */}
      <Tabs defaultValue="contracts">
        <TabsList>
          <TabsTrigger value="contracts">Contracts</TabsTrigger>
          <TabsTrigger value="plans">AMC Plans</TabsTrigger>
          <TabsTrigger value="renewals">Due for Renewal</TabsTrigger>
        </TabsList>

        <TabsContent value="contracts" className="mt-4 space-y-4">
          <div className="flex items-center gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="PENDING_PAYMENT">Pending Payment</SelectItem>
                <SelectItem value="PENDING_INSPECTION">Pending Inspection</SelectItem>
                <SelectItem value="EXPIRED">Expired</SelectItem>
                <SelectItem value="RENEWED">Renewed</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            <Select value={channelFilter} onValueChange={setChannelFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by channel" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Channels</SelectItem>
                <SelectItem value="ONLINE">Online</SelectItem>
                <SelectItem value="OFFLINE">Offline</SelectItem>
                <SelectItem value="DEALER">Dealer</SelectItem>
                <SelectItem value="TECHNICIAN">Technician</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" /> Export
            </Button>
          </div>
          <DataTable<AMCContract, unknown>
            columns={getColumns()}
            data={contractsData?.items ?? []}
            searchKey="contract_number"
            searchPlaceholder="Search contracts..."
            isLoading={contractsLoading}
            manualPagination
            pageCount={contractsData?.pages ?? 0}
            pageIndex={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={() => {}}
          />
        </TabsContent>

        <TabsContent value="plans" className="mt-4">
          <DataTable<AMCPlan, unknown>
            columns={planColumns}
            data={plansData?.items ?? []}
            searchKey="name"
            searchPlaceholder="Search plans..."
            isLoading={plansLoading}
          />
        </TabsContent>

        <TabsContent value="renewals" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Contracts Due for Renewal</CardTitle>
              <CardDescription>Contracts expiring in the next 30 days</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Current Plan</TableHead>
                    <TableHead>Channel</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contractsData?.items
                    .filter((c: AMCContract) => (c.days_remaining <= 30 && c.days_remaining >= 0) || c.status === 'EXPIRED')
                    .map((contract: AMCContract) => (
                      <TableRow key={contract.id}>
                        <TableCell className="font-mono">{contract.contract_number}</TableCell>
                        <TableCell>{contract.customer_name}</TableCell>
                        <TableCell>{contract.product_name}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3 text-orange-500" />
                            <span className="text-orange-600 font-medium">
                              {contract.days_remaining > 0 ? `${contract.days_remaining} days` : 'Expired'}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>{contract.plan_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {channelLabels[contract.sales_channel] || contract.sales_channel}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            {contract.requires_inspection && contract.inspection_status !== 'COMPLETED' ? (
                              <Button size="sm" variant="outline" onClick={() => requestInspectionMutation.mutate(contract.id)}>
                                <Search className="mr-1 h-3 w-3" /> Inspect
                              </Button>
                            ) : (
                              <Button size="sm" variant="outline" onClick={() => {
                                setSelectedContract(contract);
                                setIsRenewOpen(true);
                              }}>
                                <RefreshCw className="mr-1 h-3 w-3" /> Renew
                              </Button>
                            )}
                            <Button size="sm" variant="ghost">
                              <Bell className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  {(!contractsData?.items || contractsData.items.filter((c: AMCContract) => c.days_remaining <= 30 || c.status === 'EXPIRED').length === 0) && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No contracts due for renewal
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Contract Dialog */}
      <Dialog open={isCreateContractOpen} onOpenChange={setIsCreateContractOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create AMC Contract</DialogTitle>
            <DialogDescription>Create a new Annual Maintenance Contract</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4 max-h-[60vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Customer ID</Label>
                <Input
                  placeholder="Customer UUID"
                  value={contractForm.customer_id}
                  onChange={(e) => setContractForm({ ...contractForm, customer_id: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Product ID</Label>
                <Input
                  placeholder="Product UUID"
                  value={contractForm.product_id}
                  onChange={(e) => setContractForm({ ...contractForm, product_id: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Serial Number</Label>
              <Input
                placeholder="Product serial number"
                value={contractForm.serial_number}
                onChange={(e) => setContractForm({ ...contractForm, serial_number: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>AMC Plan</Label>
              <Select
                value={contractForm.plan_id}
                onValueChange={(value) => {
                  const plan = plansData?.items.find((p: AMCPlan) => p.id === value);
                  setContractForm({
                    ...contractForm,
                    plan_id: value,
                    base_price: plan ? String(plan.base_price) : contractForm.base_price,
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a plan (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {plansData?.items.map((plan: AMCPlan) => (
                    <SelectItem key={plan.id} value={plan.id}>
                      {plan.name} - {formatCurrency(plan.base_price)} ({plan.contract_type === 'NON_COMPREHENSIVE' ? 'Non-Comp' : 'Comprehensive'})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Start Date</Label>
                <Input
                  type="date"
                  value={contractForm.start_date}
                  onChange={(e) => setContractForm({ ...contractForm, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Duration (months)</Label>
                <Select value={contractForm.duration_months} onValueChange={(v) => setContractForm({ ...contractForm, duration_months: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="12">12 months</SelectItem>
                    <SelectItem value="24">24 months</SelectItem>
                    <SelectItem value="36">36 months</SelectItem>
                    <SelectItem value="48">48 months</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Base Price</Label>
                <Input
                  type="number"
                  placeholder="2999"
                  value={contractForm.base_price}
                  onChange={(e) => setContractForm({ ...contractForm, base_price: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Sales Channel</Label>
                <Select value={contractForm.sales_channel} onValueChange={(v) => setContractForm({ ...contractForm, sales_channel: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ONLINE">Online (D2C)</SelectItem>
                    <SelectItem value="OFFLINE">Offline (Walk-in/Call)</SelectItem>
                    <SelectItem value="DEALER">Dealer Sale</SelectItem>
                    <SelectItem value="TECHNICIAN">Technician Field Sale</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Sold By</Label>
                <Select value={contractForm.sold_by_type} onValueChange={(v) => setContractForm({ ...contractForm, sold_by_type: v })}>
                  <SelectTrigger><SelectValue placeholder="Select seller type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USER">Internal Staff</SelectItem>
                    <SelectItem value="DEALER">Dealer</SelectItem>
                    <SelectItem value="TECHNICIAN">Technician</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                placeholder="Additional notes..."
                value={contractForm.notes}
                onChange={(e) => setContractForm({ ...contractForm, notes: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateContractOpen(false)}>Cancel</Button>
            <Button onClick={() => createContractMutation.mutate(contractForm)}>Create Contract</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Plan Dialog */}
      <Dialog open={isCreatePlanOpen} onOpenChange={setIsCreatePlanOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create AMC Plan</DialogTitle>
            <DialogDescription>Define a new AMC plan with pricing, SLA, and coverage details</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4 max-h-[60vh] overflow-y-auto">
            {/* Basic Info */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Plan Name</Label>
                <Input placeholder="e.g., Premium Care" value={planForm.name} onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Plan Code</Label>
                <Input placeholder="e.g., AMC-PREM" value={planForm.code} onChange={(e) => setPlanForm({ ...planForm, code: e.target.value.toUpperCase() })} />
              </div>
              <div className="space-y-2">
                <Label>AMC Type</Label>
                <Select value={planForm.amc_type} onValueChange={(v) => setPlanForm({ ...planForm, amc_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="STANDARD">Standard</SelectItem>
                    <SelectItem value="COMPREHENSIVE">Comprehensive</SelectItem>
                    <SelectItem value="EXTENDED_WARRANTY">Extended Warranty</SelectItem>
                    <SelectItem value="PLATINUM">Platinum</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Contract Type */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Contract Type</Label>
                <Select value={planForm.contract_type} onValueChange={(v) => setPlanForm({ ...planForm, contract_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="COMPREHENSIVE">Comprehensive (Parts + Labor)</SelectItem>
                    <SelectItem value="NON_COMPREHENSIVE">Non-Comprehensive (Labor Only)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Default Duration</Label>
                <Select value={planForm.duration_months} onValueChange={(v) => setPlanForm({ ...planForm, duration_months: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="12">12 months</SelectItem>
                    <SelectItem value="24">24 months</SelectItem>
                    <SelectItem value="36">36 months</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Pricing & Services */}
            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label>Base Price (1yr)</Label>
                <Input type="number" placeholder="2999" value={planForm.base_price} onChange={(e) => setPlanForm({ ...planForm, base_price: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Tax Rate (%)</Label>
                <Input type="number" value={planForm.tax_rate} onChange={(e) => setPlanForm({ ...planForm, tax_rate: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Visits Included</Label>
                <Input type="number" value={planForm.services_included} onChange={(e) => setPlanForm({ ...planForm, services_included: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Grace Period (days)</Label>
                <Input type="number" value={planForm.grace_period_days} onChange={(e) => setPlanForm({ ...planForm, grace_period_days: e.target.value })} />
              </div>
            </div>

            {/* Multi-Year Tenure Pricing */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Multi-Year Tenure Pricing (optional)</Label>
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">1 Year</Label>
                  <Input type="number" placeholder="2999" value={planForm.tenure_1yr} onChange={(e) => setPlanForm({ ...planForm, tenure_1yr: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">2 Years</Label>
                  <Input type="number" placeholder="5499" value={planForm.tenure_2yr} onChange={(e) => setPlanForm({ ...planForm, tenure_2yr: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">3 Years</Label>
                  <Input type="number" placeholder="7999" value={planForm.tenure_3yr} onChange={(e) => setPlanForm({ ...planForm, tenure_3yr: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">4 Years</Label>
                  <Input type="number" placeholder="9999" value={planForm.tenure_4yr} onChange={(e) => setPlanForm({ ...planForm, tenure_4yr: e.target.value })} />
                </div>
              </div>
            </div>

            {/* SLA */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Response SLA (hours)</Label>
                <Input type="number" value={planForm.response_sla_hours} onChange={(e) => setPlanForm({ ...planForm, response_sla_hours: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Resolution SLA (hours)</Label>
                <Input type="number" value={planForm.resolution_sla_hours} onChange={(e) => setPlanForm({ ...planForm, resolution_sla_hours: e.target.value })} />
              </div>
            </div>

            {/* Coverage */}
            <div className="space-y-2">
              <Label>Coverage</Label>
              <div className="flex gap-6">
                <div className="flex items-center space-x-2">
                  <Checkbox id="parts" checked={planForm.parts_covered} onCheckedChange={(c) => setPlanForm({ ...planForm, parts_covered: !!c })} />
                  <Label htmlFor="parts">Parts</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="labor" checked={planForm.labor_covered} onCheckedChange={(c) => setPlanForm({ ...planForm, labor_covered: !!c })} />
                  <Label htmlFor="labor">Labor</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="emergency" checked={planForm.emergency_support} onCheckedChange={(c) => setPlanForm({ ...planForm, emergency_support: !!c })} />
                  <Label htmlFor="emergency">Emergency</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="priority" checked={planForm.priority_service} onCheckedChange={(c) => setPlanForm({ ...planForm, priority_service: !!c })} />
                  <Label htmlFor="priority">Priority</Label>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea placeholder="Plan benefits and details..." value={planForm.description} onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreatePlanOpen(false)}>Cancel</Button>
            <Button onClick={() => createPlanMutation.mutate(planForm)}>Create Plan</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Renew Contract Dialog */}
      <Dialog open={isRenewOpen} onOpenChange={setIsRenewOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Renew AMC Contract</DialogTitle>
            <DialogDescription>
              {selectedContract && `Renewing contract ${selectedContract.contract_number}`}
            </DialogDescription>
          </DialogHeader>
          {selectedContract && (
            <div className="space-y-4 py-4">
              <div className="rounded-lg bg-muted p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Customer</span>
                  <span className="font-medium">{selectedContract.customer_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Product</span>
                  <span>{selectedContract.product_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Current Plan</span>
                  <span>{selectedContract.plan_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Expires</span>
                  <span>{formatDate(selectedContract.end_date)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type</span>
                  <Badge variant="outline" className="text-xs">
                    {selectedContract.contract_type === 'NON_COMPREHENSIVE' ? 'Non-Comprehensive' : 'Comprehensive'}
                  </Badge>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Renewal Plan</Label>
                <Select defaultValue={selectedContract.plan_id}>
                  <SelectTrigger>
                    <SelectValue placeholder="Same plan" />
                  </SelectTrigger>
                  <SelectContent>
                    {plansData?.items.map((plan: AMCPlan) => (
                      <SelectItem key={plan.id} value={plan.id}>
                        {plan.name} - {formatCurrency(plan.base_price)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRenewOpen(false)}>Cancel</Button>
            <Button onClick={() => selectedContract && renewContractMutation.mutate({
              contractId: selectedContract.id,
              planId: selectedContract.plan_id
            })}>
              <RefreshCw className="mr-2 h-4 w-4" /> Renew Contract
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
