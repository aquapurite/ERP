'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ShoppingCart, Heart, Share2, Truck, Shield, Award, CheckCircle,
  Loader2, MapPin, Clock, Minus, Plus, ChevronRight, Star, Package
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { productsApi } from '@/lib/api';
import { formatCurrency, cn } from '@/lib/utils';
import { useCart } from '@/contexts/cart-context';
import { toast } from 'sonner';

// Serviceability checker component
function ServiceabilityChecker({ productId }: { productId: string }) {
  const { deliveryPincode, setDelivery } = useCart();
  const [pincode, setPincode] = useState(deliveryPincode);
  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState<{
    isServiceable: boolean;
    deliveryDays: number;
    shippingCost: number;
    codAvailable: boolean;
    estimatedDate: string;
  } | null>(null);

  const checkServiceability = async () => {
    if (pincode.length !== 6) return;

    setIsChecking(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/serviceability/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pincode,
          channel_code: 'D2C',
          product_ids: [productId],
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const deliveryDate = new Date();
        deliveryDate.setDate(deliveryDate.getDate() + (data.estimated_delivery_days || 5));

        const resultData = {
          isServiceable: data.is_serviceable,
          deliveryDays: data.estimated_delivery_days || 5,
          shippingCost: data.minimum_shipping_cost || 0,
          codAvailable: data.cod_available || false,
          estimatedDate: deliveryDate.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }),
        };

        setResult(resultData);
        setDelivery(pincode, resultData.isServiceable, resultData.estimatedDate, resultData.shippingCost);
      } else {
        // Fallback
        const deliveryDate = new Date();
        deliveryDate.setDate(deliveryDate.getDate() + 3);
        const resultData = {
          isServiceable: true,
          deliveryDays: 3,
          shippingCost: pincode.startsWith('11') ? 0 : 99,
          codAvailable: true,
          estimatedDate: deliveryDate.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }),
        };
        setResult(resultData);
        setDelivery(pincode, true, resultData.estimatedDate, resultData.shippingCost);
      }
    } catch {
      // Demo fallback
      const deliveryDate = new Date();
      deliveryDate.setDate(deliveryDate.getDate() + 3);
      setResult({
        isServiceable: pincode.length === 6,
        deliveryDays: 3,
        shippingCost: 99,
        codAvailable: true,
        estimatedDate: deliveryDate.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }),
      });
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-medium mb-3 flex items-center gap-2">
        <MapPin className="h-4 w-4 text-blue-600" />
        Check Delivery
      </h3>
      <div className="flex gap-2 mb-3">
        <Input
          type="text"
          placeholder="Enter PIN code"
          maxLength={6}
          value={pincode}
          onChange={(e) => {
            setPincode(e.target.value.replace(/\D/g, ''));
            setResult(null);
          }}
          className="flex-1"
        />
        <Button
          onClick={checkServiceability}
          disabled={pincode.length !== 6 || isChecking}
          variant="outline"
        >
          {isChecking ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Check'}
        </Button>
      </div>

      {result && (
        <div className={cn(
          "p-3 rounded-lg text-sm",
          result.isServiceable ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"
        )}>
          {result.isServiceable ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-green-700 font-medium">
                <CheckCircle className="h-4 w-4" />
                Delivery available to {pincode}
              </div>
              <div className="flex items-center gap-4 text-gray-600">
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  <span>Get it by <strong>{result.estimatedDate}</strong></span>
                </div>
              </div>
              <div className="flex items-center gap-1 text-gray-600">
                <Truck className="h-4 w-4" />
                <span>{result.shippingCost === 0 ? 'FREE Delivery' : `Delivery: ₹${result.shippingCost}`}</span>
              </div>
              {result.codAvailable && (
                <Badge variant="outline" className="text-xs">Cash on Delivery Available</Badge>
              )}
            </div>
          ) : (
            <div className="text-red-700">
              Sorry, we don't deliver to PIN code {pincode} currently.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Image gallery component
function ImageGallery({ images, productName }: { images: any[]; productName: string }) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Normalize images to have consistent 'url' property (handle both 'url' and 'image_url')
  const normalizedImages = images?.map(img => ({
    ...img,
    url: img.url || img.image_url
  })) || [];

  const displayImages = normalizedImages.length > 0 ? normalizedImages : [{ url: null }];

  return (
    <div className="space-y-4">
      {/* Main image */}
      <div className="aspect-square relative bg-gray-100 rounded-xl overflow-hidden">
        {displayImages[selectedIndex]?.url ? (
          <Image
            src={displayImages[selectedIndex].url}
            alt={productName}
            fill
            className="object-contain"
            priority
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-100 to-cyan-50">
            <span className="text-8xl">💧</span>
          </div>
        )}
      </div>

      {/* Thumbnails */}
      {displayImages.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {displayImages.map((img: any, i: number) => (
            <button
              key={i}
              onClick={() => setSelectedIndex(i)}
              className={cn(
                "w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden border-2 transition-colors",
                selectedIndex === i ? "border-blue-600" : "border-transparent hover:border-gray-300"
              )}
            >
              {img.url ? (
                <Image
                  src={img.url}
                  alt={`${productName} ${i + 1}`}
                  width={80}
                  height={80}
                  className="object-cover w-full h-full"
                />
              ) : (
                <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                  <span className="text-2xl">💧</span>
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.id as string;
  const { addItem } = useCart();

  const [quantity, setQuantity] = useState(1);
  const [isAddingToCart, setIsAddingToCart] = useState(false);

  // Fetch product
  const { data: product, isLoading, error } = useQuery({
    queryKey: ['product', slug],
    queryFn: async () => {
      try {
        // Try by slug first
        const response = await productsApi.getBySlug(slug);
        return response;
      } catch {
        // Try by ID if slug fails
        try {
          const response = await productsApi.getById(slug);
          return response;
        } catch {
          return null;
        }
      }
    },
  });

  const handleAddToCart = async () => {
    if (!product) return;

    setIsAddingToCart(true);
    await new Promise(resolve => setTimeout(resolve, 300));

    addItem({
      id: product.id,
      productId: product.id,
      name: product.name,
      slug: product.slug || product.id,
      sku: product.sku,
      image: (product.images?.[0] as any)?.url || product.images?.[0]?.image_url,
      price: product.selling_price,
      mrp: product.mrp,
      quantity,
    });

    toast.success(`${quantity} item(s) added to cart`);
    setIsAddingToCart(false);
  };

  const handleBuyNow = async () => {
    await handleAddToCart();
    window.location.href = '/checkout';
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-2 gap-8">
          <Skeleton className="aspect-square rounded-xl" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/4" />
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
        <div className="text-6xl mb-4">😕</div>
        <h1 className="text-2xl font-bold mb-2">Product Not Found</h1>
        <p className="text-gray-500 mb-6">The product you're looking for doesn't exist or has been removed.</p>
        <Link href="/products">
          <Button>Browse Products</Button>
        </Link>
      </div>
    );
  }

  const discount = product.mrp > product.selling_price
    ? Math.round(((product.mrp - product.selling_price) / product.mrp) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Link href="/" className="hover:text-blue-600">Home</Link>
            <ChevronRight className="h-4 w-4" />
            <Link href="/products" className="hover:text-blue-600">Products</Link>
            <ChevronRight className="h-4 w-4" />
            <span className="text-gray-900 truncate">{product.name}</span>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="grid md:grid-cols-2 gap-8 p-6 md:p-8">
            {/* Left: Image Gallery */}
            <ImageGallery images={product.images || []} productName={product.name} />

            {/* Right: Product Info */}
            <div className="space-y-6">
              {/* Badges */}
              <div className="flex gap-2">
                {product.is_bestseller && (
                  <Badge className="bg-orange-500">Bestseller</Badge>
                )}
                {product.is_new_arrival && (
                  <Badge className="bg-green-500">New Arrival</Badge>
                )}
                {discount > 0 && (
                  <Badge className="bg-red-500">{discount}% OFF</Badge>
                )}
              </div>

              {/* Title & SKU */}
              <div>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                  {product.name}
                </h1>
                <p className="text-sm text-gray-500">SKU: {product.sku}</p>
              </div>

              {/* Rating */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={cn(
                        "h-4 w-4",
                        i < 4 ? "text-yellow-400 fill-yellow-400" : "text-gray-300"
                      )}
                    />
                  ))}
                </div>
                <span className="text-sm text-gray-500">(42 reviews)</span>
              </div>

              {/* Price */}
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-blue-600">
                  {formatCurrency(product.selling_price)}
                </span>
                {discount > 0 && (
                  <>
                    <span className="text-xl text-gray-400 line-through">
                      {formatCurrency(product.mrp)}
                    </span>
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Save {formatCurrency(product.mrp - product.selling_price)}
                    </Badge>
                  </>
                )}
              </div>

              {/* Short description */}
              {product.description && (
                <p className="text-gray-600 line-clamp-3">{product.description}</p>
              )}

              <Separator />

              {/* Quantity & Add to Cart */}
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium">Quantity:</span>
                  <div className="flex items-center border rounded-lg">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      disabled={quantity <= 1}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="w-12 text-center font-medium">{quantity}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setQuantity(Math.min(10, quantity + 1))}
                      disabled={quantity >= 10}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    size="lg"
                    variant="outline"
                    className="flex-1"
                    onClick={handleAddToCart}
                    disabled={isAddingToCart}
                  >
                    {isAddingToCart ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <>
                        <ShoppingCart className="h-5 w-5 mr-2" />
                        Add to Cart
                      </>
                    )}
                  </Button>
                  <Button
                    size="lg"
                    className="flex-1 bg-orange-500 hover:bg-orange-600"
                    onClick={handleBuyNow}
                  >
                    Buy Now
                  </Button>
                </div>
              </div>

              <Separator />

              {/* Serviceability Check */}
              <ServiceabilityChecker productId={product.id} />

              {/* Trust badges */}
              <div className="grid grid-cols-3 gap-4 pt-4">
                <div className="text-center">
                  <Shield className="h-8 w-8 mx-auto text-blue-600 mb-1" />
                  <p className="text-xs text-gray-600">Genuine Product</p>
                </div>
                <div className="text-center">
                  <Award className="h-8 w-8 mx-auto text-blue-600 mb-1" />
                  <p className="text-xs text-gray-600">{product.warranty_months || 12}M Warranty</p>
                </div>
                <div className="text-center">
                  <Package className="h-8 w-8 mx-auto text-blue-600 mb-1" />
                  <p className="text-xs text-gray-600">Easy Returns</p>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs: Description, Specifications, Reviews */}
          <div className="border-t">
            <Tabs defaultValue="description" className="p-6 md:p-8">
              <TabsList className="grid w-full grid-cols-3 max-w-md">
                <TabsTrigger value="description">Description</TabsTrigger>
                <TabsTrigger value="specifications">Specifications</TabsTrigger>
                <TabsTrigger value="reviews">Reviews</TabsTrigger>
              </TabsList>

              <TabsContent value="description" className="mt-6">
                <div className="prose max-w-none">
                  {product.description ? (
                    <p>{product.description}</p>
                  ) : (
                    <p className="text-gray-500">No description available.</p>
                  )}
                  {product.features && (
                    <div className="mt-4">
                      <h3 className="text-lg font-semibold mb-2">Key Features</h3>
                      <ul className="list-disc pl-5 space-y-1">
                        {product.features.split('\n').map((feature: string, i: number) => (
                          <li key={i}>{feature}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="specifications" className="mt-6">
                <div className="grid md:grid-cols-2 gap-4">
                  {product.specifications && product.specifications.length > 0 ? (
                    product.specifications.map((spec: any, i: number) => (
                      <div key={i} className="flex justify-between py-2 border-b">
                        <span className="text-gray-500">{spec.name}</span>
                        <span className="font-medium">{spec.value}</span>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-gray-500">Model</span>
                        <span className="font-medium">{product.model_number || product.sku}</span>
                      </div>
                      {product.warranty_months && (
                        <div className="flex justify-between py-2 border-b">
                          <span className="text-gray-500">Warranty</span>
                          <span className="font-medium">{product.warranty_months} months</span>
                        </div>
                      )}
                      {(product as any).dead_weight_kg && (
                        <div className="flex justify-between py-2 border-b">
                          <span className="text-gray-500">Weight</span>
                          <span className="font-medium">{(product as any).dead_weight_kg} kg</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="reviews" className="mt-6">
                <div className="text-center py-8 text-gray-500">
                  <Star className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <p>No reviews yet. Be the first to review this product!</p>
                  <Button variant="outline" className="mt-4">Write a Review</Button>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
