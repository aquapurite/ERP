'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Download, RefreshCw, CheckCircle, AlertTriangle, Calendar } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import { PageHeader } from '@/components/common';
import { formatCurrency } from '@/lib/utils';

interface GSTR2ASummary {
  return_period: string;
  last_synced: string;
  total_invoices: number;
  matched_invoices: number;
  mismatched_invoices: number;
  new_invoices: number;
  total_taxable_value: number;
  total_igst: number;
  total_cgst: number;
  total_sgst: number;
}

interface GSTR2AInvoice {
  id: string;
  gstin: string;
  party_name: string;
  invoice_number: string;
  invoice_date: string;
  taxable_value: number;
  igst: number;
  cgst: number;
  sgst: number;
  total_value: number;
  match_status: 'MATCHED' | 'MISMATCHED' | 'NEW' | 'MISSING';
  mismatch_reason?: string;
}

const gstr2aApi = {
  getSummary: async (period: string): Promise<GSTR2ASummary> => {
    return {
      return_period: period,
      last_synced: '2024-01-28 14:30:00',
      total_invoices: 156,
      matched_invoices: 142,
      mismatched_invoices: 8,
      new_invoices: 6,
      total_taxable_value: 8567890,
      total_igst: 789012,
      total_cgst: 398765,
      total_sgst: 398765,
    };
  },
  getInvoices: async (period: string): Promise<{ items: GSTR2AInvoice[] }> => {
    return {
      items: [
        { id: '1', gstin: '27AAACR5055K1ZK', party_name: 'ABC Industries Pvt Ltd', invoice_number: 'PI-2024-0101', invoice_date: '2024-01-05', taxable_value: 125000, igst: 0, cgst: 11250, sgst: 11250, total_value: 147500, match_status: 'MATCHED' },
        { id: '2', gstin: '29AABCT1332L1ZL', party_name: 'XYZ Trading Co', invoice_number: 'INV-456', invoice_date: '2024-01-08', taxable_value: 89000, igst: 16020, cgst: 0, sgst: 0, total_value: 105020, match_status: 'MISMATCHED', mismatch_reason: 'Invoice amount differs by ₹1,200' },
        { id: '3', gstin: '07AABCU9603R1ZM', party_name: 'PQR Enterprises', invoice_number: 'B-789', invoice_date: '2024-01-10', taxable_value: 234500, igst: 42210, cgst: 0, sgst: 0, total_value: 276710, match_status: 'NEW' },
        { id: '4', gstin: '24AADCS8745F1Z8', party_name: 'MNO Services', invoice_number: 'TAX/23-24/987', invoice_date: '2024-01-12', taxable_value: 56000, igst: 0, cgst: 5040, sgst: 5040, total_value: 66080, match_status: 'MATCHED' },
        { id: '5', gstin: '33AABCP4321M1ZX', party_name: 'DEF Solutions', invoice_number: 'GST-001-2024', invoice_date: '2024-01-15', taxable_value: 178000, igst: 32040, cgst: 0, sgst: 0, total_value: 210040, match_status: 'MISMATCHED', mismatch_reason: 'GSTIN not matching' },
      ],
    };
  },
};

const matchStatusColors: Record<string, string> = {
  MATCHED: 'bg-green-100 text-green-800',
  MISMATCHED: 'bg-red-100 text-red-800',
  NEW: 'bg-blue-100 text-blue-800',
  MISSING: 'bg-yellow-100 text-yellow-800',
};

export default function GSTR2APage() {
  const [selectedPeriod, setSelectedPeriod] = useState('012024');

  const { data: summary } = useQuery({
    queryKey: ['gstr2a-summary', selectedPeriod],
    queryFn: () => gstr2aApi.getSummary(selectedPeriod),
  });

  const { data: invoicesData, isLoading } = useQuery({
    queryKey: ['gstr2a-invoices', selectedPeriod],
    queryFn: () => gstr2aApi.getInvoices(selectedPeriod),
  });

  const periods = [
    { value: '012024', label: 'January 2024' },
    { value: '122023', label: 'December 2023' },
    { value: '112023', label: 'November 2023' },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTR-2A"
        description="Auto-populated purchase register from supplier filings"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Sync from GST Portal
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      {/* Period Selector */}
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
        <div className="text-sm text-muted-foreground">
          Last synced: {summary?.last_synced}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Invoices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_invoices ?? 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-800">Matched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">{summary?.matched_invoices ?? 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-800">Mismatched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">{summary?.mismatched_invoices ?? 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-800">New (Not in Books)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">{summary?.new_invoices ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* ITC Summary */}
      <Card>
        <CardHeader>
          <CardTitle>ITC Available as per GSTR-2A</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground">Taxable Value</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_taxable_value ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-600">IGST</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_igst ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-green-600">CGST</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_cgst ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-sm text-purple-600">SGST</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_sgst ?? 0)}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Invoice List */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice Details</CardTitle>
          <CardDescription>Invoices reported by your suppliers</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Supplier</TableHead>
                <TableHead>Invoice</TableHead>
                <TableHead className="text-right">Taxable Value</TableHead>
                <TableHead className="text-right">Tax</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoicesData?.items.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell>
                    <div>{invoice.party_name}</div>
                    <div className="text-xs text-muted-foreground font-mono">{invoice.gstin}</div>
                  </TableCell>
                  <TableCell>
                    <div>{invoice.invoice_number}</div>
                    <div className="text-xs text-muted-foreground">{invoice.invoice_date}</div>
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(invoice.taxable_value)}</TableCell>
                  <TableCell className="text-right">
                    {invoice.igst > 0 ? (
                      <span>IGST: {formatCurrency(invoice.igst)}</span>
                    ) : (
                      <span>C+S: {formatCurrency(invoice.cgst + invoice.sgst)}</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(invoice.total_value)}</TableCell>
                  <TableCell>
                    <Badge className={matchStatusColors[invoice.match_status]}>
                      {invoice.match_status}
                    </Badge>
                    {invoice.mismatch_reason && (
                      <div className="text-xs text-red-600 mt-1">{invoice.mismatch_reason}</div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
