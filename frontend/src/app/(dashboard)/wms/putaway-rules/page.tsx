'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, ArrowRightLeft, ArrowUp, ArrowDown, GripVertical } from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';

interface PutawayRule {
  id: string;
  name: string;
  priority: number;
  rule_type: 'CATEGORY' | 'BRAND' | 'SKU' | 'VELOCITY' | 'SIZE' | 'WEIGHT' | 'CUSTOM';
  condition_field: string;
  condition_operator: 'EQUALS' | 'CONTAINS' | 'GREATER_THAN' | 'LESS_THAN' | 'IN' | 'NOT_IN';
  condition_value: string;
  target_zone_id: string;
  target_zone_name: string;
  target_bin_type?: string;
  warehouse_id: string;
  warehouse_name: string;
  is_active: boolean;
  items_processed: number;
}

interface RuleStats {
  total_rules: number;
  active_rules: number;
  items_processed_today: number;
  unmatched_items: number;
}

const putawayRulesApi = {
  list: async (params?: { page?: number; size?: number; warehouse_id?: string; rule_type?: string }) => {
    try {
      const { data } = await apiClient.get('/wms/putaway-rules', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<RuleStats> => {
    try {
      const { data } = await apiClient.get('/wms/putaway-rules/stats');
      return data;
    } catch {
      return { total_rules: 0, active_rules: 0, items_processed_today: 0, unmatched_items: 0 };
    }
  },
  create: async (rule: Partial<PutawayRule>) => {
    const { data } = await apiClient.post('/wms/putaway-rules', rule);
    return data;
  },
  update: async (id: string, rule: Partial<PutawayRule>) => {
    const { data } = await apiClient.put(`/wms/putaway-rules/${id}`, rule);
    return data;
  },
  updatePriority: async (id: string, priority: number) => {
    const { data } = await apiClient.put(`/wms/putaway-rules/${id}/priority`, { priority });
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/wms/putaway-rules/${id}`);
  },
};

const ruleTypeColors: Record<string, string> = {
  CATEGORY: 'bg-blue-100 text-blue-800',
  BRAND: 'bg-purple-100 text-purple-800',
  SKU: 'bg-green-100 text-green-800',
  VELOCITY: 'bg-yellow-100 text-yellow-800',
  SIZE: 'bg-orange-100 text-orange-800',
  WEIGHT: 'bg-red-100 text-red-800',
  CUSTOM: 'bg-gray-100 text-gray-800',
};

const ruleTypes = [
  { label: 'By Category', value: 'CATEGORY' },
  { label: 'By Brand', value: 'BRAND' },
  { label: 'By SKU', value: 'SKU' },
  { label: 'By Velocity (ABC)', value: 'VELOCITY' },
  { label: 'By Size', value: 'SIZE' },
  { label: 'By Weight', value: 'WEIGHT' },
  { label: 'Custom', value: 'CUSTOM' },
];

const operators = [
  { label: 'Equals', value: 'EQUALS' },
  { label: 'Contains', value: 'CONTAINS' },
  { label: 'Greater Than', value: 'GREATER_THAN' },
  { label: 'Less Than', value: 'LESS_THAN' },
  { label: 'In List', value: 'IN' },
  { label: 'Not In List', value: 'NOT_IN' },
];

const columns: ColumnDef<PutawayRule>[] = [
  {
    accessorKey: 'priority',
    header: 'Priority',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
        <span className="font-mono font-bold text-lg">{row.original.priority}</span>
      </div>
    ),
  },
  {
    accessorKey: 'name',
    header: 'Rule Name',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <ArrowRightLeft className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.warehouse_name}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'rule_type',
    header: 'Type',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${ruleTypeColors[row.original.rule_type]}`}>
        {row.original.rule_type}
      </span>
    ),
  },
  {
    accessorKey: 'condition',
    header: 'Condition',
    cell: ({ row }) => (
      <div className="text-sm font-mono bg-muted px-2 py-1 rounded">
        {row.original.condition_field} {row.original.condition_operator.toLowerCase().replace('_', ' ')} &quot;{row.original.condition_value}&quot;
      </div>
    ),
  },
  {
    accessorKey: 'target_zone_name',
    header: 'Target Zone',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.target_zone_name}</div>
        {row.original.target_bin_type && (
          <div className="text-xs text-muted-foreground">Bin Type: {row.original.target_bin_type}</div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'items_processed',
    header: 'Items Processed',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.items_processed.toLocaleString()}</span>
    ),
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />,
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const queryClient = useQueryClient();

      const moveUpMutation = useMutation({
        mutationFn: () => putawayRulesApi.updatePriority(row.original.id, row.original.priority - 1),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['putaway-rules'] });
          toast.success('Priority updated');
        },
      });

      const moveDownMutation = useMutation({
        mutationFn: () => putawayRulesApi.updatePriority(row.original.id, row.original.priority + 1),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['putaway-rules'] });
          toast.success('Priority updated');
        },
      });

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => moveUpMutation.mutate()}>
              <ArrowUp className="mr-2 h-4 w-4" />
              Move Up
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => moveDownMutation.mutate()}>
              <ArrowDown className="mr-2 h-4 w-4" />
              Move Down
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Pencil className="mr-2 h-4 w-4" />
              Edit Rule
            </DropdownMenuItem>
            <DropdownMenuItem className="text-destructive focus:text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

