'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { partnerAuthApi } from '@/lib/storefront/partner-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Loader2,
  User,
  Phone,
  Mail,
  MapPin,
  Gift,
  CheckCircle,
  ArrowRight,
  Wallet,
  Share2,
  TrendingUp,
} from 'lucide-react';

// Icon mapping for dynamic icons from CMS
const iconMap: Record<string, React.ElementType> = {
  Wallet,
  Share2,
  TrendingUp,
};

// Default content (used as fallback if CMS settings not configured)
const defaultContent = {
  hero_title: 'Become an AQUAPURITE Partner',
  hero_subtitle: 'Join our community of partners and earn by sharing our products. Zero investment, unlimited earning potential!',
  benefit_1_title: 'Earn Commission',
  benefit_1_description: '10-15% commission on every successful sale',
  benefit_1_icon: 'Wallet',
  benefit_2_title: 'Easy Sharing',
  benefit_2_description: 'Share products via WhatsApp, social media, and more',
  benefit_2_icon: 'Share2',
  benefit_3_title: 'Grow Together',
  benefit_3_description: 'Tier upgrades with higher commission rates',
  benefit_3_icon: 'TrendingUp',
  form_title: 'Partner Registration',
  form_subtitle: 'Fill in your details to get started',
  success_title: 'Registration Successful!',
  success_message: 'Your partner application has been submitted. You can now login with your mobile number.',
};

interface PageContent {
  hero_title: string;
  hero_subtitle: string;
  benefit_1_title: string;
  benefit_1_description: string;
  benefit_1_icon: string;
  benefit_2_title: string;
  benefit_2_description: string;
  benefit_2_icon: string;
  benefit_3_title: string;
  benefit_3_description: string;
  benefit_3_icon: string;
  form_title: string;
  form_subtitle: string;
  success_title: string;
  success_message: string;
}

export default function BecomePartnerPage() {
  const [content, setContent] = useState<PageContent>(defaultContent);
  const [contentLoading, setContentLoading] = useState(true);

  const [formData, setFormData] = useState({
    full_name: '',
    mobile: '',
    email: '',
    city: '',
    pincode: '',
    referral_code: '',
  });
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Fetch CMS content on mount
  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/cms/settings?group=partner_page&limit=50`
        );

        if (response.ok) {
          const data = await response.json();
          const items = data.items || data.data?.items || [];

          if (items.length > 0) {
            const newContent = { ...defaultContent };
            items.forEach((setting: { setting_key: string; setting_value?: string }) => {
              const key = setting.setting_key.replace('partner_page_', '') as keyof PageContent;
              if (key in defaultContent && setting.setting_value) {
                newContent[key] = setting.setting_value;
              }
            });
            setContent(newContent);
          }
        }
      } catch (err) {
        // Use default content on error
        console.log('Using default content');
      } finally {
        setContentLoading(false);
      }
    };

    fetchContent();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!acceptTerms) {
      setError('Please accept the terms and conditions');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      // Format mobile number
      const formattedMobile = formData.mobile.startsWith('+91')
        ? formData.mobile
        : formData.mobile.startsWith('91')
        ? '+' + formData.mobile
        : '+91' + formData.mobile.replace(/\D/g, '');

      const response = await partnerAuthApi.register({
        full_name: formData.full_name,
        phone: formattedMobile,
        email: formData.email || undefined,
        city: formData.city || undefined,
        pincode: formData.pincode || undefined,
        referred_by_code: formData.referral_code || undefined,
      });

      if (response.success) {
        setSuccess(true);
      } else {
        setError(response.message);
      }
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            err.message
          : 'Registration failed. Please try again.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Build benefits array from content
  const benefits = [
    {
      icon: iconMap[content.benefit_1_icon] || Wallet,
      title: content.benefit_1_title,
      description: content.benefit_1_description,
      href: '#registration',
    },
    {
      icon: iconMap[content.benefit_2_icon] || Share2,
      title: content.benefit_2_title,
      description: content.benefit_2_description,
      href: '/partner/products',
    },
    {
      icon: iconMap[content.benefit_3_icon] || TrendingUp,
      title: content.benefit_3_title,
      description: content.benefit_3_description,
      href: '/partner',
    },
  ];

  if (success) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center py-12 px-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-8">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold mb-2">{content.success_title}</h2>
            <p className="text-muted-foreground mb-6">
              {content.success_message}
            </p>
            <Button asChild className="w-full">
              <Link href="/partner/login">
                Login to Partner Portal
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            {contentLoading ? (
              <span className="animate-pulse bg-muted rounded h-10 w-96 inline-block" />
            ) : (
              content.hero_title
            )}
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            {contentLoading ? (
              <span className="animate-pulse bg-muted rounded h-6 w-full inline-block" />
            ) : (
              content.hero_subtitle
            )}
          </p>
        </div>

        {/* Benefits */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {benefits.map((benefit) => (
            <Link key={benefit.title} href={benefit.href}>
              <Card className="text-center h-full cursor-pointer hover:shadow-lg hover:border-primary/50 transition-all duration-200">
                <CardContent className="pt-6">
                  <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <benefit.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="font-semibold mb-2">{benefit.title}</h3>
                  <p className="text-sm text-muted-foreground">{benefit.description}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        {/* Registration Form */}
        <Card id="registration" className="max-w-md mx-auto scroll-mt-20">
          <CardHeader>
            <CardTitle>{content.form_title}</CardTitle>
            <CardDescription>{content.form_subtitle}</CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name *</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="full_name"
                    name="full_name"
                    placeholder="Enter your full name"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mobile">Mobile Number *</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="mobile"
                    name="mobile"
                    type="tel"
                    placeholder="10-digit mobile number"
                    value={formData.mobile}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    pattern="[0-9+]{10,13}"
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email (Optional)</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="your@email.com"
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10"
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="city"
                      name="city"
                      placeholder="Your city"
                      value={formData.city}
                      onChange={handleChange}
                      className="pl-10"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pincode">Pincode</Label>
                  <Input
                    id="pincode"
                    name="pincode"
                    placeholder="123456"
                    value={formData.pincode}
                    onChange={handleChange}
                    pattern="[0-9]{6}"
                    maxLength={6}
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="referral_code">Referral Code (Optional)</Label>
                <div className="relative">
                  <Gift className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="referral_code"
                    name="referral_code"
                    placeholder="If referred by someone"
                    value={formData.referral_code}
                    onChange={handleChange}
                    className="pl-10"
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="flex items-start space-x-2">
                <Checkbox
                  id="terms"
                  checked={acceptTerms}
                  onCheckedChange={(checked) => setAcceptTerms(checked as boolean)}
                  disabled={isSubmitting}
                />
                <Label htmlFor="terms" className="text-sm font-normal leading-none">
                  I agree to the{' '}
                  <Link href="/terms" className="text-primary hover:underline">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link href="/privacy" className="text-primary hover:underline">
                    Privacy Policy
                  </Link>
                </Label>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-4">
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Registering...
                  </>
                ) : (
                  <>
                    Register as Partner
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>

              <p className="text-sm text-center text-muted-foreground">
                Already a partner?{' '}
                <Link href="/partner/login" className="text-primary hover:underline">
                  Login here
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
