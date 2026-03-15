'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { Plus, Pencil, Trash2, Play, MoreHorizontal, Loader2, ArrowRightLeft, X } from 'lucide-react';
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
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import { costAllocationsApi, costCentersApi } from '@/lib/api';

// ---- Types ----

interface AllocationTarget {
  target_cost_center_id: string;
  percentage: number;
  target_cost_center?: { id: string; code: string; name: string };
}

interface AllocationRule {
  id: string;
  name: string;
  description?: string;
  source_cost_center_id: string;
  source_cost_center?: { id: string; code: string; name: string };
  targets: AllocationTarget[];
  is_active: boolean;
  created_at: string;
}

interface AllocationRun {
  id: string;
  period_key: string;
  fiscal_year: string;
  status: string;
  rules_applied: number;
  journal_entries_created: number;
  total_amount_allocated: number;
  run_by?: string;
  created_at: string;
  error_message?: string;
}

interface CostCenter {
  id: string;
  code: string;
  name: string;
}

// ---- Helpers ----

const statusColors: Record<string, string> = {
  COMPLETED: 'bg-green-100 text-green-800',
  RUNNING: 'bg-blue-100 text-blue-800',
  FAILED: 'bg-red-100 text-red-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
};

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ---- Component ----

export default function CostAllocationsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('rules');

  // Rule dialog state
  const [isRuleDialogOpen, setIsRuleDialogOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [ruleForm, setRuleForm] = useState({
    id: '',
    name: '',
    description: '',
    source_cost_center_id: '',
    targets: [{ target_cost_center_id: '', percentage: 0 }] as { target_cost_center_id: string; percentage: number }[],
  });

  // Run dialog state
  const [isRunDialogOpen, setIsRunDialogOpen] = useState(false);
  const [runForm, setRunForm] = useState({
    period_key: '',
    fiscal_year: '2025-26',
  });

  // ---- Queries ----

  const { data: costCentersData } = useQuery({
    queryKey: ['cost-centers-list'],
    queryFn: () => costCentersApi.list({ size: 200, is_active: true }),
  });

  const costCenters: CostCenter[] = costCentersData?.items || [];

  const { data: rulesData, isLoading: rulesLoading } = useQuery({
    queryKey: ['cost-allocation-rules'],
    queryFn: () => costAllocationsApi.listRules({ size: 100 }),
    enabled: activeTab === 'rules',
  });

  const { data: runsData, isLoading: runsLoading } = useQuery({
    queryKey: ['cost-allocation-runs'],
    queryFn: () => costAllocationsApi.listRuns({ size: 100 }),
    enabled: activeTab === 'runs',
  });

  // ---- Mutations ----

  const createRuleMutation = useMutation({
    mutationFn: (rule: {
      name: string;
      description?: string;
      source_cost_center_id: string;
      targets: { target_cost_center_id: string; percentage: number }[];
    }) => costAllocationsApi.createRule(rule),
    onSuccess: () => {
      toast.success('Allocation rule created successfully');
      queryClient.invalidateQueries({ queryKey: ['cost-allocation-rules'] });
      resetRuleForm();
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : 'Failed to create rule';
      toast.error(message);
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, ...rule }: {
      id: string;
      name?: string;
      description?: string;
      source_cost_center_id?: string;
      targets?: { target_cost_center_id: string; percentage: number }[];
      is_active?: boolean;
    }) => costAllocationsApi.updateRule(id, rule),
    onSuccess: () => {
      toast.success('Allocation rule updated successfully');
      queryClient.invalidateQueries({ queryKey: ['cost-allocation-rules'] });
      resetRuleForm();
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : 'Failed to update rule';
      toast.error(message);
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: string) => costAllocationsApi.deleteRule(id),
    onSuccess: () => {
      toast.success('Allocation rule deleted');
      queryClient.invalidateQueries({ queryKey: ['cost-allocation-rules'] });
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : 'Failed to delete rule';
      toast.error(message);
    },
  });

  const runAllocationMutation = useMutation({
    mutationFn: (params: { period_key: string; fiscal_year: string }) =>
      costAllocationsApi.runAllocation(params),
    onSuccess: () => {
      toast.success('Allocation run completed successfully');
      queryClient.invalidateQueries({ queryKey: ['cost-allocation-runs'] });
      setIsRunDialogOpen(false);
      setRunForm({ period_key: '', fiscal_year: '2025-26' });
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : 'Failed to run allocation';
      toast.error(message);
    },
  });

  // ---- Handlers ----

  function resetRuleForm() {
    setIsRuleDialogOpen(false);
    setIsEditMode(false);
    setRuleForm({
      id: '',
      name: '',
      description: '',
      source_cost_center_id: '',
      targets: [{ target_cost_center_id: '', percentage: 0 }],
    });
  }

  function openEditRule(rule: AllocationRule) {
    setIsEditMode(true);
    setRuleForm({
      id: rule.id,
      name: rule.name,
      description: rule.description || '',
      source_cost_center_id: rule.source_cost_center_id,
      targets: rule.targets.map((t) => ({
        target_cost_center_id: t.target_cost_center_id,
        percentage: t.percentage,
      })),
    });
    setIsRuleDialogOpen(true);
  }

  function addTargetRow() {
    setRuleForm((prev) => ({
      ...prev,
      targets: [...prev.targets, { target_cost_center_id: '', percentage: 0 }],
    }));
  }

  function removeTargetRow(index: number) {
    setRuleForm((prev) => ({
      ...prev,
      targets: prev.targets.filter((_, i) => i !== index),
    }));
  }

  function updateTarget(index: number, field: 'target_cost_center_id' | 'percentage', value: string | number) {
    setRuleForm((prev) => ({
      ...prev,
      targets: prev.targets.map((t, i) =>
        i === index ? { ...t, [field]: value } : t,
      ),
    }));
  }

  function handleSaveRule() {
    if (!ruleForm.name.trim()) {
      toast.error('Rule name is required');
      return;
    }
    if (!ruleForm.source_cost_center_id) {
      toast.error('Source cost center is required');
      return;
    }
    const validTargets = ruleForm.targets.filter((t) => t.target_cost_center_id);
    if (validTargets.length === 0) {
      toast.error('At least one target cost center is required');
      return;
    }
    const totalPct = validTargets.reduce((sum, t) => sum + Number(t.percentage), 0);
    if (Math.abs(totalPct - 100) > 0.01) {
      toast.error(`Target percentages must sum to 100%. Current total: ${totalPct.toFixed(2)}%`);
      return;
    }

    const payload = {
      name: ruleForm.name,
      description: ruleForm.description || undefined,
      source_cost_center_id: ruleForm.source_cost_center_id,
      targets: validTargets.map((t) => ({
        target_cost_center_id: t.target_cost_center_id,
        percentage: Number(t.percentage),
      })),
    };

    if (isEditMode) {
      updateRuleMutation.mutate({ id: ruleForm.id, ...payload });
    } else {
      createRuleMutation.mutate(payload);
    }
  }

  function handleRunAllocation() {
    if (!runForm.period_key.trim()) {
      toast.error('Period key is required (e.g. 2026-03)');
      return;
    }
    if (!runForm.fiscal_year.trim()) {
      toast.error('Fiscal year is required (e.g. 2025-26)');
      return;
    }
    runAllocationMutation.mutate(runForm);
  }

  // Cost center name lookup helper
  function getCCName(id: string): string {
    const cc = costCenters.find((c) => c.id === id);
    return cc ? `${cc.code} - ${cc.name}` : id;
  }

  // ---- Column Definitions ----

  const rulesColumns: ColumnDef<AllocationRule>[] = [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.name}</div>
          {row.original.description && (
            <div className="text-sm text-muted-foreground">{row.original.description}</div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'source_cost_center_id',
      header: 'Source CC',
      cell: ({ row }) => {
        const cc = row.original.source_cost_center;
        return cc ? `${cc.code} - ${cc.name}` : getCCName(row.original.source_cost_center_id);
      },
    },
    {
      id: 'targets',
      header: 'Targets',
      cell: ({ row }) => (
        <div className="space-y-1">
          {row.original.targets.map((t, i) => {
            const ccName = t.target_cost_center
              ? `${t.target_cost_center.code} - ${t.target_cost_center.name}`
              : getCCName(t.target_cost_center_id);
            return (
              <div key={i} className="text-sm">
                <span className="text-muted-foreground">{ccName}</span>
                <Badge variant="outline" className="ml-2">{t.percentage}%</Badge>
              </div>
            );
          })}
        </div>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => (
        <Badge className={row.original.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
          {row.original.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => openEditRule(row.original)}>
              <Pencil className="mr-2 h-4 w-4" /> Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => {
                updateRuleMutation.mutate({
                  id: row.original.id,
                  is_active: !row.original.is_active,
                });
              }}
            >
              {row.original.is_active ? 'Deactivate' : 'Activate'}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-red-600"
              onClick={() => {
                if (confirm('Are you sure you want to delete this rule?')) {
                  deleteRuleMutation.mutate(row.original.id);
                }
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const runsColumns: ColumnDef<AllocationRun>[] = [
    {
      accessorKey: 'period_key',
      header: 'Period',
    },
    {
      accessorKey: 'fiscal_year',
      header: 'Fiscal Year',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge className={statusColors[row.original.status] || 'bg-gray-100 text-gray-800'}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: 'rules_applied',
      header: 'Rules Applied',
    },
    {
      accessorKey: 'journal_entries_created',
      header: 'JEs Created',
    },
    {
      accessorKey: 'total_amount_allocated',
      header: 'Amount Allocated',
      cell: ({ row }) => {
        const val = row.original.total_amount_allocated;
        return val != null ? `Rs ${Number(val).toLocaleString('en-IN')}` : '-';
      },
    },
    {
      accessorKey: 'created_at',
      header: 'Run Date',
      cell: ({ row }) => formatDate(row.original.created_at),
    },
    {
      id: 'error',
      header: 'Error',
      cell: ({ row }) =>
        row.original.error_message ? (
          <span className="text-sm text-red-600">{row.original.error_message}</span>
        ) : (
          '-'
        ),
    },
  ];

  // ---- Derived ----

  const rules: AllocationRule[] = rulesData?.items || [];
  const runs: AllocationRun[] = runsData?.items || [];
  const targetPercentageTotal = ruleForm.targets.reduce((sum, t) => sum + Number(t.percentage || 0), 0);

  // ---- Render ----

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Cost Allocations"
        description="Define allocation rules for distributing shared costs across cost centers and run monthly allocations."
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="rules">Allocation Rules</TabsTrigger>
          <TabsTrigger value="runs">Past Runs</TabsTrigger>
        </TabsList>

        {/* ==================== RULES TAB ==================== */}
        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Allocation Rules</CardTitle>
                  <CardDescription>
                    Define how shared costs from a source cost center are distributed to target cost centers.
                  </CardDescription>
                </div>
                <Button onClick={() => { resetRuleForm(); setIsRuleDialogOpen(true); }}>
                  <Plus className="mr-2 h-4 w-4" /> New Rule
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={rulesColumns}
                data={rules}
                isLoading={rulesLoading}
                searchKey="name"
                searchPlaceholder="Search rules..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== RUNS TAB ==================== */}
        <TabsContent value="runs" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Allocation Runs</CardTitle>
                  <CardDescription>
                    History of monthly allocation runs showing journal entries created and amounts allocated.
                  </CardDescription>
                </div>
                <Button onClick={() => setIsRunDialogOpen(true)}>
                  <Play className="mr-2 h-4 w-4" /> Run Allocation
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={runsColumns}
                data={runs}
                isLoading={runsLoading}
                searchKey="period_key"
                searchPlaceholder="Search by period..."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ==================== CREATE/EDIT RULE DIALOG ==================== */}
      <Dialog open={isRuleDialogOpen} onOpenChange={(open) => { if (!open) resetRuleForm(); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{isEditMode ? 'Edit Allocation Rule' : 'Create Allocation Rule'}</DialogTitle>
            <DialogDescription>
              Define how costs from a source cost center are distributed to target cost centers.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="rule-name">Rule Name *</Label>
              <Input
                id="rule-name"
                value={ruleForm.name}
                onChange={(e) => setRuleForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g., Admin Overhead Allocation"
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="rule-desc">Description</Label>
              <Textarea
                id="rule-desc"
                value={ruleForm.description}
                onChange={(e) => setRuleForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Describe the allocation rationale..."
                rows={2}
              />
            </div>

            {/* Source Cost Center */}
            <div className="space-y-2">
              <Label>Source Cost Center *</Label>
              <Select
                value={ruleForm.source_cost_center_id}
                onValueChange={(val) => setRuleForm((f) => ({ ...f, source_cost_center_id: val }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select source cost center" />
                </SelectTrigger>
                <SelectContent>
                  {costCenters.map((cc) => (
                    <SelectItem key={cc.id} value={cc.id}>
                      {cc.code} - {cc.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Target Cost Centers */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Target Cost Centers *</Label>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={Math.abs(targetPercentageTotal - 100) < 0.01 ? 'default' : 'destructive'}
                  >
                    Total: {targetPercentageTotal.toFixed(2)}%
                  </Badge>
                  <Button type="button" variant="outline" size="sm" onClick={addTargetRow}>
                    <Plus className="mr-1 h-3 w-3" /> Add Target
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                {ruleForm.targets.map((target, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="flex-1">
                      <Select
                        value={target.target_cost_center_id}
                        onValueChange={(val) => updateTarget(index, 'target_cost_center_id', val)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select target CC" />
                        </SelectTrigger>
                        <SelectContent>
                          {costCenters
                            .filter((cc) => cc.id !== ruleForm.source_cost_center_id)
                            .map((cc) => (
                              <SelectItem key={cc.id} value={cc.id}>
                                {cc.code} - {cc.name}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="w-28">
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        step={0.01}
                        value={target.percentage || ''}
                        onChange={(e) => updateTarget(index, 'percentage', parseFloat(e.target.value) || 0)}
                        placeholder="%"
                      />
                    </div>
                    {ruleForm.targets.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeTargetRow(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={resetRuleForm}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveRule}
              disabled={createRuleMutation.isPending || updateRuleMutation.isPending}
            >
              {(createRuleMutation.isPending || updateRuleMutation.isPending) && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {isEditMode ? 'Update Rule' : 'Create Rule'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ==================== RUN ALLOCATION DIALOG ==================== */}
      <Dialog open={isRunDialogOpen} onOpenChange={setIsRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Run Monthly Allocation</DialogTitle>
            <DialogDescription>
              Run cost allocation for a specific period. This will create journal entries based on active allocation rules.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="run-period">Period Key *</Label>
              <Input
                id="run-period"
                value={runForm.period_key}
                onChange={(e) => setRunForm((f) => ({ ...f, period_key: e.target.value }))}
                placeholder="e.g., 2026-03"
              />
              <p className="text-xs text-muted-foreground">Format: YYYY-MM</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="run-fy">Fiscal Year *</Label>
              <Input
                id="run-fy"
                value={runForm.fiscal_year}
                onChange={(e) => setRunForm((f) => ({ ...f, fiscal_year: e.target.value }))}
                placeholder="e.g., 2025-26"
              />
              <p className="text-xs text-muted-foreground">Format: YYYY-YY</p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRunDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleRunAllocation}
              disabled={runAllocationMutation.isPending}
            >
              {runAllocationMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              <Play className="mr-2 h-4 w-4" /> Run Allocation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
