'use client';

import { useState, useEffect, useCallback } from 'react';
import { batchApi, productsApi, warehousesApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  Plus,
  Search,
  RefreshCw,
  AlertTriangle,
  Clock,
  Package,
  Layers,
  ArrowDownUp,
} from 'lucide-react';

interface BatchItem {
  id: string;
  batch_number: string;
  product_id: string;
  product_name: string | null;
  product_sku: string | null;
  warehouse_id: string;
  warehouse_name: string | null;
  batch_status: string;
  manufacturing_date: string | null;
  expiry_date: string | null;
  days_until_expiry: number | null;
  vendor_batch_number: string | null;
  quality_grade: string | null;
  quantity_received: number;
  quantity_available: number;
  quantity_reserved: number;
  quantity_issued: number;
  unit_cost: number;
  total_value: number;
  shelf_life_days: number | null;
  notes: string | null;
  created_at: string | null;
}

interface ExpiryAlert {
  id: string;
  batch_number: string;
  product_name: string | null;
  product_sku: string | null;
  warehouse_name: string | null;
  expiry_date: string | null;
  days_until_expiry: number | null;
  severity: string;
  quantity_available: number;
  total_value: number;
  quality_grade: string | null;
}

interface PickResult {
  batch_id: string;
  batch_number: string;
  pick_quantity: number;
  quantity_available: number;
  expiry_date: string | null;
  manufacturing_date: string | null;
  quality_grade: string | null;
  days_until_expiry: number | null;
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'UNRESTRICTED':
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Unrestricted</Badge>;
    case 'RESTRICTED':
      return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">Restricted</Badge>;
    case 'BLOCKED':
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Blocked</Badge>;
    case 'EXPIRED':
      return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">Expired</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function getExpirySeverityBadge(severity: string, days: number | null) {
  const label = days !== null ? `${days}d` : 'N/A';
  switch (severity) {
    case 'RED':
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">{days !== null && days <= 0 ? 'Expired' : label}</Badge>;
    case 'YELLOW':
      return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">{label}</Badge>;
    case 'GREEN':
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">{label}</Badge>;
    default:
      return <Badge variant="outline">{label}</Badge>;
  }
}

