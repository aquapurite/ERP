'use client';

import Link from 'next/link';
import { Droplet, Filter, Cog, Wrench, Package, Zap, ThermometerSun, Shield } from 'lucide-react';
import { StorefrontCategory } from '@/types/storefront';

interface CategoryGridProps {
  categories: StorefrontCategory[];
}

// Default categories if API returns empty (Eureka Forbes inspired)
const defaultCategories: Array<{ id: string; name: string; slug: string; icon: string; image_url?: string }> = [
  { id: '1', name: 'RO Water Purifiers', slug: 'ro-water-purifiers', icon: 'droplet' },
  { id: '2', name: 'UV Water Purifiers', slug: 'uv-water-purifiers', icon: 'zap' },
  { id: '3', name: 'RO+UV Purifiers', slug: 'ro-uv-water-purifiers', icon: 'shield' },
  { id: '4', name: 'Hot & Cold', slug: 'hot-cold-water-purifiers', icon: 'thermometer' },
  { id: '5', name: 'Spare Parts', slug: 'spare-parts', icon: 'cog' },
  { id: '6', name: 'Filters', slug: 'filters', icon: 'filter' },
];

const iconMap: Record<string, React.ElementType> = {
  droplet: Droplet,
  filter: Filter,
  cog: Cog,
  wrench: Wrench,
  package: Package,
  zap: Zap,
  thermometer: ThermometerSun,
  shield: Shield,
  ro: Droplet,
  uv: Zap,
  'ro-uv': Shield,
  'hot-cold': ThermometerSun,
};

export default function CategoryGrid({ categories }: CategoryGridProps) {
  const displayCategories = categories.length > 0
    ? categories.slice(0, 6).map((cat) => ({
        id: cat.id,
        name: cat.name,
        slug: cat.slug,
        icon: cat.icon || 'droplet',
        image_url: cat.image_url,
      }))
    : defaultCategories;

  return (
    <section className="py-12 md:py-16">
      <div className="container mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-2xl md:text-3xl font-bold mb-2">
            Shop by Category
          </h2>
          <p className="text-muted-foreground">
            Find the perfect water purification solution
          </p>
        </div>

        {/* Eureka Forbes style - Icon cards with text below */}
        <div className="grid grid-cols-3 md:grid-cols-6 gap-4 md:gap-8">
          {displayCategories.map((category) => {
            const Icon = iconMap[category.icon] || Droplet;

            return (
              <Link
                key={category.id}
                href={`/category/${category.slug}`}
                className="group flex flex-col items-center text-center"
              >
                {/* Icon Container - Eureka Forbes style */}
                <div className="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary group-hover:scale-105 transition-all duration-300">
                  {category.image_url ? (
                    <img
                      src={category.image_url}
                      alt={category.name}
                      className="w-12 h-12 md:w-14 md:h-14 object-contain"
                    />
                  ) : (
                    <Icon className="w-10 h-10 md:w-12 md:h-12 text-primary group-hover:text-primary-foreground transition-colors" />
                  )}
                </div>
                {/* Category Name */}
                <span className="text-sm md:text-base font-medium text-foreground group-hover:text-primary transition-colors">
                  {category.name}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
