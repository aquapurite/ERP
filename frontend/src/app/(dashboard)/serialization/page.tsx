'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Download, QrCode, Barcode, CheckCircle, XCircle, Settings, Package, Truck, Loader2, RefreshCw } from 'lucide-react';
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
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { serializationApi, ModelCodeReference, SupplierCode } from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface SerialItem {
  id: string;
  serial_number: string;
  barcode: string;
  product_id: string;
  product?: { name: string; sku: string };
  po_id?: string;
  po_number?: string;
  warehouse_id?: string;
  warehouse?: { name: string };
  status: 'GENERATED' | 'IN_STOCK' | 'ALLOCATED' | 'SHIPPED' | 'DELIVERED' | 'INSTALLED' | 'RETURNED' | 'SCRAPPED';
  manufactured_date?: string;
  warranty_start_date?: string;
  warranty_end_date?: string;
  created_at: string;
}

interface Product {
  id: string;
  name: string;
  sku: string;
}

interface Vendor {
  id: string;
  name: string;
  code: string;
}

const localSerializationApi = {
  list: async (params?: { page?: number; size?: number; status?: string; product_id?: string }) => {
    try {
      const { data } = await apiClient.get('/inventory/stock-items', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  validate: async (barcode: string) => {
    try {
      const { data } = await apiClient.get(`/serialization/validate/${barcode}`);
      return data;
    } catch {
      return { valid: false, message: 'Barcode not found or invalid' };
    }
  },
};

const serialColumns: ColumnDef<SerialItem>[] = [
  {
    accessorKey: 'serial_number',
    header: 'Serial Number',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Barcode className="h-4 w-4 text-muted-foreground" />
        <div>
          <div className="font-mono font-medium">{row.original.serial_number}</div>
          <div className="text-xs text-muted-foreground font-mono">
            {row.original.barcode}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'product',
    header: 'Product',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.product?.name || 'N/A'}</div>
        <div className="text-muted-foreground font-mono text-xs">
          {row.original.product?.sku}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'po_number',
    header: 'PO Reference',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.po_number || '-'}</span>
    ),
  },
  {
    accessorKey: 'warehouse',
    header: 'Location',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.warehouse?.name || '-'}</span>
    ),
  },
  {
    accessorKey: 'warranty',
    header: 'Warranty',
    cell: ({ row }) => (
      row.original.warranty_end_date ? (
        <div className="text-sm">
          <div>Till {formatDate(row.original.warranty_end_date)}</div>
        </div>
      ) : (
        <span className="text-sm text-muted-foreground">-</span>
      )
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
          <DropdownMenuItem>
            <Eye className="mr-2 h-4 w-4" />
            View History
          </DropdownMenuItem>
          <DropdownMenuItem>
            <QrCode className="mr-2 h-4 w-4" />
            Print Barcode
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

const modelCodeColumns: ColumnDef<ModelCodeReference>[] = [
  {
    accessorKey: 'model_code',
    header: 'Model Code',
    cell: ({ row }) => (
      <Badge variant="secondary" className="font-mono text-base">
        {row.original.model_code}
      </Badge>
    ),
  },
  {
    accessorKey: 'fg_code',
    header: 'FG Code',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.fg_code}</span>
    ),
  },
  {
    accessorKey: 'product_sku',
    header: 'Product SKU',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.product_sku || '-'}</span>
    ),
  },
  {
    accessorKey: 'item_type',
    header: 'Item Type',
    cell: ({ row }) => (
      <Badge variant="outline">{row.original.item_type || 'FG'}</Badge>
    ),
  },
  {
    accessorKey: 'description',
    header: 'Description',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">{row.original.description || '-'}</span>
    ),
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? 'default' : 'secondary'}>
        {row.original.is_active ? 'Active' : 'Inactive'}
      </Badge>
    ),
  },
];

const supplierCodeColumns: ColumnDef<SupplierCode>[] = [
  {
    accessorKey: 'code',
    header: 'Supplier Code',
    cell: ({ row }) => (
      <Badge variant="secondary" className="font-mono text-base">
        {row.original.code}
      </Badge>
    ),
  },
  {
    accessorKey: 'name',
    header: 'Supplier Name',
    cell: ({ row }) => (
      <span className="font-medium">{row.original.name}</span>
    ),
  },
  {
    accessorKey: 'vendor_id',
    header: 'Linked Vendor',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {row.original.vendor_id ? 'Linked' : 'Not linked'}
      </span>
    ),
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? 'default' : 'secondary'}>
        {row.original.is_active ? 'Active' : 'Inactive'}
      </Badge>
    ),
  },
];

