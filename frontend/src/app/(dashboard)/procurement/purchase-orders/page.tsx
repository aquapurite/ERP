'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, FileText, Send, CheckCircle, X, Loader2, Trash2, Download, Printer, Package } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/providers/auth-provider';
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
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { purchaseOrdersApi, vendorsApi, warehousesApi, productsApi } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';

interface POItem {
  id?: string;
  po_id?: string;
  product_id: string;
  product_name?: string;
  sku?: string;
  quantity?: number;
  quantity_ordered?: number;
  quantity_received?: number;
  unit_price: number;
  gst_rate: number;
  total?: number;
  monthly_quantities?: Record<string, number>;
}

interface MonthQuantity {
  month: string;
  quantity: number;
}

interface PurchaseOrder {
  id: string;
  po_number: string;
  vendor_id: string;
  vendor?: { id: string; name: string; code: string };
  delivery_warehouse_id?: string;
  warehouse_id?: string;
  warehouse?: { id: string; name: string };
  status: string;
  po_date?: string;
  expected_delivery_date?: string;
  credit_days?: number;
  subtotal?: number;
  gst_amount: number;
  grand_total: number;
  notes?: string;
  items?: POItem[];
  created_at: string;
}

interface Vendor {
  id: string;
  name: string;
  code: string;
}

interface Warehouse {
  id: string;
  name: string;
  code: string;
}

interface Product {
  id: string;
  name: string;
  sku: string;
  mrp: number;
}

