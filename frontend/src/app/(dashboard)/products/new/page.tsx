'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Save, Package, Loader2, Plus, X } from 'lucide-react';
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
import { PageHeader } from '@/components/common';
import { productsApi, categoriesApi, brandsApi } from '@/lib/api';
import { Category, Brand } from '@/types';

const productSchema = z.object({
  name: z.string().min(2, 'Product name must be at least 2 characters'),
  sku: z.string().min(2, 'SKU must be at least 2 characters').regex(/^[A-Za-z0-9-_]+$/, 'SKU can only contain letters, numbers, hyphens, and underscores'),
  slug: z.string().optional(),
  description: z.string().optional(),
  category_id: z.string().optional(),
  brand_id: z.string().optional(),
  mrp: z.coerce.number().min(0, 'MRP must be positive'),
  selling_price: z.coerce.number().min(0, 'Selling price must be positive'),
  cost_price: z.coerce.number().min(0, 'Cost price must be positive').optional(),
  gst_rate: z.coerce.number().min(0).max(100, 'GST rate must be between 0 and 100').optional(),
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
  tags: z.array(z.string()).optional(),
}).refine((data) => data.selling_price <= data.mrp, {
  message: 'Selling price cannot be greater than MRP',
  path: ['selling_price'],
});

type ProductFormData = z.infer<typeof productSchema>;

export default function NewProductPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);

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
    defaultValues: {
      name: '',
      sku: '',
      slug: '',
      description: '',
      mrp: 0,
      selling_price: 0,
      cost_price: 0,
      gst_rate: 18,
      warranty_months: 12,
      is_active: true,
      is_featured: false,
      requires_installation: false,
      tags: [],
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: ProductFormData) => productsApi.create({ ...data, tags }),
    onSuccess: () => {
      toast.success('Product created successfully');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      router.push('/products');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create product');
    },
  });

  const onSubmit = (data: ProductFormData) => {
    // Auto-generate slug from name if not provided
    if (!data.slug) {
      data.slug = data.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    }
    createMutation.mutate(data);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  // Auto-generate SKU suggestion from name
  const generateSku = () => {
    const name = form.getValues('name');
    if (name) {
      const sku = name.toUpperCase().replace(/\s+/g, '-').substring(0, 15) + '-' + Math.random().toString(36).substring(2, 6).toUpperCase();
      form.setValue('sku', sku);
    }
  };

  const categories = categoriesData?.items || [];
  const brands = brandsData?.items || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Add New Product"
        description="Create a new product in your catalog"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href="/products">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Cancel
              </Link>
            </Button>
            <Button
              onClick={form.handleSubmit(onSubmit)}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Product
            </Button>
          </div>
        }
      />

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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
                <CardDescription>
                  Enter the basic details of the product
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">Product Name *</Label>
                    <Input
                      id="name"
                      placeholder="Enter product name"
                      {...form.register('name')}
                    />
                    {form.formState.errors.name && (
                      <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="sku">SKU *</Label>
                    <div className="flex gap-2">
                      <Input
                        id="sku"
                        placeholder="Enter SKU"
                        {...form.register('sku')}
                      />
                      <Button type="button" variant="outline" onClick={generateSku}>
                        Generate
                      </Button>
                    </div>
                    {form.formState.errors.sku && (
                      <p className="text-sm text-destructive">{form.formState.errors.sku.message}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="slug">URL Slug</Label>
                  <Input
                    id="slug"
                    placeholder="product-url-slug (auto-generated if empty)"
                    {...form.register('slug')}
                  />
                  <p className="text-xs text-muted-foreground">
                    Leave empty to auto-generate from product name
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Enter product description"
                    rows={4}
                    {...form.register('description')}
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="category">Category</Label>
                    <Select
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
                <CardDescription>
                  Set the pricing and tax information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="mrp">MRP (Rs.) *</Label>
                    <Input
                      id="mrp"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      {...form.register('mrp')}
                    />
                    {form.formState.errors.mrp && (
                      <p className="text-sm text-destructive">{form.formState.errors.mrp.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="selling_price">Selling Price (Rs.) *</Label>
                    <Input
                      id="selling_price"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      {...form.register('selling_price')}
                    />
                    {form.formState.errors.selling_price && (
                      <p className="text-sm text-destructive">{form.formState.errors.selling_price.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cost_price">Cost Price (Rs.)</Label>
                    <Input
                      id="cost_price"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      {...form.register('cost_price')}
                    />
                  </div>
                </div>

                <Separator />

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="gst_rate">GST Rate (%)</Label>
                    <Select
                      defaultValue="18"
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
                    <Input
                      id="hsn_code"
                      placeholder="Enter HSN code"
                      {...form.register('hsn_code')}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Dimensions & Shipping */}
            <Card>
              <CardHeader>
                <CardTitle>Dimensions & Shipping</CardTitle>
                <CardDescription>
                  Physical dimensions for shipping calculations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-4">
                  <div className="space-y-2">
                    <Label htmlFor="weight">Weight (kg)</Label>
                    <Input
                      id="weight"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      {...form.register('weight')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="length">Length (cm)</Label>
                    <Input
                      id="length"
                      type="number"
                      min="0"
                      step="0.1"
                      placeholder="0"
                      {...form.register('length')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="width">Width (cm)</Label>
                    <Input
                      id="width"
                      type="number"
                      min="0"
                      step="0.1"
                      placeholder="0"
                      {...form.register('width')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="height">Height (cm)</Label>
                    <Input
                      id="height"
                      type="number"
                      min="0"
                      step="0.1"
                      placeholder="0"
                      {...form.register('height')}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* SEO */}
            <Card>
              <CardHeader>
                <CardTitle>SEO & Meta</CardTitle>
                <CardDescription>
                  Search engine optimization settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="meta_title">Meta Title</Label>
                  <Input
                    id="meta_title"
                    placeholder="SEO title for search engines"
                    {...form.register('meta_title')}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="meta_description">Meta Description</Label>
                  <Textarea
                    id="meta_description"
                    placeholder="SEO description for search engines"
                    rows={3}
                    {...form.register('meta_description')}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Tags</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a tag and press Enter"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                    />
                    <Button type="button" variant="outline" onClick={handleAddTag}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="gap-1">
                          {tag}
                          <X
                            className="h-3 w-3 cursor-pointer"
                            onClick={() => handleRemoveTag(tag)}
                          />
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <Card>
              <CardHeader>
                <CardTitle>Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="is_active">Active</Label>
                    <p className="text-xs text-muted-foreground">
                      Product visible in catalog
                    </p>
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
                    <p className="text-xs text-muted-foreground">
                      Show in featured section
                    </p>
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
                    <p className="text-xs text-muted-foreground">
                      Installation service needed
                    </p>
                  </div>
                  <Switch
                    id="requires_installation"
                    checked={form.watch('requires_installation')}
                    onCheckedChange={(checked) => form.setValue('requires_installation', checked)}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Warranty */}
            <Card>
              <CardHeader>
                <CardTitle>Warranty</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Label htmlFor="warranty_months">Warranty Period (Months)</Label>
                  <Select
                    defaultValue="12"
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
                </div>
              </CardContent>
            </Card>

            {/* Quick Info */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Tips</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-2">
                <p>- SKU should be unique across all products</p>
                <p>- Selling price cannot exceed MRP</p>
                <p>- Add images after creating the product</p>
                <p>- HSN code is required for GST compliance</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
