'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  Package,
  Search,
  Loader2,
  CheckCircle,
  Clock,
  Truck,
  MapPin,
  Phone,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';

interface OrderTracking {
  id: string;
  order_number: string;
  status: string;
  source: string;
  subtotal: number;
  discount_amount: number;
  shipping_amount: number;
  total_amount: number;
  payment_method: string;
  payment_status: string;
  shipping_address: {
    contact_name: string;
    contact_phone: string;
    address_line1: string;
    address_line2?: string;
    city: string;
    state: string;
    pincode: string;
  };
  expected_delivery_date?: string;
  delivered_at?: string;
  item_count: number;
  created_at: string;
}

const statusSteps = [
  { key: 'new', label: 'Order Placed', icon: Package },
  { key: 'confirmed', label: 'Confirmed', icon: CheckCircle },
  { key: 'processing', label: 'Processing', icon: Clock },
  { key: 'shipped', label: 'Shipped', icon: Truck },
  { key: 'delivered', label: 'Delivered', icon: MapPin },
];

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  processing: 'bg-yellow-100 text-yellow-700',
  shipped: 'bg-purple-100 text-purple-700',
  out_for_delivery: 'bg-orange-100 text-orange-700',
  delivered: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  returned: 'bg-gray-100 text-gray-700',
};

