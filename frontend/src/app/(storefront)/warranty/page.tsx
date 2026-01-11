import Link from 'next/link';
import { Shield, CheckCircle, XCircle, Clock, Wrench, FileText, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function WarrantyPage() {
  const warrantyTypes = [
    { title: 'Water Purifiers', duration: '1-2 Years', coverage: 'Manufacturing defects' },
    { title: 'Filters & Membranes', duration: '6 Months', coverage: 'Performance guarantee' },
    { title: 'Motors & Pumps', duration: '1 Year', coverage: 'Electrical components' },
    { title: 'Accessories', duration: '6 Months', coverage: 'Material defects' },
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
              Warranty Policy
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Warranty{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Information
              </span>
            </h1>
            <p className="text-lg text-slate-300">
              We stand behind our products with comprehensive warranty coverage for your peace of mind.
            </p>
          </div>
        </div>
      </section>

      {/* Warranty Overview */}
      <section className="py-12 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-6">
            {warrantyTypes.map((item, index) => (
              <Card key={index} className="bg-slate-800/50 border-slate-700 text-center">
                <CardContent className="p-6">
                  <div className="w-12 h-12 mx-auto mb-3 bg-amber-500/20 rounded-xl flex items-center justify-center">
                    <Shield className="w-6 h-6 text-amber-500" />
                  </div>
                  <h3 className="font-semibold text-white mb-1">{item.title}</h3>
                  <p className="text-2xl font-bold text-amber-500 mb-1">{item.duration}</p>
                  <p className="text-sm text-slate-400">{item.coverage}</p>
                </CardContent>
              </Card>
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
                <h2 className="text-xl font-bold text-white mb-4">What's Covered</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p>Manufacturing defects in materials and workmanship</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p>Electrical component failures under normal use</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p>Pump and motor malfunctions</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p>Tank and body structural defects</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p>Free repair or replacement of defective parts</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">What's Not Covered</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p>Damage due to misuse, neglect, or improper handling</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p>Damage from power surges or voltage fluctuations</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p>Unauthorized repairs or modifications</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p>Normal wear and tear, consumables, and filters</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p>Damage from natural disasters or external factors</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p>Installation issues if not done by authorized personnel</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">How to Claim Warranty</h2>
                <div className="space-y-4 text-slate-300">
                  <ol className="list-decimal list-inside space-y-3 ml-4">
                    <li>Keep your purchase invoice and warranty card safe</li>
                    <li>Contact our support team with product details and issue description</li>
                    <li>Our technician will diagnose the issue (on-site or remote)</li>
                    <li>If covered under warranty, repair/replacement will be done free of charge</li>
                    <li>Service completion confirmation will be provided</li>
                  </ol>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Important Guidelines</h2>
                <div className="space-y-4 text-slate-300">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Registration:</strong> Register your product within 15 days of purchase for warranty activation</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Service:</strong> Regular servicing by authorized technicians helps maintain warranty validity</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p><strong className="text-white">Genuine Parts:</strong> Only use genuine Aquapurite spare parts and consumables</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-amber-500/20 to-blue-500/20 border-amber-500/30">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">Extended Warranty & AMC</h2>
                <p className="text-slate-300 mb-4">
                  Extend your peace of mind with our Annual Maintenance Contracts (AMC). Get comprehensive coverage including:
                </p>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <span className="text-slate-300">Scheduled preventive maintenance</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <span className="text-slate-300">Priority support response</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <span className="text-slate-300">Discounted spare parts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <span className="text-slate-300">Free service visits</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="text-center pt-4">
              <p className="text-slate-400 mb-4">Need warranty service?</p>
              <Link href="/support" className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg transition-colors">
                <Wrench className="w-4 h-4 mr-2" />
                Request Service
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
