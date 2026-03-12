'use client';

import { useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User, Phone, Mail, MapPin, Calendar, ShoppingBag, Wrench, Shield, Package, Star, AlertTriangle,
  CreditCard, Clock, CheckCircle, ArrowLeft, Edit, MoreHorizontal, FileText, Heart, Activity,
  MessageSquare, IndianRupee, TrendingUp, Home, Building2, Truck, Loader2, Plus, Trash2
} from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDate, formatCurrency } from '@/lib/utils';
import { customersApi } from '@/lib/api';

// Types matching backend Customer360Response
interface CustomerAddress {
  id: string;
  address_type?: string;
  contact_name?: string;
  contact_phone?: string;
  address_line1?: string;
  address_line2?: string;
  landmark?: string;
  city?: string;
  state?: string;
  pincode?: string;
  is_default: boolean;
}

interface CustomerProfile {
  id: string;
  customer_code?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  name?: string; // computed field from backend
  email?: string;
  phone?: string;
  alternate_phone?: string;
  customer_type?: string;
  source?: string;
  company_name?: string;
  gst_number?: string;
  date_of_birth?: string;
  anniversary_date?: string;
  is_active: boolean;
  is_verified: boolean;
  addresses: CustomerAddress[];
  created_at?: string;
}

interface Customer360Stats {
  total_orders: number;
  total_order_value: number;
  delivered_orders: number;
  pending_orders: number;
  total_installations: number;
  completed_installations: number;
  total_service_requests: number;
  open_service_requests: number;
  total_calls: number;
  active_amc_contracts: number;
  average_rating?: number;
  customer_since_days: number;
}

interface Customer360Order {
  id: string;
  order_number: string;
  status: string;
  total_amount: number;
  payment_status?: string;
  items_count: number;
  created_at?: string;
}

interface Customer360ServiceRequest {
  id: string;
  ticket_number: string;
  service_type: string;
  status: string;
  priority?: string;
  title?: string;
  franchisee_name?: string;
  technician_name?: string;
  scheduled_date?: string;
  completed_at?: string;
  customer_rating?: number;
  created_at?: string;
}

interface Customer360AMC {
  id: string;
  contract_number: string;
  plan_name: string;
  status: string;
  start_date: string;
  end_date: string;
  total_services: number;
  services_used: number;
  services_remaining: number;
  next_service_due?: string;
}

interface Customer360Call {
  id: string;
  call_id?: string;
  call_type: string;
  category: string;
  status: string;
  outcome?: string;
  duration_seconds?: number;
  agent_name?: string;
  call_start_time?: string;
  sentiment?: string;
}

interface Customer360Payment {
  id: string;
  order_number?: string;
  amount: number;
  method?: string;
  status: string;
  transaction_id?: string;
  gateway?: string;
  completed_at?: string;
  created_at?: string;
}

interface Customer360Installation {
  id: string;
  installation_number: string;
  status: string;
  product_name?: string;
  installation_pincode?: string;
  franchisee_name?: string;
  scheduled_date?: string;
  completed_at?: string;
  customer_rating?: number;
  warranty_end_date?: string;
  created_at?: string;
}

