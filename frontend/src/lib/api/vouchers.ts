import apiClient from './client';

// Voucher Types
export type VoucherType =
  | 'CONTRA'
  | 'CREDIT_NOTE'
  | 'DEBIT_NOTE'
  | 'GST_SALE'
  | 'JOURNAL'
  | 'PAYMENT'
  | 'PURCHASE'
  | 'PURCHASE_RCM'
  | 'RCM_PAYMENT'
  | 'RECEIPT'
  | 'SALES';

export type VoucherStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'POSTED'
  | 'CANCELLED';

export type PartyType =
  | 'CUSTOMER'
  | 'VENDOR'
  | 'BANK'
  | 'CASH'
  | 'EMPLOYEE'
  | 'GOVERNMENT';

export type PaymentMode =
  | 'CASH'
  | 'CHEQUE'
  | 'RTGS'
  | 'NEFT'
  | 'UPI'
  | 'DD'
  | 'BANK_TRANSFER'
  | 'CARD';

// Interfaces
export interface VoucherLine {
  id: string;
  line_number: number;
  account_id: string;
  account_code?: string;
  account_name?: string;
  debit_amount: number;
  credit_amount: number;
  description?: string;
  cost_center_id?: string;
  hsn_code?: string;
  tax_rate?: number;
  is_tax_line: boolean;
  reference_line_id?: string;
  created_at: string;
}

export interface VoucherAllocation {
  id: string;
  voucher_id: string;
  source_type: string;
  source_id: string;
  source_number?: string;
  allocated_amount: number;
  tds_amount?: number;
  created_at: string;
  created_by?: string;
}

export interface Voucher {
  id: string;
  voucher_number: string;
  voucher_type: VoucherType;
  voucher_date: string;
  period_id?: string;
  narration: string;
  total_debit: number;
  total_credit: number;
  party_type?: PartyType;
  party_id?: string;
  party_name?: string;
  reference_type?: string;
  reference_id?: string;
  reference_number?: string;
  is_gst_applicable: boolean;
  gstin?: string;
  place_of_supply?: string;
  place_of_supply_code?: string;
  is_rcm: boolean;
  is_interstate: boolean;
  taxable_amount?: number;
  cgst_amount?: number;
  sgst_amount?: number;
  igst_amount?: number;
  cess_amount?: number;
  tds_amount?: number;
  payment_mode?: PaymentMode;
  bank_account_id?: string;
  cheque_number?: string;
  cheque_date?: string;
  transaction_reference?: string;
  status: VoucherStatus;
  approval_level?: string;
  rejection_reason?: string;
  is_reversed: boolean;
  reversal_voucher_id?: string;
  original_voucher_id?: string;
  journal_entry_id?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  submitted_by?: string;
  submitted_at?: string;
  approved_by?: string;
  approved_at?: string;
  posted_by?: string;
  posted_at?: string;
  cancelled_by?: string;
  cancelled_at?: string;
  cancellation_reason?: string;
  notes?: string;
  attachments?: Record<string, unknown>;
  lines: VoucherLine[];
  allocations: VoucherAllocation[];
  creator_name?: string;
  submitter_name?: string;
  approver_name?: string;
}

export interface VoucherLineCreate {
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description?: string;
  cost_center_id?: string;
  hsn_code?: string;
  tax_rate?: number;
  is_tax_line?: boolean;
  reference_line_id?: string;
}

export interface VoucherAllocationCreate {
  source_type: string;
  source_id: string;
  source_number?: string;
  allocated_amount: number;
  tds_amount?: number;
}

export interface VoucherCreate {
  voucher_type: VoucherType;
  voucher_date: string;
  narration: string;
  party_type?: PartyType;
  party_id?: string;
  party_name?: string;
  reference_type?: string;
  reference_id?: string;
  reference_number?: string;
  is_gst_applicable?: boolean;
  gstin?: string;
  place_of_supply?: string;
  place_of_supply_code?: string;
  is_rcm?: boolean;
  is_interstate?: boolean;
  taxable_amount?: number;
  cgst_amount?: number;
  sgst_amount?: number;
  igst_amount?: number;
  cess_amount?: number;
  tds_amount?: number;
  payment_mode?: PaymentMode;
  bank_account_id?: string;
  cheque_number?: string;
  cheque_date?: string;
  transaction_reference?: string;
  notes?: string;
  lines: VoucherLineCreate[];
  allocations?: VoucherAllocationCreate[];
}

