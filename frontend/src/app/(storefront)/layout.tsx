import { Metadata } from 'next';
import StorefrontHeader from '@/components/storefront/layout/header';
import StorefrontFooter from '@/components/storefront/layout/footer';
import AnnouncementBar from '@/components/storefront/layout/announcement-bar';
import CompareBarWrapper from '@/components/storefront/product/compare-bar-wrapper';
import WhatsAppButton from '@/components/storefront/layout/whatsapp-button';
import { ServiceabilityProvider } from '@/components/storefront/serviceability-provider';

export const metadata: Metadata = {
  title: {
    default: 'AQUAPURITE - Pure Water, Healthy Life',
    template: '%s | AQUAPURITE',
  },
  description:
    'India\'s trusted water purifier brand. Advanced RO, UV, and UF water purification systems for homes and offices.',
  keywords: [
    'water purifier',
    'RO purifier',
    'UV purifier',
    'water filter',
    'drinking water',
    'aquapurite',
  ],
};

export default function StorefrontLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ServiceabilityProvider>
      <div className="min-h-screen flex flex-col">
        {/* Demo Site Banner */}
        <div className="bg-gray-900 text-white text-center py-2 px-4">
          <p className="text-lg font-bold tracking-wide">
            This is a Demo Site for www.aquapurite.com
          </p>
        </div>
        {/* CMS Announcement Bar */}
        <AnnouncementBar />
        <StorefrontHeader />
        <main className="flex-1 pb-20">{children}</main>
        <StorefrontFooter />
        {/* Product Comparison Bar - Fixed at bottom */}
        <CompareBarWrapper />
        {/* WhatsApp Floating Button */}
        <WhatsAppButton />
      </div>
    </ServiceabilityProvider>
  );
}
