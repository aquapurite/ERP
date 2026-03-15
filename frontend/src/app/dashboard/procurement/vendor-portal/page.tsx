'use client';

import { useState, useCallback } from 'react';
import { vendorPortalApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import {
  Search, ShoppingCart, FileText, CreditCard, PackageSearch,
  Building2, IndianRupee, Clock, CheckCircle,
} from 'lucide-react';

interface DashboardStats {
  vendor_code: string;
  vendor_name: string;
  total_pos: number;
  pending_deliveries: number;
  invoices_submitted: number;
  payments_received: number;
  total_payment_amount: number;
}

interface POItem {
  id: string;
  po_number: string;
  order_date?: string;
  status: string;
  total_amount: number;
  delivery_date?: string;
  items_count: number;
}

interface InvoiceItem {
  id: string;
  invoice_number: string;
  invoice_date?: string;
  status: string;
  total_amount: number;
  due_date?: string;
  payment_status: string;
}

interface PaymentItem {
  id: string;
  payment_number?: string;
  payment_date?: string;
  amount: number;
  payment_mode: string;
  reference?: string;
  status: string;
}

interface GRNItem {
  id: string;
  grn_number: string;
  grn_date?: string;
  po_number?: string;
  status: string;
  total_received: number;
  total_accepted: number;
  total_rejected: number;
}

export default function VendorPortalPage() {
  const [vendorCode, setVendorCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pos, setPOs] = useState<POItem[]>([]);
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [grns, setGRNs] = useState<GRNItem[]>([]);
  const [tab, setTab] = useState('pos');

  const fmt = (n: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  const loadVendorData = useCallback(async () => {
    if (!vendorCode.trim()) {
      toast.error('Please enter a vendor code');
      return;
    }
    setLoading(true);
    try {
      const [dashData, poData, invData, payData, grnData] = await Promise.all([
        vendorPortalApi.getDashboard(vendorCode),
        vendorPortalApi.listPOs(vendorCode),
        vendorPortalApi.listInvoices(vendorCode),
        vendorPortalApi.listPayments(vendorCode),
        vendorPortalApi.listGRNs(vendorCode),
      ]);
      setStats(dashData);
      setPOs(poData.items || []);
      setInvoices(invData.items || []);
      setPayments(payData.items || []);
      setGRNs(grnData.items || []);
      toast.success(`Loaded data for ${dashData.vendor_name || vendorCode}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Vendor not found or API error';
      toast.error(message);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [vendorCode]);

  const statusColor = (status: string) => {
    const s = status.toUpperCase();
    if (['APPROVED', 'COMPLETED', 'PAID', 'FULLY_RECEIVED'].includes(s)) return 'default';
    if (['PENDING', 'DRAFT', 'PENDING_APPROVAL'].includes(s)) return 'secondary';
    if (['CANCELLED', 'REJECTED'].includes(s)) return 'destructive';
    return 'outline';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Vendor Portal</h1>
        <p className="text-muted-foreground">Self-service vendor view (SAP SRM)</p>
      </div>

      {/* Vendor Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-sm font-medium mb-1 block">Vendor Code</label>
              <Input
                value={vendorCode}
                onChange={e => setVendorCode(e.target.value)}
                placeholder="e.g. VND-00001"
                onKeyDown={e => e.key === 'Enter' && loadVendorData()}
              />
            </div>
            <Button onClick={loadVendorData} disabled={loading}>
              <Search className="h-4 w-4 mr-2" />
              {loading ? 'Loading...' : 'Load Vendor'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Dashboard Cards */}
      {stats && (
        <>
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="h-5 w-5" />
            <h2 className="text-lg font-semibold">{stats.vendor_name}</h2>
            <Badge variant="outline">{stats.vendor_code}</Badge>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <ShoppingCart className="h-4 w-4" /> Total POs
                </div>
                <p className="text-2xl font-bold mt-1">{stats.total_pos}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <Clock className="h-4 w-4" /> Pending Deliveries
                </div>
                <p className="text-2xl font-bold mt-1 text-orange-600">{stats.pending_deliveries}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <FileText className="h-4 w-4" /> Invoices
                </div>
                <p className="text-2xl font-bold mt-1">{stats.invoices_submitted}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <IndianRupee className="h-4 w-4" /> Payments
                </div>
                <p className="text-2xl font-bold mt-1 text-green-600">{fmt(stats.total_payment_amount)}</p>
                <p className="text-xs text-muted-foreground">{stats.payments_received} transactions</p>
              </CardContent>
            </Card>
          </div>

          {/* Data Tabs */}
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="pos">PO Status ({pos.length})</TabsTrigger>
              <TabsTrigger value="invoices">Invoices ({invoices.length})</TabsTrigger>
              <TabsTrigger value="payments">Payments ({payments.length})</TabsTrigger>
              <TabsTrigger value="grns">GRNs ({grns.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="pos">
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>PO Number</TableHead>
                        <TableHead>Order Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Delivery Date</TableHead>
                        <TableHead>Items</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pos.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                            No purchase orders found
                          </TableCell>
                        </TableRow>
                      ) : (
                        pos.map(po => (
                          <TableRow key={po.id}>
                            <TableCell className="font-medium">{po.po_number}</TableCell>
                            <TableCell>{po.order_date || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={statusColor(po.status) as 'default' | 'secondary' | 'destructive' | 'outline'}>
                                {po.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{fmt(po.total_amount)}</TableCell>
                            <TableCell>{po.delivery_date || '-'}</TableCell>
                            <TableCell>{po.items_count}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="invoices">
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Invoice #</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead>Payment</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {invoices.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                            No invoices found
                          </TableCell>
                        </TableRow>
                      ) : (
                        invoices.map(inv => (
                          <TableRow key={inv.id}>
                            <TableCell className="font-medium">{inv.invoice_number}</TableCell>
                            <TableCell>{inv.invoice_date || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={statusColor(inv.status) as 'default' | 'secondary' | 'destructive' | 'outline'}>
                                {inv.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{fmt(inv.total_amount)}</TableCell>
                            <TableCell>{inv.due_date || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={statusColor(inv.payment_status) as 'default' | 'secondary' | 'destructive' | 'outline'}>
                                {inv.payment_status || '-'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="payments">
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Payment #</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Mode</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Reference</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {payments.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                            No payments found
                          </TableCell>
                        </TableRow>
                      ) : (
                        payments.map(pay => (
                          <TableRow key={pay.id}>
                            <TableCell className="font-medium">{pay.payment_number || '-'}</TableCell>
                            <TableCell>{pay.payment_date || '-'}</TableCell>
                            <TableCell>{pay.payment_mode}</TableCell>
                            <TableCell className="text-right font-semibold">{fmt(pay.amount)}</TableCell>
                            <TableCell>{pay.reference || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={statusColor(pay.status) as 'default' | 'secondary' | 'destructive' | 'outline'}>
                                {pay.status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="grns">
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>GRN #</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>PO #</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Received</TableHead>
                        <TableHead className="text-right">Accepted</TableHead>
                        <TableHead className="text-right">Rejected</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {grns.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                            No GRNs found
                          </TableCell>
                        </TableRow>
                      ) : (
                        grns.map(grn => (
                          <TableRow key={grn.id}>
                            <TableCell className="font-medium">{grn.grn_number}</TableCell>
                            <TableCell>{grn.grn_date || '-'}</TableCell>
                            <TableCell>{grn.po_number || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={statusColor(grn.status) as 'default' | 'secondary' | 'destructive' | 'outline'}>
                                {grn.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{grn.total_received}</TableCell>
                            <TableCell className="text-right text-green-600">{grn.total_accepted}</TableCell>
                            <TableCell className="text-right text-red-600">{grn.total_rejected}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
