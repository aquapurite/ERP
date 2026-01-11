import Link from 'next/link';
import { RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle, Package } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function ReturnsPage() {
  const returnProcess = [
    { step: 1, title: 'Request Return', description: 'Contact support with order details' },
    { step: 2, title: 'Get Approval', description: 'Return request reviewed within 24 hours' },
    { step: 3, title: 'Ship Product', description: 'Pack and ship or schedule pickup' },
    { step: 4, title: 'Receive Refund', description: 'Refund processed after inspection' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute top-10 right-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Return Policy
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Returns &{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Refunds
              </span>
            </h1>
            <p className="text-lg text-slate-300">
              We want you to be completely satisfied with your purchase. Learn about our hassle-free return and refund policies.
            </p>
          </div>
        </div>
      </section>

      {/* Return Process */}
      <section className="py-12 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <h2 className="text-2xl font-bold text-white text-center mb-8">Return Process</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {returnProcess.map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 bg-amber-500 rounded-full flex items-center justify-center">
                  <span className="text-lg font-bold text-slate-900">{item.step}</span>
                </div>
                <h3 className="font-semibold text-white mb-1">{item.title}</h3>
                <p className="text-sm text-slate-400">{item.description}</p>
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
                <h2 className="text-xl font-bold text-white mb-4">Return Eligibility</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">7-Day Return Window:</strong> Return requests must be raised within 7 days of delivery</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Unused Condition:</strong> Product must be unused, in original packaging with all accessories</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Complete Documentation:</strong> Invoice, warranty card, and all original documents must be included</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Non-Returnable Items</h2>
                <div className="space-y-4 text-slate-300">
                  <p className="text-sm text-slate-400 mb-4">The following items cannot be returned for hygiene and safety reasons:</p>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="flex items-start gap-3">
                      <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                      <p>Filters and membranes (opened)</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                      <p>Installed water purifiers</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                      <p>Consumables and cartridges</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                      <p>Products without original packaging</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Refund Process</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="p-4 bg-slate-900/50 rounded-lg">
                    <h4 className="font-semibold text-white mb-2">Online Payments</h4>
                    <p className="text-sm">Refund processed to original payment method within 5-7 business days after product inspection</p>
                  </div>
                  <div className="p-4 bg-slate-900/50 rounded-lg">
                    <h4 className="font-semibold text-white mb-2">Cash on Delivery</h4>
                    <p className="text-sm">Refund via bank transfer. Please provide bank details when raising return request</p>
                  </div>
                  <div className="flex items-start gap-3 mt-4">
                    <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p className="text-sm">Shipping charges are non-refundable unless the return is due to our error</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Damaged or Defective Products</h2>
                <div className="space-y-4 text-slate-300">
                  <p>If you receive a damaged or defective product:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Report within 24 hours of delivery</li>
                    <li>Share photos/videos of the damage</li>
                    <li>Keep original packaging intact</li>
                    <li>We'll arrange free pickup and replacement/refund</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">How to Initiate a Return</h2>
                <div className="space-y-4 text-slate-300">
                  <ol className="list-decimal list-inside space-y-3 ml-4">
                    <li>Contact our support team via phone, email, or chat</li>
                    <li>Provide order number and reason for return</li>
                    <li>Our team will review and approve the request</li>
                    <li>Pack the product securely with all accessories</li>
                    <li>Ship using provided label or schedule pickup</li>
                    <li>Refund processed after quality inspection</li>
                  </ol>
                </div>
              </CardContent>
            </Card>

            <div className="text-center pt-4">
              <p className="text-slate-400 mb-4">Need to initiate a return?</p>
              <Link href="/support" className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg transition-colors">
                <RefreshCw className="w-4 h-4 mr-2" />
                Contact Support
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