export interface VoucherUpdate {
  voucher_date?: string;
  narration?: string;
  party_type?: PartyType;
  party_id?: string;
  party_name?: string;
  reference_type?: string;
  reference_id?: string;
  reference_number?: string;
  is_gst_applicable?: boolean;
  gstin?: string;
  place_of_supply?: string;
  place_of_supply_code?: string;
  is_rcm?: boolean;
  is_interstate?: boolean;
  taxable_amount?: number;
  cgst_amount?: number;
  sgst_amount?: number;
  igst_amount?: number;
  cess_amount?: number;
  tds_amount?: number;
  payment_mode?: PaymentMode;
  bank_account_id?: string;
  cheque_number?: string;
  cheque_date?: string;
  transaction_reference?: string;
  notes?: string;
  lines?: VoucherLineCreate[];
  allocations?: VoucherAllocationCreate[];
}

export interface VoucherListResponse {
  items: Voucher[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface VoucherWorkflowResponse {
  id: string;
  voucher_number: string;
  voucher_type: VoucherType;
  status: VoucherStatus;
  total_amount: number;
  narration: string;
  message: string;
  approval_level?: string;
}

export interface VoucherTypeMetadata {
  type: VoucherType;
  name: string;
  description: string;
  requires_party: boolean;
  party_types: string[];
  requires_bank: boolean;
  requires_gst: boolean;
  supports_allocation: boolean;
}

export interface VoucherTypesResponse {
  types: VoucherTypeMetadata[];
}

export interface PartyAccountOption {
  id: string;
  code: string;
  name: string;
  full_name: string;
  type: string;
  balance: number;
}

export interface PartyAccountsResponse {
  cash_accounts: PartyAccountOption[];
  bank_accounts: PartyAccountOption[];
  customer_accounts: PartyAccountOption[];
  vendor_accounts: PartyAccountOption[];
  expense_accounts: PartyAccountOption[];
  income_accounts: PartyAccountOption[];
}

export interface VoucherSummary {
  total_count: number;
  draft_count: number;
  pending_approval_count: number;
  approved_count: number;
  posted_count: number;
  cancelled_count: number;
  total_debit: number;
  total_credit: number;
  by_type: Record<string, number>;
}

export interface VoucherListParams {
  page?: number;
  size?: number;
  voucher_type?: VoucherType;
  status?: VoucherStatus;
  party_type?: PartyType;
  party_id?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

// Vouchers API
export const vouchersApi = {
  // CRUD Operations
  list: async (params?: VoucherListParams) => {
    const { data } = await apiClient.get<VoucherListResponse>('/vouchers', { params });
    return data;
  },

  getById: async (id: string) => {
    const { data } = await apiClient.get<Voucher>(`/vouchers/${id}`);
    return data;
  },

  create: async (voucher: VoucherCreate) => {
    const { data } = await apiClient.post<Voucher>('/vouchers', voucher);
    return data;
  },

  update: async (id: string, voucher: VoucherUpdate) => {
    const { data } = await apiClient.put<Voucher>(`/vouchers/${id}`, voucher);
    return data;
  },

  delete: async (id: string) => {
    await apiClient.delete(`/vouchers/${id}`);
  },

  // Workflow Operations
  submit: async (id: string, remarks?: string) => {
    const { data } = await apiClient.post<VoucherWorkflowResponse>(
      `/vouchers/${id}/submit`,
      { remarks }
    );
    return data;
  },

  approve: async (id: string, autoPost: boolean = true, remarks?: string) => {
    const { data } = await apiClient.post<VoucherWorkflowResponse>(
      `/vouchers/${id}/approve`,
      { auto_post: autoPost, remarks }
    );
    return data;
  },

  reject: async (id: string, reason: string) => {
    const { data } = await apiClient.post<VoucherWorkflowResponse>(
      `/vouchers/${id}/reject`,
      { reason }
    );
    return data;
  },

  post: async (id: string) => {
    const { data } = await apiClient.post<VoucherWorkflowResponse>(
      `/vouchers/${id}/post`
    );
    return data;
  },

  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post<VoucherWorkflowResponse>(
      `/vouchers/${id}/cancel`,
      { reason }
    );
    return data;
  },

  reverse: async (id: string, reversalDate: string, reason: string) => {
    const { data } = await apiClient.post<Voucher>(
      `/vouchers/${id}/reverse`,
      { reversal_date: reversalDate, reason }
    );
    return data;
  },

  // Metadata & Helper Endpoints
  getTypes: async () => {
    const { data } = await apiClient.get<VoucherTypesResponse>('/vouchers/types');
    return data;
  },

  getPartyAccounts: async () => {
    const { data } = await apiClient.get<PartyAccountsResponse>('/vouchers/party-accounts');
    return data;
  },

  getSummary: async (params?: { start_date?: string; end_date?: string; voucher_type?: VoucherType }) => {
    const { data } = await apiClient.get<VoucherSummary>('/vouchers/summary', { params });
    return data;
  },

  getPendingApprovals: async (params?: { approval_level?: string; voucher_type?: VoucherType; page?: number; size?: number }) => {
    const { data } = await apiClient.get<VoucherListResponse>('/vouchers/pending-approval', { params });
    return data;
  },
};

export default vouchersApi;
