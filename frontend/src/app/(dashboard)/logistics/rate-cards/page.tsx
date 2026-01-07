'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, Calculator, Truck, Clock, DollarSign, Star, Package } from 'lucide-react';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import apiClient from '@/lib/api/client';
import { formatCurrency } from '@/lib/utils';

interface RateCard {
  id: string;
  transporter_id: string;
  transporter_name: string;
  zone_from: string;
  zone_to: string;
  weight_slab_kg: string;
  base_rate: number;
  per_kg_rate: number;
  cod_charge: number;
  cod_percent: number;
  fuel_surcharge_percent: number;
  min_weight_kg: number;
  max_weight_kg: number;
  estimated_days: number;
  reliability_score: number;
  is_active: boolean;
}

interface RateCardStats {
  total_rate_cards: number;
  active_cards: number;
  transporters_count: number;
  avg_base_rate: number;
}

const rateCardsApi = {
  list: async (params?: { page?: number; size?: number; transporter_id?: string }) => {
    try {
      const { data } = await apiClient.get('/logistics/rate-cards', { params });
      return data;
    } catch {
      return { items: [], total: 0, pages: 0 };
    }
  },
  getStats: async (): Promise<RateCardStats> => {
    try {
      const { data } = await apiClient.get('/logistics/rate-cards/stats');
      return data;
    } catch {
      return { total_rate_cards: 0, active_cards: 0, transporters_count: 0, avg_base_rate: 0 };
    }
  },
  create: async (rateCard: Partial<RateCard>) => {
    const { data } = await apiClient.post('/logistics/rate-cards', rateCard);
    return data;
  },
  compareRates: async (params: { zone_from: string; zone_to: string; weight_kg: number; is_cod: boolean }) => {
    try {
      const { data } = await apiClient.get('/logistics/rate-cards/compare', { params });
      return data;
    } catch {
      return { rates: [] };
    }
  },
};

