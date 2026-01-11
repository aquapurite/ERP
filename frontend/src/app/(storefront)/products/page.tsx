'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ChevronRight, SlidersHorizontal, X, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Skeleton } from '@/components/ui/skeleton';
import ProductCard from '@/components/storefront/product/product-card';
import {
  StorefrontProduct,
  StorefrontCategory,
  StorefrontBrand,
  ProductFilters,
} from '@/types/storefront';
import { productsApi, categoriesApi, brandsApi } from '@/lib/storefront/api';

function ProductsContent() {
  const searchParams = useSearchParams();

  const [products, setProducts] = useState<StorefrontProduct[]>([]);
  const [categories, setCategories] = useState<StorefrontCategory[]>([]);
  const [brands, setBrands] = useState<StorefrontBrand[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalProducts, setTotalProducts] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Filters from URL
  const [filters, setFilters] = useState<ProductFilters>({
    category_id: searchParams.get('category') || undefined,
    brand_id: searchParams.get('brand') || undefined,
    min_price: searchParams.get('min_price')
      ? Number(searchParams.get('min_price'))
      : undefined,
    max_price: searchParams.get('max_price')
      ? Number(searchParams.get('max_price'))
      : undefined,
    is_bestseller: searchParams.get('is_bestseller') === 'true',
    is_new_arrival: searchParams.get('is_new_arrival') === 'true',
    search: searchParams.get('search') || undefined,
    sort_by: (searchParams.get('sort_by') as ProductFilters['sort_by']) || 'created_at',
    sort_order: (searchParams.get('sort_order') as ProductFilters['sort_order']) || 'desc',
    page: 1,
    size: 12,
  });

  useEffect(() => {
    const fetchFiltersData = async () => {
      try {
        const [categoriesData, brandsData] = await Promise.all([
          categoriesApi.list(),
          brandsApi.list(),
        ]);
        setCategories(categoriesData);
        setBrands(brandsData);
      } catch (error) {
        console.error('Failed to fetch filters data:', error);
      }
    };
    fetchFiltersData();
  }, []);

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const data = await productsApi.list({
          ...filters,
          page: currentPage,
        });
        setProducts(data.items || []);
        setTotalProducts(data.total || 0);
      } catch (error) {
        console.error('Failed to fetch products:', error);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [filters, currentPage]);

  const updateFilter = (key: keyof ProductFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      sort_by: 'created_at',
      sort_order: 'desc',
      page: 1,
      size: 12,
    });
    setCurrentPage(1);
  };

  const hasActiveFilters =
    filters.category_id ||
    filters.brand_id ||
    filters.min_price ||
    filters.max_price ||
    filters.is_bestseller ||
    filters.is_new_arrival ||
    filters.search;

  const totalPages = Math.ceil(totalProducts / 12);

  // Filter sidebar content
  const FilterContent = () => (
    <div className="space-y-6">
      {/* Categories */}
      <div>
        <Label className="text-sm font-semibold">Categories</Label>
        <div className="mt-3 space-y-2">
          {categories.map((category) => (
            <div key={category.id} className="flex items-center space-x-2">
              <Checkbox
                id={`cat-${category.id}`}
                checked={filters.category_id === category.id}
                onCheckedChange={(checked) =>
                  updateFilter('category_id', checked ? category.id : undefined)
                }
              />
              <label
                htmlFor={`cat-${category.id}`}
                className="text-sm cursor-pointer"
              >
                {category.name}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Brands */}
      <div>
        <Label className="text-sm font-semibold">Brands</Label>
        <div className="mt-3 space-y-2">
          {brands.map((brand) => (
            <div key={brand.id} className="flex items-center space-x-2">
              <Checkbox
                id={`brand-${brand.id}`}
                checked={filters.brand_id === brand.id}
                onCheckedChange={(checked) =>
                  updateFilter('brand_id', checked ? brand.id : undefined)
                }
              />
              <label
                htmlFor={`brand-${brand.id}`}
                className="text-sm cursor-pointer"
              >
                {brand.name}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div>
        <Label className="text-sm font-semibold">Price Range</Label>
        <div className="mt-3 flex items-center gap-2">
          <Input
            type="number"
            placeholder="Min"
            value={filters.min_price || ''}
            onChange={(e) =>
              updateFilter(
                'min_price',
                e.target.value ? Number(e.target.value) : undefined
              )
            }
            className="h-9"
          />
          <span>-</span>
          <Input
            type="number"
            placeholder="Max"
            value={filters.max_price || ''}
            onChange={(e) =>
              updateFilter(
                'max_price',
                e.target.value ? Number(e.target.value) : undefined
              )
            }
            className="h-9"
          />
        </div>
      </div>

      {/* Product Type */}
      <div>
        <Label className="text-sm font-semibold">Product Type</Label>
        <div className="mt-3 space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="bestseller"
              checked={filters.is_bestseller || false}
              onCheckedChange={(checked) =>
                updateFilter('is_bestseller', checked || undefined)
              }
            />
            <label htmlFor="bestseller" className="text-sm cursor-pointer">
              Bestsellers
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="new-arrival"
              checked={filters.is_new_arrival || false}
              onCheckedChange={(checked) =>
                updateFilter('is_new_arrival', checked || undefined)
              }
            />
            <label htmlFor="new-arrival" className="text-sm cursor-pointer">
              New Arrivals
            </label>
          </div>
        </div>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <Button
          variant="outline"
          className="w-full"
          onClick={clearFilters}
        >
          Clear All Filters
        </Button>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-muted/50">
      <div className="container mx-auto px-4 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
          <Link href="/" className="hover:text-primary">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground">Products</span>
        </nav>

        <div className="flex gap-8">
          {/* Sidebar - Desktop */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-24 bg-card rounded-lg p-6 shadow-sm">
              <h3 className="font-semibold mb-4">Filters</h3>
              <FilterContent />
            </div>
          </aside>

          {/* Main Content */}
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold">
                  {filters.search
                    ? `Search: "${filters.search}"`
                    : 'All Products'}
                </h1>
                <p className="text-muted-foreground">
                  {totalProducts} products found
                </p>
              </div>

              <div className="flex items-center gap-3">
                {/* Mobile Filters */}
                <Sheet
                  open={mobileFiltersOpen}
                  onOpenChange={setMobileFiltersOpen}
                >
                  <SheetTrigger asChild>
                    <Button variant="outline" className="lg:hidden">
                      <SlidersHorizontal className="h-4 w-4 mr-2" />
                      Filters
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="left">
                    <SheetHeader>
                      <SheetTitle>Filters</SheetTitle>
                    </SheetHeader>
                    <div className="mt-6">
                      <FilterContent />
                    </div>
                  </SheetContent>
                </Sheet>

                {/* Sort */}
                <Select
                  value={`${filters.sort_by}-${filters.sort_order}`}
                  onValueChange={(value) => {
                    const [sortBy, sortOrder] = value.split('-');
                    updateFilter('sort_by', sortBy);
                    updateFilter('sort_order', sortOrder);
                  }}
                >
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at-desc">Newest First</SelectItem>
                    <SelectItem value="created_at-asc">Oldest First</SelectItem>
                    <SelectItem value="price-asc">Price: Low to High</SelectItem>
                    <SelectItem value="price-desc">Price: High to Low</SelectItem>
                    <SelectItem value="name-asc">Name: A to Z</SelectItem>
                    <SelectItem value="name-desc">Name: Z to A</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Active Filters */}
            {hasActiveFilters && (
              <div className="flex flex-wrap gap-2 mb-4">
                {filters.search && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => updateFilter('search', undefined)}
                  >
                    Search: {filters.search}
                    <X className="h-3 w-3 ml-1" />
                  </Button>
                )}
                {filters.category_id && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => updateFilter('category_id', undefined)}
                  >
                    Category
                    <X className="h-3 w-3 ml-1" />
                  </Button>
                )}
                {filters.brand_id && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => updateFilter('brand_id', undefined)}
                  >
                    Brand
                    <X className="h-3 w-3 ml-1" />
                  </Button>
                )}
              </div>
            )}

            {/* Products Grid */}
            {loading ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="space-y-3">
                    <Skeleton className="aspect-square rounded-lg" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-6 w-1/3" />
                  </div>
                ))}
              </div>
            ) : products.length === 0 ? (
              <div className="text-center py-16">
                <Package className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No products found</h3>
                <p className="text-muted-foreground mb-4">
                  Try adjusting your filters or search terms
                </p>
                <Button onClick={clearFilters}>Clear Filters</Button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-center gap-2 mt-8">
                    <Button
                      variant="outline"
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage((p) => p - 1)}
                    >
                      Previous
                    </Button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }).map(
                        (_, i) => {
                          const page = i + 1;
                          return (
                            <Button
                              key={page}
                              variant={
                                currentPage === page ? 'default' : 'outline'
                              }
                              size="icon"
                              onClick={() => setCurrentPage(page)}
                            >
                              {page}
                            </Button>
                          );
                        }
                      )}
                    </div>
                    <Button
                      variant="outline"
                      disabled={currentPage === totalPages}
                      onClick={() => setCurrentPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-6">
          <Skeleton className="h-8 w-48 mb-6" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="aspect-square rounded-lg" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-6 w-1/3" />
              </div>
            ))}
          </div>
        </div>
      }
    >
      <ProductsContent />
    </Suspense>
  );
}
