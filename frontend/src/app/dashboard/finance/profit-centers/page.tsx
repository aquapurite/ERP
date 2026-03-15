'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, TrendingUp, TrendingDown, Loader2, Building, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common';
import { profitCenterApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

interface ProfitCenter {
  id: string;
  code: string;
  name: string;
  description?: string;
  parent_id?: string;
  profit_center_type: string;
  responsible_user_id?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

interface PnlData {
  profit_center: { id: string; code: string; name: string };
  period: { start_date: string; end_date: string };
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  margin_percentage: number;
  linked_cost_centers: Array<{ id: string; code: string; name: string }>;
  linked_products_count: number;
}

export default function ProfitCentersPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [pnlId, setPnlId] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    profit_center_type: 'BUSINESS_UNIT',
    is_active: true,
  });

  const { data: pcData, isLoading } = useQuery({
    queryKey: ['profit-centers'],
    queryFn: () => profitCenterApi.list({ page: 1, size: 200 }),
  });

  const { data: pnlData, isLoading: pnlLoading } = useQuery({
    queryKey: ['profit-center-pnl', pnlId],
    queryFn: () => profitCenterApi.getPnl(pnlId!),
    enabled: !!pnlId,
  });

  const pcs: ProfitCenter[] = pcData?.items || [];

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => profitCenterApi.create(payload),
    onSuccess: () => {
      toast.success('Profit center created');
      queryClient.invalidateQueries({ queryKey: ['profit-centers'] });
      setShowCreate(false);
      resetForm();
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to create');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) => profitCenterApi.update(id, payload),
    onSuccess: () => {
      toast.success('Profit center updated');
      queryClient.invalidateQueries({ queryKey: ['profit-centers'] });
      setEditId(null);
      resetForm();
    },
    onError: () => toast.error('Failed to update'),
  });

  function resetForm() {
    setFormData({ code: '', name: '', description: '', profit_center_type: 'BUSINESS_UNIT', is_active: true });
  }

  function openEdit(pc: ProfitCenter) {
    setFormData({
      code: pc.code,
      name: pc.name,
      description: pc.description || '',
      profit_center_type: pc.profit_center_type,
      is_active: pc.is_active,
    });
    setEditId(pc.id);
  }

  function handleSubmit() {
    if (!formData.code || !formData.name) {
      toast.error('Code and name are required');
      return;
    }
    if (editId) {
      updateMutation.mutate({ id: editId, payload: formData });
    } else {
      createMutation.mutate(formData);
    }
  }

  const activePcs = pcs.filter(p => p.is_active);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Profit Centers"
        description="Profit center accounting for P&L responsibility (SAP KE51)"
      />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Total Profit Centers</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{pcs.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Active</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-green-600">{activePcs.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Inactive</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-gray-500">{pcs.length - activePcs.length}</p></CardContent>
        </Card>
      </div>

      {/* Toolbar */}
      <div className="flex justify-end">
        <Button onClick={() => { resetForm(); setShowCreate(true); }}>
          <Plus className="mr-2 h-4 w-4" /> Create Profit Center
        </Button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
      ) : (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left font-medium">Code</th>
                <th className="p-3 text-left font-medium">Name</th>
                <th className="p-3 text-left font-medium">Type</th>
                <th className="p-3 text-left font-medium">Description</th>
                <th className="p-3 text-center font-medium">Active</th>
                <th className="p-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pcs.map(pc => (
                <tr key={pc.id} className="border-t hover:bg-muted/30">
                  <td className="p-3 font-mono font-medium">{pc.code}</td>
                  <td className="p-3 font-medium">{pc.name}</td>
                  <td className="p-3"><Badge variant="outline">{pc.profit_center_type}</Badge></td>
                  <td className="p-3 text-muted-foreground max-w-xs truncate">{pc.description || '-'}</td>
                  <td className="p-3 text-center">
                    <Badge variant={pc.is_active ? 'default' : 'secondary'}>{pc.is_active ? 'Active' : 'Inactive'}</Badge>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button variant="ghost" size="sm" onClick={() => setPnlId(pc.id)} title="View P&L">
                        <TrendingUp className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(pc)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {pcs.length === 0 && (
                <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No profit centers found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit Dialog */}
      <Dialog open={showCreate || !!editId} onOpenChange={() => { setShowCreate(false); setEditId(null); resetForm(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit' : 'Create'} Profit Center</DialogTitle>
            <DialogDescription>Define a profit center for P&L tracking</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Code *</Label>
                <Input value={formData.code} onChange={e => setFormData(p => ({ ...p, code: e.target.value }))} placeholder="e.g., PC-SALES" disabled={!!editId} />
              </div>
              <div>
                <Label>Name *</Label>
                <Input value={formData.name} onChange={e => setFormData(p => ({ ...p, name: e.target.value }))} placeholder="Sales Division" />
              </div>
            </div>
            <div>
              <Label>Type</Label>
              <Select value={formData.profit_center_type} onValueChange={v => setFormData(p => ({ ...p, profit_center_type: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="BUSINESS_UNIT">Business Unit</SelectItem>
                  <SelectItem value="DEPARTMENT">Department</SelectItem>
                  <SelectItem value="PRODUCT_LINE">Product Line</SelectItem>
                  <SelectItem value="REGION">Region</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={formData.description} onChange={e => setFormData(p => ({ ...p, description: e.target.value }))} rows={2} />
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={formData.is_active} onCheckedChange={v => setFormData(p => ({ ...p, is_active: v }))} />
              <Label>Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCreate(false); setEditId(null); }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
              {(createMutation.isPending || updateMutation.isPending) && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {editId ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* P&L Dialog */}
      <Dialog open={!!pnlId} onOpenChange={() => setPnlId(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Profit & Loss Report</DialogTitle>
            <DialogDescription>
              {(pnlData as PnlData)?.profit_center?.name} ({(pnlData as PnlData)?.profit_center?.code})
            </DialogDescription>
          </DialogHeader>

          {pnlLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin" /></div>
          ) : pnlData ? (
            <div className="space-y-4">
              <div className="text-xs text-muted-foreground">
                Period: {(pnlData as PnlData).period?.start_date} to {(pnlData as PnlData).period?.end_date}
              </div>

              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Revenue</CardTitle></CardHeader>
                  <CardContent>
                    <p className="text-xl font-bold text-green-600 flex items-center gap-1">
                      <TrendingUp className="h-4 w-4" />
                      {formatCurrency((pnlData as PnlData).total_revenue)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Expenses</CardTitle></CardHeader>
                  <CardContent>
                    <p className="text-xl font-bold text-red-600 flex items-center gap-1">
                      <TrendingDown className="h-4 w-4" />
                      {formatCurrency((pnlData as PnlData).total_expenses)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Net Profit</CardTitle></CardHeader>
                  <CardContent>
                    <p className={`text-xl font-bold ${(pnlData as PnlData).net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency((pnlData as PnlData).net_profit)}
                    </p>
                    <p className="text-xs text-muted-foreground">{(pnlData as PnlData).margin_percentage}% margin</p>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold mb-2">Linked Cost Centers ({(pnlData as PnlData).linked_cost_centers?.length || 0})</h4>
                  <div className="space-y-1">
                    {((pnlData as PnlData).linked_cost_centers || []).map((cc: { id: string; code: string; name: string }) => (
                      <div key={cc.id} className="flex items-center gap-2 text-sm">
                        <Building className="h-3 w-3 text-muted-foreground" />
                        <span className="font-mono text-xs">{cc.code}</span>
                        <span>{cc.name}</span>
                      </div>
                    ))}
                    {(pnlData as PnlData).linked_cost_centers?.length === 0 && (
                      <p className="text-xs text-muted-foreground">No cost centers linked. Link cost centers to see expenses here.</p>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-2">Linked Products</h4>
                  <p className="text-2xl font-bold">{(pnlData as PnlData).linked_products_count}</p>
                  <p className="text-xs text-muted-foreground">Products assigned to this profit center</p>
                </div>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
