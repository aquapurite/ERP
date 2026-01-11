'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Download, Upload, CheckCircle, AlertTriangle, Calendar, IndianRupee, Calculator, CreditCard, RefreshCw, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/common';
import { formatCurrency } from '@/lib/utils';

interface GSTR3BSummary {
  return_period: string;
  filing_status: 'NOT_FILED' | 'FILED' | 'OVERDUE';
  due_date: string;
  filed_date?: string;
  arn?: string;
  // 3.1 Outward Supplies
  outward_taxable: { taxable_value: number; igst: number; cgst: number; sgst: number; cess: number };
  outward_zero_rated: { taxable_value: number; igst: number };
  outward_nil_rated: { taxable_value: number };
  outward_exempt: { taxable_value: number };
  outward_non_gst: { taxable_value: number };
  // 3.2 Inter-state supplies
  inter_state_unreg: { taxable_value: number; igst: number };
  inter_state_comp: { taxable_value: number; igst: number };
  inter_state_uin: { taxable_value: number; igst: number };
  // 4. ITC Available
  itc_igst: number;
  itc_cgst: number;
  itc_sgst: number;
  itc_cess: number;
  itc_ineligible_igst: number;
  itc_ineligible_cgst: number;
  itc_ineligible_sgst: number;
  // 5. Exempt/Nil/Non-GST inward supplies
  inward_exempt: number;
  inward_nil: number;
  inward_non_gst: number;
  // 6. Tax Payable
  tax_payable_igst: number;
  tax_payable_cgst: number;
  tax_payable_sgst: number;
  tax_payable_cess: number;
  // ITC utilized
  itc_utilized_igst: number;
  itc_utilized_cgst: number;
  itc_utilized_sgst: number;
  itc_utilized_cess: number;
  // Cash payment
  cash_igst: number;
  cash_cgst: number;
  cash_sgst: number;
  cash_cess: number;
  // Interest/Late fee
  interest: number;
  late_fee: number;
}

const gstr3bApi = {
  getSummary: async (period: string): Promise<GSTR3BSummary> => {
    return {
      return_period: period,
      filing_status: 'NOT_FILED',
      due_date: '2024-02-20',
      outward_taxable: { taxable_value: 12456780, igst: 1245678, cgst: 623456, sgst: 623456, cess: 45678 },
      outward_zero_rated: { taxable_value: 567890, igst: 0 },
      outward_nil_rated: { taxable_value: 123456 },
      outward_exempt: { taxable_value: 89012 },
      outward_non_gst: { taxable_value: 45678 },
      inter_state_unreg: { taxable_value: 234567, igst: 42222 },
      inter_state_comp: { taxable_value: 56789, igst: 10222 },
      inter_state_uin: { taxable_value: 0, igst: 0 },
      itc_igst: 1123456,
      itc_cgst: 567890,
      itc_sgst: 567890,
      itc_cess: 34567,
      itc_ineligible_igst: 12345,
      itc_ineligible_cgst: 6789,
      itc_ineligible_sgst: 6789,
      inward_exempt: 45678,
      inward_nil: 23456,
      inward_non_gst: 12345,
      tax_payable_igst: 1245678,
      tax_payable_cgst: 623456,
      tax_payable_sgst: 623456,
      tax_payable_cess: 45678,
      itc_utilized_igst: 1123456,
      itc_utilized_cgst: 567890,
      itc_utilized_sgst: 567890,
      itc_utilized_cess: 34567,
      cash_igst: 122222,
      cash_cgst: 55566,
      cash_sgst: 55566,
      cash_cess: 11111,
      interest: 0,
      late_fee: 0,
    };
  },
};

const statusColors: Record<string, string> = {
  NOT_FILED: 'bg-yellow-100 text-yellow-800',
  FILED: 'bg-green-100 text-green-800',
  OVERDUE: 'bg-red-100 text-red-800',
};

