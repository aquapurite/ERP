'use client';

import { useState, useMemo, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Eye, Send, CheckCircle, XCircle, FileText, ShoppingCart, Clock, AlertCircle, ArrowRight, Trash2, Loader2, Calendar, Printer, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
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
import { warehousesApi, productsApi, companyApi, purchaseRequisitionsApi, categoriesApi } from '@/lib/api';
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
  category_id?: string;
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
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/approve`, { action: "APPROVE" });
    return data;
  },
  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/approve`, { action: "REJECT", rejection_reason: reason });
    return data;
  },
  convertToPO: async (id: string, vendorId: string) => {
    const { data } = await apiClient.post(`/purchase/requisitions/${id}/convert-to-po`, { vendor_id: vendorId });
    return data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/purchase/requisitions/${id}`);
  },
  getById: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/requisitions/${id}`);
    return data;
  },
  print: async (id: string) => {
    const { data } = await apiClient.get(`/purchase/requisitions/${id}/print`, { responseType: 'text' });
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
  const router = useRouter();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedPR, setSelectedPR] = useState<PurchaseRequisition | null>(null);
  const [isConvertDialogOpen, setIsConvertDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [viewPRDetails, setViewPRDetails] = useState<any>(null);
  const [selectedVendorId, setSelectedVendorId] = useState('');

  // Form state
  const [nextPRNumber, setNextPRNumber] = useState<string>('');
  const [isLoadingPRNumber, setIsLoadingPRNumber] = useState(false);
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
    monthlyQtys: {} as Record<string, number>, // e.g., {"2026-01": 500, "2026-02": 500}
  });
  const [multiDeliveryMonths, setMultiDeliveryMonths] = useState<string[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('all');

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

  // Fetch next PR number when dialog opens
  useEffect(() => {
    if (isDialogOpen) {
      const fetchNextPRNumber = async () => {
        setIsLoadingPRNumber(true);
        try {
          const result = await purchaseRequisitionsApi.getNextNumber();
          setNextPRNumber(result.next_number);
        } catch (error) {
          console.error('Failed to fetch next PR number:', error);
        } finally {
          setIsLoadingPRNumber(false);
        }
      };
      fetchNextPRNumber();
    }
  }, [isDialogOpen]);

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

  // Fetch categories for dropdown filter
  const { data: categoriesData } = useQuery({
    queryKey: ['categories-dropdown'],
    queryFn: async () => {
      try {
        const result = await categoriesApi.list({ size: 100 });
        return result?.items || [];
      } catch {
        return [];
      }
    },
  });

  const categories = categoriesData || [];

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-dropdown'],
    queryFn: async () => {
      const { data } = await apiClient.get('/vendors', { params: { limit: 100 } });
      return data;
    },
  });

  const warehouses = warehousesData?.items ?? [];
  const allProducts = productsData?.items ?? [];
  const vendors = vendorsData?.items ?? [];

  // Filter products by selected category
  const products = useMemo(() => {
    if (selectedCategoryId === 'all') {
      return allProducts;
    }
    return allProducts.filter((p: any) => {
      // Check both category_id and nested category.id
      const productCategoryId = p.category_id || p.category?.id;
      return productCategoryId === selectedCategoryId;
    });
  }, [allProducts, selectedCategoryId]);

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

  const deleteMutation = useMutation({
    mutationFn: (id: string) => requisitionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-requisitions'] });
      queryClient.invalidateQueries({ queryKey: ['pr-stats'] });
      toast.success('PR deleted successfully');
      setIsDeleteDialogOpen(false);
      setSelectedPR(null);
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to delete PR'),
  });

  // Handle Print PR - Client-side HTML generation
  const handlePrintPR = async (pr: PurchaseRequisition) => {
    try {
      // Try to get full details, fallback to basic PR info
      let prDetails: any = pr;
      let company: any = null;

      try {
        prDetails = await requisitionsApi.getById(pr.id);
      } catch {
        // Use basic PR info
      }

      // Fetch company details
      try {
        company = await companyApi.getPrimary();
      } catch {
        // Use default company info
      }

      // Generate print-friendly HTML
      const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Purchase Requisition - ${prDetails.pr_number || 'PR'}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
            .company-header { text-align: center; margin-bottom: 20px; }
            .company-name { font-size: 22px; font-weight: bold; color: #1a1a1a; margin: 0; }
            .company-details { font-size: 11px; color: #666; margin: 5px 0; }
            .company-tax { font-size: 10px; color: #888; margin-top: 8px; }
            .header { text-align: center; border-top: 2px solid #333; border-bottom: 2px solid #333; padding: 10px 0; margin-bottom: 20px; }
            .header h1 { margin: 0; font-size: 18px; }
            .header p { margin: 5px 0; color: #666; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
            .info-item { padding: 8px; background: #f5f5f5; border-radius: 4px; }
            .info-item label { font-size: 11px; color: #666; display: block; }
            .info-item span { font-weight: bold; }
            .items-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            .items-table th, .items-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            .items-table th { background: #f0f0f0; font-size: 12px; }
            .items-table td { font-size: 13px; }
            .text-right { text-align: right; }
            .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
            .status-APPROVED { background: #d4edda; color: #155724; }
            .status-DRAFT { background: #e2e3e5; color: #383d41; }
            .status-SUBMITTED { background: #cce5ff; color: #004085; }
            .status-REJECTED { background: #f8d7da; color: #721c24; }
            .footer { margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 11px; color: #666; }
            .monthly-qty { font-size: 10px; color: #666; margin-top: 4px; }
            @media print { body { padding: 0; } }
          </style>
        </head>
        <body>
          <div class="company-header">
            <p class="company-name">${company?.legal_name || 'AQUAPURITE PRIVATE LIMITED'}</p>
            <p class="company-details">
              ${company?.address_line1 || 'PLOT 36-A, KH NO 181, PH-1, SHYAM VIHAR, DINDAPUR EXT'}${company?.address_line2 ? ', ' + company.address_line2 : ', Najafgarh'}<br/>
              ${company?.city || 'New Delhi'} - ${company?.pincode || '110043'}, ${company?.state || 'Delhi'}
            </p>
            <p class="company-details">
              Phone: ${company?.phone || '9013034083'} | Email: ${company?.email || 'riaansh97@gmail.com'}
            </p>
            <p class="company-tax">
              GSTIN: ${company?.gstin || '07ABDCA6170C1Z0'} | PAN: ${company?.pan || 'ABDCA6170C'} | CIN: ${company?.cin || 'U32909DL2025PTC454115'}
            </p>
          </div>

          <div class="header">
            <h1>PURCHASE REQUISITION</h1>
            <p><strong>${prDetails.pr_number || 'N/A'}</strong></p>
            <span class="status-badge status-${prDetails.status}">${prDetails.status}</span>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <label>Requester</label>
              <span>${prDetails.requester_name || 'N/A'}</span>
            </div>
            <div class="info-item">
              <label>Department</label>
              <span>${prDetails.department || prDetails.requesting_department || 'N/A'}</span>
            </div>
            <div class="info-item">
              <label>Warehouse</label>
              <span>${prDetails.warehouse_name || prDetails.delivery_warehouse_name || 'N/A'}</span>
            </div>
            <div class="info-item">
              <label>Required By</label>
              <span>${prDetails.required_by_date ? new Date(prDetails.required_by_date).toLocaleDateString() : 'N/A'}</span>
            </div>
            <div class="info-item">
              <label>Priority</label>
              <span>${prDetails.priority || 'NORMAL'}</span>
            </div>
            <div class="info-item">
              <label>Created Date</label>
              <span>${prDetails.created_at ? new Date(prDetails.created_at).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>

          ${prDetails.justification || prDetails.reason ? `
            <div style="margin-bottom: 20px; padding: 10px; background: #f9f9f9; border-radius: 4px;">
              <label style="font-size: 11px; color: #666;">Justification/Reason</label>
              <p style="margin: 5px 0 0 0;">${prDetails.justification || prDetails.reason}</p>
            </div>
          ` : ''}

          <h3 style="margin-bottom: 10px;">Items</h3>
          <table class="items-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Product</th>
                <th>SKU</th>
                <th class="text-right">Quantity</th>
                <th class="text-right">Est. Price</th>
                <th class="text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              ${(prDetails.items || []).map((item: any, index: number) => `
                <tr>
                  <td>${index + 1}</td>
                  <td>
                    ${item.product_name || 'N/A'}
                    ${item.monthly_quantities && Object.keys(item.monthly_quantities).length > 0 ? `
                      <div class="monthly-qty">
                        ${Object.entries(item.monthly_quantities).map(([month, qty]) => {
                          const d = new Date(month + '-01');
                          return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }) + ': ' + qty;
                        }).join(' | ')}
                      </div>
                    ` : ''}
                  </td>
                  <td>${item.sku || 'N/A'}</td>
                  <td class="text-right">${item.quantity_requested || item.quantity || 0}</td>
                  <td class="text-right">₹${(item.estimated_unit_price || item.unit_price || 0).toLocaleString()}</td>
                  <td class="text-right">₹${((item.quantity_requested || item.quantity || 0) * (item.estimated_unit_price || item.unit_price || 0)).toLocaleString()}</td>
                </tr>
              `).join('')}
            </tbody>
            <tfoot>
              <tr>
                <td colspan="5" class="text-right"><strong>Total Amount:</strong></td>
                <td class="text-right"><strong>₹${(prDetails.total_amount || prDetails.estimated_total || 0).toLocaleString()}</strong></td>
              </tr>
            </tfoot>
          </table>

          <div class="footer">
            <p>Printed on: ${new Date().toLocaleString()}</p>
          </div>
        </body>
        </html>
      `;

      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        printWindow.onload = () => {
          printWindow.print();
        };
      } else {
        toast.error('Please allow popups to print');
      }
    } catch (error) {
      toast.error('Failed to print PR');
    }
  };

  // Handle View Details
  const handleViewDetails = async (pr: PurchaseRequisition) => {
    try {
      const details = await requisitionsApi.getById(pr.id);
      setViewPRDetails(details);
      setSelectedPR(pr);
      setIsViewDialogOpen(true);
    } catch {
      // Use basic PR info if details fetch fails
      setViewPRDetails(pr);
      setSelectedPR(pr);
      setIsViewDialogOpen(true);
    }
  };

  // Handle Convert to PO - Navigate to PO page with PR ID
  const handleConvertToPO = (pr: PurchaseRequisition) => {
    // Navigate to Purchase Orders page with the PR ID as a query param
    router.push(`/procurement/purchase-orders?create=true&pr_id=${pr.id}`);
  };

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
    setNewItem({ product_id: '', quantity: 1, estimated_price: 0, monthlyQtys: {} });
    setMultiDeliveryMonths([]);
    setNextPRNumber('');
    setSelectedCategoryId('all');
    setIsDialogOpen(false);
  };

  const handleAddItem = () => {
    if (!newItem.product_id) {
      toast.error('Please select a product');
      return;
    }

    const product = products.find((p: Product) => p.id === newItem.product_id);
    if (!product) {
      toast.error('Product not found');
      return;
    }

    // For multi-delivery, use monthly quantities entered by user
    let monthly_quantities: Record<string, number> | undefined;
    let totalQty = newItem.quantity;

    if (formData.is_multi_delivery && multiDeliveryMonths.length > 0) {
      // Use the quantities entered for each month
      monthly_quantities = {};
      totalQty = 0;
      multiDeliveryMonths.forEach((month) => {
        const qty = newItem.monthlyQtys[month] || 0;
        if (qty > 0) {
          monthly_quantities![month] = qty;
          totalQty += qty;
        }
      });

      if (totalQty <= 0) {
        toast.error('Please enter quantity for at least one delivery month');
        return;
      }
    } else if (newItem.quantity <= 0) {
      toast.error('Please enter quantity');
      return;
    }

    setFormData({
      ...formData,
      items: [...formData.items, {
        product_id: product.id,
        product_name: product.name,
        sku: product.sku,
        quantity_requested: totalQty,
        estimated_unit_price: newItem.estimated_price || product.mrp || 0,
        uom: 'PCS',
        monthly_quantities,
      }],
    });
    setNewItem({ product_id: '', quantity: 1, estimated_price: 0, monthlyQtys: {} });
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
              {/* 1. View Details - Always available */}
              <DropdownMenuItem onClick={() => handleViewDetails(pr)}>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              {/* 2. Convert to PO - Only for APPROVED */}
              {pr.status === 'APPROVED' && (
                <DropdownMenuItem onClick={() => handleConvertToPO(pr)}>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  Convert to PO
                </DropdownMenuItem>
              )}
              {/* 3. Delete PR - Available for all except CONVERTED */}
              {pr.status !== 'CONVERTED' && (
                <DropdownMenuItem
                  className="text-red-600"
                  onClick={() => { setSelectedPR(pr); setIsDeleteDialogOpen(true); }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete PR
                </DropdownMenuItem>
              )}
              {/* 4. Print PDF - Always available */}
              <DropdownMenuItem onClick={() => handlePrintPR(pr)}>
                <Printer className="mr-2 h-4 w-4" />
                Print PDF
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {/* Status actions */}
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
            <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Purchase Requisition</DialogTitle>
                <DialogDescription>
                  Request items for procurement. This will go through an approval workflow.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {/* PR Number - Auto-generated, Read-only */}
                <div className="space-y-2">
                  <Label htmlFor="pr_number">PR Number (Auto-generated)</Label>
                  <div className="relative">
                    <Input
                      id="pr_number"
                      placeholder={isLoadingPRNumber ? "Loading..." : "PR-YYYYMMDD-0001"}
                      value={nextPRNumber}
                      readOnly
                      disabled
                      className="bg-muted pr-8 font-mono"
                    />
                    <Lock className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
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
                  <div className="border rounded-lg p-4 space-y-4">
                    {/* Category Filter - Full width row */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <Label className="text-sm font-medium">Product Category</Label>
                        <Select
                          value={selectedCategoryId}
                          onValueChange={(value) => {
                            setSelectedCategoryId(value);
                            // Reset product selection when category changes
                            setNewItem({ ...newItem, product_id: '', estimated_price: 0 });
                          }}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="All Categories" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Categories ({allProducts.length} products)</SelectItem>
                            {categories.map((cat: { id: string; name: string }) => (
                              <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex items-end pb-2">
                        <p className="text-sm text-muted-foreground">
                          {selectedCategoryId === 'all'
                            ? `Showing all ${products.length} products`
                            : `Showing ${products.length} product(s) in selected category`}
                        </p>
                      </div>
                    </div>

                    {/* Standard layout: Product, Qty, Est. Price, Add button - Better proportions */}
                    {!formData.is_multi_delivery && (
                      <div className="grid grid-cols-12 gap-3 items-end">
                        <div className="col-span-6">
                          <Label className="text-sm font-medium">Product {isLoadingProducts && <span className="text-muted-foreground">(loading...)</span>}</Label>
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
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder={isLoadingProducts ? "Loading products..." : "Select product"} />
                            </SelectTrigger>
                            <SelectContent>
                              {isLoadingProducts ? (
                                <SelectItem value="loading" disabled>Loading products...</SelectItem>
                              ) : productsError ? (
                                <SelectItem value="error" disabled>Error loading products</SelectItem>
                              ) : products.length === 0 ? (
                                <SelectItem value="empty" disabled>No products in this category</SelectItem>
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
                          <Label className="text-sm font-medium">Quantity</Label>
                          <Input
                            type="number"
                            min="1"
                            value={newItem.quantity}
                            onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 0 })}
                            className="w-full"
                          />
                        </div>
                        <div className="col-span-2">
                          <Label className="text-sm font-medium">Est. Price</Label>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={newItem.estimated_price || ''}
                            onChange={(e) => setNewItem({ ...newItem, estimated_price: parseFloat(e.target.value) || 0 })}
                            className="w-full"
                          />
                        </div>
                        <div className="col-span-2">
                          <Button type="button" onClick={handleAddItem} className="w-full h-10">
                            <Plus className="h-4 w-4 mr-1" />
                            Add
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Multi-delivery layout: Product, Est. Price, [Month Qty columns], Total, Add button */}
                    {formData.is_multi_delivery && (
                      <div className="space-y-3">
                        {multiDeliveryMonths.length === 0 ? (
                          <p className="text-sm text-amber-600 p-3 bg-amber-50 rounded-lg">
                            Please select delivery months above first
                          </p>
                        ) : (
                          <>
                            <div className="grid gap-2" style={{ gridTemplateColumns: `2fr 1fr ${multiDeliveryMonths.map(() => '1fr').join(' ')} 0.8fr 0.5fr` }}>
                              {/* Header */}
                              <div className="text-xs font-medium text-muted-foreground">Product</div>
                              <div className="text-xs font-medium text-muted-foreground">Est. Price</div>
                              {multiDeliveryMonths.map((month) => {
                                const d = new Date(`${month}-01`);
                                const label = d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                                return (
                                  <div key={month} className="text-xs font-medium text-muted-foreground text-center">{label}</div>
                                );
                              })}
                              <div className="text-xs font-medium text-muted-foreground text-right">Total</div>
                              <div></div>

                              {/* Input Row */}
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
                                <SelectTrigger className="h-9">
                                  <SelectValue placeholder={isLoadingProducts ? "Loading..." : "Select product"} />
                                </SelectTrigger>
                                <SelectContent>
                                  {isLoadingProducts ? (
                                    <SelectItem value="loading" disabled>Loading products...</SelectItem>
                                  ) : productsError ? (
                                    <SelectItem value="error" disabled>Error loading products</SelectItem>
                                  ) : products.length === 0 ? (
                                    <SelectItem value="empty" disabled>No products in this category</SelectItem>
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

                              <Input
                                type="number"
                                min="0"
                                step="0.01"
                                className="h-9"
                                placeholder="Price"
                                value={newItem.estimated_price || ''}
                                onChange={(e) => setNewItem({ ...newItem, estimated_price: parseFloat(e.target.value) || 0 })}
                              />

                              {multiDeliveryMonths.map((month) => (
                                <Input
                                  key={month}
                                  type="number"
                                  min="0"
                                  className="h-9 text-center"
                                  placeholder="Qty"
                                  value={newItem.monthlyQtys[month] || ''}
                                  onChange={(e) => {
                                    const qty = parseInt(e.target.value) || 0;
                                    setNewItem({
                                      ...newItem,
                                      monthlyQtys: { ...newItem.monthlyQtys, [month]: qty }
                                    });
                                  }}
                                />
                              ))}

                              <div className="h-9 flex items-center justify-end font-medium text-sm bg-muted rounded px-2">
                                {Object.values(newItem.monthlyQtys).reduce((sum, qty) => sum + (qty || 0), 0)}
                              </div>

                              <Button type="button" onClick={handleAddItem} size="sm" className="h-9">
                                <Plus className="h-4 w-4" />
                              </Button>
                            </div>
                          </>
                        )}
                      </div>
                    )}
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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Purchase Requisition</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete PR <strong>{selectedPR?.pr_number}</strong>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => { setIsDeleteDialogOpen(false); setSelectedPR(null); }}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => selectedPR && deleteMutation.mutate(selectedPR.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* View Details Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setIsViewDialogOpen(false);
          setViewPRDetails(null);
          setSelectedPR(null);
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Purchase Requisition Details</DialogTitle>
            <DialogDescription>
              {selectedPR?.pr_number}
            </DialogDescription>
          </DialogHeader>
          {viewPRDetails && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground text-xs">Status</Label>
                  <div className="mt-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[viewPRDetails.status]}`}>
                      {viewPRDetails.status}
                    </span>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Priority</Label>
                  <div className="mt-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[viewPRDetails.priority] || ''}`}>
                      {viewPRDetails.priority}
                    </span>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Requester</Label>
                  <p className="font-medium">{viewPRDetails.requester_name || 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Department</Label>
                  <p className="font-medium">{viewPRDetails.department || viewPRDetails.requesting_department || 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Warehouse</Label>
                  <p className="font-medium">{viewPRDetails.warehouse_name || viewPRDetails.delivery_warehouse_name || 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Required By</Label>
                  <p className="font-medium">{viewPRDetails.required_by_date ? formatDate(viewPRDetails.required_by_date) : 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Created At</Label>
                  <p className="font-medium">{formatDate(viewPRDetails.created_at)}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Total Amount</Label>
                  <p className="font-medium text-lg">{formatCurrency(viewPRDetails.total_amount || viewPRDetails.estimated_total || 0)}</p>
                </div>
              </div>

              {viewPRDetails.justification || viewPRDetails.reason ? (
                <div>
                  <Label className="text-muted-foreground text-xs">Justification</Label>
                  <p className="mt-1 text-sm">{viewPRDetails.justification || viewPRDetails.reason}</p>
                </div>
              ) : null}

              {/* Items Table */}
              {viewPRDetails.items && viewPRDetails.items.length > 0 && (
                <div>
                  <Label className="text-muted-foreground text-xs mb-2 block">Items ({viewPRDetails.items.length})</Label>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr>
                          <th className="px-3 py-2 text-left">Product</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-right">Est. Price</th>
                          <th className="px-3 py-2 text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {viewPRDetails.items.map((item: any, index: number) => (
                          <tr key={index} className="border-t">
                            <td className="px-3 py-2">
                              <div className="font-medium">{item.product_name}</div>
                              <div className="text-xs text-muted-foreground">{item.sku}</div>
                              {item.monthly_quantities && Object.keys(item.monthly_quantities).length > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {Object.entries(item.monthly_quantities).map(([month, qty]: [string, any]) => {
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
                            <td className="px-3 py-2 text-right">{item.quantity_requested || item.quantity}</td>
                            <td className="px-3 py-2 text-right">{formatCurrency(item.estimated_unit_price || item.unit_price || 0)}</td>
                            <td className="px-3 py-2 text-right font-medium">
                              {formatCurrency((item.quantity_requested || item.quantity || 0) * (item.estimated_unit_price || item.unit_price || 0))}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {viewPRDetails.po_number && (
                <div className="p-3 bg-purple-50 rounded-lg">
                  <Label className="text-muted-foreground text-xs">Converted to PO</Label>
                  <p className="font-medium text-purple-700">{viewPRDetails.po_number}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsViewDialogOpen(false)}>Close</Button>
            <Button onClick={() => selectedPR && handlePrintPR(selectedPR)}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
