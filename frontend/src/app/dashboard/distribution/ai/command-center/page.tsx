'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Brain, AlertTriangle, TrendingUp, TrendingDown, Users, IndianRupee,
  RefreshCw, ChevronDown, ChevronUp, Target, Activity, Zap,
  BarChart3, Clock, DollarSign, Package, Award
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { dmsAiApi } from '@/lib/api';

// ─── Types ─────────────────────────────────────────────────────────────────

interface Alert {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  dealer?: string;
  scheme?: string;
  message: string;
  action: string;
}

interface DealerScore {
  dealer_id: string;
  name: string;
  tier: string;
  severity: string;
  achievement_pct: number | null;
  revenue_achieved: number;
  revenue_target: number;
  overdue_amount: number;
  growth_pct: number | null;
}

interface DealerForecast {
  dealer_id: string;
  name: string;
  tier: string;
  total_6m_revenue: number;
  forecast_next_month: number;
  growth_pct: number | null;
  anomaly: string | null;
  days_since_last_order: number;
  is_inactive: boolean;
}

interface SchemeData {
  scheme_name: string;
  scheme_type: string;
  roi_pct: number | null;
  participation_rate: number;
  budget_utilization_pct: number | null;
  recommendation: string;
  days_remaining: number;
}

interface PriorityDealer {
  dealer_name: string;
  tier: string;
  total_overdue: number;
  max_days_overdue: number;
  priority: string;
  strategy: string;
  invoice_count: number;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const severityColor: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-800 border-red-200',
  HIGH: 'bg-orange-100 text-orange-800 border-orange-200',
  MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  LOW: 'bg-green-100 text-green-800 border-green-200',
  OK: 'bg-green-100 text-green-800 border-green-200',
  NO_TARGET: 'bg-gray-100 text-gray-600 border-gray-200',
};

const tierColor: Record<string, string> = {
  PLATINUM: 'bg-purple-100 text-purple-800',
  GOLD: 'bg-yellow-100 text-yellow-800',
  SILVER: 'bg-gray-100 text-gray-600',
  BRONZE: 'bg-orange-100 text-orange-800',
};

const recColor: Record<string, string> = {
  RETIRE: 'bg-red-100 text-red-700',
  EXTEND: 'bg-green-100 text-green-700',
  PROMOTE: 'bg-blue-100 text-blue-700',
  MAINTAIN: 'bg-gray-100 text-gray-700',
};

// ─── Sub-components ─────────────────────────────────────────────────────────

