'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Eye, Store, CreditCard, Target, Gift, MapPin } from 'lucide-react';
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
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { dealersApi } from '@/lib/api';
import { Dealer } from '@/types';
import { formatCurrency } from '@/lib/utils';

const tierColors: Record<string, string> = {
  PLATINUM: 'bg-purple-100 text-purple-800',
  GOLD: 'bg-yellow-100 text-yellow-800',
  SILVER: 'bg-gray-100 text-gray-800',
  BRONZE: 'bg-orange-100 text-orange-800',
};

const getColumns = (
  router: ReturnType<typeof useRouter>,
  onEdit: (dealer: Dealer) => void
): ColumnDef<Dealer>[] => [
  {
    accessorKey: 'name',
    header: 'Dealer',
    cell: ({ row }) => (
      <div
        className="flex items-center gap-3 cursor-pointer hover:opacity-80"
        onClick={() => router.push(`/distribution/dealers/${row.original.id}`)}
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Store className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => (
      <span className="text-sm capitalize">
        {row.original.type.replace(/_/g, ' ').toLowerCase()}
      </span>
    ),
  },
  {
    accessorKey: 'pricing_tier',
    header: 'Tier',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${tierColors[row.original.pricing_tier]}`}>
        {row.original.pricing_tier}
      </span>
    ),
  },
  {
    accessorKey: 'credit',
    header: 'Credit',
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <CreditCard className="h-4 w-4 text-muted-foreground" />
        <div className="text-sm">
          <div className="font-medium">{formatCurrency(row.original.available_credit)}</div>
          <div className="text-muted-foreground text-xs">
            of {formatCurrency(row.original.credit_limit)}
          </div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'contact',
    header: 'Contact',
    cell: ({ row }) => (
      <div className="text-sm">
        <div>{row.original.email || '-'}</div>
        <div className="text-muted-foreground">{row.original.phone || '-'}</div>
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
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Actions</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => router.push(`/distribution/dealers/${row.original.id}`)}>
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push(`/distribution/dealers/${row.original.id}?tab=territory`)}>
            <MapPin className="mr-2 h-4 w-4" />
            Manage Territory
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push(`/distribution/dealers/${row.original.id}?tab=credit`)}>
            <CreditCard className="mr-2 h-4 w-4" />
            Credit Ledger
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push(`/distribution/dealers/${row.original.id}?tab=targets`)}>
            <Target className="mr-2 h-4 w-4" />
            Targets
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => onEdit(row.original)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

type DealerFormData = {
  name: string;
  code: string;
  type: 'DISTRIBUTOR' | 'DEALER' | 'SUB_DEALER' | 'FRANCHISE' | 'RETAILER' | 'CORPORATE';
  email: string;
  phone: string;
  gst_number: string;
  pricing_tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  credit_limit: string;
};

const initialFormData: DealerFormData = {
  name: '',
  code: '',
  type: 'DEALER',
  email: '',
  phone: '',
  gst_number: '',
  pricing_tier: 'SILVER',
  credit_limit: '',
};

export default function DealersPage() {
  const router = useRouter();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedDealer, setSelectedDealer] = useState<Dealer | null>(null);
  const [formData, setFormData] = useState<DealerFormData>(initialFormData);

  const queryClient = useQueryClient();

  // Handle Edit
  const handleEdit = (dealer: Dealer) => {
    setSelectedDealer(dealer);
    setFormData({
      name: dealer.name,
      code: dealer.code || '',
      type: dealer.type,
      email: dealer.email || '',
      phone: dealer.phone || '',
      gst_number: dealer.gst_number || '',
      pricing_tier: dealer.pricing_tier,
      credit_limit: String(dealer.credit_limit || 0),
    });
    setIsDialogOpen(true);
  };

  // Handle Add New
  const handleAddNew = () => {
    setSelectedDealer(null);
    setFormData(initialFormData);
    setIsDialogOpen(true);
  };

  const { data, isLoading } = useQuery({
    queryKey: ['dealers', page, pageSize],
    queryFn: () => dealersApi.list({ page: page + 1, size: pageSize }),
  });

  const createMutation = useMutation({
    mutationFn: dealersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dealers'] });
      toast.success('Dealer created successfully');
      setIsDialogOpen(false);
      setSelectedDealer(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create dealer');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Dealer> }) =>
      dealersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dealers'] });
      toast.success('Dealer updated successfully');
      setIsDialogOpen(false);
      setSelectedDealer(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update dealer');
    },
  });

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      toast.error('Dealer name is required');
      return;
    }

    const dealerData = {
      ...formData,
      credit_limit: parseFloat(formData.credit_limit) || 0,
    };

    if (selectedDealer) {
      updateMutation.mutate({ id: selectedDealer.id, data: dealerData });
    } else {
      createMutation.mutate(dealerData);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dealers"
        description="Manage dealer network and distribution partners"
        actions={
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Dealer
          </Button>
        }
      />

      <DataTable
        columns={getColumns(router, handleEdit)}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search dealers..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Create/Edit Dealer Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedDealer ? 'Edit Dealer' : 'Create New Dealer'}
            </DialogTitle>
            <DialogDescription>
              {selectedDealer
                ? `Update information for ${selectedDealer.name}`
                : 'Add a new dealer to your distribution network.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="Dealer name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="code">Code</Label>
                <Input
                  id="code"
                  placeholder="DLR001"
                  value={formData.code}
                  onChange={(e) =>
                    setFormData({ ...formData, code: e.target.value.toUpperCase() })
                  }
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select
                  value={formData.type}
                  onValueChange={(value: DealerFormData['type']) =>
                    setFormData({ ...formData, type: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DISTRIBUTOR">Distributor</SelectItem>
                    <SelectItem value="DEALER">Dealer</SelectItem>
                    <SelectItem value="SUB_DEALER">Sub-Dealer</SelectItem>
                    <SelectItem value="FRANCHISE">Franchise</SelectItem>
                    <SelectItem value="RETAILER">Retailer</SelectItem>
                    <SelectItem value="CORPORATE">Corporate</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="tier">Pricing Tier</Label>
                <Select
                  value={formData.pricing_tier}
                  onValueChange={(value: DealerFormData['pricing_tier']) =>
                    setFormData({ ...formData, pricing_tier: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select tier" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PLATINUM">Platinum</SelectItem>
                    <SelectItem value="GOLD">Gold</SelectItem>
                    <SelectItem value="SILVER">Silver</SelectItem>
                    <SelectItem value="BRONZE">Bronze</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="dealer@example.com"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  placeholder="+91 98765 43210"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="gst_number">GST Number</Label>
                <Input
                  id="gst_number"
                  placeholder="22AAAAA0000A1Z5"
                  value={formData.gst_number}
                  onChange={(e) =>
                    setFormData({ ...formData, gst_number: e.target.value.toUpperCase() })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="credit_limit">Credit Limit</Label>
                <Input
                  id="credit_limit"
                  type="number"
                  placeholder="100000"
                  value={formData.credit_limit}
                  onChange={(e) =>
                    setFormData({ ...formData, credit_limit: e.target.value })
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
              {(createMutation.isPending || updateMutation.isPending)
                ? (selectedDealer ? 'Updating...' : 'Creating...')
                : (selectedDealer ? 'Update Dealer' : 'Create Dealer')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
