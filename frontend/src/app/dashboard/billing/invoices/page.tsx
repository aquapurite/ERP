'use client';

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Download, FileText, Send, Loader2, Shield, XCircle, Printer, Trash2, Package, AlertTriangle, Search } from 'lucide-react';
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { invoicesApi, customersApi, dealersApi, warehousesApi, productsApi, inventoryApi } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';
import type { Product } from '@/types';

interface Invoice {
  id: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  customer_id: string;
  customer?: { name: string; gstin?: string; address?: string };
  items: InvoiceItem[];
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  irn?: string;
  irn_generated_at?: string;
  status: 'DRAFT' | 'SENT' | 'PAID' | 'PARTIALLY_PAID' | 'OVERDUE' | 'CANCELLED';
  notes?: string;
  created_at: string;
}

interface InvoiceItem {
  id: string;
  product_id: string;
  product_name: string;
  description?: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
}

interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  gstin?: string;
}

interface DealerItem {
  id: string;
  name: string;
  legal_name?: string;
  gstin?: string;
  dealer_code?: string;
}

interface FormItem {
  product_id: string;
  product_name: string;
  hsn_code: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  available_stock: number | null;
}

export default function InvoicesPage() {
  const { permissions } = useAuth();
  const isSuperAdmin = permissions?.is_super_admin ?? false;
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [invoiceToDelete, setInvoiceToDelete] = useState<Invoice | null>(null);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  // Product search state
  const [productSearchTerms, setProductSearchTerms] = useState<Record<number, string>>({});
  const [activeSearchIndex, setActiveSearchIndex] = useState<number | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const [formData, setFormData] = useState({
    entity_type: '' as '' | 'customer' | 'dealer',
    entity_id: '',
    warehouse_id: '',
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: '',
    notes: '',
    items: [{ product_id: '', product_name: '', hsn_code: '84212110', quantity: 1, unit_price: 0, tax_rate: 18, available_stock: null as number | null }] as FormItem[],
  });

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', page, pageSize],
    queryFn: () => invoicesApi.list({ page: page + 1, size: pageSize }),
  });

  const { data: customersData } = useQuery({
    queryKey: ['customers-list'],
    queryFn: () => customersApi.list({ size: 100 }),
  });

  const { data: dealersData } = useQuery({
    queryKey: ['dealers-dropdown-invoices'],
    queryFn: () => dealersApi.list({ size: 100, status: 'ACTIVE' }),
    enabled: isSuperAdmin,
  });

  const { data: warehousesDropdown } = useQuery({
    queryKey: ['warehouses-dropdown'],
    queryFn: () => warehousesApi.dropdown(),
  });

  const { data: productSearchResults } = useQuery({
    queryKey: ['products-search', debouncedSearchTerm],
    queryFn: () => productsApi.list({ search: debouncedSearchTerm, size: 10, is_active: true }),
    enabled: debouncedSearchTerm.length >= 2,
  });

  // Debounce product search
  const handleProductSearchChange = useCallback((index: number, value: string) => {
    setProductSearchTerms(prev => ({ ...prev, [index]: value }));
    setActiveSearchIndex(index);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearchTerm(value);
    }, 300);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setActiveSearchIndex(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch stock for a product in the selected warehouse
  const fetchStockForProduct = useCallback(async (productId: string, index: number, warehouseId?: string) => {
    const wId = warehouseId || formData.warehouse_id;
    if (!wId || !productId) return;
    try {
      const result = await inventoryApi.getInventorySummaryList({ warehouse_id: wId, product_id: productId, size: 1 });
      const items = result?.items ?? [];
      const available = items.length > 0 ? ((items[0].available_quantity ?? 0) - (items[0].reserved_quantity ?? 0)) : 0;
      setFormData(prev => {
        const newItems = [...prev.items];
        if (newItems[index]) {
          newItems[index] = { ...newItems[index], available_stock: available };
        }
        return { ...prev, items: newItems };
      });
    } catch {
      // Silently fail stock check
    }
  }, [formData.warehouse_id]);

  // Handle product select from search dropdown
  const handleProductSelect = useCallback((index: number, product: Product) => {
    const isDealer = formData.entity_type === 'dealer';
    const price = isDealer && product.dealer_price ? product.dealer_price : (product.selling_price || product.mrp || 0);

    setFormData(prev => {
      const newItems = [...prev.items];
      newItems[index] = {
        ...newItems[index],
        product_id: product.id,
        product_name: product.name,
        hsn_code: product.hsn_code || '84212110',
        unit_price: price,
        tax_rate: product.gst_rate || 18,
        available_stock: null,
      };
      return { ...prev, items: newItems };
    });

    setProductSearchTerms(prev => ({ ...prev, [index]: '' }));
    setActiveSearchIndex(null);
    setDebouncedSearchTerm('');

    // Fetch stock
    if (formData.warehouse_id) {
      fetchStockForProduct(product.id, index);
    }
  }, [formData.entity_type, formData.warehouse_id, fetchStockForProduct]);

  // Handle warehouse change — re-fetch stock for all items
  const handleWarehouseChange = useCallback((warehouseId: string) => {
    setFormData(prev => ({ ...prev, warehouse_id: warehouseId }));
    // Re-fetch stock for all items that have a product_id
    formData.items.forEach((item, index) => {
      if (item.product_id) {
        fetchStockForProduct(item.product_id, index, warehouseId);
      }
    });
  }, [formData.items, fetchStockForProduct]);

  const createMutation = useMutation({
    mutationFn: invoicesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast.success('Invoice created successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create invoice'),
  });

  const generateIRNMutation = useMutation({
    mutationFn: invoicesApi.generateIRN,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast.success('IRN generated successfully');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to generate IRN'),
  });

  const cancelIRNMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => invoicesApi.cancelIRN(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast.success('IRN cancelled');
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to cancel IRN'),
  });

  const deleteMutation = useMutation({
    mutationFn: invoicesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast.success('Invoice deleted successfully');
      setIsDeleteOpen(false);
      setInvoiceToDelete(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete invoice'),
  });

  const resetForm = () => {
    setFormData({
      entity_type: '' as '' | 'customer' | 'dealer',
      entity_id: '',
      warehouse_id: '',
      invoice_date: new Date().toISOString().split('T')[0],
      due_date: '',
      notes: '',
      items: [{ product_id: '', product_name: '', hsn_code: '84212110', quantity: 1, unit_price: 0, tax_rate: 18, available_stock: null }],
    });
    setProductSearchTerms({});
    setActiveSearchIndex(null);
    setDebouncedSearchTerm('');
    setIsDialogOpen(false);
  };

  const handleViewInvoice = async (invoice: Invoice) => {
    try {
      const detail = await invoicesApi.getById(invoice.id);
      setSelectedInvoice(detail);
      setIsViewOpen(true);
    } catch {
      toast.error('Failed to load invoice details');
    }
  };

  const handleDownload = async (invoice: Invoice) => {
    try {
      const htmlContent = await invoicesApi.download(invoice.id);
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.onload = () => window.URL.revokeObjectURL(url);
      }
      toast.success('Opening invoice for download/print');
    } catch {
      toast.error('Failed to download invoice');
    }
  };

  const handlePrint = async (invoice: Invoice) => {
    try {
      const htmlContent = await invoicesApi.download(invoice.id);
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
      toast.error('Failed to print invoice');
    }
  };

  const handleSubmit = () => {
    if (!formData.entity_id || !formData.invoice_date || !formData.due_date) {
      toast.error('Customer/Dealer, invoice date, and due date are required');
      return;
    }
    if (!formData.warehouse_id) {
      toast.error('Warehouse is required');
      return;
    }
    if (formData.items.some(item => !item.unit_price || item.unit_price <= 0)) {
      toast.error('All items must have a price greater than 0');
      return;
    }

    createMutation.mutate({
      customer_id: formData.entity_type === 'customer' ? formData.entity_id : undefined,
      dealer_id: formData.entity_type === 'dealer' ? formData.entity_id : undefined,
      warehouse_id: formData.warehouse_id,
      invoice_date: formData.invoice_date,
      due_date: formData.due_date,
      items: formData.items.map(item => ({
        product_id: item.product_id || undefined,
        product_name: item.product_name || 'Manual Item',
        hsn_code: item.hsn_code || '84212110',
        quantity: item.quantity,
        unit_price: item.unit_price,
        tax_rate: item.tax_rate,
      })),
      notes: formData.notes || undefined,
    });
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product_id: '', product_name: '', hsn_code: '84212110', quantity: 1, unit_price: 0, tax_rate: 18, available_stock: null }],
    });
  };

  const updateItem = (index: number, field: string, value: string | number) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    setFormData({ ...formData, items: newItems });
  };

  const removeItem = (index: number) => {
    if (formData.items.length > 1) {
      setFormData({
        ...formData,
        items: formData.items.filter((_, i) => i !== index),
      });
      // Clean up search term for removed index
      setProductSearchTerms(prev => {
        const next = { ...prev };
        delete next[index];
        return next;
      });
    }
  };

  // GST preview calculations
  const gstPreview = useMemo(() => {
    let subtotal = 0;
    let totalTax = 0;
    const taxBreakdown: Record<number, { taxable: number; tax: number }> = {};

    for (const item of formData.items) {
      const lineSubtotal = item.quantity * item.unit_price;
      const lineTax = lineSubtotal * (item.tax_rate / 100);
      subtotal += lineSubtotal;
      totalTax += lineTax;

      if (!taxBreakdown[item.tax_rate]) {
        taxBreakdown[item.tax_rate] = { taxable: 0, tax: 0 };
      }
      taxBreakdown[item.tax_rate].taxable += lineSubtotal;
      taxBreakdown[item.tax_rate].tax += lineTax;
    }

    return {
      subtotal,
      totalTax,
      grandTotal: subtotal + totalTax,
      taxBreakdown,
    };
  }, [formData.items]);

  const columns: ColumnDef<Invoice>[] = [
    {
      accessorKey: 'invoice_number',
      header: 'Invoice #',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{row.original.invoice_number}</span>
        </div>
      ),
    },
    {
      accessorKey: 'customer',
      header: 'Customer',
      cell: ({ row }) => (
        <div>
          <div className="text-sm font-medium">{row.original.customer?.name || 'N/A'}</div>
          {row.original.customer?.gstin && (
            <div className="text-xs text-muted-foreground font-mono">{row.original.customer.gstin}</div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'invoice_date',
      header: 'Invoice Date',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.invoice_date)}
        </span>
      ),
    },
    {
      accessorKey: 'due_date',
      header: 'Due Date',
      cell: ({ row }) => {
        const isOverdue = new Date(row.original.due_date) < new Date() && row.original.status !== 'PAID';
        return (
          <span className={`text-sm ${isOverdue ? 'text-red-600 font-medium' : 'text-muted-foreground'}`}>
            {formatDate(row.original.due_date)}
          </span>
        );
      },
    },
    {
      accessorKey: 'total_amount',
      header: 'Amount',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{formatCurrency(row.original.total_amount)}</div>
          {row.original.paid_amount > 0 && row.original.paid_amount < row.original.total_amount && (
            <div className="text-xs text-muted-foreground">
              Paid: {formatCurrency(row.original.paid_amount)}
            </div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'irn',
      header: 'IRN',
      cell: ({ row }) => (
        row.original.irn ? (
          <div className="flex items-center gap-1">
            <Shield className="h-3 w-3 text-green-600" />
            <span className="text-xs text-green-600">E-Invoice</span>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">-</span>
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
            <DropdownMenuItem onClick={() => handleViewInvoice(row.original)}>
              <Eye className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleDownload(row.original)}>
              <Download className="mr-2 h-4 w-4" />
              Download
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handlePrint(row.original)}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </DropdownMenuItem>
            {row.original.status === 'DRAFT' && (
              <DropdownMenuItem>
                <Send className="mr-2 h-4 w-4" />
                Send to Customer
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            {!row.original.irn && row.original.status !== 'CANCELLED' && (
              <DropdownMenuItem
                onClick={() => generateIRNMutation.mutate(row.original.id)}
                disabled={generateIRNMutation.isPending}
              >
                <Shield className="mr-2 h-4 w-4" />
                Generate IRN
              </DropdownMenuItem>
            )}
            {row.original.irn && (
              <DropdownMenuItem
                onClick={() => cancelIRNMutation.mutate({ id: row.original.id, reason: 'Cancelled' })}
                className="text-destructive"
              >
                <XCircle className="mr-2 h-4 w-4" />
                Cancel IRN
              </DropdownMenuItem>
            )}
            {isSuperAdmin && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => { setInvoiceToDelete(row.original); setIsDeleteOpen(true); }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const customers = customersData?.items ?? [];
  const dealers = dealersData?.items ?? [];
  const warehouses = warehousesDropdown ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Invoices"
        description="Manage sales invoices and billing"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) resetForm(); else setIsDialogOpen(true); }}>
            <DialogTrigger asChild>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Invoice</DialogTitle>
                <DialogDescription>Create a new sales invoice with product lookup and stock check</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {/* Row 1: Customer/Dealer + Warehouse */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{isSuperAdmin ? 'Customer / Dealer' : 'Customer'} *</Label>
                    <Select
                      value={formData.entity_id ? `${formData.entity_type}::${formData.entity_id}` : 'select'}
                      onValueChange={(value) => {
                        if (value === 'select') {
                          setFormData(prev => ({ ...prev, entity_type: '', entity_id: '' }));
                        } else {
                          const [type, id] = value.split('::');
                          setFormData(prev => {
                            // Reset item prices when switching entity type
                            const newItems = prev.items.map(item => ({
                              ...item,
                              // Prices will be recalculated on next product select
                            }));
                            return { ...prev, entity_type: type as 'customer' | 'dealer', entity_id: id, items: newItems };
                          });
                        }
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={isSuperAdmin ? 'Select customer or dealer' : 'Select customer'} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="select" disabled>{isSuperAdmin ? 'Select customer or dealer' : 'Select customer'}</SelectItem>
                        {isSuperAdmin && dealers.length > 0 && (
                          <SelectGroup>
                            <SelectLabel className="text-xs font-semibold text-blue-600">Dealers</SelectLabel>
                            {dealers
                              .filter((d: DealerItem) => d.id && d.id.trim() !== '')
                              .map((d: DealerItem) => (
                                <SelectItem key={`dealer-${d.id}`} value={`dealer::${d.id}`}>
                                  {d.name} {d.gstin ? `(${d.gstin})` : ''}
                                </SelectItem>
                              ))}
                          </SelectGroup>
                        )}
                        {customers.length > 0 && (
                          <SelectGroup>
                            <SelectLabel className="text-xs font-semibold text-green-600">Customers</SelectLabel>
                            {customers
                              .filter((c: Customer) => c.id && c.id.trim() !== '')
                              .map((c: Customer) => (
                                <SelectItem key={`customer-${c.id}`} value={`customer::${c.id}`}>
                                  {c.name}
                                </SelectItem>
                              ))}
                          </SelectGroup>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Warehouse *</Label>
                    <Select
                      value={formData.warehouse_id || 'select'}
                      onValueChange={(value) => {
                        if (value === 'select') return;
                        handleWarehouseChange(value);
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="select" disabled>Select warehouse</SelectItem>
                        {warehouses
                          .filter((w: { id: string; is_active?: boolean }) => w.is_active !== false)
                          .map((w: { id: string; name: string; code: string; city?: string; state?: string }) => (
                            <SelectItem key={w.id} value={w.id}>
                              {w.name} ({w.code}){w.city ? ` - ${w.city}` : ''}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Row 2: Dates */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Invoice Date *</Label>
                    <Input
                      type="date"
                      value={formData.invoice_date}
                      onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Due Date *</Label>
                    <Input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    />
                  </div>
                </div>

                {/* Items Section */}
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <Label className="text-base font-semibold">Items</Label>
                    <Button type="button" variant="outline" size="sm" onClick={addItem}>
                      <Plus className="h-3 w-3 mr-1" /> Add Item
                    </Button>
                  </div>
                  {formData.items.map((item, index) => (
                    <div key={index} className="p-3 border rounded-lg space-y-2 bg-muted/30">
                      {/* Product search row */}
                      <div className="flex items-start gap-2">
                        <div className="flex-1 relative" ref={activeSearchIndex === index ? dropdownRef : undefined}>
                          <Label className="text-xs text-muted-foreground">Product</Label>
                          {item.product_id ? (
                            <div className="flex items-center gap-2 mt-1">
                              <div className="flex-1 text-sm font-medium truncate">{item.product_name}</div>
                              {/* Stock badge */}
                              {item.available_stock !== null && formData.warehouse_id && (
                                <Badge variant={item.available_stock >= item.quantity ? 'default' : 'destructive'} className="text-xs whitespace-nowrap">
                                  <Package className="h-3 w-3 mr-1" />
                                  {item.available_stock} in stock
                                </Badge>
                              )}
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => {
                                  const newItems = [...formData.items];
                                  newItems[index] = { ...newItems[index], product_id: '', product_name: '', hsn_code: '84212110', unit_price: 0, tax_rate: 18, available_stock: null };
                                  setFormData({ ...formData, items: newItems });
                                }}
                              >
                                <XCircle className="h-3.5 w-3.5 text-muted-foreground" />
                              </Button>
                            </div>
                          ) : (
                            <>
                              <div className="relative mt-1">
                                <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                                <Input
                                  placeholder="Search product name or SKU..."
                                  className="pl-7 h-9"
                                  value={productSearchTerms[index] || ''}
                                  onChange={(e) => handleProductSearchChange(index, e.target.value)}
                                  onFocus={() => setActiveSearchIndex(index)}
                                />
                              </div>
                              {/* Search dropdown */}
                              {activeSearchIndex === index && debouncedSearchTerm.length >= 2 && productSearchResults?.items && productSearchResults.items.length > 0 && (
                                <div className="absolute z-50 mt-1 w-full bg-popover border rounded-md shadow-lg max-h-48 overflow-y-auto">
                                  {productSearchResults.items.map((product: Product) => (
                                    <button
                                      key={product.id}
                                      type="button"
                                      className="w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors border-b last:border-0"
                                      onClick={() => handleProductSelect(index, product)}
                                    >
                                      <div className="font-medium truncate">{product.name}</div>
                                      <div className="text-xs text-muted-foreground flex flex-wrap gap-2">
                                        <span>SKU: {product.sku}</span>
                                        {product.hsn_code && <span>HSN: {product.hsn_code}</span>}
                                        <span>MRP: {formatCurrency(product.mrp)}</span>
                                        {product.dealer_price && <span>Dealer: {formatCurrency(product.dealer_price)}</span>}
                                      </div>
                                    </button>
                                  ))}
                                </div>
                              )}
                              {/* Or type manually */}
                              {activeSearchIndex !== index && !item.product_id && (
                                <Input
                                  placeholder="Or type product name"
                                  className="mt-1 h-9"
                                  value={item.product_name}
                                  onChange={(e) => updateItem(index, 'product_name', e.target.value)}
                                />
                              )}
                            </>
                          )}
                        </div>
                        <div className="pt-5">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => removeItem(index)}
                            disabled={formData.items.length === 1}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>

                      {/* Stock warning */}
                      {item.available_stock !== null && item.available_stock < item.quantity && formData.warehouse_id && (
                        <div className="flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                          <AlertTriangle className="h-3 w-3" />
                          <span>Only {item.available_stock} available, requesting {item.quantity}</span>
                        </div>
                      )}

                      {/* Fields row: HSN, Qty, Price, GST%, Line Total */}
                      <div className="grid grid-cols-12 gap-2 items-end">
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs text-muted-foreground">HSN</Label>
                          <Input
                            placeholder="HSN Code"
                            className="h-8 text-xs font-mono"
                            value={item.hsn_code}
                            onChange={(e) => updateItem(index, 'hsn_code', e.target.value)}
                          />
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs text-muted-foreground">Qty</Label>
                          <Input
                            type="number"
                            min="1"
                            className="h-8 text-xs"
                            value={item.quantity}
                            onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                          />
                        </div>
                        <div className="col-span-3 space-y-1">
                          <Label className="text-xs text-muted-foreground">Unit Price</Label>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            className="h-8 text-xs"
                            value={item.unit_price}
                            onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs text-muted-foreground">GST %</Label>
                          <Input
                            type="number"
                            min="0"
                            max="28"
                            className="h-8 text-xs"
                            value={item.tax_rate}
                            onChange={(e) => updateItem(index, 'tax_rate', parseFloat(e.target.value) || 0)}
                          />
                        </div>
                        <div className="col-span-3 space-y-1">
                          <Label className="text-xs text-muted-foreground">Line Total</Label>
                          <div className="h-8 flex items-center text-xs font-semibold text-right">
                            {formatCurrency(item.quantity * item.unit_price * (1 + item.tax_rate / 100))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* GST Breakdown Preview */}
                {formData.items.some(item => item.unit_price > 0) && (
                  <Card className="bg-muted/50">
                    <CardContent className="pt-4 space-y-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Subtotal</span>
                        <span className="font-medium">{formatCurrency(gstPreview.subtotal)}</span>
                      </div>
                      {Object.entries(gstPreview.taxBreakdown).map(([rate, { tax }]) => (
                        <div key={rate} className="flex justify-between text-sm">
                          <span className="text-muted-foreground">GST ({rate}%)</span>
                          <span>{formatCurrency(tax)}</span>
                        </div>
                      ))}
                      <div className="text-[10px] text-muted-foreground italic">
                        * CGST/SGST/IGST split determined by backend based on warehouse &amp; customer state
                      </div>
                      <div className="flex justify-between text-base font-bold border-t pt-2">
                        <span>Grand Total</span>
                        <span>{formatCurrency(gstPreview.grandTotal)}</span>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Notes */}
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea
                    placeholder="Additional notes (optional)"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm}>Cancel</Button>
                <Button onClick={handleSubmit} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create Invoice
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="invoice_number"
        searchPlaceholder="Search invoices..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Invoice Detail Sheet */}
      <Sheet open={isViewOpen} onOpenChange={setIsViewOpen}>
        <SheetContent className="w-[600px] sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Invoice {selectedInvoice?.invoice_number}</SheetTitle>
            <SheetDescription>Invoice details and line items</SheetDescription>
          </SheetHeader>
          {selectedInvoice && (
            <div className="mt-6 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Customer</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-lg font-medium">{selectedInvoice.customer?.name}</div>
                  {selectedInvoice.customer?.gstin && (
                    <div className="text-sm text-muted-foreground">GSTIN: {selectedInvoice.customer.gstin}</div>
                  )}
                </CardContent>
              </Card>

              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-xs text-muted-foreground">Invoice Date</div>
                    <div className="font-medium">{formatDate(selectedInvoice.invoice_date)}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-xs text-muted-foreground">Due Date</div>
                    <div className="font-medium">{formatDate(selectedInvoice.due_date)}</div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Items</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedInvoice.items?.map((item, idx) => (
                      <div key={idx} className="flex justify-between py-2 border-b last:border-0">
                        <div>
                          <div className="font-medium">{item.product_name}</div>
                          <div className="text-sm text-muted-foreground">
                            {item.quantity} x {formatCurrency(item.unit_price)} @ {item.tax_rate}%
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">{formatCurrency(item.total)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>{formatCurrency(selectedInvoice.subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tax</span>
                    <span>{formatCurrency(selectedInvoice.tax_amount)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg border-t pt-2">
                    <span>Total</span>
                    <span>{formatCurrency(selectedInvoice.total_amount)}</span>
                  </div>
                  {selectedInvoice.paid_amount > 0 && (
                    <>
                      <div className="flex justify-between text-green-600">
                        <span>Paid</span>
                        <span>{formatCurrency(selectedInvoice.paid_amount)}</span>
                      </div>
                      <div className="flex justify-between font-medium">
                        <span>Balance</span>
                        <span>{formatCurrency(selectedInvoice.total_amount - selectedInvoice.paid_amount)}</span>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              {selectedInvoice.irn && (
                <Card className="bg-green-50">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2">
                      <Shield className="h-5 w-5 text-green-600" />
                      <div>
                        <div className="font-medium text-green-800">E-Invoice Generated</div>
                        <div className="text-xs text-green-600 font-mono">{selectedInvoice.irn}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="flex gap-2">
                <Button className="flex-1" onClick={() => handleDownload(selectedInvoice)}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
                {!selectedInvoice.irn && (
                  <Button
                    variant="outline"
                    onClick={() => generateIRNMutation.mutate(selectedInvoice.id)}
                    disabled={generateIRNMutation.isPending}
                  >
                    <Shield className="mr-2 h-4 w-4" />
                    Generate IRN
                  </Button>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Delete Invoice Confirmation */}
      <AlertDialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Invoice</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete invoice <strong>{invoiceToDelete?.invoice_number}</strong>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => invoiceToDelete && deleteMutation.mutate(invoiceToDelete.id)}
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