export default function PurchaseOrdersPage() {
  const queryClient = useQueryClient();
  const { permissions } = useAuth();
  const isSuperAdmin = permissions?.is_super_admin ?? false;
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedPO, setSelectedPO] = useState<PurchaseOrder | null>(null);

  const [isMultiDelivery, setIsMultiDelivery] = useState(false);
  const [deliveryMonths, setDeliveryMonths] = useState<string[]>([]);

  const [formData, setFormData] = useState({
    vendor_id: '',
    delivery_warehouse_id: '',
    expected_delivery_date: '',
    credit_days: 30,
    notes: '',
    items: [] as POItem[],
  });

  const [newItem, setNewItem] = useState({
    product_id: '',
    quantity: 1,
    unit_price: 0,
    gst_rate: 18,
    monthlyQtys: {} as Record<string, number>,
  });

  // Generate next 6 months for multi-delivery selection
  const getAvailableMonths = () => {
    const months = [];
    const today = new Date();
    for (let i = 0; i < 6; i++) {
      const d = new Date(today.getFullYear(), today.getMonth() + i, 1);
      const monthCode = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      const monthName = d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      months.push({ code: monthCode, name: monthName });
    }
    return months;
  };

  const availableMonths = getAvailableMonths();

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', page, pageSize, statusFilter],
    queryFn: () => purchaseOrdersApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter === 'all' ? undefined : statusFilter
    }),
  });

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-dropdown'],
    queryFn: () => vendorsApi.list({ size: 100 }),
  });

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses-dropdown'],
    queryFn: () => warehousesApi.list({ size: 100 }),
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-dropdown'],
    queryFn: () => productsApi.list({ size: 200 }),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: purchaseOrdersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      toast.success('Purchase order created successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create PO'),
  });

  const submitMutation = useMutation({
    mutationFn: purchaseOrdersApi.submit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      toast.success('PO submitted for approval');
      setIsSubmitOpen(false);
      setSelectedPO(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to submit PO'),
  });

  const approveMutation = useMutation({
    mutationFn: purchaseOrdersApi.approve,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      toast.success('PO approved successfully');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to approve PO'),
  });

  const deleteMutation = useMutation({
    mutationFn: purchaseOrdersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      toast.success('PO deleted successfully');
      setIsDeleteOpen(false);
      setSelectedPO(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete PO'),
  });

  const handleDownload = async (po: PurchaseOrder) => {
    try {
      // Fetch HTML with auth token, then open in new tab
      const htmlContent = await purchaseOrdersApi.download(po.id);
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => window.URL.revokeObjectURL(url);
      }
      toast.success('Opening PO for download/print');
    } catch {
      toast.error('Failed to download PO');
    }
  };

  const handlePrint = async (po: PurchaseOrder) => {
    try {
      // Fetch HTML with auth token, then open in new tab for printing
      const htmlContent = await purchaseOrdersApi.download(po.id);
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => {
          window.URL.revokeObjectURL(url);
          printWindow.print();
        };
      }
    } catch {
      toast.error('Failed to print PO');
    }
  };

  const resetForm = () => {
    setFormData({
      vendor_id: '',
      delivery_warehouse_id: '',
      expected_delivery_date: '',
      credit_days: 30,
      notes: '',
      items: [],
    });
    setNewItem({ product_id: '', quantity: 1, unit_price: 0, gst_rate: 18, monthlyQtys: {} });
    setIsMultiDelivery(false);
    setDeliveryMonths([]);
    setIsCreateOpen(false);
  };

  const handleAddItem = () => {
    if (!newItem.product_id || newItem.unit_price <= 0) {
      toast.error('Please fill all item fields');
      return;
    }

    // Calculate total quantity for multi-delivery or use direct quantity
    let totalQty = newItem.quantity;
    let monthlyQuantities: Record<string, number> | undefined = undefined;

    if (isMultiDelivery && deliveryMonths.length > 0) {
      // Validate all selected months have quantities
      const monthQtys = deliveryMonths.reduce((acc, month) => {
        const qty = newItem.monthlyQtys[month] || 0;
        if (qty > 0) acc[month] = qty;
        return acc;
      }, {} as Record<string, number>);

      if (Object.keys(monthQtys).length === 0) {
        toast.error('Please enter quantities for at least one month');
        return;
      }

      totalQty = Object.values(monthQtys).reduce((sum, q) => sum + q, 0);
      monthlyQuantities = monthQtys;
    } else if (newItem.quantity <= 0) {
      toast.error('Quantity must be greater than 0');
      return;
    }

    const product = products.find((p: Product) => p.id === newItem.product_id);
    setFormData({
      ...formData,
      items: [...formData.items, {
        product_id: newItem.product_id,
        product_name: product?.name,
        sku: product?.sku,
        quantity: totalQty,
        unit_price: newItem.unit_price,
        gst_rate: newItem.gst_rate,
        monthly_quantities: monthlyQuantities,
      }],
    });
    setNewItem({ product_id: '', quantity: 1, unit_price: 0, gst_rate: 18, monthlyQtys: {} });
  };

  const handleRemoveItem = (index: number) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index),
    });
  };

  const handleCreatePO = () => {
    if (!formData.vendor_id || !formData.delivery_warehouse_id || formData.items.length === 0) {
      toast.error('Please fill all required fields and add at least one item');
      return;
    }
    createMutation.mutate({
      vendor_id: formData.vendor_id,
      delivery_warehouse_id: formData.delivery_warehouse_id,
      expected_delivery_date: formData.expected_delivery_date || undefined,
      credit_days: formData.credit_days,
      notes: formData.notes || undefined,
      items: formData.items.map(item => ({
        product_id: item.product_id,
        product_name: item.product_name,
        sku: item.sku,
        quantity_ordered: item.quantity ?? 0,
        unit_price: item.unit_price,
        gst_rate: item.gst_rate ?? 0,
        monthly_quantities: item.monthly_quantities || undefined,
      })),
    } as any);
  };

  const handleViewDetails = async (po: PurchaseOrder) => {
    try {
      const detail = await purchaseOrdersApi.getById(po.id);
      setSelectedPO(detail);
      setIsViewOpen(true);
    } catch {
      setSelectedPO(po);
      setIsViewOpen(true);
    }
  };

  const calculateTotals = () => {
    const subtotal = formData.items.reduce((sum, item) => sum + ((item.quantity ?? 0) * item.unit_price), 0);
    const gst = formData.items.reduce((sum, item) => sum + ((item.quantity ?? 0) * item.unit_price * (item.gst_rate ?? 0) / 100), 0);
    return { subtotal, gst, total: subtotal + gst };
  };

  const vendors = vendorsData?.items ?? [];
  const warehouses = warehousesData?.items ?? [];
  const products = productsData?.items ?? [];
  const totals = calculateTotals();

  const columns: ColumnDef<PurchaseOrder>[] = [
    {
      accessorKey: 'po_number',
      header: 'PO Number',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium font-mono">{row.original.po_number}</span>
        </div>
      ),
    },
    {
      accessorKey: 'vendor',
      header: 'Vendor',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.vendor?.name || 'N/A'}</div>
          <div className="text-xs text-muted-foreground font-mono">{row.original.vendor?.code}</div>
        </div>
      ),
    },
    {
      accessorKey: 'warehouse',
      header: 'Warehouse',
      cell: ({ row }) => (
        <span className="text-sm">{row.original.warehouse?.name || 'N/A'}</span>
      ),
    },
    {
      accessorKey: 'grand_total',
      header: 'Amount',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{formatCurrency(row.original.grand_total)}</div>
          <div className="text-xs text-muted-foreground">
            GST: {formatCurrency(row.original.gst_amount)}
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'expected_delivery_date',
      header: 'Expected Delivery',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {row.original.expected_delivery_date
            ? formatDate(row.original.expected_delivery_date)
            : '-'}
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
            <DropdownMenuItem onClick={() => handleViewDetails(row.original)}>
              <Eye className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleDownload(row.original)}>
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handlePrint(row.original)}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {row.original.status === 'DRAFT' && (
              <DropdownMenuItem onClick={() => { setSelectedPO(row.original); setIsSubmitOpen(true); }}>
                <Send className="mr-2 h-4 w-4" />
                Submit for Approval
              </DropdownMenuItem>
            )}
            {row.original.status === 'PENDING_APPROVAL' && (
              <DropdownMenuItem onClick={() => approveMutation.mutate(row.original.id)}>
                <CheckCircle className="mr-2 h-4 w-4" />
                Approve
              </DropdownMenuItem>
            )}
            {row.original.status === 'APPROVED' && (
              <DropdownMenuItem>
                <Send className="mr-2 h-4 w-4" />
                Send to Vendor
              </DropdownMenuItem>
            )}
            {isSuperAdmin && row.original.status === 'DRAFT' && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => { setSelectedPO(row.original); setIsDeleteOpen(true); }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete PO
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Orders"
        description="Manage purchase orders and vendor procurement"
        actions={
          <div className="flex items-center gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="SENT_TO_VENDOR">Sent to Vendor</SelectItem>
                <SelectItem value="CONFIRMED">Confirmed</SelectItem>
                <SelectItem value="PARTIALLY_RECEIVED">Partially Received</SelectItem>
                <SelectItem value="RECEIVED">Received</SelectItem>
                <SelectItem value="CLOSED">Closed</SelectItem>
              </SelectContent>
            </Select>
            <Dialog open={isCreateOpen} onOpenChange={(open) => { if (!open) resetForm(); else setIsCreateOpen(true); }}>
              <DialogTrigger asChild>
                <Button onClick={() => setIsCreateOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create PO
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Purchase Order</DialogTitle>
                  <DialogDescription>Create a new purchase order for vendor procurement</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Vendor *</Label>
                      <Select
                        value={formData.vendor_id || 'select'}
                        onValueChange={(value) => setFormData({ ...formData, vendor_id: value === 'select' ? '' : value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select vendor" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="select" disabled>Select vendor</SelectItem>
                          {vendors.filter((v: Vendor) => v.id && v.id.trim() !== '').map((v: Vendor) => (
                            <SelectItem key={v.id} value={v.id}>{v.name} ({v.code})</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
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
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Expected Delivery Date</Label>
                      <Input
                        type="date"
                        value={formData.expected_delivery_date}
                        onChange={(e) => setFormData({ ...formData, expected_delivery_date: e.target.value })}
                        disabled={isMultiDelivery}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Credit Days</Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.credit_days}
                        onChange={(e) => setFormData({ ...formData, credit_days: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                  </div>

                  {/* Multi-Delivery Toggle */}
                  <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/30">
                    <div className="space-y-0.5">
                      <Label className="text-base font-medium">Multi-Delivery Schedule</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable for orders with multiple delivery dates (lot-wise)
                      </p>
                    </div>
                    <Switch
                      checked={isMultiDelivery}
                      onCheckedChange={(checked) => {
                        setIsMultiDelivery(checked);
                        if (!checked) {
                          setDeliveryMonths([]);
                          setNewItem({ ...newItem, monthlyQtys: {} });
                        }
                      }}
                    />
                  </div>

                  {/* Month Selection for Multi-Delivery */}
                  {isMultiDelivery && (
                    <div className="space-y-3 p-4 border rounded-lg">
                      <Label className="text-sm font-medium">Select Delivery Months</Label>
                      <div className="flex flex-wrap gap-3">
                        {availableMonths.map((month) => (
                          <label
                            key={month.code}
                            className="flex items-center space-x-2 cursor-pointer"
                          >
                            <Checkbox
                              checked={deliveryMonths.includes(month.code)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setDeliveryMonths([...deliveryMonths, month.code]);
                                } else {
                                  setDeliveryMonths(deliveryMonths.filter(m => m !== month.code));
                                  const newQtys = { ...newItem.monthlyQtys };
                                  delete newQtys[month.code];
                                  setNewItem({ ...newItem, monthlyQtys: newQtys });
                                }
                              }}
                            />
                            <span className="text-sm font-medium">{month.name}</span>
                          </label>
                        ))}
                      </div>
                      {deliveryMonths.length > 0 && (
                        <p className="text-xs text-muted-foreground">
                          Selected: {deliveryMonths.length} month(s) - Each lot gets 25% advance + 75% balance (45 days after delivery)
                        </p>
                      )}
                    </div>
                  )}

                  <Separator />

                  {/* Add Item Section */}
                  <div className="space-y-4">
                    <Label className="text-base font-semibold">Add Items</Label>
                    <div className="space-y-3">
                      <div className="grid grid-cols-5 gap-2">
                        <div className="col-span-2">
                          <Select
                            value={newItem.product_id || 'select'}
                            onValueChange={(value) => {
                              const product = products.find((p: Product) => p.id === value);
                              setNewItem({
                                ...newItem,
                                product_id: value === 'select' ? '' : value,
                                unit_price: product?.mrp || 0
                              });
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select product" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="select" disabled>Select product</SelectItem>
                              {products.filter((p: Product) => p.id && p.id.trim() !== '').map((p: Product) => (
                                <SelectItem key={p.id} value={p.id}>{p.name} ({p.sku})</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        {!isMultiDelivery && (
                          <Input
                            type="number"
                            min="1"
                            placeholder="Qty"
                            value={newItem.quantity}
                            onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 0 })}
                          />
                        )}
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          placeholder="Unit Price"
                          value={newItem.unit_price || ''}
                          onChange={(e) => setNewItem({ ...newItem, unit_price: parseFloat(e.target.value) || 0 })}
                          className={isMultiDelivery ? 'col-span-2' : ''}
                        />
                        {!isMultiDelivery && (
                          <Button type="button" onClick={handleAddItem}>
                            <Plus className="h-4 w-4" />
                          </Button>
                        )}
                      </div>

                      {/* Month-wise quantities for multi-delivery */}
                      {isMultiDelivery && deliveryMonths.length > 0 && newItem.product_id && (
                        <div className="p-3 border rounded-lg bg-muted/20 space-y-2">
                          <Label className="text-sm">Quantity per Month</Label>
                          <div className="flex flex-wrap gap-2">
                            {deliveryMonths.sort().map((month) => {
                              const monthData = availableMonths.find(m => m.code === month);
                              return (
                                <div key={month} className="flex items-center gap-1">
                                  <span className="text-xs font-medium w-16">{monthData?.name}:</span>
                                  <Input
                                    type="number"
                                    min="0"
                                    className="w-20 h-8"
                                    placeholder="0"
                                    value={newItem.monthlyQtys[month] || ''}
                                    onChange={(e) => {
                                      const qty = parseInt(e.target.value) || 0;
                                      setNewItem({
                                        ...newItem,
                                        monthlyQtys: { ...newItem.monthlyQtys, [month]: qty }
                                      });
                                    }}
                                  />
                                </div>
                              );
                            })}
                          </div>
                          <div className="flex items-center justify-between pt-2">
                            <span className="text-sm text-muted-foreground">
                              Total: {Object.values(newItem.monthlyQtys).reduce((sum, q) => sum + (q || 0), 0)} units
                            </span>
                            <Button type="button" onClick={handleAddItem} size="sm">
                              <Plus className="h-4 w-4 mr-1" /> Add Item
                            </Button>
                          </div>
                        </div>
                      )}

                      {isMultiDelivery && deliveryMonths.length === 0 && (
                        <p className="text-sm text-muted-foreground italic">
                          Please select at least one delivery month above
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Items List */}
                  {formData.items.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-base font-semibold">Order Items</Label>
                      <div className="border rounded-md">
                        <table className="w-full text-sm">
                          <thead className="bg-muted">
                            <tr>
                              <th className="px-3 py-2 text-left">Product</th>
                              <th className="px-3 py-2 text-right">Qty</th>
                              <th className="px-3 py-2 text-right">Unit Price</th>
                              <th className="px-3 py-2 text-right">GST %</th>
                              <th className="px-3 py-2 text-right">Total</th>
                              <th className="px-3 py-2"></th>
                            </tr>
                          </thead>
                          <tbody>
                            {formData.items.map((item, index) => (
                              <tr key={index} className="border-t">
                                <td className="px-3 py-2">
                                  <div>{item.product_name}</div>
                                  <div className="text-xs text-muted-foreground">{item.sku}</div>
                                  {item.monthly_quantities && Object.keys(item.monthly_quantities).length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {Object.entries(item.monthly_quantities).sort().map(([month, qty]) => (
                                        <Badge key={month} variant="secondary" className="text-xs">
                                          {availableMonths.find(m => m.code === month)?.name || month}: {qty}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-right">{item.quantity ?? 0}</td>
                                <td className="px-3 py-2 text-right">{formatCurrency(item.unit_price)}</td>
                                <td className="px-3 py-2 text-right">{item.gst_rate ?? 0}%</td>
                                <td className="px-3 py-2 text-right font-medium">
                                  {formatCurrency((item.quantity ?? 0) * item.unit_price * (1 + (item.gst_rate ?? 0) / 100))}
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
                              <td colSpan={4} className="px-3 py-2 text-right">Subtotal:</td>
                              <td className="px-3 py-2 text-right font-medium">{formatCurrency(totals.subtotal)}</td>
                              <td></td>
                            </tr>
                            <tr>
                              <td colSpan={4} className="px-3 py-2 text-right">GST:</td>
                              <td className="px-3 py-2 text-right font-medium">{formatCurrency(totals.gst)}</td>
                              <td></td>
                            </tr>
                            <tr className="border-t">
                              <td colSpan={4} className="px-3 py-2 text-right font-semibold">Grand Total:</td>
                              <td className="px-3 py-2 text-right font-bold text-lg">{formatCurrency(totals.total)}</td>
                              <td></td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>Notes</Label>
                    <Textarea
                      placeholder="Additional notes or instructions..."
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={resetForm}>Cancel</Button>
                  <Button onClick={handleCreatePO} disabled={createMutation.isPending}>
                    {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create Purchase Order
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="po_number"
        searchPlaceholder="Search PO number..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Submit Confirmation Dialog */}
      <AlertDialog open={isSubmitOpen} onOpenChange={setIsSubmitOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit for Approval</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to submit PO {selectedPO?.po_number} for approval?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => selectedPO && submitMutation.mutate(selectedPO.id)}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Submit
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* View Details Sheet */}
      <Sheet open={isViewOpen} onOpenChange={setIsViewOpen}>
        <SheetContent className="w-[600px] sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Purchase Order Details</SheetTitle>
            <SheetDescription>{selectedPO?.po_number}</SheetDescription>
          </SheetHeader>
          {selectedPO && (
            <div className="mt-6 space-y-6">
              <div className="flex items-center justify-between">
                <StatusBadge status={selectedPO.status} />
                <span className="text-sm text-muted-foreground">
                  {formatDate(selectedPO.created_at)}
                </span>
              </div>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Vendor</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="font-medium">{selectedPO.vendor?.name}</div>
                  <div className="text-sm text-muted-foreground font-mono">{selectedPO.vendor?.code}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Delivery Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Warehouse:</span>
                    <span>{selectedPO.warehouse?.name || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Expected Date:</span>
                    <span>{selectedPO.expected_delivery_date ? formatDate(selectedPO.expected_delivery_date) : '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Credit Days:</span>
                    <span>{selectedPO.credit_days} days</span>
                  </div>
                </CardContent>
              </Card>

              {selectedPO.items && selectedPO.items.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Package className="h-4 w-4" />
                      Items ({selectedPO.items.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {selectedPO.items.map((item, index) => (
                        <div key={index} className="flex justify-between items-center py-2 border-b last:border-0">
                          <div>
                            <div className="font-medium">{item.product_name || 'Product'}</div>
                            <div className="text-xs text-muted-foreground">
                              {item.quantity ?? item.quantity_ordered ?? 0} x {formatCurrency(item.unit_price)}
                            </div>
                          </div>
                          <div className="text-right font-medium">
                            {formatCurrency((item.quantity ?? item.quantity_ordered ?? 0) * item.unit_price)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card className="bg-muted/50">
                <CardContent className="pt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subtotal:</span>
                    <span>{formatCurrency(selectedPO.subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">GST:</span>
                    <span>{formatCurrency(selectedPO.gst_amount)}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between font-bold text-lg">
                    <span>Grand Total:</span>
                    <span>{formatCurrency(selectedPO.grand_total)}</span>
                  </div>
                </CardContent>
              </Card>

              {selectedPO.notes && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{selectedPO.notes}</p>
                  </CardContent>
                </Card>
              )}

              {/* Action Buttons in Details View */}
              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => handleDownload(selectedPO)}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
                <Button variant="outline" onClick={() => handlePrint(selectedPO)}>
                  <Printer className="mr-2 h-4 w-4" />
                  Print
                </Button>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Purchase Order</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete PO <strong>{selectedPO?.po_number}</strong>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => selectedPO && deleteMutation.mutate(selectedPO.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
