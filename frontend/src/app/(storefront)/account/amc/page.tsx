'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Shield,
  Check,
  X,
  ChevronRight,
  Calendar,
  Wrench,
  Package,
  Loader2,
  Star,
  AlertCircle,
  CheckCircle,
  Phone,
  Clock,
  Zap,
  Crown,
  RefreshCw,
  CreditCard,
  Timer,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { useIsAuthenticated } from '@/lib/storefront/auth-store';
import { useAuthStore } from '@/lib/storefront/auth-store';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import {
  amcApi,
  paymentsApi,
  deviceApi,
  AMCPlan as APIPlan,
  AMCContract,
  AMCTenureOption,
} from '@/lib/storefront/api';

// Razorpay types
declare global {
  interface Window {
    Razorpay: any;
  }
}

// Types
interface DisplayPlan {
  id: string;
  name: string;
  code: string;
  amc_type: string;
  contract_type: string;
  duration_months: number;
  base_price: number;
  tax_rate: number;
  services_included: number;
  parts_covered: boolean;
  labor_covered: boolean;
  emergency_support: boolean;
  priority_support: boolean;
  discount_on_parts: number;
  features: string[];
  tenure_options: AMCTenureOption[];
  response_sla_hours: number;
  resolution_sla_hours: number;
  is_popular?: boolean;
  description?: string;
}

interface ActiveAMC {
  id: string;
  plan_name: string;
  contract_type?: string;
  device_name: string;
  device_serial: string;
  start_date: string;
  end_date: string;
  status: 'active' | 'expired' | 'expiring_soon' | 'pending_inspection';
  visits_used: number;
  visits_total: number;
  visits_remaining: number;
  days_remaining: number;
  next_service_date?: string;
  grace_end_date?: string;
  requires_inspection: boolean;
  inspection_status?: string;
}

