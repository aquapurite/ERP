'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Eye, Store, CreditCard } from 'lucide-react';
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

const columns: ColumnDef<Dealer>[] = [
  {
    accessorKey: 'name',
    header: 'Dealer',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
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
          <DropdownMenuItem>
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function DealersPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newDealer, setNewDealer] = useState<{
    name: string;
    code: string;
    type: 'DISTRIBUTOR' | 'DEALER' | 'SUB_DEALER' | 'FRANCHISE' | 'RETAILER' | 'CORPORATE';
    email: string;
    phone: string;
    gst_number: string;
    pricing_tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
    credit_limit: string;
  }>({
    name: '',
    code: '',
    type: 'DEALER',
    email: '',
    phone: '',
    gst_number: '',
    pricing_tier: 'SILVER',
    credit_limit: '',
  });

  const queryClient = useQueryClient();

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
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create dealer');
    },
  });

  const handleCreate = () => {
    if (!newDealer.name.trim()) {
      toast.error('Dealer name is required');
      return;
    }
    createMutation.mutate({
      ...newDealer,
      credit_limit: parseFloat(newDealer.credit_limit) || 0,
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dealers"
        description="Manage dealer network and distribution partners"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Dealer
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Dealer</DialogTitle>
                <DialogDescription>
                  Add a new dealer to your distribution network.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      placeholder="Dealer name"
                      value={newDealer.name}
                      onChange={(e) =>
                        setNewDealer({ ...newDealer, name: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="code">Code</Label>
                    <Input
                      id="code"
                      placeholder="DLR001"
                      value={newDealer.code}
                      onChange={(e) =>
                        setNewDealer({ ...newDealer, code: e.target.value.toUpperCase() })
                      }
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="type">Type</Label>
                    <Select
                      value={newDealer.type}
                      onValueChange={(value: 'DISTRIBUTOR' | 'DEALER' | 'SUB_DEALER' | 'FRANCHISE' | 'RETAILER' | 'CORPORATE') =>
                        setNewDealer({ ...newDealer, type: value })
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
                      value={newDealer.pricing_tier}
                      onValueChange={(value: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE') =>
                        setNewDealer({ ...newDealer, pricing_tier: value })
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
                <div className="space-y-2">
                  <Label htmlFor="credit_limit">Credit Limit</Label>
                  <Input
                    id="credit_limit"
                    type="number"
                    placeholder="100000"
                    value={newDealer.credit_limit}
                    onChange={(e) =>
                      setNewDealer({ ...newDealer, credit_limit: e.target.value })
                    }
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Dealer'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <DataTable
        columns={columns}
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
    </div>
  );
}
