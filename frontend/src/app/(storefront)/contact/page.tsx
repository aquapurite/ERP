'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import {
  Phone,
  Mail,
  MapPin,
  Clock,
  Send,
  Loader2,
  MessageSquare,
  CheckCircle,
  MessageCircle,
  Headphones,
  Shield,
  Zap,
  Users,
  Building2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { companyApi } from '@/lib/storefront/api';

interface ContactForm {
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
}

// Quick contact options for common queries
const quickContactOptions = [
  {
    icon: Headphones,
    title: 'Customer Support',
    description: 'Get help with your existing order or product',
    action: 'support',
  },
  {
    icon: Shield,
    title: 'Warranty & AMC',
    description: 'Warranty claims, AMC renewals, service plans',
    action: 'warranty',
  },
  {
    icon: Users,
    title: 'Become a Partner',
    description: 'Join our partner network and earn commissions',
    action: 'partnership',
  },
  {
    icon: Building2,
    title: 'Bulk Orders',
    description: 'Corporate, institutional, or bulk purchases',
    action: 'bulk',
  },
];

export default function ContactPage() {
  const [form, setForm] = useState<ContactForm>({
    name: '',
    email: '',
    phone: '',
    subject: 'general',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const { data: company } = useQuery({
    queryKey: ['company-info'],
    queryFn: companyApi.getInfo,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.name || !form.email || !form.message) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);

    // Simulate form submission (in production, this would call an API)
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setIsSubmitting(false);
    setIsSubmitted(true);
    toast.success('Your message has been sent. We will get back to you soon!');
  };

  const handleChange = (field: keyof ContactForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  if (isSubmitted) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold mb-4">Message Sent Successfully!</h1>
          <p className="text-muted-foreground mb-4">
            Thank you for reaching out to AQUAPURITE. Our customer care team has received your message.
          </p>
          <div className="bg-muted/50 rounded-lg p-4 mb-6">
            <p className="text-sm font-medium mb-2">What happens next?</p>
            <ul className="text-sm text-muted-foreground text-left space-y-1">
              <li>• Our team will review your query within 2-4 hours</li>
              <li>• You will receive a confirmation email shortly</li>
              <li>• A support executive will contact you within 24 hours</li>
            </ul>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button onClick={() => setIsSubmitted(false)}>Send Another Message</Button>
            <Button variant="outline" asChild>
              <Link href="/faq">Browse FAQs</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 md:py-12">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-8">
        <Badge className="mb-4 bg-primary/10 text-primary hover:bg-primary/10">
          <MessageSquare className="h-3 w-3 mr-1" />
          We&apos;re Here to Help
        </Badge>
        <h1 className="text-3xl md:text-4xl font-bold mb-4">Contact AQUAPURITE</h1>
        <p className="text-lg text-muted-foreground">
          Have questions about water purifiers, need help with your order, or want to schedule a service? Our dedicated team is ready to assist you.
        </p>
      </div>

      {/* WhatsApp Quick Contact - Prominent CTA */}
      <div className="max-w-6xl mx-auto mb-8">
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <CardContent className="py-6">
            <div className="flex flex-col md:flex-row items-center gap-4 text-center md:text-left">
              <div className="p-3 bg-green-500 rounded-full">
                <MessageCircle className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-green-900 mb-1">
                  Need Quick Help? Chat on WhatsApp
                </h3>
                <p className="text-sm text-green-700">
                  Get instant support from our team. Available Mon-Sat, 9 AM - 8 PM IST.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-white text-green-700 border-green-300">
                  <Zap className="h-3 w-3 mr-1" />
                  Avg. response: 5 min
                </Badge>
                <Button className="bg-green-600 hover:bg-green-700" asChild>
                  <a
                    href="https://wa.me/919311939076?text=Hi, I need help with AQUAPURITE water purifiers"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Chat Now
                  </a>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Contact Options */}
      <div className="max-w-6xl mx-auto mb-8">
        <h2 className="text-lg font-semibold mb-4 text-center">How can we help you today?</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickContactOptions.map((option) => {
            const Icon = option.icon;
            return (
              <Card
                key={option.action}
                className="cursor-pointer hover:border-primary/50 hover:shadow-md transition-all"
                onClick={() => handleChange('subject', option.action)}
              >
                <CardContent className="pt-6 text-center">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-medium text-sm mb-1">{option.title}</h3>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {/* Contact Information */}
        <div className="lg:col-span-1 space-y-4">
          {/* Phone */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <Phone className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Call Us</h3>
                  <p className="text-muted-foreground text-sm mb-2">
                    Sales & Support Helpline
                  </p>
                  <a
                    href={`tel:${company?.phone || '+919311939076'}`}
                    className="text-primary hover:underline font-medium text-lg"
                  >
                    {company?.phone || '+91 93119 39076'}
                  </a>
                  <p className="text-xs text-muted-foreground mt-1">
                    Mon-Sat, 9:00 AM - 8:00 PM IST
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* WhatsApp */}
          <Card className="border-green-200 bg-green-50/50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center shrink-0">
                  <MessageCircle className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">WhatsApp</h3>
                  <p className="text-muted-foreground text-sm mb-2">
                    Quick chat support
                  </p>
                  <a
                    href="https://wa.me/919311939076"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:underline font-medium text-lg"
                  >
                    +91 93119 39076
                  </a>
                  <Badge variant="outline" className="ml-2 text-xs bg-white border-green-300 text-green-700">
                    Fastest
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Email */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <Mail className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Email Us</h3>
                  <p className="text-muted-foreground text-sm mb-2">
                    For detailed queries & documents
                  </p>
                  <a
                    href={`mailto:${company?.email || 'support@aquapurite.com'}`}
                    className="text-primary hover:underline font-medium"
                  >
                    {company?.email || 'support@aquapurite.com'}
                  </a>
                  <p className="text-xs text-muted-foreground mt-1">
                    Response within 24 hours
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Address */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <MapPin className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Corporate Office</h3>
                  <p className="text-muted-foreground text-sm">
                    {company?.address || 'AQUAPURITE Water Solutions'}
                    <br />
                    {company?.city || 'Delhi'}, {company?.state || 'Delhi'}
                    <br />
                    {company?.pincode || '110001'}, India
                  </p>
                  <Button variant="link" size="sm" className="px-0 h-auto mt-2 text-primary" asChild>
                    <a
                      href="https://maps.google.com/?q=Delhi,India"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Get Directions →
                    </a>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Support Hours */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <Clock className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-2">Support Hours</h3>
                  <div className="text-sm space-y-1">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monday - Saturday</span>
                      <span className="font-medium">9:00 AM - 8:00 PM</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Sunday</span>
                      <span className="font-medium text-orange-600">Emergency Only</span>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs text-green-600 flex items-center gap-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      24/7 online service booking available
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Contact Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <CardTitle>Send us a Message</CardTitle>
            </div>
            <CardDescription>
              Fill out the form below and we&apos;ll get back to you as soon as possible.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    Full Name <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="name"
                    placeholder="Your name"
                    value={form.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">
                    Email <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={form.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="+91 98765 43210"
                    value={form.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="subject">Subject *</Label>
                  <Select
                    value={form.subject}
                    onValueChange={(value) => handleChange('subject', value)}
                  >
                    <SelectTrigger id="subject">
                      <SelectValue placeholder="What can we help you with?" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="support">Customer Support</SelectItem>
                      <SelectItem value="product">Product Information</SelectItem>
                      <SelectItem value="order">Order Status / Delivery</SelectItem>
                      <SelectItem value="installation">Installation Query</SelectItem>
                      <SelectItem value="service">Service Request</SelectItem>
                      <SelectItem value="warranty">Warranty Claim</SelectItem>
                      <SelectItem value="amc">AMC / Service Plans</SelectItem>
                      <SelectItem value="partnership">Become a Partner</SelectItem>
                      <SelectItem value="bulk">Bulk / Corporate Order</SelectItem>
                      <SelectItem value="complaint">Complaint</SelectItem>
                      <SelectItem value="feedback">Feedback / Suggestion</SelectItem>
                      <SelectItem value="general">General Inquiry</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">
                  Message <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="message"
                  placeholder="Please describe your query in detail. Include order number, product model, or any relevant information that can help us assist you better..."
                  rows={5}
                  value={form.message}
                  onChange={(e) => handleChange('message', e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  For faster resolution, please include your order number or registered phone number.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <Button type="submit" className="w-full sm:w-auto" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Send Message
                    </>
                  )}
                </Button>
                <p className="text-xs text-muted-foreground">
                  We typically respond within 24 hours
                </p>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Additional Resources */}
      <div className="max-w-6xl mx-auto mt-12 grid md:grid-cols-3 gap-6">
        {/* FAQ Link */}
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
              <MessageSquare className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold mb-2">Frequently Asked Questions</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Find instant answers to common questions about products, orders, and services.
            </p>
            <Button variant="outline" asChild>
              <Link href="/faq">Browse FAQs</Link>
            </Button>
          </CardContent>
        </Card>

        {/* Video Guides */}
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
              <Headphones className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold mb-2">Installation & Maintenance</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Watch step-by-step video guides for installation and troubleshooting.
            </p>
            <Button variant="outline" asChild>
              <Link href="/guides">View Guides</Link>
            </Button>
          </CardContent>
        </Card>

        {/* Service Request */}
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold mb-2">Book a Service</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Schedule installation, repair, or maintenance service at your convenience.
            </p>
            <Button variant="outline" asChild>
              <Link href="/account/services">Book Service</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Trust Badges */}
      <div className="max-w-4xl mx-auto mt-12 text-center">
        <p className="text-sm text-muted-foreground mb-4">Trusted by 50,000+ happy families across India</p>
        <div className="flex flex-wrap justify-center gap-8">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span>ISO 9001 Certified</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span>100% Genuine Products</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span>Pan-India Service Network</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span>Expert Technicians</span>
          </div>
        </div>
      </div>
    </div>
  );
}