export default function PutawayRulesPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newRule, setNewRule] = useState<{
    name: string;
    warehouse_id: string;
    rule_type: 'CATEGORY' | 'BRAND' | 'SKU' | 'VELOCITY' | 'SIZE' | 'WEIGHT' | 'CUSTOM';
    condition_field: string;
    condition_operator: 'EQUALS' | 'CONTAINS' | 'GREATER_THAN' | 'LESS_THAN' | 'IN' | 'NOT_IN';
    condition_value: string;
    target_zone_id: string;
    target_bin_type: string;
    is_active: boolean;
  }>({
    name: '',
    warehouse_id: '',
    rule_type: 'CATEGORY',
    condition_field: 'category_name',
    condition_operator: 'EQUALS',
    condition_value: '',
    target_zone_id: '',
    target_bin_type: '',
    is_active: true,
  });

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['putaway-rules', page, pageSize],
    queryFn: () => putawayRulesApi.list({ page: page + 1, size: pageSize }),
  });

  const { data: stats } = useQuery({
    queryKey: ['putaway-rules-stats'],
    queryFn: putawayRulesApi.getStats,
  });

  const createMutation = useMutation({
    mutationFn: putawayRulesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['putaway-rules'] });
      toast.success('Putaway rule created successfully');
      setIsDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create rule');
    },
  });

  const handleCreate = () => {
    if (!newRule.name.trim()) {
      toast.error('Rule name is required');
      return;
    }
    createMutation.mutate(newRule);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Putaway Rules"
        description="Configure automatic putaway logic for incoming inventory"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Rule
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Create Putaway Rule</DialogTitle>
                <DialogDescription>
                  Define conditions to automatically route items to specific zones.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="space-y-2">
                  <Label htmlFor="name">Rule Name *</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Electronics to Zone A"
                    value={newRule.name}
                    onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="warehouse">Warehouse</Label>
                    <Select
                      value={newRule.warehouse_id}
                      onValueChange={(value) => setNewRule({ ...newRule, warehouse_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="wh1">Mumbai Main</SelectItem>
                        <SelectItem value="wh2">Delhi Hub</SelectItem>
                        <SelectItem value="wh3">Bangalore DC</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="type">Rule Type</Label>
                    <Select
                      value={newRule.rule_type}
                      onValueChange={(value: 'CATEGORY' | 'BRAND' | 'SKU' | 'VELOCITY' | 'SIZE' | 'WEIGHT' | 'CUSTOM') =>
                        setNewRule({ ...newRule, rule_type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {ruleTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Condition</CardTitle>
                    <CardDescription>When item matches this condition...</CardDescription>
                  </CardHeader>
                  <CardContent className="grid grid-cols-3 gap-2">
                    <Select
                      value={newRule.condition_field}
                      onValueChange={(value) => setNewRule({ ...newRule, condition_field: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Field" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="category_name">Category</SelectItem>
                        <SelectItem value="brand_name">Brand</SelectItem>
                        <SelectItem value="sku">SKU</SelectItem>
                        <SelectItem value="velocity_class">Velocity Class</SelectItem>
                        <SelectItem value="weight">Weight (kg)</SelectItem>
                        <SelectItem value="volume">Volume (m³)</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select
                      value={newRule.condition_operator}
                      onValueChange={(value: 'EQUALS' | 'CONTAINS' | 'GREATER_THAN' | 'LESS_THAN' | 'IN' | 'NOT_IN') =>
                        setNewRule({ ...newRule, condition_operator: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Operator" />
                      </SelectTrigger>
                      <SelectContent>
                        {operators.map((op) => (
                          <SelectItem key={op.value} value={op.value}>
                            {op.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="Value"
                      value={newRule.condition_value}
                      onChange={(e) => setNewRule({ ...newRule, condition_value: e.target.value })}
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Target Location</CardTitle>
                    <CardDescription>...route to this zone</CardDescription>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4">
                    <Select
                      value={newRule.target_zone_id}
                      onValueChange={(value) => setNewRule({ ...newRule, target_zone_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Target Zone" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="z1">Zone A - Storage</SelectItem>
                        <SelectItem value="z2">Zone B - Picking</SelectItem>
                        <SelectItem value="z3">Zone C - Bulk</SelectItem>
                        <SelectItem value="z4">Zone D - Cold Storage</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select
                      value={newRule.target_bin_type}
                      onValueChange={(value) => setNewRule({ ...newRule, target_bin_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Bin Type (optional)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="STANDARD">Standard</SelectItem>
                        <SelectItem value="BULK">Bulk</SelectItem>
                        <SelectItem value="SMALL_PARTS">Small Parts</SelectItem>
                        <SelectItem value="COLD_STORAGE">Cold Storage</SelectItem>
                      </SelectContent>
                    </Select>
                  </CardContent>
                </Card>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="is_active"
                    checked={newRule.is_active}
                    onCheckedChange={(checked) => setNewRule({ ...newRule, is_active: checked })}
                  />
                  <Label htmlFor="is_active">Active</Label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Rule'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Rules</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_rules || 0}</div>
            <p className="text-xs text-muted-foreground">{stats?.active_rules || 0} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Items Today</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.items_processed_today || 0}</div>
            <p className="text-xs text-muted-foreground">Auto-routed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unmatched</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.unmatched_items || 0}</div>
            <p className="text-xs text-muted-foreground">Manual routing needed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Match Rate</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.items_processed_today && stats.items_processed_today > 0
                ? ((stats.items_processed_today / (stats.items_processed_today + (stats.unmatched_items || 0))) * 100).toFixed(0)
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground">Automation rate</p>
          </CardContent>
        </Card>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search rules..."
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
