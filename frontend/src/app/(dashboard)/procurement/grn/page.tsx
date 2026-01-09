'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import {
  MoreHorizontal, Plus, Eye, Package, CheckCircle, XCircle,
  Loader2, Barcode, ClipboardList, CalendarIcon, AlertTriangle,
  Download, Printer, Trash2
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
  po_id: string;
  po_number?: string;
  warehouse_id: string;
  status: 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  received_date: string;
  total_received: number;
  total_rejected: number;
  notes?: string;
  created_at: string;
  warehouse?: { name: string; code: string };
  vendor?: { name: string; code: string };
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
  product_id: string;
  product_name: string;
  sku: string;
  received_quantity: number;
  rejected_quantity: number;
  rejection_reason?: string;
  qc_status: 'PENDING' | 'PASSED' | 'FAILED';
  serials?: string[];
}

interface PurchaseOrder {
  id: string;
  po_number: string;
  status: string;
  vendor?: { name: string; code: string };
  delivery_warehouse_id?: string;
  warehouse_id?: string;
  warehouse?: { name: string };
  total_amount: number;
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
  onComplete,
  onDownload,
  onPrint,
  onDelete,
  isSuperAdmin
}: {
  grn: GRN;
  onView: (grn: GRN) => void;
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

  // Form state
  const [formData, setFormData] = useState({
    po_id: '',
    warehouse_id: '',
    received_date: new Date(),
    notes: '',
  });

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

  const { data: purchaseOrders } = useQuery({
    queryKey: ['purchase-orders-for-grn'],
    queryFn: () => purchaseOrdersApi.list({ status: 'SENT_TO_VENDOR' }),
  });

  const { data: warehousesData } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => warehousesApi.list({ is_active: true }),
  });

  // Get selected PO details
  const selectedPO = (purchaseOrders?.items ?? []).find((po: PurchaseOrder) => po.id === formData.po_id);

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
    });
    setScannedSerials([]);
    setSerialInput('');
    setIsCreateDialogOpen(false);
  };

  const handleCreate = () => {
    if (!formData.po_id || !formData.warehouse_id) {
      toast.error('Please select a Purchase Order and Warehouse');
      return;
    }

    createMutation.mutate({
      po_id: formData.po_id,
      warehouse_id: formData.warehouse_id,
      received_date: format(formData.received_date, 'yyyy-MM-dd'),
      notes: formData.notes || undefined,
    });
  };

  const handlePOChange = (poId: string) => {
    const po = (purchaseOrders?.items ?? []).find((p: PurchaseOrder) => p.id === poId);
    setFormData({
      ...formData,
      po_id: poId,
      warehouse_id: po?.delivery_warehouse_id || '',
    });
  };

  const handleView = (grn: GRN) => {
    setSelectedGRN(grn);
    setIsDetailsOpen(true);
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
      accessorKey: 'vendor',
      header: 'Vendor',
      cell: ({ row }) => (
        <span className="text-sm">
          {row.original.vendor?.name || row.original.purchase_order?.vendor?.name || 'N/A'}
        </span>
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
      accessorKey: 'received_date',
      header: 'Received Date',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.received_date)}
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
              <DialogContent className="max-w-2xl">
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
                                {formatCurrency(po.total_amount)}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedPO && (
                    <Card>
                      <CardHeader className="py-3">
                        <CardTitle className="text-sm font-medium">PO Details</CardTitle>
                      </CardHeader>
                      <CardContent className="py-2">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-muted-foreground">Vendor:</span>{' '}
                            <span className="font-medium">{selectedPO.vendor?.name}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Warehouse:</span>{' '}
                            <span className="font-medium">{selectedPO.warehouse?.name}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Amount:</span>{' '}
                            <span className="font-medium">{formatCurrency(selectedPO.total_amount)}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Items:</span>{' '}
                            <span className="font-medium">{selectedPO.items?.length || 0} products</span>
                          </div>
                        </div>
                        {selectedPO.items && selectedPO.items.length > 0 && (
                          <div className="mt-3 border-t pt-3">
                            <p className="text-xs text-muted-foreground mb-2">Items to receive:</p>
                            <div className="space-y-1">
                              {selectedPO.items.map((item: POItem) => (
                                <div key={item.id} className="flex justify-between text-sm">
                                  <span>{item.product_name}</span>
                                  <span className="text-muted-foreground">Qty: {item.quantity_ordered}</span>
                                </div>
                              ))}
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

                  <div className="space-y-2">
                    <Label>Notes</Label>
                    <Textarea
                      placeholder="Any additional notes for this GRN..."
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      rows={3}
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreate}
                    disabled={createMutation.isPending || !formData.po_id || !formData.warehouse_id}
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
        <SheetContent className="w-[600px] sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              {selectedGRN?.grn_number}
            </SheetTitle>
            <SheetDescription>
              GRN Details and Serial Scanning
            </SheetDescription>
          </SheetHeader>

          {selectedGRN && (
            <div className="mt-6 space-y-6">
              {/* GRN Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <StatusBadge status={selectedGRN.status} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">PO Reference</p>
                  <p className="font-mono text-sm">{selectedGRN.purchase_order?.po_number || selectedGRN.po_number}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Vendor</p>
                  <p className="text-sm font-medium">{selectedGRN.vendor?.name || selectedGRN.purchase_order?.vendor?.name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Warehouse</p>
                  <p className="text-sm font-medium">{selectedGRN.warehouse?.name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Received Date</p>
                  <p className="text-sm">{formatDate(selectedGRN.received_date)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Quantities</p>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="text-green-600">
                      <CheckCircle className="mr-1 h-3 w-3" />
                      {selectedGRN.total_received} Received
                    </Badge>
                    {selectedGRN.total_rejected > 0 && (
                      <Badge variant="outline" className="text-red-600">
                        <XCircle className="mr-1 h-3 w-3" />
                        {selectedGRN.total_rejected} Rejected
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

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

              {/* GRN Items */}
              {selectedGRN.items && selectedGRN.items.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <ClipboardList className="h-5 w-5" />
                    <h3 className="font-medium">Received Items</h3>
                  </div>

                  <div className="space-y-3">
                    {selectedGRN.items.map((item: GRNItem) => (
                      <Card key={item.id}>
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium">{item.product_name}</p>
                              <p className="text-sm text-muted-foreground font-mono">{item.sku}</p>
                            </div>
                            <Badge
                              variant={item.qc_status === 'PASSED' ? 'default' : item.qc_status === 'FAILED' ? 'destructive' : 'secondary'}
                            >
                              QC: {item.qc_status}
                            </Badge>
                          </div>
                          <div className="mt-2 flex gap-4 text-sm">
                            <span className="text-green-600">
                              Received: {item.received_quantity}
                            </span>
                            {item.rejected_quantity > 0 && (
                              <span className="text-red-600">
                                Rejected: {item.rejected_quantity}
                              </span>
                            )}
                          </div>
                          {item.rejection_reason && (
                            <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3" />
                              {item.rejection_reason}
                            </p>
                          )}
                          {item.serials && item.serials.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs text-muted-foreground">Serials:</p>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {item.serials.map((serial, idx) => (
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

              {/* Notes */}
              {selectedGRN.notes && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Notes</p>
                  <p className="text-sm bg-muted p-3 rounded-md">{selectedGRN.notes}</p>
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
