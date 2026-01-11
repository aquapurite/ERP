'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Droplets,
  Phone,
  Mail,
  MapPin,
  Facebook,
  Twitter,
  Instagram,
  Youtube,
  CreditCard,
  Shield,
  Truck,
  HeadphonesIcon,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { CompanyInfo } from '@/types/storefront';
import { companyApi } from '@/lib/storefront/api';

export default function StorefrontFooter() {
  const [company, setCompany] = useState<CompanyInfo | null>(null);

  useEffect(() => {
    const fetchCompany = async () => {
      try {
        const data = await companyApi.getInfo();
        setCompany(data);
      } catch (error) {
        console.error('Failed to fetch company info:', error);
      }
    };
    fetchCompany();
  }, []);

  return (
    <footer className="bg-gray-900 text-gray-300">
      {/* Features Bar */}
      <div className="border-b border-gray-800">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="flex items-center gap-3">
              <div className="bg-primary/20 p-3 rounded-full">
                <Truck className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-white">Free Shipping</p>
                <p className="text-sm">On orders above ₹999</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="bg-primary/20 p-3 rounded-full">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-white">Secure Payment</p>
                <p className="text-sm">100% secure checkout</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="bg-primary/20 p-3 rounded-full">
                <HeadphonesIcon className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-white">24/7 Support</p>
                <p className="text-sm">Dedicated customer care</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="bg-primary/20 p-3 rounded-full">
                <CreditCard className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-white">Easy Returns</p>
                <p className="text-sm">7-day return policy</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Company Info */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              {company?.logo_url ? (
                <img src={company.logo_url} alt={company.trade_name || company.name} className="h-10 w-auto" />
              ) : (
                <>
                  <div className="bg-primary rounded-full p-2">
                    <Droplets className="h-6 w-6 text-primary-foreground" />
                  </div>
                  <span className="font-bold text-xl text-white">
                    {company?.trade_name || company?.name || 'AQUAPURITE'}
                  </span>
                </>
              )}
            </Link>
            <p className="text-sm mb-6 leading-relaxed">
              India's trusted water purifier brand. We provide advanced water
              purification solutions for homes and offices with cutting-edge RO,
              UV, and UF technologies.
            </p>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-primary" />
                <span>{company?.phone || '1800-123-4567'} (Toll Free)</span>
              </div>
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-primary" />
                <span>{company?.email || 'support@aquapurite.com'}</span>
              </div>
              <div className="flex items-start gap-3">
                <MapPin className="h-4 w-4 text-primary mt-1" />
                <span>
                  {company?.address || '123 Industrial Area, Sector 62'},
                  <br />
                  {company ? `${company.city}, ${company.state} - ${company.pincode}` : 'Noida, Uttar Pradesh - 201301'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/about" className="hover:text-primary transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/products" className="hover:text-primary transition-colors">
                  Our Products
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-primary transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="/support" className="hover:text-primary transition-colors">
                  Support
                </Link>
              </li>
              <li>
                <Link href="/track" className="hover:text-primary transition-colors">
                  Track Order
                </Link>
              </li>
            </ul>
          </div>

          {/* Customer Service */}
          <div>
            <h3 className="text-white font-semibold mb-4">Customer Service</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/shipping-policy" className="hover:text-primary transition-colors">
                  Shipping Policy
                </Link>
              </li>
              <li>
                <Link href="/return-policy" className="hover:text-primary transition-colors">
                  Return & Refund
                </Link>
              </li>
              <li>
                <Link href="/warranty" className="hover:text-primary transition-colors">
                  Warranty Policy
                </Link>
              </li>
              <li>
                <Link href="/faq" className="hover:text-primary transition-colors">
                  FAQs
                </Link>
              </li>
              <li>
                <Link href="/privacy-policy" className="hover:text-primary transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-primary transition-colors">
                  Terms & Conditions
                </Link>
              </li>
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h3 className="text-white font-semibold mb-4">Stay Updated</h3>
            <p className="text-sm mb-4">
              Subscribe to our newsletter for exclusive offers and updates.
            </p>
            <form className="space-y-3">
              <Input
                type="email"
                placeholder="Enter your email"
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
              <Button className="w-full">Subscribe</Button>
            </form>
            <div className="mt-6">
              <p className="text-sm mb-3">Follow Us</p>
              <div className="flex gap-3">
                <a
                  href="#"
                  className="bg-gray-800 p-2 rounded-full hover:bg-primary transition-colors"
                >
                  <Facebook className="h-5 w-5" />
                </a>
                <a
                  href="#"
                  className="bg-gray-800 p-2 rounded-full hover:bg-primary transition-colors"
                >
                  <Twitter className="h-5 w-5" />
                </a>
                <a
                  href="#"
                  className="bg-gray-800 p-2 rounded-full hover:bg-primary transition-colors"
                >
                  <Instagram className="h-5 w-5" />
                </a>
                <a
                  href="#"
                  className="bg-gray-800 p-2 rounded-full hover:bg-primary transition-colors"
                >
                  <Youtube className="h-5 w-5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm">
              © {new Date().getFullYear()} AQUAPURITE. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <img
                src="https://razorpay.com/build/browser/static/razorpay-logo-new.svg"
                alt="Razorpay"
                className="h-6 opacity-50 hover:opacity-100 transition-opacity"
              />
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/5/5e/Visa_Inc._logo.svg"
                alt="Visa"
                className="h-4 opacity-50 hover:opacity-100 transition-opacity"
              />
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/2/2a/Mastercard-logo.svg"
                alt="Mastercard"
                className="h-6 opacity-50 hover:opacity-100 transition-opacity"
              />
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
