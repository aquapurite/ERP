'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, DollarSign, TrendingUp, AlertCircle, Loader2 } from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatCurrency } from '@/lib/utils';

interface ChannelPricing {
  id: string;
  channel_id: string;
  channel_name: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  base_price: number;
  selling_price: number;
  commission_rate: number;
  commission_amount: number;
  net_realization: number;
  margin_percent: number;
  is_active: boolean;
}

interface PricingStats {
  total_products_mapped: number;
  avg_margin_percent: number;
  products_below_threshold: number;
  total_channels: number;
}

const pricingApi = {
  list: async (params?: { page?: number; size?: number; channel_id?: string; product_id?: string }) => {
    try {
      const { data } = await apiClient.get('/channels/pricing', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<PricingStats> => {
    try {
      const { data } = await apiClient.get('/channels/pricing/stats');
      return data;
    } catch {
      return { total_products_mapped: 0, avg_margin_percent: 0, products_below_threshold: 0, total_channels: 0 };
    }
  },
  create: async (pricing: Partial<ChannelPricing>) => {
    const { data } = await apiClient.post('/channels/pricing', pricing);
    return data;
  },
  update: async (id: string, pricing: Partial<ChannelPricing>) => {
    const { data } = await apiClient.put(`/channels/pricing/${id}`, pricing);
    return data;
  },
  bulkUpdate: async (items: { id: string; selling_price: number }[]) => {
    const { data } = await apiClient.post('/channels/pricing/bulk-update', { items });
    return data;
  },
};

// Separate component for action cell to avoid hooks in render function
function PricingActionsCell({
  pricing,
  onEdit,
  onDelete,
}: {
  pricing: ChannelPricing;
  onEdit: (pricing: ChannelPricing) => void;
  onDelete: (pricing: ChannelPricing) => void;
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
        <DropdownMenuItem onClick={() => onEdit(pricing)}>
          <Pencil className="mr-2 h-4 w-4" />
          Edit Price
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onDelete(pricing)} className="text-destructive focus:text-destructive">
          <Trash2 className="mr-2 h-4 w-4" />
          Remove
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Column definitions factory function
function getColumns(
  onEdit: (pricing: ChannelPricing) => void,
  onDelete: (pricing: ChannelPricing) => void
): ColumnDef<ChannelPricing>[] {
  return [
    {
      accessorKey: 'product_name',
      header: 'Product',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.product_name}</div>
          <div className="text-sm text-muted-foreground">{row.original.product_sku}</div>
        </div>
      ),
    },
    {
      accessorKey: 'channel_name',
      header: 'Channel',
      cell: ({ row }) => (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {row.original.channel_name}
        </span>
      ),
    },
    {
      accessorKey: 'base_price',
      header: 'Base Price',
      cell: ({ row }) => (
        <span className="font-mono text-sm">{formatCurrency(row.original.base_price)}</span>
      ),
    },
    {
      accessorKey: 'selling_price',
      header: 'Selling Price',
      cell: ({ row }) => (
        <span className="font-mono text-sm font-medium">{formatCurrency(row.original.selling_price)}</span>
      ),
    },
    {
      accessorKey: 'commission_rate',
      header: 'Commission',
      cell: ({ row }) => (
        <div className="text-sm">
          <div>{row.original.commission_rate}%</div>
          <div className="text-muted-foreground">{formatCurrency(row.original.commission_amount)}</div>
        </div>
      ),
    },
    {
      accessorKey: 'net_realization',
      header: 'Net Realization',
      cell: ({ row }) => (
        <span className="font-mono text-sm text-green-600">{formatCurrency(row.original.net_realization)}</span>
      ),
    },
    {
      accessorKey: 'margin_percent',
      header: 'Margin %',
      cell: ({ row }) => {
        const margin = row.original.margin_percent;
        const color = margin >= 20 ? 'text-green-600' : margin >= 10 ? 'text-yellow-600' : 'text-red-600';
        return <span className={`font-medium ${color}`}>{margin.toFixed(1)}%</span>;
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <PricingActionsCell pricing={row.original} onEdit={onEdit} onDelete={onDelete} />
      ),
    },
  ];
}

export default function ChannelPricingPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [channelFilter, setChannelFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedPricing, setSelectedPricing] = useState<ChannelPricing | null>(null);
  const [formData, setFormData] = useState({
    channel_id: '',
    product_id: '',
    selling_price: 0,
    commission_rate: 0,
  });

  const queryClient = useQueryClient();

  // Handlers for edit and delete
  const handleEdit = (pricing: ChannelPricing) => {
    setSelectedPricing(pricing);
    setFormData({
      channel_id: pricing.channel_id,
      product_id: pricing.product_id,
      selling_price: pricing.selling_price,
      commission_rate: pricing.commission_rate,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (pricing: ChannelPricing) => {
    if (confirm(`Remove pricing for ${pricing.product_name} on ${pricing.channel_name}?`)) {
      deleteMutation.mutate(pricing.id);
    }
  };

  const handleAddNew = () => {
    setSelectedPricing(null);
    setFormData({
      channel_id: '',
      product_id: '',
      selling_price: 0,
      commission_rate: 0,
    });
    setIsDialogOpen(true);
  };

  // Memoize columns with handlers
  const columns = useMemo(() => getColumns(handleEdit, handleDelete), []);

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: Partial<ChannelPricing>) => pricingApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel-pricing'] });
      queryClient.invalidateQueries({ queryKey: ['channel-pricing-stats'] });
      toast.success('Pricing rule created successfully');
      setIsDialogOpen(false);
    },
    onError: () => {
      toast.error('Failed to create pricing rule');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: { id: string; pricing: Partial<ChannelPricing> }) =>
      pricingApi.update(data.id, data.pricing),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel-pricing'] });
      queryClient.invalidateQueries({ queryKey: ['channel-pricing-stats'] });
      toast.success('Pricing updated successfully');
      setIsDialogOpen(false);
    },
    onError: () => {
      toast.error('Failed to update pricing');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/channels/pricing/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel-pricing'] });
      queryClient.invalidateQueries({ queryKey: ['channel-pricing-stats'] });
      toast.success('Pricing rule removed');
    },
    onError: () => {
      toast.error('Failed to remove pricing rule');
    },
  });

  const handleSubmit = () => {
    if (selectedPricing) {
      updateMutation.mutate({
        id: selectedPricing.id,
        pricing: formData,
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ['channel-pricing', page, pageSize, channelFilter],
    queryFn: () => pricingApi.list({
      page: page + 1,
      size: pageSize,
      channel_id: channelFilter !== 'all' ? channelFilter : undefined
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['channel-pricing-stats'],
    queryFn: pricingApi.getStats,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Channel Pricing"
        description="Manage product prices across different sales channels"
        actions={
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Pricing Rule
          </Button>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Products Mapped</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_products_mapped || 0}</div>
            <p className="text-xs text-muted-foreground">Across {stats?.total_channels || 0} channels</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Margin</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(stats?.avg_margin_percent || 0).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Average across all products</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Below Threshold</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.products_below_threshold || 0}</div>
            <p className="text-xs text-muted-foreground">Products with margin &lt; 10%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Channels</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_channels || 0}</div>
            <p className="text-xs text-muted-foreground">With pricing configured</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={channelFilter} onValueChange={setChannelFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by channel" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Channels</SelectItem>
            <SelectItem value="d2c">D2C</SelectItem>
            <SelectItem value="amazon">Amazon</SelectItem>
            <SelectItem value="flipkart">Flipkart</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="product_name"
        searchPlaceholder="Search products..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Add/Edit Pricing Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {selectedPricing ? 'Edit Channel Pricing' : 'Add Channel Pricing'}
            </DialogTitle>
            <DialogDescription>
              {selectedPricing
                ? `Update pricing for ${selectedPricing.product_name} on ${selectedPricing.channel_name}`
                : 'Set product pricing for a specific sales channel.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {!selectedPricing && (
              <>
                <div className="space-y-2">
                  <Label>Channel</Label>
                  <Select
                    value={formData.channel_id}
                    onValueChange={(value) => setFormData({ ...formData, channel_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select channel" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="d2c">D2C Website</SelectItem>
                      <SelectItem value="amazon">Amazon India</SelectItem>
                      <SelectItem value="flipkart">Flipkart</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Product</Label>
                  <Select
                    value={formData.product_id}
                    onValueChange={(value) => setFormData({ ...formData, product_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select product" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="prod1">Product 1</SelectItem>
                      <SelectItem value="prod2">Product 2</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Selling Price</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={formData.selling_price || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, selling_price: parseFloat(e.target.value) || 0 })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Commission %</Label>
                <Input
                  type="number"
                  placeholder="0"
                  value={formData.commission_rate || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, commission_rate: parseFloat(e.target.value) || 0 })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {(createMutation.isPending || updateMutation.isPending) && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {selectedPricing ? 'Update Pricing' : 'Save Pricing'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
