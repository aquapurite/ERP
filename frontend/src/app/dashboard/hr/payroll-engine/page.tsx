'use client';

import { useState, useEffect, useCallback } from 'react';
import { payrollEngineApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, CheckCircle, Eye, IndianRupee, Users, Calculator } from 'lucide-react';

interface SalaryComponent {
  id: string;
  structure_id: string;
  name: string;
  code: string;
  component_type: string;
  calculation_type: string;
  percentage_of?: string;
  percentage: number;
  fixed_amount: number;
  is_taxable: boolean;
  sort_order: number;
}

interface SalaryStructure {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  components: SalaryComponent[];
  created_at?: string;
}

interface PayrollSlip {
  id: string;
  employee_name: string;
  employee_code: string;
  basic_salary: number;
  gross_salary: number;
  total_deductions: number;
  net_salary: number;
  earnings_breakdown: Record<string, number>;
  deductions_breakdown: Record<string, number>;
  working_days: number;
  present_days: number;
  leave_days: number;
  lop_days: number;
  status: string;
}

interface PayrollRun {
  id: string;
  run_number: string;
  period: string;
  fiscal_year: string;
  run_date: string;
  status: string;
  total_employees: number;
  total_gross: number;
  total_deductions: number;
  total_net: number;
  slips: PayrollSlip[];
  created_at?: string;
}

const DEFAULT_COMPONENTS = [
  { name: 'Basic', code: 'BASIC', component_type: 'EARNING', calculation_type: 'FIXED', percentage: 0, fixed_amount: 0, is_taxable: true, sort_order: 1 },
  { name: 'HRA', code: 'HRA', component_type: 'EARNING', calculation_type: 'PERCENTAGE', percentage_of: 'BASIC', percentage: 50, fixed_amount: 0, is_taxable: true, sort_order: 2 },
  { name: 'Conveyance', code: 'CONV', component_type: 'EARNING', calculation_type: 'FIXED', percentage: 0, fixed_amount: 1600, is_taxable: false, sort_order: 3 },
  { name: 'Medical Allowance', code: 'MED', component_type: 'EARNING', calculation_type: 'FIXED', percentage: 0, fixed_amount: 1250, is_taxable: false, sort_order: 4 },
  { name: 'Special Allowance', code: 'SPECIAL', component_type: 'EARNING', calculation_type: 'FIXED', percentage: 0, fixed_amount: 0, is_taxable: true, sort_order: 5 },
  { name: 'PF', code: 'PF', component_type: 'DEDUCTION', calculation_type: 'PERCENTAGE', percentage_of: 'BASIC', percentage: 12, fixed_amount: 0, is_taxable: false, sort_order: 10 },
  { name: 'ESIC', code: 'ESIC', component_type: 'DEDUCTION', calculation_type: 'PERCENTAGE', percentage_of: 'GROSS', percentage: 0.75, fixed_amount: 0, is_taxable: false, sort_order: 11 },
  { name: 'Professional Tax', code: 'PT', component_type: 'DEDUCTION', calculation_type: 'FIXED', percentage: 0, fixed_amount: 200, is_taxable: false, sort_order: 12 },
  { name: 'TDS', code: 'TDS', component_type: 'DEDUCTION', calculation_type: 'PERCENTAGE', percentage_of: 'TAXABLE', percentage: 10, fixed_amount: 0, is_taxable: false, sort_order: 13 },
];