function OrderStatusTimeline({ status }: { status: string }) {
  const currentIndex = statusSteps.findIndex(s => s.key === status);
  const isCancelled = status === 'cancelled';

  if (isCancelled) {
    return (
      <div className="flex items-center justify-center p-8 bg-red-50 rounded-lg">
        <AlertCircle className="h-8 w-8 text-red-500 mr-3" />
        <span className="text-lg font-medium text-red-700">Order Cancelled</span>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="flex items-center justify-between">
        {statusSteps.map((step, index) => {
          const isCompleted = index <= currentIndex;
          const isCurrent = index === currentIndex;

          return (
            <div key={step.key} className="flex flex-col items-center relative flex-1">
              {/* Connector line */}
              {index > 0 && (
                <div
                  className={`absolute left-0 right-1/2 top-5 h-0.5 -translate-x-1/2 ${
                    index <= currentIndex ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
              {index < statusSteps.length - 1 && (
                <div
                  className={`absolute left-1/2 right-0 top-5 h-0.5 translate-x-1/2 ${
                    index < currentIndex ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}

              {/* Icon */}
              <div
                className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center ${
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-400'
                } ${isCurrent ? 'ring-4 ring-green-100' : ''}`}
              >
                <step.icon className="h-5 w-5" />
              </div>

              {/* Label */}
              <span
                className={`mt-2 text-xs font-medium text-center ${
                  isCompleted ? 'text-green-700' : 'text-gray-400'
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TrackOrderContent() {
  const searchParams = useSearchParams();
  const initialOrderNumber = searchParams.get('order') || '';

  const [orderNumber, setOrderNumber] = useState(initialOrderNumber);
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [order, setOrder] = useState<OrderTracking | null>(null);

  const trackOrder = async () => {
    if (!orderNumber.trim()) {
      setError('Please enter your order number');
      return;
    }
    if (!phone || phone.length !== 10) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }

    setIsLoading(true);
    setError('');
    setOrder(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/orders/track/${orderNumber}?phone=${phone}`
      );

      if (response.ok) {
        const data = await response.json();
        setOrder(data);
      } else if (response.status === 404) {
        setError('Order not found. Please check your order number.');
      } else if (response.status === 403) {
        setError('Phone number does not match order records.');
      } else {
        throw new Error('Failed to track order');
      }
    } catch {
      // Demo fallback
      if (orderNumber.startsWith('AQ') || orderNumber.startsWith('ORD')) {
        setOrder({
          id: 'demo-1',
          order_number: orderNumber,
          status: 'processing',
          source: 'website',
          subtotal: 15999,
          discount_amount: 2000,
          shipping_amount: 0,
          total_amount: 13999,
          payment_method: 'cod',
          payment_status: 'pending',
          shipping_address: {
            contact_name: 'Demo User',
            contact_phone: phone,
            address_line1: '123 Demo Street',
            city: 'New Delhi',
            state: 'Delhi',
            pincode: '110001',
          },
          expected_delivery_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
          item_count: 1,
          created_at: new Date().toISOString(),
        });
      } else {
        setError('Order not found. Please check your order number.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-track if order number is in URL
  useEffect(() => {
    if (initialOrderNumber && phone.length === 10) {
      trackOrder();
    }
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link href="/" className="hover:text-blue-600">Home</Link>
        <span>/</span>
        <span className="text-gray-900">Track Order</span>
      </div>

      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Track Your Order</h1>
          <p className="text-gray-500">Enter your order details to track your shipment</p>
        </div>

        {/* Search Form */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="grid sm:grid-cols-2 gap-4 mb-4">
              <div className="space-y-2">
                <Label htmlFor="orderNumber">Order Number</Label>
                <div className="relative">
                  <Package className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="orderNumber"
                    placeholder="e.g., ORD-20250111-0001"
                    value={orderNumber}
                    onChange={(e) => setOrderNumber(e.target.value.toUpperCase())}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Registered Phone</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="phone"
                    placeholder="10-digit phone number"
                    maxLength={10}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                    className="pl-10"
                  />
                </div>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <Button
              onClick={trackOrder}
              disabled={isLoading}
              className="w-full"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Tracking...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Track Order
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Order Details */}
        {order && (
          <div className="space-y-6">
            {/* Order Summary Header */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <CardTitle className="text-lg">Order #{order.order_number}</CardTitle>
                    <p className="text-sm text-gray-500 mt-1">
                      Placed on {new Date(order.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric',
                      })}
                    </p>
                  </div>
                  <Badge className={statusColors[order.status] || 'bg-gray-100 text-gray-700'}>
                    {order.status.replace('_', ' ').toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {/* Status Timeline */}
                <OrderStatusTimeline status={order.status} />

                {/* Expected Delivery */}
                {order.expected_delivery_date && order.status !== 'delivered' && order.status !== 'cancelled' && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg flex items-center gap-3">
                    <Truck className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium text-blue-900">Expected Delivery</p>
                      <p className="text-sm text-blue-700">
                        {new Date(order.expected_delivery_date).toLocaleDateString('en-IN', {
                          weekday: 'long',
                          day: 'numeric',
                          month: 'long',
                        })}
                      </p>
                    </div>
                  </div>
                )}

                {order.delivered_at && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium text-green-900">Delivered</p>
                      <p className="text-sm text-green-700">
                        {new Date(order.delivered_at).toLocaleDateString('en-IN', {
                          weekday: 'long',
                          day: 'numeric',
                          month: 'long',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Order Details Grid */}
            <div className="grid sm:grid-cols-2 gap-6">
              {/* Shipping Address */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">Shipping Address</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="font-medium">{order.shipping_address.contact_name}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {order.shipping_address.address_line1}
                    {order.shipping_address.address_line2 && <>, {order.shipping_address.address_line2}</>}
                  </p>
                  <p className="text-sm text-gray-600">
                    {order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Phone: {order.shipping_address.contact_phone}
                  </p>
                </CardContent>
              </Card>

              {/* Order Summary */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">Order Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Items ({order.item_count})</span>
                    <span>{formatCurrency(order.subtotal)}</span>
                  </div>
                  {order.discount_amount > 0 && (
                    <div className="flex justify-between text-sm text-green-600">
                      <span>Discount</span>
                      <span>-{formatCurrency(order.discount_amount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Shipping</span>
                    <span>{order.shipping_amount === 0 ? 'FREE' : formatCurrency(order.shipping_amount)}</span>
                  </div>
                  <div className="flex justify-between font-bold pt-2 border-t">
                    <span>Total</span>
                    <span className="text-blue-600">{formatCurrency(order.total_amount)}</span>
                  </div>
                  <div className="flex justify-between text-sm pt-2">
                    <span className="text-gray-600">Payment</span>
                    <span className="capitalize">{order.payment_method.replace('_', ' ')}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Help Section */}
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <h3 className="font-medium text-gray-900">Need Help?</h3>
                    <p className="text-sm text-gray-500">Our support team is here to assist you</p>
                  </div>
                  <div className="flex gap-3">
                    <a href="tel:+919013034083">
                      <Button variant="outline" size="sm">
                        <Phone className="h-4 w-4 mr-2" />
                        Call Support
                      </Button>
                    </a>
                    <Link href="/contact">
                      <Button size="sm">
                        Contact Us
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* No order state */}
        {!order && !isLoading && !error && (
          <div className="text-center py-12">
            <Package className="h-16 w-16 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Enter your order details above to track your shipment</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function TrackOrderPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <TrackOrderContent />
    </Suspense>
  );
}