export default function AMCPage() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const [activeAMCs, setActiveAMCs] = useState<ActiveAMC[]>([]);
  const [plans, setPlans] = useState<DisplayPlan[]>([]);
  const [devices, setDevices] = useState<{ id: string; name: string; serial: string; warranty_status: string; amc_status: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBuyDialog, setShowBuyDialog] = useState(false);
  const [showRenewDialog, setShowRenewDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<DisplayPlan | null>(null);
  const [selectedDevice, setSelectedDevice] = useState('');
  const [selectedTenure, setSelectedTenure] = useState<number>(12);
  const [purchasing, setPurchasing] = useState(false);
  const [renewingContract, setRenewingContract] = useState<ActiveAMC | null>(null);
  const [contractTypeFilter, setContractTypeFilter] = useState<string>('all');

  // Load Razorpay script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [plansData, contractsData, devicesData] = await Promise.all([
        amcApi.getPlans().catch(() => []),
        amcApi.getMyContracts().catch(() => []),
        deviceApi.getMyDevices().catch(() => []),
      ]);

      // Transform plans
      if (plansData && plansData.length > 0) {
        const transformedPlans: DisplayPlan[] = plansData.map((plan: APIPlan, index: number) => ({
          id: plan.id,
          name: plan.name,
          code: plan.code,
          amc_type: plan.amc_type,
          contract_type: plan.contract_type || 'COMPREHENSIVE',
          duration_months: plan.duration_months,
          base_price: plan.base_price,
          tax_rate: plan.tax_rate,
          services_included: plan.services_included,
          parts_covered: plan.parts_covered,
          labor_covered: plan.labor_covered,
          emergency_support: plan.emergency_support,
          priority_support: plan.priority_support,
          discount_on_parts: plan.discount_on_parts,
          features: generateFeatures(plan),
          tenure_options: plan.tenure_options || [{ months: 12, price: plan.base_price, discount_pct: 0 }],
          response_sla_hours: plan.response_sla_hours || 48,
          resolution_sla_hours: plan.resolution_sla_hours || 72,
          is_popular: index === 1,
          description: plan.description,
        }));
        setPlans(transformedPlans);
      }

      // Transform contracts
      const transformedAMCs: ActiveAMC[] = contractsData.map((contract: AMCContract) => {
        const endDate = new Date(contract.end_date);
        const now = new Date();
        const daysRemaining = contract.days_remaining ?? Math.floor((endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

        let status: ActiveAMC['status'] = 'active';
        if (contract.requires_inspection) status = 'pending_inspection';
        else if (daysRemaining < 0) status = 'expired';
        else if (daysRemaining <= 30) status = 'expiring_soon';

        return {
          id: contract.id,
          plan_name: contract.plan_name,
          contract_type: contract.contract_type,
          device_name: contract.product_name,
          device_serial: contract.serial_number,
          start_date: contract.start_date,
          end_date: contract.end_date,
          status,
          visits_used: contract.services_used,
          visits_total: contract.total_services,
          visits_remaining: contract.services_remaining ?? (contract.total_services - contract.services_used),
          days_remaining: daysRemaining,
          next_service_date: contract.next_service_due,
          grace_end_date: contract.grace_end_date,
          requires_inspection: contract.requires_inspection,
          inspection_status: contract.inspection_status,
        };
      });
      setActiveAMCs(transformedAMCs);

      // Transform devices
      const deviceOptions = devicesData.map((device) => ({
        id: device.serial_number,
        name: device.product_name,
        serial: device.serial_number,
        warranty_status: device.warranty_status,
        amc_status: device.amc_status,
      }));
      setDevices(deviceOptions);
    } catch (error) {
      console.error('Failed to load AMC data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/account/login?redirect=/account/amc');
      return;
    }
    fetchData();
  }, [isAuthenticated, router, fetchData]);

  function generateFeatures(plan: APIPlan): string[] {
    const features: string[] = [];
    features.push(`${plan.services_included === 99 ? 'Unlimited' : plan.services_included} preventive maintenance visits`);
    if (plan.discount_on_parts > 0) features.push(`${plan.discount_on_parts}% discount on spare parts`);
    if (plan.priority_support) features.push('Priority phone & WhatsApp support');
    if (plan.emergency_support) features.push('24/7 emergency support');
    if (plan.labor_covered) features.push('Free labor charges');
    if (plan.parts_covered) features.push('Parts covered under plan');
    if (plan.response_sla_hours && plan.response_sla_hours <= 24) features.push(`${plan.response_sla_hours}-hour response guarantee`);
    if (plan.resolution_sla_hours && plan.resolution_sla_hours <= 48) features.push(`${plan.resolution_sla_hours}-hour resolution SLA`);
    // Add custom features from plan
    if (plan.features_included) {
      plan.features_included.forEach((f) => {
        features.push(`${f.quantity > 1 ? f.quantity + 'x ' : ''}${f.name} (${f.frequency})`);
      });
    }
    if (plan.description) features.push(plan.description);
    return features;
  }

  // Get price for selected tenure
  function getTenurePrice(plan: DisplayPlan, months: number): { price: number; discount_pct: number; monthly: number } {
    const tenure = plan.tenure_options.find((t) => t.months === months);
    if (tenure) {
      return {
        price: tenure.price,
        discount_pct: tenure.discount_pct,
        monthly: Math.round(tenure.price / months),
      };
    }
    // Fallback: scale base price
    const yearMultiplier = months / 12;
    return {
      price: Math.round(plan.base_price * yearMultiplier),
      discount_pct: 0,
      monthly: Math.round(plan.base_price / 12),
    };
  }

  // Get total with tax
  function getTotalWithTax(price: number, taxRate: number): number {
    return Math.round(price * (1 + taxRate / 100));
  }

  const handleBuyPlan = (plan: DisplayPlan) => {
    setSelectedPlan(plan);
    setSelectedTenure(12);
    setSelectedDevice('');
    setShowBuyDialog(true);
  };

  const handleRenew = (amc: ActiveAMC) => {
    setRenewingContract(amc);
    setSelectedTenure(12);
    setShowRenewDialog(true);
  };

  const handlePurchase = async () => {
    if (!selectedDevice || !selectedPlan) {
      toast.error('Please select a device');
      return;
    }

    setPurchasing(true);
    try {
      const pricing = getTenurePrice(selectedPlan, selectedTenure);
      const totalAmount = getTotalWithTax(pricing.price, selectedPlan.tax_rate);

      // Try Razorpay payment first
      if (window.Razorpay) {
        try {
          const paymentOrder = await amcApi.createPaymentOrder({
            plan_id: selectedPlan.id,
            serial_number: selectedDevice,
            duration_months: selectedTenure,
            amount: totalAmount,
          });

          const razorpayOptions = {
            key: paymentOrder.key_id,
            amount: paymentOrder.amount,
            currency: paymentOrder.currency,
            name: 'Aquapurite',
            description: `${selectedPlan.name} - ${selectedTenure} months`,
            order_id: paymentOrder.razorpay_order_id,
            handler: async (response: any) => {
              // Verify payment
              try {
                await paymentsApi.verifyPayment({
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                  order_id: paymentOrder.order_id,
                });

                // Create AMC contract after successful payment
                const result = await amcApi.purchasePlan(selectedPlan.id, selectedDevice, {
                  duration_months: selectedTenure,
                  sales_channel: 'ONLINE',
                });
                toast.success(result.message || 'AMC plan purchased successfully!');
                setShowBuyDialog(false);
                fetchData();
              } catch {
                toast.error('Payment verification failed. Please contact support.');
              }
            },
            prefill: {
              name: paymentOrder.customer_name,
              email: paymentOrder.customer_email,
              contact: paymentOrder.customer_phone,
            },
            theme: { color: '#2563eb' },
          };

          const rzp = new window.Razorpay(razorpayOptions);
          rzp.open();
          setPurchasing(false);
          return;
        } catch {
          // Razorpay not available or failed, fall back to direct purchase
          console.log('Razorpay unavailable, using direct purchase');
        }
      }

      // Direct purchase fallback (no payment gateway)
      const result = await amcApi.purchasePlan(selectedPlan.id, selectedDevice, {
        duration_months: selectedTenure,
        sales_channel: 'ONLINE',
      });
      toast.success(result.message || 'AMC plan purchased successfully!');
      setShowBuyDialog(false);
      setSelectedPlan(null);
      setSelectedDevice('');
      fetchData();
    } catch (error) {
      console.error('Failed to purchase plan:', error);
      toast.error('Failed to purchase plan. Please try again.');
    } finally {
      setPurchasing(false);
    }
  };

  const handleRenewContract = async () => {
    if (!renewingContract) return;

    setPurchasing(true);
    try {
      const result = await amcApi.renewContract(renewingContract.id, {
        duration_months: selectedTenure,
        sales_channel: 'ONLINE',
      });
      toast.success(result.message || 'Contract renewed successfully!');
      setShowRenewDialog(false);
      setRenewingContract(null);
      fetchData();
    } catch (error) {
      console.error('Failed to renew contract:', error);
      toast.error('Failed to renew contract. Please try again.');
    } finally {
      setPurchasing(false);
    }
  };

  const handleRequestInspection = async (amcId: string) => {
    try {
      const result = await amcApi.requestInspection(amcId);
      toast.success(result.message || 'Inspection requested. Our team will contact you.');
      fetchData();
    } catch (error) {
      console.error('Failed to request inspection:', error);
      toast.error('Failed to request inspection. Please try again.');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'expiring_soon':
        return <Badge className="bg-yellow-100 text-yellow-800">Expiring Soon</Badge>;
      case 'expired':
        return <Badge className="bg-red-100 text-red-800">Expired</Badge>;
      case 'pending_inspection':
        return <Badge className="bg-orange-100 text-orange-800">Inspection Required</Badge>;
      default:
        return null;
    }
  };

  // Filter plans by contract type
  const filteredPlans = contractTypeFilter === 'all'
    ? plans
    : plans.filter((p) => p.contract_type === contractTypeFilter);

  // Available tenure options from all plans
  const availableTenures = [12, 24, 36, 48];

  // Devices eligible for AMC (no active AMC)
  const eligibleDevices = devices.filter((d) => d.amc_status === 'none' || d.amc_status === 'expired');

  if (!isAuthenticated) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl md:text-3xl font-bold">Annual Maintenance Contracts</h1>
        <p className="text-muted-foreground mt-2 max-w-2xl mx-auto">
          Keep your water purifier running at peak performance with our comprehensive maintenance plans.
        </p>
      </div>

      {/* Active AMCs */}
      {activeAMCs.length > 0 && (
        <div className="mb-12">
          <h2 className="text-xl font-semibold mb-4">Your Active Plans</h2>
          <div className="space-y-4">
            {activeAMCs.map((amc) => (
              <Card key={amc.id} className={cn(
                amc.status === 'expiring_soon' && 'border-yellow-300',
                amc.status === 'expired' && 'border-red-300',
                amc.status === 'pending_inspection' && 'border-orange-300'
              )}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Shield className="h-5 w-5 text-primary" />
                        <span className="font-semibold">{amc.plan_name}</span>
                        {getStatusBadge(amc.status)}
                        {amc.contract_type && (
                          <Badge variant="outline" className="text-xs">
                            {amc.contract_type === 'COMPREHENSIVE' ? 'Comprehensive' : 'Non-Comprehensive'}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {amc.device_name} ({amc.device_serial})
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Valid Until</p>
                      <p className="font-medium">
                        {new Date(amc.end_date).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </p>
                      {amc.days_remaining > 0 && amc.days_remaining <= 90 && (
                        <p className="text-xs text-yellow-600 mt-1">
                          {amc.days_remaining} days remaining
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-sm">
                    <div>
                      <span className="text-muted-foreground">Visits Used:</span>
                      <span className="ml-2 font-medium">
                        {amc.visits_used}/{amc.visits_total}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Remaining:</span>
                      <span className="ml-2 font-medium text-green-600">
                        {amc.visits_remaining}
                      </span>
                    </div>
                    {amc.next_service_date && (
                      <div>
                        <span className="text-muted-foreground">Next Service:</span>
                        <span className="ml-2 font-medium">
                          {new Date(amc.next_service_date).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                          })}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Actions based on status */}
                  {(amc.status === 'expiring_soon' || amc.status === 'expired') && (
                    <div className="mt-4 pt-4 border-t flex items-center gap-3">
                      <Button size="sm" onClick={() => handleRenew(amc)}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Renew Now
                      </Button>
                      {amc.status === 'expiring_soon' && (
                        <p className="text-xs text-muted-foreground">
                          Renew before expiry to avoid inspection fees
                        </p>
                      )}
                    </div>
                  )}

                  {amc.status === 'pending_inspection' && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-3">
                        <div className="flex items-center gap-2 text-orange-800">
                          <AlertCircle className="h-4 w-4" />
                          <span className="text-sm font-medium">
                            Contract has lapsed. An inspection is required before renewal.
                          </span>
                        </div>
                        {amc.grace_end_date && (
                          <p className="text-xs text-orange-600 mt-1 ml-6">
                            Grace period ends: {new Date(amc.grace_end_date).toLocaleDateString('en-IN')}
                          </p>
                        )}
                      </div>
                      {amc.inspection_status !== 'REQUESTED' && (
                        <Button size="sm" variant="outline" onClick={() => handleRequestInspection(amc.id)}>
                          Request Inspection
                        </Button>
                      )}
                      {amc.inspection_status === 'REQUESTED' && (
                        <Badge className="bg-blue-100 text-blue-800">Inspection Requested</Badge>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Plan Filter */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Choose Your Plan</h2>
        <Tabs value={contractTypeFilter} onValueChange={setContractTypeFilter}>
          <TabsList className="h-9">
            <TabsTrigger value="all" className="text-xs">All Plans</TabsTrigger>
            <TabsTrigger value="COMPREHENSIVE" className="text-xs">Comprehensive</TabsTrigger>
            <TabsTrigger value="NON_COMPREHENSIVE" className="text-xs">Non-Comprehensive</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Tenure Selector */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Timer className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Select Duration</span>
        </div>
        <div className="flex gap-2">
          {availableTenures.map((months) => (
            <Button
              key={months}
              variant={selectedTenure === months ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedTenure(months)}
              className="relative"
            >
              {months / 12} Year{months > 12 ? 's' : ''}
              {months >= 24 && (
                <span className="absolute -top-2 -right-2 bg-green-500 text-white text-[10px] px-1 rounded-full">
                  Save {months === 24 ? '10%' : months === 36 ? '15%' : '20%'}
                </span>
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* AMC Plans Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredPlans.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Shield className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Plans Available</h3>
            <p className="text-muted-foreground">
              AMC plans are being updated. Please check back soon.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {filteredPlans.map((plan) => {
            const pricing = getTenurePrice(plan, selectedTenure);
            const totalWithTax = getTotalWithTax(pricing.price, plan.tax_rate);
            const baseTotal = getTotalWithTax(plan.base_price, plan.tax_rate);

            return (
              <Card
                key={plan.id}
                className={cn(
                  'relative overflow-hidden flex flex-col',
                  plan.is_popular && 'border-primary shadow-lg'
                )}
              >
                {plan.is_popular && (
                  <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-xs px-3 py-1 rounded-bl-lg font-medium">
                    Most Popular
                  </div>
                )}
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {plan.priority_support ? (
                        <Crown className="h-5 w-5 text-yellow-500" />
                      ) : (
                        <Shield className="h-5 w-5 text-primary" />
                      )}
                      {plan.name}
                    </CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {plan.contract_type === 'COMPREHENSIVE' ? 'Comprehensive' : 'Non-Comprehensive'}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      <Clock className="h-3 w-3 mr-1" />
                      {plan.response_sla_hours}h Response
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 flex-1">
                  {/* Price */}
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">{formatCurrency(totalWithTax)}</span>
                      {pricing.discount_pct > 0 && (
                        <span className="text-muted-foreground line-through text-sm">
                          {formatCurrency(Math.round(baseTotal * (selectedTenure / 12)))}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatCurrency(pricing.monthly)}/month
                      {pricing.discount_pct > 0 && (
                        <span className="text-green-600 ml-2">
                          Save {pricing.discount_pct}%
                        </span>
                      )}
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      incl. {plan.tax_rate}% GST for {selectedTenure} months
                    </p>
                  </div>

                  {/* Key Highlights */}
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <Wrench className="h-4 w-4 text-primary" />
                      <span>
                        {plan.services_included === 99 ? 'Unlimited' : plan.services_included * (selectedTenure / 12)} visits
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Package className="h-4 w-4 text-primary" />
                      <span>{plan.discount_on_parts}% off parts</span>
                    </div>
                  </div>

                  {/* Coverage badges */}
                  <div className="flex flex-wrap gap-1.5">
                    {plan.parts_covered && (
                      <Badge variant="secondary" className="text-[10px]">
                        <Check className="h-3 w-3 mr-0.5" /> Parts
                      </Badge>
                    )}
                    {plan.labor_covered && (
                      <Badge variant="secondary" className="text-[10px]">
                        <Check className="h-3 w-3 mr-0.5" /> Labor
                      </Badge>
                    )}
                    {plan.emergency_support && (
                      <Badge variant="secondary" className="text-[10px]">
                        <Zap className="h-3 w-3 mr-0.5" /> Emergency
                      </Badge>
                    )}
                  </div>

                  <Separator />

                  {/* Features */}
                  <ul className="space-y-2">
                    {plan.features.slice(0, 8).map((feature, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* SLA */}
                  <div className="bg-muted/50 rounded-lg p-3 text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Response Time</span>
                      <span className="font-medium">{plan.response_sla_hours} hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Resolution Time</span>
                      <span className="font-medium">{plan.resolution_sla_hours} hours</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full"
                    variant={plan.is_popular ? 'default' : 'outline'}
                    onClick={() => handleBuyPlan(plan)}
                  >
                    <CreditCard className="h-4 w-4 mr-2" />
                    Choose {plan.name}
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      {/* Plan Comparison Table */}
      {filteredPlans.length > 1 && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="text-lg">Compare Plans</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-4">Feature</th>
                    {filteredPlans.map((plan) => (
                      <th key={plan.id} className="text-center py-2 px-2">{plan.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Contract Type</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2 text-xs">
                        {plan.contract_type === 'COMPREHENSIVE' ? 'Comprehensive' : 'Non-Comprehensive'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Service Visits / Year</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">
                        {plan.services_included === 99 ? 'Unlimited' : plan.services_included}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Parts Covered</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">
                        {plan.parts_covered ? <Check className="h-4 w-4 text-green-600 mx-auto" /> : <X className="h-4 w-4 text-red-400 mx-auto" />}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Labor Covered</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">
                        {plan.labor_covered ? <Check className="h-4 w-4 text-green-600 mx-auto" /> : <X className="h-4 w-4 text-red-400 mx-auto" />}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Parts Discount</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">{plan.discount_on_parts}%</td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Emergency Support</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">
                        {plan.emergency_support ? <Check className="h-4 w-4 text-green-600 mx-auto" /> : <X className="h-4 w-4 text-red-400 mx-auto" />}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Response SLA</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">{plan.response_sla_hours}h</td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 text-muted-foreground">Resolution SLA</td>
                    {filteredPlans.map((plan) => (
                      <td key={plan.id} className="text-center py-2 px-2">{plan.resolution_sla_hours}h</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 text-muted-foreground font-medium">Price ({selectedTenure} months)</td>
                    {filteredPlans.map((plan) => {
                      const pricing = getTenurePrice(plan, selectedTenure);
                      const total = getTotalWithTax(pricing.price, plan.tax_rate);
                      return (
                        <td key={plan.id} className="text-center py-2 px-2 font-semibold">
                          {formatCurrency(total)}
                        </td>
                      );
                    })}
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Why AMC */}
      <Card className="mt-8">
        <CardContent className="py-8">
          <h3 className="text-xl font-semibold text-center mb-6">Why Choose an AMC?</h3>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                icon: <Wrench className="h-6 w-6" />,
                title: 'Regular Maintenance',
                description: 'Scheduled visits keep your purifier in top condition',
              },
              {
                icon: <Package className="h-6 w-6" />,
                title: 'Parts Discount',
                description: 'Save up to 25% on filter and spare parts',
              },
              {
                icon: <Star className="h-6 w-6" />,
                title: 'Priority Support',
                description: 'Get faster response with SLA-backed service',
              },
              {
                icon: <CheckCircle className="h-6 w-6" />,
                title: 'Peace of Mind',
                description: 'No surprise repair bills during coverage',
              },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3 text-primary">
                  {item.icon}
                </div>
                <h4 className="font-medium mb-1">{item.title}</h4>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Buy Dialog */}
      <Dialog open={showBuyDialog} onOpenChange={setShowBuyDialog}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>Purchase AMC Plan</DialogTitle>
            <DialogDescription>
              {selectedPlan?.name} - {selectedTenure} months
              {selectedPlan?.contract_type === 'COMPREHENSIVE' ? ' (Comprehensive)' : ' (Non-Comprehensive)'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Device Selection */}
            <div>
              <Label>Select Device</Label>
              <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                <SelectTrigger className="mt-1.5">
                  <SelectValue placeholder="Choose a device" />
                </SelectTrigger>
                <SelectContent>
                  {eligibleDevices.length > 0 ? (
                    eligibleDevices.map((device) => (
                      <SelectItem key={device.id} value={device.serial}>
                        <div className="flex items-center gap-2">
                          <span>{device.name} ({device.serial})</span>
                          {device.warranty_status === 'expiring_soon' && (
                            <Badge variant="outline" className="text-[10px] text-yellow-600">Warranty Expiring</Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="no-devices" disabled>
                      No eligible devices
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Don&apos;t see your device?{' '}
                <Link href="/account/devices" className="text-primary hover:underline">
                  Register it first
                </Link>
              </p>
            </div>

            {/* Tenure Selection in Dialog */}
            <div>
              <Label>Duration</Label>
              <RadioGroup
                value={selectedTenure.toString()}
                onValueChange={(v) => setSelectedTenure(parseInt(v))}
                className="grid grid-cols-4 gap-2 mt-1.5"
              >
                {availableTenures.map((months) => {
                  if (!selectedPlan) return null;
                  const pricing = getTenurePrice(selectedPlan, months);
                  const total = getTotalWithTax(pricing.price, selectedPlan.tax_rate);
                  return (
                    <Label
                      key={months}
                      htmlFor={`tenure-${months}`}
                      className={cn(
                        'flex flex-col items-center justify-center rounded-md border-2 border-muted p-2 hover:bg-accent cursor-pointer',
                        selectedTenure === months && 'border-primary bg-primary/5'
                      )}
                    >
                      <RadioGroupItem value={months.toString()} id={`tenure-${months}`} className="sr-only" />
                      <span className="text-xs font-medium">{months / 12}Y</span>
                      <span className="text-[10px] text-muted-foreground">{formatCurrency(total)}</span>
                      {pricing.discount_pct > 0 && (
                        <span className="text-[9px] text-green-600">-{pricing.discount_pct}%</span>
                      )}
                    </Label>
                  );
                })}
              </RadioGroup>
            </div>

            {/* Price Summary */}
            {selectedPlan && (
              <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                {(() => {
                  const pricing = getTenurePrice(selectedPlan, selectedTenure);
                  const taxAmount = Math.round(pricing.price * selectedPlan.tax_rate / 100);
                  const total = pricing.price + taxAmount;
                  return (
                    <>
                      <div className="flex justify-between text-sm">
                        <span>{selectedPlan.name} ({selectedTenure} months)</span>
                        <span>{formatCurrency(pricing.price)}</span>
                      </div>
                      <div className="flex justify-between text-sm text-muted-foreground">
                        <span>GST ({selectedPlan.tax_rate}%)</span>
                        <span>{formatCurrency(taxAmount)}</span>
                      </div>
                      {pricing.discount_pct > 0 && (
                        <div className="flex justify-between text-sm text-green-600">
                          <span>Multi-year Discount</span>
                          <span>-{pricing.discount_pct}%</span>
                        </div>
                      )}
                      <Separator />
                      <div className="flex justify-between font-semibold">
                        <span>Total</span>
                        <span>{formatCurrency(total)}</span>
                      </div>
                      <p className="text-[10px] text-muted-foreground">
                        = {formatCurrency(pricing.monthly)}/month
                      </p>
                    </>
                  );
                })()}
              </div>
            )}

            <div className="flex items-start gap-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <p>
                AMC will be activated within 24 hours of payment confirmation. You&apos;ll receive a confirmation call.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBuyDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handlePurchase} disabled={purchasing || !selectedDevice}>
              {purchasing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <CreditCard className="h-4 w-4 mr-2" />
                  Pay {selectedPlan ? formatCurrency(getTotalWithTax(getTenurePrice(selectedPlan, selectedTenure).price, selectedPlan.tax_rate)) : ''}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Renew Dialog */}
      <Dialog open={showRenewDialog} onOpenChange={setShowRenewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Renew AMC Contract</DialogTitle>
            <DialogDescription>
              Renew your {renewingContract?.plan_name} for {renewingContract?.device_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Renewal Duration</Label>
              <RadioGroup
                value={selectedTenure.toString()}
                onValueChange={(v) => setSelectedTenure(parseInt(v))}
                className="grid grid-cols-4 gap-2 mt-1.5"
              >
                {availableTenures.map((months) => (
                  <Label
                    key={months}
                    htmlFor={`renew-tenure-${months}`}
                    className={cn(
                      'flex flex-col items-center justify-center rounded-md border-2 border-muted p-2 hover:bg-accent cursor-pointer',
                      selectedTenure === months && 'border-primary bg-primary/5'
                    )}
                  >
                    <RadioGroupItem value={months.toString()} id={`renew-tenure-${months}`} className="sr-only" />
                    <span className="text-sm font-medium">{months / 12} Year{months > 12 ? 's' : ''}</span>
                    {months >= 24 && (
                      <span className="text-[10px] text-green-600">
                        Save {months === 24 ? '10%' : months === 36 ? '15%' : '20%'}
                      </span>
                    )}
                  </Label>
                ))}
              </RadioGroup>
            </div>

            <div className="flex items-start gap-2 text-sm text-muted-foreground">
              <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-green-600" />
              <p>
                Your renewal will start from the current contract&apos;s end date to ensure continuous coverage.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenewDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleRenewContract} disabled={purchasing}>
              {purchasing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Renewing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Renew for {selectedTenure / 12} Year{selectedTenure > 12 ? 's' : ''}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Help */}
      <Card className="mt-8">
        <CardContent className="py-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded-full">
              <Phone className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Need help choosing a plan?</h3>
              <p className="text-sm text-muted-foreground">
                Our experts can help you find the right AMC for your needs.
              </p>
            </div>
            <Button variant="outline" asChild>
              <a href="https://wa.me/919311939076?text=I need help choosing an AMC plan" target="_blank" rel="noopener noreferrer">
                Chat with Us
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
