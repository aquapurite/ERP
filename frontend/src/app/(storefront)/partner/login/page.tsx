'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { usePartnerStore } from '@/lib/storefront/partner-store';
import { partnerAuthApi } from '@/lib/storefront/partner-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Phone, KeyRound, ArrowRight } from 'lucide-react';

export default function PartnerLoginPage() {
  const router = useRouter();
  const { isAuthenticated, login } = usePartnerStore();

  const [step, setStep] = useState<'mobile' | 'otp'>('mobile');
  const [mobile, setMobile] = useState('');
  const [otp, setOtp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/partner');
    }
  }, [isAuthenticated, router]);

  // Cooldown timer
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Format mobile number
      const formattedMobile = mobile.startsWith('+91')
        ? mobile
        : mobile.startsWith('91')
        ? '+' + mobile
        : '+91' + mobile.replace(/\D/g, '');

      const response = await partnerAuthApi.sendOTP(formattedMobile);

      if (response.success) {
        setMobile(formattedMobile);
        setStep('otp');
        if (response.cooldown_seconds) {
          setCooldown(response.cooldown_seconds);
        }
      } else {
        setError(response.message);
      }
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            err.message
          : 'Failed to send OTP. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await partnerAuthApi.verifyOTP(mobile, otp);

      login(response.access_token, response.refresh_token, response.partner);
      router.push('/partner');
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            err.message
          : 'Invalid OTP. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (cooldown > 0) return;

    setError(null);
    setIsLoading(true);

    try {
      const response = await partnerAuthApi.sendOTP(mobile);

      if (response.success) {
        if (response.cooldown_seconds) {
          setCooldown(response.cooldown_seconds);
        }
      } else {
        setError(response.message);
      }
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            err.message
          : 'Failed to resend OTP.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center py-12 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Partner Login</CardTitle>
          <CardDescription>
            {step === 'mobile'
              ? 'Enter your registered mobile number'
              : 'Enter the OTP sent to your mobile'}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {step === 'mobile' ? (
            <form onSubmit={handleSendOTP} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="mobile">Mobile Number</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="mobile"
                    type="tel"
                    placeholder="Enter 10-digit mobile number"
                    value={mobile}
                    onChange={(e) => setMobile(e.target.value)}
                    className="pl-10"
                    required
                    pattern="[0-9+]{10,13}"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending OTP...
                  </>
                ) : (
                  <>
                    Get OTP
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOTP} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">OTP</Label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="otp"
                    type="text"
                    placeholder="Enter 6-digit OTP"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="pl-10 text-center tracking-widest text-lg"
                    required
                    pattern="[0-9]{6}"
                    maxLength={6}
                    disabled={isLoading}
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  OTP sent to {mobile}
                </p>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify & Login'
                )}
              </Button>

              <div className="flex items-center justify-between text-sm">
                <button
                  type="button"
                  onClick={() => {
                    setStep('mobile');
                    setOtp('');
                    setError(null);
                  }}
                  className="text-primary hover:underline"
                >
                  Change number
                </button>
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={cooldown > 0 || isLoading}
                  className={`text-primary hover:underline ${
                    cooldown > 0 ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend OTP'}
                </button>
              </div>
            </form>
          )}
        </CardContent>

        <CardFooter className="flex flex-col gap-4">
          <div className="relative w-full">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                New to Partner Program?
              </span>
            </div>
          </div>

          <Button variant="outline" className="w-full" asChild>
            <Link href="/become-partner">
              Become a Partner
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