export default function BatchManagementPage() {
  const [activeTab, setActiveTab] = useState('master');
  const [batches, setBatches] = useState<BatchItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterProductId, setFilterProductId] = useState('');
  const [filterWarehouseId, setFilterWarehouseId] = useState('');

  // Expiry alerts
  const [alerts, setAlerts] = useState<ExpiryAlert[]>([]);
  const [alertSummary, setAlertSummary] = useState({ red: 0, yellow: 0, green: 0 });
  const [daysAhead, setDaysAhead] = useState(30);

  // Picking
  const [pickProductId, setPickProductId] = useState('');
  const [pickWarehouseId, setPickWarehouseId] = useState('');
  const [pickQuantity, setPickQuantity] = useState(0);
  const [pickStrategy, setPickStrategy] = useState('FEFO');
  const [pickResults, setPickResults] = useState<PickResult[]>([]);
  const [pickMeta, setPickMeta] = useState<{ total_picked: number; shortfall: number; fully_fulfilled: boolean } | null>(null);

  // Create dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createForm, setCreateForm] = useState({
    product_id: '',
    warehouse_id: '',
    batch_number: '',
    manufacturing_date: '',
    expiry_date: '',
    vendor_batch_number: '',
    quality_grade: 'A',
    quantity_received: 0,
    unit_cost: 0,
    notes: '',
  });

  // Products & warehouses for dropdowns
  const [products, setProducts] = useState<{ id: string; name: string; sku: string }[]>([]);
  const [warehouses, setWarehouses] = useState<{ id: string; name: string }[]>([]);

  // Load products and warehouses
  useEffect(() => {
    const loadMasterData = async () => {
      try {
        const [prodRes, whRes] = await Promise.all([
          productsApi.list({ size: 200, is_active: true }),
          warehousesApi.list({ size: 100 }),
        ]);
        setProducts((prodRes.items || []).map((p: { id: string; name: string; sku: string }) => ({
          id: p.id, name: p.name, sku: p.sku,
        })));
        setWarehouses((whRes.items || whRes || []).map((w: { id: string; name: string }) => ({
          id: w.id, name: w.name,
        })));
      } catch {
        // Silently handle - dropdowns will be empty
      }
    };
    loadMasterData();
  }, []);

  // Load batches
  const loadBatches = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean> = { page, size: 20 };
      if (search) params.search = search;
      if (filterStatus) params.batch_status = filterStatus;
      if (filterProductId) params.product_id = filterProductId;
      if (filterWarehouseId) params.warehouse_id = filterWarehouseId;
      const res = await batchApi.list(params);
      setBatches(res.items || []);
      setTotal(res.total || 0);
    } catch {
      toast.error('Failed to load batches');
    } finally {
      setLoading(false);
    }
  }, [page, search, filterStatus, filterProductId, filterWarehouseId]);

  useEffect(() => {
    if (activeTab === 'master') loadBatches();
  }, [activeTab, loadBatches]);

  // Load expiry alerts
  const loadAlerts = useCallback(async () => {
    try {
      const res = await batchApi.getExpiryAlerts({ days_ahead: daysAhead });
      setAlerts(res.alerts || []);
      setAlertSummary(res.summary || { red: 0, yellow: 0, green: 0 });
    } catch {
      toast.error('Failed to load expiry alerts');
    }
  }, [daysAhead]);

  useEffect(() => {
    if (activeTab === 'expiry') loadAlerts();
  }, [activeTab, loadAlerts]);

  // Create batch
  const handleCreate = async () => {
    if (!createForm.product_id || !createForm.warehouse_id || !createForm.batch_number) {
      toast.error('Product, Warehouse, and Batch Number are required');
      return;
    }
    try {
      await batchApi.create({
        ...createForm,
        manufacturing_date: createForm.manufacturing_date || undefined,
        expiry_date: createForm.expiry_date || undefined,
        vendor_batch_number: createForm.vendor_batch_number || undefined,
      });
      toast.success('Batch created successfully');
      setShowCreateDialog(false);
      setCreateForm({
        product_id: '', warehouse_id: '', batch_number: '',
        manufacturing_date: '', expiry_date: '', vendor_batch_number: '',
        quality_grade: 'A', quantity_received: 0, unit_cost: 0, notes: '',
      });
      loadBatches();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create batch';
      toast.error(msg);
    }
  };

  // Change batch status
  const handleStatusChange = async (batchId: string, newStatus: string) => {
    try {
      await batchApi.updateStatus(batchId, newStatus);
      toast.success(`Batch status changed to ${newStatus}`);
      loadBatches();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update status';
      toast.error(msg);
    }
  };

  // Pick batches
  const handlePick = async () => {
    if (!pickProductId || !pickWarehouseId || pickQuantity <= 0) {
      toast.error('Product, Warehouse, and Quantity are required');
      return;
    }
    try {
      const res = await batchApi.pick({
        product_id: pickProductId,
        warehouse_id: pickWarehouseId,
        quantity_needed: pickQuantity,
        strategy: pickStrategy,
      });
      setPickResults(res.picks || []);
      setPickMeta({
        total_picked: res.total_picked,
        shortfall: res.shortfall,
        fully_fulfilled: res.fully_fulfilled,
      });
    } catch {
      toast.error('Failed to execute batch picking');
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Batch Management</h1>
          <p className="text-muted-foreground">SAP-style batch tracking, FEFO/FIFO picking, and expiry management</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="master" className="flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Batch Master
          </TabsTrigger>
          <TabsTrigger value="expiry" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Expiry Alerts
            {alertSummary.red > 0 && (
              <Badge className="ml-1 bg-red-100 text-red-800 hover:bg-red-100">{alertSummary.red}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="picking" className="flex items-center gap-2">
            <ArrowDownUp className="h-4 w-4" />
            Batch Picking
          </TabsTrigger>
        </TabsList>

        {/* ==================== TAB 1: BATCH MASTER ==================== */}
        <TabsContent value="master" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Batch Master Records</CardTitle>
                  <CardDescription>Manage batch/lot inventory across warehouses</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={loadBatches}>
                    <RefreshCw className="h-4 w-4 mr-1" /> Refresh
                  </Button>
                  <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                    <DialogTrigger asChild>
                      <Button size="sm">
                        <Plus className="h-4 w-4 mr-1" /> Create Batch
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-lg">
                      <DialogHeader>
                        <DialogTitle>Create Batch Master</DialogTitle>
                        <DialogDescription>Create a new batch/lot record</DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                          <Label>Product *</Label>
                          <Select value={createForm.product_id} onValueChange={(v) => setCreateForm({ ...createForm, product_id: v })}>
                            <SelectTrigger><SelectValue placeholder="Select product" /></SelectTrigger>
                            <SelectContent>
                              {products.map((p) => (
                                <SelectItem key={p.id} value={p.id}>{p.name} ({p.sku})</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid gap-2">
                          <Label>Warehouse *</Label>
                          <Select value={createForm.warehouse_id} onValueChange={(v) => setCreateForm({ ...createForm, warehouse_id: v })}>
                            <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                            <SelectContent>
                              {warehouses.map((w) => (
                                <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid gap-2">
                          <Label>Batch Number *</Label>
                          <Input
                            value={createForm.batch_number}
                            onChange={(e) => setCreateForm({ ...createForm, batch_number: e.target.value })}
                            placeholder="e.g., BATCH-2026-001"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="grid gap-2">
                            <Label>Manufacturing Date</Label>
                            <Input
                              type="date"
                              value={createForm.manufacturing_date}
                              onChange={(e) => setCreateForm({ ...createForm, manufacturing_date: e.target.value })}
                            />
                          </div>
                          <div className="grid gap-2">
                            <Label>Expiry Date</Label>
                            <Input
                              type="date"
                              value={createForm.expiry_date}
                              onChange={(e) => setCreateForm({ ...createForm, expiry_date: e.target.value })}
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="grid gap-2">
                            <Label>Quantity Received</Label>
                            <Input
                              type="number"
                              value={createForm.quantity_received}
                              onChange={(e) => setCreateForm({ ...createForm, quantity_received: parseInt(e.target.value) || 0 })}
                            />
                          </div>
                          <div className="grid gap-2">
                            <Label>Unit Cost</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={createForm.unit_cost}
                              onChange={(e) => setCreateForm({ ...createForm, unit_cost: parseFloat(e.target.value) || 0 })}
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="grid gap-2">
                            <Label>Quality Grade</Label>
                            <Select value={createForm.quality_grade} onValueChange={(v) => setCreateForm({ ...createForm, quality_grade: v })}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="A">A - Premium</SelectItem>
                                <SelectItem value="B">B - Standard</SelectItem>
                                <SelectItem value="C">C - Economy</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid gap-2">
                            <Label>Vendor Batch No.</Label>
                            <Input
                              value={createForm.vendor_batch_number}
                              onChange={(e) => setCreateForm({ ...createForm, vendor_batch_number: e.target.value })}
                              placeholder="Supplier batch ref"
                            />
                          </div>
                        </div>
                        <div className="grid gap-2">
                          <Label>Notes</Label>
                          <Textarea
                            value={createForm.notes}
                            onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                            placeholder="Optional notes"
                          />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                        <Button onClick={handleCreate}>Create Batch</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex flex-wrap gap-3 mb-4">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder="Search batch number..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  />
                </div>
                <Select value={filterStatus} onValueChange={(v) => { setFilterStatus(v === 'ALL' ? '' : v); setPage(1); }}>
                  <SelectTrigger className="w-[160px]"><SelectValue placeholder="Status" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Statuses</SelectItem>
                    <SelectItem value="UNRESTRICTED">Unrestricted</SelectItem>
                    <SelectItem value="RESTRICTED">Restricted</SelectItem>
                    <SelectItem value="BLOCKED">Blocked</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filterWarehouseId} onValueChange={(v) => { setFilterWarehouseId(v === 'ALL' ? '' : v); setPage(1); }}>
                  <SelectTrigger className="w-[180px]"><SelectValue placeholder="Warehouse" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Warehouses</SelectItem>
                    {warehouses.map((w) => (
                      <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Table */}
              <div className="rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Batch #</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Warehouse</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Grade</TableHead>
                      <TableHead className="text-right">Avail</TableHead>
                      <TableHead className="text-right">Reserved</TableHead>
                      <TableHead className="text-right">Issued</TableHead>
                      <TableHead>Expiry</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={11} className="text-center py-8 text-muted-foreground">Loading...</TableCell>
                      </TableRow>
                    ) : batches.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={11} className="text-center py-8 text-muted-foreground">No batches found</TableCell>
                      </TableRow>
                    ) : (
                      batches.map((b) => (
                        <TableRow key={b.id}>
                          <TableCell className="font-mono font-medium">{b.batch_number}</TableCell>
                          <TableCell>
                            <div className="text-sm">{b.product_name}</div>
                            <div className="text-xs text-muted-foreground">{b.product_sku}</div>
                          </TableCell>
                          <TableCell className="text-sm">{b.warehouse_name}</TableCell>
                          <TableCell>{getStatusBadge(b.batch_status)}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{b.quality_grade || '-'}</Badge>
                          </TableCell>
                          <TableCell className="text-right font-medium">{b.quantity_available}</TableCell>
                          <TableCell className="text-right">{b.quantity_reserved}</TableCell>
                          <TableCell className="text-right">{b.quantity_issued}</TableCell>
                          <TableCell>
                            {b.expiry_date ? (
                              <div className="text-sm">
                                {b.expiry_date}
                                {b.days_until_expiry !== null && (
                                  <div className={`text-xs ${b.days_until_expiry <= 0 ? 'text-red-600 font-bold' : b.days_until_expiry <= 30 ? 'text-yellow-600' : 'text-green-600'}`}>
                                    {b.days_until_expiry <= 0 ? 'EXPIRED' : `${b.days_until_expiry}d left`}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">{b.total_value.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}</TableCell>
                          <TableCell>
                            <Select onValueChange={(v) => handleStatusChange(b.id, v)}>
                              <SelectTrigger className="h-8 w-[130px] text-xs">
                                <SelectValue placeholder="Change status" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="UNRESTRICTED">Unrestricted</SelectItem>
                                <SelectItem value="RESTRICTED">Restricted</SelectItem>
                                <SelectItem value="BLOCKED">Blocked</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Showing {(page - 1) * 20 + 1}-{Math.min(page * 20, total)} of {total}
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== TAB 2: EXPIRY ALERTS ==================== */}
        <TabsContent value="expiry" className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-8 w-8 text-red-600" />
                  <div>
                    <p className="text-2xl font-bold text-red-600">{alertSummary.red}</p>
                    <p className="text-sm text-red-700">Expired / &lt; 7 days</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Clock className="h-8 w-8 text-yellow-600" />
                  <div>
                    <p className="text-2xl font-bold text-yellow-600">{alertSummary.yellow}</p>
                    <p className="text-sm text-yellow-700">7 - 30 days</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Package className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-2xl font-bold text-green-600">{alertSummary.green}</p>
                    <p className="text-sm text-green-700">&gt; 30 days</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Expiry Alerts</CardTitle>
                  <CardDescription>Batches nearing expiry, sorted by urgency</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Label className="text-sm">Days ahead:</Label>
                  <Input
                    type="number"
                    className="w-20"
                    value={daysAhead}
                    onChange={(e) => setDaysAhead(parseInt(e.target.value) || 30)}
                  />
                  <Button variant="outline" size="sm" onClick={loadAlerts}>
                    <RefreshCw className="h-4 w-4 mr-1" /> Refresh
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Batch #</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Warehouse</TableHead>
                      <TableHead>Expiry Date</TableHead>
                      <TableHead>Urgency</TableHead>
                      <TableHead className="text-right">Qty Available</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead>Grade</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alerts.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          No expiry alerts within {daysAhead} days
                        </TableCell>
                      </TableRow>
                    ) : (
                      alerts.map((a) => (
                        <TableRow key={a.id} className={a.severity === 'RED' ? 'bg-red-50/50' : a.severity === 'YELLOW' ? 'bg-yellow-50/50' : ''}>
                          <TableCell className="font-mono font-medium">{a.batch_number}</TableCell>
                          <TableCell>
                            <div className="text-sm">{a.product_name}</div>
                            <div className="text-xs text-muted-foreground">{a.product_sku}</div>
                          </TableCell>
                          <TableCell className="text-sm">{a.warehouse_name}</TableCell>
                          <TableCell>{a.expiry_date}</TableCell>
                          <TableCell>{getExpirySeverityBadge(a.severity, a.days_until_expiry)}</TableCell>
                          <TableCell className="text-right font-medium">{a.quantity_available}</TableCell>
                          <TableCell className="text-right">{a.total_value.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}</TableCell>
                          <TableCell><Badge variant="outline">{a.quality_grade || '-'}</Badge></TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== TAB 3: BATCH PICKING ==================== */}
        <TabsContent value="picking" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Batch Picking Simulator</CardTitle>
              <CardDescription>
                Test FEFO (First Expiry First Out) or FIFO (First In First Out) picking strategies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="grid gap-2">
                  <Label>Product *</Label>
                  <Select value={pickProductId} onValueChange={setPickProductId}>
                    <SelectTrigger><SelectValue placeholder="Select product" /></SelectTrigger>
                    <SelectContent>
                      {products.map((p) => (
                        <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>Warehouse *</Label>
                  <Select value={pickWarehouseId} onValueChange={setPickWarehouseId}>
                    <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                    <SelectContent>
                      {warehouses.map((w) => (
                        <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>Quantity Needed *</Label>
                  <Input
                    type="number"
                    value={pickQuantity}
                    onChange={(e) => setPickQuantity(parseInt(e.target.value) || 0)}
                    placeholder="Enter quantity"
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Strategy</Label>
                  <div className="flex gap-2">
                    <Button
                      variant={pickStrategy === 'FEFO' ? 'default' : 'outline'}
                      size="sm"
                      className="flex-1"
                      onClick={() => setPickStrategy('FEFO')}
                    >
                      FEFO
                    </Button>
                    <Button
                      variant={pickStrategy === 'FIFO' ? 'default' : 'outline'}
                      size="sm"
                      className="flex-1"
                      onClick={() => setPickStrategy('FIFO')}
                    >
                      FIFO
                    </Button>
                  </div>
                </div>
              </div>
              <Button onClick={handlePick} className="w-full md:w-auto">
                <ArrowDownUp className="h-4 w-4 mr-2" />
                Run {pickStrategy} Picking
              </Button>

              {/* Pick results */}
              {pickMeta && (
                <div className="space-y-3 mt-4">
                  <div className="flex gap-4">
                    <Badge className={pickMeta.fully_fulfilled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                      {pickMeta.fully_fulfilled ? 'Fully Fulfilled' : `Shortfall: ${pickMeta.shortfall}`}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      Total picked: {pickMeta.total_picked} / {pickQuantity}
                    </span>
                  </div>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Batch #</TableHead>
                          <TableHead className="text-right">Pick Qty</TableHead>
                          <TableHead className="text-right">Available</TableHead>
                          <TableHead>Expiry</TableHead>
                          <TableHead>Days Left</TableHead>
                          <TableHead>Mfg Date</TableHead>
                          <TableHead>Grade</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pickResults.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-4 text-muted-foreground">
                              No batches available for picking
                            </TableCell>
                          </TableRow>
                        ) : (
                          pickResults.map((p, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-mono font-medium">{p.batch_number}</TableCell>
                              <TableCell className="text-right font-bold">{p.pick_quantity}</TableCell>
                              <TableCell className="text-right">{p.quantity_available}</TableCell>
                              <TableCell>{p.expiry_date || '-'}</TableCell>
                              <TableCell>
                                {p.days_until_expiry !== null ? (
                                  <span className={p.days_until_expiry <= 7 ? 'text-red-600 font-bold' : p.days_until_expiry <= 30 ? 'text-yellow-600' : 'text-green-600'}>
                                    {p.days_until_expiry}d
                                  </span>
                                ) : '-'}
                              </TableCell>
                              <TableCell>{p.manufacturing_date || '-'}</TableCell>
                              <TableCell><Badge variant="outline">{p.quality_grade || '-'}</Badge></TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
