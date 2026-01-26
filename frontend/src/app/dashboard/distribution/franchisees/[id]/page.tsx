'use client';

import { useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Building2,
  MapPin,
  FileText,
  GraduationCap,
  ClipboardCheck,
  LifeBuoy,
  Edit,
  Plus,
  Download,
  Phone,
  Mail,
  Calendar,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  MoreHorizontal,
  Trash2,
  Eye,
  Play,
  Pause,
  RefreshCw,
  Award,
  Star,
  MessageSquare,
  Users,
  TrendingUp,
  IndianRupee,
  FileCheck,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatCurrency, formatDate } from '@/lib/utils';
import { franchiseesApi } from '@/lib/api';

interface Contract {
  id: string;
  type: 'FRANCHISE_AGREEMENT' | 'RENEWAL' | 'AMENDMENT' | 'TERMINATION';
  contract_number: string;
  start_date: string;
  end_date: string;
  royalty_percentage: number;
  security_deposit: number;
  status: 'DRAFT' | 'PENDING_SIGNATURE' | 'ACTIVE' | 'EXPIRED' | 'TERMINATED';
  document_url?: string;
  signed_at?: string;
  terms: string;
}

interface TrainingModule {
  id: string;
  name: string;
  description: string;
  type: 'ONBOARDING' | 'PRODUCT' | 'SERVICE' | 'SALES' | 'COMPLIANCE';
  duration_hours: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'EXPIRED';
  progress: number;
  score?: number;
  passing_score: number;
  completed_at?: string;
  certificate_url?: string;
  due_date?: string;
}

interface Audit {
  id: string;
  audit_number: string;
  type: 'OPERATIONAL' | 'FINANCIAL' | 'COMPLIANCE' | 'QUALITY' | 'SAFETY';
  scheduled_date: string;
  completed_date?: string;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  score?: number;
  max_score: number;
  findings_count: number;
  critical_findings: number;
  auditor_name: string;
  report_url?: string;
  next_audit_date?: string;
}

interface SupportTicket {
  id: string;
  ticket_number: string;
  subject: string;
  category: 'TECHNICAL' | 'OPERATIONAL' | 'BILLING' | 'TRAINING' | 'COMPLAINT' | 'SUGGESTION';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'OPEN' | 'IN_PROGRESS' | 'WAITING_ON_FRANCHISEE' | 'RESOLVED' | 'CLOSED';
  description: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assigned_to?: string;
  messages_count: number;
}

interface FranchiseeDetail {
  id: string;
  code: string;
  name: string;
  owner_name: string;
  phone: string;
  email: string;
  status: 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'TERMINATED';
  territory: string;
  address: {
    line1: string;
    line2: string;
    city: string;
    state: string;
    pincode: string;
  };
  serviceable_pincodes: string[];
  bank_details: {
    bank_name: string;
    account_number: string;
    ifsc_code: string;
  };
  contracts: Contract[];
  training_modules: TrainingModule[];
  audits: Audit[];
  support_tickets: SupportTicket[];
  stats: {
    total_revenue: number;
    this_month_revenue: number;
    total_orders: number;
    active_technicians: number;
    avg_rating: number;
    total_reviews: number;
    royalty_due: number;
    royalty_paid: number;
    training_completion: number;
    compliance_score: number;
  };
  created_at: string;
  updated_at: string;
}

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  ACTIVE: 'bg-green-100 text-green-800',
  SUSPENDED: 'bg-red-100 text-red-800',
  TERMINATED: 'bg-gray-100 text-gray-800',
  DRAFT: 'bg-gray-100 text-gray-800',
  PENDING_SIGNATURE: 'bg-yellow-100 text-yellow-800',
  EXPIRED: 'bg-red-100 text-red-800',
};

const contractTypeLabels: Record<string, string> = {
  FRANCHISE_AGREEMENT: 'Franchise Agreement',
  RENEWAL: 'Renewal',
  AMENDMENT: 'Amendment',
  TERMINATION: 'Termination',
};

const trainingStatusColors: Record<string, string> = {
  NOT_STARTED: 'bg-gray-100 text-gray-800',
  IN_PROGRESS: 'bg-blue-100 text-blue-800',
  COMPLETED: 'bg-green-100 text-green-800',
  EXPIRED: 'bg-red-100 text-red-800',
};

