'use client';

import { useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User, Phone, Mail, MapPin, Calendar, ShoppingBag, Wrench, Shield, Package, Star, AlertTriangle,
  CreditCard, Clock, CheckCircle, ArrowLeft, Edit, MoreHorizontal, FileText, Heart, Activity,
  MessageSquare, IndianRupee, TrendingUp, Home, Building2, Truck
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

interface CustomerAddress {
  id: string;
  label: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  pincode: string;
  is_default: boolean;
}

interface CustomerProduct {
  id: string;
  product_name: string;
  serial_number: string;
  purchase_date: string;
  warranty_end_date: string;
  amc_status: 'ACTIVE' | 'EXPIRED' | 'NONE';
  amc_plan?: string;
  installation_date?: string;
  last_service_date?: string;
}

interface CustomerOrder {
  id: string;
  order_number: string;
  order_date: string;
  status: string;
  total_amount: number;
  items_count: number;
  payment_status: string;
}

interface CustomerServiceRequest {
  id: string;
  ticket_number: string;
  created_at: string;
  type: string;
  product_name: string;
  status: string;
  assigned_technician?: string;
  resolved_at?: string;
  rating?: number;
}

interface CustomerAMC {
  id: string;
  contract_number: string;
  product_name: string;
  serial_number: string;
  plan_name: string;
  start_date: string;
  end_date: string;
  status: 'ACTIVE' | 'EXPIRED' | 'PENDING';
  visits_used: number;
  visits_total: number;
}

interface CustomerInteraction {
  id: string;
  type: 'CALL' | 'EMAIL' | 'CHAT' | 'VISIT' | 'SMS';
  date: string;
  summary: string;
  agent?: string;
  outcome?: string;
}

interface CustomerPayment {
  id: string;
  date: string;
  reference: string;
  type: 'ORDER' | 'AMC' | 'SERVICE' | 'REFUND';
  amount: number;
  method: string;
  status: 'SUCCESS' | 'PENDING' | 'FAILED';
}

interface Customer360 {
  id: string;
  name: string;
  phone: string;
  email?: string;
  customer_type: 'INDIVIDUAL' | 'BUSINESS' | 'DEALER';
  is_active: boolean;
  created_at: string;
  date_of_birth?: string;
  anniversary?: string;
  gstin?: string;
  addresses: CustomerAddress[];
  // Stats
  total_orders: number;
  total_spent: number;
  products_owned: number;
  active_amc: number;
  service_requests: number;
  avg_rating: number;
  loyalty_points: number;
  lifetime_value: number;
  last_purchase_date?: string;
  last_service_date?: string;
  // Related data
  products: CustomerProduct[];
  orders: CustomerOrder[];
  service_requests_list: CustomerServiceRequest[];
  amc_contracts: CustomerAMC[];
  interactions: CustomerInteraction[];
  payments: CustomerPayment[];
}

const customer360Api = {
  get: async (id: string): Promise<Customer360> => {
    return {
      id,
      name: 'Priya Sharma',
      phone: '+91 98765 43210',
      email: 'priya.sharma@email.com',
      customer_type: 'INDIVIDUAL',
      is_active: true,
      created_at: '2022-06-15',
      date_of_birth: '1985-03-20',
      anniversary: '2010-11-25',
      addresses: [
        { id: '1', label: 'Home', address_line1: '123, Green Valley Apartments', address_line2: 'Near City Mall', city: 'Mumbai', state: 'Maharashtra', pincode: '400001', is_default: true },
        { id: '2', label: 'Office', address_line1: '456, Tech Park, Floor 5', city: 'Mumbai', state: 'Maharashtra', pincode: '400051', is_default: false },
      ],
      total_orders: 8,
      total_spent: 125680,
      products_owned: 3,
      active_amc: 2,
      service_requests: 5,
      avg_rating: 4.8,
      loyalty_points: 2560,
      lifetime_value: 156780,
      last_purchase_date: '2024-01-15',
      last_service_date: '2024-02-20',
      products: [
        { id: '1', product_name: 'AquaPure RO Elite', serial_number: 'AP-RO-002-67890', purchase_date: '2023-06-20', warranty_end_date: '2024-06-19', amc_status: 'ACTIVE', amc_plan: 'Premium Care', installation_date: '2023-06-22', last_service_date: '2024-02-15' },
        { id: '2', product_name: 'AquaPure UV Compact', serial_number: 'AP-UV-001-12345', purchase_date: '2022-08-10', warranty_end_date: '2023-08-09', amc_status: 'ACTIVE', amc_plan: 'Standard Care', installation_date: '2022-08-12', last_service_date: '2024-01-20' },
        { id: '3', product_name: 'Voltage Stabilizer 5KVA', serial_number: 'VS-5K-001-55555', purchase_date: '2024-01-15', warranty_end_date: '2026-01-14', amc_status: 'NONE', installation_date: '2024-01-16' },
      ],
      orders: [
        { id: '1', order_number: 'ORD-2024-0156', order_date: '2024-01-15', status: 'DELIVERED', total_amount: 45890, items_count: 2, payment_status: 'PAID' },
        { id: '2', order_number: 'ORD-2023-0892', order_date: '2023-06-20', status: 'DELIVERED', total_amount: 32500, items_count: 1, payment_status: 'PAID' },
        { id: '3', order_number: 'ORD-2022-0543', order_date: '2022-08-10', status: 'DELIVERED', total_amount: 18990, items_count: 1, payment_status: 'PAID' },
        { id: '4', order_number: 'ORD-2024-0189', order_date: '2024-02-01', status: 'PROCESSING', total_amount: 8500, items_count: 3, payment_status: 'PAID' },
      ],
      service_requests_list: [
        { id: '1', ticket_number: 'SR-2024-0234', created_at: '2024-02-15', type: 'PREVENTIVE_MAINTENANCE', product_name: 'AquaPure RO Elite', status: 'COMPLETED', assigned_technician: 'Rajesh Kumar', resolved_at: '2024-02-15', rating: 5 },
        { id: '2', ticket_number: 'SR-2024-0189', created_at: '2024-01-20', type: 'PREVENTIVE_MAINTENANCE', product_name: 'AquaPure UV Compact', status: 'COMPLETED', assigned_technician: 'Suresh Singh', resolved_at: '2024-01-20', rating: 5 },
        { id: '3', ticket_number: 'SR-2023-0876', created_at: '2023-11-10', type: 'REPAIR', product_name: 'AquaPure UV Compact', status: 'COMPLETED', assigned_technician: 'Amit Verma', resolved_at: '2023-11-11', rating: 4 },
        { id: '4', ticket_number: 'SR-2023-0654', created_at: '2023-08-25', type: 'INSTALLATION', product_name: 'AquaPure RO Elite', status: 'COMPLETED', assigned_technician: 'Rajesh Kumar', resolved_at: '2023-08-25', rating: 5 },
      ],
      amc_contracts: [
        { id: '1', contract_number: 'AMC-2024-0156', product_name: 'AquaPure RO Elite', serial_number: 'AP-RO-002-67890', plan_name: 'Premium Care', start_date: '2024-01-01', end_date: '2024-12-31', status: 'ACTIVE', visits_used: 1, visits_total: 6 },
        { id: '2', contract_number: 'AMC-2023-0892', product_name: 'AquaPure UV Compact', serial_number: 'AP-UV-001-12345', plan_name: 'Standard Care', start_date: '2023-09-01', end_date: '2024-08-31', status: 'ACTIVE', visits_used: 2, visits_total: 4 },
      ],
      interactions: [
        { id: '1', type: 'CALL', date: '2024-02-20', summary: 'Customer called regarding scheduled service visit', agent: 'Anjali', outcome: 'Confirmed appointment' },
        { id: '2', type: 'EMAIL', date: '2024-02-15', summary: 'Service completion confirmation sent', agent: 'System' },
        { id: '3', type: 'SMS', date: '2024-02-14', summary: 'Service reminder for tomorrow', agent: 'System' },
        { id: '4', type: 'CALL', date: '2024-01-18', summary: 'Customer inquiry about AMC renewal', agent: 'Priyanka', outcome: 'Shared renewal options' },
      ],
      payments: [
        { id: '1', date: '2024-01-15', reference: 'PAY-2024-0156', type: 'ORDER', amount: 45890, method: 'Credit Card', status: 'SUCCESS' },
        { id: '2', date: '2024-01-01', reference: 'PAY-2024-0001', type: 'AMC', amount: 7999, method: 'UPI', status: 'SUCCESS' },
        { id: '3', date: '2023-09-01', reference: 'PAY-2023-0892', type: 'AMC', amount: 4999, method: 'Net Banking', status: 'SUCCESS' },
        { id: '4', date: '2023-06-20', reference: 'PAY-2023-0654', type: 'ORDER', amount: 32500, method: 'Debit Card', status: 'SUCCESS' },
      ],
    };
  },
};

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

const interactionTypeIcons: Record<string, React.ReactNode> = {
  CALL: <Phone className="h-4 w-4" />,
  EMAIL: <Mail className="h-4 w-4" />,
  CHAT: <MessageSquare className="h-4 w-4" />,
  VISIT: <Home className="h-4 w-4" />,
  SMS: <MessageSquare className="h-4 w-4" />,
};

export default function Customer360Page() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get('tab') || 'overview';
  const [activeTab, setActiveTab] = useState(initialTab);

  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer-360', params.id],
    queryFn: () => customer360Api.get(params.id as string),
  });

  if (isLoading) {
    return <div className="flex items-center justify-center h-96">Loading...</div>;
  }

  if (!customer) {
    return <div className="flex items-center justify-center h-96">Customer not found</div>;
  }

  const initials = customer.name.split(' ').map(n => n[0]).join('').toUpperCase();

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
              <h1 className="text-2xl font-bold">{customer.name}</h1>
              <Badge className={customer.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                {customer.is_active ? 'Active' : 'Inactive'}
              </Badge>
              <Badge variant="outline">{customer.customer_type}</Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
              <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{customer.phone}</span>
              {customer.email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{customer.email}</span>}
              <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />Customer since {formatDate(customer.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Edit className="mr-2 h-4 w-4" />Edit</Button>
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
              <span className="text-sm text-muted-foreground">Lifetime Value</span>
            </div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(customer.lifetime_value)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <ShoppingBag className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total Orders</span>
            </div>
            <div className="text-2xl font-bold mt-1">{customer.total_orders}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Products</span>
            </div>
            <div className="text-2xl font-bold mt-1">{customer.products_owned}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Active AMC</span>
            </div>
            <div className="text-2xl font-bold mt-1">{customer.active_amc}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-500" />
              <span className="text-sm text-muted-foreground">Avg Rating</span>
            </div>
            <div className="text-2xl font-bold mt-1">{customer.avg_rating}/5</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-red-500" />
              <span className="text-sm text-muted-foreground">Loyalty Points</span>
            </div>
            <div className="text-2xl font-bold mt-1">{customer.loyalty_points.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="products">Products ({customer.products.length})</TabsTrigger>
          <TabsTrigger value="orders">Orders ({customer.orders.length})</TabsTrigger>
          <TabsTrigger value="services">Services ({customer.service_requests_list.length})</TabsTrigger>
          <TabsTrigger value="amc">AMC ({customer.amc_contracts.length})</TabsTrigger>
          <TabsTrigger value="interactions">Interactions</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
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
                  <span className="font-medium">{customer.phone}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Email</span>
                  <span className="font-medium">{customer.email || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Customer Type</span>
                  <Badge variant="outline">{customer.customer_type}</Badge>
                </div>
                {customer.date_of_birth && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Birthday</span>
                    <span className="font-medium">{formatDate(customer.date_of_birth)}</span>
                  </div>
                )}
                {customer.anniversary && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Anniversary</span>
                    <span className="font-medium">{formatDate(customer.anniversary)}</span>
                  </div>
                )}
                {customer.gstin && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">GSTIN</span>
                    <span className="font-mono text-sm">{customer.gstin}</span>
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
                {customer.addresses.map((addr) => (
                  <div key={addr.id} className="space-y-1">
                    <div className="flex items-center gap-2">
                      {addr.label === 'Home' ? <Home className="h-4 w-4" /> : <Building2 className="h-4 w-4" />}
                      <span className="font-medium">{addr.label}</span>
                      {addr.is_default && <Badge variant="outline" className="text-xs">Default</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {addr.address_line1}
                      {addr.address_line2 && `, ${addr.address_line2}`}
                      <br />{addr.city}, {addr.state} - {addr.pincode}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Activity Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Purchase</span>
                  <span className="font-medium">{customer.last_purchase_date ? formatDate(customer.last_purchase_date) : 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Service</span>
                  <span className="font-medium">{customer.last_service_date ? formatDate(customer.last_service_date) : 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Spent</span>
                  <span className="font-medium">{formatCurrency(customer.total_spent)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Avg Order Value</span>
                  <span className="font-medium">{formatCurrency(customer.total_spent / (customer.total_orders || 1))}</span>
                </div>
                <Separator />
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Service Satisfaction</span>
                    <span>{customer.avg_rating * 20}%</span>
                  </div>
                  <Progress value={customer.avg_rating * 20} />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {customer.interactions.slice(0, 5).map((interaction) => (
                  <div key={interaction.id} className="flex items-start gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                      {interactionTypeIcons[interaction.type]}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{interaction.type}</span>
                        <span className="text-xs text-muted-foreground">{formatDate(interaction.date)}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{interaction.summary}</p>
                      {interaction.agent && <p className="text-xs text-muted-foreground">By: {interaction.agent}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="products" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Registered Products</CardTitle>
              <CardDescription>All products owned by this customer</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead>Serial Number</TableHead>
                    <TableHead>Purchase Date</TableHead>
                    <TableHead>Warranty</TableHead>
                    <TableHead>AMC Status</TableHead>
                    <TableHead>Last Service</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {customer.products.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell className="font-medium">{product.product_name}</TableCell>
                      <TableCell className="font-mono text-sm">{product.serial_number}</TableCell>
                      <TableCell>{formatDate(product.purchase_date)}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>Till {formatDate(product.warranty_end_date)}</div>
                          {new Date(product.warranty_end_date) < new Date() && (
                            <Badge className="bg-red-100 text-red-800 text-xs">Expired</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[product.amc_status]}>
                          {product.amc_status}
                        </Badge>
                        {product.amc_plan && <div className="text-xs text-muted-foreground mt-1">{product.amc_plan}</div>}
                      </TableCell>
                      <TableCell>{product.last_service_date ? formatDate(product.last_service_date) : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
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
                  {customer.orders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-mono font-medium">{order.order_number}</TableCell>
                      <TableCell>{formatDate(order.order_date)}</TableCell>
                      <TableCell>{order.items_count} items</TableCell>
                      <TableCell className="font-medium">{formatCurrency(order.total_amount)}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[order.payment_status]}>{order.payment_status}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[order.status]}>{order.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => router.push(`/orders/${order.id}`)}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Service History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticket #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>Technician</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Rating</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {customer.service_requests_list.map((sr) => (
                    <TableRow key={sr.id}>
                      <TableCell className="font-mono font-medium">{sr.ticket_number}</TableCell>
                      <TableCell>{formatDate(sr.created_at)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{sr.type.replace(/_/g, ' ')}</Badge>
                      </TableCell>
                      <TableCell>{sr.product_name}</TableCell>
                      <TableCell>{sr.assigned_technician || '-'}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[sr.status]}>{sr.status}</Badge>
                      </TableCell>
                      <TableCell>
                        {sr.rating ? (
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                            <span>{sr.rating}/5</span>
                          </div>
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
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
                    <TableHead>Product</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Validity</TableHead>
                    <TableHead>Visits Used</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {customer.amc_contracts.map((amc) => (
                    <TableRow key={amc.id}>
                      <TableCell className="font-mono font-medium">{amc.contract_number}</TableCell>
                      <TableCell>
                        <div>{amc.product_name}</div>
                        <div className="text-xs text-muted-foreground font-mono">{amc.serial_number}</div>
                      </TableCell>
                      <TableCell>{amc.plan_name}</TableCell>
                      <TableCell>
                        <div>{formatDate(amc.start_date)}</div>
                        <div className="text-xs text-muted-foreground">to {formatDate(amc.end_date)}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={(amc.visits_used / amc.visits_total) * 100} className="w-16 h-2" />
                          <span className="text-sm">{amc.visits_used}/{amc.visits_total}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[amc.status]}>{amc.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => router.push(`/service/amc/${amc.id}`)}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="interactions" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Communication History</CardTitle>
              <CardDescription>All interactions with this customer</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {customer.interactions.map((interaction) => (
                  <div key={interaction.id} className="flex items-start gap-4 p-4 border rounded-lg">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      {interactionTypeIcons[interaction.type]}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{interaction.type}</Badge>
                          {interaction.agent && <span className="text-sm text-muted-foreground">by {interaction.agent}</span>}
                        </div>
                        <span className="text-sm text-muted-foreground">{formatDate(interaction.date)}</span>
                      </div>
                      <p className="mt-2">{interaction.summary}</p>
                      {interaction.outcome && (
                        <p className="mt-1 text-sm text-muted-foreground">
                          <span className="font-medium">Outcome:</span> {interaction.outcome}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
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
                    <TableHead>Reference</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {customer.payments.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell>{formatDate(payment.date)}</TableCell>
                      <TableCell className="font-mono">{payment.reference}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{payment.type}</Badge>
                      </TableCell>
                      <TableCell>{payment.method}</TableCell>
                      <TableCell className={`text-right font-medium ${payment.type === 'REFUND' ? 'text-red-600' : ''}`}>
                        {payment.type === 'REFUND' ? '-' : ''}{formatCurrency(payment.amount)}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[payment.status]}>{payment.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
