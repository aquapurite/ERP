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
      <StorefrontHeader />
      <main className="flex-1">{children}</main>
      <StorefrontFooter />
    </div>
  );
}