interface Customer360Timeline {
  event_type: string;
  event_id: string;
  title: string;
  description?: string;
  status: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

interface Customer360Response {
  customer: CustomerProfile;
  stats: Customer360Stats;
  timeline: Customer360Timeline[];
  orders: Customer360Order[];
  recent_order_history: { from_status?: string; to_status: string; notes?: string; changed_by?: string; created_at?: string }[];
  shipments: { id: string; shipment_number: string; order_number?: string; status: string; awb_number?: string; transporter_name?: string; delivered_to?: string; delivered_at?: string; created_at?: string }[];
  recent_shipment_tracking: { status: string; location?: string; city?: string; remarks?: string; event_time?: string }[];
  installations: Customer360Installation[];
  service_requests: Customer360ServiceRequest[];
  recent_service_history: { from_status?: string; to_status: string; notes?: string; changed_by?: string; created_at?: string }[];
  calls: Customer360Call[];
  payments: Customer360Payment[];
  amc_contracts: Customer360AMC[];
  lead?: { id: string; lead_number: string; status: string; source: string; converted_at?: string };
  lead_activities: { activity_type: string; subject: string; outcome?: string; old_status?: string; new_status?: string; activity_date: string }[];
}

const statusColors: Record<string, string> = {
  DELIVERED: 'bg-green-100 text-green-800',
  PROCESSING: 'bg-blue-100 text-blue-800',
  SHIPPED: 'bg-purple-100 text-purple-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  CANCELLED: 'bg-red-100 text-red-800',
  COMPLETED: 'bg-green-100 text-green-800',
  IN_PROGRESS: 'bg-blue-100 text-blue-800',
  ASSIGNED: 'bg-purple-100 text-purple-800',
  ACTIVE: 'bg-green-100 text-green-800',
  EXPIRED: 'bg-red-100 text-red-800',
  NONE: 'bg-gray-100 text-gray-800',
  SUCCESS: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  PAID: 'bg-green-100 text-green-800',
};

interface EditFormData {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  customer_type: 'INDIVIDUAL' | 'BUSINESS' | 'DEALER' | 'DISTRIBUTOR';
  source: string;
  alternate_phone: string;
  company_name: string;
  gst_number: string;
  date_of_birth: string;
  anniversary_date: string;
  notes: string;
  is_active: boolean;
}

interface AddressFormData {
  id?: string;
  address_type: string;
  contact_name: string;
  contact_phone: string;
  address_line1: string;
  address_line2: string;
  landmark: string;
  city: string;
  state: string;
  pincode: string;
  is_default: boolean;
}

const emptyAddress: AddressFormData = {
  address_type: 'HOME',
  contact_name: '',
  contact_phone: '',
  address_line1: '',
  address_line2: '',
  landmark: '',
  city: '',
  state: '',
  pincode: '',
  is_default: false,
};

const addressTypes = [
  { value: 'HOME', label: 'Home' },
  { value: 'OFFICE', label: 'Office' },
  { value: 'BILLING', label: 'Billing' },
  { value: 'SHIPPING', label: 'Shipping' },
  { value: 'OTHER', label: 'Other' },
];

// Map legacy/variant customer_type values to standard enum
const normalizeCustomerType = (val?: string): EditFormData['customer_type'] => {
  if (!val) return 'INDIVIDUAL';
  const upper = val.toUpperCase();
  if (upper === 'RETAIL' || upper === 'INDIVIDUAL') return 'INDIVIDUAL';
  if (upper === 'BUSINESS' || upper === 'B2B') return 'BUSINESS';
  if (upper === 'DEALER') return 'DEALER';
  if (upper === 'DISTRIBUTOR') return 'DISTRIBUTOR';
  return 'INDIVIDUAL';
};

const customerTypes = [
  { value: 'INDIVIDUAL', label: 'Individual' },
  { value: 'BUSINESS', label: 'Business' },
  { value: 'DEALER', label: 'Dealer' },
  { value: 'DISTRIBUTOR', label: 'Distributor' },
];

const customerSources = [
  { value: 'WEBSITE', label: 'Website' },
  { value: 'WALK_IN', label: 'Walk-in' },
  { value: 'REFERRAL', label: 'Referral' },
  { value: 'DEALER', label: 'Dealer' },
  { value: 'CAMPAIGN', label: 'Campaign' },
  { value: 'SOCIAL_MEDIA', label: 'Social Media' },
  { value: 'OTHER', label: 'Other' },
];

export default function Customer360Page() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get('tab') || 'overview';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editForm, setEditForm] = useState<EditFormData>({
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    customer_type: 'INDIVIDUAL',
    source: '',
    alternate_phone: '',
    company_name: '',
    gst_number: '',
    date_of_birth: '',
    anniversary_date: '',
    notes: '',
    is_active: true,
  });
  const [editAddresses, setEditAddresses] = useState<AddressFormData[]>([]);
  const [savingAddresses, setSavingAddresses] = useState(false);

  const { data: response, isLoading, error } = useQuery<Customer360Response>({
    queryKey: ['customer-360', params.id],
    queryFn: () => customersApi.get360View(params.id as string),
  });

  const updateMutation = useMutation({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    mutationFn: (data: Record<string, unknown>) => customersApi.update(params.id as string, data as any),
    onSuccess: () => {
      toast.success('Customer updated successfully');
      queryClient.invalidateQueries({ queryKey: ['customer-360', params.id] });
      setEditDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update customer');
    },
  });

  const handleEditOpen = () => {
    if (response?.customer) {
      const c = response.customer;
      const fullName = c.name || c.full_name || `${c.first_name || ''} ${c.last_name || ''}`.trim() || '';
      const nameParts = fullName.split(' ');
      setEditForm({
        first_name: c.first_name || nameParts[0] || '',
        last_name: c.last_name || nameParts.slice(1).join(' ') || '',
        phone: c.phone || '',
        email: c.email || '',
        customer_type: normalizeCustomerType(c.customer_type),
        source: c.source || '',
        alternate_phone: c.alternate_phone || '',
        company_name: c.company_name || '',
        gst_number: c.gst_number || '',
        date_of_birth: c.date_of_birth || '',
        anniversary_date: c.anniversary_date || '',
        notes: '',
        is_active: c.is_active,
      });
      // Load addresses into editable state
      setEditAddresses(
        (c.addresses ?? []).map((a) => ({
          id: a.id,
          address_type: a.address_type || 'HOME',
          contact_name: a.contact_name || '',
          contact_phone: a.contact_phone || '',
          address_line1: a.address_line1 || '',
          address_line2: a.address_line2 || '',
          landmark: a.landmark || '',
          city: a.city || '',
          state: a.state || '',
          pincode: a.pincode || '',
          is_default: a.is_default,
        }))
      );
      setEditDialogOpen(true);
    }
  };

  const handleAddAddress = () => {
    setEditAddresses([...editAddresses, { ...emptyAddress }]);
  };

  const handleRemoveAddress = (index: number) => {
    setEditAddresses(editAddresses.filter((_, i) => i !== index));
  };

  const handleAddressChange = (index: number, field: keyof AddressFormData, value: string | boolean) => {
    const updated = [...editAddresses];
    updated[index] = { ...updated[index], [field]: value };
    setEditAddresses(updated);
  };

  const handleEditSubmit = async () => {
    if (!editForm.first_name.trim()) {
      toast.error('First name is required');
      return;
    }
    if (!editForm.phone.trim()) {
      toast.error('Phone number is required');
      return;
    }
    // Validate addresses
    for (const addr of editAddresses) {
      if (!addr.address_line1.trim() || !addr.city.trim() || !addr.state.trim() || !addr.pincode.trim()) {
        toast.error('Address line 1, city, state and pincode are required for all addresses');
        return;
      }
    }

    // 1. Save customer profile
    const payload: Record<string, unknown> = {
      first_name: editForm.first_name.trim(),
      last_name: editForm.last_name.trim() || undefined,
      phone: editForm.phone.trim(),
      email: editForm.email.trim() || undefined,
      customer_type: editForm.customer_type,
      alternate_phone: editForm.alternate_phone.trim() || undefined,
      company_name: editForm.company_name.trim() || undefined,
      gstin: editForm.gst_number.trim() || undefined,
      notes: editForm.notes.trim() || undefined,
      is_active: editForm.is_active,
    };
    if (editForm.source) payload.source = editForm.source;
    if (editForm.date_of_birth) payload.date_of_birth = editForm.date_of_birth;
    if (editForm.anniversary_date) payload.anniversary_date = editForm.anniversary_date;

    // 2. Save addresses
    setSavingAddresses(true);
    try {
      const customerId = params.id as string;
      const originalAddresses = response?.customer?.addresses ?? [];
      const originalIds = new Set(originalAddresses.map(a => a.id));
      const currentEditIds = new Set(editAddresses.filter(a => a.id).map(a => a.id));

      // Delete removed addresses (existed originally but no longer in edit list)
      for (const orig of originalAddresses) {
        if (!currentEditIds.has(orig.id)) {
          try { await customersApi.deleteAddress(customerId, orig.id); } catch { /* ignore */ }
        }
      }
      // Update existing addresses (have an id that matches an original)
      for (const addr of editAddresses) {
        if (addr.id && originalIds.has(addr.id)) {
          const { id: addrId, ...addrData } = addr;
          try { await customersApi.updateAddress(customerId, addrId!, addrData); } catch { /* ignore */ }
        }
      }
      // Create only truly new addresses (no id at all)
      for (const addr of editAddresses) {
        if (!addr.id) {
          const { id: _id, ...addrData } = addr;
          await customersApi.addAddress(customerId, {
            address_type: addrData.address_type,
            contact_name: addrData.contact_name || undefined,
            contact_phone: addrData.contact_phone || undefined,
            address_line1: addrData.address_line1,
            address_line2: addrData.address_line2 || undefined,
            landmark: addrData.landmark || undefined,
            city: addrData.city,
            state: addrData.state,
            pincode: addrData.pincode,
            is_default: addrData.is_default,
          });
        }
      }
    } catch (err) {
      toast.error((err as Error).message || 'Failed to save addresses');
      setSavingAddresses(false);
      return;
    }
    setSavingAddresses(false);

    // 3. Save profile
    updateMutation.mutate(payload);
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-96">Loading...</div>;
  }

  if (error || !response) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <p className="text-muted-foreground">Customer not found or failed to load</p>
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />Go Back
        </Button>
      </div>
    );
  }

  const customer = response.customer;
  const stats = response.stats;
  const customerName = customer.name || customer.full_name || `${customer.first_name || ''} ${customer.last_name || ''}`.trim() || 'Unknown';
  const initials = customerName?.split(' ')?.map(n => n?.[0] ?? '')?.join('')?.toUpperCase() || 'NA';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-lg bg-primary text-primary-foreground">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">{customerName}</h1>
              <Badge className={customer.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                {customer.is_active ? 'Active' : 'Inactive'}
              </Badge>
              <Badge variant="outline">{customer.customer_type || 'INDIVIDUAL'}</Badge>
              {customer.customer_code && <Badge variant="secondary">{customer.customer_code}</Badge>}
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
              <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{customer.phone || 'N/A'}</span>
              {customer.email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{customer.email}</span>}
              <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />Customer since {formatDate(customer.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleEditOpen}><Edit className="mr-2 h-4 w-4" />Edit</Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem><FileText className="mr-2 h-4 w-4" />Generate Report</DropdownMenuItem>
              <DropdownMenuItem><Mail className="mr-2 h-4 w-4" />Send Email</DropdownMenuItem>
              <DropdownMenuItem><MessageSquare className="mr-2 h-4 w-4" />Send SMS</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <IndianRupee className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total Order Value</span>
            </div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(stats.total_order_value)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <ShoppingBag className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total Orders</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.total_orders}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Installations</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.total_installations}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Active AMC</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.active_amc_contracts}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-500" />
              <span className="text-sm text-muted-foreground">Avg Rating</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.average_rating ? `${stats.average_rating}/5` : 'N/A'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Wrench className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Service Requests</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.total_service_requests}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Timeline ({response.timeline?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="orders">Orders ({response.orders?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="installations">Installations ({response.installations?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="services">Services ({response.service_requests?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="amc">AMC ({response.amc_contracts?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="calls">Calls ({response.calls?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="payments">Payments ({response.payments?.length ?? 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-3">
            {/* Profile Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Profile Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Phone</span>
                  <span className="font-medium">{customer.phone || '-'}</span>
                </div>
                {customer.alternate_phone && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Alt Phone</span>
                    <span className="font-medium">{customer.alternate_phone}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Email</span>
                  <span className="font-medium">{customer.email || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Customer Type</span>
                  <Badge variant="outline">{customer.customer_type || 'INDIVIDUAL'}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Source</span>
                  <span className="font-medium">{customer.source || '-'}</span>
                </div>
                {customer.date_of_birth && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Birthday</span>
                    <span className="font-medium">{formatDate(customer.date_of_birth)}</span>
                  </div>
                )}
                {customer.anniversary_date && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Anniversary</span>
                    <span className="font-medium">{formatDate(customer.anniversary_date)}</span>
                  </div>
                )}
                {customer.gst_number && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">GSTIN</span>
                    <span className="font-mono text-sm">{customer.gst_number}</span>
                  </div>
                )}
                {customer.company_name && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Company</span>
                    <span className="font-medium">{customer.company_name}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Addresses */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Addresses</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {(customer.addresses ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">No addresses on file</p>
                ) : (
                  (customer.addresses ?? []).map((addr) => (
                    <div key={addr.id} className="space-y-1">
                      <div className="flex items-center gap-2">
                        {addr.address_type === 'HOME' ? <Home className="h-4 w-4" /> : <Building2 className="h-4 w-4" />}
                        <span className="font-medium">{addr.address_type || 'Address'}</span>
                        {addr.is_default && <Badge variant="outline" className="text-xs">Default</Badge>}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {addr.address_line1}
                        {addr.address_line2 && `, ${addr.address_line2}`}
                        {addr.landmark && ` (${addr.landmark})`}
                        <br />{addr.city}, {addr.state} - {addr.pincode}
                      </p>
                      {addr.contact_name && (
                        <p className="text-xs text-muted-foreground">
                          Contact: {addr.contact_name} {addr.contact_phone && `- ${addr.contact_phone}`}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Activity Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Customer For</span>
                  <span className="font-medium">{stats.customer_since_days} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Delivered Orders</span>
                  <span className="font-medium">{stats.delivered_orders} / {stats.total_orders}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Pending Orders</span>
                  <span className="font-medium">{stats.pending_orders}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Spent</span>
                  <span className="font-medium">{formatCurrency(stats.total_order_value)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Avg Order Value</span>
                  <span className="font-medium">{formatCurrency(stats.total_order_value / (stats.total_orders || 1))}</span>
                </div>
                <Separator />
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Service Satisfaction</span>
                    <span>{stats.average_rating ? `${(stats.average_rating * 20).toFixed(0)}%` : 'N/A'}</span>
                  </div>
                  <Progress value={stats.average_rating ? stats.average_rating * 20 : 0} />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity from Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(response.timeline ?? []).slice(0, 5).map((event, index) => (
                  <div key={`${event.event_id}-${index}`} className="flex items-start gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                      {event.event_type === 'ORDER' && <ShoppingBag className="h-4 w-4" />}
                      {event.event_type === 'SHIPMENT' && <Truck className="h-4 w-4" />}
                      {event.event_type === 'INSTALLATION' && <Package className="h-4 w-4" />}
                      {event.event_type === 'SERVICE' && <Wrench className="h-4 w-4" />}
                      {event.event_type === 'CALL' && <Phone className="h-4 w-4" />}
                      {event.event_type === 'PAYMENT' && <CreditCard className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{event.title}</span>
                        <span className="text-xs text-muted-foreground">{formatDate(event.timestamp)}</span>
                      </div>
                      {event.description && <p className="text-sm text-muted-foreground">{event.description}</p>}
                      <Badge className={statusColors[event.status] || 'bg-gray-100 text-gray-800'} variant="secondary">
                        {event.status?.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                  </div>
                ))}
                {(response.timeline ?? []).length === 0 && (
                  <p className="text-sm text-muted-foreground">No recent activity</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Customer Journey Timeline</CardTitle>
              <CardDescription>Chronological view of all interactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(response.timeline ?? []).map((event, index) => (
                  <div key={`${event.event_id}-${index}`} className="flex items-start gap-4 p-4 border rounded-lg">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      {event.event_type === 'ORDER' && <ShoppingBag className="h-5 w-5" />}
                      {event.event_type === 'SHIPMENT' && <Truck className="h-5 w-5" />}
                      {event.event_type === 'INSTALLATION' && <Package className="h-5 w-5" />}
                      {event.event_type === 'SERVICE' && <Wrench className="h-5 w-5" />}
                      {event.event_type === 'CALL' && <Phone className="h-5 w-5" />}
                      {event.event_type === 'PAYMENT' && <CreditCard className="h-5 w-5" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{event.event_type}</Badge>
                          <span className="font-medium">{event.title}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">{formatDate(event.timestamp)}</span>
                      </div>
                      {event.description && <p className="mt-1 text-sm text-muted-foreground">{event.description}</p>}
                      <Badge className={statusColors[event.status] || 'bg-gray-100 text-gray-800'} variant="secondary">
                        {event.status?.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                  </div>
                ))}
                {(response.timeline ?? []).length === 0 && (
                  <p className="text-center text-muted-foreground py-8">No timeline events found</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="orders" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Order History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Items</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Payment</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(response.orders ?? []).map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-mono font-medium">{order.order_number}</TableCell>
                      <TableCell>{formatDate(order.created_at)}</TableCell>
                      <TableCell>{order.items_count} items</TableCell>
                      <TableCell className="font-medium">{formatCurrency(order.total_amount)}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[order.payment_status || 'PENDING'] || 'bg-gray-100 text-gray-800'}>
                          {order.payment_status || 'PENDING'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[order.status] || 'bg-gray-100 text-gray-800'}>
                          {order.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => router.push(`/dashboard/orders/${order.id}`)}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(response.orders ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No orders found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="installations" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Installations</CardTitle>
              <CardDescription>Products installed for this customer</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Installation #</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>Scheduled</TableHead>
                    <TableHead>Completed</TableHead>
                    <TableHead>Warranty Until</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Rating</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(response.installations ?? []).map((inst) => (
                    <TableRow key={inst.id}>
                      <TableCell className="font-mono font-medium">{inst.installation_number}</TableCell>
                      <TableCell>{inst.product_name || '-'}</TableCell>
                      <TableCell>{inst.scheduled_date ? formatDate(inst.scheduled_date) : '-'}</TableCell>
                      <TableCell>{inst.completed_at ? formatDate(inst.completed_at) : '-'}</TableCell>
                      <TableCell>
                        {inst.warranty_end_date ? (
                          <div className="text-sm">
                            <div>{formatDate(inst.warranty_end_date)}</div>
                            {new Date(inst.warranty_end_date) < new Date() && (
                              <Badge className="bg-red-100 text-red-800 text-xs">Expired</Badge>
                            )}
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[inst.status] || 'bg-gray-100 text-gray-800'}>
                          {inst.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {inst.customer_rating ? (
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                            <span>{inst.customer_rating}/5</span>
                          </div>
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  {(response.installations ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No installations found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Requests</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticket #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Technician</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Rating</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(response.service_requests ?? []).map((sr) => (
                    <TableRow key={sr.id}>
                      <TableCell className="font-mono font-medium">{sr.ticket_number}</TableCell>
                      <TableCell>{formatDate(sr.created_at)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{sr.service_type?.replace(/_/g, ' ')}</Badge>
                      </TableCell>
                      <TableCell>{sr.title || '-'}</TableCell>
                      <TableCell>{sr.technician_name || sr.franchisee_name || '-'}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[sr.status] || 'bg-gray-100 text-gray-800'}>
                          {sr.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {sr.customer_rating ? (
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                            <span>{sr.customer_rating}/5</span>
                          </div>
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  {(response.service_requests ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No service requests found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="amc" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>AMC Contracts</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract #</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Validity</TableHead>
                    <TableHead>Services Used</TableHead>
                    <TableHead>Next Service Due</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(response.amc_contracts ?? []).map((amc) => (
                    <TableRow key={amc.id}>
                      <TableCell className="font-mono font-medium">{amc.contract_number}</TableCell>
                      <TableCell>{amc.plan_name}</TableCell>
                      <TableCell>
                        <div>{formatDate(amc.start_date)}</div>
                        <div className="text-xs text-muted-foreground">to {formatDate(amc.end_date)}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={amc.total_services > 0 ? (amc.services_used / amc.total_services) * 100 : 0} className="w-16 h-2" />
                          <span className="text-sm">{amc.services_used}/{amc.total_services}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">{amc.services_remaining} remaining</div>
                      </TableCell>
                      <TableCell>{amc.next_service_due ? formatDate(amc.next_service_due) : '-'}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[amc.status] || 'bg-gray-100 text-gray-800'}>
                          {amc.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => router.push(`/dashboard/service/amc/${amc.id}`)}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(response.amc_contracts ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No AMC contracts found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calls" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Call History</CardTitle>
              <CardDescription>All calls with this customer</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Call ID</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Outcome</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(response.calls ?? []).map((call) => (
                    <TableRow key={call.id}>
                      <TableCell className="font-mono">{call.call_id || '-'}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{call.call_type?.replace(/_/g, ' ')}</Badge>
                      </TableCell>
                      <TableCell>{call.category?.replace(/_/g, ' ')}</TableCell>
                      <TableCell>
                        {call.duration_seconds ? (
                          <span>{Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s</span>
                        ) : '-'}
                      </TableCell>
                      <TableCell>{call.agent_name || '-'}</TableCell>
                      <TableCell>{call.call_start_time ? formatDate(call.call_start_time) : '-'}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[call.status] || 'bg-gray-100 text-gray-800'}>
                          {call.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>{call.outcome?.replace(/_/g, ' ') || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {(response.calls ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                        No call history found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Payment History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Transaction ID</TableHead>
                    <TableHead>Order #</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Gateway</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(response.payments ?? []).map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell>{formatDate(payment.created_at)}</TableCell>
                      <TableCell className="font-mono">{payment.transaction_id || '-'}</TableCell>
                      <TableCell className="font-mono">{payment.order_number || '-'}</TableCell>
                      <TableCell>{payment.method?.replace(/_/g, ' ') || '-'}</TableCell>
                      <TableCell>{payment.gateway || '-'}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(payment.amount)}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[payment.status] || 'bg-gray-100 text-gray-800'}>
                          {payment.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(response.payments ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No payment history found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Customer Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Customer</DialogTitle>
            <DialogDescription>Update all customer profile details</DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* Basic Information */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Basic Information</h3>
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-first-name">First Name *</Label>
                    <Input
                      id="edit-first-name"
                      value={editForm.first_name}
                      onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-last-name">Last Name</Label>
                    <Input
                      id="edit-last-name"
                      value={editForm.last_name}
                      onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-phone">Phone *</Label>
                    <Input
                      id="edit-phone"
                      value={editForm.phone}
                      onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-alt-phone">Alternate Phone</Label>
                    <Input
                      id="edit-alt-phone"
                      value={editForm.alternate_phone}
                      onChange={(e) => setEditForm({ ...editForm, alternate_phone: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-email">Email</Label>
                  <Input
                    id="edit-email"
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-type">Customer Type</Label>
                    <Select
                      value={editForm.customer_type}
                      onValueChange={(value: EditFormData['customer_type']) => setEditForm({ ...editForm, customer_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {customerTypes.map((t) => (
                          <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-source">Source</Label>
                    <Select
                      value={editForm.source || 'none'}
                      onValueChange={(value) => setEditForm({ ...editForm, source: value === 'none' ? '' : value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select source" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Not set</SelectItem>
                        {customerSources.map((s) => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* Business Details */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Business Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-company">Company Name</Label>
                  <Input
                    id="edit-company"
                    value={editForm.company_name}
                    onChange={(e) => setEditForm({ ...editForm, company_name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-gst">GST Number</Label>
                  <Input
                    id="edit-gst"
                    placeholder="22AAAAA0000A1Z5"
                    value={editForm.gst_number}
                    onChange={(e) => setEditForm({ ...editForm, gst_number: e.target.value.toUpperCase() })}
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Personal Details */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Personal Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-dob">Date of Birth</Label>
                  <Input
                    id="edit-dob"
                    type="date"
                    value={editForm.date_of_birth}
                    onChange={(e) => setEditForm({ ...editForm, date_of_birth: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-anniversary">Anniversary Date</Label>
                  <Input
                    id="edit-anniversary"
                    type="date"
                    value={editForm.anniversary_date}
                    onChange={(e) => setEditForm({ ...editForm, anniversary_date: e.target.value })}
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Addresses (editable) */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold">Addresses</h3>
                <Button type="button" variant="outline" size="sm" onClick={handleAddAddress}>
                  <Plus className="mr-1 h-3 w-3" /> Add Address
                </Button>
              </div>
              {editAddresses.length === 0 ? (
                <p className="text-sm text-muted-foreground">No addresses. Click &quot;Add Address&quot; to add one.</p>
              ) : (
                <div className="space-y-4">
                  {editAddresses.map((addr, idx) => (
                    <div key={addr.id || `new-${idx}`} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Select
                            value={addr.address_type}
                            onValueChange={(v) => handleAddressChange(idx, 'address_type', v)}
                          >
                            <SelectTrigger className="w-[130px] h-8">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {addressTypes.map((t) => (
                                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <label className="flex items-center gap-1.5 text-xs">
                            <input
                              type="checkbox"
                              checked={addr.is_default}
                              onChange={(e) => {
                                // Uncheck others when setting default
                                if (e.target.checked) {
                                  const updated = editAddresses.map((a, i) => ({ ...a, is_default: i === idx }));
                                  setEditAddresses(updated);
                                } else {
                                  handleAddressChange(idx, 'is_default', false);
                                }
                              }}
                              className="rounded"
                            />
                            Default
                          </label>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => handleRemoveAddress(idx)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                      <div className="space-y-2">
                        <Input
                          placeholder="Address Line 1 *"
                          value={addr.address_line1}
                          onChange={(e) => handleAddressChange(idx, 'address_line1', e.target.value)}
                        />
                        <Input
                          placeholder="Address Line 2"
                          value={addr.address_line2}
                          onChange={(e) => handleAddressChange(idx, 'address_line2', e.target.value)}
                        />
                        <Input
                          placeholder="Landmark"
                          value={addr.landmark}
                          onChange={(e) => handleAddressChange(idx, 'landmark', e.target.value)}
                        />
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <Input
                          placeholder="City *"
                          value={addr.city}
                          onChange={(e) => handleAddressChange(idx, 'city', e.target.value)}
                        />
                        <Input
                          placeholder="State *"
                          value={addr.state}
                          onChange={(e) => handleAddressChange(idx, 'state', e.target.value)}
                        />
                        <Input
                          placeholder="Pincode *"
                          value={addr.pincode}
                          onChange={(e) => handleAddressChange(idx, 'pincode', e.target.value)}
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          placeholder="Contact Name"
                          value={addr.contact_name}
                          onChange={(e) => handleAddressChange(idx, 'contact_name', e.target.value)}
                        />
                        <Input
                          placeholder="Contact Phone"
                          value={addr.contact_phone}
                          onChange={(e) => handleAddressChange(idx, 'contact_phone', e.target.value)}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Notes & Status */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Notes & Status</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-notes">Notes</Label>
                  <Textarea
                    id="edit-notes"
                    placeholder="Additional notes about the customer..."
                    rows={3}
                    value={editForm.notes}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-3">
                  <Label htmlFor="edit-active">Status</Label>
                  <Select
                    value={editForm.is_active ? 'active' : 'inactive'}
                    onValueChange={(value) => setEditForm({ ...editForm, is_active: value === 'active' })}
                  >
                    <SelectTrigger className="w-[150px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleEditSubmit} disabled={updateMutation.isPending || savingAddresses}>
              {(updateMutation.isPending || savingAddresses) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
