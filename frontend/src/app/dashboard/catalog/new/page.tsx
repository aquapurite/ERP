'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Save, Package, Loader2, Plus, X, Upload, ImagePlus, Trash2, Lock, Sparkles } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
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
import { productsApi, categoriesApi, brandsApi, uploadsApi } from '@/lib/api';
import apiClient from '@/lib/api/client';
import { Category, Brand } from '@/types';

// Image preview type
interface ImagePreview {
  file: File;
  preview: string;
  isPrimary: boolean;
}

// Item type options
const ITEM_TYPES = [
  { value: 'FG', label: 'Finished Goods', description: 'Complete products like Water Purifiers' },
  { value: 'SP', label: 'Spare Parts', description: 'Replacement parts, filters, membranes' },
] as const;

const productSchema = z.object({
  name: z.string().min(2, 'Product name must be at least 2 characters'),
  sku: z.string().min(2, 'SKU must be at least 2 characters').regex(/^[A-Za-z0-9-_]+$/, 'SKU can only contain letters, numbers, hyphens, and underscores'),
  slug: z.string().optional(),
  description: z.string().optional(),
  brand_id: z.string().min(1, 'Brand is required'),
  category_id: z.string().min(1, 'Category is required'),
  item_type: z.enum(['FG', 'SP']).default('FG'),
  model_code: z.string().min(1, 'Model name is required').max(5, 'Model name must be 5 characters or less').regex(/^[A-Za-z]+$/, 'Model name must contain only letters'),
  mrp: z.coerce.number().min(0, 'MRP must be positive'),
  selling_price: z.coerce.number().min(0, 'Selling price must be positive').optional(),
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
});

type ProductFormData = z.infer<typeof productSchema>;

// API for SKU generation
const skuApi = {
  getNextSku: async (brandId: string, categoryId: string, itemType: string, modelCode: string) => {
    const { data } = await apiClient.get('/products/next-sku', {
      params: { brand_id: brandId, category_id: categoryId, item_type: itemType, model_code: modelCode }
    });
    return data;
  },
};

