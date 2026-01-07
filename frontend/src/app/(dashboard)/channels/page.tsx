'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Eye, Power, PowerOff, Network, ShoppingBag, TrendingUp } from 'lucide-react';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatCurrency, formatDate } from '@/lib/utils';

interface SalesChannel {
  id: string;
  name: string;
  code: string;
  channel_type: 'D2C' | 'MARKETPLACE' | 'B2B' | 'DEALER' | 'OFFLINE';
  marketplace_name?: string;
  api_key?: string;
  api_secret?: string;
  seller_id?: string;
  warehouse_id?: string;
  is_active: boolean;
  auto_sync_orders: boolean;
  auto_sync_inventory: boolean;
  commission_rate?: number;
  description?: string;
  created_at: string;
}

interface ChannelStats {
  total_channels: number;
  active_channels: number;
  total_orders_today: number;
  total_revenue_today: number;
}

const channelsApi = {
  list: async (params?: { page?: number; size?: number; channel_type?: string }) => {
    try {
      const { data } = await apiClient.get('/channels', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<ChannelStats> => {
    try {
      const { data } = await apiClient.get('/channels/stats');
      return data;
    } catch {
      return { total_channels: 0, active_channels: 0, total_orders_today: 0, total_revenue_today: 0 };
    }
  },
  create: async (channel: Partial<SalesChannel>) => {
    const { data } = await apiClient.post('/channels', channel);
    return data;
  },
  activate: async (id: string) => {
    const { data } = await apiClient.post(`/channels/${id}/activate`);
    return data;
  },
  deactivate: async (id: string) => {
    const { data } = await apiClient.post(`/channels/${id}/deactivate`);
    return data;
  },
};

const channelTypeColors: Record<string, string> = {
  D2C: 'bg-blue-100 text-blue-800',
  MARKETPLACE: 'bg-purple-100 text-purple-800',
  B2B: 'bg-green-100 text-green-800',
  DEALER: 'bg-orange-100 text-orange-800',
  OFFLINE: 'bg-gray-100 text-gray-800',
};

const marketplaces = [
  'Amazon', 'Flipkart', 'Myntra', 'Meesho', 'JioMart', 'TataCliq', 'Ajio', 'Nykaa'
];

const columns: ColumnDef<SalesChannel>[] = [
  {
    accessorKey: 'name',
    header: 'Channel',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Network className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'channel_type',
    header: 'Type',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${channelTypeColors[row.original.channel_type]}`}>
        {row.original.channel_type}
      </span>
    ),
  },
  {
    accessorKey: 'marketplace_name',
    header: 'Marketplace',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.marketplace_name || '-'}</span>
    ),
  },
  {
    accessorKey: 'commission_rate',
    header: 'Commission',
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.commission_rate ? `${row.original.commission_rate}%` : '-'}
      </span>
    ),
  },
  {
    accessorKey: 'sync',
    header: 'Auto Sync',
    cell: ({ row }) => (
      <div className="flex gap-2">
        <span className={`px-2 py-0.5 rounded text-xs ${
          row.original.auto_sync_orders ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
        }`}>
          Orders
        </span>
        <span className={`px-2 py-0.5 rounded text-xs ${
          row.original.auto_sync_inventory ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
        }`}>
          Inventory
        </span>
      </div>
    ),
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />,
  },
  {
    accessorKey: 'created_at',
    header: 'Created',
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">{formatDate(row.original.created_at)}</span>
    ),
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const queryClient = useQueryClient();

      const activateMutation = useMutation({
        mutationFn: () => channelsApi.activate(row.original.id),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['channels'] });
          toast.success('Channel activated');
        },
      });

      const deactivateMutation = useMutation({
        mutationFn: () => channelsApi.deactivate(row.original.id),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['channels'] });
          toast.success('Channel deactivated');
        },
      });

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
            <DropdownMenuItem>
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {row.original.is_active ? (
              <DropdownMenuItem
                onClick={() => deactivateMutation.mutate()}
                className="text-destructive focus:text-destructive"
              >
                <PowerOff className="mr-2 h-4 w-4" />
                Deactivate
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onClick={() => activateMutation.mutate()}>
                <Power className="mr-2 h-4 w-4" />
                Activate
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

export default function ChannelsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newChannel, setNewChannel] = useState<{
    name: string;
    code: string;
    channel_type: 'D2C' | 'MARKETPLACE' | 'B2B' | 'DEALER' | 'OFFLINE';
    marketplace_name: string;
    commission_rate: string;
    auto_sync_orders: boolean;
    auto_sync_inventory: boolean;
    description: string;
  }>({
    name: '',
    code: '',
    channel_type: 'D2C',
    marketplace_name: '',
    commission_rate: '',
    auto_sync_orders: true,
    auto_sync_inventory: true,
    description: '',
  });

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['channels', page, pageSize],
    queryFn: () => channelsApi.list({ page: page + 1, size: pageSize }),
  });

  const { data: stats } = useQuery({
    queryKey: ['channel-stats'],
    queryFn: channelsApi.getStats,
  });

  const createMutation = useMutation({
    mutationFn: channelsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      toast.success('Channel created successfully');
      setIsDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create channel');
    },
  });

  const handleCreate = () => {
    if (!newChannel.name.trim()) {
      toast.error('Channel name is required');
      return;
    }
    createMutation.mutate({
      ...newChannel,
      commission_rate: parseFloat(newChannel.commission_rate) || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sales Channels"
        description="Manage D2C, marketplace, and B2B sales channels"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Channel
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Create Sales Channel</DialogTitle>
                <DialogDescription>
                  Add a new sales channel for order and inventory management.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Channel Name *</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Amazon India"
                      value={newChannel.name}
                      onChange={(e) => setNewChannel({ ...newChannel, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="code">Code</Label>
                    <Input
                      id="code"
                      placeholder="AMAZON_IN"
                      value={newChannel.code}
                      onChange={(e) => setNewChannel({ ...newChannel, code: e.target.value.toUpperCase() })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="type">Channel Type</Label>
                    <Select
                      value={newChannel.channel_type}
                      onValueChange={(value: 'D2C' | 'MARKETPLACE' | 'B2B' | 'DEALER' | 'OFFLINE') =>
                        setNewChannel({ ...newChannel, channel_type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="D2C">D2C (Direct to Consumer)</SelectItem>
                        <SelectItem value="MARKETPLACE">Marketplace</SelectItem>
                        <SelectItem value="B2B">B2B / GTMT</SelectItem>
                        <SelectItem value="DEALER">Dealer Portal</SelectItem>
                        <SelectItem value="OFFLINE">Offline / Retail</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {newChannel.channel_type === 'MARKETPLACE' && (
                    <div className="space-y-2">
                      <Label htmlFor="marketplace">Marketplace</Label>
                      <Select
                        value={newChannel.marketplace_name}
                        onValueChange={(value) => setNewChannel({ ...newChannel, marketplace_name: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select marketplace" />
                        </SelectTrigger>
                        <SelectContent>
                          {marketplaces.map((mp) => (
                            <SelectItem key={mp} value={mp}>{mp}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="commission">Commission Rate (%)</Label>
                  <Input
                    id="commission"
                    type="number"
                    step="0.1"
                    placeholder="e.g., 15"
                    value={newChannel.commission_rate}
                    onChange={(e) => setNewChannel({ ...newChannel, commission_rate: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Channel description..."
                    value={newChannel.description}
                    onChange={(e) => setNewChannel({ ...newChannel, description: e.target.value })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="sync_orders"
                      checked={newChannel.auto_sync_orders}
                      onCheckedChange={(checked) => setNewChannel({ ...newChannel, auto_sync_orders: checked })}
                    />
                    <Label htmlFor="sync_orders">Auto-sync Orders</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="sync_inventory"
                      checked={newChannel.auto_sync_inventory}
                      onCheckedChange={(checked) => setNewChannel({ ...newChannel, auto_sync_inventory: checked })}
                    />
                    <Label htmlFor="sync_inventory">Auto-sync Inventory</Label>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Channel'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Channels</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_channels || 0}</div>
            <p className="text-xs text-muted-foreground">{stats?.active_channels || 0} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Channels</CardTitle>
            <Power className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.active_channels || 0}</div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Orders Today</CardTitle>
            <ShoppingBag className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_orders_today || 0}</div>
            <p className="text-xs text-muted-foreground">Across all channels</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue Today</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats?.total_revenue_today || 0)}</div>
            <p className="text-xs text-muted-foreground">All channels combined</p>
          </CardContent>
        </Card>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search channels..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </div>
  );
}