export default function SerializationPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('serials');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [validateBarcode, setValidateBarcode] = useState('');
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message: string;
    item?: SerialItem;
  } | null>(null);

  // Model Code Dialog State
  const [isModelCodeDialogOpen, setIsModelCodeDialogOpen] = useState(false);
  const [newModelCode, setNewModelCode] = useState({
    fg_code: '',
    model_code: '',
    item_type: 'FG',
    product_id: '',
    product_sku: '',
    description: '',
  });

  // Supplier Code Dialog State
  const [isSupplierCodeDialogOpen, setIsSupplierCodeDialogOpen] = useState(false);
  const [newSupplierCode, setNewSupplierCode] = useState({
    code: '',
    name: '',
    vendor_id: '',
    description: '',
  });

  // Queries
  const { data: serialData, isLoading: serialsLoading } = useQuery({
    queryKey: ['serial-items', page, pageSize],
    queryFn: () => localSerializationApi.list({ page: page + 1, size: pageSize }),
  });

  const { data: modelCodes = [], isLoading: modelCodesLoading } = useQuery({
    queryKey: ['model-codes'],
    queryFn: () => serializationApi.getModelCodes(false),
  });

  const { data: supplierCodes = [], isLoading: supplierCodesLoading } = useQuery({
    queryKey: ['supplier-codes'],
    queryFn: () => serializationApi.getSupplierCodes(false),
  });

  const { data: products = [] } = useQuery({
    queryKey: ['products-for-model-codes'],
    queryFn: async () => {
      try {
        const { data } = await apiClient.get('/products', { params: { limit: 500 } });
        return data.items || [];
      } catch {
        return [];
      }
    },
  });

  const { data: vendors = [] } = useQuery({
    queryKey: ['vendors-for-supplier-codes'],
    queryFn: async () => {
      try {
        const { data } = await apiClient.get('/vendors', { params: { limit: 500 } });
        return data.items || data || [];
      } catch {
        return [];
      }
    },
  });

  // Mutations
  const createModelCodeMutation = useMutation({
    mutationFn: serializationApi.createModelCode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-codes'] });
      toast.success('Model code created successfully');
      setIsModelCodeDialogOpen(false);
      setNewModelCode({ fg_code: '', model_code: '', item_type: 'FG', product_id: '', product_sku: '', description: '' });
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create model code'),
  });

  const createSupplierCodeMutation = useMutation({
    mutationFn: serializationApi.createSupplierCode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supplier-codes'] });
      toast.success('Supplier code created successfully');
      setIsSupplierCodeDialogOpen(false);
      setNewSupplierCode({ code: '', name: '', vendor_id: '', description: '' });
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create supplier code'),
  });

  const seedCodesMutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/serialization/seed-codes');
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['model-codes'] });
      queryClient.invalidateQueries({ queryKey: ['supplier-codes'] });
      toast.success(`Codes seeded: ${data.supplier_codes_created} suppliers, ${data.model_codes_created} model codes`);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to seed codes'),
  });

  const handleValidate = async () => {
    if (!validateBarcode.trim()) return;
    try {
      const result = await localSerializationApi.validate(validateBarcode);
      setValidationResult(result);
    } catch {
      setValidationResult({
        valid: false,
        message: 'Barcode not found or invalid',
      });
    }
  };

  const handleCreateModelCode = () => {
    if (!newModelCode.model_code || newModelCode.model_code.length !== 3) {
      toast.error('Model code must be exactly 3 characters');
      return;
    }
    if (!newModelCode.product_sku) {
      toast.error('Please select a product');
      return;
    }
    createModelCodeMutation.mutate(newModelCode);
  };

  const handleCreateSupplierCode = () => {
    if (!newSupplierCode.code || newSupplierCode.code.length !== 2) {
      toast.error('Supplier code must be exactly 2 characters');
      return;
    }
    if (!newSupplierCode.name) {
      toast.error('Please enter supplier name');
      return;
    }
    createSupplierCodeMutation.mutate(newSupplierCode);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Serialization"
        description="Manage product serial numbers, barcodes, and code mappings"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                if (confirm('This will delete all existing codes and create new ones. Continue?')) {
                  seedCodesMutation.mutate();
                }
              }}
              disabled={seedCodesMutation.isPending}
            >
              {seedCodesMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Seed Codes
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Generate Serials
            </Button>
          </div>
        }
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="serials" className="flex items-center gap-2">
            <Barcode className="h-4 w-4" />
            Serial Numbers
          </TabsTrigger>
          <TabsTrigger value="model-codes" className="flex items-center gap-2">
            <Package className="h-4 w-4" />
            Model Codes
          </TabsTrigger>
          <TabsTrigger value="supplier-codes" className="flex items-center gap-2">
            <Truck className="h-4 w-4" />
            Supplier Codes
          </TabsTrigger>
        </TabsList>

        {/* Serial Numbers Tab */}
        <TabsContent value="serials" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <QrCode className="h-5 w-5" />
                Barcode Validation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <Input
                    placeholder="Scan or enter barcode"
                    value={validateBarcode}
                    onChange={(e) => setValidateBarcode(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleValidate()}
                  />
                </div>
                <Button onClick={handleValidate}>Validate</Button>
              </div>
              {validationResult && (
                <div className={`mt-4 p-4 rounded-lg ${
                  validationResult.valid ? 'bg-green-50' : 'bg-red-50'
                }`}>
                  <div className="flex items-center gap-2">
                    {validationResult.valid ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-600" />
                    )}
                    <span className={validationResult.valid ? 'text-green-800' : 'text-red-800'}>
                      {validationResult.message}
                    </span>
                  </div>
                  {validationResult.item && (
                    <div className="mt-2 text-sm text-muted-foreground">
                      <div>Product: {validationResult.item.product?.name}</div>
                      <div>Status: {validationResult.item.status}</div>
                      {validationResult.item.warehouse && (
                        <div>Location: {validationResult.item.warehouse.name}</div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <DataTable
            columns={serialColumns}
            data={serialData?.items ?? []}
            searchKey="serial_number"
            searchPlaceholder="Search serial numbers..."
            isLoading={serialsLoading}
            manualPagination
            pageCount={serialData?.pages ?? 0}
            pageIndex={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        </TabsContent>

        {/* Model Codes Tab */}
        <TabsContent value="model-codes" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Model Codes
                </CardTitle>
                <CardDescription>
                  Map products to 3-character model codes for barcode generation
                </CardDescription>
              </div>
              <Button onClick={() => setIsModelCodeDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Model Code
              </Button>
            </CardHeader>
            <CardContent>
              <div className="p-4 mb-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>Barcode Format:</strong> AP + Supplier(2) + Year(1) + Month(1) + <strong>Model(3)</strong> + Serial(6)
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Example: APFS<strong>A</strong><strong>A</strong><strong>SDF</strong>000001 (FS=Supplier, A=2026, A=Jan, SDF=Model, 000001=Serial)
                </p>
              </div>
            </CardContent>
          </Card>

          <DataTable
            columns={modelCodeColumns}
            data={modelCodes}
            searchKey="product_sku"
            searchPlaceholder="Search by SKU..."
            isLoading={modelCodesLoading}
          />
        </TabsContent>

        {/* Supplier Codes Tab */}
        <TabsContent value="supplier-codes" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Supplier Codes
                </CardTitle>
                <CardDescription>
                  Map vendors to 2-character supplier codes for barcode generation
                </CardDescription>
              </div>
              <Button onClick={() => setIsSupplierCodeDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Supplier Code
              </Button>
            </CardHeader>
            <CardContent>
              <div className="p-4 mb-4 bg-green-50 rounded-lg border border-green-200">
                <p className="text-sm text-green-800">
                  <strong>Barcode Format:</strong> AP + <strong>Supplier(2)</strong> + Year(1) + Month(1) + Model(3) + Serial(6)
                </p>
                <p className="text-xs text-green-600 mt-1">
                  Example: AP<strong>FS</strong>AASDF000001 (FS=Supplier Code for the vendor/manufacturer)
                </p>
              </div>
            </CardContent>
          </Card>

          <DataTable
            columns={supplierCodeColumns}
            data={supplierCodes}
            searchKey="name"
            searchPlaceholder="Search by name..."
            isLoading={supplierCodesLoading}
          />
        </TabsContent>
      </Tabs>

      {/* Add Model Code Dialog */}
      <Dialog open={isModelCodeDialogOpen} onOpenChange={setIsModelCodeDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Model Code</DialogTitle>
            <DialogDescription>
              Create a 3-character model code for a product. This will be used in barcode generation.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Product *</Label>
              <Select
                value={newModelCode.product_id || 'select'}
                onValueChange={(value) => {
                  if (value === 'select') return;
                  const product = products.find((p: Product) => p.id === value);
                  setNewModelCode({
                    ...newModelCode,
                    product_id: value,
                    product_sku: product?.sku || '',
                    fg_code: product?.sku || '',
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select product" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="select" disabled>Select product</SelectItem>
                  {products.map((p: Product) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Model Code (3 chars) *</Label>
                <Input
                  placeholder="e.g., SDF"
                  maxLength={3}
                  className="font-mono uppercase"
                  value={newModelCode.model_code}
                  onChange={(e) => setNewModelCode({ ...newModelCode, model_code: e.target.value.toUpperCase() })}
                />
                <p className="text-xs text-muted-foreground">Must be exactly 3 characters</p>
              </div>
              <div className="space-y-2">
                <Label>Item Type</Label>
                <Select
                  value={newModelCode.item_type}
                  onValueChange={(value) => setNewModelCode({ ...newModelCode, item_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FG">Finished Goods (FG)</SelectItem>
                    <SelectItem value="RM">Raw Material (RM)</SelectItem>
                    <SelectItem value="SFG">Semi-Finished (SFG)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Input
                placeholder="Optional description"
                value={newModelCode.description}
                onChange={(e) => setNewModelCode({ ...newModelCode, description: e.target.value })}
              />
            </div>
            {newModelCode.model_code.length === 3 && (
              <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <p className="text-sm text-purple-800">
                  <strong>Preview:</strong> AP??AA<strong>{newModelCode.model_code}</strong>000001
                </p>
                <p className="text-xs text-purple-600 mt-1">
                  ?? = Supplier code (set per vendor)
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModelCodeDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateModelCode} disabled={createModelCodeMutation.isPending}>
              {createModelCodeMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Supplier Code Dialog */}
      <Dialog open={isSupplierCodeDialogOpen} onOpenChange={setIsSupplierCodeDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Supplier Code</DialogTitle>
            <DialogDescription>
              Create a 2-character supplier code for a vendor/manufacturer. This will be used in barcode generation.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Vendor (Optional)</Label>
              <Select
                value={newSupplierCode.vendor_id || 'none'}
                onValueChange={(value) => {
                  if (value === 'none') {
                    setNewSupplierCode({ ...newSupplierCode, vendor_id: '' });
                    return;
                  }
                  const vendor = vendors.find((v: Vendor) => v.id === value);
                  setNewSupplierCode({
                    ...newSupplierCode,
                    vendor_id: value,
                    name: vendor?.name || newSupplierCode.name,
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select vendor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No linked vendor</SelectItem>
                  {vendors.map((v: Vendor) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.name} ({v.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Supplier Code (2 chars) *</Label>
                <Input
                  placeholder="e.g., FS"
                  maxLength={2}
                  className="font-mono uppercase"
                  value={newSupplierCode.code}
                  onChange={(e) => setNewSupplierCode({ ...newSupplierCode, code: e.target.value.toUpperCase() })}
                />
                <p className="text-xs text-muted-foreground">Must be exactly 2 characters</p>
              </div>
              <div className="space-y-2">
                <Label>Supplier Name *</Label>
                <Input
                  placeholder="e.g., Fujian Supplier"
                  value={newSupplierCode.name}
                  onChange={(e) => setNewSupplierCode({ ...newSupplierCode, name: e.target.value })}
                />
              </div>
            </div>
            {newSupplierCode.code.length === 2 && (
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="text-sm text-green-800">
                  <strong>Preview:</strong> AP<strong>{newSupplierCode.code}</strong>AA???000001
                </p>
                <p className="text-xs text-green-600 mt-1">
                  ??? = Model code (set per product)
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSupplierCodeDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateSupplierCode} disabled={createSupplierCodeMutation.isPending}>
              {createSupplierCodeMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
