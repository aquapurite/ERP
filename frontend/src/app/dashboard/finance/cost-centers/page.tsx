'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, Building2, Loader2, TrendingUp, Wallet, Users, Calendar, FileBarChart, FolderKanban, ChevronDown, ChevronRight, UserPlus, X, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { costCentersApi, internalOrdersApi, usersApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

interface CostCenter {
  id: string;
  code: string;
  name: string;
  description?: string;
  cost_center_type: string;
  parent_id?: string;
  parent?: { name: string; code: string };
  annual_budget: number;
  current_spend: number;
  is_active: boolean;
  created_at: string;
}

interface InternalOrder {
  id: string;
  order_number: string;
  name: string;
  description?: string;
  order_type: string;
  status: string;
  cost_center_id?: string;
  responsible_user_id?: string;
  budget_amount: number;
  actual_spend: number;
  start_date?: string;
  end_date?: string;
  created_at: string;
}

interface BudgetPeriod {
  id: string;
  period_key: string;
  budget_amount: number;
  actual_spend: number;
  utilization_pct: number;
}

interface ExpenseReportItem {
  cost_center_id: string;
  code: string;
  name: string;
  annual_budget: number;
  total_spend: number;
  budget_utilization_pct: number;
  status: string;
  gl_breakdown: { account_code: string; account_name: string; total_amount: number }[];
}

interface BudgetAlert {
  code: string;
  name: string;
  level: string;
  utilization_pct: number;
  annual_budget: number;
  total_spend: number;
  remaining: number;
}

const costCenterTypes = [
  { label: 'Department', value: 'DEPARTMENT' },
  { label: 'Location', value: 'LOCATION' },
  { label: 'Project', value: 'PROJECT' },
  { label: 'Division', value: 'DIVISION' },
  { label: 'Branch', value: 'BRANCH' },
];

const orderTypes = [
  { label: 'Project', value: 'PROJECT' },
  { label: 'Maintenance', value: 'MAINTENANCE' },
  { label: 'Marketing', value: 'MARKETING' },
  { label: 'Other', value: 'OTHER' },
];

const typeColors: Record<string, string> = {
  DEPARTMENT: 'bg-blue-100 text-blue-800',
  LOCATION: 'bg-green-100 text-green-800',
  PROJECT: 'bg-purple-100 text-purple-800',
  DIVISION: 'bg-orange-100 text-orange-800',
  BRANCH: 'bg-teal-100 text-teal-800',
};

const statusColors: Record<string, string> = {
  WITHIN_BUDGET: 'bg-green-100 text-green-800',
  WARNING: 'bg-yellow-100 text-yellow-800',
  OVER_BUDGET: 'bg-red-100 text-red-800',
};

