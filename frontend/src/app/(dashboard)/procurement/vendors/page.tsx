'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, Building, Phone, Mail, Lock } from 'lucide-react';
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
import { vendorsApi } from '@/lib/api';
import { Vendor } from '@/types';

const tierColors: Record<string, string> = {
  PLATINUM: 'bg-purple-100 text-purple-800',
  GOLD: 'bg-yellow-100 text-yellow-800',
  SILVER: 'bg-gray-100 text-gray-800',
  BRONZE: 'bg-orange-100 text-orange-800',
};

const columns: ColumnDef<Vendor>[] = [
  {
    accessorKey: 'name',
    header: 'Vendor',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Building className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <div className="font-medium">{row.original.name}</div>
          <div className="text-sm text-muted-foreground">{row.original.code}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'contact',
    header: 'Contact',
    cell: ({ row }) => (
      <div className="space-y-1">
        {row.original.email && (
          <div className="flex items-center gap-1 text-sm">
            <Mail className="h-3 w-3 text-muted-foreground" />
            {row.original.email}
          </div>
        )}
        {row.original.phone && (
          <div className="flex items-center gap-1 text-sm">
            <Phone className="h-3 w-3 text-muted-foreground" />
            {row.original.phone}
          </div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'gst_number',
    header: 'GST Number',
    cell: ({ row }) => (
      <span className="font-mono text-sm">{row.original.gst_number || '-'}</span>
    ),
  },
  {
    accessorKey: 'tier',
    header: 'Tier',
    cell: ({ row }) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${tierColors[row.original.tier] || 'bg-gray-100'}`}>
        {row.original.tier}
      </span>
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
            <Pencil className="mr-2 h-4 w-4" />
            Edit
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

export default function VendorsPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [newVendor, setNewVendor] = useState<{
    name: string;
    code: string;
    email: string;
    phone: string;
    gst_number: string;
    pan_number: string;
    tier: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
    vendor_type: 'MANUFACTURER' | 'DISTRIBUTOR' | 'SPARE_PARTS' | 'SERVICE_PROVIDER' | 'RAW_MATERIAL' | 'TRANSPORTER';
    contact_person: string;
    address_line1: string;
    city: string;
    state: string;
    pincode: string;
  }>({
    name: '',
    code: '',
    email: '',
    phone: '',
    gst_number: '',
    pan_number: '',
    tier: 'SILVER',
    vendor_type: 'MANUFACTURER',
    contact_person: '',
    address_line1: '',
    city: '',
    state: '',
    pincode: '',
  });

  const queryClient = useQueryClient();

  // Fetch next vendor code when dialog opens or vendor type changes
  const fetchNextCode = async (vendorType: string) => {
    setIsLoadingCode(true);
    try {
      const result = await vendorsApi.getNextCode(vendorType);
      setNewVendor(prev => ({ ...prev, code: result.next_code }));
    } catch (error) {
      console.error('Failed to fetch next vendor code:', error);
    } finally {
      setIsLoadingCode(false);
    }
  };

  // Fetch code when dialog opens
  useEffect(() => {
    if (isDialogOpen) {
      fetchNextCode(newVendor.vendor_type);
    }
  }, [isDialogOpen]);

  // Update code when vendor type changes
  const handleVendorTypeChange = (value: typeof newVendor.vendor_type) => {
    setNewVendor(prev => ({ ...prev, vendor_type: value }));
    fetchNextCode(value);
  };

  const { data, isLoading } = useQuery({
    queryKey: ['vendors', page, pageSize],
    queryFn: () => vendorsApi.list({ page: page + 1, size: pageSize }),
  });

  const createMutation = useMutation({
    mutationFn: vendorsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      toast.success('Vendor created successfully');
      setIsDialogOpen(false);
      setNewVendor({
        name: '',
        code: '',
        email: '',
        phone: '',
        gst_number: '',
        pan_number: '',
        tier: 'SILVER',
        vendor_type: 'MANUFACTURER',
        contact_person: '',
        address_line1: '',
        city: '',
        state: '',
        pincode: '',
      });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create vendor');
    },
  });

  const handleCreate = () => {
    if (!newVendor.name.trim()) {
      toast.error('Vendor name is required');
      return;
    }
    if (!newVendor.address_line1.trim()) {
      toast.error('Address is required');
      return;
    }
    if (!newVendor.city.trim() || !newVendor.state.trim() || !newVendor.pincode.trim()) {
      toast.error('City, State and Pincode are required');
      return;
    }
    createMutation.mutate(newVendor);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vendors"
        description="Manage suppliers and vendor relationships"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Vendor
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Vendor</DialogTitle>
                <DialogDescription>
                  Add a new vendor to your supplier network.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {/* Basic Information */}
                <div className="text-sm font-medium text-muted-foreground">Basic Information</div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      placeholder="Vendor name"
                      value={newVendor.name}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, name: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="code">Code (Auto-generated)</Label>
                    <div className="relative">
                      <Input
                        id="code"
                        placeholder={isLoadingCode ? "Loading..." : "VND-MFR-00001"}
                        value={newVendor.code}
                        readOnly
                        disabled
                        className="bg-muted pr-8 font-mono"
                      />
                      <Lock className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="vendor_type">Vendor Type *</Label>
                    <Select
                      value={newVendor.vendor_type}
                      onValueChange={handleVendorTypeChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="MANUFACTURER">Manufacturer (MFR)</SelectItem>
                        <SelectItem value="SPARE_PARTS">Spare Parts (SPR)</SelectItem>
                        <SelectItem value="DISTRIBUTOR">Distributor (DST)</SelectItem>
                        <SelectItem value="RAW_MATERIAL">Raw Material (RAW)</SelectItem>
                        <SelectItem value="SERVICE_PROVIDER">Service Provider (SVC)</SelectItem>
                        <SelectItem value="TRANSPORTER">Transporter (TRN)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tier">Tier</Label>
                    <Select
                      value={newVendor.tier}
                      onValueChange={(value: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE') =>
                        setNewVendor({ ...newVendor, tier: value })
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

                {/* Contact Information */}
                <div className="text-sm font-medium text-muted-foreground mt-2">Contact Information</div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="contact_person">Contact Person</Label>
                    <Input
                      id="contact_person"
                      placeholder="Contact person name"
                      value={newVendor.contact_person}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, contact_person: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="vendor@example.com"
                      value={newVendor.email}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, email: e.target.value })
                      }
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    placeholder="+91 9876543210"
                    value={newVendor.phone}
                    onChange={(e) =>
                      setNewVendor({ ...newVendor, phone: e.target.value })
                    }
                  />
                </div>

                {/* Tax Information */}
                <div className="text-sm font-medium text-muted-foreground mt-2">Tax Information</div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="gst_number">GSTIN (15 characters)</Label>
                    <Input
                      id="gst_number"
                      placeholder="22AAAAA0000A1Z5"
                      maxLength={15}
                      value={newVendor.gst_number}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, gst_number: e.target.value.toUpperCase() })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pan_number">PAN (10 characters)</Label>
                    <Input
                      id="pan_number"
                      placeholder="AAAAA0000A"
                      maxLength={10}
                      value={newVendor.pan_number}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, pan_number: e.target.value.toUpperCase() })
                      }
                    />
                  </div>
                </div>

                {/* Address Information */}
                <div className="text-sm font-medium text-muted-foreground mt-2">Address Information</div>
                <div className="space-y-2">
                  <Label htmlFor="address_line1">Address *</Label>
                  <Input
                    id="address_line1"
                    placeholder="Street address"
                    value={newVendor.address_line1}
                    onChange={(e) =>
                      setNewVendor({ ...newVendor, address_line1: e.target.value })
                    }
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="city">City *</Label>
                    <Input
                      id="city"
                      placeholder="City"
                      value={newVendor.city}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, city: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state">State *</Label>
                    <Input
                      id="state"
                      placeholder="State"
                      value={newVendor.state}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, state: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pincode">Pincode *</Label>
                    <Input
                      id="pincode"
                      placeholder="110001"
                      maxLength={6}
                      value={newVendor.pincode}
                      onChange={(e) =>
                        setNewVendor({ ...newVendor, pincode: e.target.value })
                      }
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Vendor'}
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
        searchPlaceholder="Search vendors..."
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
