'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Loader2,
  ChevronLeft,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { PageHeader } from '@/components/common';
import { agingApi, dunningApi } from '@/lib/api';

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);

function severityColor(total: number, days90: number) {
  if (days90 > 0) return 'text-red-600 font-bold';
  if (total > 100000) return 'text-orange-600 font-semibold';
  if (total > 50000) return 'text-yellow-600';
  return 'text-green-600';
}

function dunningLevelBadge(level: number) {
  switch (level) {
    case 1: return <Badge className="bg-yellow-100 text-yellow-800">Level 1</Badge>;
    case 2: return <Badge className="bg-orange-100 text-orange-800">Level 2</Badge>;
    case 3: return <Badge className="bg-red-100 text-red-800">Level 3</Badge>;
    case 4: return <Badge className="bg-red-200 text-red-900">Level 4 - Critical</Badge>;
    default: return <Badge>{level}</Badge>;
  }
}

export default function AgingReportPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [minDays, setMinDays] = useState('30');
  const [dunningNotes, setDunningNotes] = useState('');

  const { data: agingData, isLoading: agingLoading } = useQuery({
    queryKey: ['aging-report'],
    queryFn: agingApi.getReport,
  });

  const { data: dunningRuns, isLoading: dunningLoading } = useQuery({
    queryKey: ['dunning-runs'],
    queryFn: () => dunningApi.list({ page: 1, size: 50 }),
  });

  const { data: runDetail, isLoading: runDetailLoading } = useQuery({
    queryKey: ['dunning-run-detail', selectedRunId],
    queryFn: () => dunningApi.getById(selectedRunId!),
    enabled: !!selectedRunId,
  });

  const createDunningMutation = useMutation({
    mutationFn: dunningApi.create,
    onSuccess: (data) => {
      toast.success(data.message || 'Dunning run created');
      setCreateOpen(false);
      setMinDays('30');
      setDunningNotes('');
      queryClient.invalidateQueries({ queryKey: ['dunning-runs'] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to create dunning run'),
  });

  const summary = agingData?.summary;

  return (
    <div className="space-y-6">
      <PageHeader
        title="AR Aging & Dunning"
        description="Accounts receivable aging analysis and dunning management (SAP F150)"
      />

      <Tabs defaultValue="aging">
        <TabsList>
          <TabsTrigger value="aging">Aging Report</TabsTrigger>
          <TabsTrigger value="dunning">Dunning Runs</TabsTrigger>
        </TabsList>

        {/* AGING REPORT TAB */}
        <TabsContent value="aging" className="space-y-6">
          {agingLoading ? (
            <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
          ) : (
            <>
              {/* Summary Cards */}
              {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">Current</div>
                      <div className="text-lg font-bold text-green-600">{formatCurrency(summary.current)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">1-30 Days</div>
                      <div className="text-lg font-bold text-yellow-600">{formatCurrency(summary.days_1_30)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">31-60 Days</div>
                      <div className="text-lg font-bold text-orange-600">{formatCurrency(summary.days_31_60)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">61-90 Days</div>
                      <div className="text-lg font-bold text-orange-700">{formatCurrency(summary.days_61_90)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">90+ Days</div>
                      <div className="text-lg font-bold text-red-600">{formatCurrency(summary.days_90_plus)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">Total Outstanding</div>
                      <div className="text-lg font-bold">{formatCurrency(summary.total)}</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-xs text-muted-foreground">Customers</div>
                      <div className="text-lg font-bold">{summary.total_customers}</div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Aging Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Customer-wise Aging</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Customer / Dealer</TableHead>
                        <TableHead className="text-right">Invoices</TableHead>
                        <TableHead className="text-right bg-green-50">Current</TableHead>
                        <TableHead className="text-right bg-yellow-50">1-30 Days</TableHead>
                        <TableHead className="text-right bg-orange-50">31-60 Days</TableHead>
                        <TableHead className="text-right bg-orange-100">61-90 Days</TableHead>
                        <TableHead className="text-right bg-red-50">90+ Days</TableHead>
                        <TableHead className="text-right font-bold">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(agingData?.items || []).length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                            No outstanding receivables found.
                          </TableCell>
                        </TableRow>
                      ) : (
                        (agingData?.items || []).map((item: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{item.entity_name}</TableCell>
                            <TableCell className="text-right">{item.invoice_count}</TableCell>
                            <TableCell className="text-right text-green-600">{item.current > 0 ? formatCurrency(item.current) : '-'}</TableCell>
                            <TableCell className="text-right text-yellow-600">{item.days_1_30 > 0 ? formatCurrency(item.days_1_30) : '-'}</TableCell>
                            <TableCell className="text-right text-orange-600">{item.days_31_60 > 0 ? formatCurrency(item.days_31_60) : '-'}</TableCell>
                            <TableCell className="text-right text-orange-700">{item.days_61_90 > 0 ? formatCurrency(item.days_61_90) : '-'}</TableCell>
                            <TableCell className="text-right text-red-600 font-medium">{item.days_90_plus > 0 ? formatCurrency(item.days_90_plus) : '-'}</TableCell>
                            <TableCell className={`text-right ${severityColor(item.total, item.days_90_plus)}`}>
                              {formatCurrency(item.total)}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                      {/* Summary row */}
                      {summary && (agingData?.items || []).length > 0 && (
                        <TableRow className="bg-muted/50 font-bold">
                          <TableCell>TOTAL</TableCell>
                          <TableCell></TableCell>
                          <TableCell className="text-right">{formatCurrency(summary.current)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(summary.days_1_30)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(summary.days_31_60)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(summary.days_61_90)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(summary.days_90_plus)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(summary.total)}</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* DUNNING RUNS TAB */}
        <TabsContent value="dunning" className="space-y-6">
          {selectedRunId ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Button variant="ghost" size="sm" onClick={() => setSelectedRunId(null)}>
                  <ChevronLeft className="h-4 w-4 mr-1" /> Back
                </Button>
                <h2 className="text-xl font-bold">
                  {runDetailLoading ? 'Loading...' : `Dunning Run: ${runDetail?.run_number}`}
                </h2>
              </div>

              {runDetailLoading ? (
                <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
              ) : runDetail ? (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card><CardContent className="pt-4"><div className="text-sm text-muted-foreground">Run Date</div><div className="text-lg font-semibold">{runDetail.run_date}</div></CardContent></Card>
                    <Card><CardContent className="pt-4"><div className="text-sm text-muted-foreground">Customers</div><div className="text-lg font-semibold">{runDetail.total_customers}</div></CardContent></Card>
                    <Card><CardContent className="pt-4"><div className="text-sm text-muted-foreground">Total Amount</div><div className="text-lg font-semibold">{formatCurrency(runDetail.total_amount)}</div></CardContent></Card>
                    <Card><CardContent className="pt-4"><div className="text-sm text-muted-foreground">Status</div><div className="text-lg font-semibold">{runDetail.status}</div></CardContent></Card>
                  </div>
                  <Card>
                    <CardHeader><CardTitle>Overdue Invoices ({runDetail.items?.length || 0})</CardTitle></CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Invoice #</TableHead>
                            <TableHead>Invoice Date</TableHead>
                            <TableHead>Due Date</TableHead>
                            <TableHead className="text-right">Invoice Amount</TableHead>
                            <TableHead className="text-right">Outstanding</TableHead>
                            <TableHead className="text-right">Days Overdue</TableHead>
                            <TableHead>Dunning Level</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(runDetail.items || []).map((item: any) => (
                            <TableRow key={item.id}>
                              <TableCell className="font-medium">{item.invoice_number}</TableCell>
                              <TableCell>{item.invoice_date}</TableCell>
                              <TableCell>{item.due_date}</TableCell>
                              <TableCell className="text-right">{formatCurrency(item.invoice_amount)}</TableCell>
                              <TableCell className="text-right font-medium">{formatCurrency(item.outstanding_amount)}</TableCell>
                              <TableCell className="text-right">{item.days_overdue}</TableCell>
                              <TableCell>{dunningLevelBadge(item.dunning_level)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </>
              ) : null}
            </div>
          ) : (
            <>
              <div className="flex justify-end">
                <Dialog open={createOpen} onOpenChange={setCreateOpen}>
                  <DialogTrigger asChild>
                    <Button><Plus className="h-4 w-4 mr-2" /> New Dunning Run</Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create Dunning Run</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div>
                        <Label>Minimum Days Overdue</Label>
                        <Input type="number" value={minDays} onChange={(e) => setMinDays(e.target.value)} />
                      </div>
                      <div>
                        <Label>Notes</Label>
                        <Textarea value={dunningNotes} onChange={(e) => setDunningNotes(e.target.value)} placeholder="Optional notes..." />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
                      <Button
                        onClick={() => createDunningMutation.mutate({
                          min_days_overdue: parseInt(minDays || '30'),
                          notes: dunningNotes || undefined,
                        })}
                        disabled={createDunningMutation.isPending}
                      >
                        {createDunningMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                        Create Run
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              {dunningLoading ? (
                <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Run #</TableHead>
                          <TableHead>Date</TableHead>
                          <TableHead>Level</TableHead>
                          <TableHead className="text-right">Customers</TableHead>
                          <TableHead className="text-right">Total Amount</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(dunningRuns?.items || []).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                              No dunning runs yet.
                            </TableCell>
                          </TableRow>
                        ) : (
                          (dunningRuns?.items || []).map((r: any) => (
                            <TableRow
                              key={r.id}
                              className="cursor-pointer hover:bg-muted/50"
                              onClick={() => setSelectedRunId(r.id)}
                            >
                              <TableCell className="font-medium">{r.run_number}</TableCell>
                              <TableCell>{r.run_date}</TableCell>
                              <TableCell>{dunningLevelBadge(r.dunning_level)}</TableCell>
                              <TableCell className="text-right">{r.total_customers}</TableCell>
                              <TableCell className="text-right">{formatCurrency(r.total_amount)}</TableCell>
                              <TableCell>
                                <Badge className="bg-green-100 text-green-800">{r.status}</Badge>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
