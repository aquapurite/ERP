'use client';

import { useState } from 'react';
import Link from 'next/link';
import { MapPin, Phone, Mail, Clock, Send, Loader2, CheckCircle, MessageSquare, Headphones } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function ContactPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 1500));

    setIsSubmitting(false);
    setIsSubmitted(true);
    setFormData({ name: '', email: '', phone: '', subject: '', message: '' });
  };

  const contactInfo = [
    {
      icon: MapPin,
      title: 'Visit Us',
      details: ['Plot 36-A, KH NO 181, PH-1', 'Shyam Vihar, Najafgarh', 'New Delhi - 110043'],
    },
    {
      icon: Phone,
      title: 'Call Us',
      details: ['+91 9013034083', '+91 9013034084'],
      links: ['tel:+919013034083', 'tel:+919013034084'],
    },
    {
      icon: Mail,
      title: 'Email Us',
      details: ['info@aquapurite.com', 'support@aquapurite.com'],
      links: ['mailto:info@aquapurite.com', 'mailto:support@aquapurite.com'],
    },
    {
      icon: Clock,
      title: 'Business Hours',
      details: ['Monday - Saturday', '9:00 AM - 7:00 PM', 'Sunday: Closed'],
    },
  ];

  const quickLinks = [
    { icon: Headphones, title: 'Customer Support', description: 'Get help with your orders and products', href: '/support' },
    { icon: MessageSquare, title: 'FAQs', description: 'Find answers to common questions', href: '/faq' },
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
              Contact Us
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              We'd Love to{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Hear From You
              </span>
            </h1>
            <p className="text-lg text-slate-300">
              Have questions about our products or services? Our team is here to help you find the perfect water purification solution.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Info Cards */}
      <section className="py-12 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {contactInfo.map((info, index) => (
              <Card key={index} className="bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-colors">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 mx-auto mb-4 bg-amber-500/20 rounded-xl flex items-center justify-center">
                    <info.icon className="w-6 h-6 text-amber-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-3">{info.title}</h3>
                  <div className="space-y-1">
                    {info.details.map((detail, i) => (
                      info.links ? (
                        <a
                          key={i}
                          href={info.links[i]}
                          className="block text-slate-400 hover:text-amber-500 transition-colors"
                        >
                          {detail}
                        </a>
                      ) : (
                        <p key={i} className="text-slate-400">{detail}</p>
                      )
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Form & Map */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Form */}
            <div>
              <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 mb-4">
                Send a Message
              </Badge>
              <h2 className="text-2xl font-bold text-white mb-6">Get in Touch</h2>

              {isSubmitted ? (
                <Card className="bg-emerald-500/10 border-emerald-500/30">
                  <CardContent className="p-8 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 bg-emerald-500/20 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-8 h-8 text-emerald-500" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Message Sent!</h3>
                    <p className="text-slate-400 mb-4">
                      Thank you for contacting us. We'll get back to you within 24 hours.
                    </p>
                    <Button
                      onClick={() => setIsSubmitted(false)}
                      variant="outline"
                      className="border-slate-600 text-slate-300 hover:text-amber-500 hover:border-amber-500"
                    >
                      Send Another Message
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardContent className="p-6">
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="grid sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="name" className="text-slate-300">Full Name *</Label>
                          <Input
                            id="name"
                            required
                            placeholder="John Doe"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500 focus:border-amber-500 focus:ring-amber-500/20"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="phone" className="text-slate-300">Phone Number *</Label>
                          <Input
                            id="phone"
                            required
                            placeholder="9876543210"
                            maxLength={10}
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value.replace(/\D/g, '') })}
                            className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500 focus:border-amber-500 focus:ring-amber-500/20"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="email" className="text-slate-300">Email Address *</Label>
                        <Input
                          id="email"
                          type="email"
                          required
                          placeholder="john@example.com"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500 focus:border-amber-500 focus:ring-amber-500/20"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="subject" className="text-slate-300">Subject *</Label>
                        <Input
                          id="subject"
                          required
                          placeholder="How can we help you?"
                          value={formData.subject}
                          onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                          className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500 focus:border-amber-500 focus:ring-amber-500/20"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="message" className="text-slate-300">Message *</Label>
                        <Textarea
                          id="message"
                          required
                          placeholder="Tell us more about your inquiry..."
                          rows={5}
                          value={formData.message}
                          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                          className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500 focus:border-amber-500 focus:ring-amber-500/20"
                        />
                      </div>

                      <Button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
                      >
                        {isSubmitting ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Sending...
                          </>
                        ) : (
                          <>
                            <Send className="h-4 w-4 mr-2" />
                            Send Message
                          </>
                        )}
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Map & Quick Links */}
            <div className="space-y-6">
              <div>
                <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
                  Our Location
                </Badge>
                <h2 className="text-2xl font-bold text-white mb-6">Find Us Here</h2>
                <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
                  <div className="aspect-video bg-slate-700 flex items-center justify-center">
                    <iframe
                      src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3503.0254123456789!2d76.9!3d28.6!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjjCsDM2JzAwLjAiTiA3NsKwNTQnMDAuMCJF!5e0!3m2!1sen!2sin!4v1234567890"
                      width="100%"
                      height="100%"
                      style={{ border: 0, minHeight: '300px' }}
                      allowFullScreen
                      loading="lazy"
                      referrerPolicy="no-referrer-when-downgrade"
                      className="grayscale opacity-80"
                    />
                  </div>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <MapPin className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                      <div className="text-slate-300 text-sm">
                        Plot 36-A, KH NO 181, PH-1, Shyam Vihar, Najafgarh, New Delhi - 110043
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Quick Links */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Quick Links</h3>
                <div className="grid gap-4">
                  {quickLinks.map((link, index) => (
                    <Link key={index} href={link.href}>
                      <Card className="bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-colors">
                        <CardContent className="p-4 flex items-center gap-4">
                          <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                            <link.icon className="w-5 h-5 text-amber-500" />
                          </div>
                          <div>
                            <h4 className="font-medium text-white">{link.title}</h4>
                            <p className="text-sm text-slate-400">{link.description}</p>
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
