'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Gift,
  Users,
  Share2,
  Copy,
  CheckCircle,
  IndianRupee,
  Clock,
  ChevronRight,
  Loader2,
  MessageCircle,
  Mail,
  Facebook,
  Twitter,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { useIsAuthenticated, useCustomer } from '@/lib/storefront/auth-store';
import { formatCurrency } from '@/lib/utils';

interface ReferralStats {
  referral_code: string;
  total_referrals: number;
  successful_referrals: number;
  pending_referrals: number;
  total_earnings: number;
  pending_earnings: number;
  referrals: {
    id: string;
    referee_name: string;
    status: 'pending' | 'completed' | 'expired';
    order_amount?: number;
    reward_amount?: number;
    created_at: string;
  }[];
}

// Mock data - replace with actual API
const mockReferralStats: ReferralStats = {
  referral_code: 'AQUA2024',
  total_referrals: 5,
  successful_referrals: 3,
  pending_referrals: 2,
  total_earnings: 1500,
  pending_earnings: 500,
  referrals: [
    {
      id: '1',
      referee_name: 'Rahul S.',
      status: 'completed',
      order_amount: 24999,
      reward_amount: 500,
      created_at: '2025-01-15',
    },
    {
      id: '2',
      referee_name: 'Priya M.',
      status: 'completed',
      order_amount: 34999,
      reward_amount: 500,
      created_at: '2025-01-10',
    },
    {
      id: '3',
      referee_name: 'Amit K.',
      status: 'pending',
      created_at: '2025-01-20',
    },
  ],
};

const referralBenefits = [
  {
    icon: Gift,
    title: 'You Get ₹500',
    description: 'For every successful referral that makes a purchase',
  },
  {
    icon: Users,
    title: 'Friend Gets 5% Off',
    description: 'Your friend gets 5% discount on their first purchase',
  },
  {
    icon: IndianRupee,
    title: 'No Limit',
    description: 'Refer unlimited friends and earn unlimited rewards',
  },
];

const howItWorks = [
  {
    step: 1,
    title: 'Share Your Code',
    description: 'Share your unique referral code with friends and family',
  },
  {
    step: 2,
    title: 'Friend Makes Purchase',
    description: 'Your friend uses your code and gets 5% off on their order',
  },
  {
    step: 3,
    title: 'You Earn Rewards',
    description: 'Once their order is delivered, you get ₹500 credit',
  },
];

