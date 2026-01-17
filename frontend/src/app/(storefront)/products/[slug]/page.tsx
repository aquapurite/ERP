'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ChevronRight,
  Star,
  Minus,
  Plus,
  ShoppingCart,
  Heart,
  Share2,
  Truck,
  Shield,
  RotateCcw,
  Package,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import ProductCard from '@/components/storefront/product/product-card';
import PinCodeChecker from '@/components/storefront/product/pincode-checker';
import { ProductReviews } from '@/components/storefront/reviews';
import { StorefrontProduct, ProductVariant } from '@/types/storefront';
import { productsApi, reviewsApi } from '@/lib/storefront/api';
import { useCartStore } from '@/lib/storefront/cart-store';
import { formatCurrency } from '@/lib/utils';

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [product, setProduct] = useState<StorefrontProduct | null>(null);
  const [relatedProducts, setRelatedProducts] = useState<StorefrontProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [reviewSummary, setReviewSummary] = useState<{
    average_rating: number;
    total_reviews: number;
  } | null>(null);

  const addItem = useCartStore((state) => state.addItem);

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      try {
        const data = await productsApi.getBySlug(slug);
        setProduct(data);

        // Set default variant if exists
        if (data.variants && data.variants.length > 0) {
          setSelectedVariant(data.variants[0]);
        }

        // Fetch related products and review summary in parallel
        const [related, summary] = await Promise.all([
          productsApi.getRelated(data.id, data.category_id),
          reviewsApi.getReviewSummary(data.id).catch(() => null),
        ]);
        setRelatedProducts(related);
        if (summary) {
          setReviewSummary(summary);
        }
      } catch (error) {
        console.error('Failed to fetch product:', error);
      } finally {
        setLoading(false);
      }
    };

    if (slug) {
      fetchProduct();
    }
  }, [slug]);

  const handleQuantityChange = (delta: number) => {
    setQuantity((prev) => Math.max(1, Math.min(10, prev + delta)));
  };

  const handleAddToCart = () => {
    if (!product) return;
    addItem(product, quantity, selectedVariant || undefined);
    toast.success('Added to cart!');
  };

  const handleBuyNow = () => {
    if (!product) return;
    addItem(product, quantity, selectedVariant || undefined);
    window.location.href = '/checkout';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Skeleton className="h-6 w-64 mb-6" />
        <div className="grid lg:grid-cols-2 gap-8">
          <Skeleton className="aspect-square rounded-lg" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <Package className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Product Not Found</h2>
        <p className="text-muted-foreground mb-4">
          The product you're looking for doesn't exist.
        </p>
        <Button asChild>
          <Link href="/products">Browse Products</Link>
        </Button>
      </div>
    );
  }

  const images = product.images || [];
  const primaryImage = images.find((img) => img.is_primary) || images[0];
  const currentPrice = selectedVariant?.selling_price || product.selling_price;
  const currentMrp = selectedVariant?.mrp || product.mrp;
  const discountPercentage =
    currentMrp > currentPrice
      ? Math.round(((currentMrp - currentPrice) / currentMrp) * 100)
      : 0;

  // Group specifications by group_name
  const specGroups = (product.specifications || []).reduce((acc, spec) => {
    const group = spec.group_name || 'General';
    if (!acc[group]) acc[group] = [];
    acc[group].push(spec);
    return acc;
  }, {} as Record<string, typeof product.specifications>);

  return (
    <div className="bg-muted/50 min-h-screen">
      <div className="container mx-auto px-4 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
          <Link href="/" className="hover:text-primary">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/products" className="hover:text-primary">
            Products
          </Link>
          {product.category && (
            <>
              <ChevronRight className="h-4 w-4" />
              <Link
                href={`/category/${product.category.slug}`}
                className="hover:text-primary"
              >
                {product.category.name}
              </Link>
            </>
          )}
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground truncate max-w-[200px]">
            {product.name}
          </span>
        </nav>

        {/* Product Section */}
        <div className="bg-card rounded-lg shadow-sm p-6 mb-8">
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Image Gallery */}
            <div className="space-y-4">
              <div className="aspect-square rounded-lg overflow-hidden bg-muted">
                {images.length > 0 ? (
                  <img
                    src={
                      images[selectedImage]?.image_url || primaryImage?.image_url
                    }
                    alt={
                      images[selectedImage]?.alt_text || product.name
                    }
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center">
                    <Package className="h-24 w-24 text-gray-300" />
                  </div>
                )}
              </div>

              {/* Thumbnails */}
              {images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {images.map((image, index) => (
                    <button
                      key={image.id}
                      onClick={() => setSelectedImage(index)}
                      className={`flex-shrink-0 h-20 w-20 rounded-lg overflow-hidden border-2 transition-colors ${
                        selectedImage === index
                          ? 'border-primary'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <img
                        src={image.thumbnail_url || image.image_url}
                        alt={image.alt_text || `${product.name} - ${index + 1}`}
                        className="h-full w-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Product Info */}
            <div className="space-y-6">
              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                {product.is_bestseller && (
                  <Badge className="bg-orange-500">Bestseller</Badge>
                )}
                {product.is_new_arrival && (
                  <Badge className="bg-green-500">New Arrival</Badge>
                )}
                {discountPercentage > 0 && (
                  <Badge variant="destructive">{discountPercentage}% OFF</Badge>
                )}
              </div>

              {/* Brand & Category */}
              <div className="text-sm text-muted-foreground">
                {product.brand?.name && (
                  <span className="font-medium text-primary">
                    {product.brand.name}
                  </span>
                )}
                {product.category?.name && (
                  <>
                    {product.brand?.name && ' • '}
                    {product.category.name}
                  </>
                )}
              </div>

              {/* Title */}
              <h1 className="text-2xl md:text-3xl font-bold">{product.name}</h1>

              {/* Rating */}
              {reviewSummary && reviewSummary.total_reviews > 0 ? (
                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-green-600 text-white px-2 py-0.5 rounded text-sm">
                    <Star className="h-3 w-3 fill-current mr-1" />
                    {reviewSummary.average_rating.toFixed(1)}
                  </div>
                  <span className="text-muted-foreground text-sm">
                    {reviewSummary.total_reviews} Review{reviewSummary.total_reviews !== 1 ? 's' : ''}
                  </span>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  No reviews yet - Be the first to review!
                </div>
              )}

              {/* Price */}
              <div className="space-y-1">
                <div className="flex items-baseline gap-3">
                  <span className="text-3xl font-bold text-primary">
                    {formatCurrency(currentPrice)}
                  </span>
                  {currentMrp > currentPrice && (
                    <>
                      <span className="text-xl text-muted-foreground line-through">
                        {formatCurrency(currentMrp)}
                      </span>
                      <span className="text-green-600 font-medium">
                        Save {formatCurrency(currentMrp - currentPrice)}
                      </span>
                    </>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  Inclusive of all taxes
                </p>
              </div>

              {/* Variants */}
              {product.variants && product.variants.length > 0 && (
                <div>
                  <Label className="text-sm font-semibold mb-2 block">
                    Select Variant
                  </Label>
                  <div className="flex flex-wrap gap-2">
                    {product.variants.map((variant) => (
                      <Button
                        key={variant.id}
                        variant={
                          selectedVariant?.id === variant.id
                            ? 'default'
                            : 'outline'
                        }
                        size="sm"
                        onClick={() => setSelectedVariant(variant)}
                      >
                        {variant.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Quantity */}
              <div>
                <Label className="text-sm font-semibold mb-2 block">
                  Quantity
                </Label>
                <div className="flex items-center gap-3">
                  <div className="flex items-center border rounded-lg">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-10 w-10"
                      onClick={() => handleQuantityChange(-1)}
                      disabled={quantity <= 1}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="w-12 text-center font-medium">
                      {quantity}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-10 w-10"
                      onClick={() => handleQuantityChange(1)}
                      disabled={quantity >= 10}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Delivery Check */}
              <PinCodeChecker productPrice={currentPrice} />

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  size="lg"
                  className="flex-1"
                  onClick={handleAddToCart}
                >
                  <ShoppingCart className="h-5 w-5 mr-2" />
                  Add to Cart
                </Button>
                <Button
                  size="lg"
                  variant="secondary"
                  className="flex-1"
                  onClick={handleBuyNow}
                >
                  Buy Now
                </Button>
                <Button size="lg" variant="outline" className="px-4">
                  <Heart className="h-5 w-5" />
                </Button>
              </div>

              {/* Features */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div className="text-center">
                  <Truck className="h-6 w-6 mx-auto text-primary mb-1" />
                  <p className="text-xs">Free Shipping</p>
                </div>
                <div className="text-center">
                  <Shield className="h-6 w-6 mx-auto text-primary mb-1" />
                  <p className="text-xs">{product.warranty_months || 12}M Warranty</p>
                </div>
                <div className="text-center">
                  <RotateCcw className="h-6 w-6 mx-auto text-primary mb-1" />
                  <p className="text-xs">7 Day Returns</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Product Details Tabs */}
        <div className="bg-card rounded-lg shadow-sm p-6 mb-8">
          <Tabs defaultValue="description">
            <TabsList className="mb-4">
              <TabsTrigger value="description">Description</TabsTrigger>
              <TabsTrigger value="specifications">Specifications</TabsTrigger>
              <TabsTrigger value="reviews">Reviews</TabsTrigger>
            </TabsList>

            <TabsContent value="description" className="space-y-4">
              <h3 className="font-semibold text-lg">Product Description</h3>
              {product.description ? (
                <div
                  className="prose max-w-none text-muted-foreground"
                  dangerouslySetInnerHTML={{ __html: product.description }}
                />
              ) : (
                <p className="text-muted-foreground">
                  {product.short_description || 'No description available.'}
                </p>
              )}

              {product.features && (
                <div className="mt-6">
                  <h4 className="font-semibold mb-3">Key Features</h4>
                  <ul className="space-y-2">
                    {product.features.split('\n').map((feature, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <Check className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </TabsContent>

            <TabsContent value="specifications">
              <h3 className="font-semibold text-lg mb-4">Specifications</h3>
              {Object.keys(specGroups).length > 0 ? (
                <div className="space-y-6">
                  {Object.entries(specGroups).map(([group, specs]) => (
                    <div key={group}>
                      <h4 className="font-medium text-primary mb-2">{group}</h4>
                      <div className="border rounded-lg overflow-hidden">
                        {specs?.map((spec, i) => (
                          <div
                            key={spec.id}
                            className={`flex ${
                              i % 2 === 0 ? 'bg-muted/50' : 'bg-card'
                            }`}
                          >
                            <div className="w-1/3 p-3 font-medium border-r">
                              {spec.key}
                            </div>
                            <div className="w-2/3 p-3">{spec.value}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">
                  No specifications available.
                </p>
              )}
            </TabsContent>

            <TabsContent value="reviews">
              <ProductReviews productId={product.id} productName={product.name} />
            </TabsContent>
          </Tabs>
        </div>

        {/* Related Products */}
        {relatedProducts.length > 0 && (
          <div className="bg-card rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold mb-6">Related Products</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {relatedProducts.slice(0, 4).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <label className={className}>{children}</label>;
}
