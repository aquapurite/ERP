import Link from 'next/link';
import { Truck, Clock, MapPin, Package, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function ShippingPage() {
  const shippingFeatures = [
    { icon: Truck, title: 'Free Shipping', description: 'On orders above ₹1,000' },
    { icon: Clock, title: 'Fast Delivery', description: '3-5 business days' },
    { icon: MapPin, title: 'Pan-India', description: 'Delivery across India' },
    { icon: Package, title: 'Safe Packaging', description: 'Secure & tamper-proof' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute top-10 left-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Shipping Policy
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Shipping &{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Delivery
              </span>
            </h1>
            <p className="text-lg text-slate-300">
              Fast, reliable delivery to your doorstep. Learn about our shipping options and policies.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-12 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {shippingFeatures.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 bg-amber-500/20 rounded-xl flex items-center justify-center">
                  <feature.icon className="w-6 h-6 text-amber-500" />
                </div>
                <h3 className="font-semibold text-white mb-1">{feature.title}</h3>
                <p className="text-sm text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Policy Content */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto space-y-8">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Shipping Charges</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">FREE Shipping:</strong> On all orders above ₹1,000</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Standard Shipping:</strong> ₹99 for orders below ₹1,000</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Remote Areas:</strong> Additional charges may apply for remote or hard-to-reach locations</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Delivery Timeline</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-4 bg-slate-900/50 rounded-lg">
                      <h4 className="font-semibold text-white mb-2">Metro Cities</h4>
                      <p className="text-sm">2-3 business days</p>
                      <p className="text-xs text-slate-500 mt-1">Delhi, Mumbai, Bangalore, Chennai, Kolkata, Hyderabad</p>
                    </div>
                    <div className="p-4 bg-slate-900/50 rounded-lg">
                      <h4 className="font-semibold text-white mb-2">Tier-2 Cities</h4>
                      <p className="text-sm">3-5 business days</p>
                      <p className="text-xs text-slate-500 mt-1">State capitals and major cities</p>
                    </div>
                    <div className="p-4 bg-slate-900/50 rounded-lg">
                      <h4 className="font-semibold text-white mb-2">Other Locations</h4>
                      <p className="text-sm">5-7 business days</p>
                      <p className="text-xs text-slate-500 mt-1">Smaller towns and remote areas</p>
                    </div>
                    <div className="p-4 bg-slate-900/50 rounded-lg">
                      <h4 className="font-semibold text-white mb-2">Express Delivery</h4>
                      <p className="text-sm">1-2 business days</p>
                      <p className="text-xs text-slate-500 mt-1">Available in select cities (extra charges)</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Serviceability</h2>
                <div className="space-y-4 text-slate-300">
                  <p>We deliver to most PIN codes across India. To check if we deliver to your area:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Enter your PIN code on the product page</li>
                    <li>Check during checkout before placing order</li>
                    <li>Contact our support for special delivery requests</li>
                  </ul>
                  <p className="text-sm text-slate-400">
                    Some remote areas may have limited delivery options. We'll contact you if there are any serviceability issues with your order.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Order Tracking</h2>
                <div className="space-y-4 text-slate-300">
                  <p>Once your order is shipped, you can track it through:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Our <Link href="/track" className="text-amber-500 hover:text-amber-400">Track Order</Link> page using your order number</li>
                    <li>Tracking link sent via SMS and email</li>
                    <li>Courier partner's website using AWB number</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Important Notes</h2>
                <div className="space-y-4 text-slate-300">
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Delivery times are estimates and may vary due to unforeseen circumstances</li>
                    <li>Orders placed after 2 PM may be processed the next business day</li>
                    <li>Weekends and public holidays are not counted as business days</li>
                    <li>Someone must be available to receive the delivery at the shipping address</li>
                    <li>Please ensure the address and contact details are accurate to avoid delivery issues</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <div className="text-center pt-4">
              <p className="text-slate-400 mb-4">Have questions about shipping?</p>
              <Link href="/contact" className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg transition-colors">
                Contact Us
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