const auditStatusColors: Record<string, string> = {
  SCHEDULED: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-gray-100 text-gray-800',
};

const ticketPriorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-800',
  MEDIUM: 'bg-blue-100 text-blue-800',
  HIGH: 'bg-orange-100 text-orange-800',
  URGENT: 'bg-red-100 text-red-800',
};

const ticketStatusColors: Record<string, string> = {
  OPEN: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  WAITING_ON_FRANCHISEE: 'bg-orange-100 text-orange-800',
  RESOLVED: 'bg-green-100 text-green-800',
  CLOSED: 'bg-gray-100 text-gray-800',
};

export default function FranchiseeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Dialog states
  const [isNewContractOpen, setIsNewContractOpen] = useState(false);
  const [isNewTicketOpen, setIsNewTicketOpen] = useState(false);
  const [isScheduleAuditOpen, setIsScheduleAuditOpen] = useState(false);
  const [isAssignTrainingOpen, setIsAssignTrainingOpen] = useState(false);

  // Form states
  const [ticketForm, setTicketForm] = useState({
    subject: '',
    category: 'OPERATIONAL' as 'TECHNICAL' | 'OPERATIONAL' | 'BILLING' | 'TRAINING' | 'COMPLAINT' | 'SUGGESTION',
    priority: 'MEDIUM' as 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT',
    description: '',
  });

  const [auditForm, setAuditForm] = useState({
    type: 'OPERATIONAL' as 'OPERATIONAL' | 'FINANCIAL' | 'COMPLIANCE' | 'QUALITY' | 'SAFETY',
    scheduled_date: '',
    auditor_name: '',
  });

  // Fetch franchisee details
  const { data: franchisee, isLoading } = useQuery<FranchiseeDetail>({
    queryKey: ['franchisee', id],
    queryFn: async () => {
      // Simulated API response
      return {
        id,
        code: 'FRC-001',
        name: 'Bengaluru South Franchise',
        owner_name: 'Rajesh Kumar',
        phone: '+91 98765 43210',
        email: 'rajesh@bsfranchise.com',
        status: 'ACTIVE',
        territory: 'Bengaluru South',
        address: {
          line1: '456 HSR Layout',
          line2: 'Sector 7',
          city: 'Bengaluru',
          state: 'Karnataka',
          pincode: '560102',
        },
        serviceable_pincodes: ['560102', '560103', '560104', '560105', '560068', '560076'],
        bank_details: {
          bank_name: 'ICICI Bank',
          account_number: 'XXXX XXXX 5678',
          ifsc_code: 'ICIC0001234',
        },
        contracts: [
          {
            id: '1',
            type: 'FRANCHISE_AGREEMENT',
            contract_number: 'FA-2024-001',
            start_date: '2024-01-01',
            end_date: '2026-12-31',
            royalty_percentage: 5,
            security_deposit: 500000,
            status: 'ACTIVE',
            signed_at: '2023-12-15',
            terms: '3-year franchise agreement with exclusive territory rights',
          },
          {
            id: '2',
            type: 'AMENDMENT',
            contract_number: 'AMD-2024-001',
            start_date: '2024-03-01',
            end_date: '2026-12-31',
            royalty_percentage: 4.5,
            security_deposit: 500000,
            status: 'ACTIVE',
            signed_at: '2024-02-25',
            terms: 'Royalty reduction for achieving Q1 targets',
          },
        ],
        training_modules: [
          { id: '1', name: 'Franchisee Onboarding', description: 'Complete onboarding program', type: 'ONBOARDING', duration_hours: 16, status: 'COMPLETED', progress: 100, score: 92, passing_score: 80, completed_at: '2024-01-10', certificate_url: '/certificates/1.pdf' },
          { id: '2', name: 'Product Knowledge - Water Purifiers', description: 'Technical training on water purifier products', type: 'PRODUCT', duration_hours: 8, status: 'COMPLETED', progress: 100, score: 88, passing_score: 75, completed_at: '2024-01-20' },
          { id: '3', name: 'Service Excellence', description: 'Customer service best practices', type: 'SERVICE', duration_hours: 4, status: 'IN_PROGRESS', progress: 65, passing_score: 80, due_date: '2024-04-15' },
          { id: '4', name: 'Sales Techniques', description: 'Advanced selling skills', type: 'SALES', duration_hours: 6, status: 'NOT_STARTED', progress: 0, passing_score: 75, due_date: '2024-05-01' },
          { id: '5', name: 'Compliance & Safety', description: 'Regulatory compliance training', type: 'COMPLIANCE', duration_hours: 4, status: 'NOT_STARTED', progress: 0, passing_score: 90, due_date: '2024-06-01' },
        ],
        audits: [
          { id: '1', audit_number: 'AUD-2024-001', type: 'OPERATIONAL', scheduled_date: '2024-02-15', completed_date: '2024-02-15', status: 'COMPLETED', score: 85, max_score: 100, findings_count: 3, critical_findings: 0, auditor_name: 'Priya Sharma', next_audit_date: '2024-05-15' },
          { id: '2', audit_number: 'AUD-2024-002', type: 'COMPLIANCE', scheduled_date: '2024-03-20', status: 'SCHEDULED', max_score: 100, findings_count: 0, critical_findings: 0, auditor_name: 'Amit Patel' },
        ],
        support_tickets: [
          { id: '1', ticket_number: 'TKT-10001', subject: 'Inventory sync issue', category: 'TECHNICAL', priority: 'HIGH', status: 'RESOLVED', description: 'Stock not reflecting in system', created_at: '2024-03-01', updated_at: '2024-03-02', resolved_at: '2024-03-02', assigned_to: 'Tech Support', messages_count: 5 },
          { id: '2', ticket_number: 'TKT-10015', subject: 'New product pricing query', category: 'BILLING', priority: 'MEDIUM', status: 'OPEN', description: 'Need clarification on new product margins', created_at: '2024-03-10', updated_at: '2024-03-10', messages_count: 2 },
          { id: '3', ticket_number: 'TKT-10018', subject: 'Marketing materials request', category: 'OPERATIONAL', priority: 'LOW', status: 'IN_PROGRESS', description: 'Requesting updated brochures and banners', created_at: '2024-03-12', updated_at: '2024-03-13', assigned_to: 'Marketing', messages_count: 3 },
        ],
        stats: {
          total_revenue: 4500000,
          this_month_revenue: 380000,
          total_orders: 856,
          active_technicians: 8,
          avg_rating: 4.6,
          total_reviews: 234,
          royalty_due: 22500,
          royalty_paid: 180000,
          training_completion: 60,
          compliance_score: 92,
        },
        created_at: '2024-01-01',
        updated_at: '2024-03-15',
      };
    },
  });

  // Mutations
  const createTicketMutation = useMutation({
    mutationFn: async (data: typeof ticketForm) => {
      // Map frontend priority to backend CRITICAL (URGENT -> CRITICAL)
      const backendPriority = data.priority === 'URGENT' ? 'CRITICAL' : data.priority;
      return franchiseesApi.createSupportTicket({
        franchisee_id: id,
        subject: data.subject,
        description: data.description,
        category: data.category,
        priority: backendPriority as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
        contact_name: franchisee?.owner_name || franchisee?.name || 'Unknown',
        contact_email: franchisee?.email,
        contact_phone: franchisee?.phone,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['franchisee', id] });
      queryClient.invalidateQueries({ queryKey: ['franchisee-support-tickets', id] });
      toast.success('Support ticket created');
      setIsNewTicketOpen(false);
      setTicketForm({ subject: '', category: 'OPERATIONAL', priority: 'MEDIUM', description: '' });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create support ticket');
    },
  });

  const scheduleAuditMutation = useMutation({
    mutationFn: async (data: typeof auditForm) => {
      return franchiseesApi.createAudit({
        franchisee_id: id,
        audit_type: data.type,
        scheduled_date: data.scheduled_date,
        auditor_name: data.auditor_name,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['franchisee', id] });
      queryClient.invalidateQueries({ queryKey: ['franchisee-audits', id] });
      toast.success('Audit scheduled');
      setIsScheduleAuditOpen(false);
      setAuditForm({ type: 'OPERATIONAL', scheduled_date: '', auditor_name: '' });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to schedule audit');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!franchisee) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h2 className="text-xl font-semibold">Franchisee not found</h2>
        <Button className="mt-4" onClick={() => router.back()}>
          Go Back
        </Button>
      </div>
    );
  }

  const activeContract = franchisee.contracts.find(c => c.status === 'ACTIVE' && c.type === 'FRANCHISE_AGREEMENT');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{franchisee.name}</h1>
              <Badge className={statusColors[franchisee.status]}>{franchisee.status}</Badge>
            </div>
            <p className="text-muted-foreground">
              {franchisee.code} | Owner: {franchisee.owner_name} | Territory: {franchisee.territory}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Edit className="mr-2 h-4 w-4" /> Edit
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" /> Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(franchisee.stats.total_revenue)}</div>
            <div className="text-sm text-muted-foreground">
              This month: {formatCurrency(franchisee.stats.this_month_revenue)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{franchisee.stats.total_orders}</div>
            <div className="flex items-center gap-1 text-sm">
              <Users className="h-4 w-4 text-muted-foreground" />
              {franchisee.stats.active_technicians} technicians
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rating</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-1">
              <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
              <span className="text-2xl font-bold">{franchisee.stats.avg_rating}</span>
            </div>
            <div className="text-sm text-muted-foreground">
              {franchisee.stats.total_reviews} reviews
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Training Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{franchisee.stats.training_completion}%</div>
            <Progress value={franchisee.stats.training_completion} className="mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Compliance Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{franchisee.stats.compliance_score}%</div>
            <Progress value={franchisee.stats.compliance_score} className="mt-2 [&>div]:bg-green-500" />
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="contracts">Contracts</TabsTrigger>
          <TabsTrigger value="training">Training</TabsTrigger>
          <TabsTrigger value="audits">Audits</TabsTrigger>
          <TabsTrigger value="support">Support Tickets</TabsTrigger>
          <TabsTrigger value="financials">Financials</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Contact & Address */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Contact Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{franchisee.email}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>{franchisee.phone}</span>
                </div>
                <div className="flex items-start gap-3">
                  <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p>{franchisee.address.line1}</p>
                    {franchisee.address.line2 && <p>{franchisee.address.line2}</p>}
                    <p>{franchisee.address.city}, {franchisee.address.state} - {franchisee.address.pincode}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Active Contract */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Active Contract</CardTitle>
              </CardHeader>
              <CardContent>
                {activeContract ? (
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Contract #</span>
                      <span className="font-medium">{activeContract.contract_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Validity</span>
                      <span>{formatDate(activeContract.start_date)} - {formatDate(activeContract.end_date)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Royalty</span>
                      <span className="font-medium">{activeContract.royalty_percentage}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Security Deposit</span>
                      <span className="font-medium">{formatCurrency(activeContract.security_deposit)}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No active contract</p>
                )}
              </CardContent>
            </Card>

            {/* Serviceable Pincodes */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Serviceable Area</CardTitle>
                <CardDescription>{franchisee.serviceable_pincodes.length} pincodes assigned</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {franchisee.serviceable_pincodes.map((pincode) => (
                    <Badge key={pincode} variant="outline">{pincode}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Royalty Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Royalty Paid</span>
                  <span className="font-medium text-green-600">{formatCurrency(franchisee.stats.royalty_paid)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Royalty Due</span>
                  <span className="font-medium text-orange-600">{formatCurrency(franchisee.stats.royalty_due)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Contracts Tab */}
        <TabsContent value="contracts" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Contract History</CardTitle>
                <CardDescription>All agreements and amendments</CardDescription>
              </div>
              <Button onClick={() => setIsNewContractOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> New Contract
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {franchisee.contracts.map((contract) => (
                  <div key={contract.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div>
                          <h4 className="font-medium">{contractTypeLabels[contract.type]}</h4>
                          <p className="text-sm text-muted-foreground">{contract.contract_number}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={statusColors[contract.status]}>{contract.status}</Badge>
                        {contract.document_url && (
                          <Button variant="outline" size="sm">
                            <Download className="mr-2 h-4 w-4" /> Download
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="grid gap-4 md:grid-cols-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Period</p>
                        <p className="font-medium">{formatDate(contract.start_date)} - {formatDate(contract.end_date)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Royalty</p>
                        <p className="font-medium">{contract.royalty_percentage}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Security Deposit</p>
                        <p className="font-medium">{formatCurrency(contract.security_deposit)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Signed</p>
                        <p className="font-medium">{contract.signed_at ? formatDate(contract.signed_at) : 'Pending'}</p>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-3">{contract.terms}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Training Tab */}
        <TabsContent value="training" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Training Modules</CardTitle>
                <CardDescription>Required and optional training programs</CardDescription>
              </div>
              <Button onClick={() => setIsAssignTrainingOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> Assign Training
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {franchisee.training_modules.map((module) => (
                  <div key={module.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                          module.status === 'COMPLETED' ? 'bg-green-100' :
                          module.status === 'IN_PROGRESS' ? 'bg-blue-100' : 'bg-gray-100'
                        }`}>
                          <GraduationCap className={`h-5 w-5 ${
                            module.status === 'COMPLETED' ? 'text-green-600' :
                            module.status === 'IN_PROGRESS' ? 'text-blue-600' : 'text-gray-600'
                          }`} />
                        </div>
                        <div>
                          <h4 className="font-medium">{module.name}</h4>
                          <p className="text-sm text-muted-foreground">{module.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={trainingStatusColors[module.status]}>
                          {module.status.replace(/_/g, ' ')}
                        </Badge>
                        {module.certificate_url && (
                          <Button variant="outline" size="sm">
                            <Award className="mr-2 h-4 w-4" /> Certificate
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="grid gap-4 md:grid-cols-4 text-sm mb-3">
                      <div>
                        <p className="text-muted-foreground">Type</p>
                        <p className="font-medium">{module.type}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Duration</p>
                        <p className="font-medium">{module.duration_hours} hours</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Score</p>
                        <p className="font-medium">
                          {module.score ? `${module.score}/${module.passing_score}` : `Pass: ${module.passing_score}%`}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">{module.completed_at ? 'Completed' : 'Due Date'}</p>
                        <p className="font-medium">
                          {module.completed_at ? formatDate(module.completed_at) :
                           module.due_date ? formatDate(module.due_date) : '-'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={module.progress} className="flex-1" />
                      <span className="text-sm font-medium">{module.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audits Tab */}
        <TabsContent value="audits" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Audit History</CardTitle>
                <CardDescription>Scheduled and completed audits</CardDescription>
              </div>
              <Button onClick={() => setIsScheduleAuditOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> Schedule Audit
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Audit #</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Scheduled Date</TableHead>
                    <TableHead>Auditor</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Findings</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {franchisee.audits.map((audit) => (
                    <TableRow key={audit.id}>
                      <TableCell className="font-mono text-sm">{audit.audit_number}</TableCell>
                      <TableCell>{audit.type}</TableCell>
                      <TableCell>{formatDate(audit.scheduled_date)}</TableCell>
                      <TableCell>{audit.auditor_name}</TableCell>
                      <TableCell>
                        {audit.score ? (
                          <span className={audit.score >= 80 ? 'text-green-600' : audit.score >= 60 ? 'text-yellow-600' : 'text-red-600'}>
                            {audit.score}/{audit.max_score}
                          </span>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        {audit.status === 'COMPLETED' ? (
                          <div className="flex items-center gap-2">
                            <span>{audit.findings_count} total</span>
                            {audit.critical_findings > 0 && (
                              <Badge variant="destructive">{audit.critical_findings} critical</Badge>
                            )}
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className={auditStatusColors[audit.status]}>{audit.status}</Badge>
                      </TableCell>
                      <TableCell>
                        {audit.report_url && (
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Support Tickets Tab */}
        <TabsContent value="support" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Support Tickets</CardTitle>
                <CardDescription>Issues and requests from this franchisee</CardDescription>
              </div>
              <Button onClick={() => setIsNewTicketOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> New Ticket
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {franchisee.support_tickets.map((ticket) => (
                  <div key={ticket.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                          ticket.status === 'RESOLVED' || ticket.status === 'CLOSED' ? 'bg-green-100' :
                          ticket.status === 'OPEN' ? 'bg-blue-100' : 'bg-yellow-100'
                        }`}>
                          <LifeBuoy className={`h-5 w-5 ${
                            ticket.status === 'RESOLVED' || ticket.status === 'CLOSED' ? 'text-green-600' :
                            ticket.status === 'OPEN' ? 'text-blue-600' : 'text-yellow-600'
                          }`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{ticket.subject}</h4>
                            <span className="text-sm text-muted-foreground">#{ticket.ticket_number}</span>
                          </div>
                          <p className="text-sm text-muted-foreground">{ticket.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={ticketPriorityColors[ticket.priority]}>{ticket.priority}</Badge>
                        <Badge className={ticketStatusColors[ticket.status]}>{ticket.status.replace(/_/g, ' ')}</Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm text-muted-foreground mt-3 pt-3 border-t">
                      <div className="flex items-center gap-4">
                        <span>Category: {ticket.category}</span>
                        <span className="flex items-center gap-1">
                          <MessageSquare className="h-4 w-4" />
                          {ticket.messages_count} messages
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span>Created: {formatDate(ticket.created_at)}</span>
                        {ticket.resolved_at && <span>Resolved: {formatDate(ticket.resolved_at)}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Financials Tab */}
        <TabsContent value="financials" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Royalty Paid</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{formatCurrency(franchisee.stats.royalty_paid)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Royalty Due</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">{formatCurrency(franchisee.stats.royalty_due)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Security Deposit</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(activeContract?.security_deposit || 0)}</div>
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Royalty Statements</CardTitle>
              <CardDescription>Monthly royalty calculations and payments</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground text-center py-8">
                Royalty statements will be displayed here.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* New Ticket Dialog */}
      <Dialog open={isNewTicketOpen} onOpenChange={setIsNewTicketOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Support Ticket</DialogTitle>
            <DialogDescription>Log a new support request for this franchisee</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                placeholder="Brief description of the issue"
                value={ticketForm.subject}
                onChange={(e) => setTicketForm({ ...ticketForm, subject: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={ticketForm.category}
                  onValueChange={(value: typeof ticketForm.category) => setTicketForm({ ...ticketForm, category: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TECHNICAL">Technical</SelectItem>
                    <SelectItem value="OPERATIONAL">Operational</SelectItem>
                    <SelectItem value="BILLING">Billing</SelectItem>
                    <SelectItem value="TRAINING">Training</SelectItem>
                    <SelectItem value="COMPLAINT">Complaint</SelectItem>
                    <SelectItem value="SUGGESTION">Suggestion</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select
                  value={ticketForm.priority}
                  onValueChange={(value: typeof ticketForm.priority) => setTicketForm({ ...ticketForm, priority: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">Low</SelectItem>
                    <SelectItem value="MEDIUM">Medium</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="URGENT">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Detailed description..."
                value={ticketForm.description}
                onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewTicketOpen(false)}>Cancel</Button>
            <Button onClick={() => createTicketMutation.mutate(ticketForm)}>Create Ticket</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Audit Dialog */}
      <Dialog open={isScheduleAuditOpen} onOpenChange={setIsScheduleAuditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule Audit</DialogTitle>
            <DialogDescription>Schedule a new audit for this franchisee</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Audit Type</Label>
              <Select
                value={auditForm.type}
                onValueChange={(value: typeof auditForm.type) => setAuditForm({ ...auditForm, type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="OPERATIONAL">Operational</SelectItem>
                  <SelectItem value="FINANCIAL">Financial</SelectItem>
                  <SelectItem value="COMPLIANCE">Compliance</SelectItem>
                  <SelectItem value="QUALITY">Quality</SelectItem>
                  <SelectItem value="SAFETY">Safety</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="audit_date">Scheduled Date</Label>
              <Input
                id="audit_date"
                type="date"
                value={auditForm.scheduled_date}
                onChange={(e) => setAuditForm({ ...auditForm, scheduled_date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="auditor">Auditor Name</Label>
              <Input
                id="auditor"
                placeholder="Name of the auditor"
                value={auditForm.auditor_name}
                onChange={(e) => setAuditForm({ ...auditForm, auditor_name: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsScheduleAuditOpen(false)}>Cancel</Button>
            <Button onClick={() => scheduleAuditMutation.mutate(auditForm)}>Schedule</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
