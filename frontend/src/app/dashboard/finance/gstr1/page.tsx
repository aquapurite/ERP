'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { FileText, Download, Upload, CheckCircle, AlertTriangle, Calendar, Building2, RefreshCw, ExternalLink, FileJson, FileSpreadsheet } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import { formatDate, formatCurrency } from '@/lib/utils';

interface GSTR1Summary {
  return_period: string;
  filing_status: 'NOT_FILED' | 'FILED' | 'OVERDUE';
  due_date: string;
  filed_date?: string;
  arn?: string;
  total_invoices: number;
  total_taxable_value: number;
  total_igst: number;
  total_cgst: number;
  total_sgst: number;
  total_cess: number;
  total_tax: number;
  b2b_invoices: number;
  b2b_value: number;
  b2c_large_invoices: number;
  b2c_large_value: number;
  b2cs_value: number;
  credit_debit_notes: number;
  cdn_value: number;
  exports_invoices: number;
  exports_value: number;
  nil_rated_value: number;
  hsn_summary_count: number;
}

interface B2BInvoice {
  id: string;
  invoice_number: string;
  invoice_date: string;
  gstin: string;
  party_name: string;
  invoice_type: 'Regular' | 'SEZ with payment' | 'SEZ without payment' | 'Deemed Export';
  taxable_value: number;
  igst: number;
  cgst: number;
  sgst: number;
  cess: number;
  total_value: number;
  place_of_supply: string;
  reverse_charge: boolean;
  status: 'VALID' | 'ERROR' | 'WARNING';
  error_message?: string;
}

interface HSNSummary {
  hsn_code: string;
  description: string;
  uqc: string;
  total_quantity: number;
  total_value: number;
  taxable_value: number;
  igst: number;
  cgst: number;
  sgst: number;
  cess: number;
  rate: number;
}

