'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, Loader2, Warehouse } from 'lucide-react';
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
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { fulfillmentPartnersApi } from '@/lib/api';

interface FulfillmentPartner {
  id: string;
  code: string;
  name: string;
  provider_type: string;
  api_base_url?: string;
  api_key?: string;
  auth_config?: Record<string, string>;
  webhook_secret?: string;
  is_active: boolean;
  config?: Record<string, unknown>;
  warehouse_count: number;
  created_at: string;
  updated_at: string;
}

const providerTypes = [
  { label: '3PL Partner', value: '3PL' },
  { label: 'Self Managed', value: 'SELF_MANAGED' },
];

const defaultForm = {
  code: '',
  name: '',
  provider_type: 'SELF_MANAGED',
  api_base_url: '',
  api_key: '',
  webhook_secret: '',
  is_active: true,
  auth_email: '',
  auth_password: '',
  auth_company_id: '',
  auth_integration_profile_id: '',
};

export default function FulfillmentPartnersPage() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [partnerToDelete, setPartnerToDelete] = useState<FulfillmentPartner | null>(null);
  const [formData, setFormData] = useState(defaultForm);
  const [editingId, setEditingId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['fulfillment-partners'],
    queryFn: () => fulfillmentPartnersApi.list({ limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: (payload: Parameters<typeof fulfillmentPartnersApi.create>[0]) =>
      fulfillmentPartnersApi.create(payload),
    onSuccess: () => {
      toast.success('Fulfillment partner created');
      queryClient.invalidateQueries({ queryKey: ['fulfillment-partners'] });
      closeDialog();
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to create partner');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof fulfillmentPartnersApi.update>[1] }) =>
      fulfillmentPartnersApi.update(id, payload),
    onSuccess: () => {
      toast.success('Fulfillment partner updated');
      queryClient.invalidateQueries({ queryKey: ['fulfillment-partners'] });
      closeDialog();
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to update partner');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fulfillmentPartnersApi.delete(id),
    onSuccess: () => {
      toast.success('Fulfillment partner deleted');
      queryClient.invalidateQueries({ queryKey: ['fulfillment-partners'] });
      setDeleteDialogOpen(false);
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to delete partner');
    },
  });

  const closeDialog = () => {
    setIsDialogOpen(false);
    setIsEditMode(false);
    setEditingId(null);
    setFormData(defaultForm);
  };

  const openCreate = () => {
    setFormData(defaultForm);
    setIsEditMode(false);
    setEditingId(null);
    setIsDialogOpen(true);
  };

  const openEdit = (partner: FulfillmentPartner) => {
    const auth = partner.auth_config || {};
    setFormData({
      code: partner.code,
      name: partner.name,
      provider_type: partner.provider_type,
      api_base_url: partner.api_base_url || '',
      api_key: partner.api_key || '',
      webhook_secret: partner.webhook_secret || '',
      is_active: partner.is_active,
      auth_email: auth.email || '',
      auth_password: auth.password || '',
      auth_company_id: auth.company_id || '',
      auth_integration_profile_id: auth.integration_profile_id || '',
    });
    setIsEditMode(true);
    setEditingId(partner.id);
    setIsDialogOpen(true);
  };

  const handleSubmit = () => {
    const authConfig: Record<string, string> = {};
    if (formData.auth_email) authConfig.email = formData.auth_email;
    if (formData.auth_password) authConfig.password = formData.auth_password;
    if (formData.auth_company_id) authConfig.company_id = formData.auth_company_id;
    if (formData.auth_integration_profile_id) authConfig.integration_profile_id = formData.auth_integration_profile_id;

    const payload = {
      code: formData.code,
      name: formData.name,
      provider_type: formData.provider_type,
      api_base_url: formData.api_base_url || undefined,
      api_key: formData.api_key || undefined,
      auth_config: Object.keys(authConfig).length > 0 ? authConfig : undefined,
      webhook_secret: formData.webhook_secret || undefined,
      is_active: formData.is_active,
    };

    if (isEditMode && editingId) {
      updateMutation.mutate({ id: editingId, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const columns: ColumnDef<FulfillmentPartner>[] = [
    {
      accessorKey: 'code',
      header: 'Code',
      cell: ({ row }) => (
        <span className="font-mono font-semibold text-sm">{row.original.code}</span>
      ),
    },
    {
      accessorKey: 'name',
      header: 'Name',
    },
    {
      accessorKey: 'provider_type',
      header: 'Type',
      cell: ({ row }) => (
        <StatusBadge
          status={row.original.provider_type}
        />
      ),
    },
    {
      accessorKey: 'api_base_url',
      header: 'API URL',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground truncate max-w-[200px] block">
          {row.original.api_base_url || '-'}
        </span>
      ),
    },
    {
      accessorKey: 'warehouse_count',
      header: 'Warehouses',
      cell: ({ row }) => (
        <div className="flex items-center gap-1">
          <Warehouse className="h-3.5 w-3.5 text-muted-foreground" />
          <span>{row.original.warehouse_count}</span>
        </div>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge
          status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'}
        />
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => openEdit(row.original)}>
              <Pencil className="mr-2 h-4 w-4" /> Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => {
                setPartnerToDelete(row.original);
                setDeleteDialogOpen(true);
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const partners: FulfillmentPartner[] = data?.items || [];
  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fulfillment Partners"
        description="Manage 3PL and self-managed fulfillment providers"
        actions={
          <Button onClick={openCreate}>
            <Plus className="mr-2 h-4 w-4" /> Add Partner
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={partners}
        isLoading={isLoading}
        searchKey="name"
        searchPlaceholder="Search partners..."
      />

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={(open) => !open && closeDialog()}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{isEditMode ? 'Edit' : 'Add'} Fulfillment Partner</DialogTitle>
            <DialogDescription>
              {isEditMode ? 'Update partner details and credentials.' : 'Register a new 3PL or self-managed fulfillment provider.'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Code</Label>
                <Input
                  placeholder="e.g. CJDQUICK"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  disabled={isEditMode}
                  maxLength={20}
                />
              </div>
              <div className="space-y-2">
                <Label>Provider Type</Label>
                <Select
                  value={formData.provider_type}
                  onValueChange={(v) => setFormData({ ...formData, provider_type: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {providerTypes.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                placeholder="e.g. CJDQuick Logistics"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            {formData.provider_type === '3PL' && (
              <>
                <div className="border-t pt-4 mt-2">
                  <h4 className="text-sm font-medium mb-3">API Configuration</h4>
                  <div className="grid gap-3">
                    <div className="space-y-2">
                      <Label>API Base URL</Label>
                      <Input
                        placeholder="https://api.partner.com/v1"
                        value={formData.api_base_url}
                        onChange={(e) => setFormData({ ...formData, api_base_url: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>API Key</Label>
                      <Input
                        type="password"
                        placeholder="API key for integration endpoints"
                        value={formData.api_key}
                        onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Webhook Secret</Label>
                      <Input
                        type="password"
                        placeholder="HMAC secret for webhook verification"
                        value={formData.webhook_secret}
                        onChange={(e) => setFormData({ ...formData, webhook_secret: e.target.value })}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4 mt-2">
                  <h4 className="text-sm font-medium mb-3">Authentication</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <Input
                        placeholder="auth email"
                        value={formData.auth_email}
                        onChange={(e) => setFormData({ ...formData, auth_email: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Input
                        type="password"
                        placeholder="auth password"
                        value={formData.auth_password}
                        onChange={(e) => setFormData({ ...formData, auth_password: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Company ID</Label>
                      <Input
                        placeholder="UUID"
                        value={formData.auth_company_id}
                        onChange={(e) => setFormData({ ...formData, auth_company_id: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Integration Profile ID</Label>
                      <Input
                        placeholder="UUID"
                        value={formData.auth_integration_profile_id}
                        onChange={(e) => setFormData({ ...formData, auth_integration_profile_id: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            <div className="flex items-center gap-2 border-t pt-4 mt-2">
              <Switch
                checked={formData.is_active}
                onCheckedChange={(v) => setFormData({ ...formData, is_active: v })}
              />
              <Label>Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeDialog}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={isSaving || !formData.code || !formData.name}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEditMode ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Fulfillment Partner?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete <strong>{partnerToDelete?.name}</strong> ({partnerToDelete?.code}).
              {(partnerToDelete?.warehouse_count ?? 0) > 0 && (
                <span className="block mt-2 text-destructive font-medium">
                  Cannot delete: {partnerToDelete?.warehouse_count} warehouse(s) are still linked.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => partnerToDelete && deleteMutation.mutate(partnerToDelete.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
