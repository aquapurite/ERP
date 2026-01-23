'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { StorefrontCategory } from '@/types/storefront';
import { cn } from '@/lib/utils';

interface MegaMenuProps {
  categories: StorefrontCategory[];
  className?: string;
}

interface MegaMenuItemProps {
  category: StorefrontCategory;
  onClose?: () => void;
}

export function MegaMenuItem({ category, onClose }: MegaMenuItemProps) {
  const [isOpen, setIsOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const hasChildren = category.children && category.children.length > 0;

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    // Small delay before closing to prevent flickering
    timeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 150);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div
      ref={menuRef}
      className="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Menu trigger */}
      <Link
        href={`/category/${category.slug}`}
        className={cn(
          'flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors',
          'hover:text-primary',
          isOpen && 'text-primary'
        )}
        onClick={() => {
          setIsOpen(false);
          onClose?.();
        }}
      >
        {category.name}
        {hasChildren && (
          <ChevronDown
            className={cn(
              'h-4 w-4 transition-transform',
              isOpen && 'rotate-180'
            )}
          />
        )}
      </Link>

      {/* Dropdown mega menu */}
      {hasChildren && isOpen && (
        <div
          className={cn(
            'absolute top-full left-0 z-50',
            'bg-background border border-border rounded-lg shadow-lg',
            'animate-in fade-in-0 zoom-in-95 slide-in-from-top-2',
            'min-w-[280px]'
          )}
        >
          <div className="p-4">
            {/* Category header */}
            <div className="pb-3 mb-3 border-b">
              <Link
                href={`/category/${category.slug}`}
                className="text-sm font-semibold text-primary hover:underline"
                onClick={() => {
                  setIsOpen(false);
                  onClose?.();
                }}
              >
                View All {category.name}
              </Link>
              {category.product_count !== undefined && category.product_count > 0 && (
                <span className="ml-2 text-xs text-muted-foreground">
                  ({category.product_count} products)
                </span>
              )}
            </div>

            {/* Subcategories grid */}
            <div className="grid grid-cols-1 gap-1">
              {category.children?.map((child) => (
                <Link
                  key={child.id}
                  href={`/category/${child.slug}`}
                  className={cn(
                    'flex items-center justify-between gap-2 px-3 py-2 rounded-md',
                    'text-sm text-foreground/80 hover:text-foreground',
                    'hover:bg-muted transition-colors'
                  )}
                  onClick={() => {
                    setIsOpen(false);
                    onClose?.();
                  }}
                >
                  <div className="flex items-center gap-2">
                    {child.image_url && (
                      <img
                        src={child.image_url}
                        alt={child.name}
                        className="h-6 w-6 rounded object-cover"
                      />
                    )}
                    <span>{child.name}</span>
                  </div>
                  {child.product_count !== undefined && child.product_count > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {child.product_count}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function MegaMenuWide({ category, onClose }: MegaMenuItemProps) {
  const [isOpen, setIsOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const hasChildren = category.children && category.children.length > 0;

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 150);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Calculate grid columns based on children count
  const getGridCols = (count: number) => {
    if (count <= 3) return 'grid-cols-1';
    if (count <= 6) return 'grid-cols-2';
    if (count <= 9) return 'grid-cols-3';
    return 'grid-cols-4';
  };

  return (
    <div
      className="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <Link
        href={`/category/${category.slug}`}
        className={cn(
          'flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors',
          'hover:text-primary',
          isOpen && 'text-primary'
        )}
        onClick={() => {
          setIsOpen(false);
          onClose?.();
        }}
      >
        {category.name}
        {hasChildren && (
          <ChevronDown
            className={cn(
              'h-4 w-4 transition-transform',
              isOpen && 'rotate-180'
            )}
          />
        )}
      </Link>

      {hasChildren && isOpen && (
        <div
          className={cn(
            'absolute top-full left-1/2 -translate-x-1/2 z-50',
            'bg-background border border-border rounded-lg shadow-xl',
            'animate-in fade-in-0 zoom-in-95 slide-in-from-top-2',
            'min-w-[400px] max-w-[800px]'
          )}
        >
          <div className="p-6">
            <div className="flex items-center justify-between pb-4 mb-4 border-b">
              <div>
                <Link
                  href={`/category/${category.slug}`}
                  className="text-lg font-semibold text-primary hover:underline"
                  onClick={() => {
                    setIsOpen(false);
                    onClose?.();
                  }}
                >
                  {category.name}
                </Link>
                {category.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {category.description}
                  </p>
                )}
              </div>
              <Link
                href={`/category/${category.slug}`}
                className="text-sm text-primary hover:underline flex items-center gap-1"
                onClick={() => {
                  setIsOpen(false);
                  onClose?.();
                }}
              >
                View All
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>

            <div className={cn('grid gap-4', getGridCols(category.children?.length || 0))}>
              {category.children?.map((child) => (
                <Link
                  key={child.id}
                  href={`/category/${child.slug}`}
                  className={cn(
                    'group flex items-start gap-3 p-3 rounded-lg',
                    'hover:bg-muted transition-colors'
                  )}
                  onClick={() => {
                    setIsOpen(false);
                    onClose?.();
                  }}
                >
                  {child.image_url ? (
                    <img
                      src={child.image_url}
                      alt={child.name}
                      className="h-12 w-12 rounded-lg object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                      <span className="text-lg font-semibold text-muted-foreground">
                        {child.name.charAt(0)}
                      </span>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm group-hover:text-primary transition-colors">
                      {child.name}
                    </p>
                    {child.product_count !== undefined && child.product_count > 0 && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {child.product_count} products
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MegaMenu({ categories, className }: MegaMenuProps) {
  // Filter to only show root categories (those without parent)
  const rootCategories = categories.filter((cat) => !cat.parent_id);

  return (
    <nav className={cn('flex items-center', className)}>
      {rootCategories.map((category) => (
        <MegaMenuItem key={category.id} category={category} />
      ))}
    </nav>
  );
}

// Alternative wide layout mega menu
export function MegaMenuWideCentered({ categories, className }: MegaMenuProps) {
  const rootCategories = categories.filter((cat) => !cat.parent_id);

  return (
    <nav className={cn('flex items-center justify-center', className)}>
      {rootCategories.map((category) => (
        <MegaMenuWide key={category.id} category={category} />
      ))}
    </nav>
  );
}
