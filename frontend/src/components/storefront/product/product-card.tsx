'use client';

import Link from 'next/link';
import { ShoppingCart, Heart, Star, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { StorefrontProduct } from '@/types/storefront';
import { useCartStore } from '@/lib/storefront/cart-store';
import { formatCurrency } from '@/lib/utils';

interface ProductCardProps {
  product: StorefrontProduct;
  showAddToCart?: boolean;
}

export default function ProductCard({
  product,
  showAddToCart = true,
}: ProductCardProps) {
  const addItem = useCartStore((state) => state.addItem);

  const primaryImage =
    product.images?.find((img) => img.is_primary) || product.images?.[0];

  const discountPercentage = product.mrp > product.selling_price
    ? Math.round(((product.mrp - product.selling_price) / product.mrp) * 100)
    : 0;

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    addItem(product, 1);
  };

  return (
    <Card className="group overflow-hidden hover:shadow-lg transition-shadow">
      <Link href={`/products/${product.slug}`}>
        <div className="relative aspect-square overflow-hidden bg-muted">
          {primaryImage ? (
            <img
              src={primaryImage.thumbnail_url || primaryImage.image_url}
              alt={primaryImage.alt_text || product.name}
              className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="h-full w-full flex items-center justify-center">
              <Package className="h-16 w-16 text-gray-300" />
            </div>
          )}

          {/* Badges */}
          <div className="absolute top-2 left-2 flex flex-col gap-1">
            {discountPercentage > 0 && (
              <Badge variant="destructive" className="text-xs">
                {discountPercentage}% OFF
              </Badge>
            )}
            {product.is_new_arrival && (
              <Badge className="bg-green-500 text-xs">New</Badge>
            )}
            {product.is_bestseller && (
              <Badge className="bg-orange-500 text-xs">Bestseller</Badge>
            )}
          </div>

          {/* Wishlist Button */}
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 h-8 w-8 bg-background/80 hover:bg-background opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              // TODO: Add to wishlist
            }}
          >
            <Heart className="h-4 w-4" />
          </Button>

          {/* Quick Add to Cart */}
          {showAddToCart && (
            <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                className="w-full"
                size="sm"
                onClick={handleAddToCart}
              >
                <ShoppingCart className="h-4 w-4 mr-2" />
                Add to Cart
              </Button>
            </div>
          )}
        </div>

        <CardContent className="p-4">
          {/* Category & Brand */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            {product.category?.name && (
              <span>{product.category.name}</span>
            )}
            {product.brand?.name && (
              <>
                <span>•</span>
                <span>{product.brand.name}</span>
              </>
            )}
          </div>

          {/* Product Name */}
          <h3 className="font-medium line-clamp-2 group-hover:text-primary transition-colors">
            {product.name}
          </h3>

          {/* Rating */}
          <div className="flex items-center gap-1 mt-2">
            <div className="flex items-center text-yellow-500">
              <Star className="h-3.5 w-3.5 fill-current" />
              <span className="text-xs ml-1 text-foreground">4.5</span>
            </div>
            <span className="text-xs text-muted-foreground">(234)</span>
          </div>

          {/* Price */}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-lg font-bold text-primary">
              {formatCurrency(product.selling_price)}
            </span>
            {product.mrp > product.selling_price && (
              <span className="text-sm text-muted-foreground line-through">
                {formatCurrency(product.mrp)}
              </span>
            )}
          </div>

          {/* Warranty */}
          {product.warranty_months && (
            <p className="text-xs text-muted-foreground mt-2">
              {product.warranty_months} Months Warranty
            </p>
          )}
        </CardContent>
      </Link>
    </Card>
  );
}
