'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Banner {
  id: string;
  title: string;
  subtitle: string;
  image: string;
  cta_text: string;
  cta_link: string;
}

const banners: Banner[] = [
  {
    id: '1',
    title: 'Pure Water, Healthy Life',
    subtitle: 'Advanced 7-Stage RO Purification with Mineral Enrichment',
    image: 'https://images.unsplash.com/photo-1559839914-17aae19cec71?q=80&w=2070',
    cta_text: 'Shop Now',
    cta_link: '/products',
  },
  {
    id: '2',
    title: 'New Arrivals',
    subtitle: 'Discover our latest water purifiers with smart features',
    image: 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?q=80&w=2076',
    cta_text: 'Explore',
    cta_link: '/products?is_new_arrival=true',
  },
  {
    id: '3',
    title: 'Free Installation',
    subtitle: 'Get free installation on all water purifiers',
    image: 'https://images.unsplash.com/photo-1562016600-ece13e8ba570?q=80&w=2069',
    cta_text: 'Learn More',
    cta_link: '/products',
  },
];

export default function HeroBanner() {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % banners.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  const goToPrev = () => {
    setCurrentSlide((prev) => (prev - 1 + banners.length) % banners.length);
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % banners.length);
  };

  return (
    <section className="relative w-full h-[400px] md:h-[500px] lg:h-[600px] overflow-hidden">
      {/* Slides */}
      {banners.map((banner, index) => (
        <div
          key={banner.id}
          className={`absolute inset-0 transition-opacity duration-1000 ${
            index === currentSlide ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {/* Background Image */}
          <div
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${banner.image})` }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/50 to-transparent" />
          </div>

          {/* Content */}
          <div className="relative h-full container mx-auto px-4 flex items-center">
            <div className="max-w-xl text-white">
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 animate-fadeInUp">
                {banner.title}
              </h1>
              <p className="text-lg md:text-xl text-gray-200 mb-6 animate-fadeInUp animation-delay-200">
                {banner.subtitle}
              </p>
              <Button
                size="lg"
                className="animate-fadeInUp animation-delay-400"
                asChild
              >
                <Link href={banner.cta_link}>{banner.cta_text}</Link>
              </Button>
            </div>
          </div>
        </div>
      ))}

      {/* Navigation Arrows */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-4 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full bg-white/20 hover:bg-white/40 text-white"
        onClick={goToPrev}
      >
        <ChevronLeft className="h-6 w-6" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-4 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full bg-white/20 hover:bg-white/40 text-white"
        onClick={goToNext}
      >
        <ChevronRight className="h-6 w-6" />
      </Button>

      {/* Dots */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
        {banners.map((_, index) => (
          <button
            key={index}
            className={`h-2 rounded-full transition-all ${
              index === currentSlide
                ? 'w-8 bg-white'
                : 'w-2 bg-white/50 hover:bg-white/75'
            }`}
            onClick={() => goToSlide(index)}
          />
        ))}
      </div>
    </section>
  );
}
