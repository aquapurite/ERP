'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Send, CheckCircle, XCircle, FileText, ShoppingCart, Clock, AlertCircle, ArrowRight, Trash2, Loader2, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { warehousesApi, productsApi } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';

interface PurchaseRequisition {
  id: string;
  pr_number: string;
  requester_id: string;
  requester_name: string;
  department: string;
  warehouse_id: string;
  warehouse_name: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CONVERTED' | 'CANCELLED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  total_items: number;
  total_amount: number;
  required_by_date?: string;
  justification?: string;
  approved_by?: string;
  approved_at?: string;
  po_number?: string;
  created_at: string;
}

interface PRStats {
  total: number;
  draft: number;
  pending_approval: number;
  approved: number;
  converted_to_po: number;
  avg_approval_time_hours: number;
}

interface PRFormItem {
  product_id: string;
  product_name: string;
  sku: string;
  quantity_requested: number;
  estimated_unit_price: number;
  uom: string;
  monthly_quantities?: Record<string, number>; // e.g., {"2026-01": 500, "2026-02": 500}
}

interface PRFormData {
  delivery_warehouse_id: string;
  required_by_date: string;
  priority: number;
  reason: string;
  notes: string;
  items: PRFormItem[];
  is_multi_delivery?: boolean;
}

interface Warehouse {
  id: string;
  name: string;
  code?: string;
}

interface Product {
  id: string;
  name: string;
  sku: string;
  mrp: number;
}

const requisitionsApi = {
  list: async (params?: { page?: number; size?: number; status?: string }) => {
    try {
      const { data } = await apiClient.get('/purchase/requisitions', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<PRStats> => {
    try {
      const { data } = await apiClient.get('/purchase/requisitions/stats');
      return data;
    } catch {
      return { total: 0, draft: 0, pending_approval: 0, approved: 0, converted_to_po: 0, avg_approval_time_hours: 0 };
    }
  },
  create: async (params: { warehouse_id: string; required_by_date: string; priority: string; justification: string; items: { product_id: string; quantity: number }[] }) => {
    const { data } = await apiClient.post('/purchase/requisitions', params);
    return data;
  },
  submit: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/submit`);
    return data;
  },
  approve: async (id: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/approve`);
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/reject`, { reason });
    return data;
  },
  convertToPO: async (id: string, vendorId: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/convert-to-po`, { vendor_id: vendorId });
    return data;
  },
};

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  SUBMITTED: 'bg-blue-100 text-blue-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  CONVERTED: 'bg-purple-100 text-purple-800',
  CANCELLED: 'bg-gray-100 text-gray-600',
};

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-600',
  NORMAL: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-700',
  URGENT: 'bg-red-100 text-red-700',
};

