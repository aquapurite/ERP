'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import {
  MoreHorizontal, Plus, Eye, Package, CheckCircle, XCircle,
  Loader2, Barcode, ClipboardList, CalendarIcon, AlertTriangle,
  Download, Printer, Trash2, Pencil
} from 'lucide-react';
import { format } from 'date-fns';
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
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { grnApi, purchaseOrdersApi, warehousesApi } from '@/lib/api';
import { formatDate, formatCurrency, cn } from '@/lib/utils';

interface GRN {
  id: string;
  grn_number: string;
  grn_type?: 'INVENTORY' | 'ASSET';
  po_id: string;
  po_number?: string;
  warehouse_id: string;
  status: 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'PUT_AWAY_PENDING' | 'PENDING_QC';
  grn_date?: string;
  received_date?: string;
  total_received: number;
  total_rejected: number;
  total_quantity_received?: number;
  total_quantity_accepted?: number;
  total_quantity_rejected?: number;
  total_value?: number;
  notes?: string;
  vendor_challan_number?: string;
  vendor_challan_date?: string;
  transporter_name?: string;
  vehicle_number?: string;
  lr_number?: string;
  e_way_bill_number?: string;
  receiving_remarks?: string;
  created_at: string;
  vendor_name?: string;
  warehouse_name?: string;
  warehouse?: { name: string; code?: string };
  vendor?: { name: string; code?: string; vendor_code?: string };
  purchase_order?: {
    po_number: string;
    vendor?: { name: string };
    items?: POItem[];
  };
  items?: GRNItem[];
}

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
}

interface GRNItem {
  id: string;
  po_item_id?: string;
  product_id: string;
  product_name: string;
  sku: string;
  part_code?: string;
  sub_item_code?: string;
  hsn_code?: string;
  quantity_expected?: number;
  quantity_received?: number;
  quantity_accepted?: number;
  quantity_rejected?: number;
  received_quantity?: number;
  rejected_quantity?: number;
  unit_price?: number;
  accepted_value?: number;
  batch_number?: string;
  manufacturing_date?: string;
  expiry_date?: string;
  serial_numbers?: string[];
  bin_location?: string;
  qc_result?: string;
  qc_status?: 'PENDING' | 'PASSED' | 'FAILED';
  rejection_reason?: string;
  remarks?: string;
  serials?: string[];
}

interface PurchaseOrder {
  id: string;
  po_number: string;
  status: string;
  vendor?: { name: string; code?: string; vendor_code?: string };
  delivery_warehouse_id?: string;
  warehouse_id?: string;
  warehouse?: { name: string };
  total_amount?: number;
  grand_total?: number;
  items?: POItem[];
}

interface Warehouse {
  id: string;
  name: string;
  code: string;
}

