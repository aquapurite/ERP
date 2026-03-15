'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  ClipboardCheck,
  Loader2,
  ChevronLeft,
  CheckCircle,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
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
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/common';
import { physicalCountApi, warehousesApi } from '@/lib/api';

function statusColor(status: string) {
  switch (status) {
    case 'PLANNED': return 'bg-blue-100 text-blue-800';
    case 'IN_PROGRESS':
    case 'COUNTING': return 'bg-yellow-100 text-yellow-800';
    case 'COMPLETED': return 'bg-green-100 text-green-800';
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800';
    case 'CANCELLED': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

function itemStatusColor(status: string) {
  switch (status) {
    case 'PENDING': return 'bg-gray-100 text-gray-800';
    case 'COUNTED': return 'bg-green-100 text-green-800';
    case 'VARIANCE': return 'bg-orange-100 text-orange-800';
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default function PhysicalCountPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedCountId, setSelectedCountId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Form state
  const [warehouseId, setWarehouseId] = useState('');
  const [countType, setCountType] = useState('FULL');
  const [plannedDate, setPlannedDate] = useState('');
  const [notes, setNotes] = useState('');

  // Counting state
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [countedQty, setCountedQty] = useState<string>('');
  const [remarks, setRemarks] = useState('');

  const { data: warehouses } = useQuery({
    queryKey: ['warehouses-list'],
    queryFn: () => warehousesApi.list({ page: 1, size: 100 }),
  });

  const { data: countsData, isLoading } = useQuery({
    queryKey: ['physical-counts', statusFilter],
    queryFn: () => physicalCountApi.list({
      status: statusFilter || undefined,
      page: 1,
      size: 50,
    }),
  });

  const { data: countDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['physical-count-detail', selectedCountId],
    queryFn: () => physicalCountApi.getById(selectedCountId!),
    enabled: !!selectedCountId,
  });

  const createMutation = useMutation({
    mutationFn: physicalCountApi.create,
    onSuccess: (data) => {
      toast.success(data.message || 'Physical count created');
      setCreateOpen(false);
      setWarehouseId('');
      setCountType('FULL');
      setPlannedDate('');
      setNotes('');
      queryClient.invalidateQueries({ queryKey: ['physical-counts'] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to create count'),
  });

  const updateItemMutation = useMutation({
    mutationFn: ({ countId, itemId, body }: { countId: string; itemId: string; body: { counted_quantity: number; remarks?: string } }) =>
      physicalCountApi.updateItem(countId, itemId, body),
    onSuccess: () => {
      toast.success('Item updated');
      setEditingItem(null);
      setCountedQty('');
      setRemarks('');
      queryClient.invalidateQueries({ queryKey: ['physical-count-detail', selectedCountId] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to update item'),
  });

  const approveMutation = useMutation({
    mutationFn: physicalCountApi.approve,
    onSuccess: (data) => {
      toast.success(data.message || 'Count approved');
      queryClient.invalidateQueries({ queryKey: ['physical-counts'] });
      queryClient.invalidateQueries({ queryKey: ['physical-count-detail', selectedCountId] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to approve'),
  });

  // Detail view
  if (selectedCountId) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setSelectedCountId(null)}>
            <ChevronLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <h1 className="text-2xl font-bold">
            {detailLoading ? 'Loading...' : `Count: ${countDetail?.count_number}`}
          </h1>
          {countDetail && (
            <Badge className={statusColor(countDetail.status)}>{countDetail.status}</Badge>
          )}
        </div>

        {detailLoading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
        ) : countDetail ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Warehouse</div>
                  <div className="text-lg font-semibold">{countDetail.warehouse_name}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Planned Date</div>
                  <div className="text-lg font-semibold">{countDetail.planned_date}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Variances</div>
                  <div className="text-lg font-semibold">{countDetail.total_variances}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Variance Value</div>
                  <div className="text-lg font-semibold">
                    {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(countDetail.variance_value || 0)}
                  </div>
                </CardContent>
              </Card>
            </div>

            {countDetail.status !== 'APPROVED' && countDetail.status !== 'CANCELLED' && (
              <div className="flex gap-2">
                <Button
                  onClick={() => approveMutation.mutate(selectedCountId!)}
                  disabled={approveMutation.isPending}
                >
                  {approveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                  Approve & Create Adjustments
                </Button>
              </div>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Count Items ({countDetail.items?.length || 0})</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>SKU</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead className="text-right">System Qty</TableHead>
                      <TableHead className="text-right">Counted Qty</TableHead>
                      <TableHead className="text-right">Variance</TableHead>
                      <TableHead className="text-right">Variance Value</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(countDetail.items || []).map((item: any) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-mono text-sm">{item.sku}</TableCell>
                        <TableCell>{item.product_name}</TableCell>
                        <TableCell className="text-right">{item.system_quantity}</TableCell>
                        <TableCell className="text-right">
                          {editingItem === item.id ? (
                            <Input
                              type="number"
                              value={countedQty}
                              onChange={(e) => setCountedQty(e.target.value)}
                              className="w-24 text-right"
                            />
                          ) : (
                            item.counted_quantity ?? '-'
                          )}
                        </TableCell>
                        <TableCell className={`text-right font-medium ${item.variance > 0 ? 'text-green-600' : item.variance < 0 ? 'text-red-600' : ''}`}>
                          {item.counted_quantity !== null ? item.variance : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {item.counted_quantity !== null
                            ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(item.variance_value)
                            : '-'}
                        </TableCell>
                        <TableCell>
                          <Badge className={itemStatusColor(item.count_status)}>{item.count_status}</Badge>
                        </TableCell>
                        <TableCell>
                          {countDetail.status !== 'APPROVED' && countDetail.status !== 'CANCELLED' && (
                            editingItem === item.id ? (
                              <div className="flex gap-1">
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    updateItemMutation.mutate({
                                      countId: selectedCountId!,
                                      itemId: item.id,
                                      body: { counted_quantity: parseInt(countedQty || '0'), remarks: remarks || undefined },
                                    });
                                  }}
                                  disabled={updateItemMutation.isPending}
                                >
                                  Save
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => { setEditingItem(null); setCountedQty(''); }}>
                                  Cancel
                                </Button>
                              </div>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setEditingItem(item.id);
                                  setCountedQty(item.counted_quantity?.toString() || '');
                                }}
                              >
                                Count
                              </Button>
                            )
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    );
  }

  // List view
  return (
    <div className="space-y-6">
      <PageHeader
        title="Physical Inventory Count"
        description="Cycle counting and physical inventory verification (SAP MI01/MI04/MI07)"
      />

      <div className="flex items-center justify-between">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Statuses</SelectItem>
            <SelectItem value="PLANNED">Planned</SelectItem>
            <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
          </SelectContent>
        </Select>

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" /> New Count</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Physical Count</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Warehouse</Label>
                <Select value={warehouseId} onValueChange={setWarehouseId}>
                  <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                  <SelectContent>
                    {((warehouses as any)?.items || (warehouses as any)?.warehouses || []).map((w: any) => (
                      <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Count Type</Label>
                <Select value={countType} onValueChange={setCountType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FULL">Full Count</SelectItem>
                    <SelectItem value="CYCLE">Cycle Count</SelectItem>
                    <SelectItem value="SPOT">Spot Check</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Planned Date</Label>
                <Input type="date" value={plannedDate} onChange={(e) => setPlannedDate(e.target.value)} />
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes..." />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button
                onClick={() => createMutation.mutate({ warehouse_id: warehouseId, count_type: countType, planned_date: plannedDate, notes: notes || undefined })}
                disabled={!warehouseId || !plannedDate || createMutation.isPending}
              >
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Create Count
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Count #</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Warehouse</TableHead>
                  <TableHead>Planned Date</TableHead>
                  <TableHead className="text-right">Items</TableHead>
                  <TableHead className="text-right">Variances</TableHead>
                  <TableHead className="text-right">Variance Value</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(countsData?.items || []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      No physical counts found. Create one to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  (countsData?.items || []).map((c: any) => (
                    <TableRow
                      key={c.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedCountId(c.id)}
                    >
                      <TableCell className="font-medium">{c.count_number}</TableCell>
                      <TableCell>{c.count_type}</TableCell>
                      <TableCell>{c.warehouse_name}</TableCell>
                      <TableCell>{c.planned_date}</TableCell>
                      <TableCell className="text-right">{c.total_items_counted}</TableCell>
                      <TableCell className="text-right">{c.total_variances}</TableCell>
                      <TableCell className="text-right">
                        {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(c.variance_value || 0)}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColor(c.status)}>{c.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
