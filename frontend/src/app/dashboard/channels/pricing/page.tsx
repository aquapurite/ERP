'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, DollarSign, TrendingUp, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import { channelsApi, productsApi, categoriesApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

interface Category {
  id: string;
  name: string;
  slug: string;
}

interface ChannelPricing {
  id: string;
  channel_id: string;
  product_id: string;
  variant_id?: string;
  mrp: number;
  selling_price: number;
  transfer_price?: number;
  discount_percentage?: number;
  max_discount_percentage?: number;
  is_active: boolean;
  is_listed: boolean;
  effective_from?: string;
  effective_to?: string;
  created_at: string;
  updated_at: string;
  // Computed/joined fields
  margin_percentage?: number;
}

interface Channel {
  id: string;
  code: string;
  name: string;
  type: string;
}

interface Product {
  id: string;
  name: string;
  sku: string;
  mrp: number;
}

// Separate component for action cell to avoid hooks in render function
function PricingActionsCell({
  pricing,
  channelId,
  onEdit,
  onDelete,
}: {
  pricing: ChannelPricing;
  channelId: string;
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

export default function ChannelPricingPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [selectedChannelId, setSelectedChannelId] = useState<string>('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');
  const [activeTab, setActiveTab] = useState('pricing');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedPricing, setSelectedPricing] = useState<ChannelPricing | null>(null);
  const [formData, setFormData] = useState({
    product_id: '',
    mrp: 0,
    selling_price: 0,
    transfer_price: 0,
    discount_percentage: 0,
    max_discount_percentage: 25,
    is_active: true,
    is_listed: true,
  });

  const queryClient = useQueryClient();

  // Fetch channels for dropdown
  const { data: channels = [] } = useQuery({
    queryKey: ['channels-dropdown'],
    queryFn: () => channelsApi.dropdown(),
  });

  // Fetch categories for dropdown
  const { data: categoriesData } = useQuery({
    queryKey: ['categories-dropdown'],
    queryFn: () => categoriesApi.list({ size: 100 }),
  });
  const categories: Category[] = categoriesData?.items || [];

  // Fetch products for dropdown (filtered by category if selected)
  const { data: productsData } = useQuery({
    queryKey: ['products-dropdown', selectedCategoryId],
    queryFn: () => productsApi.list({
      size: 100,
      ...(selectedCategoryId ? { category_id: selectedCategoryId } : {})
    }),
  });
  const products: Product[] = productsData?.items || [];

  // Fetch pricing for selected channel
  const { data: pricingData, isLoading } = useQuery({
    queryKey: ['channel-pricing', selectedChannelId, page, pageSize],
    queryFn: () => channelsApi.pricing.list(selectedChannelId, {
      skip: page * pageSize,
      limit: pageSize,
    }),
    enabled: !!selectedChannelId,
  });

  // Get product map for displaying names
  const productMap = useMemo(() => {
    const map = new Map<string, Product>();
    products.forEach(p => map.set(p.id, p));
    return map;
  }, [products]);

  // Get channel map
  const channelMap = useMemo(() => {
    const map = new Map<string, Channel>();
    channels.forEach((c: Channel) => map.set(c.id, c));
    return map;
  }, [channels]);

  // Calculate stats from pricing data
  const stats = useMemo(() => {
    const items = pricingData?.items || [];
    const totalProducts = items.length;
    const avgMargin = totalProducts > 0
      ? items.reduce((sum: number, p: ChannelPricing) => {
          const margin = p.mrp > 0 ? ((p.mrp - p.selling_price) / p.mrp) * 100 : 0;
          return sum + margin;
        }, 0) / totalProducts
      : 0;
    const belowThreshold = items.filter((p: ChannelPricing) => {
      const margin = p.mrp > 0 ? ((p.mrp - p.selling_price) / p.mrp) * 100 : 0;
      return margin < 10;
    }).length;

    return {
      total_products_mapped: pricingData?.total || 0,
      avg_margin_percent: avgMargin,
      products_below_threshold: belowThreshold,
      total_channels: channels.length,
    };
  }, [pricingData, channels]);

  // Handlers
  const handleEdit = (pricing: ChannelPricing) => {
    setSelectedPricing(pricing);
    setFormData({
      product_id: pricing.product_id,
      mrp: pricing.mrp,
      selling_price: pricing.selling_price,
      transfer_price: pricing.transfer_price || 0,
      discount_percentage: pricing.discount_percentage || 0,
      max_discount_percentage: pricing.max_discount_percentage || 25,
      is_active: pricing.is_active,
      is_listed: pricing.is_listed,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (pricing: ChannelPricing) => {
    const product = productMap.get(pricing.product_id);
    if (confirm(`Remove pricing for ${product?.name || 'this product'}?`)) {
      deleteMutation.mutate({ channelId: selectedChannelId, pricingId: pricing.id });
    }
  };

  const handleAddNew = () => {
    if (!selectedChannelId) {
      toast.error('Please select a channel first');
      return;
    }
    setSelectedPricing(null);
    setFormData({
      product_id: '',
      mrp: 0,
      selling_price: 0,
      transfer_price: 0,
      discount_percentage: 0,
      max_discount_percentage: 25,
      is_active: true,
      is_listed: true,
    });
    setIsDialogOpen(true);
  };

  // Column definitions
  const columns: ColumnDef<ChannelPricing>[] = useMemo(() => [
    {
      accessorKey: 'product_id',
      header: 'Product',
      cell: ({ row }) => {
        const product = productMap.get(row.original.product_id);
        return (
          <div>
            <div className="font-medium">{product?.name || 'Unknown Product'}</div>
            <div className="text-sm text-muted-foreground">{product?.sku || '-'}</div>
          </div>
        );
      },
    },
    {
      accessorKey: 'mrp',
      header: 'MRP',
      cell: ({ row }) => (
        <span className="font-mono text-sm">{formatCurrency(row.original.mrp)}</span>
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
      id: 'discount',
      header: 'Discount',
      cell: ({ row }) => {
        const discount = row.original.mrp > 0
          ? ((row.original.mrp - row.original.selling_price) / row.original.mrp) * 100
          : 0;
        return (
          <span className="text-orange-600 font-medium">
            {discount.toFixed(1)}%
          </span>
        );
      },
    },
    {
      id: 'margin',
      header: 'Margin %',
      cell: ({ row }) => {
        const margin = row.original.mrp > 0
          ? ((row.original.mrp - row.original.selling_price) / row.original.mrp) * 100
          : 0;
        const color = margin >= 20 ? 'text-green-600' : margin >= 10 ? 'text-yellow-600' : 'text-red-600';
        return <span className={`font-medium ${color}`}>{margin.toFixed(1)}%</span>;
      },
    },
    {
      accessorKey: 'max_discount_percentage',
      header: 'Max Discount',
      cell: ({ row }) => {
        const maxDiscount = row.original.max_discount_percentage || 0;
        return (
          <span className="text-sm text-muted-foreground">
            {maxDiscount > 0 ? `${maxDiscount}%` : '-'}
          </span>
        );
      },
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          row.original.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
        }`}>
          {row.original.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <PricingActionsCell
          pricing={row.original}
          channelId={selectedChannelId}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      ),
    },
  ], [productMap, selectedChannelId]);

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof channelsApi.pricing.create>[1]) =>
      channelsApi.pricing.create(selectedChannelId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel-pricing'] });
      toast.success('Pricing rule created successfully');
      setIsDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create pricing rule');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: { pricingId: string; pricing: Parameters<typeof channelsApi.pricing.update>[2] }) =>
      channelsApi.pricing.update(selectedChannelId, data.pricingId, data.pricing),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel-pricing'] });
      toast.success('Pricing updated successfully');
      setIsDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update pricing');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (data: { channelId: string; pricingId: string }) =>
      channelsApi.pricing.delete(data.channelId, data.pricingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel-pricing'] });
      toast.success('Pricing rule removed');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to remove pricing rule');
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => channelsApi.pricing.sync(selectedChannelId),
    onSuccess: (result) => {
      toast.success(`Synced ${result.synced_count} pricing rules to channel`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to sync pricing');
    },
  });

  const handleSubmit = () => {
    if (selectedPricing) {
      updateMutation.mutate({
        pricingId: selectedPricing.id,
        pricing: {
          mrp: formData.mrp,
          selling_price: formData.selling_price,
          transfer_price: formData.transfer_price || undefined,
          discount_percentage: formData.discount_percentage || undefined,
          max_discount_percentage: formData.max_discount_percentage || undefined,
          is_active: formData.is_active,
          is_listed: formData.is_listed,
        },
      });
    } else {
      createMutation.mutate({
        product_id: formData.product_id,
        mrp: formData.mrp,
        selling_price: formData.selling_price,
        transfer_price: formData.transfer_price || undefined,
        discount_percentage: formData.discount_percentage || undefined,
        max_discount_percentage: formData.max_discount_percentage || undefined,
        is_active: formData.is_active,
        is_listed: formData.is_listed,
      });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Channel Pricing"
        description="Manage product prices across different sales channels"
        actions={
          <div className="flex gap-2">
            {selectedChannelId && (
              <Button
                variant="outline"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
              >
                {syncMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Sync to Channel
              </Button>
            )}
            <Button onClick={handleAddNew} disabled={!selectedChannelId}>
              <Plus className="mr-2 h-4 w-4" />
              Add Pricing Rule
            </Button>
          </div>
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
            <div className="text-2xl font-bold">{stats.total_products_mapped}</div>
            <p className="text-xs text-muted-foreground">In selected channel</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Margin</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.avg_margin_percent.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Average across products</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Below Threshold</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.products_below_threshold}</div>
            <p className="text-xs text-muted-foreground">Products with margin &lt; 10%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Channels</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_channels}</div>
            <p className="text-xs text-muted-foreground">Available channels</p>
          </CardContent>
        </Card>
      </div>

      {/* Channel and Category Selectors */}
      <div className="flex gap-4 flex-wrap">
        <Select value={selectedChannelId} onValueChange={setSelectedChannelId}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select a channel to manage pricing" />
          </SelectTrigger>
          <SelectContent>
            {channels.map((channel: Channel) => (
              <SelectItem key={channel.id} value={channel.id}>
                {channel.name} ({channel.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedCategoryId} onValueChange={setSelectedCategoryId}>
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!selectedChannelId ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <DollarSign className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">Select a Channel</p>
            <p className="text-sm text-muted-foreground">Choose a sales channel above to view and manage its pricing</p>
          </CardContent>
        </Card>
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="pricing" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Pricing
            </TabsTrigger>
            <TabsTrigger value="commission" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Commission
            </TabsTrigger>
            <TabsTrigger value="rules" className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Rules
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="pricing" className="space-y-4">
            <DataTable
              columns={columns}
              data={pricingData?.items ?? []}
              searchKey="product_id"
              searchPlaceholder="Search products..."
              isLoading={isLoading}
              manualPagination
              pageCount={Math.ceil((pricingData?.total || 0) / pageSize)}
              pageIndex={page}
              pageSize={pageSize}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
            />
          </TabsContent>

          <TabsContent value="commission" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Commission Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Default Commission %</Label>
                      <Input type="number" placeholder="0" defaultValue="10" />
                      <p className="text-xs text-muted-foreground">Applied to all products in this channel</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Fixed Fee per Order</Label>
                      <Input type="number" placeholder="0" defaultValue="0" />
                      <p className="text-xs text-muted-foreground">Additional fee per order</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Payment Gateway Fee %</Label>
                      <Input type="number" placeholder="0" defaultValue="2" />
                      <p className="text-xs text-muted-foreground">Deducted from order value</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Logistics Fee</Label>
                      <Input type="number" placeholder="0" defaultValue="50" />
                      <p className="text-xs text-muted-foreground">Per shipment charge</p>
                    </div>
                  </div>
                  <div className="pt-4 border-t">
                    <Button>Save Commission Settings</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rules" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Pricing Rules</CardTitle>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Rule
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Volume Discount Rule */}
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">VOLUME_DISCOUNT</Badge>
                        <span className="font-medium">Bulk Purchase Discount</span>
                      </div>
                      <Badge variant="outline" className="text-green-600">Active</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      Quantity-based discounts for bulk orders
                    </p>
                    <div className="grid grid-cols-4 gap-2 text-sm">
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">10+ units</div>
                        <div className="text-muted-foreground">3% off</div>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">25+ units</div>
                        <div className="text-muted-foreground">5% off</div>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">50+ units</div>
                        <div className="text-muted-foreground">7% off</div>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">100+ units</div>
                        <div className="text-muted-foreground">10% off</div>
                      </div>
                    </div>
                  </div>

                  {/* Customer Segment Rule */}
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">CUSTOMER_SEGMENT</Badge>
                        <span className="font-medium">Customer Type Pricing</span>
                      </div>
                      <Badge variant="outline" className="text-green-600">Active</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      Special pricing for different customer segments
                    </p>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">VIP Customers</div>
                        <div className="text-muted-foreground">5% off</div>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">Dealers</div>
                        <div className="text-muted-foreground">15% off</div>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <div className="font-medium">Distributors</div>
                        <div className="text-muted-foreground">20% off</div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Pricing History</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 text-sm border-b pb-4">
                    <div className="w-32 font-medium">2026-01-24 10:30</div>
                    <Badge variant="outline">PRICE_UPDATE</Badge>
                    <div className="flex-1">
                      <span className="font-medium">Aquapurite Blitz</span>
                      <span className="text-muted-foreground"> - Selling price changed from </span>
                      <span className="line-through text-red-500">₹15,999</span>
                      <span className="text-muted-foreground"> to </span>
                      <span className="text-green-600">₹14,999</span>
                    </div>
                    <div className="text-muted-foreground">by Admin</div>
                  </div>
                  <div className="flex items-center gap-4 text-sm border-b pb-4">
                    <div className="w-32 font-medium">2026-01-23 15:45</div>
                    <Badge variant="outline">RULE_ADDED</Badge>
                    <div className="flex-1">
                      <span className="font-medium">Volume Discount Rule</span>
                      <span className="text-muted-foreground"> created with 4 tiers</span>
                    </div>
                    <div className="text-muted-foreground">by Admin</div>
                  </div>
                  <div className="flex items-center gap-4 text-sm border-b pb-4">
                    <div className="w-32 font-medium">2026-01-22 09:15</div>
                    <Badge variant="outline">BULK_IMPORT</Badge>
                    <div className="flex-1">
                      <span className="font-medium">12 products</span>
                      <span className="text-muted-foreground"> pricing imported from CSV</span>
                    </div>
                    <div className="text-muted-foreground">by Admin</div>
                  </div>
                  <p className="text-sm text-muted-foreground text-center py-4">
                    Showing last 30 days of changes
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Add/Edit Pricing Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {selectedPricing ? 'Edit Channel Pricing' : 'Add Channel Pricing'}
            </DialogTitle>
            <DialogDescription>
              {selectedPricing
                ? `Update pricing for ${productMap.get(selectedPricing.product_id)?.name || 'this product'}`
                : `Set product pricing for ${channelMap.get(selectedChannelId)?.name || 'this channel'}`}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {!selectedPricing && (
              <div className="space-y-2">
                <Label>Product</Label>
                <Select
                  value={formData.product_id}
                  onValueChange={(value) => {
                    const product = productMap.get(value);
                    setFormData({
                      ...formData,
                      product_id: value,
                      mrp: product?.mrp || 0,
                      selling_price: product?.mrp || 0,
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        {product.name} ({product.sku})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>MRP</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={formData.mrp || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, mrp: parseFloat(e.target.value) || 0 })
                  }
                />
              </div>
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
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Transfer Price (B2B)</Label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={formData.transfer_price || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, transfer_price: parseFloat(e.target.value) || 0 })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Discount %</Label>
                <Input
                  type="number"
                  placeholder="0"
                  value={formData.discount_percentage || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, discount_percentage: parseFloat(e.target.value) || 0 })
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Max Discount % (Guard Rail)</Label>
              <Input
                type="number"
                placeholder="25"
                value={formData.max_discount_percentage || ''}
                onChange={(e) =>
                  setFormData({ ...formData, max_discount_percentage: parseFloat(e.target.value) || 0 })
                }
              />
              <p className="text-xs text-muted-foreground">Maximum discount allowed on this product for this channel</p>
            </div>
            {formData.mrp > 0 && formData.selling_price > 0 && (
              <div className="p-3 bg-muted rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>Calculated Margin:</span>
                  <span className={`font-medium ${
                    ((formData.mrp - formData.selling_price) / formData.mrp) * 100 >= 10
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}>
                    {(((formData.mrp - formData.selling_price) / formData.mrp) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending || updateMutation.isPending || (!selectedPricing && !formData.product_id)}
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