const statusOptions = [
  { label: 'All Statuses', value: 'all' },
  { label: 'Draft', value: 'DRAFT' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Cancelled', value: 'CANCELLED' },
];

// Separate component for actions to use hooks properly
function GRNActionsCell({
  grn,
  onView,
  onEdit,
  onComplete,
  onDownload,
  onPrint,
  onDelete,
  isSuperAdmin
}: {
  grn: GRN;
  onView: (grn: GRN) => void;
  onEdit: (grn: GRN) => void;
  onComplete: (grn: GRN) => void;
  onDownload: (grn: GRN) => void;
  onPrint: (grn: GRN) => void;
  onDelete: (grn: GRN) => void;
  isSuperAdmin: boolean;
}) {
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
        <DropdownMenuItem onClick={() => onView(grn)}>
          <Eye className="mr-2 h-4 w-4" />
          View Details
        </DropdownMenuItem>
        {grn.status !== 'CANCELLED' && grn.status !== 'COMPLETED' && (
          <DropdownMenuItem onClick={() => onEdit(grn)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit GRN
          </DropdownMenuItem>
        )}
        <DropdownMenuItem onClick={() => onDownload(grn)}>
          <Download className="mr-2 h-4 w-4" />
          Download PDF
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onPrint(grn)}>
          <Printer className="mr-2 h-4 w-4" />
          Print
        </DropdownMenuItem>
        {grn.status === 'IN_PROGRESS' && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onComplete(grn)}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Complete GRN
            </DropdownMenuItem>
          </>
        )}
        {isSuperAdmin && grn.status !== 'COMPLETED' && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => onDelete(grn)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete GRN
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default function GRNPage() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { permissions } = useAuth();
  const isSuperAdmin = permissions?.is_super_admin ?? false;
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedGRN, setSelectedGRN] = useState<GRN | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [grnToComplete, setGrnToComplete] = useState<GRN | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [grnToDelete, setGrnToDelete] = useState<GRN | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editGrn, setEditGrn] = useState<GRN | null>(null);
  const [editFormData, setEditFormData] = useState({
    vendor_challan_number: '',
    vendor_challan_date: '',
    transporter_name: '',
    vehicle_number: '',
    lr_number: '',
    e_way_bill_number: '',
    receiving_remarks: '',
  });

  // URL parameter handling for PO pre-selection
  const [urlPoId, setUrlPoId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    po_id: '',
    warehouse_id: '',
    received_date: new Date(),
    notes: '',
    vendor_challan_number: '',
    vehicle_number: '',
  });

  // Full PO details fetched on selection (list API doesn't return items)
  const [selectedPODetails, setSelectedPODetails] = useState<PurchaseOrder | null>(null);
  const [isLoadingPO, setIsLoadingPO] = useState(false);

  // Item quantities state - maps po_item_id to received quantity
  const [itemQuantities, setItemQuantities] = useState<Record<string, number>>({});

  // Full GRN details loading
  const [isLoadingGRNDetails, setIsLoadingGRNDetails] = useState(false);

  // Serial scanning state
  const [serialInput, setSerialInput] = useState('');
  const [scannedSerials, setScannedSerials] = useState<string[]>([]);

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['grn', page, pageSize, statusFilter],
    queryFn: () => grnApi.list({
      page: page + 1,
      size: pageSize,
      status: statusFilter !== 'all' ? statusFilter : undefined,
    }),
  });

  // Fetch POs that can have GRN created
  // Valid POStatus values: APPROVED, SENT_TO_VENDOR, ACKNOWLEDGED, PARTIALLY_RECEIVED
  // Note: APPROVED included because goods can arrive after approval but before formal send-to-vendor
  const { data: purchaseOrders } = useQuery({
    queryKey: ['purchase-orders-for-grn'],
    queryFn: async () => {
      // Fetch POs with statuses that allow GRN creation
      const results = await Promise.all([
        purchaseOrdersApi.list({ status: 'APPROVED', size: 100 }),
        purchaseOrdersApi.list({ status: 'SENT_TO_VENDOR', size: 100 }),
        purchaseOrdersApi.list({ status: 'ACKNOWLEDGED', size: 100 }),
        purchaseOrdersApi.list({ status: 'PARTIALLY_RECEIVED', size: 100 }),
      ]);
      // Combine all results
      const allItems = [
        ...(results[0]?.items || []),
        ...(results[1]?.items || []),
        ...(results[2]?.items || []),
        ...(results[3]?.items || []),
      ];
      return { items: allItems };
    },
  });

  // Handle URL parameters for Create GRN from PO page
  useEffect(() => {
    const createParam = searchParams.get('create');
    const poIdParam = searchParams.get('po_id');

    if (createParam === 'true') {
      setIsCreateDialogOpen(true);
      if (poIdParam) {
        setUrlPoId(poIdParam);
      }
      // Clear URL params after handling
      router.replace('/procurement/grn', { scroll: false });
    }
  }, [searchParams, router]);

  // Auto-select PO when purchaseOrders loads and urlPoId is set
  useEffect(() => {
    if (urlPoId && purchaseOrders?.items && purchaseOrders.items.length > 0 && isCreateDialogOpen) {
      const po = purchaseOrders.items.find((p: PurchaseOrder) => p.id === urlPoId);
      if (po) {
        handlePOChange(urlPoId);
        setUrlPoId(null); // Clear after selection
      }
    }
  }, [urlPoId, purchaseOrders, isCreateDialogOpen]);

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => warehousesApi.list({ is_active: true }),
  });

  // selectedPODetails holds the full PO (fetched on selection); fall back to list summary
  const selectedPO = selectedPODetails || (purchaseOrders?.items ?? []).find((po: PurchaseOrder) => po.id === formData.po_id);

  // Mutations
  const createMutation = useMutation({
    mutationFn: grnApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grn'] });
      toast.success('GRN created successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create GRN'),
  });

  const completeMutation = useMutation({
    mutationFn: (id: string) => grnApi.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grn'] });
      toast.success('GRN completed successfully');
      setGrnToComplete(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to complete GRN'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => grnApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grn'] });
      toast.success('GRN deleted successfully');
      setIsDeleteOpen(false);
      setGrnToDelete(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete GRN'),
  });

  const handleDownload = async (grn: GRN) => {
    try {
      // Fetch HTML with auth token, then open in new tab
      const htmlContent = await grnApi.download(grn.id);
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => window.URL.revokeObjectURL(url);
      }
      toast.success('Opening GRN for download/print');
    } catch {
      toast.error('Failed to download GRN');
    }
  };

  const handlePrint = async (grn: GRN) => {
    try {
      // Fetch HTML with auth token, then open in new tab for printing
      const htmlContent = await grnApi.download(grn.id);
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
      toast.error('Failed to print GRN');
    }
  };

  const scanMutation = useMutation({
    mutationFn: ({ id, serial }: { id: string; serial: string }) =>
      grnApi.scanSerial(id, { serial_number: serial }),
    onSuccess: (_, variables) => {
      setScannedSerials(prev => [...prev, variables.serial]);
      setSerialInput('');
      toast.success('Serial scanned successfully');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to scan serial'),
  });

  const resetForm = () => {
    setFormData({
      po_id: '',
      warehouse_id: '',
      received_date: new Date(),
      notes: '',
      vendor_challan_number: '',
      vehicle_number: '',
    });
    setItemQuantities({});
    setSelectedPODetails(null);
    setScannedSerials([]);
    setSerialInput('');
    setIsCreateDialogOpen(false);
  };

  const handleCreate = () => {
    if (!formData.po_id || !formData.warehouse_id) {
      toast.error('Please select a Purchase Order and Warehouse');
      return;
    }

    // Build items array from PO items and entered quantities
    const items: {
      po_item_id: string;
      product_id: string;
      variant_id?: string;
      product_name: string;
      sku: string;
      sub_item_code?: string;
      quantity_expected: number;
      quantity_received: number;
      quantity_accepted: number;
      uom: string;
    }[] = [];

    const po = selectedPODetails || (purchaseOrders?.items ?? []).find((p: PurchaseOrder) => p.id === formData.po_id);
    if (!po?.items || po.items.length === 0) {
      toast.error('No items found in selected PO');
      return;
    }

    // Build items with quantities
    for (const poItem of po.items) {
      if (!poItem.id) continue;

      const receivedQty = itemQuantities[poItem.id] || 0;
      if (receivedQty <= 0) continue; // Skip items with 0 quantity

      const ordered = poItem.quantity_ordered || poItem.quantity || 0;
      const alreadyReceived = poItem.quantity_received || 0;
      const pending = ordered - alreadyReceived;

      // Validate quantity doesn't exceed pending
      if (receivedQty > pending) {
        toast.error(`Cannot receive ${receivedQty} units for ${poItem.product_name}. Only ${pending} units pending.`);
        return;
      }

      items.push({
        po_item_id: poItem.id,
        product_id: poItem.product_id,
        product_name: poItem.product_name || 'Unknown Product',
        sku: poItem.sku || '',
        sub_item_code: (poItem as any).sub_item_code || undefined,
        quantity_expected: pending,
        quantity_received: receivedQty,
        quantity_accepted: receivedQty, // Default: all received are accepted
        uom: 'PCS',
      });
    }

    if (items.length === 0) {
      toast.error('Please enter quantity for at least one item');
      return;
    }

    createMutation.mutate({
      purchase_order_id: formData.po_id,
      warehouse_id: formData.warehouse_id,
      grn_date: format(formData.received_date, 'yyyy-MM-dd'),
      vendor_challan_number: formData.vendor_challan_number || undefined,
      vehicle_number: formData.vehicle_number || undefined,
      receiving_remarks: formData.notes || undefined,
      qc_required: false, // Default to no QC
      items,
    });
  };

  const handlePOChange = async (poId: string) => {
    const poSummary = (purchaseOrders?.items ?? []).find((p: PurchaseOrder) => p.id === poId);
    setFormData({
      ...formData,
      po_id: poId,
      warehouse_id: poSummary?.delivery_warehouse_id || poSummary?.warehouse_id || '',
    });
    setSelectedPODetails(null);
    setItemQuantities({});

    // Fetch full PO details to get items and accurate amount
    setIsLoadingPO(true);
    try {
      const fullPO = await purchaseOrdersApi.getById(poId);
      setSelectedPODetails(fullPO);
      if (fullPO?.items) {
        const initialQuantities: Record<string, number> = {};
        fullPO.items.forEach((item: POItem) => {
          if (item.id) {
            const ordered = item.quantity_ordered || item.quantity || 0;
            const received = item.quantity_received || 0;
            const pending = ordered - received;
            initialQuantities[item.id] = Math.max(0, pending);
          }
        });
        setItemQuantities(initialQuantities);
      }
      // Auto-fill warehouse from full PO if not set
      if (fullPO?.delivery_warehouse_id || fullPO?.warehouse_id) {
        setFormData(prev => ({
          ...prev,
          warehouse_id: prev.warehouse_id || fullPO.delivery_warehouse_id || fullPO.warehouse_id || '',
        }));
      }
    } catch {
      toast.error('Failed to load PO details');
    } finally {
      setIsLoadingPO(false);
    }
  };

  const handleView = async (grn: GRN) => {
    setSelectedGRN(grn);
    setIsDetailsOpen(true);
    setIsLoadingGRNDetails(true);
    try {
      const fullGRN = await grnApi.getById(grn.id);
      setSelectedGRN(fullGRN);
    } catch {
      // Keep list data if detail fetch fails
    } finally {
      setIsLoadingGRNDetails(false);
    }
  };

  const handleEdit = (grn: GRN) => {
    setEditGrn(grn);
    setEditFormData({
      vendor_challan_number: grn.vendor_challan_number || '',
      vendor_challan_date: grn.vendor_challan_date || '',
      transporter_name: grn.transporter_name || '',
      vehicle_number: grn.vehicle_number || '',
      lr_number: grn.lr_number || '',
      e_way_bill_number: grn.e_way_bill_number || '',
      receiving_remarks: grn.receiving_remarks || grn.notes || '',
    });
    setIsEditOpen(true);
  };

  const handleEditSubmit = async () => {
    if (!editGrn) return;
    try {
      const payload: Record<string, string> = {};
      if (editFormData.vendor_challan_number) payload.vendor_challan_number = editFormData.vendor_challan_number;
      if (editFormData.vendor_challan_date) payload.vendor_challan_date = editFormData.vendor_challan_date;
      if (editFormData.transporter_name) payload.transporter_name = editFormData.transporter_name;
      if (editFormData.vehicle_number) payload.vehicle_number = editFormData.vehicle_number;
      if (editFormData.lr_number) payload.lr_number = editFormData.lr_number;
      if (editFormData.e_way_bill_number) payload.e_way_bill_number = editFormData.e_way_bill_number;
      if (editFormData.receiving_remarks) payload.receiving_remarks = editFormData.receiving_remarks;

      await grnApi.update(editGrn.id, payload);
      toast.success(`GRN ${editGrn.grn_number} updated`);
      setIsEditOpen(false);
      setEditGrn(null);
      queryClient.invalidateQueries({ queryKey: ['grns'] });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to update GRN');
    }
  };

  const handleComplete = (grn: GRN) => {
    setGrnToComplete(grn);
  };

  const handleScanSerial = () => {
    if (!selectedGRN || !serialInput.trim()) return;
    scanMutation.mutate({ id: selectedGRN.id, serial: serialInput.trim() });
  };

  const columns: ColumnDef<GRN>[] = [
    {
      accessorKey: 'grn_number',
      header: 'GRN Number',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{row.original.grn_number}</span>
        </div>
      ),
    },
    {
      accessorKey: 'po_number',
      header: 'PO Reference',
      cell: ({ row }) => (
        <span className="text-sm font-mono text-muted-foreground">
          {row.original.purchase_order?.po_number || row.original.po_number || row.original.po_id?.slice(0, 8)}
        </span>
      ),
    },
    {
      accessorKey: 'vendor_name',
      header: 'Vendor',
      cell: ({ row }) => (
        <span className="text-sm">
          {row.original.vendor_name || row.original.vendor?.name || 'N/A'}
        </span>
      ),
    },
    {
      accessorKey: 'warehouse_name',
      header: 'Warehouse',
      cell: ({ row }) => (
        <span className="text-sm">{row.original.warehouse_name || row.original.warehouse?.name || 'N/A'}</span>
      ),
    },
    {
      accessorKey: 'grn_date',
      header: 'Received Date',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.grn_date || row.original.received_date)}
        </span>
      ),
    },
    {
      accessorKey: 'quantities',
      header: 'Quantities',
      cell: ({ row }) => (
        <div className="text-sm">
          <div className="flex items-center gap-1 text-green-600">
            <CheckCircle className="h-3 w-3" />
            Received: {row.original.total_received}
          </div>
          {row.original.total_rejected > 0 && (
            <div className="flex items-center gap-1 text-red-600">
              <XCircle className="h-3 w-3" />
              Rejected: {row.original.total_rejected}
            </div>
          )}
        </div>
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
        <GRNActionsCell
          grn={row.original}
          onView={handleView}
          onEdit={handleEdit}
          onComplete={handleComplete}
          onDownload={handleDownload}
          onPrint={handlePrint}
          onDelete={(grn) => { setGrnToDelete(grn); setIsDeleteOpen(true); }}
          isSuperAdmin={isSuperAdmin}
        />
      ),
    },
  ];

  const warehouses: Warehouse[] = warehousesData?.items ?? (Array.isArray(warehousesData) ? warehousesData : []);
  const pos = purchaseOrders?.items ?? [];
  const grnList = data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goods Receipt Notes"
        description="Process and track incoming goods from vendors"
        actions={
          <div className="flex items-center gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                {statusOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create GRN
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Goods Receipt Note</DialogTitle>
                  <DialogDescription>
                    Create a new GRN to receive goods against a purchase order
                  </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label>Purchase Order *</Label>
                    <Select value={formData.po_id} onValueChange={handlePOChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Purchase Order" />
                      </SelectTrigger>
                      <SelectContent>
                        {pos.filter((po: PurchaseOrder) => po.id && po.id.trim() !== '').map((po: PurchaseOrder) => (
                          <SelectItem key={po.id} value={po.id}>
                            <div className="flex items-center gap-2">
                              <span className="font-mono">{po.po_number}</span>
                              <span className="text-muted-foreground">-</span>
                              <span>{po.vendor?.name || 'Unknown Vendor'}</span>
                              <Badge variant="outline" className="ml-2">
                                {formatCurrency(po.grand_total ?? po.total_amount)}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.po_id && (
                    <Card>
                      <CardHeader className="py-3">
                        <CardTitle className="text-sm font-medium">PO Details</CardTitle>
                      </CardHeader>
                      <CardContent className="py-2">
                        {isLoadingPO ? (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Loading PO details...
                          </div>
                        ) : (
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-muted-foreground">Vendor:</span>{' '}
                            <span className="font-medium">{selectedPO?.vendor?.name}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Warehouse:</span>{' '}
                            <span className="font-medium">{selectedPO?.warehouse?.name}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Amount:</span>{' '}
                            <span className="font-medium">{formatCurrency(selectedPO?.grand_total ?? selectedPO?.total_amount ?? 0)}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Items:</span>{' '}
                            <span className="font-medium">{selectedPO?.items?.length || 0} products</span>
                          </div>
                        </div>
                        )}
                        {!isLoadingPO && selectedPO?.items && selectedPO.items.length > 0 && (
                          <div className="mt-3 border-t pt-3">
                            <p className="text-xs font-medium mb-2">Enter quantities to receive:</p>
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                              {selectedPO.items.map((item: POItem) => {
                                const ordered = item.quantity_ordered || item.quantity || 0;
                                const alreadyReceived = item.quantity_received || 0;
                                const pending = Math.max(0, ordered - alreadyReceived);
                                const itemId = item.id || '';
                                const currentQty = itemQuantities[itemId] || 0;
                                const isOverQuantity = currentQty > pending;

                                return (
                                  <div key={itemId} className="flex items-center justify-between gap-3 p-2 bg-muted/50 rounded-lg">
                                    <div className="flex-1 min-w-0">
                                      <div className="font-medium text-sm truncate">{item.product_name}</div>
                                      <div className="text-xs text-muted-foreground">
                                        {item.sku}{(item as any).sub_item_code ? ` | Sub: ${(item as any).sub_item_code}` : ''} | Ordered: {ordered} | Received: {alreadyReceived} | <span className="text-green-600 font-medium">Pending: {pending}</span>
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <Input
                                        type="number"
                                        min={0}
                                        max={pending}
                                        value={currentQty}
                                        onChange={(e) => {
                                          const val = parseInt(e.target.value) || 0;
                                          setItemQuantities(prev => ({
                                            ...prev,
                                            [itemId]: val
                                          }));
                                        }}
                                        className={cn(
                                          "w-24 text-right",
                                          isOverQuantity && "border-red-500 focus-visible:ring-red-500"
                                        )}
                                      />
                                      <span className="text-xs text-muted-foreground w-12">/ {pending}</span>
                                    </div>
                                    {isOverQuantity && (
                                      <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0" />
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                            <div className="mt-2 pt-2 border-t flex justify-between text-sm">
                              <span className="text-muted-foreground">Total items to receive:</span>
                              <span className="font-medium">
                                {Object.values(itemQuantities).reduce((sum, qty) => sum + (qty || 0), 0)} units
                              </span>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Warehouse *</Label>
                      <Select
                        value={formData.warehouse_id}
                        onValueChange={(value) => setFormData({ ...formData, warehouse_id: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select warehouse" />
                        </SelectTrigger>
                        <SelectContent>
                          {warehouses.filter((w: Warehouse) => w.id && w.id.trim() !== '').map((warehouse: Warehouse) => (
                            <SelectItem key={warehouse.id} value={warehouse.id}>
                              {warehouse.name} ({warehouse.code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Received Date *</Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className={cn(
                              'w-full justify-start text-left font-normal',
                              !formData.received_date && 'text-muted-foreground'
                            )}
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {formData.received_date ? format(formData.received_date, 'PPP') : 'Pick a date'}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={formData.received_date}
                            onSelect={(date) => date && setFormData({ ...formData, received_date: date })}
                            disabled={(date) => date > new Date()}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Vendor Challan No.</Label>
                      <Input
                        placeholder="DC/Challan number"
                        value={formData.vendor_challan_number}
                        onChange={(e) => setFormData({ ...formData, vendor_challan_number: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Vehicle Number</Label>
                      <Input
                        placeholder="e.g., DL 01 AB 1234"
                        value={formData.vehicle_number}
                        onChange={(e) => setFormData({ ...formData, vehicle_number: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Remarks</Label>
                    <Textarea
                      placeholder="Any additional remarks for this GRN..."
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      rows={2}
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreate}
                    disabled={
                      createMutation.isPending ||
                      !formData.po_id ||
                      !formData.warehouse_id ||
                      Object.values(itemQuantities).every(q => !q || q === 0) ||
                      (selectedPO?.items || []).some((item: POItem) => {
                        const ordered = item.quantity_ordered || item.quantity || 0;
                        const received = item.quantity_received || 0;
                        const pending = ordered - received;
                        return (itemQuantities[item.id || ''] || 0) > pending;
                      })
                    }
                  >
                    {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create GRN
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={grnList}
        searchKey="grn_number"
        searchPlaceholder="Search GRN..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* GRN Details Sheet */}
      <Sheet open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <SheetContent className="w-[700px] sm:max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              {selectedGRN?.grn_number}
            </SheetTitle>
            <SheetDescription>
              GRN Details and Serial Scanning
            </SheetDescription>
          </SheetHeader>

          {isLoadingGRNDetails && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">Loading details...</span>
            </div>
          )}

          {selectedGRN && (
            <div className="mt-6 space-y-6">
              {/* GRN Header Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <StatusBadge status={selectedGRN.status} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">PO Reference</p>
                  <p className="font-mono text-sm font-medium">{selectedGRN.purchase_order?.po_number || selectedGRN.po_number}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Vendor</p>
                  <p className="text-sm font-medium">{selectedGRN.vendor?.name || selectedGRN.vendor_name || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Warehouse</p>
                  <p className="text-sm font-medium">{selectedGRN.warehouse?.name || selectedGRN.warehouse_name || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">GRN Date</p>
                  <p className="text-sm">{formatDate(selectedGRN.received_date || selectedGRN.grn_date)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">GRN Type</p>
                  <p className="text-sm">{selectedGRN.grn_type || 'INVENTORY'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Received By</p>
                  <p className="text-sm">{(selectedGRN as any).received_by || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Value</p>
                  <p className="text-sm font-medium">{formatCurrency(selectedGRN.total_value || 0)}</p>
                </div>
              </div>

              {/* Quantity Summary */}
              <div className="bg-muted/50 rounded-lg p-4">
                <p className="text-sm font-medium mb-3">Quantity Summary</p>
                <div className="flex flex-wrap gap-3">
                  <Badge variant="outline" className="text-blue-600 px-3 py-1">
                    Expected: {(selectedGRN as any).total_items || 0} items
                  </Badge>
                  <Badge variant="outline" className="text-green-600 px-3 py-1">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Received: {selectedGRN.total_received || selectedGRN.total_quantity_received || 0}
                  </Badge>
                  <Badge variant="outline" className="text-emerald-600 px-3 py-1">
                    Accepted: {selectedGRN.total_quantity_accepted || 0}
                  </Badge>
                  {(selectedGRN.total_rejected || selectedGRN.total_quantity_rejected || 0) > 0 && (
                    <Badge variant="outline" className="text-red-600 px-3 py-1">
                      <XCircle className="mr-1 h-3 w-3" />
                      Rejected: {selectedGRN.total_rejected || selectedGRN.total_quantity_rejected}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Transport & Challan Details */}
              {(selectedGRN.vendor_challan_number || selectedGRN.transporter_name || selectedGRN.vehicle_number || selectedGRN.lr_number || selectedGRN.e_way_bill_number) && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm font-medium mb-3">Transport & Challan Details</p>
                    <div className="grid grid-cols-2 gap-3">
                      {selectedGRN.vendor_challan_number && (
                        <div>
                          <p className="text-xs text-muted-foreground">Vendor Challan No.</p>
                          <p className="text-sm">{selectedGRN.vendor_challan_number}</p>
                        </div>
                      )}
                      {selectedGRN.vendor_challan_date && (
                        <div>
                          <p className="text-xs text-muted-foreground">Challan Date</p>
                          <p className="text-sm">{formatDate(selectedGRN.vendor_challan_date)}</p>
                        </div>
                      )}
                      {selectedGRN.transporter_name && (
                        <div>
                          <p className="text-xs text-muted-foreground">Transporter</p>
                          <p className="text-sm">{selectedGRN.transporter_name}</p>
                        </div>
                      )}
                      {selectedGRN.vehicle_number && (
                        <div>
                          <p className="text-xs text-muted-foreground">Vehicle No.</p>
                          <p className="text-sm">{selectedGRN.vehicle_number}</p>
                        </div>
                      )}
                      {selectedGRN.lr_number && (
                        <div>
                          <p className="text-xs text-muted-foreground">LR Number</p>
                          <p className="text-sm">{selectedGRN.lr_number}</p>
                        </div>
                      )}
                      {selectedGRN.e_way_bill_number && (
                        <div>
                          <p className="text-xs text-muted-foreground">E-Way Bill No.</p>
                          <p className="text-sm">{selectedGRN.e_way_bill_number}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* QC Details */}
              {((selectedGRN as any).qc_status || (selectedGRN as any).qc_remarks) && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm font-medium mb-3">Quality Check</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-muted-foreground">QC Status</p>
                        <StatusBadge status={(selectedGRN as any).qc_status || 'PENDING'} />
                      </div>
                      {(selectedGRN as any).qc_done_by && (
                        <div>
                          <p className="text-xs text-muted-foreground">QC Done By</p>
                          <p className="text-sm">{(selectedGRN as any).qc_done_by}</p>
                        </div>
                      )}
                      {(selectedGRN as any).qc_done_at && (
                        <div>
                          <p className="text-xs text-muted-foreground">QC Date</p>
                          <p className="text-sm">{formatDate((selectedGRN as any).qc_done_at)}</p>
                        </div>
                      )}
                      {(selectedGRN as any).qc_remarks && (
                        <div className="col-span-2">
                          <p className="text-xs text-muted-foreground">QC Remarks</p>
                          <p className="text-sm bg-muted p-2 rounded">{(selectedGRN as any).qc_remarks}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}

              <Separator />

              {/* Serial Scanning Section (for IN_PROGRESS GRN) */}
              {selectedGRN.status === 'IN_PROGRESS' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Barcode className="h-5 w-5" />
                    <h3 className="font-medium">Serial Scanning</h3>
                  </div>

                  <div className="flex gap-2">
                    <Input
                      placeholder="Scan or enter serial number..."
                      value={serialInput}
                      onChange={(e) => setSerialInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleScanSerial()}
                    />
                    <Button
                      onClick={handleScanSerial}
                      disabled={scanMutation.isPending || !serialInput.trim()}
                    >
                      {scanMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        'Scan'
                      )}
                    </Button>
                  </div>

                  {scannedSerials.length > 0 && (
                    <div className="bg-muted p-3 rounded-md">
                      <p className="text-sm text-muted-foreground mb-2">
                        Scanned Serials ({scannedSerials.length}):
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {scannedSerials.map((serial, idx) => (
                          <Badge key={idx} variant="secondary" className="font-mono text-xs">
                            {serial}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* GRN Items - Line-level details */}
              {selectedGRN.items && selectedGRN.items.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <ClipboardList className="h-5 w-5" />
                    <h3 className="font-medium">Received Items ({selectedGRN.items.length})</h3>
                  </div>

                  <div className="space-y-3">
                    {selectedGRN.items.map((item: GRNItem) => (
                      <Card key={item.id}>
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium">{item.product_name}</p>
                              <div className="flex gap-2 mt-1">
                                <span className="text-xs text-muted-foreground font-mono">SKU: {item.sku}</span>
                                {item.hsn_code && (
                                  <span className="text-xs text-muted-foreground font-mono">HSN: {item.hsn_code}</span>
                                )}
                              </div>
                              {item.sub_item_code && (
                                <p className="text-xs text-blue-600 mt-0.5">Sub Item: {item.sub_item_code}</p>
                              )}
                              {item.part_code && (
                                <p className="text-xs text-muted-foreground mt-0.5">Part: {item.part_code}</p>
                              )}
                            </div>
                            {item.qc_result && (
                              <Badge
                                variant={item.qc_result === 'PASSED' || item.qc_result === 'ACCEPTED' ? 'default' : item.qc_result === 'FAILED' || item.qc_result === 'REJECTED' ? 'destructive' : 'secondary'}
                              >
                                QC: {item.qc_result}
                              </Badge>
                            )}
                          </div>

                          {/* Quantity breakdown */}
                          <div className="mt-3 bg-muted/50 rounded p-3">
                            <div className="grid grid-cols-4 gap-2 text-sm">
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">Expected</p>
                                <p className="font-semibold text-blue-600">{item.quantity_expected ?? '-'}</p>
                              </div>
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">Received</p>
                                <p className="font-semibold text-green-600">{item.quantity_received ?? item.received_quantity ?? 0}</p>
                              </div>
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">Accepted</p>
                                <p className="font-semibold text-emerald-600">{item.quantity_accepted ?? 0}</p>
                              </div>
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">Rejected</p>
                                <p className="font-semibold text-red-600">{item.quantity_rejected ?? item.rejected_quantity ?? 0}</p>
                              </div>
                            </div>
                          </div>

                          {/* Price info */}
                          {(item.unit_price != null && item.unit_price > 0) && (
                            <div className="mt-2 flex gap-4 text-sm">
                              <span className="text-muted-foreground">Unit Price: {formatCurrency(item.unit_price)}</span>
                              {item.accepted_value != null && item.accepted_value > 0 && (
                                <span className="text-muted-foreground">Accepted Value: {formatCurrency(item.accepted_value)}</span>
                              )}
                            </div>
                          )}

                          {/* Batch & expiry info */}
                          {(item.batch_number || item.manufacturing_date || item.expiry_date) && (
                            <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                              {item.batch_number && <span>Batch: {item.batch_number}</span>}
                              {item.manufacturing_date && <span>Mfg: {formatDate(item.manufacturing_date)}</span>}
                              {item.expiry_date && <span>Exp: {formatDate(item.expiry_date)}</span>}
                            </div>
                          )}

                          {/* Bin location */}
                          {item.bin_location && (
                            <p className="mt-1 text-xs text-muted-foreground">Bin: {item.bin_location}</p>
                          )}

                          {/* Rejection reason */}
                          {item.rejection_reason && (
                            <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3" />
                              {item.rejection_reason}
                            </p>
                          )}

                          {/* Remarks */}
                          {item.remarks && (
                            <p className="mt-1 text-xs text-muted-foreground italic">Remarks: {item.remarks}</p>
                          )}

                          {/* Serial Numbers */}
                          {((item.serial_numbers && item.serial_numbers.length > 0) || (item.serials && item.serials.length > 0)) && (
                            <div className="mt-2">
                              <p className="text-xs text-muted-foreground">Serial Numbers:</p>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {(item.serial_numbers || item.serials || []).map((serial: string, idx: number) => (
                                  <Badge key={idx} variant="outline" className="font-mono text-xs">
                                    {serial}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* No items message */}
              {!isLoadingGRNDetails && (!selectedGRN.items || selectedGRN.items.length === 0) && (
                <div className="text-center py-6 text-muted-foreground">
                  <ClipboardList className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No item details available</p>
                </div>
              )}

              {/* Receiving Remarks / Notes */}
              {(selectedGRN.receiving_remarks || selectedGRN.notes) && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Remarks / Notes</p>
                  <p className="text-sm bg-muted p-3 rounded-md">{selectedGRN.receiving_remarks || selectedGRN.notes}</p>
                </div>
              )}

              {/* Actions */}
              {selectedGRN.status === 'IN_PROGRESS' && (
                <div className="flex justify-end pt-4">
                  <Button onClick={() => handleComplete(selectedGRN)}>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Complete GRN
                  </Button>
                </div>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Complete GRN Confirmation */}
      <AlertDialog open={!!grnToComplete} onOpenChange={() => setGrnToComplete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Complete GRN?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to complete GRN <strong>{grnToComplete?.grn_number}</strong>?
              This will finalize the goods receipt and update inventory. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => grnToComplete && completeMutation.mutate(grnToComplete.id)}
              disabled={completeMutation.isPending}
            >
              {completeMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Complete GRN
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit GRN Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit GRN — {editGrn?.grn_number}</DialogTitle>
            <DialogDescription>Update transport and delivery details</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Vendor Challan No.</Label>
                <Input
                  value={editFormData.vendor_challan_number}
                  onChange={(e) => setEditFormData({ ...editFormData, vendor_challan_number: e.target.value })}
                  placeholder="DC/Challan number"
                />
              </div>
              <div className="space-y-2">
                <Label>Vendor Challan Date</Label>
                <Input
                  type="date"
                  value={editFormData.vendor_challan_date}
                  onChange={(e) => setEditFormData({ ...editFormData, vendor_challan_date: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Transporter Name</Label>
                <Input
                  value={editFormData.transporter_name}
                  onChange={(e) => setEditFormData({ ...editFormData, transporter_name: e.target.value })}
                  placeholder="e.g., Blue Dart"
                />
              </div>
              <div className="space-y-2">
                <Label>Vehicle Number</Label>
                <Input
                  value={editFormData.vehicle_number}
                  onChange={(e) => setEditFormData({ ...editFormData, vehicle_number: e.target.value })}
                  placeholder="e.g., DL 01 AB 1234"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>LR Number</Label>
                <Input
                  value={editFormData.lr_number}
                  onChange={(e) => setEditFormData({ ...editFormData, lr_number: e.target.value })}
                  placeholder="Lorry Receipt No."
                />
              </div>
              <div className="space-y-2">
                <Label>E-Way Bill Number</Label>
                <Input
                  value={editFormData.e_way_bill_number}
                  onChange={(e) => setEditFormData({ ...editFormData, e_way_bill_number: e.target.value })}
                  placeholder="E-Way Bill No."
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Remarks</Label>
              <Textarea
                value={editFormData.receiving_remarks}
                onChange={(e) => setEditFormData({ ...editFormData, receiving_remarks: e.target.value })}
                placeholder="Any additional remarks..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>Cancel</Button>
            <Button onClick={handleEditSubmit}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete GRN Confirmation */}
      <AlertDialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete GRN</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete GRN <strong>{grnToDelete?.grn_number}</strong>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => grnToDelete && deleteMutation.mutate(grnToDelete.id)}
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
