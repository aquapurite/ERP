'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Search,
  Plus,
  Trash2,
  User,
  Phone,
  MapPin,
  Package,
  CreditCard,
  Truck,
  Calculator,
  Loader2,
  CheckCircle,
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { PageHeader } from '@/components/common';
import { formatCurrency } from '@/lib/utils';

// Types
interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  customer_type: string;
  addresses: CustomerAddress[];
}

interface CustomerAddress {
  id: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  pincode: string;
  is_default: boolean;
}

interface Product {
  id: string;
  name: string;
  sku: string;
  mrp: number;
  selling_price: number;
  gst_rate: number;
  hsn_code: string;
  stock_available: number;
  category: string;
  brand: string;
}

interface Channel {
  id: string;
  name: string;
  code: string;
}

interface Warehouse {
  id: string;
  name: string;
  code: string;
}

// Mock APIs
const orderApi = {
  searchCustomers: async (phone: string): Promise<Customer[]> => {
    await new Promise((r) => setTimeout(r, 500));
    if (phone.length < 4) return [];
    return [
      {
        id: 'cust-1',
        name: 'Rajesh Kumar',
        phone: '+91 98765 43210',
        email: 'rajesh@example.com',
        customer_type: 'INDIVIDUAL',
        addresses: [
          { id: 'addr-1', address_line1: '123 MG Road', address_line2: 'Near Metro Station', city: 'Mumbai', state: 'Maharashtra', pincode: '400001', is_default: true },
          { id: 'addr-2', address_line1: '456 Park Street', city: 'Mumbai', state: 'Maharashtra', pincode: '400002', is_default: false },
        ],
      },
      {
        id: 'cust-2',
        name: 'Priya Sharma',
        phone: '+91 98765 43211',
        email: 'priya@example.com',
        customer_type: 'INDIVIDUAL',
        addresses: [
          { id: 'addr-3', address_line1: '789 Linking Road', city: 'Mumbai', state: 'Maharashtra', pincode: '400050', is_default: true },
        ],
      },
    ].filter((c) => c.phone.includes(phone) || c.name.toLowerCase().includes(phone.toLowerCase()));
  },
  searchProducts: async (query: string): Promise<Product[]> => {
    await new Promise((r) => setTimeout(r, 300));
    const products: Product[] = [
      { id: 'prod-1', name: 'AquaPure RO+UV Pro', sku: 'AP-RO-UV-001', mrp: 18999, selling_price: 15999, gst_rate: 18, hsn_code: '84212110', stock_available: 45, category: 'Water Purifiers', brand: 'AquaPure' },
      { id: 'prod-2', name: 'AquaPure UV Compact', sku: 'AP-UV-002', mrp: 12999, selling_price: 10999, gst_rate: 18, hsn_code: '84212120', stock_available: 32, category: 'Water Purifiers', brand: 'AquaPure' },
      { id: 'prod-3', name: 'PuroGuard Filter Set', sku: 'PG-FS-001', mrp: 2999, selling_price: 2499, gst_rate: 18, hsn_code: '84219900', stock_available: 156, category: 'Spare Parts', brand: 'PuroGuard' },
      { id: 'prod-4', name: 'AquaPure Alkaline Plus', sku: 'AP-ALK-001', mrp: 24999, selling_price: 21999, gst_rate: 18, hsn_code: '84212110', stock_available: 18, category: 'Water Purifiers', brand: 'AquaPure' },
      { id: 'prod-5', name: 'UV Lamp Replacement', sku: 'UV-LAMP-001', mrp: 1499, selling_price: 1299, gst_rate: 18, hsn_code: '85393100', stock_available: 89, category: 'Spare Parts', brand: 'AquaPure' },
    ];
    if (!query) return products.slice(0, 5);
    return products.filter((p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.sku.toLowerCase().includes(query.toLowerCase())
    );
  },
  getChannels: async (): Promise<Channel[]> => {
    return [
      { id: 'ch-1', name: 'Direct to Consumer', code: 'D2C' },
      { id: 'ch-2', name: 'Amazon', code: 'AMZ' },
      { id: 'ch-3', name: 'Flipkart', code: 'FK' },
      { id: 'ch-4', name: 'Dealer Network', code: 'DEALER' },
      { id: 'ch-5', name: 'Retail Store', code: 'RETAIL' },
    ];
  },
  getWarehouses: async (): Promise<Warehouse[]> => {
    return [
      { id: 'wh-1', name: 'Mumbai Central Warehouse', code: 'MUM-CEN' },
      { id: 'wh-2', name: 'Delhi Hub', code: 'DEL-HUB' },
      { id: 'wh-3', name: 'Bangalore Fulfillment', code: 'BLR-FC' },
    ];
  },
  createOrder: async (data: OrderFormData): Promise<{ id: string; order_number: string }> => {
    await new Promise((r) => setTimeout(r, 1000));
    return { id: 'ord-new-1', order_number: 'ORD-2024-00156' };
  },
};

// Form Schema
const orderItemSchema = z.object({
  product_id: z.string().min(1, 'Product is required'),
  product_name: z.string(),
  sku: z.string(),
  quantity: z.number().min(1, 'Quantity must be at least 1'),
  unit_price: z.number().min(0),
  discount_percent: z.number().min(0).max(100),
  gst_rate: z.number(),
  hsn_code: z.string(),
});

const orderFormSchema = z.object({
  customer_id: z.string().min(1, 'Customer is required'),
  shipping_address_id: z.string().min(1, 'Shipping address is required'),
  billing_address_id: z.string().optional(),
  channel_id: z.string().min(1, 'Channel is required'),
  warehouse_id: z.string().min(1, 'Warehouse is required'),
  payment_mode: z.enum(['COD', 'PREPAID', 'PARTIAL']),
  prepaid_amount: z.number().optional(),
  items: z.array(orderItemSchema).min(1, 'At least one item is required'),
  notes: z.string().optional(),
  same_billing_address: z.boolean(),
  installation_required: z.boolean(),
  priority: z.enum(['NORMAL', 'HIGH', 'URGENT']),
});

type OrderFormData = z.infer<typeof orderFormSchema>;
type OrderItemData = z.infer<typeof orderItemSchema>;

export default function CreateOrderPage() {
  const router = useRouter();
  const [customerSearchOpen, setCustomerSearchOpen] = useState(false);
  const [customerSearch, setCustomerSearch] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [productSearchOpen, setProductSearchOpen] = useState(false);
  const [productSearch, setProductSearch] = useState('');
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);
  const [createdOrder, setCreatedOrder] = useState<{ id: string; order_number: string } | null>(null);

  const form = useForm<OrderFormData>({
    resolver: zodResolver(orderFormSchema),
    defaultValues: {
      customer_id: '',
      shipping_address_id: '',
      billing_address_id: '',
      channel_id: '',
      warehouse_id: '',
      payment_mode: 'COD',
      prepaid_amount: 0,
      items: [],
      notes: '',
      same_billing_address: true,
      installation_required: true,
      priority: 'NORMAL',
    },
  });

  const { fields, append, remove, update } = useFieldArray({
    control: form.control,
    name: 'items',
  });

  // Queries
  const { data: customerResults, isLoading: searchingCustomers } = useQuery({
    queryKey: ['customer-search', customerSearch],
    queryFn: () => orderApi.searchCustomers(customerSearch),
    enabled: customerSearch.length >= 3,
  });

  const { data: productResults, isLoading: searchingProducts } = useQuery({
    queryKey: ['product-search', productSearch],
    queryFn: () => orderApi.searchProducts(productSearch),
    enabled: productSearchOpen,
  });

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: orderApi.getChannels,
  });

  const { data: warehouses } = useQuery({
    queryKey: ['warehouses'],
    queryFn: orderApi.getWarehouses,
  });

  // Mutation
  const createOrderMutation = useMutation({
    mutationFn: orderApi.createOrder,
    onSuccess: (data) => {
      setCreatedOrder(data);
      setSuccessDialogOpen(true);
    },
  });

  // Calculations
  const calculateItemTotal = (item: OrderItemData) => {
    const basePrice = item.unit_price * item.quantity;
    const discount = (basePrice * item.discount_percent) / 100;
    const taxableAmount = basePrice - discount;
    const gstAmount = (taxableAmount * item.gst_rate) / 100;
    return {
      basePrice,
      discount,
      taxableAmount,
      gstAmount,
      total: taxableAmount + gstAmount,
    };
  };

  const orderSummary = form.watch('items').reduce(
    (acc, item) => {
      const calc = calculateItemTotal(item);
      return {
        subtotal: acc.subtotal + calc.basePrice,
        discount: acc.discount + calc.discount,
        taxable: acc.taxable + calc.taxableAmount,
        gst: acc.gst + calc.gstAmount,
        total: acc.total + calc.total,
      };
    },
    { subtotal: 0, discount: 0, taxable: 0, gst: 0, total: 0 }
  );

  // Handlers
  const handleCustomerSelect = (customer: Customer) => {
    setSelectedCustomer(customer);
    form.setValue('customer_id', customer.id);
    const defaultAddress = customer.addresses.find((a) => a.is_default);
    if (defaultAddress) {
      form.setValue('shipping_address_id', defaultAddress.id);
      form.setValue('billing_address_id', defaultAddress.id);
    }
    setCustomerSearchOpen(false);
    setCustomerSearch('');
  };

  const handleAddProduct = (product: Product) => {
    const existingIndex = fields.findIndex((f) => f.product_id === product.id);
    if (existingIndex >= 0) {
      const existing = fields[existingIndex];
      update(existingIndex, {
        ...existing,
        quantity: existing.quantity + 1,
      });
    } else {
      append({
        product_id: product.id,
        product_name: product.name,
        sku: product.sku,
        quantity: 1,
        unit_price: product.selling_price,
        discount_percent: 0,
        gst_rate: product.gst_rate,
        hsn_code: product.hsn_code,
      });
    }
    setProductSearchOpen(false);
    setProductSearch('');
  };

  const handleQuantityChange = (index: number, delta: number) => {
    const current = fields[index];
    const newQty = Math.max(1, current.quantity + delta);
    update(index, { ...current, quantity: newQty });
  };

  const handleDiscountChange = (index: number, discount: number) => {
    const current = fields[index];
    update(index, { ...current, discount_percent: Math.min(100, Math.max(0, discount)) });
  };

  const onSubmit = (data: OrderFormData) => {
    createOrderMutation.mutate(data);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Order"
        description="Create a new sales order"
        actions={
          <Button variant="outline" asChild>
            <Link href="/orders">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Orders
            </Link>
          </Button>
        }
      />

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Customer Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Customer Details
                </CardTitle>
                <CardDescription>Search and select customer by phone or name</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!selectedCustomer ? (
                  <Popover open={customerSearchOpen} onOpenChange={setCustomerSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start">
                        <Search className="mr-2 h-4 w-4" />
                        Search customer by phone or name...
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-96 p-0" align="start">
                      <Command>
                        <CommandInput
                          placeholder="Enter phone number or name..."
                          value={customerSearch}
                          onValueChange={setCustomerSearch}
                        />
                        <CommandList>
                          {searchingCustomers && (
                            <div className="flex items-center justify-center py-6">
                              <Loader2 className="h-4 w-4 animate-spin" />
                            </div>
                          )}
                          <CommandEmpty>
                            {customerSearch.length < 3
                              ? 'Enter at least 3 characters to search'
                              : 'No customers found'}
                          </CommandEmpty>
                          <CommandGroup heading="Customers">
                            {customerResults?.map((customer) => (
                              <CommandItem
                                key={customer.id}
                                onSelect={() => handleCustomerSelect(customer)}
                                className="cursor-pointer"
                              >
                                <div className="flex items-center gap-3">
                                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                                    <User className="h-5 w-5" />
                                  </div>
                                  <div>
                                    <div className="font-medium">{customer.name}</div>
                                    <div className="text-sm text-muted-foreground">
                                      {customer.phone} | {customer.customer_type}
                                    </div>
                                  </div>
                                </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                          <User className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <div className="font-semibold">{selectedCustomer.name}</div>
                          <div className="text-sm text-muted-foreground flex items-center gap-2">
                            <Phone className="h-3 w-3" />
                            {selectedCustomer.phone}
                          </div>
                          {selectedCustomer.email && (
                            <div className="text-sm text-muted-foreground">{selectedCustomer.email}</div>
                          )}
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedCustomer(null);
                          form.setValue('customer_id', '');
                          form.setValue('shipping_address_id', '');
                        }}
                      >
                        Change
                      </Button>
                    </div>

                    {/* Address Selection */}
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Shipping Address</Label>
                        <Select
                          value={form.watch('shipping_address_id')}
                          onValueChange={(v) => form.setValue('shipping_address_id', v)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select shipping address" />
                          </SelectTrigger>
                          <SelectContent>
                            {selectedCustomer.addresses.map((addr) => (
                              <SelectItem key={addr.id} value={addr.id}>
                                <div className="flex items-center gap-2">
                                  <MapPin className="h-3 w-3" />
                                  {addr.address_line1}, {addr.city} - {addr.pincode}
                                  {addr.is_default && <Badge variant="secondary" className="ml-2">Default</Badge>}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label>Billing Address</Label>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={form.watch('same_billing_address')}
                              onCheckedChange={(v) => form.setValue('same_billing_address', v)}
                            />
                            <span className="text-sm text-muted-foreground">Same as shipping</span>
                          </div>
                        </div>
                        {!form.watch('same_billing_address') && (
                          <Select
                            value={form.watch('billing_address_id')}
                            onValueChange={(v) => form.setValue('billing_address_id', v)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select billing address" />
                            </SelectTrigger>
                            <SelectContent>
                              {selectedCustomer.addresses.map((addr) => (
                                <SelectItem key={addr.id} value={addr.id}>
                                  {addr.address_line1}, {addr.city} - {addr.pincode}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                {form.formState.errors.customer_id && (
                  <p className="text-sm text-destructive">{form.formState.errors.customer_id.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Order Items */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Order Items
                </CardTitle>
                <CardDescription>Add products to the order</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Add Product */}
                <Popover open={productSearchOpen} onOpenChange={setProductSearchOpen}>
                  <PopoverTrigger asChild>
                    <Button type="button" variant="outline" className="w-full justify-start">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Product
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[500px] p-0" align="start">
                    <Command>
                      <CommandInput
                        placeholder="Search products by name or SKU..."
                        value={productSearch}
                        onValueChange={setProductSearch}
                      />
                      <CommandList>
                        {searchingProducts && (
                          <div className="flex items-center justify-center py-6">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </div>
                        )}
                        <CommandEmpty>No products found</CommandEmpty>
                        <CommandGroup heading="Products">
                          {productResults?.map((product) => (
                            <CommandItem
                              key={product.id}
                              onSelect={() => handleAddProduct(product)}
                              className="cursor-pointer"
                            >
                              <div className="flex items-center justify-between w-full">
                                <div>
                                  <div className="font-medium">{product.name}</div>
                                  <div className="text-sm text-muted-foreground">
                                    SKU: {product.sku} | Stock: {product.stock_available}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="font-medium">{formatCurrency(product.selling_price)}</div>
                                  <div className="text-sm text-muted-foreground line-through">
                                    {formatCurrency(product.mrp)}
                                  </div>
                                </div>
                              </div>
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>

                {/* Items List */}
                {fields.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
                    <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No items added yet</p>
                    <p className="text-sm">Search and add products above</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {fields.map((item, index) => {
                      const calc = calculateItemTotal(item);
                      return (
                        <div key={item.id} className="flex items-center gap-4 p-4 border rounded-lg">
                          <div className="flex-1">
                            <div className="font-medium">{item.product_name}</div>
                            <div className="text-sm text-muted-foreground">
                              SKU: {item.sku} | HSN: {item.hsn_code}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleQuantityChange(index, -1)}
                            >
                              -
                            </Button>
                            <Input
                              type="number"
                              value={item.quantity}
                              onChange={(e) => update(index, { ...item, quantity: parseInt(e.target.value) || 1 })}
                              className="w-16 text-center h-8"
                            />
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleQuantityChange(index, 1)}
                            >
                              +
                            </Button>
                          </div>
                          <div className="w-24">
                            <Label className="text-xs">Discount %</Label>
                            <Input
                              type="number"
                              value={item.discount_percent}
                              onChange={(e) => handleDiscountChange(index, parseFloat(e.target.value) || 0)}
                              className="h-8"
                              min={0}
                              max={100}
                            />
                          </div>
                          <div className="w-28 text-right">
                            <div className="font-medium">{formatCurrency(calc.total)}</div>
                            <div className="text-xs text-muted-foreground">
                              GST: {formatCurrency(calc.gstAmount)}
                            </div>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive"
                            onClick={() => remove(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                )}
                {form.formState.errors.items && (
                  <p className="text-sm text-destructive">{form.formState.errors.items.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Order Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Order Settings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Channel</Label>
                    <Select
                      value={form.watch('channel_id')}
                      onValueChange={(v) => form.setValue('channel_id', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select channel" />
                      </SelectTrigger>
                      <SelectContent>
                        {channels?.map((ch) => (
                          <SelectItem key={ch.id} value={ch.id}>
                            {ch.name} ({ch.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {form.formState.errors.channel_id && (
                      <p className="text-sm text-destructive">{form.formState.errors.channel_id.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Fulfillment Warehouse</Label>
                    <Select
                      value={form.watch('warehouse_id')}
                      onValueChange={(v) => form.setValue('warehouse_id', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses?.map((wh) => (
                          <SelectItem key={wh.id} value={wh.id}>
                            {wh.name} ({wh.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {form.formState.errors.warehouse_id && (
                      <p className="text-sm text-destructive">{form.formState.errors.warehouse_id.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select
                      value={form.watch('priority')}
                      onValueChange={(v: 'NORMAL' | 'HIGH' | 'URGENT') => form.setValue('priority', v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NORMAL">Normal</SelectItem>
                        <SelectItem value="HIGH">High Priority</SelectItem>
                        <SelectItem value="URGENT">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Installation Required</Label>
                    <div className="flex items-center gap-2 pt-2">
                      <Switch
                        checked={form.watch('installation_required')}
                        onCheckedChange={(v) => form.setValue('installation_required', v)}
                      />
                      <span className="text-sm">
                        {form.watch('installation_required') ? 'Yes, schedule installation' : 'No installation needed'}
                      </span>
                    </div>
                  </div>
                </div>

                <Separator className="my-4" />

                <div className="space-y-2">
                  <Label>Order Notes</Label>
                  <Textarea
                    placeholder="Add any special instructions or notes..."
                    {...form.register('notes')}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Payment & Summary */}
          <div className="space-y-6">
            {/* Payment Mode */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Payment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Payment Mode</Label>
                  <Select
                    value={form.watch('payment_mode')}
                    onValueChange={(v: 'COD' | 'PREPAID' | 'PARTIAL') => form.setValue('payment_mode', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="COD">Cash on Delivery</SelectItem>
                      <SelectItem value="PREPAID">Prepaid</SelectItem>
                      <SelectItem value="PARTIAL">Partial Payment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {form.watch('payment_mode') === 'PARTIAL' && (
                  <div className="space-y-2">
                    <Label>Prepaid Amount</Label>
                    <Input
                      type="number"
                      placeholder="Enter prepaid amount"
                      {...form.register('prepaid_amount', { valueAsNumber: true })}
                    />
                    <p className="text-sm text-muted-foreground">
                      Balance: {formatCurrency(orderSummary.total - (form.watch('prepaid_amount') || 0))}
                    </p>
                  </div>
                )}

                {form.watch('payment_mode') === 'PREPAID' && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 text-green-800">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">Payment collected</span>
                    </div>
                    <p className="text-sm text-green-600 mt-1">
                      Full payment of {formatCurrency(orderSummary.total)} received
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Order Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5" />
                  Order Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>{formatCurrency(orderSummary.subtotal)}</span>
                </div>
                {orderSummary.discount > 0 && (
                  <div className="flex justify-between text-sm text-green-600">
                    <span>Discount</span>
                    <span>-{formatCurrency(orderSummary.discount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Taxable Amount</span>
                  <span>{formatCurrency(orderSummary.taxable)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">GST (18%)</span>
                  <span>{formatCurrency(orderSummary.gst)}</span>
                </div>
                <Separator />
                <div className="flex justify-between font-semibold text-lg">
                  <span>Total</span>
                  <span>{formatCurrency(orderSummary.total)}</span>
                </div>

                {form.watch('payment_mode') !== 'PREPAID' && orderSummary.total > 0 && (
                  <div className="pt-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        {form.watch('payment_mode') === 'COD' ? 'COD Amount' : 'Balance Due'}
                      </span>
                      <span className="font-medium">
                        {formatCurrency(
                          form.watch('payment_mode') === 'PARTIAL'
                            ? orderSummary.total - (form.watch('prepaid_amount') || 0)
                            : orderSummary.total
                        )}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Submit */}
            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={createOrderMutation.isPending || fields.length === 0}
            >
              {createOrderMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Order...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Create Order
                </>
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Success Dialog */}
      <Dialog open={successDialogOpen} onOpenChange={setSuccessDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              Order Created Successfully
            </DialogTitle>
            <DialogDescription>
              Your order has been created and is ready for processing.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="text-center space-y-2">
              <div className="text-2xl font-bold">{createdOrder?.order_number}</div>
              <div className="text-sm text-muted-foreground">Order Number</div>
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => router.push('/orders')}>
              Back to Orders
            </Button>
            <Button onClick={() => router.push(`/orders/${createdOrder?.id}`)}>
              View Order Details
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
