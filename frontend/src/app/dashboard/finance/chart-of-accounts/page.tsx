'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, ChevronRight, FileSpreadsheet, Loader2 } from 'lucide-react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { accountsApi } from '@/lib/api';

interface Account {
  id: string;
  code: string;
  name: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  parent_id?: string;
  parent?: { name: string; code: string };
  description?: string;
  is_active: boolean;
  is_group: boolean;
  balance: number;
  created_at: string;
}

const accountTypes = [
  { label: 'Asset', value: 'ASSET' },
  { label: 'Liability', value: 'LIABILITY' },
  { label: 'Equity', value: 'EQUITY' },
  { label: 'Revenue', value: 'REVENUE' },
  { label: 'Expense', value: 'EXPENSE' },
];

const typeColors: Record<string, string> = {
  ASSET: 'bg-blue-100 text-blue-800',
  LIABILITY: 'bg-red-100 text-red-800',
  EQUITY: 'bg-purple-100 text-purple-800',
  REVENUE: 'bg-green-100 text-green-800',
  EXPENSE: 'bg-orange-100 text-orange-800',
};

export default function ChartOfAccountsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    code: '',
    name: '',
    type: 'ASSET',
    parent_id: '',
    description: '',
    is_group: false,
    is_active: true,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['accounts', page, pageSize],
    queryFn: () => accountsApi.list({ page: page + 1, size: pageSize }),
  });

  const createMutation = useMutation({
    mutationFn: accountsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Account created successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create account'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof accountsApi.update>[1] }) =>
      accountsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Account updated successfully');
      resetForm();
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to update account'),
  });

  const resetForm = () => {
    setFormData({
      id: '',
      code: '',
      name: '',
      type: 'ASSET',
      parent_id: '',
      description: '',
      is_group: false,
      is_active: true,
    });
    setIsEditMode(false);
    setIsDialogOpen(false);
  };

  const handleEdit = (account: Account) => {
    setFormData({
      id: account.id,
      code: account.code,
      name: account.name,
      type: account.type,
      parent_id: account.parent_id || '',
      description: account.description || '',
      is_group: account.is_group,
      is_active: account.is_active,
    });
    setIsEditMode(true);
    setIsDialogOpen(true);
  };

  const handleSubmit = () => {
    if (!formData.code.trim() || !formData.name.trim() || !formData.type) {
      toast.error('Code, name, and type are required');
      return;
    }

    if (isEditMode) {
      updateMutation.mutate({
        id: formData.id,
        data: {
          name: formData.name,
          description: formData.description || undefined,
          is_active: formData.is_active,
        },
      });
    } else {
      createMutation.mutate({
        code: formData.code.toUpperCase(),
        name: formData.name,
        type: formData.type,
        parent_id: formData.parent_id || undefined,
        description: formData.description || undefined,
        is_group: formData.is_group,
      });
    }
  };

  const columns: ColumnDef<Account>[] = [
    {
      accessorKey: 'code',
      header: 'Code',
      cell: ({ row }) => (
        <span className="font-mono text-sm">{row.original.code}</span>
      ),
    },
    {
      accessorKey: 'name',
      header: 'Account Name',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          {row.original.is_group && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
          <span className={row.original.is_group ? 'font-medium' : ''}>
            {row.original.name}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'type',
      header: 'Type',
      cell: ({ row }) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeColors[row.original.type]}`}>
          {row.original.type}
        </span>
      ),
    },
    {
      accessorKey: 'parent',
      header: 'Parent',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {row.original.parent?.name || '-'}
        </span>
      ),
    },
    {
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ row }) => (
        <span className={`font-medium ${row.original.balance < 0 ? 'text-red-600' : ''}`}>
          ₹{Math.abs(row.original.balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          {row.original.balance !== 0 && (
            <span className="text-xs ml-1">{row.original.balance < 0 ? 'Cr' : 'Dr'}</span>
          )}
        </span>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />
      ),
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
            <DropdownMenuItem onClick={() => handleEdit(row.original)}>
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  // Get parent accounts (groups only) for dropdown
  const parentAccounts = data?.items?.filter((a: Account) => a.is_group) ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Chart of Accounts"
        description="Manage accounting structure and ledger accounts"
        actions={
          <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) resetForm(); else setIsDialogOpen(true); }}>
            <DialogTrigger asChild>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Account
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{isEditMode ? 'Edit Account' : 'Add New Account'}</DialogTitle>
                <DialogDescription>
                  {isEditMode ? 'Update account details' : 'Create a new ledger account'}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Code *</Label>
                    <Input
                      placeholder="1001"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                      disabled={isEditMode}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Type *</Label>
                    <Select
                      value={formData.type}
                      onValueChange={(value) => setFormData({ ...formData, type: value })}
                      disabled={isEditMode}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {accountTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Name *</Label>
                  <Input
                    placeholder="Cash in Hand"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Parent Account</Label>
                  <Select
                    value={formData.parent_id || 'none'}
                    onValueChange={(value) => setFormData({ ...formData, parent_id: value === 'none' ? '' : value })}
                    disabled={isEditMode}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select parent (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Parent (Top Level)</SelectItem>
                      {parentAccounts
                        .filter((acc: Account) => acc.id && acc.id.trim() !== '')
                        .map((acc: Account) => (
                          <SelectItem key={acc.id} value={acc.id}>
                            {acc.code} - {acc.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    placeholder="Account description (optional)"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_group"
                      checked={formData.is_group}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_group: checked })}
                      disabled={isEditMode}
                    />
                    <Label htmlFor="is_group">Group Account</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_active"
                      checked={formData.is_active}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                    />
                    <Label htmlFor="is_active">Active</Label>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={resetForm}>Cancel</Button>
                <Button
                  onClick={handleSubmit}
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {(createMutation.isPending || updateMutation.isPending) && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  {isEditMode ? 'Update' : 'Create'}
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
        searchPlaceholder="Search accounts..."
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
