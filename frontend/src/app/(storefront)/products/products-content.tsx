'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Filter, Grid3X3, List, X, Droplets,
  MapPin, Loader2, ShoppingCart, Shield
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { productsApi } from '@/lib/api';
import { formatCurrency, cn } from '@/lib/utils';
import { useCart } from '@/contexts/cart-context';
import { toast } from 'sonner';
import { ProductCardSkeleton } from './products-skeleton';

interface ProductsContentProps {
  initialProducts: any[];
  initialCategories: any[];
}

// Product card - Dark Theme
function ProductCard({ product, onAddToCart }: { product: any; onAddToCart: (product: any) => Promise<boolean> }) {
  const [isAdding, setIsAdding] = useState(false);

  const discount = product.mrp > product.selling_price
    ? Math.round(((product.mrp - product.selling_price) / product.mrp) * 100)
    : 0;

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    setIsAdding(true);

    const success = await onAddToCart(product);

    if (success) {
      toast.success('Added to cart');
    }

    setIsAdding(false);
  };

  return (
    <Card className="group overflow-hidden bg-slate-800/50 border-slate-700 hover:border-amber-500/50 hover:shadow-lg hover:shadow-amber-500/10 transition-all duration-300">
      <Link href={`/products/${product.slug || product.id}`}>
        <div className="aspect-square relative bg-slate-900 overflow-hidden">
          {product.images?.[0]?.url ? (
            <Image
              src={product.images[0].url}
              alt={product.name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
              <Droplets className="h-16 w-16 text-amber-500/30" />
            </div>
          )}
          {discount > 0 && (
            <Badge className="absolute top-3 left-3 bg-red-500 text-white border-0">
              {discount}% OFF
            </Badge>
          )}
          {product.is_bestseller && (
            <Badge className="absolute top-3 right-3 bg-amber-500 text-slate-900 border-0">
              Bestseller
            </Badge>
          )}
          {product.is_new_arrival && !product.is_bestseller && (
            <Badge className="absolute top-3 right-3 bg-emerald-500 text-white border-0">
              New
            </Badge>
          )}
          {/* Quick add button */}
          <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              size="sm"
              className="w-full bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
              onClick={handleAddToCart}
              disabled={isAdding}
            >
              {isAdding ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  Add to Cart
                </>
              )}
            </Button>
          </div>
        </div>
        <CardContent className="p-4">
          <p className="text-xs text-slate-500 mb-1">{product.category?.name || 'Water Purifier'}</p>
          <h3 className="font-medium text-white line-clamp-2 mb-2 group-hover:text-amber-500 transition-colors min-h-[2.5rem]">
            {product.name}
          </h3>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-xl font-bold text-amber-500">
              {formatCurrency(product.selling_price)}
            </span>
            {discount > 0 && (
              <span className="text-sm text-slate-500 line-through">
                {formatCurrency(product.mrp)}
              </span>
            )}
          </div>
          {product.warranty_months && (
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <Shield className="h-3 w-3" />
              {product.warranty_months} months warranty
            </p>
          )}
        </CardContent>
      </Link>
    </Card>
  );
}

