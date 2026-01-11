'use client';

import { useEffect, useState } from 'react';
import HeroBanner from '@/components/storefront/home/hero-banner';
import CategoryGrid from '@/components/storefront/home/category-grid';
import ProductSection from '@/components/storefront/home/product-section';
import WhyChooseUs from '@/components/storefront/home/why-choose-us';
import Testimonials from '@/components/storefront/home/testimonials';
import { StorefrontProduct, StorefrontCategory } from '@/types/storefront';
import { productsApi, categoriesApi } from '@/lib/storefront/api';
import { Skeleton } from '@/components/ui/skeleton';

export default function HomePage() {
  const [categories, setCategories] = useState<StorefrontCategory[]>([]);
  const [bestsellers, setBestsellers] = useState<StorefrontProduct[]>([]);
  const [newArrivals, setNewArrivals] = useState<StorefrontProduct[]>([]);
  const [featured, setFeatured] = useState<StorefrontProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [categoriesData, bestsellersData, newArrivalsData, featuredData] =
          await Promise.all([
            categoriesApi.getTree().catch(() => []),
            productsApi.getBestsellers(8).catch(() => []),
            productsApi.getNewArrivals(8).catch(() => []),
            productsApi.getFeatured(8).catch(() => []),
          ]);

        setCategories(categoriesData);
        setBestsellers(bestsellersData);
        setNewArrivals(newArrivalsData);
        setFeatured(featuredData);
      } catch (error) {
        console.error('Failed to fetch homepage data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <>
      {/* Hero Banner */}
      <HeroBanner />

      {/* Categories */}
      <CategoryGrid categories={categories} />

      {/* Bestsellers */}
      {loading ? (
        <ProductSectionSkeleton title="Bestsellers" />
      ) : (
        <ProductSection
          title="Bestsellers"
          subtitle="Our most popular products loved by customers"
          products={bestsellers}
          viewAllLink="/products?is_bestseller=true"
        />
      )}

      {/* Why Choose Us */}
      <WhyChooseUs />

      {/* New Arrivals */}
      {loading ? (
        <ProductSectionSkeleton title="New Arrivals" />
      ) : (
        <ProductSection
          title="New Arrivals"
          subtitle="Discover our latest water purification solutions"
          products={newArrivals}
          viewAllLink="/products?is_new_arrival=true"
        />
      )}

      {/* Featured Products */}
      {loading ? (
        <ProductSectionSkeleton title="Featured Products" />
      ) : (
        featured.length > 0 && (
          <div className="bg-muted/50">
            <ProductSection
              title="Featured Products"
              subtitle="Handpicked products for you"
              products={featured}
              viewAllLink="/products?is_featured=true"
            />
          </div>
        )
      )}

      {/* Testimonials */}
      <Testimonials />

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-primary to-primary/80 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">
            Need Help Choosing the Right Purifier?
          </h2>
          <p className="text-lg text-white/80 mb-6 max-w-2xl mx-auto">
            Our experts are here to help you find the perfect water purification
            solution for your home or office.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="tel:18001234567"
              className="inline-flex items-center justify-center px-6 py-3 bg-background text-primary font-semibold rounded-lg hover:bg-muted transition-colors"
            >
              Call 1800-123-4567
            </a>
            <a
              href="/contact"
              className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition-colors"
            >
              Contact Us
            </a>
          </div>
        </div>
      </section>
    </>
  );
}

// Loading skeleton for product sections
function ProductSectionSkeleton({ title }: { title: string }) {
  return (
    <section className="py-12 md:py-16">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h2 className="text-2xl md:text-3xl font-bold">{title}</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="aspect-square rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-6 w-1/3" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