export default function PayrollEnginePage() {
  const [tab, setTab] = useState('structures');
  const [structures, setStructures] = useState<SalaryStructure[]>([]);
  const [runs, setRuns] = useState<PayrollRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateStruct, setShowCreateStruct] = useState(false);
  const [showCreateRun, setShowCreateRun] = useState(false);
  const [selectedRun, setSelectedRun] = useState<PayrollRun | null>(null);
  const [showRunDetail, setShowRunDetail] = useState(false);

  // Structure form
  const [structName, setStructName] = useState('');
  const [structCode, setStructCode] = useState('');
  const [structDesc, setStructDesc] = useState('');
  const [components, setComponents] = useState(DEFAULT_COMPONENTS.map(c => ({ ...c })));

  // Run form
  const [runPeriod, setRunPeriod] = useState('');
  const [runFY, setRunFY] = useState('2025-26');

  const loadStructures = useCallback(async () => {
    try {
      const res = await payrollEngineApi.listStructures();
      setStructures(res.items || []);
    } catch {
      // silent
    }
  }, []);

  const loadRuns = useCallback(async () => {
    try {
      const res = await payrollEngineApi.listRuns();
      setRuns(res.items || []);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    loadStructures();
    loadRuns();
  }, [loadStructures, loadRuns]);

  const handleCreateStructure = async () => {
    if (!structName || !structCode) {
      toast.error('Name and code are required');
      return;
    }
    setLoading(true);
    try {
      await payrollEngineApi.createStructure({
        name: structName,
        code: structCode,
        description: structDesc,
        components: components,
      });
      toast.success('Salary structure created');
      setShowCreateStruct(false);
      setStructName('');
      setStructCode('');
      setStructDesc('');
      setComponents(DEFAULT_COMPONENTS.map(c => ({ ...c })));
      loadStructures();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create structure';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRun = async () => {
    if (!runPeriod) {
      toast.error('Period is required (YYYY-MM)');
      return;
    }
    setLoading(true);
    try {
      const res = await payrollEngineApi.createRun({ period: runPeriod, fiscal_year: runFY });
      toast.success(`Payroll run created: ${res.run_number}`);
      setShowCreateRun(false);
      setRunPeriod('');
      loadRuns();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create payroll run';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (runId: string) => {
    try {
      await payrollEngineApi.approveRun(runId);
      toast.success('Payroll run approved');
      loadRuns();
      if (selectedRun?.id === runId) {
        const updated = await payrollEngineApi.getRun(runId);
        setSelectedRun(updated);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to approve';
      toast.error(message);
    }
  };

  const handleViewRun = async (runId: string) => {
    try {
      const res = await payrollEngineApi.getRun(runId);
      setSelectedRun(res);
      setShowRunDetail(true);
    } catch {
      toast.error('Failed to load payroll run details');
    }
  };

  const fmt = (n: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Payroll Engine</h1>
          <p className="text-muted-foreground">Advanced payroll processing (SAP PA03)</p>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="structures">Salary Structures</TabsTrigger>
          <TabsTrigger value="runs">Payroll Runs</TabsTrigger>
        </TabsList>

        {/* ===== Salary Structures Tab ===== */}
        <TabsContent value="structures" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showCreateStruct} onOpenChange={setShowCreateStruct}>
              <DialogTrigger asChild>
                <Button><Plus className="h-4 w-4 mr-2" /> Create Structure</Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Salary Structure</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Name</Label>
                      <Input value={structName} onChange={e => setStructName(e.target.value)} placeholder="e.g. Standard India" />
                    </div>
                    <div>
                      <Label>Code</Label>
                      <Input value={structCode} onChange={e => setStructCode(e.target.value)} placeholder="e.g. STD-IND" />
                    </div>
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Input value={structDesc} onChange={e => setStructDesc(e.target.value)} placeholder="Optional description" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Components</h3>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Code</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Calc</TableHead>
                          <TableHead>% / Amount</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {components.map((comp, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{comp.name}</TableCell>
                            <TableCell>{comp.code}</TableCell>
                            <TableCell>
                              <Badge variant={comp.component_type === 'EARNING' ? 'default' : 'destructive'}>
                                {comp.component_type}
                              </Badge>
                            </TableCell>
                            <TableCell>{comp.calculation_type}</TableCell>
                            <TableCell>
                              {comp.calculation_type === 'PERCENTAGE'
                                ? `${comp.percentage}% of ${comp.percentage_of || ''}`
                                : fmt(comp.fixed_amount)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <Button onClick={handleCreateStructure} disabled={loading} className="w-full">
                    {loading ? 'Creating...' : 'Create Structure'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {structures.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                No salary structures yet. Create one to get started.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {structures.map(s => (
                <Card key={s.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{s.name} <span className="text-sm text-muted-foreground">({s.code})</span></CardTitle>
                      <Badge variant={s.is_active ? 'default' : 'secondary'}>{s.is_active ? 'Active' : 'Inactive'}</Badge>
                    </div>
                    {s.description && <p className="text-sm text-muted-foreground">{s.description}</p>}
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Component</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Calculation</TableHead>
                          <TableHead>Value</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(s.components || []).map(c => (
                          <TableRow key={c.id}>
                            <TableCell className="font-medium">{c.name}</TableCell>
                            <TableCell>
                              <Badge variant={c.component_type === 'EARNING' ? 'default' : 'destructive'} className="text-xs">
                                {c.component_type}
                              </Badge>
                            </TableCell>
                            <TableCell>{c.calculation_type}</TableCell>
                            <TableCell>
                              {c.calculation_type === 'PERCENTAGE'
                                ? `${c.percentage}% of ${c.percentage_of || ''}`
                                : fmt(c.fixed_amount)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ===== Payroll Runs Tab ===== */}
        <TabsContent value="runs" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={showCreateRun} onOpenChange={setShowCreateRun}>
              <DialogTrigger asChild>
                <Button><Plus className="h-4 w-4 mr-2" /> Create Payroll Run</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Payroll Run</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Period (YYYY-MM)</Label>
                    <Input value={runPeriod} onChange={e => setRunPeriod(e.target.value)} placeholder="e.g. 2026-03" />
                  </div>
                  <div>
                    <Label>Fiscal Year</Label>
                    <Select value={runFY} onValueChange={setRunFY}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="2024-25">2024-25</SelectItem>
                        <SelectItem value="2025-26">2025-26</SelectItem>
                        <SelectItem value="2026-27">2026-27</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button onClick={handleCreateRun} disabled={loading} className="w-full">
                    {loading ? 'Processing...' : 'Process Payroll'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Summary Cards */}
          {runs.length > 0 && (
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Calculator className="h-4 w-4" /> Total Runs
                  </div>
                  <p className="text-2xl font-bold mt-1">{runs.length}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Users className="h-4 w-4" /> Latest Employees
                  </div>
                  <p className="text-2xl font-bold mt-1">{runs[0]?.total_employees || 0}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <IndianRupee className="h-4 w-4" /> Latest Gross
                  </div>
                  <p className="text-2xl font-bold mt-1">{fmt(runs[0]?.total_gross || 0)}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <IndianRupee className="h-4 w-4" /> Latest Net
                  </div>
                  <p className="text-2xl font-bold mt-1">{fmt(runs[0]?.total_net || 0)}</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Runs Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Run #</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>FY</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Employees</TableHead>
                    <TableHead className="text-right">Gross</TableHead>
                    <TableHead className="text-right">Deductions</TableHead>
                    <TableHead className="text-right">Net</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No payroll runs yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    runs.map(run => (
                      <TableRow key={run.id}>
                        <TableCell className="font-medium">{run.run_number}</TableCell>
                        <TableCell>{run.period}</TableCell>
                        <TableCell>{run.fiscal_year}</TableCell>
                        <TableCell>
                          <Badge variant={run.status === 'APPROVED' ? 'default' : 'secondary'}>
                            {run.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{run.total_employees}</TableCell>
                        <TableCell className="text-right">{fmt(run.total_gross)}</TableCell>
                        <TableCell className="text-right">{fmt(run.total_deductions)}</TableCell>
                        <TableCell className="text-right font-semibold">{fmt(run.total_net)}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button variant="ghost" size="sm" onClick={() => handleViewRun(run.id)}>
                              <Eye className="h-4 w-4" />
                            </Button>
                            {run.status === 'DRAFT' && (
                              <Button variant="ghost" size="sm" onClick={() => handleApprove(run.id)}>
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Payroll Run Detail Dialog */}
      <Dialog open={showRunDetail} onOpenChange={setShowRunDetail}>
        <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Payroll Run: {selectedRun?.run_number} ({selectedRun?.period})
              <Badge className="ml-2" variant={selectedRun?.status === 'APPROVED' ? 'default' : 'secondary'}>
                {selectedRun?.status}
              </Badge>
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Employees</p>
                <p className="text-xl font-bold">{selectedRun?.total_employees}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Gross</p>
                <p className="text-xl font-bold">{fmt(selectedRun?.total_gross || 0)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Deductions</p>
                <p className="text-xl font-bold text-red-600">{fmt(selectedRun?.total_deductions || 0)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm text-muted-foreground">Net Pay</p>
                <p className="text-xl font-bold text-green-600">{fmt(selectedRun?.total_net || 0)}</p>
              </CardContent>
            </Card>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employee</TableHead>
                <TableHead>Code</TableHead>
                <TableHead>Days</TableHead>
                <TableHead className="text-right">Basic</TableHead>
                <TableHead className="text-right">Gross</TableHead>
                <TableHead className="text-right">Deductions</TableHead>
                <TableHead className="text-right">Net</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(selectedRun?.slips || []).map(slip => (
                <TableRow key={slip.id}>
                  <TableCell className="font-medium">{slip.employee_name}</TableCell>
                  <TableCell>{slip.employee_code}</TableCell>
                  <TableCell>
                    <span className="text-sm">{slip.present_days}/{slip.working_days}</span>
                    {slip.lop_days > 0 && <span className="text-xs text-red-500 ml-1">({slip.lop_days} LOP)</span>}
                  </TableCell>
                  <TableCell className="text-right">{fmt(slip.basic_salary)}</TableCell>
                  <TableCell className="text-right">{fmt(slip.gross_salary)}</TableCell>
                  <TableCell className="text-right text-red-600">{fmt(slip.total_deductions)}</TableCell>
                  <TableCell className="text-right font-semibold text-green-600">{fmt(slip.net_salary)}</TableCell>
                  <TableCell>
                    <Badge variant={slip.status === 'APPROVED' ? 'default' : 'secondary'} className="text-xs">
                      {slip.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {selectedRun?.status === 'DRAFT' && (
            <div className="flex justify-end mt-4">
              <Button onClick={() => handleApprove(selectedRun.id)}>
                <CheckCircle className="h-4 w-4 mr-2" /> Approve Payroll
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