export default function NewProductPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [images, setImages] = useState<ImagePreview[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSkuGenerated, setIsSkuGenerated] = useState(false);
  const [isGeneratingSku, setIsGeneratingSku] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cascading category state
  const [selectedParentCategoryId, setSelectedParentCategoryId] = useState<string>('');

  // Fetch brands
  const { data: brandsData } = useQuery({
    queryKey: ['brands'],
    queryFn: () => brandsApi.list({ size: 100 }),
  });

  // Fetch root categories (parent_id IS NULL)
  const { data: rootCategoriesData } = useQuery({
    queryKey: ['categories-roots'],
    queryFn: () => categoriesApi.getRoots(),
  });

  // Fetch subcategories when parent is selected
  const { data: subcategoriesData } = useQuery({
    queryKey: ['categories-children', selectedParentCategoryId],
    queryFn: () => categoriesApi.getChildren(selectedParentCategoryId),
    enabled: !!selectedParentCategoryId,
  });

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema) as any,
    defaultValues: {
      name: '',
      sku: '',
      slug: '',
      description: '',
      brand_id: '',
      category_id: '',
      item_type: 'FG',
      model_code: '',
      mrp: 0,
      selling_price: 0,
      gst_rate: 18,
      warranty_months: 12,
      is_active: true,
      is_featured: false,
      requires_installation: false,
      tags: [],
    },
  });

  // Watch for hierarchy field changes to auto-generate SKU
  const watchBrandId = form.watch('brand_id');
  const watchCategoryId = form.watch('category_id');
  const watchItemType = form.watch('item_type');
  const watchModelCode = form.watch('model_code');

  // Auto-generate SKU when all hierarchy fields are filled (including model_code)
  useEffect(() => {
    const generateSku = async () => {
      // Need all 4 fields: brand, category, item type, and model code
      if (watchBrandId && watchCategoryId && watchItemType && watchModelCode && watchModelCode.length >= 1) {
        setIsGeneratingSku(true);
        try {
          const result = await skuApi.getNextSku(watchBrandId, watchCategoryId, watchItemType, watchModelCode);
          form.setValue('sku', result.sku);
          // Also store the model_code in the form (already uppercase from API)
          form.setValue('model_code', result.model_code);
          setIsSkuGenerated(true);
        } catch (error) {
          console.error('Failed to generate SKU:', error);
          // Don't show error - user can still enter manually
          setIsSkuGenerated(false);
        } finally {
          setIsGeneratingSku(false);
        }
      } else {
        // Reset SKU if model code is cleared
        if (!watchModelCode) {
          setIsSkuGenerated(false);
        }
      }
    };

    generateSku();
  }, [watchBrandId, watchCategoryId, watchItemType, watchModelCode, form]);

  const createMutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      // Transform frontend field names to backend field names
      const { weight, length, width, height, requires_installation, tags: formTags, ...rest } = data;
      const backendData = {
        ...rest,
        dead_weight_kg: weight,
        length_cm: length,
        width_cm: width,
        height_cm: height,
        // Store tags in extra_data since backend doesn't have a tags field
        extra_data: tags.length > 0 ? { tags } : undefined,
      };

      // Debug: log what we're sending
      console.log('Creating product with data:', JSON.stringify(backendData, null, 2));

      const product = await productsApi.create(backendData);

      if (images.length > 0) {
        setIsUploading(true);
        try {
          for (let i = 0; i < images.length; i++) {
            const img = images[i];
            const uploadResult = await uploadsApi.uploadImage(img.file, 'products');
            await productsApi.addImage(product.id, {
              image_url: uploadResult.url,
              thumbnail_url: uploadResult.thumbnail_url,
              alt_text: data.name,
              is_primary: img.isPrimary || i === 0,
              sort_order: i,
            });
          }
        } catch (uploadError) {
          console.error('Image upload error:', uploadError);
          toast.warning('Product created but some images failed to upload');
        } finally {
          setIsUploading(false);
        }
      }

      return product;
    },
    onSuccess: () => {
      toast.success('Product created successfully');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      router.push('/dashboard/catalog');
    },
    onError: (error: any) => {
      // Extract actual error message from API response
      const apiError = error?.response?.data?.detail;
      const errorMessage = typeof apiError === 'string'
        ? apiError
        : Array.isArray(apiError)
          ? apiError.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join(', ')
          : error.message || 'Failed to create product';

      console.error('Product creation failed:', error?.response?.data || error);
      toast.error(errorMessage);
    },
  });

  const onSubmit = (data: ProductFormData) => {
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

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newImages: ImagePreview[] = [];
    const maxImages = 10;
    const remainingSlots = maxImages - images.length;

    if (files.length > remainingSlots) {
      toast.warning(`You can only add ${remainingSlots} more images (max ${maxImages})`);
    }

    const filesToProcess = Array.from(files).slice(0, remainingSlots);

    filesToProcess.forEach((file) => {
      if (!file.type.startsWith('image/')) {
        toast.error(`${file.name} is not an image file`);
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        toast.error(`${file.name} is too large (max 5MB)`);
        return;
      }

      const preview = URL.createObjectURL(file);
      newImages.push({
        file,
        preview,
        isPrimary: images.length === 0 && newImages.length === 0,
      });
    });

    setImages([...images, ...newImages]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveImage = (index: number) => {
    const newImages = [...images];
    URL.revokeObjectURL(newImages[index].preview);
    newImages.splice(index, 1);
    if (images[index].isPrimary && newImages.length > 0) {
      newImages[0].isPrimary = true;
    }
    setImages(newImages);
  };

  const handleSetPrimary = (index: number) => {
    const newImages = images.map((img, i) => ({
      ...img,
      isPrimary: i === index,
    }));
    setImages(newImages);
  };

  // Handle parent category change - reset subcategory selection
  const handleParentCategoryChange = (parentId: string) => {
    setSelectedParentCategoryId(parentId);
    form.setValue('category_id', '');
    setIsSkuGenerated(false);
  };

  const brands = brandsData?.items || [];
  const rootCategories = rootCategoriesData?.items || [];
  const subcategories = subcategoriesData?.items || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Add New Product"
        description="Create a new product in your catalog"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href="/dashboard/catalog">
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
            {/* Step 1: Product Classification (NEW ORDER) */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Product Classification
                </CardTitle>
                <CardDescription>
                  Select brand, product line, subcategory, item type, and model name. SKU will be auto-generated.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Step 1: Brand Selection */}
                <div className="space-y-2">
                  <Label htmlFor="brand">Step 1: Brand *</Label>
                  <Select
                    value={form.watch('brand_id')}
                    onValueChange={(value) => {
                      form.setValue('brand_id', value);
                      setIsSkuGenerated(false);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select brand" />
                    </SelectTrigger>
                    <SelectContent>
                      {brands.map((brand: Brand) => (
                        <SelectItem key={brand.id} value={brand.id}>
                          {brand.code && <span className="font-mono text-muted-foreground mr-2">[{brand.code}]</span>}
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {form.formState.errors.brand_id && (
                    <p className="text-sm text-destructive">{form.formState.errors.brand_id.message}</p>
                  )}
                </div>

                {/* Step 2: Product Line (Parent Category) */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="parent_category">Step 2: Product Line *</Label>
                    <Select
                      value={selectedParentCategoryId}
                      onValueChange={handleParentCategoryChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select product line" />
                      </SelectTrigger>
                      <SelectContent>
                        {rootCategories.map((category: Category) => (
                          <SelectItem key={category.id} value={category.id}>
                            {category.code && <span className="font-mono text-muted-foreground mr-2">[{category.code}]</span>}
                            {category.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      E.g., Water Purifiers, Air Purifiers
                    </p>
                  </div>

                  {/* Step 3: Subcategory */}
                  <div className="space-y-2">
                    <Label htmlFor="category">Step 3: Subcategory *</Label>
                    <Select
                      value={form.watch('category_id')}
                      onValueChange={(value) => {
                        form.setValue('category_id', value);
                        setIsSkuGenerated(false);
                      }}
                      disabled={!selectedParentCategoryId}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={selectedParentCategoryId ? "Select subcategory" : "Select product line first"} />
                      </SelectTrigger>
                      <SelectContent>
                        {subcategories.map((category: Category) => (
                          <SelectItem key={category.id} value={category.id}>
                            {category.code && <span className="font-mono text-muted-foreground mr-2">[{category.code}]</span>}
                            {category.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {form.formState.errors.category_id && (
                      <p className="text-sm text-destructive">{form.formState.errors.category_id.message}</p>
                    )}
                  </div>
                </div>

                {/* Step 4: Item Type Selection */}
                <div className="space-y-2">
                  <Label>Step 4: Item Type *</Label>
                  <div className="flex gap-4">
                    {ITEM_TYPES.map((type) => (
                      <div
                        key={type.value}
                        className={`flex-1 cursor-pointer rounded-lg border-2 p-4 transition-colors ${
                          form.watch('item_type') === type.value
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                        onClick={() => {
                          form.setValue('item_type', type.value);
                          setIsSkuGenerated(false);
                        }}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`h-4 w-4 rounded-full border-2 ${
                            form.watch('item_type') === type.value
                              ? 'border-primary bg-primary'
                              : 'border-muted-foreground'
                          }`}>
                            {form.watch('item_type') === type.value && (
                              <div className="h-full w-full rounded-full bg-primary" />
                            )}
                          </div>
                          <span className="font-medium">{type.label}</span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {type.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Step 5: Model Name */}
                <div className="space-y-2">
                  <Label htmlFor="model_code">Step 5: Model Name * (for SKU)</Label>
                  <Input
                    id="model_code"
                    placeholder="e.g., ELITZ, REGAL, PRIME"
                    maxLength={5}
                    {...form.register('model_code', {
                      onChange: (e) => {
                        // Uppercase and remove non-letters
                        const value = e.target.value.toUpperCase().replace(/[^A-Z]/g, '');
                        form.setValue('model_code', value);
                        setIsSkuGenerated(false);
                      }
                    })}
                    className="font-mono uppercase"
                  />
                  {form.formState.errors.model_code && (
                    <p className="text-sm text-destructive">{form.formState.errors.model_code.message}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    1-5 letters for model identification in SKU (e.g., ELITZ → AP-WP-RU-FG-ELITZ-001)
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Step 2: Product Details */}
            <Card>
              <CardHeader>
                <CardTitle>Product Details</CardTitle>
                <CardDescription>
                  Enter product name and other details. SKU is auto-generated based on classification.
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
                    <Label htmlFor="sku" className="flex items-center gap-2">
                      SKU (Auto-Generated)
                      {isSkuGenerated && <Sparkles className="h-4 w-4 text-green-500" />}
                    </Label>
                    <div className="relative">
                      <Input
                        id="sku"
                        placeholder={isGeneratingSku ? "Generating..." : "Select classification to generate"}
                        {...form.register('sku')}
                        readOnly={isSkuGenerated}
                        className={isSkuGenerated ? "bg-muted font-mono" : ""}
                      />
                      {isGeneratingSku && (
                        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                      )}
                    </div>
                    {form.formState.errors.sku && (
                      <p className="text-sm text-destructive">{form.formState.errors.sku.message}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {isSkuGenerated
                        ? "SKU auto-generated: Brand-Category-SubCat-ItemType-Model-Sequence"
                        : "Complete all 5 steps above to auto-generate SKU"}
                    </p>
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
              </CardContent>
            </Card>

            {/* Product Images */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImagePlus className="h-5 w-5" />
                  Product Images
                </CardTitle>
                <CardDescription>
                  Upload product images. First image will be the primary image. You can add up to 10 images.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleImageSelect}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={images.length >= 10}
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Images
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    {images.length}/10 images
                  </span>
                </div>

                {images.length > 0 ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                    {images.map((img, index) => (
                      <div
                        key={index}
                        className={`relative group rounded-lg border-2 overflow-hidden ${
                          img.isPrimary ? 'border-primary' : 'border-border'
                        }`}
                      >
                        <div className="aspect-square relative">
                          <Image
                            src={img.preview}
                            alt={`Preview ${index + 1}`}
                            fill
                            className="object-cover"
                          />
                        </div>
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          {!img.isPrimary && (
                            <Button
                              type="button"
                              size="sm"
                              variant="secondary"
                              onClick={() => handleSetPrimary(index)}
                            >
                              Set Primary
                            </Button>
                          )}
                          <Button
                            type="button"
                            size="icon"
                            variant="destructive"
                            onClick={() => handleRemoveImage(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        {img.isPrimary && (
                          <Badge className="absolute top-2 left-2" variant="default">
                            Primary
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="border-2 border-dashed rounded-lg p-8 text-center">
                    <ImagePlus className="mx-auto h-12 w-12 text-muted-foreground" />
                    <p className="mt-2 text-sm text-muted-foreground">
                      Click "Upload Images" to add product photos
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Supports JPEG, PNG, WebP (max 5MB each)
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Pricing & Tax */}
            <Card>
              <CardHeader>
                <CardTitle>Pricing & Tax</CardTitle>
                <CardDescription>
                  Set the MRP and tax information. Channel-specific selling prices can be configured after creation.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="mrp">Maximum Retail Price (MRP) *</Label>
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
                    <p className="text-xs text-muted-foreground">
                      The maximum price at which the product can be sold
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="hsn_code">HSN Code</Label>
                    <Input
                      id="hsn_code"
                      placeholder="Enter HSN code"
                      {...form.register('hsn_code')}
                    />
                    <p className="text-xs text-muted-foreground">
                      Required for GST compliance
                    </p>
                  </div>
                </div>

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
                    <Label htmlFor="cost_price" className="flex items-center gap-2">
                      Cost Price (COGS)
                      <Lock className="h-3 w-3 text-muted-foreground" />
                    </Label>
                    <div className="relative">
                      <Input
                        id="cost_price"
                        type="text"
                        value="****"
                        disabled
                        className="bg-muted cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Auto-calculated from Purchase Orders
                    </p>
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    <strong>Note:</strong> Selling prices for different channels (D2C, B2B, Marketplace)
                    can be configured in the Channel Pricing section after creating the product.
                    Cost price is auto-calculated from Purchase Orders using weighted average method.
                  </p>
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
                <p>1. Select Brand, Product Line, Subcategory</p>
                <p>2. Choose Item Type (FG/SP)</p>
                <p>3. Enter Model Name (1-5 letters)</p>
                <p>4. SKU auto-generates with model name</p>
                <p>5. HSN code is required for GST compliance</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
