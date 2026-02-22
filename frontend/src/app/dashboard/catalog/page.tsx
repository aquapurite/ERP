'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Plus, Pencil, Trash2, Package, Loader2, Barcode, Tag } from 'lucide-react';
import Link from 'next/link';
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader, StatusBadge } from '@/components/common';
import { productsApi, categoriesApi } from '@/lib/api';
import { Product, Category } from '@/types';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [productToDelete, setProductToDelete] = useState<Product | null>(null);

  // Category filter state
  const [categoryId, setCategoryId] = useState<string>('');
  const [subcategoryId, setSubcategoryId] = useState<string>('');
  const [subcategories, setSubcategories] = useState<Category[]>([]);
  const [loadingSubcats, setLoadingSubcats] = useState(false);

  // Root categories
  const { data: rootCategories } = useQuery({
    queryKey: ['categories-roots'],
    queryFn: () => categoriesApi.getRoots(),
  });

  // Fetch subcategories on category change
  const handleCategoryChange = useCallback(async (catId: string) => {
    setCategoryId(catId);
    setSubcategoryId('');
    setSubcategories([]);
    setPage(0);

    if (catId) {
      setLoadingSubcats(true);
      try {
        const result = await categoriesApi.getChildren(catId);
        const items = result?.items ?? result ?? [];
        setSubcategories(Array.isArray(items) ? items : []);
      } catch {
        setSubcategories([]);
      }
      setLoadingSubcats(false);
    }
  }, []);

  const handleSubcategoryChange = useCallback((subId: string) => {
    setSubcategoryId(subId);
    setPage(0);
  }, []);

  // Use subcategory_id if selected, else category_id if selected, else no filter
  const activeCategoryFilter = subcategoryId || categoryId || undefined;

  const { data, isLoading } = useQuery({
    queryKey: ['products', page, pageSize, activeCategoryFilter],
    queryFn: () => productsApi.list({ page: page + 1, size: pageSize, category_id: activeCategoryFilter }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productsApi.delete(id),
    onSuccess: () => {
      toast.success('Product deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setDeleteDialogOpen(false);
      setProductToDelete(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete product');
    },
  });

  const handleDeleteClick = (product: Product) => {
    setProductToDelete(product);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (productToDelete) {
      deleteMutation.mutate(productToDelete.id);
    }
  };

  const columns: ColumnDef<Product>[] = [
    {
      accessorKey: 'name',
      header: 'Product',
      cell: ({ row }) => {
        const primaryImage = row.original.images?.find(img => img.is_primary) || row.original.images?.[0];
        return (
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted overflow-hidden">
              {primaryImage ? (
                <img
                  src={primaryImage.thumbnail_url || primaryImage.image_url}
                  alt={primaryImage.alt_text || row.original.name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <Package className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Link href={`/dashboard/catalog/${row.original.id}`} className="font-medium hover:underline">
                  {row.original.name}
                </Link>
                {row.original.model_code && (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 text-xs font-medium" title="Model Code for Barcode">
                    <Barcode className="h-3 w-3" />
                    {row.original.model_code}
                  </span>
                )}
                {row.original.item_type && (
                  <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${
                    row.original.item_type === 'FG' ? 'bg-green-100 text-green-700' :
                    row.original.item_type === 'SP' ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-100 text-gray-700'
                  }`} title={row.original.item_type === 'FG' ? 'Finished Goods' : row.original.item_type === 'SP' ? 'Spare Part' : row.original.item_type}>
                    <Tag className="h-3 w-3" />
                    {row.original.item_type}
                  </span>
                )}
              </div>
              <div className="text-sm text-muted-foreground">{row.original.sku}</div>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ row }) => row.original.category?.name || '-',
    },
    {
      accessorKey: 'brand',
      header: 'Brand',
      cell: ({ row }) => row.original.brand?.name || '-',
    },
    {
      accessorKey: 'mrp',
      header: 'MRP',
      cell: ({ row }) => formatCurrency(row.original.mrp),
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
            <DropdownMenuItem asChild>
              <Link href={`/dashboard/catalog/${row.original.id}`}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => handleDeleteClick(row.original)}
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
        title="Products"
        description="Manage your product catalog"
        actions={
          <Button asChild>
            <Link href="/dashboard/catalog/new">
              <Plus className="mr-2 h-4 w-4" />
              Add Product
            </Link>
          </Button>
        }
      />

      {/* Category / Subcategory Filters */}
      <div className="flex items-center gap-3">
        <Select
          value={categoryId || 'all'}
          onValueChange={(value) => handleCategoryChange(value === 'all' ? '' : value)}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {(Array.isArray(rootCategories) ? rootCategories : rootCategories?.items ?? [])
              .filter((c: Category) => c.is_active !== false)
              .map((c: Category) => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
          </SelectContent>
        </Select>

        <Select
          value={subcategoryId || 'all'}
          onValueChange={(value) => handleSubcategoryChange(value === 'all' ? '' : value)}
          disabled={!categoryId || loadingSubcats}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder={loadingSubcats ? 'Loading...' : 'All Subcategories'} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Subcategories</SelectItem>
            {subcategories
              .filter((c: Category) => c.is_active !== false)
              .map((c: Category) => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            {categoryId && !loadingSubcats && subcategories.length === 0 && (
              <SelectItem value="none" disabled>No subcategories</SelectItem>
            )}
          </SelectContent>
        </Select>

        {(categoryId || subcategoryId) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setCategoryId(''); setSubcategoryId(''); setSubcategories([]); setPage(0); }}
          >
            Clear filters
          </Button>
        )}
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        searchKey="name"
        searchPlaceholder="Search products..."
        isLoading={isLoading}
        manualPagination
        pageCount={data?.pages ?? 0}
        pageIndex={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Product</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{productToDelete?.name}"? This action cannot be undone.
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
