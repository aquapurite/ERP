'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  CheckCircle,
  Package,
  Truck,
  Phone,
  Mail,
  ArrowRight,
  Download,
  FileText,
  Wrench,
  Copy,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { companyApi } from '@/lib/storefront/api';
import { CompanyInfo } from '@/types/storefront';

function OrderSuccessContent() {
  const searchParams = useSearchParams();
  const orderNumber = searchParams.get('order') || 'ORD-XXXXXX';
  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchCompany = async () => {
      try {
        const data = await companyApi.getInfo();
        setCompany(data);
      } catch {
        // Silently fail - will use fallbacks
      }
    };
    fetchCompany();
  }, []);

  const copyOrderNumber = () => {
    navigator.clipboard.writeText(orderNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-muted/50 py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        {/* Success Icon */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-24 w-24 rounded-full bg-green-100 mb-4">
            <CheckCircle className="h-12 w-12 text-green-600" />
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-green-600 mb-2">
            Order Placed Successfully!
          </h1>
          <p className="text-muted-foreground">
            Thank you for shopping with {company?.trade_name || company?.name || 'Aquapurite'}
          </p>
        </div>

        {/* Order Number Card */}
        <Card className="mb-6 border-primary/20">
          <CardContent className="p-6">
            <div className="text-center mb-6">
              <p className="text-sm text-muted-foreground mb-1">Your Order Number</p>
              <div className="flex items-center justify-center gap-2">
                <p className="text-2xl font-bold text-primary">{orderNumber}</p>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={copyOrderNumber}
                  title="Copy order number"
                >
                  {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              <Badge variant="secondary" className="mt-2 bg-green-100 text-green-800 border-green-200">
                Confirmed
              </Badge>
            </div>

            <Separator className="my-4" />

            {/* Order Timeline */}
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium">Order Confirmed</p>
                  <p className="text-sm text-muted-foreground">
                    Your order has been placed successfully
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                  <Package className="h-5 w-5 text-gray-400" />
                </div>
                <div>
                  <p className="font-medium text-muted-foreground">Processing & Dispatch</p>
                  <p className="text-sm text-muted-foreground">
                    Your order will be dispatched within 24–48 hours
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                  <Truck className="h-5 w-5 text-gray-400" />
                </div>
                <div>
                  <p className="font-medium text-muted-foreground">Delivery</p>
                  <p className="text-sm text-muted-foreground">
                    Estimated: 5–7 business days
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* What's Next */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">What happens next?</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span>
                  A confirmation email has been sent to your registered email address
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span>
                  Your order will be packed and dispatched within 24–48 hours
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span>
                  A <strong>GST Tax Invoice</strong> will be emailed to you at the time of dispatch
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span>
                  Free installation will be scheduled after delivery for eligible products
                </span>
              </li>
              <li className="flex items-start gap-2">
                <FileText className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <span>
                  Your invoice will be available to download from{' '}
                  <Link href="/account/orders" className="text-primary underline font-medium">
                    My Orders
                  </Link>{' '}
                  once the order is dispatched
                </span>
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* Invoice info banner */}
        <Card className="mb-6 bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-blue-900 text-sm">About Your GST Invoice</p>
                <p className="text-xs text-blue-700 mt-1">
                  As per GST regulations, a tax invoice is generated at the time of dispatch (Goods Issue).
                  You will receive the invoice by email when your order is shipped, and it will also be
                  available to download from your account.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Support */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">Need Help?</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <a
                href={`tel:${company?.phone?.replace(/[^0-9]/g, '') || '18001234567'}`}
                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Phone className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium">Call Us</p>
                  <p className="text-sm text-muted-foreground">{company?.phone || '1800-123-4567'}</p>
                </div>
              </a>
              <a
                href={`mailto:${company?.email || 'support@aquapurite.com'}`}
                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Mail className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium">Email Us</p>
                  <p className="text-sm text-muted-foreground">
                    {company?.email || 'support@aquapurite.com'}
                  </p>
                </div>
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href={`/track?order=${orderNumber}`}>
              Track My Order
              <Truck className="h-4 w-4 ml-2" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/account/orders">
              <Download className="h-4 w-4 mr-2" />
              My Orders & Invoices
            </Link>
          </Button>
          <Button size="lg" variant="ghost" asChild>
            <Link href="/products">
              Continue Shopping
              <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function OrderSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-pulse text-center">
            <div className="h-24 w-24 rounded-full bg-gray-200 mx-auto mb-4" />
            <div className="h-8 w-64 bg-gray-200 rounded mx-auto mb-2" />
            <div className="h-4 w-48 bg-gray-200 rounded mx-auto" />
          </div>
        </div>
      }
    >
      <OrderSuccessContent />
    </Suspense>
  );
}
