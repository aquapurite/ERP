'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Trash2, Plus, Minus, ShoppingBag, ArrowLeft, Truck, Shield, MapPin, Loader2, CheckCircle, AlertCircle, Clock, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useCart } from '@/contexts/cart-context';
import { formatCurrency } from '@/lib/utils';

// PIN Code Serviceability Checker for Cart - Dark Theme
function CartServiceabilityChecker() {
  const { deliveryPincode, isServiceable, estimatedDelivery, setDelivery } = useCart();
  const [pincode, setPincode] = useState(deliveryPincode);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState('');

  const checkServiceability = async () => {
    if (pincode.length !== 6) {
      setError('Please enter a valid 6-digit PIN code');
      return;
    }

    setIsChecking(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/serviceability/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pincode, channel_code: 'D2C' }),
      });

      if (response.ok) {
        const data = await response.json();
        setDelivery(
          pincode,
          data.is_serviceable,
          data.estimated_delivery_days ? `${data.estimated_delivery_days} business days` : '',
          data.minimum_shipping_cost || 0
        );
      } else {
        // Fallback for demo
        const isDemo = pincode.length === 6;
        setDelivery(
          pincode,
          isDemo,
          isDemo ? '3-5 business days' : '',
          pincode.startsWith('11') ? 0 : 99
        );
      }
    } catch {
      // Demo fallback
      setDelivery(
        pincode,
        true,
        '3-5 business days',
        99
      );
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2 text-white">
          <MapPin className="h-4 w-4 text-amber-500" />
          Delivery Location
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder="Enter PIN code"
            maxLength={6}
            value={pincode}
            onChange={(e) => {
              setPincode(e.target.value.replace(/\D/g, ''));
              setError('');
            }}
            className="flex-1 bg-slate-900 border-slate-600 text-white placeholder:text-slate-400 focus:border-amber-500 focus:ring-amber-500/20"
          />
          <Button
            onClick={checkServiceability}
            disabled={pincode.length !== 6 || isChecking}
            size="sm"
            className="bg-amber-500 hover:bg-amber-600 text-slate-900"
          >
            {isChecking ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Check'}
          </Button>
        </div>

        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}

        {deliveryPincode && (
          <div className={`p-3 rounded-lg ${isServiceable ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
            {isServiceable ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">Delivery available to {deliveryPincode}</span>
                </div>
                {estimatedDelivery && (
                  <div className="flex items-center gap-1 text-sm text-slate-400">
                    <Clock className="h-3 w-3" />
                    <span>Estimated delivery: {estimatedDelivery}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-400">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">Sorry, delivery not available to {deliveryPincode}</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Cart Item Component - Dark Theme
function CartItemCard({ item }: { item: any }) {
  const { updateQuantity, removeItem } = useCart();
  const discount = item.mrp > item.price
    ? Math.round(((item.mrp - item.price) / item.mrp) * 100)
    : 0;

  return (
    <div className="flex gap-4 py-4 border-b border-slate-700 last:border-0">
      {/* Product Image */}
      <Link href={`/products/${item.slug}`} className="flex-shrink-0">
        <div className="w-24 h-24 bg-slate-700 rounded-lg overflow-hidden relative">
          {item.image ? (
            <Image
              src={item.image}
              alt={item.name}
              fill
              className="object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-amber-500/20 to-blue-500/20">
              <span className="text-3xl">💧</span>
            </div>
          )}
        </div>
      </Link>

      {/* Product Details */}
      <div className="flex-1 min-w-0">
        <Link href={`/products/${item.slug}`}>
          <h3 className="font-medium text-white hover:text-amber-500 line-clamp-2 transition-colors">
            {item.name}
          </h3>
        </Link>
        <p className="text-sm text-slate-400 mt-1">SKU: {item.sku}</p>

        <div className="flex items-baseline gap-2 mt-2">
          <span className="font-bold text-amber-500">{formatCurrency(item.price)}</span>
          {discount > 0 && (
            <>
              <span className="text-sm text-slate-500 line-through">{formatCurrency(item.mrp)}</span>
              <Badge className="text-xs bg-red-500 text-white border-0">
                {discount}% OFF
              </Badge>
            </>
          )}
        </div>

        {/* Quantity Controls */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 hover:text-amber-500"
              onClick={() => updateQuantity(item.id, item.quantity - 1)}
              disabled={item.quantity <= 1}
            >
              <Minus className="h-3 w-3" />
            </Button>
            <span className="w-8 text-center font-medium text-white">{item.quantity}</span>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 hover:text-amber-500"
              onClick={() => updateQuantity(item.id, item.quantity + 1)}
              disabled={item.quantity >= (item.maxQuantity || 10)}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
            onClick={() => removeItem(item.id)}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Remove
          </Button>
        </div>
      </div>

      {/* Item Total */}
      <div className="text-right flex-shrink-0">
        <p className="font-bold text-white">{formatCurrency(item.price * item.quantity)}</p>
      </div>
    </div>
  );
}

// Empty Cart State - Dark Theme
function EmptyCart() {
  return (
    <div className="text-center py-16">
      <div className="w-24 h-24 mx-auto mb-6 bg-slate-800 rounded-full flex items-center justify-center">
        <ShoppingBag className="h-12 w-12 text-slate-500" />
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">Your cart is empty</h2>
      <p className="text-slate-400 mb-8">Looks like you haven't added any products yet</p>
      <Link href="/products">
        <Button size="lg" className="bg-amber-500 hover:bg-amber-600 text-slate-900">
          Browse Products
        </Button>
      </Link>
    </div>
  );
}

export default function CartPage() {
  const router = useRouter();
  const { items, itemCount, subtotal, discount, shipping, total, isServiceable, deliveryPincode } = useCart();

  if (items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 min-h-screen">
        <EmptyCart />
      </div>
    );
  }

  const canCheckout = isServiceable && deliveryPincode;

  return (
    <div className="container mx-auto px-4 py-8 min-h-screen">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
        <Link href="/" className="hover:text-amber-500 transition-colors">Home</Link>
        <span>/</span>
        <span className="text-white">Shopping Cart</span>
      </div>

      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-white">
          Shopping Cart ({itemCount} {itemCount === 1 ? 'item' : 'items'})
        </h1>
        <Link href="/products">
          <Button variant="ghost" size="sm" className="text-slate-300 hover:text-amber-500 hover:bg-slate-800">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Continue Shopping
          </Button>
        </Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              {items.map((item) => (
                <CartItemCard key={item.id} item={item} />
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Order Summary */}
        <div className="space-y-4">
          {/* Delivery Location */}
          <CartServiceabilityChecker />

          {/* Price Summary */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-white">Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Subtotal ({itemCount} items)</span>
                <span className="text-white">{formatCurrency(subtotal + discount)}</span>
              </div>

              {discount > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-emerald-400">Discount</span>
                  <span className="text-emerald-400">-{formatCurrency(discount)}</span>
                </div>
              )}

              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Shipping</span>
                <span>{shipping === 0 ? <span className="text-emerald-400">FREE</span> : <span className="text-white">{formatCurrency(shipping)}</span>}</span>
              </div>

              {subtotal < 1000 && shipping > 0 && (
                <p className="text-xs text-slate-500">
                  Add {formatCurrency(1000 - subtotal)} more for FREE shipping
                </p>
              )}

              <Separator className="bg-slate-700" />

              <div className="flex justify-between font-bold text-lg">
                <span className="text-white">Total</span>
                <span className="text-amber-500">{formatCurrency(total)}</span>
              </div>

              {discount > 0 && (
                <p className="text-sm text-emerald-400 text-center">
                  You're saving {formatCurrency(discount)} on this order!
                </p>
              )}

              <Button
                className="w-full bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
                size="lg"
                disabled={!canCheckout}
                onClick={() => router.push('/checkout')}
              >
                {!deliveryPincode ? 'Enter PIN code to continue' :
                 !isServiceable ? 'Delivery not available' :
                 'Proceed to Checkout'}
              </Button>

              {!canCheckout && deliveryPincode && !isServiceable && (
                <p className="text-sm text-red-400 text-center">
                  Please enter a serviceable PIN code to checkout
                </p>
              )}
            </CardContent>
          </Card>

          {/* Trust Badges */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Shield className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                <span className="text-slate-300">100% Secure Payments</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Truck className="h-5 w-5 text-amber-500 flex-shrink-0" />
                <span className="text-slate-300">Free Shipping on orders above ₹1000</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <CheckCircle className="h-5 w-5 text-blue-500 flex-shrink-0" />
                <span className="text-slate-300">Easy Returns & Refunds</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
