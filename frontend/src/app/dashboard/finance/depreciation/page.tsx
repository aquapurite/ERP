'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Loader2,
  ChevronLeft,
  CheckCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/common';
import { depreciationRunApi } from '@/lib/api';

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);

function statusColor(status: string) {
  switch (status) {
    case 'DRAFT': return 'bg-gray-100 text-gray-800';
    case 'PROCESSING': return 'bg-blue-100 text-blue-800';
    case 'COMPLETED': return 'bg-green-100 text-green-800';
    case 'APPROVED': return 'bg-emerald-100 text-emerald-800';
    case 'CANCELLED': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default function DepreciationPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [period, setPeriod] = useState('');
  const [fiscalYear, setFiscalYear] = useState('2025-26');

  const { data: runsData, isLoading } = useQuery({
    queryKey: ['depreciation-runs'],
    queryFn: () => depreciationRunApi.list({ page: 1, size: 50 }),
  });

  const { data: runDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['depreciation-run-detail', selectedRunId],
    queryFn: () => depreciationRunApi.getById(selectedRunId!),
    enabled: !!selectedRunId,
  });

  const createMutation = useMutation({
    mutationFn: () => depreciationRunApi.create({ period, fiscal_year: fiscalYear }),
    onSuccess: (data) => {
      toast.success(data.message || 'Depreciation run created');
      setCreateOpen(false);
      setPeriod('');
      queryClient.invalidateQueries({ queryKey: ['depreciation-runs'] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to create run'),
  });

  const approveMutation = useMutation({
    mutationFn: depreciationRunApi.approve,
    onSuccess: (data) => {
      toast.success(data.message || 'Run approved');
      queryClient.invalidateQueries({ queryKey: ['depreciation-runs'] });
      queryClient.invalidateQueries({ queryKey: ['depreciation-run-detail', selectedRunId] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to approve'),
  });

  // Detail view
  if (selectedRunId) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setSelectedRunId(null)}>
            <ChevronLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <h1 className="text-2xl font-bold">
            {detailLoading ? 'Loading...' : `Run: ${runDetail?.run_number}`}
          </h1>
          {runDetail && (
            <Badge className={statusColor(runDetail.status)}>{runDetail.status}</Badge>
          )}
        </div>

        {detailLoading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
        ) : runDetail ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Period</div>
                  <div className="text-lg font-semibold">{runDetail.period}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Fiscal Year</div>
                  <div className="text-lg font-semibold">{runDetail.fiscal_year}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Run Date</div>
                  <div className="text-lg font-semibold">{runDetail.run_date}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Total Assets</div>
                  <div className="text-lg font-semibold">{runDetail.total_assets}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Total Depreciation</div>
                  <div className="text-lg font-semibold">{formatCurrency(runDetail.total_depreciation || 0)}</div>
                </CardContent>
              </Card>
            </div>

            {runDetail.status === 'COMPLETED' && (
              <Button
                onClick={() => approveMutation.mutate(selectedRunId!)}
                disabled={approveMutation.isPending}
              >
                {approveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                Approve & Post to Assets
              </Button>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Asset-wise Depreciation ({runDetail.entries?.length || 0})</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset Code</TableHead>
                      <TableHead>Asset Name</TableHead>
                      <TableHead>Method</TableHead>
                      <TableHead className="text-right">Acquisition Cost</TableHead>
                      <TableHead className="text-right">Accum. Depreciation</TableHead>
                      <TableHead className="text-right">Net Book Value</TableHead>
                      <TableHead className="text-right">Monthly Dep.</TableHead>
                      <TableHead className="text-right">Useful Life (Months)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(runDetail.entries || []).map((e: any) => (
                      <TableRow key={e.id}>
                        <TableCell className="font-mono text-sm">{e.asset_code}</TableCell>
                        <TableCell>{e.asset_name}</TableCell>
                        <TableCell>{e.depreciation_method}</TableCell>
                        <TableCell className="text-right">{formatCurrency(e.acquisition_cost)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(e.accumulated_depreciation)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(e.net_book_value)}</TableCell>
                        <TableCell className="text-right font-medium text-blue-600">{formatCurrency(e.depreciation_amount)}</TableCell>
                        <TableCell className="text-right">{e.useful_life_months}</TableCell>
                      </TableRow>
                    ))}
                    {/* Summary */}
                    {(runDetail.entries || []).length > 0 && (
                      <TableRow className="bg-muted/50 font-bold">
                        <TableCell colSpan={3}>TOTAL</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency((runDetail.entries || []).reduce((s: number, e: any) => s + (e.acquisition_cost || 0), 0))}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency((runDetail.entries || []).reduce((s: number, e: any) => s + (e.accumulated_depreciation || 0), 0))}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency((runDetail.entries || []).reduce((s: number, e: any) => s + (e.net_book_value || 0), 0))}
                        </TableCell>
                        <TableCell className="text-right text-blue-600">
                          {formatCurrency(runDetail.total_depreciation || 0)}
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    );
  }

  // List view
  return (
    <div className="space-y-6">
      <PageHeader
        title="Depreciation Runs"
        description="Auto depreciation processing for fixed assets (SAP AFAB)"
      />

      <div className="flex justify-end">
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" /> New Depreciation Run</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Depreciation Run</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Period (YYYY-MM)</Label>
                <Input
                  placeholder="e.g. 2026-03"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                />
              </div>
              <div>
                <Label>Fiscal Year</Label>
                <Input
                  placeholder="e.g. 2025-26"
                  value={fiscalYear}
                  onChange={(e) => setFiscalYear(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={!period || !fiscalYear || createMutation.isPending}
              >
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Run Depreciation
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run #</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Fiscal Year</TableHead>
                  <TableHead>Run Date</TableHead>
                  <TableHead className="text-right">Assets</TableHead>
                  <TableHead className="text-right">Total Depreciation</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(runsData?.items || []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No depreciation runs yet. Create one to calculate depreciation for all active assets.
                    </TableCell>
                  </TableRow>
                ) : (
                  (runsData?.items || []).map((r: any) => (
                    <TableRow
                      key={r.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedRunId(r.id)}
                    >
                      <TableCell className="font-medium">{r.run_number}</TableCell>
                      <TableCell>{r.period}</TableCell>
                      <TableCell>{r.fiscal_year}</TableCell>
                      <TableCell>{r.run_date}</TableCell>
                      <TableCell className="text-right">{r.total_assets}</TableCell>
                      <TableCell className="text-right">{formatCurrency(r.total_depreciation || 0)}</TableCell>
                      <TableCell>
                        <Badge className={statusColor(r.status)}>{r.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