export default function GSTR3BPage() {
  const queryClient = useQueryClient();
  const [selectedPeriod, setSelectedPeriod] = useState('012024');
  const [isPaymentOpen, setIsPaymentOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');

  const { data: summary, isLoading } = useQuery({
    queryKey: ['gstr3b-summary', selectedPeriod],
    queryFn: () => gstr3bApi.getSummary(selectedPeriod),
  });

  const generateMutation = useMutation({
    mutationFn: async () => {},
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstr3b-summary'] });
      toast.success('GSTR-3B report generated');
    },
  });

  const fileMutation = useMutation({
    mutationFn: async () => {},
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstr3b-summary'] });
      toast.success('GSTR-3B filed successfully');
      setIsPaymentOpen(false);
    },
  });

  const periods = [
    { value: '012024', label: 'January 2024' },
    { value: '122023', label: 'December 2023' },
    { value: '112023', label: 'November 2023' },
    { value: '102023', label: 'October 2023' },
  ];

  const totalTaxPayable = (summary?.tax_payable_igst ?? 0) + (summary?.tax_payable_cgst ?? 0) +
    (summary?.tax_payable_sgst ?? 0) + (summary?.tax_payable_cess ?? 0);
  const totalITCUtilized = (summary?.itc_utilized_igst ?? 0) + (summary?.itc_utilized_cgst ?? 0) +
    (summary?.itc_utilized_sgst ?? 0) + (summary?.itc_utilized_cess ?? 0);
  const totalCashPayment = (summary?.cash_igst ?? 0) + (summary?.cash_cgst ?? 0) +
    (summary?.cash_sgst ?? 0) + (summary?.cash_cess ?? 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTR-3B Return"
        description="Summary return - Monthly filing with tax payment"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => generateMutation.mutate()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Generate
            </Button>
            <Button variant="outline">
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>
            <Button onClick={() => setIsPaymentOpen(true)}>
              <Upload className="mr-2 h-4 w-4" />
              File & Pay
            </Button>
          </div>
        }
      />

      {/* Period Selector & Status */}
      <div className="flex items-center justify-between">
        <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            {periods.map((p) => (
              <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Due: {summary?.due_date}</span>
          </div>
          <Badge className={statusColors[summary?.filing_status ?? 'NOT_FILED']}>
            {summary?.filing_status?.replace(/_/g, ' ')}
          </Badge>
        </div>
      </div>

      {/* Payment Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-blue-800">Total Tax Payable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">{formatCurrency(totalTaxPayable)}</div>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-800">ITC Utilized</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">{formatCurrency(totalITCUtilized)}</div>
          </CardContent>
        </Card>
        <Card className="bg-orange-50 border-orange-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-orange-800">Cash Payment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900">{formatCurrency(totalCashPayment)}</div>
          </CardContent>
        </Card>
        <Card className="bg-purple-50 border-purple-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-purple-800">Interest + Late Fee</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">
              {formatCurrency((summary?.interest ?? 0) + (summary?.late_fee ?? 0))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary">Return Summary</TabsTrigger>
          <TabsTrigger value="outward">3.1 Outward Supplies</TabsTrigger>
          <TabsTrigger value="itc">4. ITC Available</TabsTrigger>
          <TabsTrigger value="payment">6. Tax Payment</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GSTR-3B Summary</CardTitle>
              <CardDescription>Overview of all sections</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Section</TableHead>
                    <TableHead className="text-right">Taxable Value</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="font-medium">
                    <TableCell>3.1(a) Outward Taxable Supplies</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.sgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.cess ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>3.1(b) Zero Rated Supplies</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_zero_rated.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_zero_rated.igst ?? 0)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>3.1(c) Nil Rated Supplies</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_nil_rated.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>3.1(d) Exempt Supplies</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_exempt.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                  <TableRow className="bg-muted/50">
                    <TableCell className="font-bold">4. ITC Available</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.itc_igst ?? 0)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.itc_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.itc_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.itc_cess ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow className="bg-blue-50">
                    <TableCell className="font-bold">6.1 Tax Payable</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.tax_payable_igst ?? 0)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.tax_payable_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.tax_payable_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(summary?.tax_payable_cess ?? 0)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="outward" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>3.1 Details of Outward Supplies</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nature of Supplies</TableHead>
                    <TableHead className="text-right">Taxable Value</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>
                      <div>(a) Outward Taxable Supplies (other than zero rated, nil rated and exempted)</div>
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_taxable.sgst ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(b) Outward taxable supplies (zero rated)</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_zero_rated.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_zero_rated.igst ?? 0)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(c) Other outward supplies (nil rated, exempted)</TableCell>
                    <TableCell className="text-right">{formatCurrency((summary?.outward_nil_rated.taxable_value ?? 0) + (summary?.outward_exempt.taxable_value ?? 0))}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(d) Inward supplies (liable to reverse charge)</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(e) Non-GST outward supplies</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.outward_non_gst.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>3.2 Inter-State Supplies to Unregistered Persons, Composition Dealers, UIN Holders</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nature of Supplies</TableHead>
                    <TableHead className="text-right">Taxable Value</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>Supplies to Unregistered Persons</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.inter_state_unreg.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.inter_state_unreg.igst ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Supplies to Composition Dealers</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.inter_state_comp.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.inter_state_comp.igst ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Supplies to UIN Holders</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.inter_state_uin.taxable_value ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.inter_state_uin.igst ?? 0)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="itc" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>4. Eligible ITC</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Details</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="font-medium">
                    <TableCell>(A) ITC Available</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_cess ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="pl-8">Import of goods</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="pl-8">Import of services</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="pl-8">Inward supplies liable to reverse charge</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="pl-8">Inward supplies from ISD</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                    <TableCell className="text-right">0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="pl-8">All other ITC</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_cess ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow className="text-red-600">
                    <TableCell>(B) ITC Reversed</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_ineligible_igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_ineligible_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_ineligible_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right">0</TableCell>
                  </TableRow>
                  <TableRow className="font-bold bg-green-50">
                    <TableCell>(C) Net ITC Available (A - B)</TableCell>
                    <TableCell className="text-right">{formatCurrency((summary?.itc_igst ?? 0) - (summary?.itc_ineligible_igst ?? 0))}</TableCell>
                    <TableCell className="text-right">{formatCurrency((summary?.itc_cgst ?? 0) - (summary?.itc_ineligible_cgst ?? 0))}</TableCell>
                    <TableCell className="text-right">{formatCurrency((summary?.itc_sgst ?? 0) - (summary?.itc_ineligible_sgst ?? 0))}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.itc_cess ?? 0)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payment" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>6. Payment of Tax</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="font-medium">
                    <TableCell>6.1 Tax Payable</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.tax_payable_igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.tax_payable_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.tax_payable_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.tax_payable_cess ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="text-green-600">6.2 ITC Utilized</TableCell>
                    <TableCell className="text-right text-green-600">{formatCurrency(summary?.itc_utilized_igst ?? 0)}</TableCell>
                    <TableCell className="text-right text-green-600">{formatCurrency(summary?.itc_utilized_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right text-green-600">{formatCurrency(summary?.itc_utilized_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right text-green-600">{formatCurrency(summary?.itc_utilized_cess ?? 0)}</TableCell>
                  </TableRow>
                  <TableRow className="font-bold bg-orange-50">
                    <TableCell>6.3 Tax Paid in Cash</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.cash_igst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.cash_cgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.cash_sgst ?? 0)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(summary?.cash_cess ?? 0)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Interest</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(summary?.interest ?? 0)}</div>
                <p className="text-sm text-muted-foreground">18% p.a. on delayed payment</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Late Fee</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(summary?.late_fee ?? 0)}</div>
                <p className="text-sm text-muted-foreground">₹50/day CGST + ₹50/day SGST</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Payment Dialog */}
      <Dialog open={isPaymentOpen} onOpenChange={setIsPaymentOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>File GSTR-3B & Make Payment</DialogTitle>
            <DialogDescription>
              Review and confirm the payment details before filing
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Total Tax Payable</Label>
              <div className="text-2xl font-bold">{formatCurrency(totalTaxPayable)}</div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">ITC Utilized</Label>
                <div className="font-medium text-green-600">{formatCurrency(totalITCUtilized)}</div>
              </div>
              <div>
                <Label className="text-muted-foreground">Cash Payment</Label>
                <div className="font-medium text-orange-600">{formatCurrency(totalCashPayment)}</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">Interest</Label>
                <div className="font-medium">{formatCurrency(summary?.interest ?? 0)}</div>
              </div>
              <div>
                <Label className="text-muted-foreground">Late Fee</Label>
                <div className="font-medium">{formatCurrency(summary?.late_fee ?? 0)}</div>
              </div>
            </div>
            <div className="border-t pt-4">
              <div className="flex justify-between items-center">
                <Label className="text-lg">Total Amount</Label>
                <div className="text-2xl font-bold text-primary">
                  {formatCurrency(totalCashPayment + (summary?.interest ?? 0) + (summary?.late_fee ?? 0))}
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPaymentOpen(false)}>Cancel</Button>
            <Button onClick={() => fileMutation.mutate()}>
              <CreditCard className="mr-2 h-4 w-4" />
              Pay & File
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