const gstr1Api = {
  getSummary: async (period: string): Promise<GSTR1Summary> => {
    return {
      return_period: period,
      filing_status: 'NOT_FILED',
      due_date: '2024-02-11',
      total_invoices: 456,
      total_taxable_value: 12456780,
      total_igst: 1245678,
      total_cgst: 623456,
      total_sgst: 623456,
      total_cess: 45678,
      total_tax: 2538268,
      b2b_invoices: 234,
      b2b_value: 8567890,
      b2c_large_invoices: 12,
      b2c_large_value: 1234567,
      b2cs_value: 2345678,
      credit_debit_notes: 23,
      cdn_value: 456789,
      exports_invoices: 5,
      exports_value: 567890,
      nil_rated_value: 123456,
      hsn_summary_count: 45,
    };
  },
  getB2BInvoices: async (period: string): Promise<{ items: B2BInvoice[] }> => {
    return {
      items: [
        { id: '1', invoice_number: 'INV-2024-0001', invoice_date: '2024-01-05', gstin: '27AAACR5055K1ZK', party_name: 'ABC Industries Pvt Ltd', invoice_type: 'Regular', taxable_value: 125000, igst: 0, cgst: 11250, sgst: 11250, cess: 0, total_value: 147500, place_of_supply: '27-Maharashtra', reverse_charge: false, status: 'VALID' },
        { id: '2', invoice_number: 'INV-2024-0002', invoice_date: '2024-01-08', gstin: '29AABCT1332L1ZL', party_name: 'XYZ Trading Co', invoice_type: 'Regular', taxable_value: 89000, igst: 16020, cgst: 0, sgst: 0, cess: 0, total_value: 105020, place_of_supply: '29-Karnataka', reverse_charge: false, status: 'VALID' },
        { id: '3', invoice_number: 'INV-2024-0003', invoice_date: '2024-01-10', gstin: '07AABCU9603R1ZM', party_name: 'PQR Enterprises', invoice_type: 'Regular', taxable_value: 234500, igst: 42210, cgst: 0, sgst: 0, cess: 0, total_value: 276710, place_of_supply: '07-Delhi', reverse_charge: false, status: 'WARNING', error_message: 'GSTIN not verified recently' },
        { id: '4', invoice_number: 'INV-2024-0004', invoice_date: '2024-01-12', gstin: '', party_name: 'MNO Services', invoice_type: 'Regular', taxable_value: 56000, igst: 0, cgst: 5040, sgst: 5040, cess: 0, total_value: 66080, place_of_supply: '27-Maharashtra', reverse_charge: false, status: 'ERROR', error_message: 'Invalid GSTIN' },
        { id: '5', invoice_number: 'INV-2024-0005', invoice_date: '2024-01-15', gstin: '27AADCS8745F1Z8', party_name: 'DEF Solutions', invoice_type: 'SEZ with payment', taxable_value: 345000, igst: 0, cgst: 0, sgst: 0, cess: 0, total_value: 345000, place_of_supply: '27-Maharashtra', reverse_charge: false, status: 'VALID' },
      ],
    };
  },
  getHSNSummary: async (period: string): Promise<{ items: HSNSummary[] }> => {
    return {
      items: [
        { hsn_code: '84212110', description: 'Water Purifiers - RO Type', uqc: 'NOS', total_quantity: 234, total_value: 5678900, taxable_value: 4812627, igst: 456789, cgst: 216890, sgst: 216890, cess: 0, rate: 18 },
        { hsn_code: '84212120', description: 'Water Purifiers - UV Type', uqc: 'NOS', total_quantity: 156, total_value: 3456780, taxable_value: 2929475, igst: 278456, cgst: 132045, sgst: 132045, cess: 0, rate: 18 },
        { hsn_code: '84219900', description: 'Parts & Accessories', uqc: 'NOS', total_quantity: 567, total_value: 1234567, taxable_value: 1046243, igst: 94234, cgst: 47117, sgst: 47117, cess: 0, rate: 18 },
        { hsn_code: '85044010', description: 'Voltage Stabilizers', uqc: 'NOS', total_quantity: 89, total_value: 890123, taxable_value: 754341, igst: 67890, cgst: 34012, sgst: 34012, cess: 0, rate: 18 },
        { hsn_code: '99833', description: 'Installation Services', uqc: 'OTH', total_quantity: 345, total_value: 1196410, taxable_value: 1013907, igst: 91309, cgst: 45741, sgst: 45741, cess: 0, rate: 18 },
      ],
    };
  },
};

const statusColors: Record<string, string> = {
  VALID: 'bg-green-100 text-green-800',
  ERROR: 'bg-red-100 text-red-800',
  WARNING: 'bg-yellow-100 text-yellow-800',
  NOT_FILED: 'bg-yellow-100 text-yellow-800',
  FILED: 'bg-green-100 text-green-800',
  OVERDUE: 'bg-red-100 text-red-800',
};

