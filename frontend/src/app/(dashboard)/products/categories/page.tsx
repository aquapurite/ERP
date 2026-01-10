'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, FolderTree, ChevronRight, Loader2 } from 'lucide-react';
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
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { categoriesApi } from '@/lib/api';
import { Category } from '@/types';

interface CategoryFormData {
  name: string;
  slug: string;
  description: string;
  parent_id: string;
  sort_order: number;
  is_active: boolean;
}

const defaultFormData: CategoryFormData = {
  name: '',
  slug: '',
  description: '',
  parent_id: '',
  sort_order: 0,
  is_active: true,
};

export default function CategoriesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // Create dialog state
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [createFormData, setCreateFormData] = useState<CategoryFormData>(defaultFormData);

  // Edit dialog state
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editFormData, setEditFormData] = useState<CategoryFormData>(defaultFormData);

  // Delete dialog state
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [categoryToDelete, setCategoryToDelete] = useState<Category | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['categories', page, pageSize],
    queryFn: () => categoriesApi.list({ page: page + 1, size: pageSize }),
  });

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      toast.success('Category created successfully');
      setIsCreateDialogOpen(false);
      setCreateFormData(defaultFormData);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create category');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Category> }) =>
      categoriesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      toast.success('Category updated successfully');
      setIsEditDialogOpen(false);
      setEditingCategory(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update category');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => categoriesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      toast.success('Category deleted successfully');
      setIsDeleteDialogOpen(false);
      setCategoryToDelete(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete category');
    },
  });

  const handleCreate = () => {
    if (!createFormData.name.trim()) {
      toast.error('Category name is required');
      return;
    }
    createMutation.mutate({
      name: createFormData.name,
      slug: createFormData.slug || createFormData.name.toLowerCase().replace(/\s+/g, '-'),
      description: createFormData.description || undefined,
      parent_id: createFormData.parent_id || undefined,
      sort_order: createFormData.sort_order || 0,
      is_active: createFormData.is_active,
    });
  };

  const handleEdit = (category: Category) => {
    setEditingCategory(category);
    setEditFormData({
      name: category.name,
      slug: category.slug,
      description: category.description || '',
      parent_id: category.parent_id || '',
      sort_order: category.sort_order || 0,
      is_active: category.is_active,
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdate = () => {
    if (!editingCategory || !editFormData.name.trim()) {
      toast.error('Category name is required');
      return;
    }
    updateMutation.mutate({
      id: editingCategory.id,
      data: {
        name: editFormData.name,
        slug: editFormData.slug || editFormData.name.toLowerCase().replace(/\s+/g, '-'),
        description: editFormData.description || undefined,
        parent_id: editFormData.parent_id || undefined,
        sort_order: editFormData.sort_order,
        is_active: editFormData.is_active,
      },
    });
  };

  const handleDelete = (category: Category) => {
    setCategoryToDelete(category);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (categoryToDelete) {
      deleteMutation.mutate(categoryToDelete.id);
    }
  };

  // Get root categories for parent selection
  const rootCategories = data?.items?.filter((c: Category) => !c.parent_id) ?? [];

  const columns: ColumnDef<Category>[] = [
    {
      accessorKey: 'name',
      header: 'Category',
      size: 200,
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted flex-shrink-0">
            <FolderTree className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <div className="font-medium truncate">{row.original.name}</div>
            <div className="text-sm text-muted-foreground truncate">{row.original.slug}</div>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'parent',
      header: 'Parent',
      size: 100,
      cell: ({ row }) => {
        const parentId = row.original.parent_id;
        return parentId ? (
          <span className="flex items-center gap-1 text-sm text-muted-foreground">
            <ChevronRight className="h-3 w-3" />
            Sub
          </span>
        ) : (
          <span className="text-sm font-medium">Root</span>
        );
      },
    },
    {
      accessorKey: 'description',
      header: 'Description',
      size: 250,
      maxSize: 300,
      cell: ({ row }) => (
        <div className="max-w-[250px]">
          <span className="text-sm text-muted-foreground line-clamp-1 truncate block" title={row.original.description || ''}>
            {row.original.description || '-'}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'sort_order',
      header: 'Order',
      size: 70,
      cell: ({ row }) => (
        <span className="text-sm">{row.original.sort_order ?? 0}</span>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      size: 80,
      cell: ({ row }) => (
        <StatusBadge status={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />
      ),
    },
    {
      id: 'actions',
      size: 50,
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
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => handleDelete(row.original)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Categories"
        description="Manage product categories and subcategories"
        actions={
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Category
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Category</DialogTitle>
                <DialogDescription>
                  Add a new product category to organize your catalog.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="create-name">Name *</Label>
                  <Input
                    id="create-name"
                    placeholder="Category name"
                    value={createFormData.name}
                    onChange={(e) =>
                      setCreateFormData({ ...createFormData, name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-slug">Slug</Label>
                  <Input
                    id="create-slug"
                    placeholder="category-slug (auto-generated if empty)"
                    value={createFormData.slug}
                    onChange={(e) =>
                      setCreateFormData({ ...createFormData, slug: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-parent">Parent Category</Label>
                  <Select
                    value={createFormData.parent_id || 'none'}
                    onValueChange={(value) =>
                      setCreateFormData({ ...createFormData, parent_id: value === 'none' ? '' : value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select parent (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None (Root Category)</SelectItem>
                      {rootCategories.map((cat: Category) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-description">Description</Label>
                  <Textarea
                    id="create-description"
                    placeholder="Category description"
                    value={createFormData.description}
                    onChange={(e) =>
                      setCreateFormData({ ...createFormData, description: e.target.value })
                    }
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="create-order">Sort Order</Label>
                    <Input
                      id="create-order"
                      type="number"
                      placeholder="0"
                      value={createFormData.sort_order}
                      onChange={(e) =>
                        setCreateFormData({ ...createFormData, sort_order: parseInt(e.target.value) || 0 })
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between pt-6">
                    <Label htmlFor="create-active">Active</Label>
                    <Switch
                      id="create-active"
                      checked={createFormData.is_active}
                      onCheckedChange={(checked) =>
                        setCreateFormData({ ...createFormData, is_active: checked })
                      }
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create Category
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
        searchPlaceholder="Search categories..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Category</DialogTitle>
            <DialogDescription>
              Update the category details.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Name *</Label>
              <Input
                id="edit-name"
                placeholder="Category name"
                value={editFormData.name}
                onChange={(e) =>
                  setEditFormData({ ...editFormData, name: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-slug">Slug</Label>
              <Input
                id="edit-slug"
                placeholder="category-slug"
                value={editFormData.slug}
                onChange={(e) =>
                  setEditFormData({ ...editFormData, slug: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-parent">Parent Category</Label>
              <Select
                value={editFormData.parent_id || 'none'}
                onValueChange={(value) =>
                  setEditFormData({ ...editFormData, parent_id: value === 'none' ? '' : value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select parent (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None (Root Category)</SelectItem>
                  {rootCategories
                    .filter((cat: Category) => cat.id !== editingCategory?.id)
                    .map((cat: Category) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                placeholder="Category description"
                value={editFormData.description}
                onChange={(e) =>
                  setEditFormData({ ...editFormData, description: e.target.value })
                }
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-order">Sort Order</Label>
                <Input
                  id="edit-order"
                  type="number"
                  placeholder="0"
                  value={editFormData.sort_order}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, sort_order: parseInt(e.target.value) || 0 })
                  }
                />
              </div>
              <div className="flex items-center justify-between pt-6">
                <Label htmlFor="edit-active">Active</Label>
                <Switch
                  id="edit-active"
                  checked={editFormData.is_active}
                  onCheckedChange={(checked) =>
                    setEditFormData({ ...editFormData, is_active: checked })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdate} disabled={updateMutation.isPending}>
              {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Category</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{categoryToDelete?.name}"? This action cannot be undone.
              {categoryToDelete?.parent_id === undefined && (
                <span className="block mt-2 text-amber-600">
                  Warning: This is a root category. Deleting it may affect subcategories.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
