import { Metadata } from 'next';
import StorefrontHeader from '@/components/storefront/layout/header';
import StorefrontFooter from '@/components/storefront/layout/footer';

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
    <div className="min-h-screen flex flex-col">
      {/* Demo Site Banner */}
      <div className="bg-gray-900 text-white text-center py-2 px-4">
        <p className="text-lg font-bold tracking-wide">
          This is a Demo Site for www.aquapurite.com
        </p>
      </div>
      <StorefrontHeader />
      <main className="flex-1">{children}</main>
      <StorefrontFooter />
    </div>
  );
}
