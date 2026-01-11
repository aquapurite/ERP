'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShoppingCart,
  User,
  Menu,
  X,
  Phone,
  Mail,
  MapPin,
  Search,
  ChevronDown,
  Droplets,
  Facebook,
  Instagram,
  Twitter,
  Youtube,
  HeartHandshake,
  Truck,
  Shield,
  Award,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { CartProvider, useCart } from '@/contexts/cart-context';
import { cn } from '@/lib/utils';

// Header component - Dark theme with golden accents
function StoreHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const pathname = usePathname();
  const { itemCount } = useCart();

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/products', label: 'Products' },
    { href: '/about', label: 'About Us' },
    { href: '/contact', label: 'Contact' },
    { href: '/support', label: 'Support' },
  ];

  const productCategories = [
    { href: '/products?category=water-purifiers', label: 'Water Purifiers' },
    { href: '/products?category=spare-parts', label: 'Spare Parts' },
    { href: '/products?category=filters', label: 'Filters & Membranes' },
    { href: '/products?category=accessories', label: 'Accessories' },
  ];

  return (
    <header className="sticky top-0 z-50">
      {/* Top bar - Golden accent */}
      <div className="bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600 text-slate-900 text-sm py-2">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <a href="tel:+919013034083" className="flex items-center gap-1.5 hover:text-slate-700 font-medium">
              <Phone className="h-3.5 w-3.5" />
              <span>+91 9013034083</span>
            </a>
            <a href="mailto:info@aquapurite.com" className="hidden sm:flex items-center gap-1.5 hover:text-slate-700 font-medium">
              <Mail className="h-3.5 w-3.5" />
              <span>info@aquapurite.com</span>
            </a>
          </div>
          <div className="flex items-center gap-4 font-medium">
            <Link href="/track" className="hover:text-slate-700">Track Order</Link>
            <Link href="/login" className="hover:text-slate-700">Login</Link>
          </div>
        </div>
      </div>

      {/* Main header - Dark background */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20">
                <Droplets className="h-7 w-7 text-slate-900" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-wide">AQUAPURITE</h1>
                <p className="text-xs text-amber-500 font-medium">Pure Water, Pure Life</p>
              </div>
            </Link>

            {/* Search bar - desktop */}
            <div className="hidden md:flex flex-1 max-w-xl mx-8">
              <div className="relative w-full">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  type="search"
                  placeholder="Search for water purifiers, filters, spare parts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-11 pr-4 w-full bg-slate-800 border-slate-700 text-white placeholder:text-slate-400 focus:border-amber-500 focus:ring-amber-500/20 rounded-lg"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Link href="/cart">
                <Button variant="ghost" size="icon" className="relative text-slate-300 hover:text-amber-500 hover:bg-slate-800">
                  <ShoppingCart className="h-5 w-5" />
                  {itemCount > 0 && (
                    <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs bg-amber-500 text-slate-900 border-0">
                      {itemCount}
                    </Badge>
                  )}
                </Button>
              </Link>
              <Link href="/account" className="hidden sm:block">
                <Button variant="ghost" size="icon" className="text-slate-300 hover:text-amber-500 hover:bg-slate-800">
                  <User className="h-5 w-5" />
                </Button>
              </Link>
              {/* Mobile menu */}
              <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
                <SheetTrigger asChild className="md:hidden">
                  <Button variant="ghost" size="icon" className="text-slate-300 hover:text-amber-500 hover:bg-slate-800">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="bg-slate-900 border-slate-800">
                  <SheetHeader>
                    <SheetTitle className="text-white">Menu</SheetTitle>
                  </SheetHeader>
                  <nav className="flex flex-col gap-4 mt-8">
                    {navLinks.map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={() => setIsMenuOpen(false)}
                        className={cn(
                          "text-lg font-medium transition-colors",
                          pathname === link.href ? "text-amber-500" : "text-slate-300 hover:text-white"
                        )}
                      >
                        {link.label}
                      </Link>
                    ))}
                  </nav>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </div>

        {/* Navigation - desktop */}
        <nav className="hidden md:block bg-slate-800/50 border-t border-slate-800">
          <div className="container mx-auto px-4">
            <ul className="flex items-center gap-1">
              {navLinks.map((link) => (
                <li key={link.href}>
                  {link.label === 'Products' ? (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className={cn(
                          "px-4 py-3 text-sm font-medium flex items-center gap-1 transition-colors",
                          pathname.startsWith('/products')
                            ? "text-amber-500"
                            : "text-slate-300 hover:text-amber-500"
                        )}>
                          {link.label}
                          <ChevronDown className="h-4 w-4" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="bg-slate-800 border-slate-700">
                        <DropdownMenuItem asChild className="text-slate-300 hover:text-white focus:text-white focus:bg-slate-700">
                          <Link href="/products">All Products</Link>
                        </DropdownMenuItem>
                        {productCategories.map((cat) => (
                          <DropdownMenuItem key={cat.href} asChild className="text-slate-300 hover:text-white focus:text-white focus:bg-slate-700">
                            <Link href={cat.href}>{cat.label}</Link>
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  ) : (
                    <Link
                      href={link.href}
                      className={cn(
                        "px-4 py-3 text-sm font-medium block transition-colors",
                        pathname === link.href
                          ? "text-amber-500"
                          : "text-slate-300 hover:text-amber-500"
                      )}
                    >
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </div>
    </header>
  );
}

// Footer component - Dark theme
function StoreFooter() {
  const features = [
    { icon: Truck, title: 'Free Delivery', desc: 'On orders above Rs 1000' },
    { icon: Shield, title: 'Warranty', desc: 'Up to 2 years coverage' },
    { icon: HeartHandshake, title: '24/7 Support', desc: 'Expert assistance' },
    { icon: Award, title: 'Genuine Products', desc: '100% authentic' },
  ];

  return (
    <footer className="bg-slate-900 text-slate-300">
      {/* Trust badges */}
      <div className="border-t border-b border-slate-800 py-8">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                  <feature.icon className="h-6 w-6 text-amber-500" />
                </div>
                <div>
                  <h4 className="font-semibold text-white text-sm">{feature.title}</h4>
                  <p className="text-xs text-slate-400">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main footer */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company info */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-amber-600 rounded-lg flex items-center justify-center">
                <Droplets className="h-6 w-6 text-slate-900" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">AQUAPURITE</h3>
                <p className="text-xs text-amber-500">Pure Water, Pure Life</p>
              </div>
            </div>
            <p className="text-sm mb-4 text-slate-400">
              India's trusted water purifier brand delivering pure, safe drinking water to homes and businesses since 2025.
            </p>
            <div className="flex items-start gap-2 text-sm">
              <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0 text-amber-500" />
              <span className="text-slate-400">Plot 36-A, KH NO 181, PH-1, Shyam Vihar, Najafgarh, New Delhi - 110043</span>
            </div>
          </div>

          {/* Quick links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/products" className="text-slate-400 hover:text-amber-500 transition-colors">Products</Link></li>
              <li><Link href="/about" className="text-slate-400 hover:text-amber-500 transition-colors">About Us</Link></li>
              <li><Link href="/contact" className="text-slate-400 hover:text-amber-500 transition-colors">Contact</Link></li>
              <li><Link href="/track" className="text-slate-400 hover:text-amber-500 transition-colors">Track Order</Link></li>
              <li><Link href="/support" className="text-slate-400 hover:text-amber-500 transition-colors">Support</Link></li>
            </ul>
          </div>

          {/* Customer service */}
          <div>
            <h4 className="text-white font-semibold mb-4">Customer Service</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/shipping" className="text-slate-400 hover:text-amber-500 transition-colors">Shipping Policy</Link></li>
              <li><Link href="/returns" className="text-slate-400 hover:text-amber-500 transition-colors">Returns & Refunds</Link></li>
              <li><Link href="/warranty" className="text-slate-400 hover:text-amber-500 transition-colors">Warranty</Link></li>
              <li><Link href="/faq" className="text-slate-400 hover:text-amber-500 transition-colors">FAQs</Link></li>
              <li><Link href="/installation" className="text-slate-400 hover:text-amber-500 transition-colors">Installation Guide</Link></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-semibold mb-4">Contact Us</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-amber-500" />
                <a href="tel:+919013034083" className="text-slate-400 hover:text-amber-500 transition-colors">+91 9013034083</a>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-amber-500" />
                <a href="mailto:info@aquapurite.com" className="text-slate-400 hover:text-amber-500 transition-colors">info@aquapurite.com</a>
              </li>
            </ul>
            <div className="mt-6">
              <h5 className="text-white font-medium mb-2">Business Hours</h5>
              <p className="text-sm text-slate-400">Mon - Sat: 9:00 AM - 7:00 PM</p>
              <p className="text-sm text-slate-400">Sunday: Closed</p>
            </div>

            {/* Social links */}
            <div className="mt-6">
              <h5 className="text-white font-medium mb-3">Follow Us</h5>
              <div className="flex gap-3">
                <a href="#" className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-amber-500 hover:text-slate-900 transition-colors">
                  <Facebook className="h-4 w-4" />
                </a>
                <a href="#" className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-amber-500 hover:text-slate-900 transition-colors">
                  <Instagram className="h-4 w-4" />
                </a>
                <a href="#" className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-amber-500 hover:text-slate-900 transition-colors">
                  <Twitter className="h-4 w-4" />
                </a>
                <a href="#" className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-amber-500 hover:text-slate-900 transition-colors">
                  <Youtube className="h-4 w-4" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-800 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-500">&copy; 2025 Aquapurite Private Limited. All rights reserved.</p>
          <div className="flex gap-4 text-sm">
            <Link href="/privacy" className="text-slate-500 hover:text-amber-500 transition-colors">Privacy Policy</Link>
            <Link href="/terms" className="text-slate-500 hover:text-amber-500 transition-colors">Terms & Conditions</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function StorefrontLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <CartProvider>
      <div className="min-h-screen flex flex-col bg-slate-950">
        <StoreHeader />
        <main className="flex-1">
          {children}
        </main>
        <StoreFooter />
      </div>
    </CartProvider>
  );
}
