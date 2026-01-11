'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, FileText, Send, CheckCircle, X, Loader2, Trash2, Download, Printer, Package, Barcode, Lock } from 'lucide-react';
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
import { purchaseOrdersApi, purchaseRequisitionsApi, PurchaseRequisition, vendorsApi, warehousesApi, productsApi, serializationApi, companyApi, Company, ModelCodeReference, SupplierCode as SupplierCodeType, POSerialsResponse } from '@/lib/api';
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
  uom?: string;
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
  const searchParams = useSearchParams();
  const router = useRouter();
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
  const [urlPrId, setUrlPrId] = useState<string | null>(null);

  const [isMultiDelivery, setIsMultiDelivery] = useState(false);
  const [deliveryMonths, setDeliveryMonths] = useState<string[]>([]);
  const [nextPONumber, setNextPONumber] = useState<string>('');
  const [isLoadingPONumber, setIsLoadingPONumber] = useState(false);

  const [formData, setFormData] = useState({
    requisition_id: '',  // Required - PO must be linked to an approved PR
    vendor_id: '',
    delivery_warehouse_id: '',
    expected_delivery_date: '',
    credit_days: 30,
    advance_required: 0,  // Advance payment amount
    bill_to: null as any,  // Bill To address
    ship_to: null as any,  // Ship To address
    terms_and_conditions: '',  // Terms & Conditions (previously notes)
    items: [] as POItem[],
  });

  // Selected PR object for reference
  const [selectedPR, setSelectedPR] = useState<PurchaseRequisition | null>(null);

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

  // Open Purchase Requisitions query (for PR dropdown)
  const { data: openPRsData } = useQuery({
    queryKey: ['open-purchase-requisitions'],
    queryFn: () => purchaseRequisitionsApi.getOpenForPO(),
  });

  // Serialization queries
  const { data: modelCodesData } = useQuery({
    queryKey: ['model-codes'],
    queryFn: () => serializationApi.getModelCodes(true),
  });

  const { data: supplierCodesData } = useQuery({
    queryKey: ['supplier-codes'],
    queryFn: () => serializationApi.getSupplierCodes(true),
  });

  // Company data for Bill To address
  const { data: companyData } = useQuery({
    queryKey: ['company-primary'],
    queryFn: () => companyApi.getPrimary(),
  });

  // State for serial number preview in PO view
  const [poSerials, setPOSerials] = useState<POSerialsResponse | null>(null);
  const [loadingSerials, setLoadingSerials] = useState(false);

  // Handle URL parameters for Convert to PO navigation
  useEffect(() => {
    const createParam = searchParams.get('create');
    const prIdParam = searchParams.get('pr_id');

    if (createParam === 'true' && prIdParam) {
      setUrlPrId(prIdParam);
      setIsCreateOpen(true);
      // Clear URL params after handling
      router.replace('/procurement/purchase-orders', { scroll: false });
    }
  }, [searchParams, router]);

  // Fetch next PO number when dialog opens
  useEffect(() => {
    if (isCreateOpen) {
      const fetchNextPONumber = async () => {
        setIsLoadingPONumber(true);
        try {
          const result = await purchaseOrdersApi.getNextNumber();
          setNextPONumber(result.next_number);
        } catch (error) {
          console.error('Failed to fetch next PO number:', error);
        } finally {
          setIsLoadingPONumber(false);
        }
      };
      fetchNextPONumber();
    }
  }, [isCreateOpen]);

  // Auto-select PR when openPRsData loads and urlPrId is set
  useEffect(() => {
    if (urlPrId && openPRsData && openPRsData.length > 0 && isCreateOpen) {
      const pr = openPRsData.find((p: PurchaseRequisition) => p.id === urlPrId);
      if (pr) {
        handlePRSelect(urlPrId);
        setUrlPrId(null); // Clear after selection
      }
    }
  }, [urlPrId, openPRsData, isCreateOpen]);

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
      requisition_id: '',
      vendor_id: '',
      delivery_warehouse_id: '',
      expected_delivery_date: '',
      credit_days: 30,
      advance_required: 0,
      bill_to: null,
      ship_to: null,
      terms_and_conditions: '',
      items: [],
    });
    setSelectedPR(null);
    setNewItem({ product_id: '', quantity: 1, unit_price: 0, gst_rate: 18, monthlyQtys: {} });
    setIsMultiDelivery(false);
    setDeliveryMonths([]);
    setNextPONumber('');
    setIsCreateOpen(false);
  };

  const handleAddItem = () => {
    if (!selectedPR) {
      toast.error('Please select a Purchase Requisition first');
      return;
    }

    if (!newItem.product_id) {
      toast.error('Please select a product from the PR');
      return;
    }

    if (newItem.unit_price <= 0) {
      toast.error('Please enter a valid unit price');
      return;
    }

    // Get month-wise quantities (filter out zero values)
    const monthQtys = Object.entries(newItem.monthlyQtys).reduce((acc, [month, qty]) => {
      if (qty && qty > 0) acc[month] = qty;
      return acc;
    }, {} as Record<string, number>);

    if (Object.keys(monthQtys).length === 0) {
      toast.error('Please enter quantities for at least one delivery month');
      return;
    }

    const totalQty = Object.values(monthQtys).reduce((sum, q) => sum + q, 0);

    // Get product info from PR item
    const prItem = selectedPR.items.find(item => item.product_id === newItem.product_id);
    if (!prItem) {
      toast.error('Product not found in selected PR');
      return;
    }

    // Update delivery months for the PO
    const allMonths = new Set([...deliveryMonths, ...Object.keys(monthQtys)]);
    setDeliveryMonths(Array.from(allMonths).sort());

    // Enable multi-delivery mode since we're using month-wise quantities
    if (Object.keys(monthQtys).length > 0) {
      setIsMultiDelivery(true);
    }

    setFormData({
      ...formData,
      items: [...formData.items, {
        product_id: newItem.product_id,
        product_name: prItem.product_name,
        sku: prItem.sku,
        quantity: totalQty,
        unit_price: newItem.unit_price,
        gst_rate: newItem.gst_rate,
        uom: prItem.uom || 'Nos',
        monthly_quantities: monthQtys,
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
    // Validate: PR selection is mandatory
    if (!formData.requisition_id) {
      toast.error('Please select an approved Purchase Requisition first');
      return;
    }
    if (!formData.vendor_id || !formData.delivery_warehouse_id || formData.items.length === 0) {
      toast.error('Please fill all required fields and add at least one item');
      return;
    }

    // Validate: PO quantity cannot exceed PR quantity for any item
    const overLimitItems = formData.items.filter(item => {
      const prItem = selectedPR?.items.find(pi => pi.product_id === item.product_id);
      return (item.quantity ?? 0) > (prItem?.quantity_requested || 0);
    });
    if (overLimitItems.length > 0) {
      toast.error('PO quantity cannot exceed PR quantity. Please adjust quantities.');
      return;
    }

    createMutation.mutate({
      requisition_id: formData.requisition_id,  // Link PO to PR
      vendor_id: formData.vendor_id,
      delivery_warehouse_id: formData.delivery_warehouse_id,
      expected_delivery_date: formData.expected_delivery_date || undefined,
      credit_days: formData.credit_days,
      advance_required: formData.advance_required || 0,  // Include advance payment
      bill_to: formData.bill_to || undefined,  // Bill To address
      ship_to: formData.ship_to || undefined,  // Ship To address
      terms_and_conditions: formData.terms_and_conditions || undefined,  // Terms & Conditions
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

      // Fetch serial numbers for the PO
      setLoadingSerials(true);
      try {
        const serials = await serializationApi.getByPO(po.id);
        setPOSerials(serials);
      } catch {
        setPOSerials(null);
      } finally {
        setLoadingSerials(false);
      }
    } catch {
      setSelectedPO(po);
      setIsViewOpen(true);
      setPOSerials(null);
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
  const openPRs = openPRsData ?? [];
  const modelCodes = modelCodesData ?? [];
  const supplierCodes = supplierCodesData ?? [];
  const totals = calculateTotals();

  // Helper to get model code for a product
  const getModelCodeForProduct = (productId: string, productSku?: string): ModelCodeReference | undefined => {
    return modelCodes.find(mc => mc.product_id === productId || mc.product_sku === productSku);
  };

  // Helper to get supplier code for a vendor
  const getSupplierCodeForVendor = (vendorId: string): SupplierCodeType | undefined => {
    return supplierCodes.find(sc => sc.vendor_id === vendorId);
  };

  // Handle PR selection - auto-populate ALL data from PR including items with monthly quantities
  const handlePRSelect = (prId: string) => {
    const pr = openPRs.find(p => p.id === prId);
    setSelectedPR(pr || null);

    if (pr) {
      // Get preferred vendor from first item that has one
      const preferredVendorId = pr.items.find(item => item.preferred_vendor_id)?.preferred_vendor_id || '';

      // Convert PR items to PO items - inherit monthly quantities from PR
      const poItems: POItem[] = pr.items.map(item => ({
        product_id: item.product_id,
        product_name: item.product_name,
        sku: item.sku,
        quantity: item.quantity_requested,
        unit_price: item.estimated_unit_price || 0,
        gst_rate: 18, // Default GST rate
        uom: item.uom || 'Nos',
        monthly_quantities: item.monthly_quantities, // Inherit from PR
      }));

      // Check if multi-delivery and collect delivery months
      const allMonths = new Set<string>();
      pr.items.forEach(item => {
        if (item.monthly_quantities) {
          Object.keys(item.monthly_quantities).forEach(m => allMonths.add(m));
        }
      });
      const hasMonthlyBreakdown = allMonths.size > 0;

      setIsMultiDelivery(hasMonthlyBreakdown);
      setDeliveryMonths(Array.from(allMonths).sort());

      setFormData({
        ...formData,
        requisition_id: prId,
        vendor_id: preferredVendorId,
        delivery_warehouse_id: pr.delivery_warehouse_id,
        expected_delivery_date: pr.required_by_date || '',
        notes: pr.reason || '',
        items: poItems, // Auto-populate items from PR
      });
    } else {
      // Clear form if no PR selected
      setFormData({
        ...formData,
        requisition_id: '',
        vendor_id: '',
        delivery_warehouse_id: '',
        expected_delivery_date: '',
        notes: '',
        items: [],
      });
      setIsMultiDelivery(false);
      setDeliveryMonths([]);
    }
  };

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
            {['SENT_TO_VENDOR', 'CONFIRMED', 'PARTIALLY_RECEIVED'].includes(row.original.status) && (
              <DropdownMenuItem onClick={() => router.push(`/procurement/grn?create=true&po_id=${row.original.id}`)}>
                <Package className="mr-2 h-4 w-4" />
                Create GRN
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
                  {/* PO Number - Auto-generated, Read-only */}
                  <div className="space-y-2">
                    <Label htmlFor="po_number">PO Number (Auto-generated)</Label>
                    <div className="relative">
                      <Input
                        id="po_number"
                        placeholder={isLoadingPONumber ? "Loading..." : "PO/APL/YY-YY/0001"}
                        value={nextPONumber}
                        readOnly
                        disabled
                        className="bg-muted pr-8 font-mono"
                      />
                      <Lock className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>

                  {/* Purchase Requisition Selection - MANDATORY */}
                  <div className="space-y-2 p-3 border rounded-lg bg-blue-50/50">
                    <Label className="text-base font-semibold flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Purchase Requisition *
                      <span className="text-xs font-normal text-muted-foreground">(Required)</span>
                    </Label>
                    <Select
                      value={formData.requisition_id || 'select'}
                      onValueChange={(value) => handlePRSelect(value === 'select' ? '' : value)}
                    >
                      <SelectTrigger className={!formData.requisition_id ? 'border-amber-400' : ''}>
                        <SelectValue placeholder="Select an approved Purchase Requisition" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="select" disabled>Select an approved PR</SelectItem>
                        {openPRs.length === 0 ? (
                          <SelectItem value="none" disabled>No open PRs available</SelectItem>
                        ) : (
                          openPRs.map((pr) => (
                            <SelectItem key={pr.id} value={pr.id}>
                              {pr.requisition_number} - {pr.reason || 'No description'} ({formatCurrency(pr.estimated_total || 0)})
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    {selectedPR && (
                      <div className="text-xs text-muted-foreground mt-1 space-y-1">
                        <p><strong>Department:</strong> {selectedPR.requesting_department || 'N/A'}</p>
                        <p><strong>Items:</strong> {selectedPR.items.length} | <strong>Total:</strong> {formatCurrency(selectedPR.estimated_total || 0)}</p>
                        {selectedPR.required_by_date && <p><strong>Required By:</strong> {formatDate(selectedPR.required_by_date)}</p>}
                      </div>
                    )}
                    {!formData.requisition_id && openPRs.length === 0 && (
                      <p className="text-xs text-amber-600">
                        No approved Purchase Requisitions available. Create and approve a PR first.
                      </p>
                    )}
                  </div>

                  <Separator />

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Vendor *</Label>
                      <Select
                        value={formData.vendor_id || 'select'}
                        onValueChange={(value) => setFormData({ ...formData, vendor_id: value === 'select' ? '' : value })}
                        disabled={!formData.requisition_id}
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
                        disabled={!formData.requisition_id}
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
                  {/* Bill To & Ship To Section */}
                  <div className="space-y-4 p-4 border rounded-lg bg-blue-50/30">
                    <Label className="text-base font-semibold">Billing & Shipping Addresses</Label>

                    <div className="grid grid-cols-2 gap-4">
                      {/* Bill To */}
                      <div className="space-y-2">
                        <Label>Bill To (Invoice Address) *</Label>
                        <Select
                          value={formData.bill_to ? 'company' : 'select'}
                          onValueChange={(value) => {
                            if (value === 'company' && companyData) {
                              setFormData({
                                ...formData,
                                bill_to: {
                                  name: companyData.legal_name,
                                  address_line1: companyData.address_line1,
                                  address_line2: companyData.address_line2 || '',
                                  city: companyData.city,
                                  state: companyData.state,
                                  pincode: companyData.pincode,
                                  gstin: companyData.gstin,
                                  state_code: companyData.state_code,
                                }
                              });
                            } else {
                              setFormData({ ...formData, bill_to: null });
                            }
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select billing address" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="select" disabled>Select billing address</SelectItem>
                            {companyData && (
                              <SelectItem value="company">
                                {companyData.legal_name} - {companyData.city}
                              </SelectItem>
                            )}
                          </SelectContent>
                        </Select>
                        {formData.bill_to && (
                          <div className="text-xs text-muted-foreground p-2 bg-white rounded border">
                            <strong>{formData.bill_to.name}</strong><br />
                            {formData.bill_to.address_line1}<br />
                            {formData.bill_to.city}, {formData.bill_to.state} - {formData.bill_to.pincode}<br />
                            GSTIN: {formData.bill_to.gstin}
                          </div>
                        )}
                      </div>

                      {/* Ship To */}
                      <div className="space-y-2">
                        <Label>Ship To (Delivery Address) *</Label>
                        <Select
                          value={formData.ship_to ? (formData.ship_to.type || 'warehouse') : 'select'}
                          onValueChange={(value) => {
                            if (value === 'warehouse') {
                              const selectedWarehouse = warehouses.find((w: Warehouse) => w.id === formData.delivery_warehouse_id);
                              if (selectedWarehouse) {
                                setFormData({
                                  ...formData,
                                  ship_to: {
                                    type: 'warehouse',
                                    name: selectedWarehouse.name,
                                    address_line1: (selectedWarehouse as any).address_line1 || '',
                                    city: (selectedWarehouse as any).city || '',
                                    state: (selectedWarehouse as any).state || '',
                                    pincode: (selectedWarehouse as any).pincode || '',
                                  }
                                });
                              }
                            } else if (value === 'same_as_bill') {
                              setFormData({
                                ...formData,
                                ship_to: formData.bill_to ? { ...formData.bill_to, type: 'same_as_bill' } : null
                              });
                            } else {
                              setFormData({ ...formData, ship_to: null });
                            }
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select shipping address" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="select" disabled>Select shipping address</SelectItem>
                            <SelectItem value="warehouse">Delivery Warehouse Address</SelectItem>
                            <SelectItem value="same_as_bill">Same as Bill To</SelectItem>
                          </SelectContent>
                        </Select>
                        {formData.ship_to && (
                          <div className="text-xs text-muted-foreground p-2 bg-white rounded border">
                            <strong>{formData.ship_to.name}</strong><br />
                            {formData.ship_to.address_line1}<br />
                            {formData.ship_to.city}, {formData.ship_to.state} - {formData.ship_to.pincode}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Expected Delivery Date</Label>
                      <Input
                        type="date"
                        value={formData.expected_delivery_date}
                        onChange={(e) => setFormData({ ...formData, expected_delivery_date: e.target.value })}
                        disabled={isMultiDelivery || !formData.requisition_id}
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

                  {/* Advance Payment Section */}
                  <div className="space-y-2 p-3 border rounded-lg bg-green-50/50">
                    <Label className="text-base font-semibold">Advance Payment</Label>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="advance_required">Advance Amount (₹)</Label>
                        <Input
                          id="advance_required"
                          type="number"
                          min="0"
                          step="0.01"
                          placeholder="Enter advance payment amount"
                          value={formData.advance_required || ''}
                          onChange={(e) => setFormData({ ...formData, advance_required: parseFloat(e.target.value) || 0 })}
                        />
                        <p className="text-xs text-muted-foreground">
                          Amount to be paid in advance before delivery
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label>Advance Percentage</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="text"
                            readOnly
                            value={totals.total > 0 ? `${((formData.advance_required / totals.total) * 100).toFixed(1)}%` : '0%'}
                            className="bg-muted w-20"
                          />
                          <span className="text-sm text-muted-foreground">of total {formatCurrency(totals.total)}</span>
                        </div>
                        {/* Quick percentage buttons */}
                        <div className="flex gap-1 mt-1">
                          {[10, 25, 50].map((pct) => (
                            <Button
                              key={pct}
                              type="button"
                              variant="outline"
                              size="sm"
                              className="text-xs h-6 px-2"
                              onClick={() => setFormData({ ...formData, advance_required: Math.round((totals.total * pct / 100) * 100) / 100 })}
                            >
                              {pct}%
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Items from PR - Auto-populated */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label className="text-base font-semibold">Items from Purchase Requisition</Label>
                      {selectedPR && formData.items.length > 0 && (
                        <Badge variant="secondary">{formData.items.length} item(s)</Badge>
                      )}
                    </div>

                    {!selectedPR ? (
                      <p className="text-sm text-muted-foreground italic p-4 border rounded-lg bg-muted/20">
                        Please select a Purchase Requisition first - items will be auto-populated
                      </p>
                    ) : formData.items.length === 0 ? (
                      <p className="text-sm text-amber-600 p-4 border rounded-lg bg-amber-50">
                        Selected PR has no items. Please select a different PR.
                      </p>
                    ) : (
                      <div className="p-3 border rounded-lg bg-green-50/30 space-y-2">
                        <p className="text-xs text-muted-foreground">
                          Items inherited from PR. You can redistribute month-wise quantities (total cannot exceed PR qty) and adjust prices.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Month Selection for PO (can differ from PR) */}
                  {selectedPR && formData.items.length > 0 && isMultiDelivery && (
                    <div className="space-y-2 border rounded-lg p-3 bg-blue-50/50">
                      <Label className="text-sm font-medium">PO Delivery Months</Label>
                      <p className="text-xs text-muted-foreground mb-2">
                        You can redistribute quantities across different months. Select the months for this PO.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {availableMonths.map((month) => (
                          <Button
                            key={month.code}
                            type="button"
                            size="sm"
                            variant={deliveryMonths.includes(month.code) ? 'default' : 'outline'}
                            onClick={() => {
                              if (deliveryMonths.includes(month.code)) {
                                setDeliveryMonths(deliveryMonths.filter(m => m !== month.code));
                              } else {
                                setDeliveryMonths([...deliveryMonths, month.code].sort());
                              }
                            }}
                          >
                            {month.name}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Items List - Editable Prices and Monthly Quantities */}
                  {formData.items.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-base font-semibold">Order Items</Label>
                      <div className="border rounded-md overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-muted">
                            <tr>
                              <th className="px-3 py-2 text-left">Product</th>
                              <th className="px-3 py-2 text-center text-xs">PR Max</th>
                              {isMultiDelivery && deliveryMonths.map(month => (
                                <th key={month} className="px-2 py-2 text-center text-xs">
                                  {availableMonths.find(m => m.code === month)?.name || month}
                                </th>
                              ))}
                              <th className="px-3 py-2 text-right">PO Qty</th>
                              <th className="px-3 py-2 text-right">Unit Price</th>
                              <th className="px-3 py-2 text-right">GST %</th>
                              <th className="px-3 py-2 text-right">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {formData.items.map((item, index) => {
                              // Get PR item to know max quantity
                              const prItem = selectedPR?.items.find(pi => pi.product_id === item.product_id);
                              const prMaxQty = prItem?.quantity_requested || 0;
                              const currentTotal = item.quantity ?? 0;
                              const isOverLimit = currentTotal > prMaxQty;

                              return (
                                <tr key={index} className={`border-t ${isOverLimit ? 'bg-red-50' : ''}`}>
                                  <td className="px-3 py-2">
                                    <div className="font-medium">{item.product_name}</div>
                                    <div className="text-xs text-muted-foreground">{item.sku}</div>
                                  </td>
                                  <td className="px-3 py-2 text-center">
                                    <Badge variant="outline" className="text-xs">
                                      {prMaxQty}
                                    </Badge>
                                  </td>
                                  {isMultiDelivery && deliveryMonths.map(month => (
                                    <td key={month} className="px-2 py-2">
                                      <Input
                                        type="number"
                                        min="0"
                                        className="w-16 h-8 text-center"
                                        value={item.monthly_quantities?.[month] || ''}
                                        onChange={(e) => {
                                          const qty = parseInt(e.target.value) || 0;
                                          const newItems = [...formData.items];
                                          const newMonthlyQtys = { ...newItems[index].monthly_quantities, [month]: qty };
                                          // Remove zero values
                                          Object.keys(newMonthlyQtys).forEach(k => {
                                            if (!newMonthlyQtys[k]) delete newMonthlyQtys[k];
                                          });
                                          // Calculate new total
                                          const newTotal = Object.values(newMonthlyQtys).reduce((sum, q) => sum + (q || 0), 0);
                                          newItems[index] = {
                                            ...newItems[index],
                                            monthly_quantities: newMonthlyQtys,
                                            quantity: newTotal,
                                          };
                                          setFormData({ ...formData, items: newItems });
                                        }}
                                      />
                                    </td>
                                  ))}
                                  <td className="px-3 py-2 text-right">
                                    {isMultiDelivery ? (
                                      <span className={`font-medium ${isOverLimit ? 'text-red-600' : ''}`}>
                                        {currentTotal}
                                        {isOverLimit && <span className="text-xs ml-1">!</span>}
                                      </span>
                                    ) : (
                                      <Input
                                        type="number"
                                        min="1"
                                        max={prMaxQty}
                                        className={`w-20 h-8 text-right ${isOverLimit ? 'border-red-500' : ''}`}
                                        value={item.quantity || ''}
                                        onChange={(e) => {
                                          const qty = parseInt(e.target.value) || 0;
                                          const newItems = [...formData.items];
                                          newItems[index] = { ...newItems[index], quantity: qty };
                                          setFormData({ ...formData, items: newItems });
                                        }}
                                      />
                                    )}
                                  </td>
                                  <td className="px-3 py-2">
                                    <Input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      className="w-24 h-8 text-right ml-auto"
                                      value={item.unit_price || ''}
                                      onChange={(e) => {
                                        const newItems = [...formData.items];
                                        newItems[index] = { ...newItems[index], unit_price: parseFloat(e.target.value) || 0 };
                                        setFormData({ ...formData, items: newItems });
                                      }}
                                    />
                                  </td>
                                  <td className="px-3 py-2">
                                    <Input
                                      type="number"
                                      min="0"
                                      max="28"
                                      className="w-16 h-8 text-right ml-auto"
                                      value={item.gst_rate ?? 18}
                                      onChange={(e) => {
                                        const newItems = [...formData.items];
                                        newItems[index] = { ...newItems[index], gst_rate: parseFloat(e.target.value) || 0 };
                                        setFormData({ ...formData, items: newItems });
                                      }}
                                    />
                                  </td>
                                  <td className="px-3 py-2 text-right font-medium">
                                    {formatCurrency((item.quantity ?? 0) * item.unit_price * (1 + (item.gst_rate ?? 0) / 100))}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                          <tfoot className="bg-muted/50">
                            <tr className="border-t">
                              <td colSpan={isMultiDelivery ? deliveryMonths.length + 5 : 5} className="px-3 py-2 text-right">Subtotal:</td>
                              <td className="px-3 py-2 text-right font-medium">{formatCurrency(totals.subtotal)}</td>
                            </tr>
                            <tr>
                              <td colSpan={isMultiDelivery ? deliveryMonths.length + 5 : 5} className="px-3 py-2 text-right">GST:</td>
                              <td className="px-3 py-2 text-right font-medium">{formatCurrency(totals.gst)}</td>
                            </tr>
                            <tr className="border-t">
                              <td colSpan={isMultiDelivery ? deliveryMonths.length + 5 : 5} className="px-3 py-2 text-right font-semibold">Grand Total:</td>
                              <td className="px-3 py-2 text-right font-bold text-lg">{formatCurrency(totals.total)}</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                      {/* Validation Warning */}
                      {formData.items.some((item, idx) => {
                        const prItem = selectedPR?.items.find(pi => pi.product_id === item.product_id);
                        return (item.quantity ?? 0) > (prItem?.quantity_requested || 0);
                      }) && (
                        <p className="text-sm text-red-600 p-2 bg-red-50 rounded">
                          Warning: Some items exceed PR quantity. PO quantity cannot be more than PR quantity.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Serial Numbers Preview Section - Lot-wise */}
                  {formData.items.length > 0 && isMultiDelivery && deliveryMonths.length > 0 && (
                    <div className="space-y-2 p-4 border rounded-lg bg-purple-50/50">
                      <Label className="text-base font-semibold flex items-center gap-2">
                        <Barcode className="h-4 w-4" />
                        Serial Numbers Preview (Lot-wise)
                      </Label>
                      <p className="text-xs text-muted-foreground mb-2">
                        <strong>System Generated:</strong> Serial numbers will be auto-assigned when PO is created
                      </p>
                      <div className="border rounded-md bg-background">
                        <table className="w-full text-sm">
                          <thead className="bg-muted">
                            <tr>
                              <th className="px-3 py-2 text-left">Lot (Month)</th>
                              <th className="px-3 py-2 text-right">Qty</th>
                              <th className="px-3 py-2 text-center">Serial Range (Preview)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(() => {
                              // Calculate quantities per month
                              const monthQtys: Record<string, number> = {};
                              formData.items.forEach(item => {
                                if (item.monthly_quantities) {
                                  Object.entries(item.monthly_quantities).forEach(([month, qty]) => {
                                    monthQtys[month] = (monthQtys[month] || 0) + (qty || 0);
                                  });
                                }
                              });

                              // Sort months and calculate serial ranges
                              const sortedMonths = Object.keys(monthQtys).sort();
                              let runningSerial = 1; // Preview starts from 1 (actual will continue from last)
                              const totalQty = Object.values(monthQtys).reduce((sum, q) => sum + q, 0);

                              return (
                                <>
                                  {sortedMonths.map((month, idx) => {
                                    const qty = monthQtys[month];
                                    const startSerial = runningSerial;
                                    const endSerial = runningSerial + qty - 1;
                                    runningSerial = endSerial + 1;

                                    const monthName = availableMonths.find(m => m.code === month)?.name || month;

                                    return (
                                      <tr key={month} className="border-t">
                                        <td className="px-3 py-2 font-medium">
                                          LOT {idx + 1} ({monthName})
                                        </td>
                                        <td className="px-3 py-2 text-right">{qty.toLocaleString()}</td>
                                        <td className="px-3 py-2 text-center">
                                          <Badge variant="outline" className="font-mono text-xs">
                                            {startSerial.toLocaleString()} - {endSerial.toLocaleString()}
                                          </Badge>
                                        </td>
                                      </tr>
                                    );
                                  })}
                                  <tr className="border-t bg-muted/50 font-medium">
                                    <td className="px-3 py-2">TOTAL</td>
                                    <td className="px-3 py-2 text-right">{totalQty.toLocaleString()}</td>
                                    <td className="px-3 py-2 text-center">
                                      <Badge variant="secondary" className="font-mono text-xs">
                                        1 - {totalQty.toLocaleString()}
                                      </Badge>
                                    </td>
                                  </tr>
                                </>
                              );
                            })()}
                          </tbody>
                        </table>
                      </div>
                      <p className="text-xs text-muted-foreground italic">
                        Note: Actual serial numbers will continue from last PO's ending serial. Preview shows relative range.
                      </p>
                    </div>
                  )}

                  {/* Terms & Conditions Section */}
                  <div className="space-y-2 p-4 border rounded-lg bg-amber-50/30">
                    <Label className="text-base font-semibold">Terms & Conditions</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Enter the terms and conditions for this Purchase Order. These will appear on the printed PO.
                    </p>
                    <Textarea
                      placeholder="Enter terms and conditions for this PO...&#10;&#10;Example:&#10;1. Delivery must be as per schedule mentioned above.&#10;2. All goods must be in original packing with serial numbers as specified.&#10;3. Payment will be released as per lot-wise schedule.&#10;4. Quality check will be done before acceptance."
                      value={formData.terms_and_conditions}
                      onChange={(e) => setFormData({ ...formData, terms_and_conditions: e.target.value })}
                      rows={6}
                      className="font-mono text-sm"
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

              {/* Delivery Schedule & Lot-wise Payment Plan */}
              {(selectedPO as any).delivery_schedules && (selectedPO as any).delivery_schedules.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Delivery Schedule & Lot-wise Payment Plan
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="border rounded-md overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted">
                          <tr>
                            <th className="px-3 py-2 text-left">Lot</th>
                            <th className="px-3 py-2 text-right">Qty</th>
                            <th className="px-3 py-2 text-center">Serial No. Range</th>
                            <th className="px-3 py-2 text-right">Value</th>
                            <th className="px-3 py-2 text-center">Delivery Date</th>
                            <th className="px-3 py-2 text-center">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(selectedPO as any).delivery_schedules.map((schedule: any) => (
                            <tr key={schedule.id} className="border-t">
                              <td className="px-3 py-2 font-medium">{schedule.lot_name}</td>
                              <td className="px-3 py-2 text-right">{schedule.total_quantity}</td>
                              <td className="px-3 py-2 text-center font-mono">
                                {schedule.serial_number_start && schedule.serial_number_end ? (
                                  <Badge variant="outline" className="font-mono text-xs">
                                    {schedule.serial_number_start} - {schedule.serial_number_end}
                                  </Badge>
                                ) : (
                                  <span className="text-muted-foreground text-xs">-</span>
                                )}
                              </td>
                              <td className="px-3 py-2 text-right">{formatCurrency(schedule.lot_total)}</td>
                              <td className="px-3 py-2 text-center text-xs">
                                {formatDate(schedule.expected_delivery_date)}
                              </td>
                              <td className="px-3 py-2 text-center">
                                <StatusBadge status={schedule.status} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot className="bg-muted/50">
                          <tr className="border-t font-medium">
                            <td className="px-3 py-2">Total</td>
                            <td className="px-3 py-2 text-right">
                              {(selectedPO as any).delivery_schedules.reduce((sum: number, s: any) => sum + s.total_quantity, 0)}
                            </td>
                            <td className="px-3 py-2 text-center font-mono text-xs">
                              {(() => {
                                const schedules = (selectedPO as any).delivery_schedules;
                                const first = schedules[0]?.serial_number_start;
                                const last = schedules[schedules.length - 1]?.serial_number_end;
                                return first && last ? `${first} - ${last}` : '-';
                              })()}
                            </td>
                            <td className="px-3 py-2 text-right">
                              {formatCurrency((selectedPO as any).delivery_schedules.reduce((sum: number, s: any) => sum + parseFloat(s.lot_total || 0), 0))}
                            </td>
                            <td colSpan={2}></td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Serial Numbers Section */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Barcode className="h-4 w-4" />
                    Serial Numbers
                    {poSerials && poSerials.total > 0 && (
                      <Badge variant="secondary" className="ml-2">{poSerials.total}</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loadingSerials ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      <span className="ml-2 text-sm text-muted-foreground">Loading serials...</span>
                    </div>
                  ) : poSerials && poSerials.total > 0 ? (
                    <div className="space-y-3">
                      {/* Status Summary */}
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(poSerials.by_status).map(([status, count]) => (
                          status !== 'total' && (
                            <Badge key={status} variant={status === 'received' ? 'default' : 'secondary'}>
                              {status}: {count}
                            </Badge>
                          )
                        ))}
                      </div>

                      {/* Serial Numbers by Model */}
                      <div className="border rounded-md max-h-48 overflow-y-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-muted sticky top-0">
                            <tr>
                              <th className="px-3 py-2 text-left">Model</th>
                              <th className="px-3 py-2 text-left">Barcode Range</th>
                              <th className="px-3 py-2 text-right">Count</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(() => {
                              // Group serials by model_code
                              const byModel: Record<string, { barcodes: string[]; count: number }> = {};
                              poSerials.serials.forEach(s => {
                                if (!byModel[s.model_code]) {
                                  byModel[s.model_code] = { barcodes: [], count: 0 };
                                }
                                byModel[s.model_code].barcodes.push(s.barcode);
                                byModel[s.model_code].count++;
                              });

                              return Object.entries(byModel).map(([model, data]) => (
                                <tr key={model} className="border-t">
                                  <td className="px-3 py-2 font-mono font-medium">{model}</td>
                                  <td className="px-3 py-2">
                                    <span className="font-mono text-xs">
                                      {data.barcodes[0]}
                                      {data.barcodes.length > 1 && (
                                        <> ... {data.barcodes[data.barcodes.length - 1]}</>
                                      )}
                                    </span>
                                  </td>
                                  <td className="px-3 py-2 text-right">{data.count}</td>
                                </tr>
                              ));
                            })()}
                          </tbody>
                        </table>
                      </div>

                      {/* Export Button */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          try {
                            const csv = await serializationApi.exportPOSerials(selectedPO.id, 'csv');
                            const blob = new Blob([csv], { type: 'text/csv' });
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `serials_${selectedPO.po_number}.csv`;
                            a.click();
                            window.URL.revokeObjectURL(url);
                            toast.success('Serial numbers exported');
                          } catch {
                            toast.error('Failed to export serials');
                          }
                        }}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Export Serials (CSV)
                      </Button>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-sm text-muted-foreground">
                        No serial numbers generated yet.
                      </p>
                      {selectedPO.status === 'APPROVED' && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Serials will be generated when PO is sent to vendor.
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

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