export default function CostCentersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [activeTab, setActiveTab] = useState('cost-centers');
  const [formData, setFormData] = useState({
    id: '',
    code: '',
    name: '',
    cost_center_type: 'DEPARTMENT',
    parent_id: '',
    description: '',
    annual_budget: 0,
    is_active: true,
  });

  // Budget tab state
  const [selectedCCForBudget, setSelectedCCForBudget] = useState<string>('');
  const [budgetFiscalYear, setBudgetFiscalYear] = useState('2025-26');
  const [budgetEntries, setBudgetEntries] = useState<{ period_key: string; budget_amount: number }[]>([]);
  const [isBudgetDialogOpen, setIsBudgetDialogOpen] = useState(false);

  // Internal Orders state
  const [isIODialogOpen, setIsIODialogOpen] = useState(false);
  const [isIOEditMode, setIsIOEditMode] = useState(false);
  const [ioFormData, setIOFormData] = useState({
    id: '',
    order_number: '',
    name: '',
    description: '',
    order_type: 'PROJECT',
    cost_center_id: '',
    budget_amount: 0,
    start_date: '',
    end_date: '',
  });

  // User assignment state
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false);
  const [selectedCCForUsers, setSelectedCCForUsers] = useState<string>('');
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  // Expense report state
  const [expandedCC, setExpandedCC] = useState<string | null>(null);

  // ---- Queries ----

  const { data, isLoading } = useQuery({
    queryKey: ['cost-centers', page, pageSize],
    queryFn: () => costCentersApi.list({ page: page + 1, size: pageSize }),
  });

  const { data: budgetData, isLoading: budgetLoading } = useQuery({
    queryKey: ['cc-budgets', selectedCCForBudget, budgetFiscalYear],
    queryFn: () => costCentersApi.getBudgets(selectedCCForBudget, budgetFiscalYear),
    enabled: !!selectedCCForBudget && activeTab === 'budgets',
  });

  const { data: expenseReport, isLoading: expenseLoading } = useQuery({
    queryKey: ['cc-expense-report'],
    queryFn: () => costCentersApi.getExpenseReport(),
    enabled: activeTab === 'expense-report',
  });

  const { data: ioData, isLoading: ioLoading } = useQuery({
    queryKey: ['internal-orders'],
    queryFn: () => internalOrdersApi.list(),
    enabled: activeTab === 'internal-orders',
  });

  const { data: ccUsersData } = useQuery({
    queryKey: ['cc-users', selectedCCForUsers],
    queryFn: () => costCentersApi.getUsers(selectedCCForUsers),
    enabled: !!selectedCCForUsers && activeTab === 'access-control',
  });

  const { data: allUsers } = useQuery({
    queryKey: ['users-list'],
    queryFn: () => usersApi.list({ page: 1, size: 200, is_active: true }),
    enabled: isUserDialogOpen,
  });

  const { data: budgetAlertsData } = useQuery({
    queryKey: ['cc-budget-alerts'],
    queryFn: () => costCentersApi.getBudgetAlerts(),
  });

  const budgetAlerts: BudgetAlert[] = budgetAlertsData?.alerts || [];
  const budgetAlertTotal: number = budgetAlertsData?.total || 0;

  // ---- Mutations ----

  const createMutation = useMutation({
    mutationFn: costCentersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cost-centers'] });
      toast.success('Cost center created successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create cost center'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof costCentersApi.update>[1] }) =>
      costCentersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cost-centers'] });
      toast.success('Cost center updated successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to update cost center'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => costCentersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cost-centers'] });
      toast.success('Cost center deleted successfully');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete cost center'),
  });

  const saveBudgetMutation = useMutation({
    mutationFn: ({ ccId, fy, budgets }: { ccId: string; fy: string; budgets: { period_key: string; budget_amount: number }[] }) =>
      costCentersApi.setBudgets(ccId, fy, budgets),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cc-budgets'] });
      toast.success('Budgets saved successfully');
      setIsBudgetDialogOpen(false);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to save budgets'),
  });

  const createIOMutation = useMutation({
    mutationFn: internalOrdersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['internal-orders'] });
      toast.success('Internal order created');
      setIsIODialogOpen(false);
      resetIOForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create internal order'),
  });

  const updateIOMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof internalOrdersApi.update>[1] }) =>
      internalOrdersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['internal-orders'] });
      toast.success('Internal order updated');
      setIsIODialogOpen(false);
      resetIOForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to update internal order'),
  });

  const deleteIOMutation = useMutation({
    mutationFn: internalOrdersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['internal-orders'] });
      toast.success('Internal order deleted');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete internal order'),
  });

  const assignUsersMutation = useMutation({
    mutationFn: ({ ccId, userIds }: { ccId: string; userIds: string[] }) =>
      costCentersApi.assignUsers(ccId, userIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cc-users'] });
      toast.success('Users assigned');
      setIsUserDialogOpen(false);
      setSelectedUserIds([]);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to assign users'),
  });

  const removeUserMutation = useMutation({
    mutationFn: ({ ccId, userId }: { ccId: string; userId: string }) =>
      costCentersApi.removeUser(ccId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cc-users'] });
      toast.success('User removed');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to remove user'),
  });

  // ---- Handlers ----

  const resetForm = () => {
    setFormData({ id: '', code: '', name: '', cost_center_type: 'DEPARTMENT', parent_id: '', description: '', annual_budget: 0, is_active: true });
    setIsEditMode(false);
    setIsDialogOpen(false);
  };

  const resetIOForm = () => {
    setIOFormData({ id: '', order_number: '', name: '', description: '', order_type: 'PROJECT', cost_center_id: '', budget_amount: 0, start_date: '', end_date: '' });
    setIsIOEditMode(false);
  };

  const handleEdit = (costCenter: CostCenter) => {
    setFormData({
      id: costCenter.id, code: costCenter.code, name: costCenter.name,
      cost_center_type: costCenter.cost_center_type, parent_id: costCenter.parent_id || '',
      description: costCenter.description || '', annual_budget: costCenter.annual_budget, is_active: costCenter.is_active,
    });
    setIsEditMode(true);
    setIsDialogOpen(true);
  };

  const handleDelete = (costCenter: CostCenter) => {
    const spent = Number(costCenter.current_spend) || 0;
    if (spent > 0) {
      toast.error(`Cannot delete cost center with expenses. Deactivate it instead.`);
      return;
    }
    if (confirm(`Are you sure you want to delete cost center "${costCenter.name}"?`)) {
      deleteMutation.mutate(costCenter.id);
    }
  };

  const handleSubmit = () => {
    if (!formData.code.trim() || !formData.name.trim() || !formData.cost_center_type) {
      toast.error('Code, name, and type are required');
      return;
    }
    if (isEditMode) {
      updateMutation.mutate({ id: formData.id, data: { name: formData.name, description: formData.description || undefined, annual_budget: formData.annual_budget, is_active: formData.is_active } });
    } else {
      createMutation.mutate({ code: formData.code.toUpperCase(), name: formData.name, cost_center_type: formData.cost_center_type, parent_id: formData.parent_id || undefined, description: formData.description || undefined, annual_budget: formData.annual_budget });
    }
  };

  const getBudgetUtilization = (spent: number, budget: number) => {
    if (budget === 0) return 0;
    return Math.min((spent / budget) * 100, 100);
  };

  const openBudgetDialog = (ccId: string) => {
    setSelectedCCForBudget(ccId);
    // Generate 12 months for fiscal year
    const months = [];
    const [startYear] = budgetFiscalYear.split('-').map(Number);
    for (let m = 4; m <= 12; m++) {
      months.push({ period_key: `${startYear}-${String(m).padStart(2, '0')}`, budget_amount: 0 });
    }
    for (let m = 1; m <= 3; m++) {
      months.push({ period_key: `${startYear + 1}-${String(m).padStart(2, '0')}`, budget_amount: 0 });
    }
    setBudgetEntries(months);
    setIsBudgetDialogOpen(true);
  };

  const handleIOSubmit = () => {
    if (!ioFormData.order_number.trim() || !ioFormData.name.trim()) {
      toast.error('Order number and name are required');
      return;
    }
    if (isIOEditMode) {
      updateIOMutation.mutate({ id: ioFormData.id, data: { name: ioFormData.name, description: ioFormData.description || undefined, order_type: ioFormData.order_type, cost_center_id: ioFormData.cost_center_id || undefined, budget_amount: ioFormData.budget_amount, start_date: ioFormData.start_date || undefined, end_date: ioFormData.end_date || undefined } });
    } else {
      createIOMutation.mutate({ order_number: ioFormData.order_number, name: ioFormData.name, description: ioFormData.description || undefined, order_type: ioFormData.order_type, cost_center_id: ioFormData.cost_center_id || undefined, budget_amount: ioFormData.budget_amount, start_date: ioFormData.start_date || undefined, end_date: ioFormData.end_date || undefined });
    }
  };

  // ---- Columns ----

  const columns: ColumnDef<CostCenter>[] = [
    { accessorKey: 'code', header: 'Code', cell: ({ row }) => <span className="font-mono text-sm">{row.original.code}</span> },
    { accessorKey: 'name', header: 'Name', cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Building2 className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{row.original.name}</span>
      </div>
    )},
    { accessorKey: 'cost_center_type', header: 'Type', cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeColors[row.original.cost_center_type] || 'bg-gray-100 text-gray-800'}`}>
        {row.original.cost_center_type}
      </span>
    )},
    { accessorKey: 'parent', header: 'Parent', cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">{row.original.parent?.name || '-'}</span>
    )},
    { accessorKey: 'annual_budget', header: 'Budget', cell: ({ row }) => (
      <div className="space-y-1">
        <span className="font-medium text-sm">{formatCurrency(row.original.annual_budget)}</span>
        {row.original.annual_budget > 0 && (
          <div className="flex items-center gap-2">
            <Progress value={getBudgetUtilization(row.original.current_spend, row.original.annual_budget)} className="h-1.5 w-20" />
            <span className="text-xs text-muted-foreground">{getBudgetUtilization(row.original.current_spend, row.original.annual_budget).toFixed(0)}%</span>
          </div>
        )}
      </div>
    )},
    { accessorKey: 'current_spend', header: 'Spent', cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <TrendingUp className="h-3 w-3 text-muted-foreground" />
        <span className={`text-sm ${row.original.current_spend > row.original.annual_budget ? 'text-red-600 font-medium' : ''}`}>
          {formatCurrency(row.original.current_spend)}
        </span>
      </div>
    )},
    { accessorKey: 'is_active', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} /> },
    { id: 'actions', cell: ({ row }) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Actions</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => handleEdit(row.original)}><Pencil className="mr-2 h-4 w-4" />Edit</DropdownMenuItem>
          <DropdownMenuItem onClick={() => { setSelectedCCForBudget(row.original.id); openBudgetDialog(row.original.id); }}>
            <Calendar className="mr-2 h-4 w-4" />Monthly Budgets
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => { setSelectedCCForUsers(row.original.id); setActiveTab('access-control'); }}>
            <Users className="mr-2 h-4 w-4" />Manage Users
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => handleDelete(row.original)} className="text-red-600">
            <Trash2 className="mr-2 h-4 w-4" />Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    )},
  ];

  const parentCostCenters = (data?.items ?? data ?? []).filter(
    (cc: CostCenter) => cc.id && cc.id.trim() !== '' && cc.id !== formData.id
  );
  const costCenters = data?.items ?? data ?? [];

  const monthNames: Record<string, string> = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
    '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cost Centers"
        description="Manage cost centers, budgets, internal orders, and access control"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) resetForm(); else setIsDialogOpen(true); }}>
            <DialogTrigger asChild>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />Add Cost Center
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{isEditMode ? 'Edit Cost Center' : 'Add New Cost Center'}</DialogTitle>
                <DialogDescription>{isEditMode ? 'Update cost center details' : 'Create a new cost center'}</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Code *</Label>
                    <Input placeholder="CC001" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })} disabled={isEditMode} />
                  </div>
                  <div className="space-y-2">
                    <Label>Type *</Label>
                    <Select value={formData.cost_center_type} onValueChange={(v) => setFormData({ ...formData, cost_center_type: v })} disabled={isEditMode}>
                      <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>{costCenterTypes.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Name *</Label>
                  <Input placeholder="Sales Department" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Parent Cost Center</Label>
                  <Select value={formData.parent_id || 'none'} onValueChange={(v) => setFormData({ ...formData, parent_id: v === 'none' ? '' : v })} disabled={isEditMode}>
                    <SelectTrigger><SelectValue placeholder="Select parent" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Parent (Top Level)</SelectItem>
                      {parentCostCenters.map((cc: CostCenter) => <SelectItem key={cc.id} value={cc.id}>{cc.code} - {cc.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Annual Budget</Label>
                  <div className="relative">
                    <Wallet className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input type="number" min="0" step="1000" placeholder="0" className="pl-10" value={formData.annual_budget || ''} onChange={(e) => setFormData({ ...formData, annual_budget: parseFloat(e.target.value) || 0 })} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea placeholder="Description (optional)" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                </div>
                {isEditMode && (
                  <div className="flex items-center space-x-2">
                    <Switch id="is_active" checked={formData.is_active} onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })} />
                    <Label htmlFor="is_active">Active</Label>
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm}>Cancel</Button>
                <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
                  {(createMutation.isPending || updateMutation.isPending) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isEditMode ? 'Update' : 'Create'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {budgetAlertTotal > 0 && (
        <Card className="border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <CardTitle className="text-lg">Budget Alerts</CardTitle>
              <Badge variant="destructive" className="ml-1">{budgetAlertTotal}</Badge>
            </div>
            <CardDescription>Cost centers approaching or exceeding their budget limits</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {budgetAlerts.map((alert) => {
                const isOverBudget = alert.level === 'OVER_BUDGET';
                const barColor = isOverBudget ? 'bg-red-500' : 'bg-amber-500';
                const pct = Math.min(alert.utilization_pct, 100);
                return (
                  <div key={alert.code} className="rounded-lg border p-3 bg-white dark:bg-gray-950">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{alert.name}</span>
                        <Badge variant={isOverBudget ? 'destructive' : 'outline'} className={isOverBudget ? '' : 'border-amber-500 text-amber-700 dark:text-amber-400'}>
                          {isOverBudget ? 'Over Budget' : 'Warning'}
                        </Badge>
                      </div>
                      <span className="text-sm font-semibold">{alert.utilization_pct.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-800 mb-2">
                      <div className={`h-2 rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Budget: {formatCurrency(alert.annual_budget)}</span>
                      <span>Spent: {formatCurrency(alert.total_spend)}</span>
                      <span className={alert.remaining < 0 ? 'text-red-600 font-medium' : ''}>
                        Remaining: {formatCurrency(alert.remaining)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="cost-centers"><Building2 className="mr-1 h-4 w-4" />Cost Centers</TabsTrigger>
          <TabsTrigger value="budgets"><Calendar className="mr-1 h-4 w-4" />Monthly Budgets</TabsTrigger>
          <TabsTrigger value="expense-report"><FileBarChart className="mr-1 h-4 w-4" />Expense Report</TabsTrigger>
          <TabsTrigger value="internal-orders"><FolderKanban className="mr-1 h-4 w-4" />Internal Orders</TabsTrigger>
          <TabsTrigger value="access-control"><Users className="mr-1 h-4 w-4" />Access Control</TabsTrigger>
        </TabsList>

        {/* ===== Tab 1: Cost Centers ===== */}
        <TabsContent value="cost-centers">
          <DataTable columns={columns} data={costCenters} searchKey="name" searchPlaceholder="Search cost centers..." isLoading={isLoading} manualPagination pageCount={data?.pages ?? 0} pageIndex={page} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />
        </TabsContent>

        {/* ===== Tab 2: Monthly Budgets (Gap 6) ===== */}
        <TabsContent value="budgets">
          <Card>
            <CardHeader>
              <CardTitle>Period-Based Budget Allocation</CardTitle>
              <CardDescription>Set and view monthly budget allocations per cost center</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="space-y-2 w-64">
                  <Label>Cost Center</Label>
                  <Select value={selectedCCForBudget || 'none'} onValueChange={(v) => setSelectedCCForBudget(v === 'none' ? '' : v)}>
                    <SelectTrigger><SelectValue placeholder="Select cost center" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">-- Select --</SelectItem>
                      {costCenters.map((cc: CostCenter) => <SelectItem key={cc.id} value={cc.id}>{cc.code} - {cc.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 w-40">
                  <Label>Fiscal Year</Label>
                  <Select value={budgetFiscalYear} onValueChange={setBudgetFiscalYear}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2024-25">2024-25</SelectItem>
                      <SelectItem value="2025-26">2025-26</SelectItem>
                      <SelectItem value="2026-27">2026-27</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {selectedCCForBudget && (
                  <Button onClick={() => openBudgetDialog(selectedCCForBudget)}>
                    <Pencil className="mr-2 h-4 w-4" />Set Budgets
                  </Button>
                )}
              </div>

              {budgetLoading && <div className="flex items-center gap-2 py-8"><Loader2 className="h-5 w-5 animate-spin" />Loading budgets...</div>}

              {budgetData && budgetData.periods?.length > 0 && (
                <div className="space-y-3">
                  <div className="flex gap-4 text-sm">
                    <span>Total Budget: <strong>{formatCurrency(budgetData.total_budget)}</strong></span>
                    <span>Total Actual: <strong>{formatCurrency(budgetData.total_actual)}</strong></span>
                    <span>Utilization: <strong>{budgetData.total_utilization_pct}%</strong></span>
                  </div>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          <th className="text-left p-3">Period</th>
                          <th className="text-right p-3">Budget</th>
                          <th className="text-right p-3">Actual Spend</th>
                          <th className="text-right p-3">Utilization</th>
                          <th className="p-3 w-32">Progress</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(budgetData.periods as BudgetPeriod[]).map((p: BudgetPeriod) => {
                          const monthKey = p.period_key.split('-')[1];
                          return (
                            <tr key={p.period_key} className="border-t">
                              <td className="p-3 font-medium">{monthNames[monthKey] || monthKey} {p.period_key.split('-')[0]}</td>
                              <td className="p-3 text-right">{formatCurrency(p.budget_amount)}</td>
                              <td className="p-3 text-right">{formatCurrency(p.actual_spend)}</td>
                              <td className="p-3 text-right">
                                <span className={p.utilization_pct > 100 ? 'text-red-600 font-medium' : p.utilization_pct > 90 ? 'text-yellow-600' : ''}>
                                  {p.utilization_pct}%
                                </span>
                              </td>
                              <td className="p-3"><Progress value={Math.min(p.utilization_pct, 100)} className="h-2" /></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {budgetData && budgetData.periods?.length === 0 && selectedCCForBudget && (
                <p className="text-muted-foreground py-4">No budget periods set for this fiscal year. Click "Set Budgets" to allocate.</p>
              )}

              {!selectedCCForBudget && <p className="text-muted-foreground py-4">Select a cost center to view/edit monthly budgets.</p>}
            </CardContent>
          </Card>

          {/* Budget Edit Dialog */}
          <Dialog open={isBudgetDialogOpen} onOpenChange={setIsBudgetDialogOpen}>
            <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Set Monthly Budgets - FY {budgetFiscalYear}</DialogTitle>
                <DialogDescription>Allocate budget amounts for each month</DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-4">
                {budgetEntries.map((entry, idx) => {
                  const monthKey = entry.period_key.split('-')[1];
                  return (
                    <div key={entry.period_key} className="flex items-center gap-3">
                      <span className="w-20 text-sm font-medium">{monthNames[monthKey]} {entry.period_key.split('-')[0]}</span>
                      <Input
                        type="number"
                        min="0"
                        step="1000"
                        value={entry.budget_amount || ''}
                        onChange={(e) => {
                          const updated = [...budgetEntries];
                          updated[idx] = { ...entry, budget_amount: parseFloat(e.target.value) || 0 };
                          setBudgetEntries(updated);
                        }}
                        className="w-40"
                        placeholder="0"
                      />
                    </div>
                  );
                })}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsBudgetDialogOpen(false)}>Cancel</Button>
                <Button
                  onClick={() => saveBudgetMutation.mutate({ ccId: selectedCCForBudget, fy: budgetFiscalYear, budgets: budgetEntries.filter(b => b.budget_amount > 0) })}
                  disabled={saveBudgetMutation.isPending}
                >
                  {saveBudgetMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save Budgets
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* ===== Tab 3: Expense Report (Gap 8) ===== */}
        <TabsContent value="expense-report">
          <Card>
            <CardHeader>
              <CardTitle>Cost Center Expense Report</CardTitle>
              <CardDescription>Budget vs actual spend by cost center with GL account breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              {expenseLoading && <div className="flex items-center gap-2 py-8"><Loader2 className="h-5 w-5 animate-spin" />Loading report...</div>}

              {expenseReport && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left p-3 w-8"></th>
                        <th className="text-left p-3">Cost Center</th>
                        <th className="text-right p-3">Budget</th>
                        <th className="text-right p-3">Actual Spend</th>
                        <th className="text-right p-3">Utilization %</th>
                        <th className="p-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(expenseReport.items as ExpenseReportItem[]).map((item: ExpenseReportItem) => (
                        <>
                          <tr key={item.cost_center_id} className="border-t cursor-pointer hover:bg-muted/50" onClick={() => setExpandedCC(expandedCC === item.cost_center_id ? null : item.cost_center_id)}>
                            <td className="p-3">
                              {item.gl_breakdown.length > 0 && (
                                expandedCC === item.cost_center_id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                              )}
                            </td>
                            <td className="p-3">
                              <span className="font-mono text-xs mr-2">{item.code}</span>
                              <span className="font-medium">{item.name}</span>
                            </td>
                            <td className="p-3 text-right">{formatCurrency(item.annual_budget)}</td>
                            <td className="p-3 text-right font-medium">{formatCurrency(item.total_spend)}</td>
                            <td className="p-3 text-right">{item.budget_utilization_pct}%</td>
                            <td className="p-3">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[item.status] || 'bg-gray-100'}`}>
                                {item.status.replace('_', ' ')}
                              </span>
                            </td>
                          </tr>
                          {expandedCC === item.cost_center_id && item.gl_breakdown.length > 0 && (
                            <tr key={`${item.cost_center_id}-detail`}>
                              <td colSpan={6} className="p-0">
                                <div className="bg-muted/30 px-8 py-3">
                                  <table className="w-full text-xs">
                                    <thead>
                                      <tr>
                                        <th className="text-left py-1">GL Account</th>
                                        <th className="text-left py-1">Account Name</th>
                                        <th className="text-right py-1">Amount</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {item.gl_breakdown.map((gl) => (
                                        <tr key={gl.account_code} className="border-t border-muted">
                                          <td className="py-1 font-mono">{gl.account_code}</td>
                                          <td className="py-1">{gl.account_name}</td>
                                          <td className="py-1 text-right">{formatCurrency(gl.total_amount)}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
                      ))}
                      {(!expenseReport.items || expenseReport.items.length === 0) && (
                        <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No expense data found</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ===== Tab 4: Internal Orders (Gap 9) ===== */}
        <TabsContent value="internal-orders">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Internal Orders</CardTitle>
                <CardDescription>Project cost tracking - track budgets and actual spend per project</CardDescription>
              </div>
              <Button onClick={() => { resetIOForm(); setIsIODialogOpen(true); }}>
                <Plus className="mr-2 h-4 w-4" />New Internal Order
              </Button>
            </CardHeader>
            <CardContent>
              {ioLoading && <div className="flex items-center gap-2 py-8"><Loader2 className="h-5 w-5 animate-spin" />Loading...</div>}

              {ioData && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left p-3">Order #</th>
                        <th className="text-left p-3">Name</th>
                        <th className="text-left p-3">Type</th>
                        <th className="text-left p-3">Status</th>
                        <th className="text-right p-3">Budget</th>
                        <th className="text-right p-3">Actual</th>
                        <th className="text-left p-3">Dates</th>
                        <th className="p-3 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {((ioData.items || []) as InternalOrder[]).map((io: InternalOrder) => (
                        <tr key={io.id} className="border-t">
                          <td className="p-3 font-mono text-xs">{io.order_number}</td>
                          <td className="p-3 font-medium">{io.name}</td>
                          <td className="p-3"><Badge variant="outline">{io.order_type}</Badge></td>
                          <td className="p-3"><StatusBadge status={io.status} /></td>
                          <td className="p-3 text-right">{formatCurrency(io.budget_amount)}</td>
                          <td className="p-3 text-right">
                            <span className={io.actual_spend > io.budget_amount && io.budget_amount > 0 ? 'text-red-600 font-medium' : ''}>
                              {formatCurrency(io.actual_spend)}
                            </span>
                          </td>
                          <td className="p-3 text-xs text-muted-foreground">
                            {io.start_date || '-'} to {io.end_date || '-'}
                          </td>
                          <td className="p-3">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => {
                                  setIOFormData({ id: io.id, order_number: io.order_number, name: io.name, description: io.description || '', order_type: io.order_type, cost_center_id: io.cost_center_id || '', budget_amount: io.budget_amount, start_date: io.start_date || '', end_date: io.end_date || '' });
                                  setIsIOEditMode(true);
                                  setIsIODialogOpen(true);
                                }}>
                                  <Pencil className="mr-2 h-4 w-4" />Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => {
                                  if (io.actual_spend > 0) { toast.error('Cannot delete order with actual spend'); return; }
                                  if (confirm(`Delete internal order "${io.name}"?`)) deleteIOMutation.mutate(io.id);
                                }} className="text-red-600">
                                  <Trash2 className="mr-2 h-4 w-4" />Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </td>
                        </tr>
                      ))}
                      {(!ioData.items || ioData.items.length === 0) && (
                        <tr><td colSpan={8} className="p-8 text-center text-muted-foreground">No internal orders found</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Internal Order Dialog */}
          <Dialog open={isIODialogOpen} onOpenChange={(open) => { if (!open) { resetIOForm(); setIsIODialogOpen(false); } }}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{isIOEditMode ? 'Edit Internal Order' : 'New Internal Order'}</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Order Number *</Label>
                    <Input placeholder="IO-2026-001" value={ioFormData.order_number} onChange={(e) => setIOFormData({ ...ioFormData, order_number: e.target.value })} disabled={isIOEditMode} />
                  </div>
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <Select value={ioFormData.order_type} onValueChange={(v) => setIOFormData({ ...ioFormData, order_type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{orderTypes.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Name *</Label>
                  <Input placeholder="Project name" value={ioFormData.name} onChange={(e) => setIOFormData({ ...ioFormData, name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Cost Center</Label>
                  <Select value={ioFormData.cost_center_id || 'none'} onValueChange={(v) => setIOFormData({ ...ioFormData, cost_center_id: v === 'none' ? '' : v })}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {costCenters.map((cc: CostCenter) => <SelectItem key={cc.id} value={cc.id}>{cc.code} - {cc.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Budget Amount</Label>
                  <Input type="number" min="0" value={ioFormData.budget_amount || ''} onChange={(e) => setIOFormData({ ...ioFormData, budget_amount: parseFloat(e.target.value) || 0 })} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Start Date</Label>
                    <Input type="date" value={ioFormData.start_date} onChange={(e) => setIOFormData({ ...ioFormData, start_date: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>End Date</Label>
                    <Input type="date" value={ioFormData.end_date} onChange={(e) => setIOFormData({ ...ioFormData, end_date: e.target.value })} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea placeholder="Description" value={ioFormData.description} onChange={(e) => setIOFormData({ ...ioFormData, description: e.target.value })} />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsIODialogOpen(false)}>Cancel</Button>
                <Button onClick={handleIOSubmit} disabled={createIOMutation.isPending || updateIOMutation.isPending}>
                  {(createIOMutation.isPending || updateIOMutation.isPending) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isIOEditMode ? 'Update' : 'Create'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* ===== Tab 5: Access Control (Gap 10) ===== */}
        <TabsContent value="access-control">
          <Card>
            <CardHeader>
              <CardTitle>Cost Center Access Control</CardTitle>
              <CardDescription>Assign users to cost centers - controls which cost centers users can view and post to</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="space-y-2 w-64">
                  <Label>Cost Center</Label>
                  <Select value={selectedCCForUsers || 'none'} onValueChange={(v) => setSelectedCCForUsers(v === 'none' ? '' : v)}>
                    <SelectTrigger><SelectValue placeholder="Select cost center" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">-- Select --</SelectItem>
                      {costCenters.map((cc: CostCenter) => <SelectItem key={cc.id} value={cc.id}>{cc.code} - {cc.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                {selectedCCForUsers && (
                  <Button onClick={() => setIsUserDialogOpen(true)}>
                    <UserPlus className="mr-2 h-4 w-4" />Assign Users
                  </Button>
                )}
              </div>

              {selectedCCForUsers && ccUsersData && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left p-3">User</th>
                        <th className="text-left p-3">Email</th>
                        <th className="text-center p-3">Can View</th>
                        <th className="text-center p-3">Can Post</th>
                        <th className="p-3 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                      {((ccUsersData.items || []) as any[]).map((u: any) => (
                        <tr key={u.id} className="border-t">
                          <td className="p-3 font-medium">{u.user_name}</td>
                          <td className="p-3 text-muted-foreground">{u.user_email}</td>
                          <td className="p-3 text-center">{u.can_view ? 'Yes' : 'No'}</td>
                          <td className="p-3 text-center">{u.can_post ? 'Yes' : 'No'}</td>
                          <td className="p-3">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-red-600" onClick={() => {
                              if (confirm('Remove this user from the cost center?'))
                                removeUserMutation.mutate({ ccId: selectedCCForUsers, userId: u.user_id });
                            }}>
                              <X className="h-4 w-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                      {(!ccUsersData.items || ccUsersData.items.length === 0) && (
                        <tr><td colSpan={5} className="p-8 text-center text-muted-foreground">No users assigned. Click "Assign Users" to add.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {!selectedCCForUsers && <p className="text-muted-foreground py-4">Select a cost center to manage user access.</p>}
            </CardContent>
          </Card>

          {/* Assign Users Dialog */}
          <Dialog open={isUserDialogOpen} onOpenChange={setIsUserDialogOpen}>
            <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Assign Users to Cost Center</DialogTitle>
                <DialogDescription>Select users to grant access</DialogDescription>
              </DialogHeader>
              <div className="space-y-2 py-4">
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {(allUsers?.items || []).map((u: any) => (
                  <label key={u.id} className="flex items-center gap-3 p-2 rounded hover:bg-muted cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedUserIds.includes(u.id)}
                      onChange={(e) => {
                        if (e.target.checked) setSelectedUserIds([...selectedUserIds, u.id]);
                        else setSelectedUserIds(selectedUserIds.filter(id => id !== u.id));
                      }}
                      className="rounded"
                    />
                    <div>
                      <div className="font-medium text-sm">{u.full_name || u.email}</div>
                      <div className="text-xs text-muted-foreground">{u.email}</div>
                    </div>
                  </label>
                ))}
                {(!allUsers?.items || allUsers.items.length === 0) && (
                  <p className="text-muted-foreground text-center py-4">No users found</p>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => { setIsUserDialogOpen(false); setSelectedUserIds([]); }}>Cancel</Button>
                <Button
                  onClick={() => assignUsersMutation.mutate({ ccId: selectedCCForUsers, userIds: selectedUserIds })}
                  disabled={selectedUserIds.length === 0 || assignUsersMutation.isPending}
                >
                  {assignUsersMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Assign {selectedUserIds.length} User(s)
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>
      </Tabs>
    </div>
  );
}