function SummaryCard({
  title, value, sub, icon: Icon, color
}: {
  title: string; value: string; sub?: string; icon: React.ElementType; color: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">{title}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
            {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
          </div>
          <div className={`rounded-xl p-3 ${color.replace('text-', 'bg-').replace('-600', '-100').replace('-800', '-100')}`}>
            <Icon className={`h-5 w-5 ${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AlertItem({ alert }: { alert: Alert }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`rounded-lg border p-3 ${severityColor[alert.severity] || severityColor.LOW}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={`text-xs ${severityColor[alert.severity]}`}>
              {alert.severity}
            </Badge>
            <span className="text-xs font-medium">{alert.type.replace(/_/g, ' ')}</span>
          </div>
          <p className="text-sm font-medium">{alert.message}</p>
          {expanded && (
            <p className="text-xs mt-1 opacity-75">→ {alert.action}</p>
          )}
        </div>
        <button onClick={() => setExpanded(!expanded)} className="shrink-0 opacity-60 hover:opacity-100">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}

// ─── Dealer Performance Tab ──────────────────────────────────────────────────

function DealerPerformanceTab({ data }: { data: { dealer_scores: DealerScore[]; summary: Record<string, number> } }) {
  const scores = data.dealer_scores ?? [];
  const s = data.summary ?? {};
  return (
    <div className="space-y-4">
      {/* Summary pills */}
      <div className="flex flex-wrap gap-2">
        {[
          { label: 'Critical', count: s.critical, color: 'bg-red-100 text-red-800' },
          { label: 'High Risk', count: s.high, color: 'bg-orange-100 text-orange-800' },
          { label: 'Medium', count: s.medium, color: 'bg-yellow-100 text-yellow-800' },
          { label: 'On Track', count: s.ok, color: 'bg-green-100 text-green-800' },
        ].map(({ label, count, color }) => (
          count > 0 && (
            <span key={label} className={`rounded-full px-3 py-1 text-xs font-medium ${color}`}>
              {count} {label}
            </span>
          )
        ))}
      </div>

      {/* Table */}
      <div className="rounded-lg border overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left p-3 font-medium">Dealer</th>
              <th className="text-left p-3 font-medium">Tier</th>
              <th className="text-right p-3 font-medium">Achievement</th>
              <th className="text-right p-3 font-medium">Revenue</th>
              <th className="text-right p-3 font-medium">Overdue</th>
              <th className="text-right p-3 font-medium">Growth</th>
            </tr>
          </thead>
          <tbody>
            {scores.slice(0, 15).map((d) => (
              <tr key={d.dealer_id} className="border-t hover:bg-muted/20">
                <td className="p-3">
                  <div className="font-medium">{d.name}</div>
                  <Badge variant="outline" className={`text-xs mt-0.5 ${severityColor[d.severity]}`}>
                    {d.severity}
                  </Badge>
                </td>
                <td className="p-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tierColor[d.tier] ?? 'bg-gray-100 text-gray-600'}`}>
                    {d.tier ?? '—'}
                  </span>
                </td>
                <td className="p-3 text-right">
                  {d.achievement_pct != null ? (
                    <span className={d.achievement_pct >= 85 ? 'text-green-600 font-medium' : d.achievement_pct < 50 ? 'text-red-600 font-bold' : 'text-orange-600 font-medium'}>
                      {d.achievement_pct.toFixed(1)}%
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
                <td className="p-3 text-right text-muted-foreground">{fmt(d.revenue_achieved)}</td>
                <td className="p-3 text-right">
                  {d.overdue_amount > 0 ? (
                    <span className="text-red-600">{fmt(d.overdue_amount)}</span>
                  ) : (
                    <span className="text-green-600">✓</span>
                  )}
                </td>
                <td className="p-3 text-right">
                  {d.growth_pct != null ? (
                    <span className={d.growth_pct >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {d.growth_pct > 0 ? '+' : ''}{d.growth_pct.toFixed(1)}%
                    </span>
                  ) : '—'}
                </td>
              </tr>
            ))}
            {scores.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">No dealer data available</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Demand Sensing Tab ──────────────────────────────────────────────────────

function DemandSensingTab({ data }: { data: { dealer_forecasts: DealerForecast[]; summary: Record<string, number>; inactive_dealers: { dealer: string; days_inactive: number; last_order: string }[] } }) {
  const forecasts = data.dealer_forecasts ?? [];
  const inactive = data.inactive_dealers ?? [];
  const s = data.summary ?? {};
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">Forecast Next Month</p>
          <p className="text-lg font-bold">{fmt(s.forecast_next_month_total ?? 0)}</p>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">Current Month</p>
          <p className="text-lg font-bold">{fmt(s.current_month_revenue ?? 0)}</p>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">MoM Growth</p>
          <p className={`text-lg font-bold ${(s.mom_growth_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {(s.mom_growth_pct ?? 0) > 0 ? '+' : ''}{(s.mom_growth_pct ?? 0).toFixed(1)}%
          </p>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">Inactive Dealers</p>
          <p className={`text-lg font-bold ${(s.inactive_dealers ?? 0) > 0 ? 'text-orange-600' : 'text-green-600'}`}>
            {s.inactive_dealers ?? 0}
          </p>
        </div>
      </div>

      <div className="rounded-lg border overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left p-3 font-medium">Dealer</th>
              <th className="text-right p-3 font-medium">6M Revenue</th>
              <th className="text-right p-3 font-medium">Next Month Forecast</th>
              <th className="text-right p-3 font-medium">MoM</th>
              <th className="text-center p-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {forecasts.slice(0, 15).map((d) => (
              <tr key={d.dealer_id} className="border-t hover:bg-muted/20">
                <td className="p-3">
                  <div className="font-medium">{d.name}</div>
                  <span className={`text-xs ${tierColor[d.tier] ?? ''} rounded-full px-2 py-0.5`}>{d.tier ?? '—'}</span>
                </td>
                <td className="p-3 text-right text-muted-foreground">{fmt(d.total_6m_revenue)}</td>
                <td className="p-3 text-right font-medium">{fmt(d.forecast_next_month)}</td>
                <td className="p-3 text-right">
                  {d.growth_pct != null ? (
                    <span className={d.growth_pct >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {d.growth_pct > 0 ? '+' : ''}{d.growth_pct.toFixed(1)}%
                    </span>
                  ) : '—'}
                </td>
                <td className="p-3 text-center">
                  {d.is_inactive ? (
                    <Badge variant="outline" className="bg-orange-100 text-orange-700 text-xs">Inactive {d.days_since_last_order}d</Badge>
                  ) : d.anomaly ? (
                    <Badge variant="outline" className={d.anomaly === 'SPIKE' ? 'bg-blue-100 text-blue-700 text-xs' : 'bg-red-100 text-red-700 text-xs'}>
                      {d.anomaly}
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-green-100 text-green-700 text-xs">Active</Badge>
                  )}
                </td>
              </tr>
            ))}
            {forecasts.length === 0 && (
              <tr><td colSpan={5} className="p-8 text-center text-muted-foreground">No forecast data available</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {inactive.length > 0 && (
        <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
          <h4 className="font-medium text-orange-800 mb-2">Inactive Dealers (30+ days)</h4>
          <div className="space-y-1">
            {inactive.map((d) => (
              <div key={d.dealer} className="text-sm text-orange-700">
                {d.dealer} — {d.days_inactive} days inactive (last order: {d.last_order})
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Scheme Effectiveness Tab ────────────────────────────────────────────────

function SchemeEffectivenessTab({ data }: { data: { schemes: SchemeData[]; summary: Record<string, number> } }) {
  const schemes = data.schemes ?? [];
  const s = data.summary ?? {};
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">Active Schemes</p>
          <p className="text-lg font-bold">{s.active_schemes ?? 0}</p>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">Avg ROI</p>
          <p className="text-lg font-bold text-green-600">{(s.avg_roi_pct ?? 0).toFixed(1)}%</p>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <p className="text-xs text-muted-foreground">Orders Driven</p>
          <p className="text-lg font-bold">{fmt(s.total_order_value_driven ?? 0)}</p>
        </div>
      </div>

      <div className="rounded-lg border overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left p-3 font-medium">Scheme</th>
              <th className="text-right p-3 font-medium">ROI</th>
              <th className="text-right p-3 font-medium">Participation</th>
              <th className="text-right p-3 font-medium">Budget Used</th>
              <th className="text-right p-3 font-medium">Days Left</th>
              <th className="text-center p-3 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {schemes.map((s, i) => (
              <tr key={i} className="border-t hover:bg-muted/20">
                <td className="p-3">
                  <div className="font-medium">{s.scheme_name}</div>
                  <div className="text-xs text-muted-foreground">{s.scheme_type}</div>
                </td>
                <td className="p-3 text-right">
                  {s.roi_pct != null ? (
                    <span className={s.roi_pct >= 200 ? 'text-green-600 font-medium' : 'text-red-600'}>
                      {s.roi_pct.toFixed(0)}%
                    </span>
                  ) : '—'}
                </td>
                <td className="p-3 text-right">{s.participation_rate.toFixed(0)}%</td>
                <td className="p-3 text-right">
                  {s.budget_utilization_pct != null ? (
                    <span className={s.budget_utilization_pct > 90 ? 'text-red-600 font-medium' : 'text-muted-foreground'}>
                      {s.budget_utilization_pct.toFixed(0)}%
                    </span>
                  ) : '—'}
                </td>
                <td className="p-3 text-right">
                  <span className={s.days_remaining <= 7 ? 'text-red-600 font-medium' : 'text-muted-foreground'}>
                    {s.days_remaining}d
                  </span>
                </td>
                <td className="p-3 text-center">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${recColor[s.recommendation] ?? 'bg-gray-100 text-gray-600'}`}>
                    {s.recommendation}
                  </span>
                </td>
              </tr>
            ))}
            {schemes.length === 0 && (
              <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No active schemes</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Collection Optimizer Tab ────────────────────────────────────────────────

function CollectionOptimizerTab({ data }: {
  data: {
    priority_list: PriorityDealer[];
    aging_buckets: Record<string, { amount: number; invoices: number; dealers: number }>;
    summary: Record<string, number>;
  }
}) {
  const list = data.priority_list ?? [];
  const buckets = data.aging_buckets ?? {};
  const s = data.summary ?? {};

  const bucketRows = [
    { key: '0_30_days', label: '0–30 days', color: 'text-green-600' },
    { key: '31_60_days', label: '31–60 days', color: 'text-yellow-600' },
    { key: '61_90_days', label: '61–90 days', color: 'text-orange-600' },
    { key: '90_plus_days', label: '90+ days', color: 'text-red-600' },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        {bucketRows.map(({ key, label, color }) => (
          <div key={key} className="rounded-lg bg-muted/40 p-3">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className={`text-lg font-bold ${color}`}>{fmt(buckets[key]?.amount ?? 0)}</p>
            <p className="text-xs text-muted-foreground">{buckets[key]?.dealers ?? 0} dealers</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left p-3 font-medium">Dealer</th>
              <th className="text-right p-3 font-medium">Overdue</th>
              <th className="text-right p-3 font-medium">Max Days</th>
              <th className="text-center p-3 font-medium">Priority</th>
              <th className="text-left p-3 font-medium">Strategy</th>
            </tr>
          </thead>
          <tbody>
            {list.slice(0, 15).map((d, i) => (
              <tr key={i} className="border-t hover:bg-muted/20">
                <td className="p-3">
                  <div className="font-medium">{d.dealer_name}</div>
                  <span className={`text-xs ${tierColor[d.tier] ?? 'bg-gray-100 text-gray-600'} rounded-full px-2 py-0.5`}>{d.tier}</span>
                </td>
                <td className="p-3 text-right font-medium text-red-600">{fmt(d.total_overdue)}</td>
                <td className="p-3 text-right">{d.max_days_overdue}d</td>
                <td className="p-3 text-center">
                  <Badge variant="outline" className={`text-xs ${severityColor[d.priority] ?? ''}`}>{d.priority}</Badge>
                </td>
                <td className="p-3 text-xs text-muted-foreground max-w-[200px] truncate" title={d.strategy}>{d.strategy}</td>
              </tr>
            ))}
            {list.length === 0 && (
              <tr><td colSpan={5} className="p-8 text-center text-muted-foreground">No overdue invoices</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function DMSCommandCenterPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['dms-command-center'],
    queryFn: () => dmsAiApi.getCommandCenter(),
    staleTime: 2 * 60 * 1000, // 2 min cache
  });

  const summary = data?.summary ?? {};
  const alerts: Alert[] = data?.alerts ?? [];
  const dp = data?.dealer_performance ?? { dealer_scores: [], summary: {} };
  const ds = data?.demand_sensing ?? { dealer_forecasts: [], summary: {}, inactive_dealers: [] };
  const se = data?.scheme_effectiveness ?? { schemes: [], summary: {} };
  const co = data?.collection_optimizer ?? { priority_list: [], aging_buckets: {}, summary: {} };

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-600" />
            <h1 className="text-2xl font-bold">DMS AI Command Centre</h1>
            <Badge className="bg-purple-100 text-purple-700 border-purple-200 ml-1">AI</Badge>
          </div>
          <p className="text-muted-foreground mt-0.5">
            Real-time intelligence across your dealer network — performance, demand, schemes & collections
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Running AI agents…</span>
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-700 font-medium">Failed to load DMS intelligence data</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>Try again</Button>
        </div>
      )}

      {!isLoading && !isError && data && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <SummaryCard
              title="Active Dealers"
              value={String(summary.active_dealers ?? 0)}
              sub={`${summary.critical_dealers ?? 0} critical`}
              icon={Users}
              color="text-blue-600"
            />
            <SummaryCard
              title="Total Outstanding"
              value={fmt(summary.total_outstanding ?? 0)}
              sub={`${fmt(summary.total_overdue ?? 0)} overdue`}
              icon={IndianRupee}
              color="text-red-600"
            />
            <SummaryCard
              title="Next Month Forecast"
              value={fmt(summary.forecast_next_month ?? 0)}
              sub={`${summary.inactive_dealers ?? 0} inactive dealers`}
              icon={TrendingUp}
              color="text-green-600"
            />
            <SummaryCard
              title="Active Schemes"
              value={String(summary.active_schemes ?? 0)}
              sub={`Avg ROI: ${(summary.avg_scheme_roi_pct ?? 0).toFixed(1)}%`}
              icon={Target}
              color="text-purple-600"
            />
          </div>

          {/* Alerts */}
          {alerts.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                  Active Alerts ({alerts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2">
                  {alerts.map((a, i) => <AlertItem key={i} alert={a} />)}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Agent Tabs */}
          <Card>
            <CardContent className="p-4">
              <Tabs defaultValue="performance">
                <TabsList className="grid w-full grid-cols-4 mb-4">
                  <TabsTrigger value="performance" className="text-xs">
                    <Activity className="h-3 w-3 mr-1" />
                    Performance
                    {(summary.critical_dealers ?? 0) > 0 && (
                      <span className="ml-1 rounded-full bg-red-500 text-white text-xs px-1.5 py-0.5 leading-none">
                        {summary.critical_dealers}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="demand" className="text-xs">
                    <BarChart3 className="h-3 w-3 mr-1" />
                    Demand
                  </TabsTrigger>
                  <TabsTrigger value="schemes" className="text-xs">
                    <Package className="h-3 w-3 mr-1" />
                    Schemes
                  </TabsTrigger>
                  <TabsTrigger value="collections" className="text-xs">
                    <DollarSign className="h-3 w-3 mr-1" />
                    Collections
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="performance">
                  <DealerPerformanceTab data={dp as { dealer_scores: DealerScore[]; summary: Record<string, number> }} />
                </TabsContent>
                <TabsContent value="demand">
                  <DemandSensingTab data={ds as { dealer_forecasts: DealerForecast[]; summary: Record<string, number>; inactive_dealers: { dealer: string; days_inactive: number; last_order: string }[] }} />
                </TabsContent>
                <TabsContent value="schemes">
                  <SchemeEffectivenessTab data={se as { schemes: SchemeData[]; summary: Record<string, number> }} />
                </TabsContent>
                <TabsContent value="collections">
                  <CollectionOptimizerTab data={co as { priority_list: PriorityDealer[]; aging_buckets: Record<string, { amount: number; invoices: number; dealers: number }>; summary: Record<string, number> }} />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Run info */}
          {data.run_at && (
            <p className="text-xs text-muted-foreground text-right">
              Last run: {new Date(data.run_at).toLocaleString()}
            </p>
          )}
        </>
      )}
    </div>
  );
}
