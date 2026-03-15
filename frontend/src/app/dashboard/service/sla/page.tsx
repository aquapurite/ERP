'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Loader2, AlertTriangle, ShieldCheck, Clock, Zap, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PageHeader } from '@/components/common';
import { slaApi } from '@/lib/api';

interface SLARule {
  id: string;
  name: string;
  service_type?: string;
  priority?: string;
  response_hours: number;
  resolution_hours: number;
  escalation_level_1_hours?: number;
  escalation_level_2_hours?: number;
  escalation_level_1_user_id?: string;
  escalation_level_2_user_id?: string;
  is_active: boolean;
  created_at?: string;
}

interface SLABreach {
  id: string;
  service_request_id: string;
  ticket_number?: string;
  service_type?: string;
  priority?: string;
  sr_status?: string;
  sla_rule_id?: string;
  breach_type: string;
  breached_at?: string;
  escalation_level: number;
  escalated_to?: string;
  resolution_at?: string;
  created_at?: string;
}

const BREACH_COLORS: Record<string, string> = {
  RESPONSE: 'bg-yellow-100 text-yellow-800',
  RESOLUTION: 'bg-red-100 text-red-800',
};

const PRIORITY_COLORS: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-700',
  NORMAL: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-700',
  URGENT: 'bg-red-100 text-red-700',
  CRITICAL: 'bg-red-200 text-red-900',
};

