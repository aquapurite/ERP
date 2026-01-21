'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Search,
  ShoppingCart,
  User,
  Menu,
  X,
  Phone,
  ChevronDown,
  Droplets,
  Moon,
  Sun,
} from 'lucide-react';
import { useTheme } from 'next-themes';
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
import { useCartStore } from '@/lib/storefront/cart-store';
import { useAuthStore, useIsAuthenticated, useCustomer } from '@/lib/storefront/auth-store';
import { StorefrontCategory, CompanyInfo } from '@/types/storefront';
import { categoriesApi, companyApi, authApi, contentApi, StorefrontMenuItem } from '@/lib/storefront/api';
import CartDrawer from '../cart/cart-drawer';
import SearchAutocomplete from '../search/search-autocomplete';

export default function StorefrontHeader() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const [categories, setCategories] = useState<StorefrontCategory[]>([]);
  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const [headerMenuItems, setHeaderMenuItems] = useState<StorefrontMenuItem[]>([]);

  const cartItemCount = useCartStore((state) => state.getItemCount());
  const openCart = useCartStore((state) => state.openCart);

  // Auth state
  const isAuthenticated = useIsAuthenticated();
  const customer = useCustomer();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = async () => {
    await authApi.logout();
    logout();
    router.push('/');
  };

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [categoriesData, companyData, menuItems] = await Promise.all([
          categoriesApi.getTree(),
          companyApi.getInfo(),
          contentApi.getMenuItems('header'),
        ]);
        setCategories(categoriesData);
        setCompany(companyData);
        setHeaderMenuItems(menuItems);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    };
    fetchData();
  }, []);

  return (
    <>
      {/* Top Bar */}
      <div className="bg-secondary text-secondary-foreground text-sm py-2 hidden md:block">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Phone className="h-3 w-3" />
              {company?.phone || '1800-123-4567'} (Toll Free)
            </span>
            <span>Free Shipping on orders above ₹999</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/track" className="hover:underline">
              Track Order
            </Link>
            <Link href="/support" className="hover:underline">
              Support
            </Link>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header
        className={`sticky top-0 z-50 bg-background transition-shadow ${
          isScrolled ? 'shadow-md' : 'shadow-sm'
        }`}
      >
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </Button>

            {/* Logo */}
            <Link href="/" className="flex items-center gap-2">
              {company?.logo_url ? (
                <img
                  src={company.logo_url}
                  alt={company.trade_name || company.name}
                  className="h-10 w-auto"
                />
              ) : (
                <>
                  <div className="bg-primary rounded-full p-2">
                    <Droplets className="h-6 w-6 text-primary-foreground" />
                  </div>
                  <span className="font-bold text-xl hidden sm:block">
                    {company?.trade_name || company?.name || 'AQUAPURITE'}
                  </span>
                </>
              )}
            </Link>

            {/* Search Bar - Desktop */}
            <div className="hidden md:flex flex-1 max-w-xl mx-8">
              <SearchAutocomplete
                placeholder="Search for products..."
                className="w-full"
              />
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-2 md:gap-4">
              {/* Search - Mobile */}
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setMobileSearchOpen(true)}
              >
                <Search className="h-5 w-5" />
              </Button>

              {/* Dark Mode Toggle */}
              {mounted && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                  {theme === 'dark' ? (
                    <Sun className="h-5 w-5" />
                  ) : (
                    <Moon className="h-5 w-5" />
                  )}
                </Button>
              )}

              {/* Account */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="hidden md:flex">
                    <User className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  {isAuthenticated && customer ? (
                    <>
                      <div className="px-2 py-1.5 text-sm font-medium border-b mb-1">
                        Hi, {customer.first_name}
                      </div>
                      <DropdownMenuItem asChild>
                        <Link href="/account">My Account</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/account/orders">My Orders</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/account/addresses">Saved Addresses</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={handleLogout}
                        className="text-red-600 focus:text-red-600"
                      >
                        Logout
                      </DropdownMenuItem>
                    </>
                  ) : (
                    <>
                      <DropdownMenuItem asChild>
                        <Link href="/account/login">Login / Sign Up</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/track">Track Order</Link>
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Cart */}
              <Button
                variant="ghost"
                size="icon"
                className="relative"
                onClick={openCart}
              >
                <ShoppingCart className="h-5 w-5" />
                {cartItemCount > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs"
                  >
                    {cartItemCount}
                  </Badge>
                )}
              </Button>
            </div>
          </div>

          {/* Category Navigation - Desktop */}
          <nav className="hidden md:flex items-center gap-6 py-3 border-t">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="font-medium">
                  All Categories
                  <ChevronDown className="ml-1 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                {categories.map((category) => (
                  <DropdownMenuItem key={category.id} asChild>
                    <Link href={`/category/${category.slug}`}>
                      {category.name}
                    </Link>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* CMS Menu Items - falls back to defaults if empty */}
            {headerMenuItems.length > 0 ? (
              headerMenuItems.map((item) => (
                <Link
                  key={item.id}
                  href={item.url}
                  target={item.target}
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  {item.title}
                </Link>
              ))
            ) : (
              <>
                <Link
                  href="/products?is_bestseller=true"
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  Bestsellers
                </Link>
                <Link
                  href="/products?is_new_arrival=true"
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  New Arrivals
                </Link>
                <Link
                  href="/products"
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  All Products
                </Link>
                <Link
                  href="/about"
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  About Us
                </Link>
                <Link
                  href="/contact"
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  Contact
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Mobile Menu */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="w-80">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-primary" />
              {company?.trade_name || company?.name || 'AQUAPURITE'}
            </SheetTitle>
          </SheetHeader>
          <nav className="mt-8 flex flex-col gap-4">
            <Link
              href="/"
              className="text-lg font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Home
            </Link>
            <Link
              href="/products"
              className="text-lg font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              All Products
            </Link>
            <div className="border-t pt-4">
              <p className="text-sm text-muted-foreground mb-2">Categories</p>
              {categories.map((category) => (
                <Link
                  key={category.id}
                  href={`/category/${category.slug}`}
                  className="block py-2 text-base"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {category.name}
                </Link>
              ))}
            </div>
            <div className="border-t pt-4">
              {isAuthenticated && customer ? (
                <>
                  <p className="text-sm text-muted-foreground mb-2">
                    Hi, {customer.first_name}
                  </p>
                  <Link
                    href="/account"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    My Account
                  </Link>
                  <Link
                    href="/account/orders"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    My Orders
                  </Link>
                  <Link
                    href="/account/addresses"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Saved Addresses
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setMobileMenuOpen(false);
                    }}
                    className="block py-2 text-base text-red-600 w-full text-left"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/account/login"
                    className="block py-2 text-base font-medium text-primary"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Login / Sign Up
                  </Link>
                  <Link
                    href="/track"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Track Order
                  </Link>
                </>
              )}
            </div>
            <div className="border-t pt-4">
              {/* CMS Menu Items for mobile */}
              {headerMenuItems.length > 0 ? (
                headerMenuItems.map((item) => (
                  <Link
                    key={item.id}
                    href={item.url}
                    target={item.target}
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item.title}
                  </Link>
                ))
              ) : (
                <>
                  <Link
                    href="/about"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    About Us
                  </Link>
                  <Link
                    href="/contact"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Contact Us
                  </Link>
                  <Link
                    href="/support"
                    className="block py-2 text-base"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Support
                  </Link>
                </>
              )}
            </div>
          </nav>
        </SheetContent>
      </Sheet>

      {/* Cart Drawer */}
      <CartDrawer />

      {/* Mobile Search Overlay */}
      <Sheet open={mobileSearchOpen} onOpenChange={setMobileSearchOpen}>
        <SheetContent side="top" className="h-auto pb-8">
          <SheetHeader className="mb-4">
            <SheetTitle>Search Products</SheetTitle>
          </SheetHeader>
          <SearchAutocomplete
            placeholder="Search for products..."
            autoFocus
            onClose={() => setMobileSearchOpen(false)}
          />
        </SheetContent>
      </Sheet>
    </>
  );
}