export default function PurchaseRequisitionsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedPR, setSelectedPR] = useState<PurchaseRequisition | null>(null);
  const [isConvertDialogOpen, setIsConvertDialogOpen] = useState(false);
  const [selectedVendorId, setSelectedVendorId] = useState('');

  // Form state
  const [formData, setFormData] = useState<PRFormData>({
    delivery_warehouse_id: '',
    required_by_date: '',
    priority: 5,
    reason: '',
    notes: '',
    items: [],
    is_multi_delivery: false,
  });
  const [newItem, setNewItem] = useState({
    product_id: '',
    quantity: 1,
    estimated_price: 0,
  });
  const [multiDeliveryMonths, setMultiDeliveryMonths] = useState<string[]>([]);

  // Generate next 12 months for multi-delivery selection
  const availableMonths = useMemo(() => {
    const months: { value: string; label: string }[] = [];
    const today = new Date();
    for (let i = 0; i < 12; i++) {
      const d = new Date(today.getFullYear(), today.getMonth() + i, 1);
      const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      const label = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      months.push({ value, label });
    }
    return months;
  }, []);

  const queryClient = useQueryClient();

  // Fetch warehouses and products for dropdowns
  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses-dropdown'],
    queryFn: () => warehousesApi.list({ size: 100 }),
  });

  const { data: productsData, isLoading: isLoadingProducts, error: productsError } = useQuery({
    queryKey: ['products-dropdown'],
    queryFn: async () => {
      console.log('[PR Form] Fetching products...');
      // Backend max size is 100, so fetch 100 at a time
      const result = await productsApi.list({ size: 100 });
      console.log('[PR Form] Products fetched:', result?.items?.length || 0);
      return result;
    },
  });

  // Log any errors
  if (productsError) {
    console.error('[PR Form] Products fetch error:', productsError);
  }

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-dropdown'],
    queryFn: async () => {
      const { data } = await apiClient.get('/vendors', { params: { limit: 100 } });
      return data;
    },
  });

  const warehouses = warehousesData?.items ?? [];
  const products = productsData?.items ?? [];
  const vendors = vendorsData?.items ?? [];

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-requisitions', page, pageSize, statusFilter],
    queryFn: () => requisitionsApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter !== 'all' ? statusFilter : undefined,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['pr-stats'],
    queryFn: requisitionsApi.getStats,
  });

  const submitMutation = useMutation({
    mutationFn: (id: string) => requisitionsApi.submit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      toast.success('PR submitted for approval');
    },
    onError: () => toast.error('Failed to submit PR'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => requisitionsApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      toast.success('PR approved successfully');
    },
    onError: () => toast.error('Failed to approve PR'),
  });

  const createMutation = useMutation({
    mutationFn: async (params: { data: PRFormData; submitForApproval: boolean }) => {
      const payload = {
        delivery_warehouse_id: params.data.delivery_warehouse_id,
        required_by_date: params.data.required_by_date || null,
        priority: params.data.priority,
        reason: params.data.reason || null,
        notes: params.data.notes || null,
        items: params.data.items.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          sku: item.sku,
          quantity_requested: item.quantity_requested,
          estimated_unit_price: item.estimated_unit_price,
          uom: item.uom,
          // Include monthly_quantities for multi-delivery PRs
          monthly_quantities: item.monthly_quantities || null,
        })),
      };
      const { data: created } = await apiClient.post('/purchase/requisitions', payload);

      // If submit for approval, submit it immediately
      if (params.submitForApproval && created.id) {
        await apiClient.post(`/purchase/requisitions/${created.id}/submit`);
      }
      return created;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      toast.success(variables.submitForApproval ? 'PR created and submitted for approval' : 'PR saved as draft');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create PR'),
  });

  const convertToPOMutation = useMutation({
    mutationFn: async ({ prId, vendorId }: { prId: string; vendorId: string }) => {
      const { data } = await apiClient.post(`/purchase/requisitions/${prId}/convert-to-po`, { vendor_id: vendorId });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      toast.success('PO created from PR successfully');
      setIsConvertDialogOpen(false);
      setSelectedPR(null);
      setSelectedVendorId('');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to convert to PO'),
  });

  // Helper functions
  const resetForm = () => {
    setFormData({
      delivery_warehouse_id: '',
      required_by_date: '',
      priority: 5,
      reason: '',
      notes: '',
      items: [],
      is_multi_delivery: false,
    });
    setNewItem({ product_id: '', quantity: 1, estimated_price: 0 });
    setMultiDeliveryMonths([]);
    setIsDialogOpen(false);
  };

  const handleAddItem = () => {
    if (!newItem.product_id || newItem.quantity <= 0) {
      toast.error('Please select a product and enter quantity');
      return;
    }

    const product = products.find((p: Product) => p.id === newItem.product_id);
    if (!product) {
      toast.error('Product not found');
      return;
    }

    // Generate monthly_quantities if multi-delivery is enabled
    let monthly_quantities: Record<string, number> | undefined;
    if (formData.is_multi_delivery && multiDeliveryMonths.length > 0) {
      const qtyPerMonth = Math.floor(newItem.quantity / multiDeliveryMonths.length);
      const remainder = newItem.quantity % multiDeliveryMonths.length;
      monthly_quantities = {};
      multiDeliveryMonths.forEach((month, index) => {
        // Distribute remainder to first months
        monthly_quantities![month] = qtyPerMonth + (index < remainder ? 1 : 0);
      });
    }

    setFormData({
      ...formData,
      items: [...formData.items, {
        product_id: product.id,
        product_name: product.name,
        sku: product.sku,
        quantity_requested: newItem.quantity,
        estimated_unit_price: newItem.estimated_price || product.mrp || 0,
        uom: 'PCS',
        monthly_quantities,
      }],
    });
    setNewItem({ product_id: '', quantity: 1, estimated_price: 0 });
  };

  const handleRemoveItem = (index: number) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index),
    });
  };

  const handleSaveDraft = () => {
    if (!formData.delivery_warehouse_id || formData.items.length === 0) {
      toast.error('Please select warehouse and add at least one item');
      return;
    }
    createMutation.mutate({ data: formData, submitForApproval: false });
  };

  const handleSubmitForApproval = () => {
    if (!formData.delivery_warehouse_id || formData.items.length === 0) {
      toast.error('Please select warehouse and add at least one item');
      return;
    }
    createMutation.mutate({ data: formData, submitForApproval: true });
  };

  const calculateTotal = () => {
    return formData.items.reduce((sum, item) => sum + (item.quantity_requested * item.estimated_unit_price), 0);
  };

  const columns: ColumnDef<PurchaseRequisition>[] = [
    {
      accessorKey: 'pr_number',
      header: 'PR Number',
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <div className="font-mono font-medium">{row.original.pr_number}</div>
            <div className="text-sm text-muted-foreground">{row.original.department}</div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'requester_name',
      header: 'Requester',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.requester_name}</div>
          <div className="text-sm text-muted-foreground">
            {formatDate(row.original.created_at)}
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'warehouse_name',
      header: 'Warehouse',
      cell: ({ row }) => (
        <span className="text-sm">{row.original.warehouse_name}</span>
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
      accessorKey: 'items_amount',
      header: 'Items / Amount',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.total_items} items</div>
          <div className="text-sm text-muted-foreground">{formatCurrency(row.original.total_amount)}</div>
        </div>
      ),
    },
    {
      accessorKey: 'required_by_date',
      header: 'Required By',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">
            {row.original.required_by_date ? formatDate(row.original.required_by_date) : '-'}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[row.original.status]}`}>
            {row.original.status.replace('_', ' ')}
          </span>
          {row.original.po_number && (
            <div className="text-xs text-muted-foreground mt-1">
              PO: {row.original.po_number}
            </div>
          )}
        </div>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const pr = row.original;
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
              <DropdownMenuItem>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              {pr.status === 'DRAFT' && (
                <DropdownMenuItem onClick={() => submitMutation.mutate(pr.id)}>
                  <Send className="mr-2 h-4 w-4" />
                  Submit for Approval
                </DropdownMenuItem>
              )}
              {pr.status === 'SUBMITTED' && (
                <>
                  <DropdownMenuItem onClick={() => approveMutation.mutate(pr.id)}>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Approve
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-red-600">
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject
                  </DropdownMenuItem>
                </>
              )}
              {pr.status === 'APPROVED' && (
                <DropdownMenuItem onClick={() => { setSelectedPR(pr); setIsConvertDialogOpen(true); }}>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  Convert to PO
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Requisitions"
        description="Manage purchase requests and approval workflow"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) resetForm(); else setIsDialogOpen(true); }}>
            <DialogTrigger asChild>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create PR
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Purchase Requisition</DialogTitle>
                <DialogDescription>
                  Request items for procurement. This will go through an approval workflow.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Delivery Warehouse *</Label>
                    <Select
                      value={formData.delivery_warehouse_id || 'select'}
                      onValueChange={(value) => setFormData({ ...formData, delivery_warehouse_id: value === 'select' ? '' : value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="select" disabled>Select warehouse</SelectItem>
                        {warehouses.filter((w: Warehouse) => w.id && w.id.trim() !== '').map((w: Warehouse) => (
                          <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select
                      value={formData.priority.toString()}
                      onValueChange={(value) => setFormData({ ...formData, priority: parseInt(value) })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select priority" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 - Lowest</SelectItem>
                        <SelectItem value="3">3 - Low</SelectItem>
                        <SelectItem value="5">5 - Normal</SelectItem>
                        <SelectItem value="7">7 - High</SelectItem>
                        <SelectItem value="10">10 - Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Required By Date</Label>
                    <Input
                      type="date"
                      value={formData.required_by_date}
                      onChange={(e) => setFormData({ ...formData, required_by_date: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Multi-Delivery PO
                    </Label>
                    <div className="flex items-center gap-3 pt-2">
                      <Switch
                        checked={formData.is_multi_delivery}
                        onCheckedChange={(checked) => {
                          setFormData({ ...formData, is_multi_delivery: checked });
                          if (!checked) setMultiDeliveryMonths([]);
                        }}
                      />
                      <span className="text-sm text-muted-foreground">
                        {formData.is_multi_delivery ? 'Enabled' : 'Single delivery'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Multi-Delivery Month Selection */}
                {formData.is_multi_delivery && (
                  <div className="space-y-2 border rounded-lg p-4 bg-blue-50/50">
                    <Label className="text-sm font-medium">Select Delivery Months</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Select months for staggered delivery. Quantities will be distributed across selected months.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {availableMonths.map((month) => (
                        <Button
                          key={month.value}
                          type="button"
                          size="sm"
                          variant={multiDeliveryMonths.includes(month.value) ? 'default' : 'outline'}
                          onClick={() => {
                            if (multiDeliveryMonths.includes(month.value)) {
                              setMultiDeliveryMonths(multiDeliveryMonths.filter(m => m !== month.value));
                            } else {
                              setMultiDeliveryMonths([...multiDeliveryMonths, month.value].sort());
                            }
                          }}
                        >
                          {month.label}
                        </Button>
                      ))}
                    </div>
                    {multiDeliveryMonths.length > 0 && (
                      <p className="text-xs text-blue-600 mt-2">
                        Selected: {multiDeliveryMonths.length} month(s)
                      </p>
                    )}
                  </div>
                )}
                <div className="space-y-2">
                  <Label>Justification / Reason</Label>
                  <Textarea
                    placeholder="Explain why these items are needed..."
                    rows={2}
                    value={formData.reason}
                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  />
                </div>

                {/* Add Item Section */}
                <div className="space-y-2">
                  <Label className="text-base font-semibold">Add Items *</Label>
                  <div className="border rounded-lg p-4 space-y-3">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-5">
                        <Label className="text-xs">Product {isLoadingProducts && <span className="text-muted-foreground">(loading...)</span>}</Label>
                        <Select
                          value={newItem.product_id || 'select'}
                          onValueChange={(value) => {
                            const product = products.find((p: Product) => p.id === value);
                            setNewItem({
                              ...newItem,
                              product_id: value === 'select' ? '' : value,
                              estimated_price: parseFloat(String(product?.mrp)) || 0
                            });
                          }}
                          disabled={isLoadingProducts}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder={isLoadingProducts ? "Loading products..." : "Select product"} />
                          </SelectTrigger>
                          <SelectContent>
                            {isLoadingProducts ? (
                              <SelectItem value="loading" disabled>Loading products...</SelectItem>
                            ) : productsError ? (
                              <SelectItem value="error" disabled>Error loading products</SelectItem>
                            ) : products.length === 0 ? (
                              <SelectItem value="empty" disabled>No products found</SelectItem>
                            ) : (
                              <>
                                <SelectItem value="select" disabled>Select product ({products.length} available)</SelectItem>
                                {products.filter((p: Product) => p.id && p.id.trim() !== '').map((p: Product) => (
                                  <SelectItem key={p.id} value={p.id}>{p.name} ({p.sku})</SelectItem>
                                ))}
                              </>
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-2">
                        <Label className="text-xs">Qty</Label>
                        <Input
                          type="number"
                          min="1"
                          value={newItem.quantity}
                          onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 0 })}
                        />
                      </div>
                      <div className="col-span-3">
                        <Label className="text-xs">Est. Price</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          value={newItem.estimated_price || ''}
                          onChange={(e) => setNewItem({ ...newItem, estimated_price: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                      <div className="col-span-2">
                        <Button type="button" onClick={handleAddItem} className="w-full">
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Items List */}
                {formData.items.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          <th className="px-3 py-2 text-left">Product</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Est. Price</th>
                          <th className="px-3 py-2 text-right">Total</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {formData.items.map((item, index) => (
                          <tr key={index} className="border-t">
                            <td className="px-3 py-2">
                              <div className="font-medium">{item.product_name}</div>
                              <div className="text-xs text-muted-foreground">{item.sku}</div>
                              {item.monthly_quantities && Object.keys(item.monthly_quantities).length > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {Object.entries(item.monthly_quantities).map(([month, qty]) => {
                                    const d = new Date(`${month}-01`);
                                    const label = d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                                    return (
                                      <span key={month} className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-blue-100 text-blue-700">
                                        {label}: {qty}
                                      </span>
                                    );
                                  })}
                                </div>
                              )}
                            </td>
                            <td className="px-3 py-2 text-right">{item.quantity_requested}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.estimated_unit_price)}</td>
                            <td className="px-3 py-2 text-right font-medium">
                              {formatCurrency(item.quantity_requested * item.estimated_unit_price)}
                            </td>
                            <td className="px-3 py-2">
                              <Button variant="ghost" size="icon" onClick={() => handleRemoveItem(index)}>
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-muted/50">
                        <tr className="border-t">
                          <td colSpan={3} className="px-3 py-2 text-right font-semibold">Estimated Total:</td>
                          <td className="px-3 py-2 text-right font-bold">{formatCurrency(calculateTotal())}</td>
                          <td></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}

                {formData.items.length === 0 && (
                  <div className="text-sm text-muted-foreground text-center py-4 border rounded-lg">
                    No items added yet. Select a product and click + to add.
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Notes (Optional)</Label>
                  <Textarea
                    placeholder="Additional notes..."
                    rows={2}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm}>Cancel</Button>
                <Button variant="secondary" onClick={handleSaveDraft} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save as Draft
                </Button>
                <Button onClick={handleSubmitForApproval} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Submit for Approval
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PRs</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft</CardTitle>
            <FileText className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats?.draft || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.pending_approval || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.approved || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Converted to PO</CardTitle>
            <ShoppingCart className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats?.converted_to_po || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Approval Time</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avg_approval_time_hours || 0}h</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="SUBMITTED">Submitted</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
            <SelectItem value="CONVERTED">Converted</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="pr_number"
        searchPlaceholder="Search PR number..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Convert to PO Dialog */}
      <Dialog open={isConvertDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setSelectedPR(null);
          setSelectedVendorId('');
        }
        setIsConvertDialogOpen(open);
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Convert to Purchase Order</DialogTitle>
            <DialogDescription>
              Select a vendor to create a Purchase Order from PR {selectedPR?.pr_number}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-2">
              <Label>Select Vendor *</Label>
              <Select
                value={selectedVendorId || 'select'}
                onValueChange={(value) => setSelectedVendorId(value === 'select' ? '' : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose vendor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="select" disabled>Choose vendor</SelectItem>
                  {vendors.filter((v: { id: string }) => v.id && v.id.trim() !== '').map((v: { id: string; name?: string; legal_name?: string; code?: string }) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.name || v.legal_name} {v.code && `(${v.code})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Items:</span>
                  <span className="font-medium">{selectedPR?.total_items || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount:</span>
                  <span className="font-medium">{formatCurrency(selectedPR?.total_amount || 0)}</span>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConvertDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (!selectedPR || !selectedVendorId) {
                  toast.error('Please select a vendor');
                  return;
                }
                convertToPOMutation.mutate({ prId: selectedPR.id, vendorId: selectedVendorId });
              }}
              disabled={convertToPOMutation.isPending || !selectedVendorId}
            >
              {convertToPOMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Purchase Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
