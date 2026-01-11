import { Suspense } from 'react';
import { Metadata } from 'next';
import ProductsContent from './products-content';
import { ProductsPageSkeleton } from './products-skeleton';

// Dynamic rendering - don't pre-render at build time
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Water Purifiers & Accessories | AQUAPURITE',
  description: 'Shop premium water purifiers, RO systems, and accessories. Free installation, warranty, and genuine products.',
  openGraph: {
    title: 'Water Purifiers & Accessories | AQUAPURITE',
    description: 'Shop premium water purifiers, RO systems, and accessories. Free installation, warranty, and genuine products.',
  },
};

// Fetch initial products on server with ISR
async function getProducts() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/v1/products?is_active=true&size=50`, {
      cache: 'no-store', // Dynamic fetch
    });

    if (!response.ok) {
      return { items: [] };
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch products:', error);
    return { items: [] };
  }
}

// Fetch categories on server with ISR
async function getCategories() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/v1/categories?is_active=true`, {
      next: { revalidate: 900 }, // 15 minutes
    });

    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    return data.items || data || [];
  } catch (error) {
    console.error('Failed to fetch categories:', error);
    return [];
  }
}

export default async function ProductsPage() {
  // Fetch initial data on server (with ISR caching)
  const [productsData, categories] = await Promise.all([
    getProducts(),
    getCategories(),
  ]);

  const initialProducts = productsData.items || [];

  return (
    <Suspense fallback={<ProductsPageSkeleton />}>
      <ProductsContent
        initialProducts={initialProducts}
        initialCategories={categories}
      />
    </Suspense>
  );
}
