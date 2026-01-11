'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowRight,
  Shield,
  Truck,
  Headphones,
  Award,
  CheckCircle,
  Loader2,
  MapPin,
  Clock,
  Droplets,
  Zap,
  Sparkles,
  BadgeCheck,
  Star,
  ChevronRight,
  HeartHandshake,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { productsApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

// PIN Code Serviceability Checker - Dark Theme
function PinCodeChecker() {
  const [pincode, setPincode] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState<{
    isServiceable: boolean;
    deliveryDays: number;
    shippingCost: number;
    codAvailable: boolean;
  } | null>(null);

  const checkServiceability = async () => {
    if (pincode.length !== 6) return;

    setIsChecking(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/serviceability/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pincode, channel_code: 'D2C' }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult({
          isServiceable: data.is_serviceable,
          deliveryDays: data.estimated_delivery_days || 5,
          shippingCost: data.minimum_shipping_cost || 0,
          codAvailable: data.cod_available || false,
        });
      } else {
        setResult({
          isServiceable: true,
          deliveryDays: 3,
          shippingCost: pincode.startsWith('11') ? 0 : 99,
          codAvailable: true,
        });
      }
    } catch {
      setResult({
        isServiceable: pincode.length === 6,
        deliveryDays: 3,
        shippingCost: 99,
        codAvailable: true,
      });
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-700 shadow-xl">
      <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
        <MapPin className="h-5 w-5 text-amber-500" />
        Check Delivery Availability
      </h3>
      <div className="flex gap-2">
        <Input
          type="text"
          placeholder="Enter PIN code"
          maxLength={6}
          value={pincode}
          onChange={(e) => {
            setPincode(e.target.value.replace(/\D/g, ''));
            setResult(null);
          }}
          className="flex-1 bg-slate-900 border-slate-600 text-white placeholder:text-slate-400 focus:border-amber-500"
        />
        <Button
          onClick={checkServiceability}
          disabled={pincode.length !== 6 || isChecking}
          className="bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
        >
          {isChecking ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Check'}
        </Button>
      </div>

      {result && (
        <div className={`mt-4 p-3 rounded-lg ${result.isServiceable ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
          {result.isServiceable ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Delivery available!</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex items-center gap-1 text-slate-300">
                  <Clock className="h-4 w-4 text-amber-500" />
                  <span>Delivery in {result.deliveryDays} days</span>
                </div>
                <div className="flex items-center gap-1 text-slate-300">
                  <Truck className="h-4 w-4 text-amber-500" />
                  <span>{result.shippingCost === 0 ? 'FREE Shipping' : `Shipping: Rs ${result.shippingCost}`}</span>
                </div>
              </div>
              {result.codAvailable && (
                <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 text-xs">
                  Cash on Delivery Available
                </Badge>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-400">
              <span>Sorry, we don't deliver to this PIN code yet.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Product card - Dark Theme
function ProductCard({ product }: { product: any }) {
  const discount = product.mrp > product.selling_price
    ? Math.round(((product.mrp - product.selling_price) / product.mrp) * 100)
    : 0;

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
        </div>
        <CardContent className="p-4">
          <h3 className="font-medium text-white line-clamp-2 mb-2 group-hover:text-amber-500 transition-colors">
            {product.name}
          </h3>
          <div className="flex items-baseline gap-2">
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
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
              <Shield className="h-3 w-3" />
              {product.warranty_months} months warranty
            </p>
          )}
        </CardContent>
      </Link>
    </Card>
  );
}

// Product skeleton - Dark Theme
function ProductSkeleton() {
  return (
    <Card className="overflow-hidden bg-slate-800/50 border-slate-700">
      <Skeleton className="aspect-square bg-slate-700" />
      <CardContent className="p-4 space-y-2">
        <Skeleton className="h-4 w-3/4 bg-slate-700" />
        <Skeleton className="h-4 w-1/2 bg-slate-700" />
        <Skeleton className="h-6 w-1/3 bg-slate-700" />
      </CardContent>
    </Card>
  );
}

// Category Card
function CategoryCard({ title, description, icon: Icon, href, gradient }: {
  title: string;
  description: string;
  icon: any;
  href: string;
  gradient: string;
}) {
  return (
    <Link href={href}>
      <div className={`relative overflow-hidden rounded-2xl p-6 h-48 group cursor-pointer ${gradient}`}>
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="relative z-10 h-full flex flex-col justify-end">
          <Icon className="h-10 w-10 text-white mb-3 group-hover:scale-110 transition-transform" />
          <h3 className="text-xl font-bold text-white mb-1">{title}</h3>
          <p className="text-sm text-white/80">{description}</p>
        </div>
        <div className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition-colors">
          <ChevronRight className="h-5 w-5 text-white" />
        </div>
      </div>
    </Link>
  );
}

export default function HomePage() {
  // Fetch featured products
  const { data: featuredProducts, isLoading: loadingFeatured } = useQuery({
    queryKey: ['featured-products'],
    queryFn: async () => {
      try {
        const response = await productsApi.list({ is_featured: true, is_active: true, size: 4 });
        return response.items || [];
      } catch {
        return [];
      }
    },
  });

  // Fetch bestsellers
  const { data: bestsellers, isLoading: loadingBestsellers } = useQuery({
    queryKey: ['bestseller-products'],
    queryFn: async () => {
      try {
        const response = await productsApi.list({ is_bestseller: true, is_active: true, size: 4 });
        return response.items || [];
      } catch {
        return [];
      }
    },
  });

  const features = [
    { icon: Shield, title: 'Genuine Products', desc: '100% authentic purifiers' },
    { icon: Truck, title: 'Free Shipping', desc: 'On orders above Rs 1000' },
    { icon: Headphones, title: '24/7 Support', desc: 'Expert assistance' },
    { icon: Award, title: 'Warranty', desc: 'Up to 2 years' },
  ];

  const categories = [
    {
      title: 'Water Purifiers',
      description: 'RO + UV + UF Technology',
      icon: Droplets,
      href: '/products?category=water-purifiers',
      gradient: 'bg-gradient-to-br from-blue-600 to-blue-900',
    },
    {
      title: 'Filters & Membranes',
      description: 'Genuine replacement parts',
      icon: Sparkles,
      href: '/products?category=filters',
      gradient: 'bg-gradient-to-br from-amber-600 to-amber-900',
    },
    {
      title: 'Spare Parts',
      description: 'All components available',
      icon: Zap,
      href: '/products?category=spare-parts',
      gradient: 'bg-gradient-to-br from-emerald-600 to-emerald-900',
    },
    {
      title: 'Accessories',
      description: 'Enhance your purifier',
      icon: BadgeCheck,
      href: '/products?category=accessories',
      gradient: 'bg-gradient-to-br from-purple-600 to-purple-900',
    },
  ];

  const stats = [
    { value: '50,000+', label: 'Happy Customers' },
    { value: '99.9%', label: 'Pure Water' },
    { value: '8,500+', label: 'Service Engineers' },
    { value: '2 Years', label: 'Warranty' },
  ];

  return (
    <div className="bg-slate-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5" />

        {/* Decorative elements */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 py-16 md:py-24 relative">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-4 py-1.5">
                India's Trusted Water Purifier Brand
              </Badge>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight text-white">
                Pure Water,<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                  Healthy Life
                </span>
              </h1>
              <p className="text-lg text-slate-300 max-w-lg">
                Experience the difference with Aquapurite water purifiers.
                Advanced RO+UV+UF technology for 99.9% pure drinking water.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/products">
                  <Button size="lg" className="bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold shadow-lg shadow-amber-500/25">
                    Shop Now
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <Link href="/contact">
                  <Button size="lg" variant="outline" className="border-slate-600 text-white hover:bg-slate-800 hover:border-slate-500">
                    Book Free Demo
                  </Button>
                </Link>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-4 pt-8">
                {stats.map((stat, i) => (
                  <div key={i} className="text-center">
                    <p className="text-2xl md:text-3xl font-bold text-amber-500">{stat.value}</p>
                    <p className="text-xs text-slate-400">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-center md:justify-end">
              <PinCodeChecker />
            </div>
          </div>
        </div>
      </section>

      {/* Features Strip */}
      <section className="bg-slate-900 border-y border-slate-800 py-6">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                  <feature.icon className="h-6 w-6 text-amber-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-white text-sm">{feature.title}</h3>
                  <p className="text-xs text-slate-400">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 bg-slate-950">
        <div className="container mx-auto px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Shop by Category</h2>
            <p className="text-slate-400">Find what you need</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {categories.map((category, i) => (
              <CategoryCard key={i} {...category} />
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16 bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-white">Featured Products</h2>
              <p className="text-slate-400 mt-1">Our top-rated water purifiers</p>
            </div>
            <Link href="/products?featured=true">
              <Button variant="outline" className="border-slate-700 text-slate-300 hover:text-amber-500 hover:border-amber-500">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {loadingFeatured ? (
              [...Array(4)].map((_, i) => <ProductSkeleton key={i} />)
            ) : featuredProducts && featuredProducts.length > 0 ? (
              featuredProducts.map((product: any) => (
                <ProductCard key={product.id} product={product} />
              ))
            ) : (
              // Demo products
              [...Array(4)].map((_, i) => (
                <Card key={i} className="group overflow-hidden bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-all">
                  <div className="aspect-square relative bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                    <Droplets className="h-16 w-16 text-amber-500/30" />
                    <Badge className="absolute top-3 left-3 bg-red-500 text-white border-0">20% OFF</Badge>
                  </div>
                  <CardContent className="p-4">
                    <h3 className="font-medium text-white mb-2">Aquapurite Pro {i + 1}</h3>
                    <div className="flex items-baseline gap-2">
                      <span className="text-xl font-bold text-amber-500">Rs {(15999 + i * 2000).toLocaleString()}</span>
                      <span className="text-sm text-slate-500 line-through">Rs {(19999 + i * 2000).toLocaleString()}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                      <Shield className="h-3 w-3" /> 12 months warranty
                    </p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Bestsellers */}
      <section className="py-16 bg-slate-950">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-white">Bestsellers</h2>
              <p className="text-slate-400 mt-1">Most loved by our customers</p>
            </div>
            <Link href="/products?bestseller=true">
              <Button variant="outline" className="border-slate-700 text-slate-300 hover:text-amber-500 hover:border-amber-500">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {loadingBestsellers ? (
              [...Array(4)].map((_, i) => <ProductSkeleton key={i} />)
            ) : bestsellers && bestsellers.length > 0 ? (
              bestsellers.map((product: any) => (
                <ProductCard key={product.id} product={product} />
              ))
            ) : (
              // Demo products
              [...Array(4)].map((_, i) => (
                <Card key={i} className="group overflow-hidden bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-all">
                  <div className="aspect-square relative bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                    <Droplets className="h-16 w-16 text-blue-500/30" />
                    <Badge className="absolute top-3 right-3 bg-amber-500 text-slate-900 border-0">Bestseller</Badge>
                  </div>
                  <CardContent className="p-4">
                    <h3 className="font-medium text-white mb-2">Aquapurite Elite {i + 1}</h3>
                    <div className="flex items-baseline gap-2">
                      <span className="text-xl font-bold text-amber-500">Rs {(12999 + i * 1500).toLocaleString()}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                      <Shield className="h-3 w-3" /> 24 months warranty
                    </p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-16 bg-gradient-to-br from-blue-950 to-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Why Choose Aquapurite?</h2>
            <p className="text-slate-400">Trusted by thousands of families across India</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-amber-500/20 flex items-center justify-center mb-4">
                <Droplets className="h-8 w-8 text-amber-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Advanced Technology</h3>
              <p className="text-slate-400">RO + UV + UF multi-stage purification removes 99.9% of contaminants</p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-blue-500/20 flex items-center justify-center mb-4">
                <Star className="h-8 w-8 text-blue-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Premium Quality</h3>
              <p className="text-slate-400">Built with high-grade components for long-lasting performance</p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/20 flex items-center justify-center mb-4">
                <HeartHandshake className="h-8 w-8 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Expert Support</h3>
              <p className="text-slate-400">8,500+ trained service engineers for doorstep assistance</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Need Help Choosing?</h2>
          <p className="text-slate-800 max-w-2xl mx-auto mb-8">
            Our water experts are here to help you find the perfect purifier for your home.
            Get personalized recommendations based on your water source and family needs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact">
              <Button size="lg" className="bg-slate-900 hover:bg-slate-800 text-white">
                Talk to an Expert
              </Button>
            </Link>
            <a href="tel:+919013034083">
              <Button size="lg" variant="outline" className="border-slate-900 text-slate-900 hover:bg-slate-900/10">
                Call: +91 9013034083
              </Button>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