// Filter sidebar - Dark Theme
function FilterContent({
  categories,
  selectedCategory,
  setSelectedCategory,
  priceRange,
  setPriceRange,
  onlyInStock,
  setOnlyInStock,
  onReset,
}: {
  categories: any[];
  selectedCategory: string;
  setSelectedCategory: (v: string) => void;
  priceRange: [number, number];
  setPriceRange: (v: [number, number]) => void;
  onlyInStock: boolean;
  setOnlyInStock: (v: boolean) => void;
  onReset: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-white">Filters</h3>
        <Button variant="ghost" size="sm" onClick={onReset} className="text-amber-500 hover:text-amber-400 hover:bg-slate-700">
          Reset
        </Button>
      </div>

      <Accordion type="multiple" defaultValue={['category', 'price', 'availability']} className="space-y-2">
        <AccordionItem value="category" className="border-slate-700">
          <AccordionTrigger className="text-white hover:text-amber-500">Category</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={selectedCategory === 'all'}
                  onCheckedChange={() => setSelectedCategory('all')}
                  className="border-slate-600 data-[state=checked]:bg-amber-500 data-[state=checked]:border-amber-500"
                />
                <span className="text-sm text-slate-300">All Categories</span>
              </label>
              {categories.map((cat) => (
                <label key={cat.id} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={selectedCategory === cat.id}
                    onCheckedChange={() => setSelectedCategory(cat.id)}
                    className="border-slate-600 data-[state=checked]:bg-amber-500 data-[state=checked]:border-amber-500"
                  />
                  <span className="text-sm text-slate-300">{cat.name}</span>
                </label>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="price" className="border-slate-700">
          <AccordionTrigger className="text-white hover:text-amber-500">Price Range</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4 px-1">
              <Slider
                min={0}
                max={50000}
                step={1000}
                value={priceRange}
                onValueChange={(v) => setPriceRange(v as [number, number])}
                className="[&_[role=slider]]:bg-amber-500"
              />
              <div className="flex justify-between text-sm text-slate-400">
                <span>{formatCurrency(priceRange[0])}</span>
                <span>{formatCurrency(priceRange[1])}</span>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="availability" className="border-slate-700">
          <AccordionTrigger className="text-white hover:text-amber-500">Availability</AccordionTrigger>
          <AccordionContent>
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={onlyInStock}
                onCheckedChange={(checked) => setOnlyInStock(!!checked)}
                className="border-slate-600 data-[state=checked]:bg-amber-500 data-[state=checked]:border-amber-500"
              />
              <span className="text-sm text-slate-300">In Stock Only</span>
            </label>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

export default function ProductsContent({ initialProducts, initialCategories }: ProductsContentProps) {
  const searchParams = useSearchParams();
  const { addItem } = useCart();
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('relevance');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || 'all');
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 50000]);
  const [onlyInStock, setOnlyInStock] = useState(false);
  const [pincode, setPincode] = useState('');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const categories = initialCategories;

  // Fetch products with filters (client-side for interactivity)
  const { data: productsData, isLoading } = useQuery({
    queryKey: ['products', selectedCategory, priceRange, sortBy, onlyInStock],
    queryFn: async () => {
      try {
        const params: any = {
          is_active: true,
          size: 50,
        };

        if (selectedCategory !== 'all') {
          params.category_id = selectedCategory;
        }
        if (priceRange[0] > 0) {
          params.min_price = priceRange[0];
        }
        if (priceRange[1] < 50000) {
          params.max_price = priceRange[1];
        }
        if (sortBy === 'price_low') {
          params.sort_by = 'selling_price';
          params.sort_order = 'asc';
        } else if (sortBy === 'price_high') {
          params.sort_by = 'selling_price';
          params.sort_order = 'desc';
        } else if (sortBy === 'newest') {
          params.sort_by = 'created_at';
          params.sort_order = 'desc';
        }

        const response = await productsApi.list(params);
        return response.items || [];
      } catch {
        return initialProducts;
      }
    },
    initialData: initialProducts,
    staleTime: 60000, // 1 minute
  });

  const products = productsData || initialProducts;

  const resetFilters = () => {
    setSelectedCategory('all');
    setPriceRange([0, 50000]);
    setOnlyInStock(false);
  };

  const activeFiltersCount = [
    selectedCategory !== 'all',
    priceRange[0] > 0 || priceRange[1] < 50000,
    onlyInStock,
  ].filter(Boolean).length;

  // Phase 2: Add to cart with stock verification
  const handleAddToCart = async (product: any): Promise<boolean> => {
    try {
      // Phase 2: Verify stock before adding to cart
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/inventory/verify-stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: product.id,
          quantity: 1,
          pincode: pincode || undefined,
        }),
      });

      if (response.ok) {
        const stockData = await response.json();
        if (!stockData.in_stock) {
          toast.error(stockData.message || 'Product out of stock');
          return false;
        }
      }
      // If API fails, proceed anyway (graceful degradation)
    } catch (error) {
      console.warn('Stock verification failed, proceeding with add to cart');
    }

    // Add to cart
    addItem({
      id: product.id,
      productId: product.id,
      name: product.name,
      slug: product.slug || product.id,
      sku: product.sku,
      image: product.images?.[0]?.url,
      price: product.selling_price,
      mrp: product.mrp,
    });

    return true;
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Breadcrumb & Header */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="container mx-auto px-4 py-6">
          <div className="text-sm text-slate-400 mb-2">
            <Link href="/" className="hover:text-amber-500 transition-colors">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-white">Products</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">
            Water Purifiers & Accessories
          </h1>
          <p className="text-slate-400 mt-1">
            {products.length} products available
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="flex gap-8">
          {/* Sidebar - Desktop */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-24 bg-slate-800/50 rounded-xl border border-slate-700 p-4">
              <FilterContent
                categories={categories}
                selectedCategory={selectedCategory}
                setSelectedCategory={setSelectedCategory}
                priceRange={priceRange}
                setPriceRange={setPriceRange}
                onlyInStock={onlyInStock}
                setOnlyInStock={setOnlyInStock}
                onReset={resetFilters}
              />

              {/* PIN Code Check */}
              <div className="mt-6 pt-6 border-t border-slate-700">
                <h3 className="font-semibold mb-3 flex items-center gap-2 text-white">
                  <MapPin className="h-4 w-4 text-amber-500" />
                  Check Delivery
                </h3>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    placeholder="PIN code"
                    maxLength={6}
                    value={pincode}
                    onChange={(e) => setPincode(e.target.value.replace(/\D/g, ''))}
                    className="flex-1 bg-slate-900 border-slate-600 text-white placeholder:text-slate-400 focus:border-amber-500"
                  />
                  <Button size="sm" variant="outline" disabled={pincode.length !== 6} className="border-slate-600 text-slate-300 hover:text-amber-500 hover:border-amber-500">
                    Check
                  </Button>
                </div>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            {/* Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6 bg-slate-800/50 rounded-xl border border-slate-700 p-4">
              <div className="flex items-center gap-2">
                {/* Mobile filter button */}
                <Sheet open={isFilterOpen} onOpenChange={setIsFilterOpen}>
                  <SheetTrigger asChild>
                    <Button variant="outline" size="sm" className="lg:hidden border-slate-600 text-slate-300 hover:text-amber-500 hover:border-amber-500">
                      <Filter className="h-4 w-4 mr-2" />
                      Filters
                      {activeFiltersCount > 0 && (
                        <Badge className="ml-2 bg-amber-500 text-slate-900">{activeFiltersCount}</Badge>
                      )}
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="left" className="bg-slate-900 border-slate-800">
                    <SheetHeader>
                      <SheetTitle className="text-white">Filters</SheetTitle>
                    </SheetHeader>
                    <div className="mt-6">
                      <FilterContent
                        categories={categories}
                        selectedCategory={selectedCategory}
                        setSelectedCategory={setSelectedCategory}
                        priceRange={priceRange}
                        setPriceRange={setPriceRange}
                        onlyInStock={onlyInStock}
                        setOnlyInStock={setOnlyInStock}
                        onReset={resetFilters}
                      />
                    </div>
                  </SheetContent>
                </Sheet>

                {/* Active filters */}
                {activeFiltersCount > 0 && (
                  <div className="hidden md:flex items-center gap-2">
                    {selectedCategory !== 'all' && (
                      <Badge className="gap-1 bg-slate-700 text-slate-300 hover:bg-slate-600">
                        {categories.find((c: any) => c.id === selectedCategory)?.name}
                        <button onClick={() => setSelectedCategory('all')}>
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    )}
                    {(priceRange[0] > 0 || priceRange[1] < 50000) && (
                      <Badge className="gap-1 bg-slate-700 text-slate-300 hover:bg-slate-600">
                        {formatCurrency(priceRange[0])} - {formatCurrency(priceRange[1])}
                        <button onClick={() => setPriceRange([0, 50000])}>
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                {/* Sort */}
                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="w-[160px] bg-slate-900 border-slate-600 text-white">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="relevance" className="text-slate-300 focus:text-white focus:bg-slate-700">Relevance</SelectItem>
                    <SelectItem value="price_low" className="text-slate-300 focus:text-white focus:bg-slate-700">Price: Low to High</SelectItem>
                    <SelectItem value="price_high" className="text-slate-300 focus:text-white focus:bg-slate-700">Price: High to Low</SelectItem>
                    <SelectItem value="newest" className="text-slate-300 focus:text-white focus:bg-slate-700">Newest First</SelectItem>
                  </SelectContent>
                </Select>

                {/* View toggle */}
                <div className="hidden sm:flex border border-slate-700 rounded-lg">
                  <Button
                    variant={view === 'grid' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setView('grid')}
                    className={view === 'grid' ? 'bg-slate-700 text-amber-500' : 'text-slate-400 hover:text-white'}
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={view === 'list' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setView('list')}
                    className={view === 'list' ? 'bg-slate-700 text-amber-500' : 'text-slate-400 hover:text-white'}
                  >
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Products Grid */}
            {isLoading ? (
              <div className={cn(
                "grid gap-6",
                view === 'grid' ? "grid-cols-2 md:grid-cols-3" : "grid-cols-1"
              )}>
                {[...Array(6)].map((_, i) => <ProductCardSkeleton key={i} />)}
              </div>
            ) : products.length > 0 ? (
              <div className={cn(
                "grid gap-6",
                view === 'grid' ? "grid-cols-2 md:grid-cols-3" : "grid-cols-1"
              )}>
                {products.map((product: any) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onAddToCart={handleAddToCart}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-16 bg-slate-800/50 rounded-xl border border-slate-700">
                <Droplets className="h-16 w-16 mx-auto mb-4 text-slate-600" />
                <h3 className="text-xl font-semibold text-white mb-2">No products found</h3>
                <p className="text-slate-400 mb-6">Try adjusting your filters or search criteria</p>
                <Button onClick={resetFilters} variant="outline" className="border-amber-500 text-amber-500 hover:bg-amber-500 hover:text-slate-900">
                  Reset Filters
                </Button>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
