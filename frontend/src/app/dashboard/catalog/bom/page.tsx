'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Calculator, Trash2, Pencil, Eye, Loader2, Package, Layers } from 'lucide-react';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common';
import { bomApi, productsApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

interface BOMItem {
  id: string;
  bom_id: string;
  component_product_id: string;
  component_product_name?: string;
  component_sku?: string;
  line_number: number;
  quantity: number;
  uom: string;
  unit_cost: number;
  total_cost: number;
  scrap_percentage: number;
  is_critical: boolean;
  notes?: string;
}

interface BOM {
  id: string;
  parent_product_id: string;
  parent_product_name?: string;
  bom_number: string;
  name: string;
  bom_type: string;
  status: string;
  version: number;
  base_quantity: number;
  total_component_cost: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  items: BOMItem[];
}

interface Product {
  id: string;
  name: string;
  sku: string;
  cost_price?: number;
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  ACTIVE: 'bg-green-100 text-green-800',
  INACTIVE: 'bg-red-100 text-red-800',
};

export default function BOMPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    parent_product_id: '',
    name: '',
    bom_type: 'PRODUCTION',
    base_quantity: 1,
    notes: '',
  });
  const [formItems, setFormItems] = useState<Array<{
    component_product_id: string;
    quantity: number;
    uom: string;
    unit_cost: number;
    scrap_percentage: number;
    is_critical: boolean;
    notes: string;
  }>>([]);

  // Queries
  const { data: bomData, isLoading } = useQuery({
    queryKey: ['boms', filterStatus],
    queryFn: () => bomApi.list({ status: filterStatus || undefined, page: 1, size: 100 }),
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-list'],
    queryFn: () => productsApi.list({ page: 1, size: 500, is_active: true }),
  });

  const { data: bomDetail } = useQuery({
    queryKey: ['bom-detail', showDetail],
    queryFn: () => bomApi.getById(showDetail!),
    enabled: !!showDetail,
  });

  const products: Product[] = productsData?.items || [];
  const boms: BOM[] = bomData?.items || [];

  // Mutations
  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => bomApi.create(payload),
    onSuccess: () => {
      toast.success('BOM created successfully');
      queryClient.invalidateQueries({ queryKey: ['boms'] });
      setShowCreate(false);
      resetForm();
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to create BOM');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => bomApi.delete(id),
    onSuccess: () => {
      toast.success('BOM deleted');
      queryClient.invalidateQueries({ queryKey: ['boms'] });
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    },
  });

  const costMutation = useMutation({
    mutationFn: (id: string) => bomApi.calculateCost(id),
    onSuccess: () => {
      toast.success('Cost recalculated');
      queryClient.invalidateQueries({ queryKey: ['boms'] });
      if (showDetail) queryClient.invalidateQueries({ queryKey: ['bom-detail', showDetail] });
    },
    onError: () => toast.error('Failed to recalculate cost'),
  });

  function resetForm() {
    setFormData({ parent_product_id: '', name: '', bom_type: 'PRODUCTION', base_quantity: 1, notes: '' });
    setFormItems([]);
  }

  function addItem() {
    setFormItems(prev => [...prev, {
      component_product_id: '', quantity: 1, uom: 'PCS', unit_cost: 0,
      scrap_percentage: 0, is_critical: false, notes: '',
    }]);
  }

  function removeItem(idx: number) {
    setFormItems(prev => prev.filter((_, i) => i !== idx));
  }

  function updateItem(idx: number, field: string, value: unknown) {
    setFormItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  }

  function handleCreate() {
    if (!formData.parent_product_id || !formData.name) {
      toast.error('Parent product and name are required');
      return;
    }
    createMutation.mutate({
      ...formData,
      items: formItems.filter(i => i.component_product_id),
    });
  }

  const totalCost = boms.reduce((sum, b) => sum + (b.total_component_cost || 0), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bill of Materials"
        description="Manage product component structures (SAP CS01/CS02)"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Total BOMs</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{bomData?.total || 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Active</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-green-600">{boms.filter(b => b.status === 'ACTIVE').length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Draft</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-gray-500">{boms.filter(b => b.status === 'DRAFT').length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Total Component Cost</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{formatCurrency(totalCost)}</p></CardContent>
        </Card>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[150px]"><SelectValue placeholder="All Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="DRAFT">Draft</SelectItem>
              <SelectItem value="ACTIVE">Active</SelectItem>
              <SelectItem value="INACTIVE">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button onClick={() => { resetForm(); setShowCreate(true); }}>
          <Plus className="mr-2 h-4 w-4" /> Create BOM
        </Button>
      </div>

      {/* BOM Table */}
      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
      ) : (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="p-3 text-left font-medium">BOM Number</th>
                <th className="p-3 text-left font-medium">Name</th>
                <th className="p-3 text-left font-medium">Parent Product</th>
                <th className="p-3 text-left font-medium">Type</th>
                <th className="p-3 text-left font-medium">Status</th>
                <th className="p-3 text-left font-medium">Version</th>
                <th className="p-3 text-right font-medium">Total Cost</th>
                <th className="p-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {boms.map(bom => (
                <tr key={bom.id} className="border-t hover:bg-muted/30">
                  <td className="p-3 font-mono text-xs">{bom.bom_number}</td>
                  <td className="p-3 font-medium">{bom.name}</td>
                  <td className="p-3">{bom.parent_product_name || '-'}</td>
                  <td className="p-3"><Badge variant="outline">{bom.bom_type}</Badge></td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[bom.status] || 'bg-gray-100'}`}>
                      {bom.status}
                    </span>
                  </td>
                  <td className="p-3">v{bom.version}</td>
                  <td className="p-3 text-right font-medium">{formatCurrency(bom.total_component_cost)}</td>
                  <td className="p-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button variant="ghost" size="sm" onClick={() => setShowDetail(bom.id)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => costMutation.mutate(bom.id)}>
                        <Calculator className="h-4 w-4" />
                      </Button>
                      {bom.status === 'DRAFT' && (
                        <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(bom.id)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {boms.length === 0 && (
                <tr><td colSpan={8} className="p-8 text-center text-muted-foreground">No BOMs found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create BOM Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Bill of Materials</DialogTitle>
            <DialogDescription>Define component structure for a product</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Parent Product *</Label>
                <Select value={formData.parent_product_id} onValueChange={v => setFormData(p => ({ ...p, parent_product_id: v }))}>
                  <SelectTrigger><SelectValue placeholder="Select product" /></SelectTrigger>
                  <SelectContent>
                    {products.map(p => (
                      <SelectItem key={p.id} value={p.id}>{p.name} ({p.sku})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>BOM Name *</Label>
                <Input value={formData.name} onChange={e => setFormData(p => ({ ...p, name: e.target.value }))} placeholder="e.g., RO Assembly BOM" />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>BOM Type</Label>
                <Select value={formData.bom_type} onValueChange={v => setFormData(p => ({ ...p, bom_type: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PRODUCTION">Production</SelectItem>
                    <SelectItem value="ENGINEERING">Engineering</SelectItem>
                    <SelectItem value="SALES">Sales</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Base Quantity</Label>
                <Input type="number" value={formData.base_quantity} onChange={e => setFormData(p => ({ ...p, base_quantity: parseInt(e.target.value) || 1 }))} />
              </div>
              <div>
                <Label>Notes</Label>
                <Input value={formData.notes} onChange={e => setFormData(p => ({ ...p, notes: e.target.value }))} />
              </div>
            </div>

            {/* Component Items */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-base font-semibold">Component Items</Label>
                <Button variant="outline" size="sm" onClick={addItem}><Plus className="h-3 w-3 mr-1" /> Add Component</Button>
              </div>

              {formItems.length === 0 && (
                <p className="text-sm text-muted-foreground py-4 text-center border rounded">No components added yet. Click &quot;Add Component&quot; to start.</p>
              )}

              {formItems.map((item, idx) => (
                <div key={idx} className="border rounded p-3 mb-2 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Component #{idx + 1}</span>
                    <Button variant="ghost" size="sm" onClick={() => removeItem(idx)}><Trash2 className="h-3 w-3 text-red-500" /></Button>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <div className="col-span-2">
                      <Select value={item.component_product_id} onValueChange={v => updateItem(idx, 'component_product_id', v)}>
                        <SelectTrigger className="text-xs"><SelectValue placeholder="Select component" /></SelectTrigger>
                        <SelectContent>
                          {products.map(p => (
                            <SelectItem key={p.id} value={p.id}>{p.name} ({p.sku})</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Input type="number" placeholder="Qty" value={item.quantity} onChange={e => updateItem(idx, 'quantity', parseFloat(e.target.value) || 1)} className="text-xs" />
                    <Input type="number" placeholder="Unit Cost" value={item.unit_cost} onChange={e => updateItem(idx, 'unit_cost', parseFloat(e.target.value) || 0)} className="text-xs" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Create BOM
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* BOM Detail Dialog */}
      <Dialog open={!!showDetail} onOpenChange={() => setShowDetail(null)}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>BOM Detail: {(bomDetail as BOM)?.bom_number}</DialogTitle>
            <DialogDescription>{(bomDetail as BOM)?.name}</DialogDescription>
          </DialogHeader>

          {bomDetail && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Parent Product</p>
                  <p className="font-medium">{(bomDetail as BOM).parent_product_name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Status</p>
                  <Badge>{(bomDetail as BOM).status}</Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Total Cost</p>
                  <p className="font-bold text-lg">{formatCurrency((bomDetail as BOM).total_component_cost)}</p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Layers className="h-4 w-4" /> Components ({(bomDetail as BOM).items?.length || 0})
                </h4>
                <div className="rounded-md border">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="p-2 text-left">#</th>
                        <th className="p-2 text-left">Component</th>
                        <th className="p-2 text-left">SKU</th>
                        <th className="p-2 text-right">Qty</th>
                        <th className="p-2 text-left">UOM</th>
                        <th className="p-2 text-right">Unit Cost</th>
                        <th className="p-2 text-right">Total</th>
                        <th className="p-2 text-center">Critical</th>
                      </tr>
                    </thead>
                    <tbody>
                      {((bomDetail as BOM).items || []).map((item: BOMItem) => (
                        <tr key={item.id} className="border-t">
                          <td className="p-2">{item.line_number}</td>
                          <td className="p-2 font-medium">{item.component_product_name || '-'}</td>
                          <td className="p-2 font-mono text-xs">{item.component_sku || '-'}</td>
                          <td className="p-2 text-right">{item.quantity}</td>
                          <td className="p-2">{item.uom}</td>
                          <td className="p-2 text-right">{formatCurrency(item.unit_cost)}</td>
                          <td className="p-2 text-right font-medium">{formatCurrency(item.total_cost)}</td>
                          <td className="p-2 text-center">{item.is_critical ? <Badge variant="destructive">Yes</Badge> : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end">
                <Button variant="outline" onClick={() => costMutation.mutate((bomDetail as BOM).id)}>
                  <Calculator className="h-4 w-4 mr-2" /> Recalculate Cost
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
