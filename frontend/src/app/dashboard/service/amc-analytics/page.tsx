'use client';

import { useState, useEffect } from 'react';
import {
  Shield,
  TrendingUp,
  Users,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  Loader2,
  BarChart3,
  PieChart,
  Target,
  RefreshCw,
  Phone,
  Clock,
  IndianRupee,
  Percent,
  Activity,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { amcApi } from '@/lib/api';

interface ConversionData {
  total_installations: number;
  installations_with_amc: number;
  conversion_rate: number;
  expired_warranty_no_amc: number;
  opportunity_count: number;
  by_channel: Record<string, number>;
  monthly_trend: { month: string; contracts: number; revenue: number }[];
  warranty_expiry_funnel: Record<string, number>;
}

interface ProfitabilityData {
  total_revenue: number;
  revenue_recognized: number;
  revenue_pending: number;
  average_contract_value: number;
  total_contracts: number;
  active_contracts: number;
  renewal_rate: number;
  renewed_count: number;
  expired_count: number;
  by_plan: { plan_name: string; count: number; revenue: number; avg_value: number }[];
  by_channel: { channel: string; count: number; revenue: number }[];
  total_services_delivered: number;
  total_commission: number;
  commission_paid: number;
  sla_breached_count: number;
  sla_compliance_rate: number;
}

interface ChurnRiskCustomer {
  contract_id: string;
  contract_number: string;
  customer_name: string;
  customer_phone: string;
  product_name: string;
  serial_number: string;
  end_date: string;
  days_remaining: number;
  services_used: number;
  total_services: number;
  risk_score: number;
  risk_level: string;
  risk_factors: string[];
}

interface ChurnData {
  total_at_risk: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  customers: ChurnRiskCustomer[];
}

export default function AMCAnalyticsPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [conversion, setConversion] = useState<ConversionData | null>(null);
  const [profitability, setProfitability] = useState<ProfitabilityData | null>(null);
  const [churn, setChurn] = useState<ChurnData | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [convData, profData, churnData] = await Promise.all([
          amcApi.getConversionAnalytics().catch(() => null),
          amcApi.getProfitabilityAnalytics().catch(() => null),
          amcApi.getChurnRisk().catch(() => null),
        ]);
        setConversion(convData);
        setProfitability(profData);
        setChurn(churnData);
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AMC Analytics & Intelligence</h1>
        <p className="text-muted-foreground">
          Conversion funnels, profitability metrics, churn prediction, and SLA compliance.
        </p>
      </div>

      {/* Top KPI Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Conversion Rate</p>
                <p className="text-2xl font-bold">{conversion?.conversion_rate || 0}%</p>
                <p className="text-[10px] text-muted-foreground">Warranty to AMC</p>
              </div>
              <Target className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">AMC Revenue</p>
                <p className="text-2xl font-bold">
                  <span className="text-base">Rs </span>
                  {((profitability?.total_revenue || 0) / 1000).toFixed(0)}K
                </p>
                <p className="text-[10px] text-muted-foreground">Total lifetime</p>
              </div>
              <IndianRupee className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Renewal Rate</p>
                <p className="text-2xl font-bold">{profitability?.renewal_rate || 0}%</p>
                <p className="text-[10px] text-muted-foreground">
                  {profitability?.renewed_count || 0} renewed
                </p>
              </div>
              <RefreshCw className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">SLA Compliance</p>
                <p className="text-2xl font-bold">{profitability?.sla_compliance_rate || 100}%</p>
                <p className="text-[10px] text-muted-foreground">
                  {profitability?.sla_breached_count || 0} breaches
                </p>
              </div>
              <Activity className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Churn Risk</p>
                <p className="text-2xl font-bold text-red-600">{churn?.high_risk || 0}</p>
                <p className="text-[10px] text-muted-foreground">
                  High risk of {churn?.total_at_risk || 0} total
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">
            <BarChart3 className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="conversion">
            <Target className="h-4 w-4 mr-2" />
            Conversion Funnel
          </TabsTrigger>
          <TabsTrigger value="profitability">
            <IndianRupee className="h-4 w-4 mr-2" />
            Profitability
          </TabsTrigger>
          <TabsTrigger value="churn">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Churn Risk
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Warranty Expiry Funnel */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Warranty Expiry Funnel</CardTitle>
              <CardDescription>Devices with expiring warranty (without AMC) - conversion opportunities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { label: 'Next 7 days', key: 'expiring_in_7_days', color: 'bg-red-500' },
                  { label: 'Next 15 days', key: 'expiring_in_15_days', color: 'bg-orange-500' },
                  { label: 'Next 30 days', key: 'expiring_in_30_days', color: 'bg-yellow-500' },
                  { label: 'Next 60 days', key: 'expiring_in_60_days', color: 'bg-blue-400' },
                  { label: 'Next 90 days', key: 'expiring_in_90_days', color: 'bg-blue-300' },
                ].map((item) => {
                  const count = conversion?.warranty_expiry_funnel?.[item.key] || 0;
                  const maxCount = conversion?.warranty_expiry_funnel?.['expiring_in_90_days'] || 1;
                  const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
                  return (
                    <div key={item.key} className="flex items-center gap-4">
                      <span className="text-sm w-28 text-muted-foreground">{item.label}</span>
                      <div className="flex-1 bg-muted rounded-full h-6 relative overflow-hidden">
                        <div
                          className={`h-full ${item.color} rounded-full transition-all`}
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                        <span className="absolute inset-0 flex items-center justify-center text-xs font-medium">
                          {count} devices
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Monthly Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Monthly AMC Sales Trend</CardTitle>
              <CardDescription>New contracts and revenue over last 6 months</CardDescription>
            </CardHeader>
            <CardContent>
              {conversion?.monthly_trend && conversion.monthly_trend.length > 0 ? (
                <div className="space-y-2">
                  {conversion.monthly_trend.map((month) => (
                    <div key={month.month} className="flex items-center gap-4">
                      <span className="text-sm w-20 text-muted-foreground">{month.month}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-muted rounded-full h-4 relative overflow-hidden">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{
                                width: `${Math.max(
                                  (month.contracts / Math.max(...conversion.monthly_trend.map(m => m.contracts), 1)) * 100,
                                  3
                                )}%`
                              }}
                            />
                          </div>
                          <span className="text-xs w-20 text-right">
                            {month.contracts} contracts
                          </span>
                          <span className="text-xs w-24 text-right text-muted-foreground">
                            Rs {(month.revenue / 1000).toFixed(1)}K
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-4 text-center">No monthly trend data available</p>
              )}
            </CardContent>
          </Card>

          {/* Channel Breakdown */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sales by Channel</CardTitle>
              </CardHeader>
              <CardContent>
                {profitability?.by_channel && profitability.by_channel.length > 0 ? (
                  <div className="space-y-3">
                    {profitability.by_channel.map((ch) => (
                      <div key={ch.channel} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{ch.channel}</Badge>
                          <span className="text-sm">{ch.count} contracts</span>
                        </div>
                        <span className="font-medium">Rs {ch.revenue.toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-4 text-center">No channel data</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Revenue by Plan</CardTitle>
              </CardHeader>
              <CardContent>
                {profitability?.by_plan && profitability.by_plan.length > 0 ? (
                  <div className="space-y-3">
                    {profitability.by_plan.map((plan) => (
                      <div key={plan.plan_name} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">{plan.plan_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {plan.count} contracts | Avg: Rs {Math.round(plan.avg_value).toLocaleString('en-IN')}
                          </p>
                        </div>
                        <span className="font-medium">Rs {plan.revenue.toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-4 text-center">No plan data</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Conversion Funnel Tab */}
        <TabsContent value="conversion" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-4xl font-bold">{conversion?.total_installations || 0}</p>
                <p className="text-sm text-muted-foreground">Total Installations</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-4xl font-bold text-green-600">
                  {conversion?.installations_with_amc || 0}
                </p>
                <p className="text-sm text-muted-foreground">With Active AMC</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-4xl font-bold text-blue-600">
                  {conversion?.conversion_rate || 0}%
                </p>
                <p className="text-sm text-muted-foreground">Conversion Rate</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-4xl font-bold text-orange-600">
                  {conversion?.opportunity_count || 0}
                </p>
                <p className="text-sm text-muted-foreground">Untapped Opportunity</p>
                <p className="text-xs text-muted-foreground">Expired warranty, no AMC</p>
              </CardContent>
            </Card>
          </div>

          {/* Channel-wise conversion */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Conversion by Channel</CardTitle>
              <CardDescription>Number of AMC contracts sold per sales channel</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-4">
                {Object.entries(conversion?.by_channel || {}).map(([channel, count]) => (
                  <div key={channel} className="border rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold">{count as number}</p>
                    <p className="text-sm text-muted-foreground">{channel}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {conversion?.total_installations
                        ? ((count as number) / conversion.total_installations * 100).toFixed(1)
                        : 0}% of total
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Profitability Tab */}
        <TabsContent value="profitability" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground">Total AMC Revenue</p>
                <p className="text-xl font-bold">
                  Rs {(profitability?.total_revenue || 0).toLocaleString('en-IN')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground">Revenue Recognized</p>
                <p className="text-xl font-bold text-green-600">
                  Rs {(profitability?.revenue_recognized || 0).toLocaleString('en-IN')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground">Revenue Pending</p>
                <p className="text-xl font-bold text-orange-600">
                  Rs {(profitability?.revenue_pending || 0).toLocaleString('en-IN')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-muted-foreground">Avg Contract Value</p>
                <p className="text-xl font-bold">
                  Rs {Math.round(profitability?.average_contract_value || 0).toLocaleString('en-IN')}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Commission & SLA */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <IndianRupee className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Commission</p>
                    <p className="text-lg font-bold">
                      Rs {(profitability?.total_commission || 0).toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Paid: Rs {(profitability?.commission_paid || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Activity className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Services Delivered</p>
                    <p className="text-lg font-bold">{profitability?.total_services_delivered || 0}</p>
                    <p className="text-xs text-muted-foreground">
                      For AMC contracts
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-100 rounded-lg">
                    <CheckCircle className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">SLA Compliance</p>
                    <p className="text-lg font-bold">{profitability?.sla_compliance_rate || 100}%</p>
                    <p className="text-xs text-muted-foreground">
                      {profitability?.sla_breached_count || 0} breaches
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Plan-wise breakdown table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Revenue by Plan Tier</CardTitle>
            </CardHeader>
            <CardContent>
              {profitability?.by_plan && profitability.by_plan.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Plan</TableHead>
                      <TableHead className="text-right">Contracts</TableHead>
                      <TableHead className="text-right">Total Revenue</TableHead>
                      <TableHead className="text-right">Avg Value</TableHead>
                      <TableHead className="text-right">% of Revenue</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {profitability.by_plan.map((plan) => (
                      <TableRow key={plan.plan_name}>
                        <TableCell className="font-medium">{plan.plan_name}</TableCell>
                        <TableCell className="text-right">{plan.count}</TableCell>
                        <TableCell className="text-right">
                          Rs {plan.revenue.toLocaleString('en-IN')}
                        </TableCell>
                        <TableCell className="text-right">
                          Rs {Math.round(plan.avg_value).toLocaleString('en-IN')}
                        </TableCell>
                        <TableCell className="text-right">
                          {profitability.total_revenue > 0
                            ? ((plan.revenue / profitability.total_revenue) * 100).toFixed(1)
                            : 0}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-sm text-muted-foreground py-4 text-center">No plan data available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Churn Risk Tab */}
        <TabsContent value="churn" className="space-y-6">
          {/* Risk Summary */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-3xl font-bold">{churn?.total_at_risk || 0}</p>
                <p className="text-sm text-muted-foreground">Total At Risk</p>
              </CardContent>
            </Card>
            <Card className="border-red-200">
              <CardContent className="pt-6 text-center">
                <p className="text-3xl font-bold text-red-600">{churn?.high_risk || 0}</p>
                <p className="text-sm text-muted-foreground">High Risk</p>
              </CardContent>
            </Card>
            <Card className="border-yellow-200">
              <CardContent className="pt-6 text-center">
                <p className="text-3xl font-bold text-yellow-600">{churn?.medium_risk || 0}</p>
                <p className="text-sm text-muted-foreground">Medium Risk</p>
              </CardContent>
            </Card>
            <Card className="border-green-200">
              <CardContent className="pt-6 text-center">
                <p className="text-3xl font-bold text-green-600">{churn?.low_risk || 0}</p>
                <p className="text-sm text-muted-foreground">Low Risk</p>
              </CardContent>
            </Card>
          </div>

          {/* Churn Risk Table */}
          {churn?.customers && churn.customers.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">At-Risk Customers</CardTitle>
                <CardDescription>Customers likely to not renew, sorted by risk score</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Customer</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Contract</TableHead>
                      <TableHead>Expiry</TableHead>
                      <TableHead>Usage</TableHead>
                      <TableHead>Risk</TableHead>
                      <TableHead>Factors</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {churn.customers.map((customer) => (
                      <TableRow key={customer.contract_id}>
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{customer.customer_name}</p>
                            <p className="text-xs text-muted-foreground">{customer.customer_phone}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">{customer.product_name}</TableCell>
                        <TableCell>
                          <code className="text-xs">{customer.contract_number}</code>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-sm">
                              {new Date(customer.end_date).toLocaleDateString('en-IN', {
                                day: 'numeric',
                                month: 'short',
                              })}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {customer.days_remaining}d left
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <p className="text-sm">
                            {customer.services_used}/{customer.total_services}
                          </p>
                          <Progress
                            value={(customer.services_used / customer.total_services) * 100}
                            className="h-1.5 mt-1"
                          />
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              customer.risk_level === 'HIGH'
                                ? 'bg-red-100 text-red-800'
                                : customer.risk_level === 'MEDIUM'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-green-100 text-green-800'
                            }
                          >
                            {customer.risk_score}% {customer.risk_level}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-0.5">
                            {customer.risk_factors.slice(0, 2).map((factor, i) => (
                              <p key={i} className="text-[10px] text-muted-foreground">
                                {factor}
                              </p>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="outline" asChild>
                            <a href={`tel:${customer.customer_phone}`}>
                              <Phone className="h-3.5 w-3.5 mr-1" />
                              Call
                            </a>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle className="h-16 w-16 mx-auto text-green-500 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Churn Risk Detected</h3>
                <p className="text-muted-foreground">
                  All active contracts are in good standing. Great job on customer retention!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
