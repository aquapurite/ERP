'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings,
  Loader2,
  RefreshCw,
  ExternalLink,
  Save,
  Bell,
  Shield,
  Truck,
  Scale,
  Route,
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  MapPin,
  Package,
  BarChart3,
  Eye,
} from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { PageHeader } from '@/components/common';

// ─── CJDQuick API Helper ─────────────────────────────────────────────────────

const CJDQ_BASE = 'https://lsp-oms-api.onrender.com/api/v1';
const CJDQ_TOKEN = 'Bearer 21fb78de75e14d4b9a013a646f6b40e78262b7a35c1202b52095fb6acdd8ffa8';

const cjdqFetch = async (path: string, options?: RequestInit) => {
  const res = await fetch(`${CJDQ_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': CJDQ_TOKEN,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || 'CJDQuick API error');
  }
  return res.json();
};

// ─── Types ───────────────────────────────────────────────────────────────────

interface GSTConfig {
  gstin: string;
  legal_name: string;
  trade_name: string;
  state_code: string;
  address?: string;
  pincode?: string;
}

interface TrackingPageConfig {
  primary_color: string;
  secondary_color: string;
  logo_url: string;
  support_email: string;
  support_phone: string;
  company_name: string;
  custom_css?: string;
}

interface TrackingRequest {
  id: string;
  tracking_number: string;
  request_type: string;
  status: string;
  details: string;
  created_at: string;
}

interface NotificationPreference {
  event: string;
  email: boolean;
  sms: boolean;
  whatsapp: boolean;
}

interface RTORiskData {
  total_orders: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  cod_orders: number;
  prepaid_orders: number;
  rto_rate: number;
  top_risky_pincodes: Array<{ pincode: string; risk_score: number; order_count: number }>;
}

interface WeightFreeze {
  id: string;
  awb_number: string;
  courier: string;
  applied_weight: number;
  frozen_weight: number;
  status: string;
  created_at: string;
}

interface WeightDashboard {
  total_disputes: number;
  resolved: number;
  pending: number;
  savings: number;
}

interface FacilityGroup {
  id: string;
  name: string;
  facilities: string[];
  is_active: boolean;
}

interface RoutingRule {
  id: string;
  name: string;
  priority: number;
  conditions: Record<string, unknown>;
  action: string;
  is_active: boolean;
}

// ─── Notification Events ─────────────────────────────────────────────────────

const NOTIFICATION_EVENTS = [
  { key: 'order.confirmed', label: 'Order Confirmed' },
  { key: 'order.shipped', label: 'Order Shipped' },
  { key: 'order.out_for_delivery', label: 'Out for Delivery' },
  { key: 'order.delivered', label: 'Order Delivered' },
  { key: 'ndr.created', label: 'NDR Created' },
  { key: 'order.rto', label: 'RTO Initiated' },
];

const CHANNELS = ['email', 'sms', 'whatsapp'] as const;

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 1: GST CONFIG
// ═══════════════════════════════════════════════════════════════════════════════

function GSTConfigTab() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Partial<GSTConfig>>({});
  const [editing, setEditing] = useState(false);

  const { data: config, isLoading } = useQuery<GSTConfig>({
    queryKey: ['cjdq-gst-config'],
    queryFn: () => cjdqFetch('/gst/config'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<GSTConfig>) =>
      cjdqFetch('/gst/config', { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      toast.success('GST configuration updated');
      queryClient.invalidateQueries({ queryKey: ['cjdq-gst-config'] });
      setEditing(false);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const handleEdit = () => {
    setForm(config || {});
    setEditing(true);
  };

  const handleSave = () => {
    updateMutation.mutate(form);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              GST Configuration
            </CardTitle>
            <CardDescription>
              GSTIN and business details used for shipping labels and tax documents
            </CardDescription>
          </div>
          {!editing && (
            <Button variant="outline" onClick={handleEdit}>
              Edit
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {editing ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>GSTIN</Label>
                <Input
                  value={form.gstin || ''}
                  onChange={(e) => setForm({ ...form, gstin: e.target.value })}
                  placeholder="22AAAAA0000A1Z5"
                />
              </div>
              <div className="space-y-2">
                <Label>Legal Name</Label>
                <Input
                  value={form.legal_name || ''}
                  onChange={(e) => setForm({ ...form, legal_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Trade Name</Label>
                <Input
                  value={form.trade_name || ''}
                  onChange={(e) => setForm({ ...form, trade_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>State Code</Label>
                <Input
                  value={form.state_code || ''}
                  onChange={(e) => setForm({ ...form, state_code: e.target.value })}
                  placeholder="09"
                />
              </div>
              <div className="space-y-2">
                <Label>Address</Label>
                <Input
                  value={form.address || ''}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Pincode</Label>
                <Input
                  value={form.pincode || ''}
                  onChange={(e) => setForm({ ...form, pincode: e.target.value })}
                  placeholder="201301"
                />
              </div>
              <div className="col-span-full flex gap-2 pt-2">
                <Button onClick={handleSave} disabled={updateMutation.isPending}>
                  {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </Button>
                <Button variant="outline" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-sm font-medium text-muted-foreground">GSTIN</p>
                <p className="text-sm font-mono">{config?.gstin || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Legal Name</p>
                <p className="text-sm">{config?.legal_name || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Trade Name</p>
                <p className="text-sm">{config?.trade_name || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">State Code</p>
                <p className="text-sm">{config?.state_code || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Address</p>
                <p className="text-sm">{config?.address || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Pincode</p>
                <p className="text-sm">{config?.pincode || '—'}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 2: TRACKING PAGE
// ═══════════════════════════════════════════════════════════════════════════════

function TrackingPageTab() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Partial<TrackingPageConfig>>({});
  const [editing, setEditing] = useState(false);

  const { data: config, isLoading } = useQuery<TrackingPageConfig>({
    queryKey: ['cjdq-tracking-page'],
    queryFn: () => cjdqFetch('/settings/tracking-page'),
  });

  const { data: requests, isLoading: requestsLoading } = useQuery<TrackingRequest[]>({
    queryKey: ['cjdq-tracking-requests'],
    queryFn: () => cjdqFetch('/settings/tracking-requests'),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<TrackingPageConfig>) =>
      cjdqFetch('/settings/tracking-page', { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      toast.success('Tracking page branding updated');
      queryClient.invalidateQueries({ queryKey: ['cjdq-tracking-page'] });
      setEditing(false);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const handleEdit = () => {
    setForm(config || {});
    setEditing(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Branding Config */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Tracking Page Branding
            </CardTitle>
            <CardDescription>
              Customize the public tracking page appearance
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href="https://lsp-oms.vercel.app/track" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Preview
              </a>
            </Button>
            {!editing && (
              <Button variant="outline" size="sm" onClick={handleEdit}>
                Edit
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {editing ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Company Name</Label>
                <Input
                  value={form.company_name || ''}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Logo URL</Label>
                <Input
                  value={form.logo_url || ''}
                  onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>
              <div className="space-y-2">
                <Label>Primary Color</Label>
                <div className="flex gap-2">
                  <Input
                    value={form.primary_color || ''}
                    onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
                    placeholder="#1a73e8"
                  />
                  <input
                    type="color"
                    value={form.primary_color || '#1a73e8'}
                    onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
                    className="h-10 w-10 rounded border cursor-pointer"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Secondary Color</Label>
                <div className="flex gap-2">
                  <Input
                    value={form.secondary_color || ''}
                    onChange={(e) => setForm({ ...form, secondary_color: e.target.value })}
                    placeholder="#f1f3f4"
                  />
                  <input
                    type="color"
                    value={form.secondary_color || '#f1f3f4'}
                    onChange={(e) => setForm({ ...form, secondary_color: e.target.value })}
                    className="h-10 w-10 rounded border cursor-pointer"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Support Email</Label>
                <Input
                  value={form.support_email || ''}
                  onChange={(e) => setForm({ ...form, support_email: e.target.value })}
                  type="email"
                />
              </div>
              <div className="space-y-2">
                <Label>Support Phone</Label>
                <Input
                  value={form.support_phone || ''}
                  onChange={(e) => setForm({ ...form, support_phone: e.target.value })}
                />
              </div>
              <div className="col-span-full space-y-2">
                <Label>Custom CSS (optional)</Label>
                <Textarea
                  value={form.custom_css || ''}
                  onChange={(e) => setForm({ ...form, custom_css: e.target.value })}
                  rows={3}
                  placeholder=".tracking-container { ... }"
                />
              </div>
              <div className="col-span-full flex gap-2 pt-2">
                <Button onClick={() => updateMutation.mutate(form)} disabled={updateMutation.isPending}>
                  {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </Button>
                <Button variant="outline" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Company Name</p>
                <p className="text-sm">{config?.company_name || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Logo URL</p>
                <p className="text-sm truncate">{config?.logo_url || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Primary Color</p>
                <div className="flex items-center gap-2">
                  <div
                    className="h-4 w-4 rounded border"
                    style={{ backgroundColor: config?.primary_color || '#ccc' }}
                  />
                  <span className="text-sm font-mono">{config?.primary_color || '—'}</span>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Secondary Color</p>
                <div className="flex items-center gap-2">
                  <div
                    className="h-4 w-4 rounded border"
                    style={{ backgroundColor: config?.secondary_color || '#ccc' }}
                  />
                  <span className="text-sm font-mono">{config?.secondary_color || '—'}</span>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Support Email</p>
                <p className="text-sm">{config?.support_email || '—'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Support Phone</p>
                <p className="text-sm">{config?.support_phone || '—'}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tracking Requests */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Tracking Requests
          </CardTitle>
          <CardDescription>
            Customer requests for address changes and reschedules
          </CardDescription>
        </CardHeader>
        <CardContent>
          {requestsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !requests || requests.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">No tracking requests yet</p>
          ) : (
            <div className="overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tracking #</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requests.map((req) => (
                    <TableRow key={req.id}>
                      <TableCell className="font-mono text-sm">{req.tracking_number}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{req.request_type}</Badge>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm">
                        {req.details}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            req.status === 'APPROVED'
                              ? 'default'
                              : req.status === 'REJECTED'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {req.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(req.created_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 3: NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════════════════════

function NotificationsTab() {
  const queryClient = useQueryClient();

  const { data: preferences, isLoading } = useQuery<NotificationPreference[]>({
    queryKey: ['cjdq-notification-prefs'],
    queryFn: () => cjdqFetch('/communications/preferences'),
  });

  const updateMutation = useMutation({
    mutationFn: (prefs: NotificationPreference[]) =>
      cjdqFetch('/communications/preferences', {
        method: 'POST',
        body: JSON.stringify({ preferences: prefs }),
      }),
    onSuccess: () => {
      toast.success('Notification preferences saved');
      queryClient.invalidateQueries({ queryKey: ['cjdq-notification-prefs'] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  // Build local state from fetched prefs or defaults
  const [localPrefs, setLocalPrefs] = useState<NotificationPreference[]>([]);
  const [initialized, setInitialized] = useState(false);

  if (preferences && !initialized) {
    // Merge fetched preferences with all known events
    const merged = NOTIFICATION_EVENTS.map((evt) => {
      const existing = preferences.find((p) => p.event === evt.key);
      return existing || { event: evt.key, email: false, sms: false, whatsapp: false };
    });
    setLocalPrefs(merged);
    setInitialized(true);
  }

  const toggleChannel = (eventKey: string, channel: typeof CHANNELS[number]) => {
    setLocalPrefs((prev) =>
      prev.map((p) => (p.event === eventKey ? { ...p, [channel]: !p[channel] } : p))
    );
  };

  const handleSave = () => {
    updateMutation.mutate(localPrefs);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notification Preferences
            </CardTitle>
            <CardDescription>
              Configure which events trigger notifications on each channel
            </CardDescription>
          </div>
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[250px]">Event</TableHead>
                  <TableHead className="text-center">Email</TableHead>
                  <TableHead className="text-center">SMS</TableHead>
                  <TableHead className="text-center">WhatsApp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {NOTIFICATION_EVENTS.map((evt) => {
                  const pref = localPrefs.find((p) => p.event === evt.key);
                  return (
                    <TableRow key={evt.key}>
                      <TableCell className="font-medium">{evt.label}</TableCell>
                      {CHANNELS.map((ch) => (
                        <TableCell key={ch} className="text-center">
                          <Switch
                            checked={pref?.[ch] ?? false}
                            onCheckedChange={() => toggleChannel(evt.key, ch)}
                          />
                        </TableCell>
                      ))}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4: RTO RISK
// ═══════════════════════════════════════════════════════════════════════════════

function RTORiskTab() {
  const queryClient = useQueryClient();

  const { data: riskData, isLoading } = useQuery<RTORiskData>({
    queryKey: ['cjdq-rto-risk'],
    queryFn: () => cjdqFetch('/analytics/rto-risk'),
  });

  const recalcMutation = useMutation({
    mutationFn: () =>
      cjdqFetch('/analytics/rto-risk/recalculate', { method: 'POST' }),
    onSuccess: () => {
      toast.success('RTO risk recalculation triggered');
      queryClient.invalidateQueries({ queryKey: ['cjdq-rto-risk'] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm font-medium text-muted-foreground">Total Orders</div>
            <div className="text-2xl font-bold">{riskData?.total_orders ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm font-medium text-muted-foreground">RTO Rate</div>
            <div className="text-2xl font-bold text-red-600">
              {riskData?.rto_rate != null ? `${riskData.rto_rate.toFixed(1)}%` : '—'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm font-medium text-muted-foreground">COD Orders</div>
            <div className="text-2xl font-bold">{riskData?.cod_orders ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm font-medium text-muted-foreground">Prepaid Orders</div>
            <div className="text-2xl font-bold">{riskData?.prepaid_orders ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Distribution */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Risk Distribution
            </CardTitle>
          </div>
          <Button
            variant="outline"
            onClick={() => recalcMutation.mutate()}
            disabled={recalcMutation.isPending}
          >
            {recalcMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Recalculate
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
              <div className="text-sm font-medium text-red-700">High Risk</div>
              <div className="mt-1 text-3xl font-bold text-red-700">{riskData?.high_risk ?? 0}</div>
            </div>
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-center">
              <div className="text-sm font-medium text-yellow-700">Medium Risk</div>
              <div className="mt-1 text-3xl font-bold text-yellow-700">{riskData?.medium_risk ?? 0}</div>
            </div>
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-center">
              <div className="text-sm font-medium text-green-700">Low Risk</div>
              <div className="mt-1 text-3xl font-bold text-green-700">{riskData?.low_risk ?? 0}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Risky Pincodes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Top Risky Pincodes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!riskData?.top_risky_pincodes || riskData.top_risky_pincodes.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No pincode data available</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pincode</TableHead>
                  <TableHead>Risk Score</TableHead>
                  <TableHead>Order Count</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {riskData.top_risky_pincodes.map((p) => (
                  <TableRow key={p.pincode}>
                    <TableCell className="font-mono">{p.pincode}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          p.risk_score > 70 ? 'destructive' : p.risk_score > 40 ? 'secondary' : 'default'
                        }
                      >
                        {p.risk_score.toFixed(0)}
                      </Badge>
                    </TableCell>
                    <TableCell>{p.order_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 5: WEIGHT MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

function WeightManagementTab() {
  const queryClient = useQueryClient();

  const { data: dashboard, isLoading: dashLoading } = useQuery<WeightDashboard>({
    queryKey: ['cjdq-weight-dashboard'],
    queryFn: () => cjdqFetch('/weight/dashboard'),
  });

  const { data: freezes, isLoading: freezesLoading } = useQuery<WeightFreeze[]>({
    queryKey: ['cjdq-weight-freezes'],
    queryFn: () => cjdqFetch('/weight/freezes'),
  });

  const detectMutation = useMutation({
    mutationFn: () =>
      cjdqFetch('/weight/detect-discrepancies', { method: 'POST' }),
    onSuccess: (data) => {
      toast.success(`Discrepancy detection complete. ${data?.detected ?? 0} found.`);
      queryClient.invalidateQueries({ queryKey: ['cjdq-weight-freezes'] });
      queryClient.invalidateQueries({ queryKey: ['cjdq-weight-dashboard'] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <div className="space-y-6">
      {/* Dashboard Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {dashLoading ? (
          <div className="col-span-full flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm font-medium text-muted-foreground">Total Disputes</div>
                <div className="text-2xl font-bold">{dashboard?.total_disputes ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm font-medium text-muted-foreground">Resolved</div>
                <div className="text-2xl font-bold text-green-600">{dashboard?.resolved ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm font-medium text-muted-foreground">Pending</div>
                <div className="text-2xl font-bold text-yellow-600">{dashboard?.pending ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm font-medium text-muted-foreground">Total Savings</div>
                <div className="text-2xl font-bold text-blue-600">
                  {dashboard?.savings != null ? `₹${dashboard.savings.toLocaleString()}` : '—'}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Detect Discrepancies */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5" />
              Weight Freezes
            </CardTitle>
            <CardDescription>
              Frozen weights for shipped orders. Detect discrepancies to find overcharges.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            onClick={() => detectMutation.mutate()}
            disabled={detectMutation.isPending}
          >
            {detectMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Detect Discrepancies
          </Button>
        </CardHeader>
        <CardContent>
          {freezesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !freezes || freezes.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No weight freezes found</p>
          ) : (
            <div className="overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>AWB Number</TableHead>
                    <TableHead>Courier</TableHead>
                    <TableHead>Applied (kg)</TableHead>
                    <TableHead>Frozen (kg)</TableHead>
                    <TableHead>Diff</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {freezes.map((f) => {
                    const diff = f.frozen_weight - f.applied_weight;
                    return (
                      <TableRow key={f.id}>
                        <TableCell className="font-mono text-sm">{f.awb_number}</TableCell>
                        <TableCell>{f.courier}</TableCell>
                        <TableCell>{f.applied_weight.toFixed(2)}</TableCell>
                        <TableCell>{f.frozen_weight.toFixed(2)}</TableCell>
                        <TableCell>
                          <span className={diff > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>
                            {diff > 0 ? '+' : ''}
                            {diff.toFixed(2)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              f.status === 'RESOLVED'
                                ? 'default'
                                : f.status === 'DISPUTED'
                                  ? 'destructive'
                                  : 'secondary'
                            }
                          >
                            {f.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(f.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 6: ROUTING
// ═══════════════════════════════════════════════════════════════════════════════

function RoutingTab() {
  const [simForm, setSimForm] = useState({
    origin_pincode: '',
    destination_pincode: '',
    weight: '',
    payment_mode: 'prepaid' as string,
  });
  const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null);

  const { data: facilityGroups, isLoading: fgLoading } = useQuery<FacilityGroup[]>({
    queryKey: ['cjdq-facility-groups'],
    queryFn: () => cjdqFetch('/routing/facility-groups'),
  });

  const { data: rules, isLoading: rulesLoading } = useQuery<RoutingRule[]>({
    queryKey: ['cjdq-routing-rules'],
    queryFn: () => cjdqFetch('/routing/rules'),
  });

  const simulateMutation = useMutation({
    mutationFn: (data: typeof simForm) =>
      cjdqFetch('/routing/simulate', {
        method: 'POST',
        body: JSON.stringify({
          origin_pincode: data.origin_pincode,
          destination_pincode: data.destination_pincode,
          weight: parseFloat(data.weight) || 0.5,
          payment_mode: data.payment_mode,
        }),
      }),
    onSuccess: (data) => {
      setSimResult(data);
      toast.success('Routing simulation complete');
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <div className="space-y-6">
      {/* Simulate Routing */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Route className="h-5 w-5" />
            Route Simulation
          </CardTitle>
          <CardDescription>
            Test which courier would be selected for a given shipment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div className="space-y-2">
              <Label>Origin Pincode</Label>
              <Input
                value={simForm.origin_pincode}
                onChange={(e) => setSimForm({ ...simForm, origin_pincode: e.target.value })}
                placeholder="201301"
              />
            </div>
            <div className="space-y-2">
              <Label>Destination Pincode</Label>
              <Input
                value={simForm.destination_pincode}
                onChange={(e) => setSimForm({ ...simForm, destination_pincode: e.target.value })}
                placeholder="400001"
              />
            </div>
            <div className="space-y-2">
              <Label>Weight (kg)</Label>
              <Input
                value={simForm.weight}
                onChange={(e) => setSimForm({ ...simForm, weight: e.target.value })}
                placeholder="0.5"
                type="number"
                step="0.1"
              />
            </div>
            <div className="space-y-2">
              <Label>Payment Mode</Label>
              <Select
                value={simForm.payment_mode}
                onValueChange={(v) => setSimForm({ ...simForm, payment_mode: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="prepaid">Prepaid</SelectItem>
                  <SelectItem value="cod">COD</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                onClick={() => simulateMutation.mutate(simForm)}
                disabled={simulateMutation.isPending || !simForm.origin_pincode || !simForm.destination_pincode}
                className="w-full"
              >
                {simulateMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Truck className="mr-2 h-4 w-4" />
                )}
                Simulate
              </Button>
            </div>
          </div>
          {simResult && (
            <div className="mt-4 rounded-lg border bg-muted/50 p-4">
              <h4 className="text-sm font-semibold mb-2">Simulation Result</h4>
              <pre className="text-sm whitespace-pre-wrap font-mono">
                {JSON.stringify(simResult, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Facility Groups */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Facility Groups
          </CardTitle>
        </CardHeader>
        <CardContent>
          {fgLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !facilityGroups || facilityGroups.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No facility groups configured</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Facilities</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {facilityGroups.map((fg) => (
                  <TableRow key={fg.id}>
                    <TableCell className="font-medium">{fg.name}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {fg.facilities.map((f) => (
                          <Badge key={f} variant="outline" className="text-xs">
                            {f}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={fg.is_active ? 'default' : 'secondary'}>
                        {fg.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Routing Rules */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Routing Rules
          </CardTitle>
        </CardHeader>
        <CardContent>
          {rulesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !rules || rules.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No routing rules configured</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Priority</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Conditions</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono">{r.priority}</TableCell>
                    <TableCell className="font-medium">{r.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{r.action}</Badge>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate text-xs font-mono">
                      {JSON.stringify(r.conditions)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={r.is_active ? 'default' : 'secondary'}>
                        {r.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function CJDQuickSettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="CJDQuick Integration Settings"
        description="Manage CJDQuick v3 logistics platform configuration — GST, tracking, notifications, RTO risk, weight, and routing."
      />

      <Tabs defaultValue="gst" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
          <TabsTrigger value="gst" className="gap-1">
            <FileText className="h-4 w-4 hidden sm:inline" />
            GST
          </TabsTrigger>
          <TabsTrigger value="tracking" className="gap-1">
            <Eye className="h-4 w-4 hidden sm:inline" />
            Tracking
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-1">
            <Bell className="h-4 w-4 hidden sm:inline" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="rto-risk" className="gap-1">
            <AlertTriangle className="h-4 w-4 hidden sm:inline" />
            RTO Risk
          </TabsTrigger>
          <TabsTrigger value="weight" className="gap-1">
            <Scale className="h-4 w-4 hidden sm:inline" />
            Weight
          </TabsTrigger>
          <TabsTrigger value="routing" className="gap-1">
            <Route className="h-4 w-4 hidden sm:inline" />
            Routing
          </TabsTrigger>
        </TabsList>

        <TabsContent value="gst">
          <GSTConfigTab />
        </TabsContent>
        <TabsContent value="tracking">
          <TrackingPageTab />
        </TabsContent>
        <TabsContent value="notifications">
          <NotificationsTab />
        </TabsContent>
        <TabsContent value="rto-risk">
          <RTORiskTab />
        </TabsContent>
        <TabsContent value="weight">
          <WeightManagementTab />
        </TabsContent>
        <TabsContent value="routing">
          <RoutingTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
