'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { contentApi, StorefrontBanner } from '@/lib/storefront/api';

// Fallback banners for when API fails or returns empty
const fallbackBanners: StorefrontBanner[] = [
  {
    id: '1',
    title: 'Pure Water, Healthy Life',
    subtitle: 'Advanced 7-Stage RO Purification with Mineral Enrichment',
    image_url: 'https://images.unsplash.com/photo-1559839914-17aae19cec71?q=80&w=2070',
    cta_text: 'Shop Now',
    cta_link: '/products',
    text_position: 'left',
    text_color: 'white',
  },
  {
    id: '2',
    title: 'New Arrivals',
    subtitle: 'Discover our latest water purifiers with smart features',
    image_url: 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?q=80&w=2076',
    cta_text: 'Explore',
    cta_link: '/products?is_new_arrival=true',
    text_position: 'left',
    text_color: 'white',
  },
  {
    id: '3',
    title: 'Free Installation',
    subtitle: 'Get free installation on all water purifiers',
    image_url: 'https://images.unsplash.com/photo-1562016600-ece13e8ba570?q=80&w=2069',
    cta_text: 'Learn More',
    cta_link: '/products',
    text_position: 'left',
    text_color: 'white',
  },
];

export default function HeroBanner() {
  const [banners, setBanners] = useState<StorefrontBanner[]>(fallbackBanners);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch banners from API
  useEffect(() => {
    const fetchBanners = async () => {
      try {
        const data = await contentApi.getBanners();
        if (data && data.length > 0) {
          setBanners(data);
        }
      } catch {
        // Keep fallback banners on error
      } finally {
        setIsLoading(false);
      }
    };
    fetchBanners();
  }, []);

  // Auto-advance carousel
  useEffect(() => {
    if (banners.length <= 1) return;
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % banners.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [banners.length]);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  const goToPrev = () => {
    setCurrentSlide((prev) => (prev - 1 + banners.length) % banners.length);
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % banners.length);
  };

  const getTextAlignment = (position: string) => {
    switch (position) {
      case 'center':
        return 'items-center text-center';
      case 'right':
        return 'items-end text-right';
      default:
        return 'items-start text-left';
    }
  };

  const getTextColorClass = (color: string) => {
    return color === 'dark' ? 'text-gray-900' : 'text-white';
  };

  const getGradientClass = (position: string, color: string) => {
    const isDark = color === 'dark';
    const baseColor = isDark ? 'white' : 'black';
    switch (position) {
      case 'center':
        return `bg-gradient-to-b from-${baseColor}/60 via-${baseColor}/40 to-${baseColor}/60`;
      case 'right':
        return `bg-gradient-to-l from-${baseColor}/70 via-${baseColor}/50 to-transparent`;
      default:
        return `bg-gradient-to-r from-${baseColor}/70 via-${baseColor}/50 to-transparent`;
    }
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
            style={{ backgroundImage: `url(${banner.image_url})` }}
          >
            <div className={`absolute inset-0 ${
              banner.text_color === 'dark'
                ? 'bg-gradient-to-r from-white/70 via-white/50 to-transparent'
                : 'bg-gradient-to-r from-black/70 via-black/50 to-transparent'
            }`} />
          </div>

          {/* Content */}
          <div className={`relative h-full container mx-auto px-4 flex ${getTextAlignment(banner.text_position)}`}>
            <div className={`max-w-xl ${getTextColorClass(banner.text_color)} flex flex-col justify-center h-full py-12`}>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 animate-fadeInUp">
                {banner.title}
              </h1>
              {banner.subtitle && (
                <p className={`text-lg md:text-xl mb-6 animate-fadeInUp animation-delay-200 ${
                  banner.text_color === 'dark' ? 'text-gray-700' : 'text-gray-200'
                }`}>
                  {banner.subtitle}
                </p>
              )}
              {banner.cta_text && banner.cta_link && (
                <div>
                  <Button
                    size="lg"
                    className="animate-fadeInUp animation-delay-400"
                    asChild
                  >
                    <Link href={banner.cta_link}>{banner.cta_text}</Link>
                  </Button>
                </div>
              )}
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