const columns: ColumnDef<RateCard>[] = [
  {
    accessorKey: 'transporter_name',
    header: 'Transporter',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Truck className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.transporter_name}</div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Star className="h-3 w-3 text-yellow-500" />
            {row.original.reliability_score.toFixed(1)}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'zones',
    header: 'Zones',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.zone_from} → {row.original.zone_to}</div>
      </div>
    ),
  },
  {
    accessorKey: 'weight_slab_kg',
    header: 'Weight Slab',
    cell: ({ row }) => (
      <div className="text-sm font-mono">
        {row.original.min_weight_kg} - {row.original.max_weight_kg} kg
      </div>
    ),
  },
  {
    accessorKey: 'base_rate',
    header: 'Base Rate',
    cell: ({ row }) => (
      <span className="font-mono font-medium">{formatCurrency(row.original.base_rate)}</span>
    ),
  },
  {
    accessorKey: 'per_kg_rate',
    header: 'Per Kg',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{formatCurrency(row.original.per_kg_rate)}/kg</span>
    ),
  },
  {
    accessorKey: 'cod_charges',
    header: 'COD Charges',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{formatCurrency(row.original.cod_charge)} flat</div>
        <div className="text-muted-foreground">+ {row.original.cod_percent}%</div>
      </div>
    ),
  },
  {
    accessorKey: 'fuel_surcharge_percent',
    header: 'Fuel Surcharge',
    cell: ({ row }) => (
      <span className="text-sm">{row.original.fuel_surcharge_percent}%</span>
    ),
  },
  {
    accessorKey: 'estimated_days',
    header: 'Delivery',
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">{row.original.estimated_days} days</span>
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
            <Pencil className="mr-2 h-4 w-4" />
            Edit Rate
          </DropdownMenuItem>
          <DropdownMenuItem className="text-destructive focus:text-destructive">
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function RateCardsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [transporterFilter, setTransporterFilter] = useState<string>('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isCompareDialogOpen, setIsCompareDialogOpen] = useState(false);
  const [compareParams, setCompareParams] = useState({
    zone_from: '',
    zone_to: '',
    weight_kg: '',
    is_cod: false,
  });

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['rate-cards', page, pageSize, transporterFilter],
    queryFn: () => rateCardsApi.list({
      page: page + 1,
      size: pageSize,
      transporter_id: transporterFilter !== 'all' ? transporterFilter : undefined,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['rate-cards-stats'],
    queryFn: rateCardsApi.getStats,
  });

  const { data: comparedRates, refetch: fetchComparedRates } = useQuery({
    queryKey: ['compared-rates', compareParams],
    queryFn: () => rateCardsApi.compareRates({
      zone_from: compareParams.zone_from,
      zone_to: compareParams.zone_to,
      weight_kg: parseFloat(compareParams.weight_kg) || 0,
      is_cod: compareParams.is_cod,
    }),
    enabled: false,
  });

  const handleCompare = () => {
    if (!compareParams.zone_from || !compareParams.zone_to || !compareParams.weight_kg) {
      toast.error('Please fill all required fields');
      return;
    }
    fetchComparedRates();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transporter Rate Cards"
        description="Manage and compare shipping rates across transporters"
        actions={
          <div className="flex gap-2">
            <Dialog open={isCompareDialogOpen} onOpenChange={setIsCompareDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Calculator className="mr-2 h-4 w-4" />
                  Compare Rates
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Compare Shipping Rates</DialogTitle>
                  <DialogDescription>
                    Compare rates across all transporters for a specific route and weight.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>From Zone</Label>
                      <Select
                        value={compareParams.zone_from}
                        onValueChange={(value) => setCompareParams({ ...compareParams, zone_from: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select zone" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NORTH">North</SelectItem>
                          <SelectItem value="SOUTH">South</SelectItem>
                          <SelectItem value="EAST">East</SelectItem>
                          <SelectItem value="WEST">West</SelectItem>
                          <SelectItem value="CENTRAL">Central</SelectItem>
                          <SelectItem value="METRO">Metro</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>To Zone</Label>
                      <Select
                        value={compareParams.zone_to}
                        onValueChange={(value) => setCompareParams({ ...compareParams, zone_to: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select zone" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NORTH">North</SelectItem>
                          <SelectItem value="SOUTH">South</SelectItem>
                          <SelectItem value="EAST">East</SelectItem>
                          <SelectItem value="WEST">West</SelectItem>
                          <SelectItem value="CENTRAL">Central</SelectItem>
                          <SelectItem value="METRO">Metro</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Weight (kg)</Label>
                      <Input
                        type="number"
                        placeholder="e.g., 2.5"
                        value={compareParams.weight_kg}
                        onChange={(e) => setCompareParams({ ...compareParams, weight_kg: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2 flex items-end">
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="is_cod"
                          checked={compareParams.is_cod}
                          onCheckedChange={(checked) => setCompareParams({ ...compareParams, is_cod: checked })}
                        />
                        <Label htmlFor="is_cod">COD Order</Label>
                      </div>
                    </div>
                  </div>
                  <Button onClick={handleCompare}>Compare Rates</Button>

                  {/* Comparison Results */}
                  {comparedRates?.rates?.length > 0 && (
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-muted">
                          <tr>
                            <th className="text-left p-3">Transporter</th>
                            <th className="text-right p-3">Rate</th>
                            <th className="text-right p-3">COD</th>
                            <th className="text-right p-3">Total</th>
                            <th className="text-center p-3">Days</th>
                            <th className="text-center p-3">Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {comparedRates.rates.map((rate: { transporter_name: string; base_amount: number; cod_amount: number; total_amount: number; estimated_days: number; reliability_score: number }, idx: number) => (
                            <tr key={idx} className={idx === 0 ? 'bg-green-50' : ''}>
                              <td className="p-3">
                                <div className="flex items-center gap-2">
                                  {idx === 0 && <span className="text-xs bg-green-500 text-white px-1 rounded">Best</span>}
                                  {rate.transporter_name}
                                </div>
                              </td>
                              <td className="text-right p-3 font-mono">{formatCurrency(rate.base_amount)}</td>
                              <td className="text-right p-3 font-mono">{formatCurrency(rate.cod_amount)}</td>
                              <td className="text-right p-3 font-mono font-bold">{formatCurrency(rate.total_amount)}</td>
                              <td className="text-center p-3">{rate.estimated_days}d</td>
                              <td className="text-center p-3">
                                <div className="flex items-center justify-center gap-1">
                                  <Star className="h-3 w-3 text-yellow-500" />
                                  {rate.reliability_score.toFixed(1)}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Rate Card
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Add Rate Card</DialogTitle>
                  <DialogDescription>
                    Create a new shipping rate card for a transporter.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label>Transporter</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select transporter" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="delhivery">Delhivery</SelectItem>
                        <SelectItem value="bluedart">BlueDart</SelectItem>
                        <SelectItem value="dtdc">DTDC</SelectItem>
                        <SelectItem value="xpressbees">Xpressbees</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>From Zone</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Zone" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NORTH">North</SelectItem>
                          <SelectItem value="SOUTH">South</SelectItem>
                          <SelectItem value="EAST">East</SelectItem>
                          <SelectItem value="WEST">West</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>To Zone</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Zone" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NORTH">North</SelectItem>
                          <SelectItem value="SOUTH">South</SelectItem>
                          <SelectItem value="EAST">East</SelectItem>
                          <SelectItem value="WEST">West</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Min Weight (kg)</Label>
                      <Input type="number" placeholder="0" />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Weight (kg)</Label>
                      <Input type="number" placeholder="0.5" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Base Rate</Label>
                      <Input type="number" placeholder="50" />
                    </div>
                    <div className="space-y-2">
                      <Label>Per Kg Rate</Label>
                      <Input type="number" placeholder="20" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>COD Flat Charge</Label>
                      <Input type="number" placeholder="30" />
                    </div>
                    <div className="space-y-2">
                      <Label>COD %</Label>
                      <Input type="number" placeholder="1.5" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Fuel Surcharge %</Label>
                      <Input type="number" placeholder="10" />
                    </div>
                    <div className="space-y-2">
                      <Label>Estimated Days</Label>
                      <Input type="number" placeholder="3" />
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                  <Button>Create Rate Card</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Rate Cards</CardTitle>
            <Calculator className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_rate_cards || 0}</div>
            <p className="text-xs text-muted-foreground">{stats?.active_cards || 0} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transporters</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.transporters_count || 0}</div>
            <p className="text-xs text-muted-foreground">Integrated</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Base Rate</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats?.avg_base_rate || 0)}</div>
            <p className="text-xs text-muted-foreground">Across all cards</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Coverage</CardTitle>
            <Package className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">99.5%</div>
            <p className="text-xs text-muted-foreground">Pincode coverage</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={transporterFilter} onValueChange={setTransporterFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Transporters" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Transporters</SelectItem>
            <SelectItem value="delhivery">Delhivery</SelectItem>
            <SelectItem value="bluedart">BlueDart</SelectItem>
            <SelectItem value="dtdc">DTDC</SelectItem>
            <SelectItem value="xpressbees">Xpressbees</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="transporter_name"
        searchPlaceholder="Search rate cards..."
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
