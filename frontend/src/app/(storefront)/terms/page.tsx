import Link from 'next/link';
import { FileText, CheckSquare, AlertTriangle, Scale, Shield, Mail } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function TermsPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute top-10 left-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Legal
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Terms &{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Conditions
              </span>
            </h1>
            <p className="text-lg text-slate-300">
              Please read these terms and conditions carefully before using our website and services.
            </p>
            <p className="text-sm text-slate-500 mt-4">Last updated: January 2025</p>
          </div>
        </div>
      </section>

      {/* Terms Content */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto space-y-8">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <CheckSquare className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Acceptance of Terms</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>By accessing and using the Aquapurite website (www.aquapurite.com) and services, you agree to be bound by these Terms and Conditions. If you do not agree to these terms, please do not use our services.</p>
                  <p>These terms apply to all visitors, users, and customers who access or use our website.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <FileText className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Use of Website</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>You agree to use our website only for lawful purposes and in accordance with these terms:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>You must be at least 18 years old to place orders</li>
                    <li>You are responsible for maintaining the confidentiality of your account</li>
                    <li>You must provide accurate and complete information during registration and checkout</li>
                    <li>You must not use the site for any fraudulent or illegal purposes</li>
                    <li>You must not attempt to gain unauthorized access to our systems</li>
                    <li>You must not interfere with the proper functioning of the website</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Products and Pricing</h2>
                <div className="space-y-4 text-slate-300">
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>All products are subject to availability</li>
                    <li>Prices are displayed in Indian Rupees (INR) and include applicable taxes</li>
                    <li>We reserve the right to modify prices without prior notice</li>
                    <li>Product images are for illustration purposes; actual products may vary slightly</li>
                    <li>We strive for accuracy but do not guarantee that descriptions are error-free</li>
                    <li>We reserve the right to limit order quantities</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Orders and Payment</h2>
                <div className="space-y-4 text-slate-300">
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Placing an order constitutes an offer to purchase, which we may accept or reject</li>
                    <li>Orders are confirmed only upon receipt of payment (for prepaid) or dispatch (for COD)</li>
                    <li>We accept various payment methods as displayed during checkout</li>
                    <li>You represent that you have the right to use the payment method provided</li>
                    <li>We reserve the right to cancel orders suspected of fraud</li>
                    <li>Prices charged are those displayed at the time of order placement</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Shipping and Delivery</h2>
                <div className="space-y-4 text-slate-300">
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Delivery timelines are estimates and not guaranteed</li>
                    <li>Risk of loss transfers to you upon delivery</li>
                    <li>Ensure someone is available at the delivery address to receive the order</li>
                    <li>Multiple delivery attempts may be made before returning to warehouse</li>
                    <li>Additional charges may apply for re-delivery</li>
                  </ul>
                  <p className="mt-4">For detailed shipping information, please see our <Link href="/shipping" className="text-amber-500 hover:text-amber-400">Shipping Policy</Link>.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Returns and Refunds</h2>
                <div className="space-y-4 text-slate-300">
                  <p>Our return and refund policy is subject to the following conditions:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Returns must be initiated within 7 days of delivery</li>
                    <li>Products must be unused and in original packaging</li>
                    <li>Certain products are non-returnable (filters, consumables)</li>
                    <li>Refunds are processed within 5-7 business days after inspection</li>
                  </ul>
                  <p className="mt-4">For detailed return information, please see our <Link href="/returns" className="text-amber-500 hover:text-amber-400">Return Policy</Link>.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Warranty</h2>
                <div className="space-y-4 text-slate-300">
                  <p>Products are covered under manufacturer warranty as specified on product pages. Warranty terms, coverage, and limitations are detailed in our <Link href="/warranty" className="text-amber-500 hover:text-amber-400">Warranty Policy</Link>.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Intellectual Property</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>All content on this website, including but not limited to:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Text, graphics, logos, and images</li>
                    <li>Product descriptions and specifications</li>
                    <li>Software and source code</li>
                    <li>Trademarks and brand elements</li>
                  </ul>
                  <p className="mt-4">are the property of Aquapurite Private Limited or its licensors and are protected by copyright and trademark laws. You may not reproduce, distribute, or create derivative works without written permission.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <AlertTriangle className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Limitation of Liability</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>To the maximum extent permitted by law:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>We shall not be liable for any indirect, incidental, or consequential damages</li>
                    <li>Our total liability shall not exceed the amount paid for the specific product or service</li>
                    <li>We are not liable for delays or failures due to circumstances beyond our control</li>
                    <li>We do not warrant that the website will be error-free or uninterrupted</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Indemnification</h2>
                <div className="space-y-4 text-slate-300">
                  <p>You agree to indemnify and hold harmless Aquapurite Private Limited, its officers, directors, employees, and agents from any claims, damages, losses, or expenses arising from:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Your violation of these terms</li>
                    <li>Your use of our products or services</li>
                    <li>Your violation of any third-party rights</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Scale className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Governing Law & Disputes</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>These terms shall be governed by the laws of India. Any disputes arising from these terms or use of our services shall be subject to the exclusive jurisdiction of the courts in New Delhi, India.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Changes to Terms</h2>
                <div className="space-y-4 text-slate-300">
                  <p>We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting on the website. Your continued use of our services after changes constitutes acceptance of the modified terms.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-amber-500/20 to-blue-500/20 border-amber-500/30">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Contact Us</h2>
                <p className="text-slate-300 mb-4">
                  If you have any questions about these Terms and Conditions, please contact us:
                </p>
                <div className="space-y-2">
                  <p className="flex items-center gap-2 text-slate-300">
                    <Mail className="w-4 h-4 text-amber-500" />
                    <a href="mailto:legal@aquapurite.com" className="hover:text-amber-500">legal@aquapurite.com</a>
                  </p>
                  <p className="text-slate-300">
                    Aquapurite Private Limited<br />
                    Plot 36-A, KH NO 181, PH-1, Shyam Vihar<br />
                    Najafgarh, New Delhi - 110043
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