export default function GSTR1Page() {
  const queryClient = useQueryClient();
  const [selectedPeriod, setSelectedPeriod] = useState('012024');
  const [activeTab, setActiveTab] = useState('summary');

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['gstr1-summary', selectedPeriod],
    queryFn: () => gstr1Api.getSummary(selectedPeriod),
  });

  const { data: b2bData, isLoading: b2bLoading } = useQuery({
    queryKey: ['gstr1-b2b', selectedPeriod],
    queryFn: () => gstr1Api.getB2BInvoices(selectedPeriod),
    enabled: activeTab === 'b2b',
  });

  const { data: hsnData, isLoading: hsnLoading } = useQuery({
    queryKey: ['gstr1-hsn', selectedPeriod],
    queryFn: () => gstr1Api.getHSNSummary(selectedPeriod),
    enabled: activeTab === 'hsn',
  });

  const generateMutation = useMutation({
    mutationFn: async () => {},
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstr1-summary'] });
      toast.success('GSTR-1 report generated successfully');
    },
  });

  const b2bColumns: ColumnDef<B2BInvoice>[] = [
    {
      accessorKey: 'invoice_number',
      header: 'Invoice',
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.invoice_number}</div>
          <div className="text-xs text-muted-foreground">{formatDate(row.original.invoice_date)}</div>
        </div>
      ),
    },
    {
      accessorKey: 'party_name',
      header: 'Recipient',
      cell: ({ row }) => (
        <div>
          <div className="text-sm">{row.original.party_name}</div>
          <div className="text-xs text-muted-foreground font-mono">{row.original.gstin || 'N/A'}</div>
        </div>
      ),
    },
    {
      accessorKey: 'invoice_type',
      header: 'Type',
      cell: ({ row }) => (
        <Badge variant="outline">{row.original.invoice_type}</Badge>
      ),
    },
    {
      accessorKey: 'place_of_supply',
      header: 'POS',
      cell: ({ row }) => (
        <span className="text-sm">{row.original.place_of_supply}</span>
      ),
    },
    {
      accessorKey: 'taxable_value',
      header: 'Taxable Value',
      cell: ({ row }) => (
        <span className="font-medium">{formatCurrency(row.original.taxable_value)}</span>
      ),
    },
    {
      accessorKey: 'tax',
      header: 'Tax',
      cell: ({ row }) => (
        <div className="text-sm">
          {row.original.igst > 0 ? (
            <div>IGST: {formatCurrency(row.original.igst)}</div>
          ) : (
            <>
              <div>CGST: {formatCurrency(row.original.cgst)}</div>
              <div>SGST: {formatCurrency(row.original.sgst)}</div>
            </>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'total_value',
      header: 'Total',
      cell: ({ row }) => (
        <span className="font-bold">{formatCurrency(row.original.total_value)}</span>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <div>
          <Badge className={statusColors[row.original.status]}>
            {row.original.status}
          </Badge>
          {row.original.error_message && (
            <div className="text-xs text-red-600 mt-1">{row.original.error_message}</div>
          )}
        </div>
      ),
    },
  ];

  const hsnColumns: ColumnDef<HSNSummary>[] = [
    {
      accessorKey: 'hsn_code',
      header: 'HSN Code',
      cell: ({ row }) => (
        <div>
          <div className="font-mono font-medium">{row.original.hsn_code}</div>
          <div className="text-xs text-muted-foreground max-w-48 truncate">{row.original.description}</div>
        </div>
      ),
    },
    {
      accessorKey: 'uqc',
      header: 'UQC',
    },
    {
      accessorKey: 'total_quantity',
      header: 'Qty',
      cell: ({ row }) => row.original.total_quantity.toLocaleString(),
    },
    {
      accessorKey: 'taxable_value',
      header: 'Taxable Value',
      cell: ({ row }) => formatCurrency(row.original.taxable_value),
    },
    {
      accessorKey: 'rate',
      header: 'Rate',
      cell: ({ row }) => `${row.original.rate}%`,
    },
    {
      accessorKey: 'igst',
      header: 'IGST',
      cell: ({ row }) => formatCurrency(row.original.igst),
    },
    {
      accessorKey: 'cgst',
      header: 'CGST',
      cell: ({ row }) => formatCurrency(row.original.cgst),
    },
    {
      accessorKey: 'sgst',
      header: 'SGST',
      cell: ({ row }) => formatCurrency(row.original.sgst),
    },
  ];

  const periods = [
    { value: '012024', label: 'January 2024' },
    { value: '122023', label: 'December 2023' },
    { value: '112023', label: 'November 2023' },
    { value: '102023', label: 'October 2023' },
  ];

  const validInvoices = b2bData?.items.filter((i) => i.status === 'VALID').length ?? 0;
  const errorInvoices = b2bData?.items.filter((i) => i.status === 'ERROR').length ?? 0;
  const warningInvoices = b2bData?.items.filter((i) => i.status === 'WARNING').length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTR-1 Return"
        description="Outward supplies (Sales) - Monthly/Quarterly filing"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => generateMutation.mutate()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Generate Report
            </Button>
            <Button variant="outline">
              <FileJson className="mr-2 h-4 w-4" />
              Export JSON
            </Button>
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              File Return
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

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Invoices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_invoices ?? 0}</div>
            <div className="text-xs text-muted-foreground">Across all sections</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Taxable Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.total_taxable_value ?? 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tax</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.total_tax ?? 0)}</div>
            <div className="text-xs text-muted-foreground">IGST + CGST + SGST + Cess</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">HSN Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.hsn_summary_count ?? 0}</div>
            <div className="text-xs text-muted-foreground">Unique HSN codes</div>
          </CardContent>
        </Card>
      </div>

      {/* Tax Breakup */}
      <Card>
        <CardHeader>
          <CardTitle>Tax Breakup</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-600 font-medium">IGST</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_igst ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-green-600 font-medium">CGST</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_cgst ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-sm text-purple-600 font-medium">SGST</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_sgst ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-sm text-orange-600 font-medium">Cess</div>
              <div className="text-xl font-bold">{formatCurrency(summary?.total_cess ?? 0)}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for Sections */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary">Section Summary</TabsTrigger>
          <TabsTrigger value="b2b">B2B Invoices</TabsTrigger>
          <TabsTrigger value="hsn">HSN Summary</TabsTrigger>
          <TabsTrigger value="errors">Errors & Warnings</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">B2B - Tax Invoice</CardTitle>
                <CardDescription>Supplies to registered persons</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.b2b_invoices ?? 0} invoices</div>
                <div className="text-sm text-muted-foreground">{formatCurrency(summary?.b2b_value ?? 0)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">B2C Large</CardTitle>
                <CardDescription>Inter-state B2C &gt; ₹2.5L</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.b2c_large_invoices ?? 0} invoices</div>
                <div className="text-sm text-muted-foreground">{formatCurrency(summary?.b2c_large_value ?? 0)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">B2CS</CardTitle>
                <CardDescription>Intra-state B2C supplies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(summary?.b2cs_value ?? 0)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Credit/Debit Notes</CardTitle>
                <CardDescription>Amendments to invoices</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.credit_debit_notes ?? 0} notes</div>
                <div className="text-sm text-muted-foreground">{formatCurrency(summary?.cdn_value ?? 0)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Exports</CardTitle>
                <CardDescription>Export supplies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.exports_invoices ?? 0} invoices</div>
                <div className="text-sm text-muted-foreground">{formatCurrency(summary?.exports_value ?? 0)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Nil Rated/Exempt</CardTitle>
                <CardDescription>Zero-rated supplies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(summary?.nil_rated_value ?? 0)}</div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="b2b" className="mt-4">
          <div className="flex items-center gap-4 mb-4">
            <Badge variant="outline" className="bg-green-50">
              <CheckCircle className="mr-1 h-3 w-3" /> {validInvoices} Valid
            </Badge>
            <Badge variant="outline" className="bg-yellow-50">
              <AlertTriangle className="mr-1 h-3 w-3" /> {warningInvoices} Warnings
            </Badge>
            <Badge variant="outline" className="bg-red-50">
              <AlertTriangle className="mr-1 h-3 w-3" /> {errorInvoices} Errors
            </Badge>
          </div>
          <DataTable<B2BInvoice, unknown>
            columns={b2bColumns}
            data={b2bData?.items ?? []}
            searchKey="invoice_number"
            searchPlaceholder="Search invoices..."
            isLoading={b2bLoading}
          />
        </TabsContent>

        <TabsContent value="hsn" className="mt-4">
          <DataTable<HSNSummary, unknown>
            columns={hsnColumns}
            data={hsnData?.items ?? []}
            searchKey="hsn_code"
            searchPlaceholder="Search HSN codes..."
            isLoading={hsnLoading}
          />
        </TabsContent>

        <TabsContent value="errors" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Validation Errors & Warnings</CardTitle>
              <CardDescription>Issues that need to be resolved before filing</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Issue</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {b2bData?.items.filter((i) => i.status !== 'VALID').map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Badge className={statusColors[item.status]}>{item.status}</Badge>
                      </TableCell>
                      <TableCell className="font-medium">{item.invoice_number}</TableCell>
                      <TableCell>{item.error_message}</TableCell>
                      <TableCell>
                        <Button size="sm" variant="outline">Fix</Button>
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