export default function ReferralPage() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const customer = useCustomer();
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      // Allow viewing the page but show limited content
      setLoading(false);
      return;
    }

    // Fetch referral stats
    const fetchStats = async () => {
      try {
        await new Promise((resolve) => setTimeout(resolve, 500));
        // Generate referral code from customer name if available
        const code = customer
          ? `${customer.first_name?.toUpperCase().slice(0, 4) || 'AQUA'}${customer.phone?.slice(-4) || '2024'}`
          : 'AQUA2024';
        setStats({ ...mockReferralStats, referral_code: code });
      } catch (error) {
        toast.error('Failed to load referral data');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [isAuthenticated, customer]);

  const copyCode = async () => {
    if (!stats) return;
    try {
      await navigator.clipboard.writeText(stats.referral_code);
      setCopied(true);
      toast.success('Referral code copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy code');
    }
  };

  const shareVia = (platform: string) => {
    if (!stats) return;

    const message = `Hey! Use my referral code ${stats.referral_code} to get 5% off on your first water purifier from Aquapurite. Shop now at https://www.aquapurite.com?ref=${stats.referral_code}`;
    const encodedMessage = encodeURIComponent(message);

    let url = '';
    switch (platform) {
      case 'whatsapp':
        url = `https://wa.me/?text=${encodedMessage}`;
        break;
      case 'facebook':
        url = `https://www.facebook.com/sharer/sharer.php?u=https://www.aquapurite.com?ref=${stats.referral_code}&quote=${encodedMessage}`;
        break;
      case 'twitter':
        url = `https://twitter.com/intent/tweet?text=${encodedMessage}`;
        break;
      case 'email':
        url = `mailto:?subject=Get 5% off on Aquapurite Water Purifiers&body=${encodedMessage}`;
        break;
    }

    if (url) {
      window.open(url, '_blank');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">Completed</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'expired':
        return <Badge className="bg-red-100 text-red-800">Expired</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Hero Section */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-4">
          <Gift className="h-4 w-4" />
          Referral Program
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-4">
          Refer Friends & Earn <span className="text-primary">₹500</span> Each
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Share the gift of pure water with your friends and family. They get 5% off, you get ₹500 - it&apos;s a win-win!
        </p>
      </div>

      {/* Benefits */}
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        {referralBenefits.map((benefit, index) => {
          const Icon = benefit.icon;
          return (
            <Card key={index}>
              <CardContent className="pt-6 text-center">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-1">{benefit.title}</h3>
                <p className="text-sm text-muted-foreground">{benefit.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Referral Code Section */}
      {isAuthenticated && stats ? (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Your Referral Code</CardTitle>
            <CardDescription>Share this code with friends to earn rewards</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4 items-center">
              <div className="flex-1 w-full">
                <div className="flex">
                  <Input
                    value={stats.referral_code}
                    readOnly
                    className="text-lg font-mono font-bold text-center sm:text-left rounded-r-none"
                  />
                  <Button
                    variant="secondary"
                    className="rounded-l-none"
                    onClick={copyCode}
                  >
                    {copied ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              <Separator orientation="vertical" className="h-10 hidden sm:block" />
              <div className="flex gap-2">
                <Button
                  size="icon"
                  variant="outline"
                  className="bg-green-50 hover:bg-green-100 border-green-200"
                  onClick={() => shareVia('whatsapp')}
                  title="Share on WhatsApp"
                >
                  <MessageCircle className="h-4 w-4 text-green-600" />
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  className="bg-blue-50 hover:bg-blue-100 border-blue-200"
                  onClick={() => shareVia('facebook')}
                  title="Share on Facebook"
                >
                  <Facebook className="h-4 w-4 text-blue-600" />
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  className="bg-sky-50 hover:bg-sky-100 border-sky-200"
                  onClick={() => shareVia('twitter')}
                  title="Share on Twitter"
                >
                  <Twitter className="h-4 w-4 text-sky-500" />
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => shareVia('email')}
                  title="Share via Email"
                >
                  <Mail className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t">
              <div className="text-center">
                <p className="text-2xl font-bold text-primary">{stats.total_referrals}</p>
                <p className="text-sm text-muted-foreground">Total Referrals</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{stats.successful_referrals}</p>
                <p className="text-sm text-muted-foreground">Successful</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{stats.pending_referrals}</p>
                <p className="text-sm text-muted-foreground">Pending</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{formatCurrency(stats.total_earnings)}</p>
                <p className="text-sm text-muted-foreground">Total Earned</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="mb-8">
          <CardContent className="py-8 text-center">
            <Gift className="h-12 w-12 mx-auto text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Login to Get Your Referral Code</h3>
            <p className="text-muted-foreground mb-4">
              Create an account or login to start referring friends and earning rewards.
            </p>
            <Link href="/account/login?redirect=/referral">
              <Button>
                Login / Sign Up
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* How It Works */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            {howItWorks.map((item) => (
              <div key={item.step} className="relative">
                <div className="flex items-center gap-4 mb-2">
                  <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                    {item.step}
                  </div>
                  <h4 className="font-semibold">{item.title}</h4>
                </div>
                <p className="text-sm text-muted-foreground ml-14">{item.description}</p>
                {item.step < 3 && (
                  <ChevronRight className="hidden md:block absolute top-3 -right-3 h-6 w-6 text-muted-foreground/50" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Referral History */}
      {isAuthenticated && stats && stats.referrals.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Referral History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.referrals.map((referral) => (
                <div
                  key={referral.id}
                  className="flex items-center justify-between py-3 border-b last:border-0"
                >
                  <div>
                    <p className="font-medium">{referral.referee_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(referral.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </p>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(referral.status)}
                    {referral.reward_amount && (
                      <p className="text-sm font-medium text-green-600 mt-1">
                        +{formatCurrency(referral.reward_amount)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Terms */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Terms & Conditions</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="text-sm text-muted-foreground space-y-2">
            <li>• Referral reward of ₹500 is credited after the referred order is delivered.</li>
            <li>• The referred friend must be a new customer making their first purchase.</li>
            <li>• Minimum order value of ₹10,000 is required for referral to be valid.</li>
            <li>• Rewards can be used on your next purchase or withdrawn to bank (min ₹1000).</li>
            <li>• Self-referrals or fraudulent referrals will result in account suspension.</li>
            <li>• Aquapurite reserves the right to modify or terminate this program at any time.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
