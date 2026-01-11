import Link from 'next/link';
import { Shield, Lock, Eye, Database, Bell, UserCheck, Mail } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute top-10 right-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Privacy Policy
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Your Privacy{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Matters
              </span>
            </h1>
            <p className="text-lg text-slate-300">
              We are committed to protecting your personal information and being transparent about how we use it.
            </p>
            <p className="text-sm text-slate-500 mt-4">Last updated: January 2025</p>
          </div>
        </div>
      </section>

      {/* Policy Content */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto space-y-8">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Database className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Information We Collect</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>We collect information to provide better services to our customers:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li><strong className="text-white">Personal Information:</strong> Name, email, phone number, and address when you create an account or place an order</li>
                    <li><strong className="text-white">Payment Information:</strong> Payment details are processed securely through our payment partners and not stored on our servers</li>
                    <li><strong className="text-white">Usage Data:</strong> Information about how you use our website, including pages visited and products viewed</li>
                    <li><strong className="text-white">Device Information:</strong> Browser type, IP address, and device identifiers</li>
                    <li><strong className="text-white">Communication Data:</strong> Records of your interactions with our customer support</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Eye className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">How We Use Your Information</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Process and fulfill your orders</li>
                    <li>Send order confirmations, shipping updates, and delivery notifications</li>
                    <li>Provide customer support and respond to inquiries</li>
                    <li>Improve our products, services, and website experience</li>
                    <li>Send promotional communications (with your consent)</li>
                    <li>Prevent fraud and ensure security</li>
                    <li>Comply with legal obligations</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Lock className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Data Security</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>We implement industry-standard security measures to protect your data:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>SSL encryption for all data transmission</li>
                    <li>Secure payment processing through trusted partners</li>
                    <li>Regular security audits and vulnerability assessments</li>
                    <li>Access controls limiting data access to authorized personnel</li>
                    <li>Secure data storage with encryption at rest</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <UserCheck className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Information Sharing</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>We do not sell your personal information. We may share data with:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li><strong className="text-white">Service Providers:</strong> Logistics partners for delivery, payment processors for transactions</li>
                    <li><strong className="text-white">Business Partners:</strong> Installation and service technicians</li>
                    <li><strong className="text-white">Legal Requirements:</strong> When required by law or to protect our rights</li>
                  </ul>
                  <p className="text-sm text-slate-400 mt-4">All third parties are contractually obligated to protect your information.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Bell className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Your Rights</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>You have the following rights regarding your personal data:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li><strong className="text-white">Access:</strong> Request a copy of your personal data</li>
                    <li><strong className="text-white">Correction:</strong> Update or correct inaccurate information</li>
                    <li><strong className="text-white">Deletion:</strong> Request deletion of your data (subject to legal requirements)</li>
                    <li><strong className="text-white">Opt-out:</strong> Unsubscribe from marketing communications</li>
                    <li><strong className="text-white">Portability:</strong> Receive your data in a structured format</li>
                  </ul>
                  <p className="mt-4">To exercise these rights, contact us at <a href="mailto:privacy@aquapurite.com" className="text-amber-500 hover:text-amber-400">privacy@aquapurite.com</a></p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="w-6 h-6 text-amber-500" />
                  <h2 className="text-xl font-bold text-white">Cookies & Tracking</h2>
                </div>
                <div className="space-y-4 text-slate-300">
                  <p>We use cookies and similar technologies to:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Remember your preferences and login status</li>
                    <li>Analyze website traffic and usage patterns</li>
                    <li>Provide personalized content and recommendations</li>
                    <li>Enable social media features</li>
                  </ul>
                  <p className="text-sm text-slate-400 mt-4">You can manage cookie preferences through your browser settings.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Policy Updates</h2>
                <div className="space-y-4 text-slate-300">
                  <p>We may update this privacy policy from time to time. Changes will be posted on this page with an updated revision date. We encourage you to review this policy periodically.</p>
                  <p>For significant changes, we will notify you via email or through a notice on our website.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-amber-500/20 to-blue-500/20 border-amber-500/30">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Contact Us</h2>
                <p className="text-slate-300 mb-4">
                  If you have questions about this privacy policy or how we handle your data, please contact us:
                </p>
                <div className="space-y-2">
                  <p className="flex items-center gap-2 text-slate-300">
                    <Mail className="w-4 h-4 text-amber-500" />
                    <a href="mailto:privacy@aquapurite.com" className="hover:text-amber-500">privacy@aquapurite.com</a>
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
