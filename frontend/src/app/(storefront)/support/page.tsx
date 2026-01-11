'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Headphones, MessageSquare, Phone, Mail, Package, Wrench, FileText, Clock, Search, ArrowRight, CheckCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function SupportPage() {
  const [orderNumber, setOrderNumber] = useState('');

  const supportOptions = [
    {
      icon: Phone,
      title: 'Call Us',
      description: 'Speak to our support team',
      action: 'Call Now',
      href: 'tel:+919013034083',
      detail: '+91 9013034083',
    },
    {
      icon: Mail,
      title: 'Email Support',
      description: 'Get help via email',
      action: 'Send Email',
      href: 'mailto:support@aquapurite.com',
      detail: 'support@aquapurite.com',
    },
    {
      icon: MessageSquare,
      title: 'Live Chat',
      description: 'Chat with our team',
      action: 'Start Chat',
      href: '#chat',
      detail: 'Available 9 AM - 7 PM',
    },
  ];

  const quickLinks = [
    { icon: Package, title: 'Track Order', description: 'Check your order status', href: '/track' },
    { icon: Wrench, title: 'Installation Help', description: 'Schedule or manage installation', href: '/installation' },
    { icon: FileText, title: 'FAQs', description: 'Find quick answers', href: '/faq' },
    { icon: Clock, title: 'Returns & Refunds', description: 'Initiate return or refund', href: '/returns' },
  ];

  const commonIssues = [
    { title: 'Order not delivered', description: 'Track or report delivery issues' },
    { title: 'Product not working', description: 'Troubleshoot or request service' },
    { title: 'Installation pending', description: 'Schedule or reschedule installation' },
    { title: 'Filter replacement', description: 'Order spare parts or schedule service' },
    { title: 'Refund status', description: 'Check refund processing status' },
    { title: 'Warranty claim', description: 'Submit warranty service request' },
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
              Customer Support
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              How Can We{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Help You?
              </span>
            </h1>
            <p className="text-lg text-slate-300 mb-8">
              Our dedicated support team is here to assist you with any questions or concerns.
            </p>

            {/* Quick Order Track */}
            <Card className="bg-slate-800/50 border-slate-700 max-w-md mx-auto">
              <CardContent className="p-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter Order Number"
                    value={orderNumber}
                    onChange={(e) => setOrderNumber(e.target.value)}
                    className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500 focus:border-amber-500"
                  />
                  <Link href={orderNumber ? `/track?order=${orderNumber}` : '/track'}>
                    <Button className="bg-amber-500 hover:bg-amber-600 text-slate-900">
                      <Search className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Contact Options */}
      <section className="py-12 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-6">
            {supportOptions.map((option, index) => (
              <Card key={index} className="bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-colors">
                <CardContent className="p-6 text-center">
                  <div className="w-14 h-14 mx-auto mb-4 bg-amber-500/20 rounded-xl flex items-center justify-center">
                    <option.icon className="w-7 h-7 text-amber-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">{option.title}</h3>
                  <p className="text-sm text-slate-400 mb-3">{option.description}</p>
                  <p className="text-sm text-amber-500 mb-4">{option.detail}</p>
                  <a href={option.href}>
                    <Button className="w-full bg-amber-500 hover:bg-amber-600 text-slate-900">
                      {option.action}
                    </Button>
                  </a>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">Quick Links</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quickLinks.map((link, index) => (
              <Link key={index} href={link.href}>
                <Card className="bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-colors h-full">
                  <CardContent className="p-6 flex items-start gap-4">
                    <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <link.icon className="w-5 h-5 text-blue-500" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white mb-1">{link.title}</h3>
                      <p className="text-sm text-slate-400">{link.description}</p>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Common Issues */}
      <section className="py-12 bg-slate-900/50">
        <div className="container mx-auto px-4">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">Common Issues</h2>
          <div className="max-w-3xl mx-auto">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="grid gap-4">
                  {commonIssues.map((issue, index) => (
                    <button
                      key={index}
                      className="flex items-center justify-between p-4 border border-slate-700 rounded-lg hover:border-amber-500/50 hover:bg-slate-800/50 transition-colors text-left"
                    >
                      <div>
                        <h4 className="font-medium text-white">{issue.title}</h4>
                        <p className="text-sm text-slate-400">{issue.description}</p>
                      </div>
                      <ArrowRight className="w-5 h-5 text-slate-500" />
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Business Hours */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <Card className="bg-gradient-to-r from-amber-500/20 to-blue-500/20 border-amber-500/30">
              <CardContent className="p-8">
                <div className="grid md:grid-cols-2 gap-8 items-center">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-4">Support Hours</h2>
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                        <span className="text-slate-300">Monday - Saturday: 9:00 AM - 7:00 PM</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                        <span className="text-slate-300">Phone & Chat: Real-time assistance</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                        <span className="text-slate-300">Email: Response within 24 hours</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-center md:text-right">
                    <p className="text-slate-400 mb-4">Need immediate assistance?</p>
                    <a href="tel:+919013034083">
                      <Button size="lg" className="bg-amber-500 hover:bg-amber-600 text-slate-900">
                        <Phone className="w-4 h-4 mr-2" />
                        Call Now
                      </Button>
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
