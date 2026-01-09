'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { FileText, Download, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/data-table/data-table';
import { PageHeader } from '@/components/common';
import { formatCurrency } from '@/lib/utils';

interface HSNItem {
  id: string;
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

interface HSNSummaryStats {
  total_hsn_codes: number;
  total_taxable_value: number;
  total_tax: number;
  gst_5_value: number;
  gst_12_value: number;
  gst_18_value: number;
  gst_28_value: number;
}

const hsnApi = {
  getStats: async (period: string): Promise<HSNSummaryStats> => {
    return {
      total_hsn_codes: 45,
      total_taxable_value: 12456780,
      total_tax: 2241220,
      gst_5_value: 234567,
      gst_12_value: 567890,
      gst_18_value: 10234567,
      gst_28_value: 1419756,
    };
  },
  getOutwardHSN: async (period: string): Promise<{ items: HSNItem[] }> => {
    return {
      items: [
        { id: '1', hsn_code: '84212110', description: 'Water Purifiers - RO Type', uqc: 'NOS', total_quantity: 234, total_value: 5678900, taxable_value: 4812627, igst: 456789, cgst: 216890, sgst: 216890, cess: 0, rate: 18 },
        { id: '2', hsn_code: '84212120', description: 'Water Purifiers - UV Type', uqc: 'NOS', total_quantity: 156, total_value: 3456780, taxable_value: 2929475, igst: 278456, cgst: 132045, sgst: 132045, cess: 0, rate: 18 },
        { id: '3', hsn_code: '84219900', description: 'Parts & Accessories for Water Purifiers', uqc: 'NOS', total_quantity: 567, total_value: 1234567, taxable_value: 1046243, igst: 94234, cgst: 47117, sgst: 47117, cess: 0, rate: 18 },
        { id: '4', hsn_code: '85044010', description: 'Static Converters (Voltage Stabilizers)', uqc: 'NOS', total_quantity: 89, total_value: 890123, taxable_value: 754341, igst: 67890, cgst: 34012, sgst: 34012, cess: 0, rate: 18 },
        { id: '5', hsn_code: '99833', description: 'Installation Services', uqc: 'OTH', total_quantity: 345, total_value: 1196410, taxable_value: 1013907, igst: 91309, cgst: 45741, sgst: 45741, cess: 0, rate: 18 },
        { id: '6', hsn_code: '99872', description: 'AMC/Repair Services', uqc: 'OTH', total_quantity: 456, total_value: 890000, taxable_value: 754237, igst: 67956, cgst: 34089, sgst: 34089, cess: 0, rate: 18 },
      ],
    };
  },
  getInwardHSN: async (period: string): Promise<{ items: HSNItem[] }> => {
    return {
      items: [
        { id: '1', hsn_code: '84212110', description: 'Water Purifier Units', uqc: 'NOS', total_quantity: 300, total_value: 4500000, taxable_value: 3813559, igst: 686440, cgst: 0, sgst: 0, cess: 0, rate: 18 },
        { id: '2', hsn_code: '39269099', description: 'Plastic Components', uqc: 'KGS', total_quantity: 1200, total_value: 890000, taxable_value: 754237, igst: 135763, cgst: 0, sgst: 0, cess: 0, rate: 18 },
        { id: '3', hsn_code: '84818090', description: 'Valves & Fittings', uqc: 'NOS', total_quantity: 2500, total_value: 675000, taxable_value: 572034, igst: 0, cgst: 51483, sgst: 51483, cess: 0, rate: 18 },
        { id: '4', hsn_code: '85371000', description: 'Control Boards/PCB', uqc: 'NOS', total_quantity: 450, total_value: 1125000, taxable_value: 953390, igst: 171610, cgst: 0, sgst: 0, cess: 0, rate: 18 },
        { id: '5', hsn_code: '73182900', description: 'Screws, Bolts, Nuts', uqc: 'KGS', total_quantity: 500, total_value: 125000, taxable_value: 105932, igst: 0, cgst: 9534, sgst: 9534, cess: 0, rate: 18 },
      ],
    };
  },
};

export default function HSNSummaryPage() {
  const [selectedPeriod, setSelectedPeriod] = useState('012024');
  const [activeTab, setActiveTab] = useState('outward');

  const { data: stats } = useQuery({
    queryKey: ['hsn-stats', selectedPeriod],
    queryFn: () => hsnApi.getStats(selectedPeriod),
  });

  const { data: outwardData, isLoading: outwardLoading } = useQuery({
    queryKey: ['hsn-outward', selectedPeriod],
    queryFn: () => hsnApi.getOutwardHSN(selectedPeriod),
    enabled: activeTab === 'outward',
  });

  const { data: inwardData, isLoading: inwardLoading } = useQuery({
    queryKey: ['hsn-inward', selectedPeriod],
    queryFn: () => hsnApi.getInwardHSN(selectedPeriod),
    enabled: activeTab === 'inward',
  });

  const columns: ColumnDef<HSNItem>[] = [
    {
      accessorKey: 'hsn_code',
      header: 'HSN/SAC',
      cell: ({ row }) => (
        <div>
          <div className="font-mono font-medium">{row.original.hsn_code}</div>
          <div className="text-xs text-muted-foreground max-w-56 truncate">{row.original.description}</div>
        </div>
      ),
    },
    {
      accessorKey: 'uqc',
      header: 'UQC',
      cell: ({ row }) => <Badge variant="outline">{row.original.uqc}</Badge>,
    },
    {
      accessorKey: 'total_quantity',
      header: 'Quantity',
      cell: ({ row }) => row.original.total_quantity.toLocaleString(),
    },
    {
      accessorKey: 'taxable_value',
      header: 'Taxable Value',
      cell: ({ row }) => <span className="font-medium">{formatCurrency(row.original.taxable_value)}</span>,
    },
    {
      accessorKey: 'rate',
      header: 'Rate',
      cell: ({ row }) => (
        <Badge className="bg-blue-100 text-blue-800">{row.original.rate}%</Badge>
      ),
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
    {
      accessorKey: 'total_value',
      header: 'Total Value',
      cell: ({ row }) => <span className="font-bold">{formatCurrency(row.original.total_value)}</span>,
    },
  ];

  const periods = [
    { value: '012024', label: 'January 2024' },
    { value: '122023', label: 'December 2023' },
    { value: '112023', label: 'November 2023' },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="HSN Summary"
        description="HSN/SAC wise tax summary for GST returns"
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Summary
          </Button>
        }
      />

      {/* Period Selector */}
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

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total HSN Codes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_hsn_codes ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Taxable Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats?.total_taxable_value ?? 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tax</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats?.total_tax ?? 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Tax Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {((stats?.total_tax ?? 0) / (stats?.total_taxable_value ?? 1) * 100).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tax Rate Breakup */}
      <Card>
        <CardHeader>
          <CardTitle>Tax Rate Wise Breakup</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-green-600 font-medium">5% GST</div>
              <div className="text-xl font-bold">{formatCurrency(stats?.gst_5_value ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-600 font-medium">12% GST</div>
              <div className="text-xl font-bold">{formatCurrency(stats?.gst_12_value ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-sm text-purple-600 font-medium">18% GST</div>
              <div className="text-xl font-bold">{formatCurrency(stats?.gst_18_value ?? 0)}</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-sm text-orange-600 font-medium">28% GST</div>
              <div className="text-xl font-bold">{formatCurrency(stats?.gst_28_value ?? 0)}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* HSN Details */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="outward">Outward HSN (Sales)</TabsTrigger>
          <TabsTrigger value="inward">Inward HSN (Purchases)</TabsTrigger>
        </TabsList>

        <TabsContent value="outward" className="mt-4">
          <DataTable<HSNItem, unknown>
            columns={columns}
            data={outwardData?.items ?? []}
            searchKey="hsn_code"
            searchPlaceholder="Search HSN codes..."
            isLoading={outwardLoading}
          />
        </TabsContent>

        <TabsContent value="inward" className="mt-4">
          <DataTable<HSNItem, unknown>
            columns={columns}
            data={inwardData?.items ?? []}
            searchKey="hsn_code"
            searchPlaceholder="Search HSN codes..."
            isLoading={inwardLoading}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
