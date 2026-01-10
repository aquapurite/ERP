'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  ArrowLeft, Save, Package, Loader2, Plus, X, Trash2,
  Image as ImageIcon, Star, Upload, Edit2, Check, AlertCircle,
  FileText, List, File
} from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { PageHeader } from '@/components/common';
import { productsApi, categoriesApi, brandsApi } from '@/lib/api';
import { Category, Brand, Product, ProductImage, ProductVariant, ProductSpecification, ProductDocument } from '@/types';

interface ProductFormData {
  name: string;
  sku: string;
  slug?: string;
  description?: string;
  category_id?: string;
  brand_id?: string;
  mrp: number;
  selling_price: number;
  cost_price?: number;
  gst_rate?: number;
  hsn_code?: string;
  weight?: number;
  length?: number;
  width?: number;
  height?: number;
  is_active: boolean;
  is_featured: boolean;
  requires_installation: boolean;
  warranty_months?: number;
  meta_title?: string;
  meta_description?: string;
}

const productSchema = z.object({
  name: z.string().min(2, 'Product name must be at least 2 characters'),
  sku: z.string().min(2, 'SKU must be at least 2 characters'),
  slug: z.string().optional(),
  description: z.string().optional(),
  category_id: z.string().optional(),
  brand_id: z.string().optional(),
  mrp: z.coerce.number().min(0, 'MRP must be positive'),
  selling_price: z.coerce.number().min(0, 'Selling price must be positive'),
  cost_price: z.coerce.number().min(0, 'Cost price must be positive').optional(),
  gst_rate: z.coerce.number().min(0).max(100).optional(),
  hsn_code: z.string().optional(),
  weight: z.coerce.number().min(0).optional(),
  length: z.coerce.number().min(0).optional(),
  width: z.coerce.number().min(0).optional(),
  height: z.coerce.number().min(0).optional(),
  is_active: z.boolean().default(true),
  is_featured: z.boolean().default(false),
  requires_installation: z.boolean().default(false),
  warranty_months: z.coerce.number().min(0).optional(),
  meta_title: z.string().optional(),
  meta_description: z.string().optional(),
}).refine((data) => data.selling_price <= data.mrp, {
  message: 'Selling price cannot be greater than MRP',
  path: ['selling_price'],
});

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const productId = params.id as string;

  const [activeTab, setActiveTab] = useState('details');
  const [isImageDialogOpen, setIsImageDialogOpen] = useState(false);
  const [isVariantDialogOpen, setIsVariantDialogOpen] = useState(false);
  const [newImageUrl, setNewImageUrl] = useState('');
  const [newImageAlt, setNewImageAlt] = useState('');
  const [editingVariant, setEditingVariant] = useState<ProductVariant | null>(null);

  // Variant form state
  const [variantName, setVariantName] = useState('');
  const [variantSku, setVariantSku] = useState('');
  const [variantMrp, setVariantMrp] = useState('');
  const [variantSellingPrice, setVariantSellingPrice] = useState('');
  const [variantStock, setVariantStock] = useState('');

  // Specification form state
  const [isSpecDialogOpen, setIsSpecDialogOpen] = useState(false);
  const [specGroupName, setSpecGroupName] = useState('General');
  const [specKey, setSpecKey] = useState('');
  const [specValue, setSpecValue] = useState('');

  // Document form state
  const [isDocDialogOpen, setIsDocDialogOpen] = useState(false);
  const [docTitle, setDocTitle] = useState('');
  const [docType, setDocType] = useState('OTHER');
  const [docFileUrl, setDocFileUrl] = useState('');

  const { data: product, isLoading, error } = useQuery({
    queryKey: ['product', productId],
    queryFn: () => productsApi.getById(productId),
    enabled: !!productId,
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list({ size: 100 }),
  });

  const { data: brandsData } = useQuery({
    queryKey: ['brands'],
    queryFn: () => brandsApi.list({ size: 100 }),
  });

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema) as any,
    values: product ? {
      name: product.name || '',
      sku: product.sku || '',
      slug: product.slug || '',
      description: product.description || '',
      // Handle both direct category_id and nested category.id
      category_id: product.category_id || product.category?.id || '',
      brand_id: product.brand_id || product.brand?.id || '',
      mrp: product.mrp || 0,
      selling_price: product.selling_price || 0,
      cost_price: product.cost_price || 0,
      gst_rate: product.gst_rate || 18,
      hsn_code: product.hsn_code || '',
      weight: product.weight || (product as any).dead_weight_kg || 0,
      length: product.length || (product as any).length_cm || 0,
      width: product.width || (product as any).width_cm || 0,
      height: product.height || (product as any).height_cm || 0,
      is_active: product.is_active ?? true,
      is_featured: product.is_featured ?? false,
      requires_installation: product.requires_installation ?? false,
      warranty_months: product.warranty_months || 12,
      meta_title: product.meta_title || '',
      meta_description: product.meta_description || '',
    } : undefined,
  });

  const updateMutation = useMutation({
    mutationFn: (data: ProductFormData) => productsApi.update(productId, data),
    onSuccess: () => {
      toast.success('Product updated successfully');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update product');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => productsApi.delete(productId),
    onSuccess: () => {
      toast.success('Product deleted successfully');
      router.push('/products');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete product');
    },
  });

  const addImageMutation = useMutation({
    mutationFn: (image: { image_url: string; alt_text?: string }) =>
      productsApi.addImage(productId, image),
    onSuccess: () => {
      toast.success('Image added successfully');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      setIsImageDialogOpen(false);
      setNewImageUrl('');
      setNewImageAlt('');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to add image');
    },
  });

  const deleteImageMutation = useMutation({
    mutationFn: (imageId: string) => productsApi.deleteImage(productId, imageId),
    onSuccess: () => {
      toast.success('Image deleted');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete image');
    },
  });

  const setPrimaryImageMutation = useMutation({
    mutationFn: (imageId: string) => productsApi.setPrimaryImage(productId, imageId),
    onSuccess: () => {
      toast.success('Primary image updated');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to set primary image');
    },
  });

  const addVariantMutation = useMutation({
    mutationFn: (variant: { name: string; sku: string; mrp?: number; selling_price?: number; stock_quantity?: number }) =>
      productsApi.addVariant(productId, variant),
    onSuccess: () => {
      toast.success('Variant added successfully');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      resetVariantForm();
      setIsVariantDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to add variant');
    },
  });

  const updateVariantMutation = useMutation({
    mutationFn: ({ variantId, variant }: { variantId: string; variant: Partial<ProductVariant> }) =>
      productsApi.updateVariant(productId, variantId, variant),
    onSuccess: () => {
      toast.success('Variant updated');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      resetVariantForm();
      setEditingVariant(null);
      setIsVariantDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update variant');
    },
  });

  const deleteVariantMutation = useMutation({
    mutationFn: (variantId: string) => productsApi.deleteVariant(productId, variantId),
    onSuccess: () => {
      toast.success('Variant deleted');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete variant');
    },
  });

  // Specification mutations
  const addSpecMutation = useMutation({
    mutationFn: (spec: { group_name?: string; key: string; value: string }) =>
      productsApi.addSpecification(productId, spec),
    onSuccess: () => {
      toast.success('Specification added');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      setIsSpecDialogOpen(false);
      setSpecGroupName('General');
      setSpecKey('');
      setSpecValue('');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to add specification');
    },
  });

  const deleteSpecMutation = useMutation({
    mutationFn: (specId: string) => productsApi.deleteSpecification(productId, specId),
    onSuccess: () => {
      toast.success('Specification deleted');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete specification');
    },
  });

  // Document mutations
  const addDocMutation = useMutation({
    mutationFn: (doc: { title: string; document_type?: string; file_url: string }) =>
      productsApi.addDocument(productId, doc),
    onSuccess: () => {
      toast.success('Document added');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      setIsDocDialogOpen(false);
      setDocTitle('');
      setDocType('OTHER');
      setDocFileUrl('');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to add document');
    },
  });

  const deleteDocMutation = useMutation({
    mutationFn: (docId: string) => productsApi.deleteDocument(productId, docId),
    onSuccess: () => {
      toast.success('Document deleted');
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete document');
    },
  });

  const onSubmit = (data: ProductFormData) => {
    console.log('Form submitted with data:', data);
    updateMutation.mutate(data);
  };

  const onFormError = (errors: any) => {
    console.error('Form validation errors:', errors);
    const errorMessages = Object.entries(errors)
      .map(([field, error]: [string, any]) => `${field}: ${error?.message || 'Invalid'}`)
      .join(', ');
    toast.error(`Validation failed: ${errorMessages}`);
  };

  const resetVariantForm = () => {
    setVariantName('');
    setVariantSku('');
    setVariantMrp('');
    setVariantSellingPrice('');
    setVariantStock('');
    setEditingVariant(null);
  };

  const handleAddImage = () => {
    if (newImageUrl.trim()) {
      addImageMutation.mutate({ image_url: newImageUrl, alt_text: newImageAlt });
    }
  };

  const handleAddVariant = () => {
    if (variantName && variantSku) {
      if (editingVariant) {
        updateVariantMutation.mutate({
          variantId: editingVariant.id,
          variant: {
            name: variantName,
            sku: variantSku,
            mrp: variantMrp ? parseFloat(variantMrp) : undefined,
            selling_price: variantSellingPrice ? parseFloat(variantSellingPrice) : undefined,
            stock_quantity: variantStock ? parseInt(variantStock) : undefined,
          },
        });
      } else {
        addVariantMutation.mutate({
          name: variantName,
          sku: variantSku,
          mrp: variantMrp ? parseFloat(variantMrp) : undefined,
          selling_price: variantSellingPrice ? parseFloat(variantSellingPrice) : undefined,
          stock_quantity: variantStock ? parseInt(variantStock) : undefined,
        });
      }
    }
  };

  const openEditVariant = (variant: ProductVariant) => {
    setEditingVariant(variant);
    setVariantName(variant.name);
    setVariantSku(variant.sku);
    setVariantMrp(variant.mrp?.toString() || '');
    setVariantSellingPrice(variant.selling_price?.toString() || '');
    setVariantStock(variant.stock_quantity?.toString() || '');
    setIsVariantDialogOpen(true);
  };

  const handleAddSpec = () => {
    if (specKey && specValue) {
      addSpecMutation.mutate({
        group_name: specGroupName || 'General',
        key: specKey,
        value: specValue,
      });
    }
  };

  const handleAddDoc = () => {
    if (docTitle && docFileUrl) {
      addDocMutation.mutate({
        title: docTitle,
        document_type: docType,
        file_url: docFileUrl,
      });
    }
  };

  const categories = categoriesData?.items || [];
  const brands = brandsData?.items || [];
  const images: ProductImage[] = product?.images || [];
  const variants: ProductVariant[] = product?.variants || [];
  const specifications: ProductSpecification[] = product?.specifications || [];
  const documents: ProductDocument[] = product?.documents || [];

  // Group specifications by group_name
  const groupedSpecs = specifications.reduce((acc, spec) => {
    const group = (spec as any).group_name || 'General';
    if (!acc[group]) acc[group] = [];
    acc[group].push(spec);
    return acc;
  }, {} as Record<string, ProductSpecification[]>);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Skeleton className="h-96" />
          </div>
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Product Not Found"
          description="The product you're looking for doesn't exist"
          actions={
            <Button variant="outline" asChild>
              <Link href="/products">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Products
              </Link>
            </Button>
          }
        />
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Unable to load product. Please check the ID and try again.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={product.name}
        description={`SKU: ${product.sku}`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href="/products">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Link>
            </Button>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="destructive">
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete Product</DialogTitle>
                  <DialogDescription>
                    Are you sure you want to delete "{product.name}"? This action cannot be undone.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button variant="outline">Cancel</Button>
                  </DialogClose>
                  <Button
                    variant="destructive"
                    onClick={() => deleteMutation.mutate()}
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : null}
                    Delete
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <Button
              onClick={form.handleSubmit(onSubmit, onFormError)}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Changes
            </Button>
          </div>
        }
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="images">Images ({images.length})</TabsTrigger>
          <TabsTrigger value="specs">Specifications ({specifications.length})</TabsTrigger>
          <TabsTrigger value="variants">Variants ({variants.length})</TabsTrigger>
          <TabsTrigger value="docs">Documents ({documents.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="mt-6">
          <form onSubmit={form.handleSubmit(onSubmit, onFormError)} className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Main Content */}
              <div className="lg:col-span-2 space-y-6">
                {/* Basic Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Package className="h-5 w-5" />
                      Basic Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="name">Product Name *</Label>
                        <Input id="name" {...form.register('name')} />
                        {form.formState.errors.name && (
                          <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="sku">SKU *</Label>
                        <Input id="sku" {...form.register('sku')} />
                        {form.formState.errors.sku && (
                          <p className="text-sm text-destructive">{form.formState.errors.sku.message}</p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Textarea id="description" rows={4} {...form.register('description')} />
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="category">Category</Label>
                        <Select
                          value={form.watch('category_id')}
                          onValueChange={(value) => form.setValue('category_id', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select category" />
                          </SelectTrigger>
                          <SelectContent>
                            {categories.map((category: Category) => (
                              <SelectItem key={category.id} value={category.id}>
                                {category.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="brand">Brand</Label>
                        <Select
                          value={form.watch('brand_id')}
                          onValueChange={(value) => form.setValue('brand_id', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select brand" />
                          </SelectTrigger>
                          <SelectContent>
                            {brands.map((brand: Brand) => (
                              <SelectItem key={brand.id} value={brand.id}>
                                {brand.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Pricing */}
                <Card>
                  <CardHeader>
                    <CardTitle>Pricing</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-3">
                      <div className="space-y-2">
                        <Label htmlFor="mrp">MRP (Rs.) *</Label>
                        <Input id="mrp" type="number" min="0" step="0.01" {...form.register('mrp')} />
                        {form.formState.errors.mrp && (
                          <p className="text-sm text-destructive">{form.formState.errors.mrp.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="selling_price">Selling Price (Rs.) *</Label>
                        <Input id="selling_price" type="number" min="0" step="0.01" {...form.register('selling_price')} />
                        {form.formState.errors.selling_price && (
                          <p className="text-sm text-destructive">{form.formState.errors.selling_price.message}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="cost_price">Cost Price (Rs.)</Label>
                        <Input id="cost_price" type="number" min="0" step="0.01" {...form.register('cost_price')} />
                      </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="gst_rate">GST Rate (%)</Label>
                        <Select
                          value={form.watch('gst_rate')?.toString()}
                          onValueChange={(value) => form.setValue('gst_rate', parseFloat(value))}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select GST rate" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0">0%</SelectItem>
                            <SelectItem value="5">5%</SelectItem>
                            <SelectItem value="12">12%</SelectItem>
                            <SelectItem value="18">18%</SelectItem>
                            <SelectItem value="28">28%</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="hsn_code">HSN Code</Label>
                        <Input id="hsn_code" {...form.register('hsn_code')} />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Dimensions */}
                <Card>
                  <CardHeader>
                    <CardTitle>Dimensions & Shipping</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 sm:grid-cols-4">
                      <div className="space-y-2">
                        <Label htmlFor="weight">Weight (kg)</Label>
                        <Input id="weight" type="number" min="0" step="0.01" {...form.register('weight')} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="length">Length (cm)</Label>
                        <Input id="length" type="number" min="0" step="0.1" {...form.register('length')} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="width">Width (cm)</Label>
                        <Input id="width" type="number" min="0" step="0.1" {...form.register('width')} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="height">Height (cm)</Label>
                        <Input id="height" type="number" min="0" step="0.1" {...form.register('height')} />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label htmlFor="is_active">Active</Label>
                        <p className="text-xs text-muted-foreground">Product visible in catalog</p>
                      </div>
                      <Switch
                        id="is_active"
                        checked={form.watch('is_active')}
                        onCheckedChange={(checked) => form.setValue('is_active', checked)}
                      />
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label htmlFor="is_featured">Featured</Label>
                        <p className="text-xs text-muted-foreground">Show in featured section</p>
                      </div>
                      <Switch
                        id="is_featured"
                        checked={form.watch('is_featured')}
                        onCheckedChange={(checked) => form.setValue('is_featured', checked)}
                      />
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label htmlFor="requires_installation">Requires Installation</Label>
                        <p className="text-xs text-muted-foreground">Installation service needed</p>
                      </div>
                      <Switch
                        id="requires_installation"
                        checked={form.watch('requires_installation')}
                        onCheckedChange={(checked) => form.setValue('requires_installation', checked)}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Warranty</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Select
                      value={form.watch('warranty_months')?.toString()}
                      onValueChange={(value) => form.setValue('warranty_months', parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warranty" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0">No Warranty</SelectItem>
                        <SelectItem value="6">6 Months</SelectItem>
                        <SelectItem value="12">12 Months</SelectItem>
                        <SelectItem value="24">24 Months</SelectItem>
                        <SelectItem value="36">36 Months</SelectItem>
                        <SelectItem value="60">60 Months</SelectItem>
                      </SelectContent>
                    </Select>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Info</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Created</span>
                      <span>{new Date(product.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Updated</span>
                      <span>{new Date(product.updated_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Category</span>
                      <span>{product.category?.name || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Brand</span>
                      <span>{product.brand?.name || '-'}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </form>
        </TabsContent>

        <TabsContent value="images" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5" />
                  Product Images
                </CardTitle>
                <CardDescription>Manage product images and set the primary image</CardDescription>
              </div>
              <Dialog open={isImageDialogOpen} onOpenChange={setIsImageDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Image
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Product Image</DialogTitle>
                    <DialogDescription>Enter the URL of the image to add</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="image_url">Image URL *</Label>
                      <Input
                        id="image_url"
                        placeholder="https://example.com/image.jpg"
                        value={newImageUrl}
                        onChange={(e) => setNewImageUrl(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="alt_text">Alt Text</Label>
                      <Input
                        id="alt_text"
                        placeholder="Image description"
                        value={newImageAlt}
                        onChange={(e) => setNewImageAlt(e.target.value)}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsImageDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddImage} disabled={!newImageUrl || addImageMutation.isPending}>
                      {addImageMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Add Image
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {images.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <ImageIcon className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium">No images yet</h3>
                  <p className="text-sm text-muted-foreground mt-1">Add images to showcase your product</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {images.map((image) => (
                    <div key={image.id} className="relative group">
                      <div className="aspect-square rounded-lg border overflow-hidden bg-muted">
                        <img
                          src={image.thumbnail_url || image.image_url}
                          alt={image.alt_text || 'Product image'}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      {image.is_primary && (
                        <Badge className="absolute top-2 left-2" variant="secondary">
                          <Star className="h-3 w-3 mr-1" />
                          Primary
                        </Badge>
                      )}
                      <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {!image.is_primary && (
                          <Button
                            size="icon"
                            variant="secondary"
                            className="h-8 w-8"
                            onClick={() => setPrimaryImageMutation.mutate(image.id)}
                          >
                            <Star className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          size="icon"
                          variant="destructive"
                          className="h-8 w-8"
                          onClick={() => deleteImageMutation.mutate(image.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="variants" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Product Variants</CardTitle>
                <CardDescription>Manage different variants of this product (sizes, colors, etc.)</CardDescription>
              </div>
              <Dialog open={isVariantDialogOpen} onOpenChange={(open) => {
                setIsVariantDialogOpen(open);
                if (!open) resetVariantForm();
              }}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Variant
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{editingVariant ? 'Edit Variant' : 'Add Product Variant'}</DialogTitle>
                    <DialogDescription>
                      {editingVariant ? 'Update variant details' : 'Create a new variant for this product'}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="variant_name">Variant Name *</Label>
                        <Input
                          id="variant_name"
                          placeholder="e.g., Blue - Large"
                          value={variantName}
                          onChange={(e) => setVariantName(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="variant_sku">SKU *</Label>
                        <Input
                          id="variant_sku"
                          placeholder="PROD-BL-LG"
                          value={variantSku}
                          onChange={(e) => setVariantSku(e.target.value)}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="variant_mrp">MRP</Label>
                        <Input
                          id="variant_mrp"
                          type="number"
                          placeholder="0"
                          value={variantMrp}
                          onChange={(e) => setVariantMrp(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="variant_price">Selling Price</Label>
                        <Input
                          id="variant_price"
                          type="number"
                          placeholder="0"
                          value={variantSellingPrice}
                          onChange={(e) => setVariantSellingPrice(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="variant_stock">Stock</Label>
                        <Input
                          id="variant_stock"
                          type="number"
                          placeholder="0"
                          value={variantStock}
                          onChange={(e) => setVariantStock(e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => {
                      setIsVariantDialogOpen(false);
                      resetVariantForm();
                    }}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleAddVariant}
                      disabled={!variantName || !variantSku || addVariantMutation.isPending || updateVariantMutation.isPending}
                    >
                      {(addVariantMutation.isPending || updateVariantMutation.isPending) && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      {editingVariant ? 'Update Variant' : 'Add Variant'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {variants.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Package className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium">No variants yet</h3>
                  <p className="text-sm text-muted-foreground mt-1">Add variants for different sizes, colors, etc.</p>
                </div>
              ) : (
                <div className="border rounded-lg">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3 font-medium">Variant</th>
                        <th className="text-left p-3 font-medium">SKU</th>
                        <th className="text-right p-3 font-medium">MRP</th>
                        <th className="text-right p-3 font-medium">Price</th>
                        <th className="text-right p-3 font-medium">Stock</th>
                        <th className="text-center p-3 font-medium">Status</th>
                        <th className="text-right p-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {variants.map((variant) => (
                        <tr key={variant.id} className="border-b last:border-0">
                          <td className="p-3 font-medium">{variant.name}</td>
                          <td className="p-3 text-muted-foreground">{variant.sku}</td>
                          <td className="p-3 text-right">{variant.mrp ? formatCurrency(variant.mrp) : '-'}</td>
                          <td className="p-3 text-right">{variant.selling_price ? formatCurrency(variant.selling_price) : '-'}</td>
                          <td className="p-3 text-right">{variant.stock_quantity ?? '-'}</td>
                          <td className="p-3 text-center">
                            <Badge variant={variant.is_active ? 'default' : 'secondary'}>
                              {variant.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td className="p-3 text-right">
                            <div className="flex justify-end gap-1">
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8"
                                onClick={() => openEditVariant(variant)}
                              >
                                <Edit2 className="h-4 w-4" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 text-destructive hover:text-destructive"
                                onClick={() => deleteVariantMutation.mutate(variant.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Specifications Tab */}
        <TabsContent value="specs" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <List className="h-5 w-5" />
                  Product Specifications
                </CardTitle>
                <CardDescription>Technical specifications and details</CardDescription>
              </div>
              <Dialog open={isSpecDialogOpen} onOpenChange={setIsSpecDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Specification
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Specification</DialogTitle>
                    <DialogDescription>Add a new specification to this product</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="spec_group">Group</Label>
                      <Select value={specGroupName} onValueChange={setSpecGroupName}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select group" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="General">General</SelectItem>
                          <SelectItem value="Technical">Technical</SelectItem>
                          <SelectItem value="Dimensions">Dimensions</SelectItem>
                          <SelectItem value="Electrical">Electrical</SelectItem>
                          <SelectItem value="Features">Features</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="spec_key">Specification Name *</Label>
                      <Input
                        id="spec_key"
                        placeholder="e.g., Storage Capacity"
                        value={specKey}
                        onChange={(e) => setSpecKey(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="spec_value">Value *</Label>
                      <Input
                        id="spec_value"
                        placeholder="e.g., 12 Liters"
                        value={specValue}
                        onChange={(e) => setSpecValue(e.target.value)}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsSpecDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddSpec} disabled={!specKey || !specValue || addSpecMutation.isPending}>
                      {addSpecMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Add Specification
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {specifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <List className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium">No specifications yet</h3>
                  <p className="text-sm text-muted-foreground mt-1">Add technical specifications to help customers</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {Object.entries(groupedSpecs).map(([groupName, specs]) => (
                    <div key={groupName}>
                      <h4 className="font-medium text-sm text-muted-foreground mb-3">{groupName}</h4>
                      <div className="border rounded-lg divide-y">
                        {specs.map((spec) => (
                          <div key={spec.id} className="flex items-center justify-between p-3 hover:bg-muted/50">
                            <div className="flex-1">
                              <span className="font-medium">{(spec as any).key || spec.name}</span>
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="text-muted-foreground">{(spec as any).value || spec.value}</span>
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 text-destructive hover:text-destructive"
                                onClick={() => deleteSpecMutation.mutate(spec.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="docs" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Product Documents
                </CardTitle>
                <CardDescription>Manuals, brochures, and other documents</CardDescription>
              </div>
              <Dialog open={isDocDialogOpen} onOpenChange={setIsDocDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Document
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Document</DialogTitle>
                    <DialogDescription>Add a document link to this product</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="doc_title">Document Title *</Label>
                      <Input
                        id="doc_title"
                        placeholder="e.g., User Manual"
                        value={docTitle}
                        onChange={(e) => setDocTitle(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="doc_type">Document Type</Label>
                      <Select value={docType} onValueChange={setDocType}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="MANUAL">User Manual</SelectItem>
                          <SelectItem value="WARRANTY_CARD">Warranty Card</SelectItem>
                          <SelectItem value="BROCHURE">Brochure</SelectItem>
                          <SelectItem value="CERTIFICATE">Certificate</SelectItem>
                          <SelectItem value="OTHER">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="doc_url">File URL *</Label>
                      <Input
                        id="doc_url"
                        placeholder="https://example.com/document.pdf"
                        value={docFileUrl}
                        onChange={(e) => setDocFileUrl(e.target.value)}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsDocDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddDoc} disabled={!docTitle || !docFileUrl || addDocMutation.isPending}>
                      {addDocMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Add Document
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {documents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium">No documents yet</h3>
                  <p className="text-sm text-muted-foreground mt-1">Add user manuals, brochures, and other documents</p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {documents.map((doc) => (
                    <div key={doc.id} className="border rounded-lg p-4 hover:bg-muted/50">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                            <File className="h-5 w-5 text-muted-foreground" />
                          </div>
                          <div>
                            <h4 className="font-medium">{(doc as any).title || doc.name}</h4>
                            <p className="text-sm text-muted-foreground">{doc.document_type}</p>
                          </div>
                        </div>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => deleteDocMutation.mutate(doc.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="mt-3">
                        <a
                          href={(doc as any).file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          Open Document
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
