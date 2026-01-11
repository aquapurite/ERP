'use client';

import {
  Droplets,
  Shield,
  Award,
  Truck,
  Headphones,
  Wrench,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const features = [
  {
    icon: Droplets,
    title: '7-Stage Purification',
    description: 'Advanced RO+UV+UF technology for 100% pure drinking water',
  },
  {
    icon: Shield,
    title: '1 Year Warranty',
    description: 'Comprehensive warranty coverage on all products',
  },
  {
    icon: Award,
    title: 'ISI Certified',
    description: 'All products meet Indian quality standards',
  },
  {
    icon: Truck,
    title: 'Free Installation',
    description: 'Professional installation by trained technicians',
  },
  {
    icon: Headphones,
    title: '24/7 Support',
    description: 'Round-the-clock customer service support',
  },
  {
    icon: Wrench,
    title: 'AMC Plans',
    description: 'Annual maintenance contracts for hassle-free service',
  },
];

export default function WhyChooseUs() {
  return (
    <section className="py-12 md:py-16 bg-primary text-primary-foreground">
      <div className="container mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-2xl md:text-3xl font-bold mb-2">
            Why Choose AQUAPURITE?
          </h2>
          <p className="text-primary-foreground/80">
            India's most trusted water purification brand
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="bg-white/10 border-white/20 hover:bg-white/20 transition-colors"
            >
              <CardContent className="p-4 md:p-6 text-center">
                <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-white/20 mb-4">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="font-semibold mb-1 text-sm md:text-base">
                  {feature.title}
                </h3>
                <p className="text-xs md:text-sm text-primary-foreground/70">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