export default function SLAPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [editRule, setEditRule] = useState<SLARule | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    service_type: '',
    priority: '',
    response_hours: 24,
    resolution_hours: 72,
    escalation_level_1_hours: 48,
    escalation_level_2_hours: 72,
    is_active: true,
  });

  // Queries
  const { data: rulesData, isLoading: rulesLoading } = useQuery({
    queryKey: ['sla-rules'],
    queryFn: () => slaApi.listRules(),
  });

  const { data: breachesData, isLoading: breachesLoading } = useQuery({
    queryKey: ['sla-breaches'],
    queryFn: () => slaApi.listBreaches({ page: 1, size: 100 }),
  });

  const rules: SLARule[] = rulesData?.items || [];
  const breaches: SLABreach[] = breachesData?.items || [];

  // Mutations
  const createRuleMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => slaApi.createRule(payload),
    onSuccess: () => {
      toast.success('SLA rule created');
      queryClient.invalidateQueries({ queryKey: ['sla-rules'] });
      setShowCreate(false);
      resetForm();
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to create rule');
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) => slaApi.updateRule(id, payload),
    onSuccess: () => {
      toast.success('SLA rule updated');
      queryClient.invalidateQueries({ queryKey: ['sla-rules'] });
      setEditRule(null);
      resetForm();
    },
    onError: () => toast.error('Failed to update rule'),
  });

  const checkSlaMutation = useMutation({
    mutationFn: () => slaApi.checkSla(),
    onSuccess: (data: { message?: string; new_breaches?: number }) => {
      toast.success(data.message || 'SLA check completed');
      queryClient.invalidateQueries({ queryKey: ['sla-breaches'] });
    },
    onError: () => toast.error('Failed to check SLA'),
  });

  function resetForm() {
    setFormData({
      name: '', service_type: '', priority: '',
      response_hours: 24, resolution_hours: 72,
      escalation_level_1_hours: 48, escalation_level_2_hours: 72, is_active: true,
    });
  }

  function openEdit(rule: SLARule) {
    setFormData({
      name: rule.name,
      service_type: rule.service_type || '',
      priority: rule.priority || '',
      response_hours: rule.response_hours,
      resolution_hours: rule.resolution_hours,
      escalation_level_1_hours: rule.escalation_level_1_hours || 48,
      escalation_level_2_hours: rule.escalation_level_2_hours || 72,
      is_active: rule.is_active,
    });
    setEditRule(rule);
  }

  function handleSubmit() {
    if (!formData.name) {
      toast.error('Name is required');
      return;
    }
    const payload: Record<string, unknown> = {
      ...formData,
      service_type: formData.service_type || null,
      priority: formData.priority || null,
    };
    if (editRule) {
      updateRuleMutation.mutate({ id: editRule.id, payload });
    } else {
      createRuleMutation.mutate(payload);
    }
  }

  const responseBreaches = breaches.filter(b => b.breach_type === 'RESPONSE');
  const resolutionBreaches = breaches.filter(b => b.breach_type === 'RESOLUTION');

  return (
    <div className="space-y-6">
      <PageHeader
        title="SLA Automation & Escalation"
        description="Service Level Agreement rules and breach monitoring"
      />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Active Rules</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-green-500" />
              {rules.filter(r => r.is_active).length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Total Breaches</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              {breachesData?.total || 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Response Breaches</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-yellow-600">{responseBreaches.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Resolution Breaches</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-red-600">{resolutionBreaches.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Escalated</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-orange-600">{breaches.filter(b => b.escalation_level > 0).length}</p></CardContent>
        </Card>
      </div>

      <Tabs defaultValue="rules">
        <TabsList>
          <TabsTrigger value="rules">SLA Rules</TabsTrigger>
          <TabsTrigger value="breaches">Breaches Dashboard</TabsTrigger>
        </TabsList>

        {/* SLA Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => { resetForm(); setShowCreate(true); }}>
              <Plus className="mr-2 h-4 w-4" /> Create SLA Rule
            </Button>
          </div>

          {rulesLoading ? (
            <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
          ) : (
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="p-3 text-left font-medium">Name</th>
                    <th className="p-3 text-left font-medium">Service Type</th>
                    <th className="p-3 text-left font-medium">Priority</th>
                    <th className="p-3 text-center font-medium">Response (hrs)</th>
                    <th className="p-3 text-center font-medium">Resolution (hrs)</th>
                    <th className="p-3 text-center font-medium">Esc L1 (hrs)</th>
                    <th className="p-3 text-center font-medium">Esc L2 (hrs)</th>
                    <th className="p-3 text-center font-medium">Active</th>
                    <th className="p-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map(rule => (
                    <tr key={rule.id} className="border-t hover:bg-muted/30">
                      <td className="p-3 font-medium">{rule.name}</td>
                      <td className="p-3">{rule.service_type || <span className="text-muted-foreground">All</span>}</td>
                      <td className="p-3">
                        {rule.priority ? (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[rule.priority] || ''}`}>
                            {rule.priority}
                          </span>
                        ) : <span className="text-muted-foreground">All</span>}
                      </td>
                      <td className="p-3 text-center font-mono">{rule.response_hours}h</td>
                      <td className="p-3 text-center font-mono">{rule.resolution_hours}h</td>
                      <td className="p-3 text-center font-mono">{rule.escalation_level_1_hours || '-'}h</td>
                      <td className="p-3 text-center font-mono">{rule.escalation_level_2_hours || '-'}h</td>
                      <td className="p-3 text-center">
                        <Badge variant={rule.is_active ? 'default' : 'secondary'}>{rule.is_active ? 'Yes' : 'No'}</Badge>
                      </td>
                      <td className="p-3 text-right">
                        <Button variant="ghost" size="sm" onClick={() => openEdit(rule)}><Pencil className="h-4 w-4" /></Button>
                      </td>
                    </tr>
                  ))}
                  {rules.length === 0 && (
                    <tr><td colSpan={9} className="p-8 text-center text-muted-foreground">No SLA rules configured</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* Breaches Tab */}
        <TabsContent value="breaches" className="space-y-4">
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => checkSlaMutation.mutate()} disabled={checkSlaMutation.isPending}>
              {checkSlaMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Run SLA Check
            </Button>
          </div>

          {breachesLoading ? (
            <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
          ) : (
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="p-3 text-left font-medium">Ticket</th>
                    <th className="p-3 text-left font-medium">Service Type</th>
                    <th className="p-3 text-left font-medium">Priority</th>
                    <th className="p-3 text-left font-medium">SR Status</th>
                    <th className="p-3 text-left font-medium">Breach Type</th>
                    <th className="p-3 text-center font-medium">Esc Level</th>
                    <th className="p-3 text-left font-medium">Breached At</th>
                    <th className="p-3 text-left font-medium">Resolved</th>
                  </tr>
                </thead>
                <tbody>
                  {breaches.map(b => (
                    <tr key={b.id} className="border-t hover:bg-muted/30">
                      <td className="p-3 font-mono text-xs font-medium">{b.ticket_number || '-'}</td>
                      <td className="p-3">{b.service_type || '-'}</td>
                      <td className="p-3">
                        {b.priority ? (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[b.priority] || ''}`}>
                            {b.priority}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="p-3"><Badge variant="outline">{b.sr_status || '-'}</Badge></td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${BREACH_COLORS[b.breach_type] || ''}`}>
                          {b.breach_type}
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        {b.escalation_level > 0 ? (
                          <Badge variant="destructive">L{b.escalation_level}</Badge>
                        ) : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="p-3 text-xs">{b.breached_at ? new Date(b.breached_at).toLocaleString() : '-'}</td>
                      <td className="p-3 text-xs">
                        {b.resolution_at ? (
                          <span className="text-green-600">{new Date(b.resolution_at).toLocaleString()}</span>
                        ) : <span className="text-red-500">Pending</span>}
                      </td>
                    </tr>
                  ))}
                  {breaches.length === 0 && (
                    <tr><td colSpan={8} className="p-8 text-center text-muted-foreground">No SLA breaches found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create / Edit SLA Rule Dialog */}
      <Dialog open={showCreate || !!editRule} onOpenChange={() => { setShowCreate(false); setEditRule(null); resetForm(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editRule ? 'Edit' : 'Create'} SLA Rule</DialogTitle>
            <DialogDescription>Configure SLA thresholds and escalation</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label>Rule Name *</Label>
              <Input value={formData.name} onChange={e => setFormData(p => ({ ...p, name: e.target.value }))} placeholder="e.g., High Priority - 4hr Response" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Service Type (optional)</Label>
                <Select value={formData.service_type} onValueChange={v => setFormData(p => ({ ...p, service_type: v === 'ALL' ? '' : v }))}>
                  <SelectTrigger><SelectValue placeholder="All Types" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Types</SelectItem>
                    <SelectItem value="INSTALLATION">Installation</SelectItem>
                    <SelectItem value="WARRANTY_REPAIR">Warranty Repair</SelectItem>
                    <SelectItem value="PAID_REPAIR">Paid Repair</SelectItem>
                    <SelectItem value="AMC_SERVICE">AMC Service</SelectItem>
                    <SelectItem value="COMPLAINT">Complaint</SelectItem>
                    <SelectItem value="FILTER_CHANGE">Filter Change</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Priority (optional)</Label>
                <Select value={formData.priority} onValueChange={v => setFormData(p => ({ ...p, priority: v === 'ALL' ? '' : v }))}>
                  <SelectTrigger><SelectValue placeholder="All Priorities" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Priorities</SelectItem>
                    <SelectItem value="LOW">Low</SelectItem>
                    <SelectItem value="NORMAL">Normal</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="URGENT">Urgent</SelectItem>
                    <SelectItem value="CRITICAL">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Response SLA (hours)</Label>
                <Input type="number" value={formData.response_hours} onChange={e => setFormData(p => ({ ...p, response_hours: parseInt(e.target.value) || 24 }))} />
              </div>
              <div>
                <Label>Resolution SLA (hours)</Label>
                <Input type="number" value={formData.resolution_hours} onChange={e => setFormData(p => ({ ...p, resolution_hours: parseInt(e.target.value) || 72 }))} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Escalation L1 (hours)</Label>
                <Input type="number" value={formData.escalation_level_1_hours} onChange={e => setFormData(p => ({ ...p, escalation_level_1_hours: parseInt(e.target.value) || 48 }))} />
              </div>
              <div>
                <Label>Escalation L2 (hours)</Label>
                <Input type="number" value={formData.escalation_level_2_hours} onChange={e => setFormData(p => ({ ...p, escalation_level_2_hours: parseInt(e.target.value) || 72 }))} />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch checked={formData.is_active} onCheckedChange={v => setFormData(p => ({ ...p, is_active: v }))} />
              <Label>Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCreate(false); setEditRule(null); }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createRuleMutation.isPending || updateRuleMutation.isPending}>
              {(createRuleMutation.isPending || updateRuleMutation.isPending) && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {editRule ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
