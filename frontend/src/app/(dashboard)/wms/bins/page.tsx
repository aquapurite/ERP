'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, Grid3X3, Package, Eye, Lock, Unlock } from 'lucide-react';
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

interface Bin {
  id: string;
  zone_id: string;
  zone?: { id: string; zone_code: string; zone_name: string };
  warehouse_id?: string;
  warehouse?: { id: string; name: string };
  bin_code: string;
  aisle?: string;
  rack?: string;
  shelf?: string;
  position?: string;
  bin_type: 'SHELF' | 'PALLET' | 'FLOOR' | 'RACK' | 'BULK';
  max_weight_kg?: number;
  max_capacity?: number;
  current_items: number;
  current_weight_kg?: number;
  is_reserved: boolean;
  is_pickable: boolean;
  is_receivable: boolean;
  is_active: boolean;
}

interface Zone {
  id: string;
  zone_code: string;
  zone_name: string;
  zone_type: string;
}

interface BinStats {
  total_bins: number;
  available_bins: number;
  occupied_bins: number;
  reserved_bins: number;
}

const binsApi = {
  list: async (params?: { page?: number; size?: number; zone_id?: string; bin_type?: string }) => {
    try {
      const { data } = await apiClient.get('/wms/bins', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<BinStats> => {
    try {
      const { data } = await apiClient.get('/wms/bins/stats');
      return data;
    } catch {
      return { total_bins: 0, available_bins: 0, occupied_bins: 0, reserved_bins: 0 };
    }
  },
  create: async (bin: Partial<Bin>) => {
    const { data } = await apiClient.post('/wms/bins', bin);
    return data;
  },
  update: async (id: string, data: Partial<Bin>) => {
    const { data: result } = await apiClient.put(`/wms/bins/${id}`, data);
    return result;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/wms/bins/${id}`);
  },
};

const zonesApi = {
  dropdown: async (): Promise<Zone[]> => {
    try {
      const { data } = await apiClient.get('/wms/zones/dropdown');
      return data;
    } catch {
      return [];
    }
  },
};

// Separate component for actions cell to properly use hooks
function BinActionsCell({ bin }: { bin: Bin }) {
  const queryClient = useQueryClient();

  const reserveMutation = useMutation({
    mutationFn: () => binsApi.update(bin.id, { is_reserved: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wms-bins'] });
      toast.success('Bin reserved');
    },
    onError: () => toast.error('Failed to reserve bin'),
  });

  const unreserveMutation = useMutation({
    mutationFn: () => binsApi.update(bin.id, { is_reserved: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wms-bins'] });
      toast.success('Bin unreserved');
    },
    onError: () => toast.error('Failed to unreserve bin'),
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
          View Contents
        </DropdownMenuItem>
        <DropdownMenuItem>
          <Pencil className="mr-2 h-4 w-4" />
          Edit
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {bin.is_reserved ? (
          <DropdownMenuItem onClick={() => unreserveMutation.mutate()}>
            <Unlock className="mr-2 h-4 w-4" />
            Unreserve Bin
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem onClick={() => reserveMutation.mutate()}>
            <Lock className="mr-2 h-4 w-4" />
            Reserve Bin
          </DropdownMenuItem>
        )}
        <DropdownMenuItem className="text-destructive focus:text-destructive">
          <Trash2 className="mr-2 h-4 w-4" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

const binTypeColors: Record<string, string> = {
  SHELF: 'bg-blue-100 text-blue-800',
  PALLET: 'bg-purple-100 text-purple-800',
  FLOOR: 'bg-green-100 text-green-800',
  RACK: 'bg-orange-100 text-orange-800',
  BULK: 'bg-cyan-100 text-cyan-800',
};

const binTypes = [
  { label: 'Shelf', value: 'SHELF' },
  { label: 'Pallet', value: 'PALLET' },
  { label: 'Floor', value: 'FLOOR' },
  { label: 'Rack', value: 'RACK' },
  { label: 'Bulk', value: 'BULK' },
];

const columns: ColumnDef<Bin>[] = [
  {
    accessorKey: 'bin_code',
    header: 'Bin Location',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Grid3X3 className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-mono font-medium">{row.original.bin_code}</div>
          <div className="text-xs text-muted-foreground">
            {row.original.aisle && `Aisle ${row.original.aisle}`}
            {row.original.rack && `, Rack ${row.original.rack}`}
            {row.original.shelf && `, Shelf ${row.original.shelf}`}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'zone',
    header: 'Zone / Warehouse',
    cell: ({ row }) => (
      <div>
        <div className="text-sm font-medium">{row.original.zone?.zone_name || '-'}</div>
        <div className="text-xs text-muted-foreground">{row.original.warehouse?.name || '-'}</div>
      </div>
    ),
  },
  {
    accessorKey: 'bin_type',
    header: 'Type',
    cell: ({ row }) => {
      const binType = row.original.bin_type || 'STANDARD';
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${binTypeColors[binType] || 'bg-gray-100 text-gray-800'}`}>
          {binType.replace('_', ' ')}
        </span>
      );
    },
  },
  {
    accessorKey: 'current_items',
    header: 'Items',
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Package className="h-4 w-4 text-muted-foreground" />
        <span className="font-mono text-sm">{row.original.current_items}</span>
      </div>
    ),
  },
  {
    accessorKey: 'capacity',
    header: 'Capacity',
    cell: ({ row }) => {
      const currentItems = row.original.current_items ?? 0;
      const maxCapacity = row.original.max_capacity ?? 0;
      const utilization = maxCapacity > 0 ? (currentItems / maxCapacity) * 100 : 0;
      return (
        <div className="space-y-1">
          <div className="text-sm">
            {currentItems} / {maxCapacity || '∞'} items
          </div>
          {maxCapacity > 0 && (
            <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full ${utilization > 90 ? 'bg-red-500' : utilization > 70 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${Math.min(utilization, 100)}%` }}
              />
            </div>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: 'is_reserved',
    header: 'Status',
    cell: ({ row }) => (
      <div className={`inline-flex items-center gap-1.5 text-xs font-medium ${
        row.original.is_reserved ? 'text-orange-600' : 'text-green-600'
      }`}>
        {row.original.is_reserved ? (
          <>
            <Lock className="h-3 w-3" />
            Reserved
          </>
        ) : (
          <>
            <Unlock className="h-3 w-3" />
            Available
          </>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'is_active',
    header: 'Status',
    cell: ({ row }) => <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />,
  },
  {
    id: 'actions',
    cell: ({ row }) => <BinActionsCell bin={row.original} />,
  },
];

export default function BinsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [zoneFilter, setZoneFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [newBin, setNewBin] = useState<{
    zone_id: string;
    bin_code: string;
    aisle: string;
    rack: string;
    shelf: string;
    bin_type: 'SHELF' | 'PALLET' | 'FLOOR' | 'RACK' | 'BULK';
    max_capacity: string;
    max_weight_kg: string;
    is_active: boolean;
  }>({
    zone_id: '',
    bin_code: '',
    aisle: '',
    rack: '',
    shelf: '',
    bin_type: 'SHELF',
    max_capacity: '',
    max_weight_kg: '',
    is_active: true,
  });

  const queryClient = useQueryClient();

  // Fetch zones for dropdown
  const { data: zones = [] } = useQuery({
    queryKey: ['wms-zones-dropdown'],
    queryFn: zonesApi.dropdown,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['wms-bins', page, pageSize, zoneFilter, typeFilter],
    queryFn: () => binsApi.list({
      page: page + 1,
      size: pageSize,
      zone_id: zoneFilter !== 'all' ? zoneFilter : undefined,
      bin_type: typeFilter !== 'all' ? typeFilter : undefined,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['wms-bins-stats'],
    queryFn: binsApi.getStats,
  });

  const createMutation = useMutation({
    mutationFn: binsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wms-bins'] });
      toast.success('Bin created successfully');
      setIsDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create bin');
    },
  });

  const handleCreate = () => {
    if (!newBin.bin_code.trim()) {
      toast.error('Bin code is required');
      return;
    }
    createMutation.mutate({
      zone_id: newBin.zone_id || undefined,
      bin_code: newBin.bin_code,
      aisle: newBin.aisle || undefined,
      rack: newBin.rack || undefined,
      shelf: newBin.shelf || undefined,
      bin_type: newBin.bin_type,
      max_capacity: parseInt(newBin.max_capacity) || undefined,
      max_weight_kg: parseFloat(newBin.max_weight_kg) || undefined,
      is_active: newBin.is_active,
    } as any);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Warehouse Bins"
        description="Manage bin locations for precise inventory placement"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Bin
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Create New Bin</DialogTitle>
                <DialogDescription>
                  Add a new bin location within a zone.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="zone">Zone</Label>
                    <Select
                      value={newBin.zone_id || 'none'}
                      onValueChange={(value) => setNewBin({ ...newBin, zone_id: value === 'none' ? '' : value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select zone" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Zone</SelectItem>
                        {zones.map((zone) => (
                          <SelectItem key={zone.id} value={zone.id}>
                            {zone.zone_name} ({zone.zone_code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bin_code">Bin Code *</Label>
                    <Input
                      id="bin_code"
                      placeholder="A-01-01-01"
                      value={newBin.bin_code}
                      onChange={(e) => setNewBin({ ...newBin, bin_code: e.target.value.toUpperCase() })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="aisle">Aisle</Label>
                    <Input
                      id="aisle"
                      placeholder="A"
                      value={newBin.aisle}
                      onChange={(e) => setNewBin({ ...newBin, aisle: e.target.value.toUpperCase() })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="rack">Rack</Label>
                    <Input
                      id="rack"
                      placeholder="01"
                      value={newBin.rack}
                      onChange={(e) => setNewBin({ ...newBin, rack: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shelf">Shelf</Label>
                    <Input
                      id="shelf"
                      placeholder="01"
                      value={newBin.shelf}
                      onChange={(e) => setNewBin({ ...newBin, shelf: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Bin Type</Label>
                  <Select
                    value={newBin.bin_type}
                    onValueChange={(value: 'SHELF' | 'PALLET' | 'FLOOR' | 'RACK' | 'BULK') =>
                      setNewBin({ ...newBin, bin_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {binTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="max_capacity">Max Capacity (items)</Label>
                    <Input
                      id="max_capacity"
                      type="number"
                      placeholder="100"
                      value={newBin.max_capacity}
                      onChange={(e) => setNewBin({ ...newBin, max_capacity: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_weight_kg">Max Weight (kg)</Label>
                    <Input
                      id="max_weight_kg"
                      type="number"
                      placeholder="100"
                      step="0.1"
                      value={newBin.max_weight_kg}
                      onChange={(e) => setNewBin({ ...newBin, max_weight_kg: e.target.value })}
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="is_active"
                    checked={newBin.is_active}
                    onCheckedChange={(checked) => setNewBin({ ...newBin, is_active: checked })}
                  />
                  <Label htmlFor="is_active">Active</Label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Bin'}
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
            <CardTitle className="text-sm font-medium">Total Bins</CardTitle>
            <Grid3X3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_bins || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available</CardTitle>
            <Unlock className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.available_bins || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Occupied</CardTitle>
            <Package className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.occupied_bins || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reserved</CardTitle>
            <Lock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.reserved_bins || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={zoneFilter} onValueChange={setZoneFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by zone" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Zones</SelectItem>
            {zones.map((zone) => (
              <SelectItem key={zone.id} value={zone.id}>
                {zone.zone_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {binTypes.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="bin_code"
        searchPlaceholder="Search bins..."
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
