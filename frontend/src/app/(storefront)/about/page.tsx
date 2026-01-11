import Link from 'next/link';
import { Droplets, Award, Users, Target, Heart, Shield, Truck, CheckCircle, MapPin, Phone, Mail } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function AboutPage() {
  const stats = [
    { value: '10+', label: 'Years Experience' },
    { value: '50K+', label: 'Happy Customers' },
    { value: '100+', label: 'Cities Served' },
    { value: '99%', label: 'Satisfaction Rate' },
  ];

  const values = [
    {
      icon: Heart,
      title: 'Customer First',
      description: 'We put our customers at the heart of everything we do, ensuring their satisfaction is our top priority.',
    },
    {
      icon: Shield,
      title: 'Quality Assurance',
      description: 'Every product undergoes rigorous testing to meet the highest quality standards before reaching you.',
    },
    {
      icon: Target,
      title: 'Innovation',
      description: 'We constantly innovate to bring you the latest and most efficient water purification technologies.',
    },
    {
      icon: Users,
      title: 'Expert Team',
      description: 'Our team of water experts and technicians are dedicated to providing exceptional service.',
    },
  ];

  const milestones = [
    { year: '2015', title: 'Company Founded', description: 'Started with a vision to provide pure water to every household.' },
    { year: '2017', title: 'First 10,000 Customers', description: 'Reached our first major milestone of satisfied customers.' },
    { year: '2019', title: 'Pan-India Expansion', description: 'Expanded operations to serve customers across all major cities.' },
    { year: '2021', title: 'Service Excellence Award', description: 'Recognized for outstanding customer service in the industry.' },
    { year: '2023', title: '50,000+ Customers', description: 'Celebrated serving over 50,000 happy households.' },
    { year: '2025', title: 'Digital Innovation', description: 'Launched D2C platform for seamless customer experience.' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute top-20 left-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              About Aquapurite
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Bringing Pure Water to{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Every Home
              </span>
            </h1>
            <p className="text-lg text-slate-300 mb-8">
              At Aquapurite, we believe that access to clean, pure drinking water is a fundamental right.
              Our mission is to provide innovative water purification solutions that ensure health and
              well-being for families across India.
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-slate-800 bg-slate-900/50">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-amber-500 mb-2">{stat.value}</div>
                <div className="text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Our Story */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 mb-4">
                Our Story
              </Badge>
              <h2 className="text-3xl font-bold text-white mb-6">
                A Decade of Commitment to Pure Water
              </h2>
              <div className="space-y-4 text-slate-300">
                <p>
                  Founded in 2015, Aquapurite began with a simple yet powerful vision: to ensure that every
                  Indian household has access to safe, pure drinking water. What started as a small venture
                  has grown into one of the most trusted names in water purification.
                </p>
                <p>
                  Our journey has been marked by continuous innovation, unwavering commitment to quality,
                  and a deep understanding of our customers' needs. We've developed advanced RO, UV, and UF
                  purification technologies that deliver the purest water possible.
                </p>
                <p>
                  Today, we're proud to serve over 50,000 households across India, providing them with
                  reliable water purification solutions and exceptional after-sales service.
                </p>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-amber-500/20 to-blue-500/20 rounded-2xl flex items-center justify-center">
                <Droplets className="w-32 h-32 text-amber-500" />
              </div>
              <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-amber-500 rounded-xl flex items-center justify-center">
                <Award className="w-12 h-12 text-slate-900" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Our Values */}
      <section className="py-16 bg-slate-900/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Our Values
            </Badge>
            <h2 className="text-3xl font-bold text-white mb-4">What Drives Us</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Our core values guide every decision we make and every product we create.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <Card key={index} className="bg-slate-800/50 border-slate-700 hover:border-amber-500/50 transition-colors">
                <CardContent className="p-6 text-center">
                  <div className="w-14 h-14 mx-auto mb-4 bg-amber-500/20 rounded-xl flex items-center justify-center">
                    <value.icon className="w-7 h-7 text-amber-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{value.title}</h3>
                  <p className="text-sm text-slate-400">{value.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 mb-4">
              Our Journey
            </Badge>
            <h2 className="text-3xl font-bold text-white mb-4">Milestones We're Proud Of</h2>
          </div>
          <div className="max-w-3xl mx-auto">
            <div className="relative">
              <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-slate-700" />
              {milestones.map((milestone, index) => (
                <div key={index} className="relative flex gap-6 pb-8 last:pb-0">
                  <div className="w-16 h-16 rounded-full bg-slate-800 border-2 border-amber-500 flex items-center justify-center flex-shrink-0 z-10">
                    <span className="text-amber-500 font-bold text-sm">{milestone.year}</span>
                  </div>
                  <div className="pt-3">
                    <h3 className="text-lg font-semibold text-white mb-1">{milestone.title}</h3>
                    <p className="text-slate-400">{milestone.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="py-16 bg-slate-900/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Why Choose Us
            </Badge>
            <h2 className="text-3xl font-bold text-white mb-4">The Aquapurite Advantage</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <CheckCircle className="w-6 h-6 text-emerald-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Genuine Products</h3>
                <p className="text-slate-400">100% authentic products with manufacturer warranty and quality assurance.</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-amber-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Truck className="w-6 h-6 text-amber-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Pan-India Delivery</h3>
                <p className="text-slate-400">Fast and reliable delivery to your doorstep across all major cities.</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Shield className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Expert Support</h3>
                <p className="text-slate-400">Dedicated customer support and professional installation services.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact CTA */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <Card className="bg-gradient-to-r from-amber-500/20 to-blue-500/20 border-amber-500/30">
            <CardContent className="p-8 md:p-12">
              <div className="grid md:grid-cols-2 gap-8 items-center">
                <div>
                  <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                    Get in Touch With Us
                  </h2>
                  <p className="text-slate-300 mb-6">
                    Have questions about our products or services? Our team is here to help you find the perfect water purification solution.
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 text-slate-300">
                      <MapPin className="w-5 h-5 text-amber-500" />
                      <span>Plot 36-A, KH NO 181, PH-1, Shyam Vihar, Najafgarh, New Delhi - 110043</span>
                    </div>
                    <div className="flex items-center gap-3 text-slate-300">
                      <Phone className="w-5 h-5 text-amber-500" />
                      <a href="tel:+919013034083" className="hover:text-amber-500">+91 9013034083</a>
                    </div>
                    <div className="flex items-center gap-3 text-slate-300">
                      <Mail className="w-5 h-5 text-amber-500" />
                      <a href="mailto:info@aquapurite.com" className="hover:text-amber-500">info@aquapurite.com</a>
                    </div>
                  </div>
                </div>
                <div className="text-center md:text-right">
                  <Link href="/contact" className="inline-flex items-center justify-center px-8 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg transition-colors">
                    Contact Us
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
