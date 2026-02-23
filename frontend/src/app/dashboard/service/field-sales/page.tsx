'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Users,
  DollarSign,
  AlertTriangle,
  Clock,
  Phone,
  Loader2,
  Search,
  CreditCard,
  UserCheck,
  Store,
  Wrench,
  ChevronRight,
  Filter,
  TrendingUp,
  ArrowRight,
  CheckCircle,
  QrCode,
  IndianRupee,
  Calendar,
  MapPin,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { amcApi, installationsApi, customersApi } from '@/lib/api';

// Types
interface WarrantyExpiringDevice {
  id: string;
  serial_number: string;
  product_name: string;
  customer_name: string;
  customer_phone: string;
  customer_id: string;
  product_id: string;
  warranty_end_date: string;
  days_until_expiry: number;
  installation_date: string;
  address?: string;
  amc_status: string;
}

interface CommissionEntry {
  contract_number: string;
  customer_name: string;
  plan_name: string;
  amount: number;
  commission_rate: number;
  commission_amount: number;
  sold_by_type: string;
  sold_by_name?: string;
  sales_channel: string;
  created_at: string;
  commission_paid: boolean;
}

export default function FieldSalesPage() {
  const [activeTab, setActiveTab] = useState('leads');
  const [loading, setLoading] = useState(true);
  const [expiringDevices, setExpiringDevices] = useState<WarrantyExpiringDevice[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [expiryFilter, setExpiryFilter] = useState('90');
  const [channelFilter, setChannelFilter] = useState('all');

  // Quick sell dialog
  const [showSellDialog, setShowSellDialog] = useState(false);
  const [selectedLead, setSelectedLead] = useState<WarrantyExpiringDevice | null>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [selectedTenure, setSelectedTenure] = useState('12');
  const [soldByType, setSoldByType] = useState('TECHNICIAN');
  const [paymentMode, setPaymentMode] = useState('UPI');
  const [paymentRef, setPaymentRef] = useState('');
  const [selling, setSelling] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, plansData, contractsData] = await Promise.all([
        amcApi.getContractStats().catch(() => ({})),
        amcApi.listPlans({ is_active: true }).catch(() => ({ items: [] })),
        amcApi.listContracts({ page: 1, size: 50 }).catch(() => ({ items: [] })),
      ]);

      setStats(statsData);
      setPlans(plansData.items || []);
      setContracts(contractsData.items || []);

      // Fetch warranty expiring devices
      try {
        const installData = await amcApi.getWarrantyExpiring({ days: parseInt(expiryFilter) });
        const items = installData.items || [];
        const transformed: WarrantyExpiringDevice[] = items.map((inst: any) => {
          const warrantyEnd = new Date(inst.warranty_end_date || inst.warranty_expiry_date || '');
          const now = new Date();
          const daysUntil = Math.floor((warrantyEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
          return {
            id: inst.id,
            serial_number: inst.serial_number,
            product_name: inst.product_name || inst.product?.name || 'Water Purifier',
            customer_name: inst.customer_name || inst.customer?.name || 'Unknown',
            customer_phone: inst.customer_phone || inst.customer?.phone || '',
            customer_id: inst.customer_id,
            product_id: inst.product_id,
            warranty_end_date: inst.warranty_end_date || inst.warranty_expiry_date,
            days_until_expiry: daysUntil,
            installation_date: inst.installation_date || inst.created_at,
            address: inst.address || inst.installation_address,
            amc_status: inst.amc_contract?.status || 'none',
          };
        });
        // Filter to only show devices without active AMC
        setExpiringDevices(transformed.filter((d) => d.amc_status === 'none' || d.amc_status === 'EXPIRED'));
      } catch {
        setExpiringDevices([]);
      }
    } catch (error) {
      console.error('Failed to load field sales data:', error);
    } finally {
      setLoading(false);
    }
  }, [expiryFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleQuickSell = (device: WarrantyExpiringDevice) => {
    setSelectedLead(device);
    setSelectedPlanId('');
    setSelectedTenure('12');
    setPaymentRef('');
    setShowSellDialog(true);
  };

  const handleCreateSale = async () => {
    if (!selectedLead || !selectedPlanId) {
      toast.error('Please select a plan');
      return;
    }

    setSelling(true);
    try {
      await amcApi.createContract({
        customer_id: selectedLead.customer_id,
        product_id: selectedLead.product_id,
        serial_number: selectedLead.serial_number,
        plan_id: selectedPlanId,
        start_date: new Date().toISOString().split('T')[0],
        duration_months: parseInt(selectedTenure),
        base_price: plans.find((p: any) => p.id === selectedPlanId)?.base_price || 0,
        sales_channel: soldByType === 'DEALER' ? 'DEALER' : 'OFFLINE',
        sold_by_type: soldByType,
      });

      toast.success('AMC contract created successfully!');
      setShowSellDialog(false);
      setSelectedLead(null);
      fetchData();
    } catch (error: any) {
      console.error('Failed to create sale:', error);
      toast.error(error?.response?.data?.detail || 'Failed to create AMC contract');
    } finally {
      setSelling(false);
    }
  };

  // Filter leads by search term
  const filteredLeads = expiringDevices.filter((d) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      d.customer_name.toLowerCase().includes(term) ||
      d.serial_number.toLowerCase().includes(term) ||
      d.customer_phone.includes(term) ||
      d.product_name.toLowerCase().includes(term)
    );
  });

  // Filter contracts by channel
  const filteredContracts = channelFilter === 'all'
    ? contracts
    : contracts.filter((c: any) => c.sales_channel === channelFilter);

  // Commission data from contracts
  const commissionContracts = contracts.filter((c: any) => c.commission_amount > 0);
  const totalCommission = commissionContracts.reduce((sum: number, c: any) => sum + (c.commission_amount || 0), 0);
  const pendingCommission = commissionContracts.filter((c: any) => !c.commission_paid).reduce((sum: number, c: any) => sum + (c.commission_amount || 0), 0);

  const getUrgencyBadge = (days: number) => {
    if (days < 0) return <Badge className="bg-red-100 text-red-800">Expired {Math.abs(days)}d ago</Badge>;
    if (days <= 7) return <Badge className="bg-red-100 text-red-800">Expires in {days}d</Badge>;
    if (days <= 30) return <Badge className="bg-orange-100 text-orange-800">{days} days left</Badge>;
    if (days <= 60) return <Badge className="bg-yellow-100 text-yellow-800">{days} days left</Badge>;
    return <Badge className="bg-blue-100 text-blue-800">{days} days left</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Field Sales - AMC</h1>
        <p className="text-muted-foreground">
          Sell AMC contracts to customers with expiring warranties. Track commissions and conversions.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Warranty Expiring</p>
                <p className="text-2xl font-bold">{expiringDevices.length}</p>
                <p className="text-xs text-muted-foreground">Next {expiryFilter} days</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Contracts</p>
                <p className="text-2xl font-bold">{stats?.active || 0}</p>
                <p className="text-xs text-muted-foreground">Total active AMCs</p>
              </div>
              <Shield className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Commission</p>
                <p className="text-2xl font-bold">
                  <span className="text-lg">Rs </span>
                  {totalCommission.toLocaleString('en-IN')}
                </p>
                <p className="text-xs text-muted-foreground">All time</p>
              </div>
              <IndianRupee className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending Payout</p>
                <p className="text-2xl font-bold text-orange-600">
                  <span className="text-lg">Rs </span>
                  {pendingCommission.toLocaleString('en-IN')}
                </p>
                <p className="text-xs text-muted-foreground">Unpaid commission</p>
              </div>
              <DollarSign className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="leads">
            <AlertTriangle className="h-4 w-4 mr-2" />
            AMC Leads ({expiringDevices.length})
          </TabsTrigger>
          <TabsTrigger value="sales">
            <CreditCard className="h-4 w-4 mr-2" />
            Recent Sales
          </TabsTrigger>
          <TabsTrigger value="commission">
            <IndianRupee className="h-4 w-4 mr-2" />
            Commission
          </TabsTrigger>
        </TabsList>

        {/* AMC Leads Tab */}
        <TabsContent value="leads" className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by customer name, serial number, or phone..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={expiryFilter} onValueChange={setExpiryFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Expiry window" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Next 7 days</SelectItem>
                <SelectItem value="15">Next 15 days</SelectItem>
                <SelectItem value="30">Next 30 days</SelectItem>
                <SelectItem value="60">Next 60 days</SelectItem>
                <SelectItem value="90">Next 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredLeads.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle className="h-16 w-16 mx-auto text-green-500 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Warranty Expiring Devices</h3>
                <p className="text-muted-foreground">
                  No devices have warranties expiring in the next {expiryFilter} days without AMC coverage.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Device</TableHead>
                    <TableHead>Serial No.</TableHead>
                    <TableHead>Warranty Expiry</TableHead>
                    <TableHead>Urgency</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLeads.map((device) => (
                    <TableRow key={device.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{device.customer_name}</p>
                          <p className="text-xs text-muted-foreground flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {device.customer_phone}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm">{device.product_name}</p>
                      </TableCell>
                      <TableCell>
                        <code className="text-xs">{device.serial_number}</code>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm">
                          {new Date(device.warranty_end_date).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </p>
                      </TableCell>
                      <TableCell>{getUrgencyBadge(device.days_until_expiry)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            asChild
                          >
                            <a href={`tel:${device.customer_phone}`}>
                              <Phone className="h-3.5 w-3.5 mr-1" />
                              Call
                            </a>
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleQuickSell(device)}
                          >
                            <Shield className="h-3.5 w-3.5 mr-1" />
                            Sell AMC
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* Recent Sales Tab */}
        <TabsContent value="sales" className="space-y-4">
          <div className="flex items-center gap-4">
            <Select value={channelFilter} onValueChange={setChannelFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sales channel" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Channels</SelectItem>
                <SelectItem value="ONLINE">Online</SelectItem>
                <SelectItem value="OFFLINE">Offline</SelectItem>
                <SelectItem value="DEALER">Dealer</SelectItem>
                <SelectItem value="TECHNICIAN">Technician</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {filteredContracts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CreditCard className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Sales Yet</h3>
                <p className="text-muted-foreground">
                  AMC contract sales will appear here.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract #</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Channel</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredContracts.slice(0, 25).map((contract: any) => (
                    <TableRow key={contract.id}>
                      <TableCell className="font-mono text-sm">{contract.contract_number}</TableCell>
                      <TableCell>
                        <p className="font-medium">{contract.customer?.name || '-'}</p>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{contract.plan_name || contract.amc_type}</span>
                          {contract.contract_type && (
                            <Badge variant="outline" className="text-[10px]">
                              {contract.contract_type === 'COMPREHENSIVE' ? 'Comp.' : 'Non-Comp.'}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        Rs {(contract.total_amount || 0).toLocaleString('en-IN')}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-xs">
                          {contract.sales_channel === 'ONLINE' && 'Online'}
                          {contract.sales_channel === 'OFFLINE' && 'Offline'}
                          {contract.sales_channel === 'DEALER' && 'Dealer'}
                          {contract.sales_channel === 'TECHNICIAN' && 'Technician'}
                          {!contract.sales_channel && 'N/A'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={
                          contract.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                          contract.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }>
                          {contract.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(contract.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* Commission Tab */}
        <TabsContent value="commission" className="space-y-4">
          {/* Commission Summary Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Wrench className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Technician Commission</p>
                    <p className="text-lg font-bold">
                      Rs {commissionContracts
                        .filter((c: any) => c.sold_by_type === 'TECHNICIAN')
                        .reduce((s: number, c: any) => s + (c.commission_amount || 0), 0)
                        .toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-muted-foreground">@ 10% rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Store className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Dealer Commission</p>
                    <p className="text-lg font-bold">
                      Rs {commissionContracts
                        .filter((c: any) => c.sold_by_type === 'DEALER')
                        .reduce((s: number, c: any) => s + (c.commission_amount || 0), 0)
                        .toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-muted-foreground">@ 15% rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <UserCheck className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Staff Commission</p>
                    <p className="text-lg font-bold">
                      Rs {commissionContracts
                        .filter((c: any) => c.sold_by_type === 'USER')
                        .reduce((s: number, c: any) => s + (c.commission_amount || 0), 0)
                        .toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-muted-foreground">@ 5% rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Commission entries */}
          {commissionContracts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <IndianRupee className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Commission Data</h3>
                <p className="text-muted-foreground">
                  Commission entries will appear here when AMC contracts are sold through field/dealer channels.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract</TableHead>
                    <TableHead>Sold By</TableHead>
                    <TableHead>Channel</TableHead>
                    <TableHead>Contract Amount</TableHead>
                    <TableHead>Commission Rate</TableHead>
                    <TableHead>Commission</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {commissionContracts.map((contract: any) => (
                    <TableRow key={contract.id}>
                      <TableCell className="font-mono text-sm">{contract.contract_number}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {contract.sold_by_type || '-'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{contract.sales_channel || '-'}</TableCell>
                      <TableCell>Rs {(contract.total_amount || 0).toLocaleString('en-IN')}</TableCell>
                      <TableCell>{contract.commission_rate || 0}%</TableCell>
                      <TableCell className="font-medium text-green-600">
                        Rs {(contract.commission_amount || 0).toLocaleString('en-IN')}
                      </TableCell>
                      <TableCell>
                        {contract.commission_paid ? (
                          <Badge className="bg-green-100 text-green-800">Paid</Badge>
                        ) : (
                          <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Quick Sell Dialog */}
      <Dialog open={showSellDialog} onOpenChange={setShowSellDialog}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>Quick AMC Sale</DialogTitle>
            <DialogDescription>
              Create AMC contract for {selectedLead?.customer_name}
            </DialogDescription>
          </DialogHeader>
          {selectedLead && (
            <div className="space-y-4 py-4">
              {/* Customer Info */}
              <div className="bg-muted/50 rounded-lg p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{selectedLead.customer_name}</span>
                  <a href={`tel:${selectedLead.customer_phone}`} className="text-primary text-sm flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    {selectedLead.customer_phone}
                  </a>
                </div>
                <div className="text-xs text-muted-foreground">
                  {selectedLead.product_name} | S/N: {selectedLead.serial_number}
                </div>
                <div className="text-xs text-red-600">
                  Warranty expires: {new Date(selectedLead.warranty_end_date).toLocaleDateString('en-IN')}
                  ({selectedLead.days_until_expiry > 0 ? `${selectedLead.days_until_expiry} days left` : `expired ${Math.abs(selectedLead.days_until_expiry)} days ago`})
                </div>
              </div>

              {/* Plan Selection */}
              <div>
                <Label>Select AMC Plan *</Label>
                <Select value={selectedPlanId} onValueChange={setSelectedPlanId}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue placeholder="Choose a plan" />
                  </SelectTrigger>
                  <SelectContent>
                    {plans.map((plan: any) => (
                      <SelectItem key={plan.id} value={plan.id}>
                        <div className="flex items-center gap-2">
                          <span>{plan.name}</span>
                          <span className="text-muted-foreground">
                            - Rs {plan.base_price?.toLocaleString('en-IN')}
                          </span>
                          {plan.contract_type && (
                            <Badge variant="outline" className="text-[10px]">
                              {plan.contract_type === 'COMPREHENSIVE' ? 'Comp.' : 'Non-Comp.'}
                            </Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Tenure */}
              <div>
                <Label>Duration</Label>
                <Select value={selectedTenure} onValueChange={setSelectedTenure}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="12">1 Year</SelectItem>
                    <SelectItem value="24">2 Years (Save 10%)</SelectItem>
                    <SelectItem value="36">3 Years (Save 15%)</SelectItem>
                    <SelectItem value="48">4 Years (Save 20%)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Sold By */}
              <div>
                <Label>Sold By</Label>
                <Select value={soldByType} onValueChange={setSoldByType}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TECHNICIAN">Technician (10% commission)</SelectItem>
                    <SelectItem value="DEALER">Dealer (15% commission)</SelectItem>
                    <SelectItem value="USER">Staff (5% commission)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Payment */}
              <div>
                <Label>Payment Mode</Label>
                <Select value={paymentMode} onValueChange={setPaymentMode}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="UPI">UPI / QR Code</SelectItem>
                    <SelectItem value="CASH">Cash</SelectItem>
                    <SelectItem value="CARD">Card</SelectItem>
                    <SelectItem value="BANK_TRANSFER">Bank Transfer</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Payment Reference (Optional)</Label>
                <Input
                  placeholder="Transaction ID or reference"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  className="mt-1.5"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateSale} disabled={selling || !selectedPlanId}>
              {selling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4 mr-2" />
                  Create AMC
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
