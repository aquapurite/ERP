'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ChevronRight,
  CreditCard,
  Truck,
  Package,
  ArrowLeft,
  Loader2,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { useCartStore, useCartSummary } from '@/lib/storefront/cart-store';
import { ordersApi } from '@/lib/storefront/api';
import { formatCurrency } from '@/lib/utils';
import { D2COrderRequest, ShippingAddress } from '@/types/storefront';

const indianStates = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
  'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
  'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
  'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Delhi', 'Jammu and Kashmir', 'Ladakh',
];

export default function CheckoutPage() {
  const router = useRouter();
  const clearCart = useCartStore((state) => state.clearCart);
  const { items, subtotal, tax, shipping, total } = useCartSummary();

  const [step, setStep] = useState<'shipping' | 'payment' | 'review'>('shipping');
  const [loading, setLoading] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'RAZORPAY' | 'COD'>('RAZORPAY');

  const [formData, setFormData] = useState<ShippingAddress>({
    full_name: '',
    phone: '',
    email: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    pincode: '',
    country: 'India',
  });

  const [errors, setErrors] = useState<Partial<ShippingAddress>>({});

  // Redirect if cart is empty
  if (items.length === 0) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center px-4">
        <Package className="h-16 w-16 text-gray-400 mb-6" />
        <h2 className="text-2xl font-bold mb-2">Your cart is empty</h2>
        <p className="text-muted-foreground mb-6">
          Add some products to proceed with checkout.
        </p>
        <Button size="lg" asChild>
          <Link href="/products">Browse Products</Link>
        </Button>
      </div>
    );
  }

  const validateShipping = (): boolean => {
    const newErrors: Partial<ShippingAddress> = {};

    if (!formData.full_name.trim()) newErrors.full_name = 'Name is required';
    if (!formData.phone.trim()) newErrors.phone = 'Phone is required';
    else if (!/^[6-9]\d{9}$/.test(formData.phone))
      newErrors.phone = 'Enter valid 10-digit phone';
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email))
      newErrors.email = 'Enter valid email';
    if (!formData.address_line1.trim())
      newErrors.address_line1 = 'Address is required';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.state) newErrors.state = 'State is required';
    if (!formData.pincode.trim()) newErrors.pincode = 'Pincode is required';
    else if (!/^\d{6}$/.test(formData.pincode))
      newErrors.pincode = 'Enter valid 6-digit pincode';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleShippingSubmit = () => {
    if (validateShipping()) {
      setStep('payment');
    }
  };

  const handlePaymentSubmit = () => {
    setStep('review');
  };

  const handlePlaceOrder = async () => {
    setLoading(true);

    try {
      const orderData: D2COrderRequest = {
        customer_name: formData.full_name,
        customer_phone: formData.phone,
        customer_email: formData.email || undefined,
        shipping_address: formData,
        items: items.map((item) => ({
          product_id: item.product.id,
          sku: item.variant?.sku || item.product.sku,
          name: item.product.name + (item.variant ? ` - ${item.variant.name}` : ''),
          quantity: item.quantity,
          unit_price: item.price,
          tax_rate: item.product.gst_rate || 18,
        })),
        payment_method: paymentMethod,
        subtotal,
        tax_amount: tax,
        shipping_amount: shipping,
        total_amount: total,
      };

      if (paymentMethod === 'RAZORPAY') {
        // Load Razorpay script if not already loaded
        if (!(window as any).Razorpay) {
          await loadRazorpayScript();
        }

        // Create order first
        const order = await ordersApi.createD2C(orderData);

        // Initialize Razorpay
        const options = {
          key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || 'rzp_test_xxx',
          amount: total * 100, // Amount in paise
          currency: 'INR',
          name: 'AQUAPURITE',
          description: `Order #${order.order_number}`,
          order_id: order.id, // This should be razorpay_order_id from backend
          prefill: {
            name: formData.full_name,
            email: formData.email,
            contact: formData.phone,
          },
          handler: function (response: any) {
            // Payment successful
            clearCart();
            router.push(`/order-success?order=${order.order_number}`);
          },
          modal: {
            ondismiss: function () {
              setLoading(false);
              toast.error('Payment cancelled');
            },
          },
        };

        const razorpay = new (window as any).Razorpay(options);
        razorpay.open();
      } else {
        // COD Order
        const order = await ordersApi.createD2C(orderData);
        clearCart();
        router.push(`/order-success?order=${order.order_number}`);
      }
    } catch (error: any) {
      console.error('Order error:', error);
      toast.error(error.message || 'Failed to place order. Please try again.');
      setLoading(false);
    }
  };

  const loadRazorpayScript = (): Promise<void> => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve();
      document.body.appendChild(script);
    });
  };

  const updateFormData = (field: keyof ShippingAddress, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="bg-muted/50 min-h-screen py-6">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
          <Link href="/" className="hover:text-primary">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/cart" className="hover:text-primary">
            Cart
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground">Checkout</span>
        </nav>

        <h1 className="text-2xl md:text-3xl font-bold mb-6">Checkout</h1>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center">
            <div
              className={`flex items-center justify-center h-10 w-10 rounded-full ${
                step === 'shipping' || step === 'payment' || step === 'review'
                  ? 'bg-primary text-white'
                  : 'bg-muted'
              }`}
            >
              {step === 'payment' || step === 'review' ? (
                <Check className="h-5 w-5" />
              ) : (
                <Truck className="h-5 w-5" />
              )}
            </div>
            <span className="ml-2 text-sm font-medium">Shipping</span>
          </div>
          <div className="w-16 h-0.5 bg-muted mx-2">
            <div
              className={`h-full bg-primary transition-all ${
                step === 'payment' || step === 'review' ? 'w-full' : 'w-0'
              }`}
            />
          </div>
          <div className="flex items-center">
            <div
              className={`flex items-center justify-center h-10 w-10 rounded-full ${
                step === 'payment' || step === 'review'
                  ? 'bg-primary text-white'
                  : 'bg-muted'
              }`}
            >
              {step === 'review' ? (
                <Check className="h-5 w-5" />
              ) : (
                <CreditCard className="h-5 w-5" />
              )}
            </div>
            <span className="ml-2 text-sm font-medium">Payment</span>
          </div>
          <div className="w-16 h-0.5 bg-muted mx-2">
            <div
              className={`h-full bg-primary transition-all ${
                step === 'review' ? 'w-full' : 'w-0'
              }`}
            />
          </div>
          <div className="flex items-center">
            <div
              className={`flex items-center justify-center h-10 w-10 rounded-full ${
                step === 'review' ? 'bg-primary text-white' : 'bg-muted'
              }`}
            >
              <Package className="h-5 w-5" />
            </div>
            <span className="ml-2 text-sm font-medium">Review</span>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Shipping Form */}
            {step === 'shipping' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Truck className="h-5 w-5" />
                    Shipping Address
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="full_name">Full Name *</Label>
                      <Input
                        id="full_name"
                        value={formData.full_name}
                        onChange={(e) => updateFormData('full_name', e.target.value)}
                        className={errors.full_name ? 'border-red-500' : ''}
                      />
                      {errors.full_name && (
                        <p className="text-red-500 text-xs mt-1">{errors.full_name}</p>
                      )}
                    </div>
                    <div>
                      <Label htmlFor="phone">Phone Number *</Label>
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) =>
                          updateFormData('phone', e.target.value.replace(/\D/g, '').slice(0, 10))
                        }
                        className={errors.phone ? 'border-red-500' : ''}
                      />
                      {errors.phone && (
                        <p className="text-red-500 text-xs mt-1">{errors.phone}</p>
                      )}
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="email">Email (Optional)</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => updateFormData('email', e.target.value)}
                      className={errors.email ? 'border-red-500' : ''}
                    />
                    {errors.email && (
                      <p className="text-red-500 text-xs mt-1">{errors.email}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="address_line1">Address Line 1 *</Label>
                    <Input
                      id="address_line1"
                      value={formData.address_line1}
                      onChange={(e) => updateFormData('address_line1', e.target.value)}
                      placeholder="House/Flat No., Building Name"
                      className={errors.address_line1 ? 'border-red-500' : ''}
                    />
                    {errors.address_line1 && (
                      <p className="text-red-500 text-xs mt-1">{errors.address_line1}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="address_line2">Address Line 2</Label>
                    <Input
                      id="address_line2"
                      value={formData.address_line2}
                      onChange={(e) => updateFormData('address_line2', e.target.value)}
                      placeholder="Street, Area, Landmark"
                    />
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="city">City *</Label>
                      <Input
                        id="city"
                        value={formData.city}
                        onChange={(e) => updateFormData('city', e.target.value)}
                        className={errors.city ? 'border-red-500' : ''}
                      />
                      {errors.city && (
                        <p className="text-red-500 text-xs mt-1">{errors.city}</p>
                      )}
                    </div>
                    <div>
                      <Label htmlFor="state">State *</Label>
                      <select
                        id="state"
                        value={formData.state}
                        onChange={(e) => updateFormData('state', e.target.value)}
                        className={`w-full h-10 px-3 rounded-md border ${
                          errors.state ? 'border-red-500' : 'border-input'
                        } bg-background`}
                      >
                        <option value="">Select State</option>
                        {indianStates.map((state) => (
                          <option key={state} value={state}>
                            {state}
                          </option>
                        ))}
                      </select>
                      {errors.state && (
                        <p className="text-red-500 text-xs mt-1">{errors.state}</p>
                      )}
                    </div>
                    <div>
                      <Label htmlFor="pincode">Pincode *</Label>
                      <Input
                        id="pincode"
                        value={formData.pincode}
                        onChange={(e) =>
                          updateFormData('pincode', e.target.value.replace(/\D/g, '').slice(0, 6))
                        }
                        className={errors.pincode ? 'border-red-500' : ''}
                      />
                      {errors.pincode && (
                        <p className="text-red-500 text-xs mt-1">{errors.pincode}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button variant="ghost" asChild>
                      <Link href="/cart">
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Cart
                      </Link>
                    </Button>
                    <Button onClick={handleShippingSubmit}>
                      Continue to Payment
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Payment Options */}
            {step === 'payment' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Payment Method
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <RadioGroup
                    value={paymentMethod}
                    onValueChange={(value) => setPaymentMethod(value as 'RAZORPAY' | 'COD')}
                  >
                    <div className="flex items-center space-x-3 p-4 border rounded-lg">
                      <RadioGroupItem value="RAZORPAY" id="razorpay" />
                      <Label htmlFor="razorpay" className="flex-1 cursor-pointer">
                        <div className="font-medium">Pay Online</div>
                        <div className="text-sm text-muted-foreground">
                          Credit/Debit Card, UPI, Net Banking, Wallets
                        </div>
                      </Label>
                      <img
                        src="https://razorpay.com/build/browser/static/razorpay-logo-new.svg"
                        alt="Razorpay"
                        className="h-6"
                      />
                    </div>
                    <div className="flex items-center space-x-3 p-4 border rounded-lg">
                      <RadioGroupItem value="COD" id="cod" />
                      <Label htmlFor="cod" className="flex-1 cursor-pointer">
                        <div className="font-medium">Cash on Delivery</div>
                        <div className="text-sm text-muted-foreground">
                          Pay when you receive your order
                        </div>
                      </Label>
                    </div>
                  </RadioGroup>

                  <div className="flex justify-between pt-4">
                    <Button variant="ghost" onClick={() => setStep('shipping')}>
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back
                    </Button>
                    <Button onClick={handlePaymentSubmit}>
                      Review Order
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Order Review */}
            {step === 'review' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Review Your Order
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Shipping Address */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">Shipping Address</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setStep('shipping')}
                      >
                        Edit
                      </Button>
                    </div>
                    <div className="bg-muted/50 p-4 rounded-lg text-sm">
                      <p className="font-medium">{formData.full_name}</p>
                      <p>{formData.address_line1}</p>
                      {formData.address_line2 && <p>{formData.address_line2}</p>}
                      <p>
                        {formData.city}, {formData.state} - {formData.pincode}
                      </p>
                      <p>Phone: {formData.phone}</p>
                      {formData.email && <p>Email: {formData.email}</p>}
                    </div>
                  </div>

                  {/* Payment Method */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">Payment Method</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setStep('payment')}
                      >
                        Edit
                      </Button>
                    </div>
                    <div className="bg-muted/50 p-4 rounded-lg text-sm">
                      {paymentMethod === 'RAZORPAY'
                        ? 'Pay Online (Razorpay)'
                        : 'Cash on Delivery'}
                    </div>
                  </div>

                  {/* Order Items */}
                  <div>
                    <h4 className="font-medium mb-2">Order Items</h4>
                    <div className="space-y-3">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="flex justify-between items-center bg-muted/50 p-3 rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-sm">{item.product.name}</p>
                            <p className="text-xs text-muted-foreground">
                              Qty: {item.quantity}
                            </p>
                          </div>
                          <p className="font-medium">
                            {formatCurrency(item.price * item.quantity)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button variant="ghost" onClick={() => setStep('payment')}>
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back
                    </Button>
                    <Button
                      onClick={handlePlaceOrder}
                      disabled={loading}
                      size="lg"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        `Place Order - ${formatCurrency(total)}`
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Order Summary Sidebar */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Items */}
                <div className="space-y-2">
                  {items.map((item) => (
                    <div key={item.id} className="flex justify-between text-sm">
                      <span className="truncate flex-1 pr-2">
                        {item.product.name} x{item.quantity}
                      </span>
                      <span>{formatCurrency(item.price * item.quantity)}</span>
                    </div>
                  ))}
                </div>

                <Separator />

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>{formatCurrency(subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Shipping</span>
                    <span>
                      {shipping === 0 ? (
                        <span className="text-green-600">FREE</span>
                      ) : (
                        formatCurrency(shipping)
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tax (GST)</span>
                    <span>{formatCurrency(tax)}</span>
                  </div>
                </div>

                <Separator />

                <div className="flex justify-between text-lg font-semibold">
                  <span>Total</span>
                  <span className="text-primary">{formatCurrency(total)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
