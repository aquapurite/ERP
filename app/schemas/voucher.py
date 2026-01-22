"""Pydantic schemas for Voucher module."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer


# ==================== Enums for Validation ====================

class VoucherType(str, Enum):
    """Voucher type classification."""
    CONTRA = "CONTRA"
    CREDIT_NOTE = "CREDIT_NOTE"
    DEBIT_NOTE = "DEBIT_NOTE"
    GST_SALE = "GST_SALE"
    JOURNAL = "JOURNAL"
    PAYMENT = "PAYMENT"
    PURCHASE = "PURCHASE"
    PURCHASE_RCM = "PURCHASE_RCM"
    RCM_PAYMENT = "RCM_PAYMENT"
    RECEIPT = "RECEIPT"
    SALES = "SALES"


class VoucherStatus(str, Enum):
    """Voucher workflow status."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class PartyType(str, Enum):
    """Party type for voucher transactions."""
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    BANK = "BANK"
    CASH = "CASH"
    EMPLOYEE = "EMPLOYEE"
    GOVERNMENT = "GOVERNMENT"


class PaymentMode(str, Enum):
    """Payment mode options."""
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    RTGS = "RTGS"
    NEFT = "NEFT"
    UPI = "UPI"
    DD = "DD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"


# ==================== Voucher Line Schemas ====================

class VoucherLineBase(BaseModel):
    """Base schema for VoucherLine - NO validators here."""
    account_id: UUID
    debit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    description: Optional[str] = None
    cost_center_id: Optional[UUID] = None
    hsn_code: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    is_tax_line: bool = False
    reference_line_id: Optional[UUID] = None

    model_config = ConfigDict(populate_by_name=True)


class VoucherLineCreate(VoucherLineBase):
    """Schema for creating VoucherLine - validators allowed here."""

    @field_validator('debit_amount', 'credit_amount', mode='before')
    @classmethod
    def coerce_decimal(cls, v):
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class VoucherLineResponse(VoucherLineBase):
    """Response schema for VoucherLine."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_number: int
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    created_at: datetime

    @field_serializer('debit_amount', 'credit_amount')
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value) if value is not None else 0.0


# ==================== Voucher Allocation Schemas ====================

class VoucherAllocationBase(BaseModel):
    """Base schema for VoucherAllocation."""
    source_type: str
    source_id: UUID
    source_number: Optional[str] = None
    allocated_amount: Decimal = Field(..., ge=0)
    tds_amount: Optional[Decimal] = Field(default=None, ge=0)

    model_config = ConfigDict(populate_by_name=True)


class VoucherAllocationCreate(VoucherAllocationBase):
    """Schema for creating VoucherAllocation."""
    pass


class VoucherAllocationResponse(VoucherAllocationBase):
    """Response schema for VoucherAllocation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    voucher_id: UUID
    created_at: datetime
    created_by: Optional[UUID] = None

    @field_serializer('allocated_amount', 'tds_amount')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None


# ==================== Voucher Schemas ====================

class VoucherBase(BaseModel):
    """Base schema for Voucher - NO validators here per CLAUDE.md Rule 2."""
    voucher_type: str
    voucher_date: date
    narration: str = Field(..., min_length=2, max_length=500)

    # Party
    party_type: Optional[str] = None
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None

    # Document Reference
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None

    # GST
    is_gst_applicable: bool = False
    gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    place_of_supply_code: Optional[str] = None
    is_rcm: bool = False
    is_interstate: bool = False

    # GST Amounts
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    cess_amount: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None

    # Payment
    payment_mode: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    transaction_reference: Optional[str] = None

    # Notes
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class VoucherCreate(VoucherBase):
    """Schema for creating Voucher - validators allowed here."""
    lines: List[VoucherLineCreate] = Field(..., min_length=1)
    allocations: Optional[List[VoucherAllocationCreate]] = None

    @field_validator('voucher_type')
    @classmethod
    def validate_voucher_type(cls, v):
        valid_types = [t.value for t in VoucherType]
        if v not in valid_types:
            raise ValueError(f"Invalid voucher type. Must be one of: {valid_types}")
        return v

    @field_validator('lines')
    @classmethod
    def validate_lines(cls, v):
        if len(v) < 1:
            raise ValueError("Voucher must have at least 1 line")

        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)

        if total_debit != total_credit:
            raise ValueError(
                f"Voucher must balance. Total Debit: {total_debit}, Total Credit: {total_credit}"
            )

        if total_debit == 0:
            raise ValueError("Voucher cannot have zero amount")

        return v

    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, v):
        if v and len(v) != 15:
            raise ValueError("GSTIN must be exactly 15 characters")
        return v

    @field_validator('place_of_supply_code')
    @classmethod
    def validate_pos_code(cls, v):
        if v and len(v) != 2:
            raise ValueError("Place of supply code must be exactly 2 digits")
        return v


class VoucherUpdate(BaseModel):
    """Schema for updating Voucher - only allowed for DRAFT status."""
    voucher_date: Optional[date] = None
    narration: Optional[str] = Field(None, min_length=2, max_length=500)

    # Party
    party_type: Optional[str] = None
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None

    # Document Reference
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None

    # GST
    is_gst_applicable: Optional[bool] = None
    gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    place_of_supply_code: Optional[str] = None
    is_rcm: Optional[bool] = None
    is_interstate: Optional[bool] = None

    # GST Amounts
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    cess_amount: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None

    # Payment
    payment_mode: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    transaction_reference: Optional[str] = None

    # Notes
    notes: Optional[str] = None

    # Lines (optional - if provided, replaces all existing lines)
    lines: Optional[List[VoucherLineCreate]] = None
    allocations: Optional[List[VoucherAllocationCreate]] = None

    @field_validator('lines')
    @classmethod
    def validate_lines(cls, v):
        if v is None:
            return v
        if len(v) < 1:
            raise ValueError("Voucher must have at least 1 line")

        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)

        if total_debit != total_credit:
            raise ValueError(
                f"Voucher must balance. Total Debit: {total_debit}, Total Credit: {total_credit}"
            )
        return v


class VoucherResponse(BaseModel):
    """Response schema for Voucher."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    voucher_number: str
    voucher_type: str
    voucher_date: date
    period_id: Optional[UUID] = None
    narration: str

    # Amounts
    total_debit: Decimal
    total_credit: Decimal

    # Party
    party_type: Optional[str] = None
    party_id: Optional[UUID] = None
    party_name: Optional[str] = None

    # Document Reference
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None

    # GST
    is_gst_applicable: bool = False
    gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    place_of_supply_code: Optional[str] = None
    is_rcm: bool = False
    is_interstate: bool = False

    # GST Amounts
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    cess_amount: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None

    # Payment
    payment_mode: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    transaction_reference: Optional[str] = None

    # Workflow
    status: str
    approval_level: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Reversal
    is_reversed: bool = False
    reversal_voucher_id: Optional[UUID] = None
    original_voucher_id: Optional[UUID] = None

    # GL Link
    journal_entry_id: Optional[UUID] = None

    # Audit
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    posted_by: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    cancelled_by: Optional[UUID] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Notes & Attachments
    notes: Optional[str] = None
    attachments: Optional[dict] = None

    # Nested
    lines: List[VoucherLineResponse] = []
    allocations: List[VoucherAllocationResponse] = []

    # User names (populated by service)
    creator_name: Optional[str] = None
    submitter_name: Optional[str] = None
    approver_name: Optional[str] = None

    @field_serializer('total_debit', 'total_credit', 'taxable_amount', 'cgst_amount',
                      'sgst_amount', 'igst_amount', 'cess_amount', 'tds_amount')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None


class VoucherListResponse(BaseModel):
    """Paginated list response for vouchers."""
    items: List[VoucherResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== Workflow Schemas ====================

class VoucherSubmitRequest(BaseModel):
    """Request to submit voucher for approval."""
    remarks: Optional[str] = Field(None, max_length=500)


class VoucherApproveRequest(BaseModel):
    """Request to approve a voucher."""
    remarks: Optional[str] = Field(None, max_length=500)
    auto_post: bool = Field(default=True, description="Automatically post to GL after approval")


class VoucherRejectRequest(BaseModel):
    """Request to reject a voucher."""
    reason: str = Field(..., min_length=5, max_length=500)


class VoucherCancelRequest(BaseModel):
    """Request to cancel a voucher."""
    reason: str = Field(..., min_length=5, max_length=500)


class VoucherReverseRequest(BaseModel):
    """Request to reverse a posted voucher."""
    reversal_date: date
    reason: str = Field(..., min_length=5, max_length=500)


class VoucherWorkflowResponse(BaseModel):
    """Response for workflow operations."""
    id: UUID
    voucher_number: str
    voucher_type: str
    status: str
    total_amount: float
    narration: str
    message: str
    approval_level: Optional[str] = None


# ==================== Type Metadata Schema ====================

class VoucherTypeMetadata(BaseModel):
    """Metadata about a voucher type."""
    type: str
    name: str
    description: str
    requires_party: bool = False
    party_types: List[str] = []
    requires_bank: bool = False
    requires_gst: bool = False
    supports_allocation: bool = False


class VoucherTypesResponse(BaseModel):
    """Response containing all voucher type metadata."""
    types: List[VoucherTypeMetadata]


# ==================== Party Accounts Schema ====================

class PartyAccountOption(BaseModel):
    """Account option for party dropdown."""
    id: str
    code: str
    name: str
    full_name: str
    type: str
    balance: float = 0.0


class PartyAccountsResponse(BaseModel):
    """Response for party accounts dropdown."""
    cash_accounts: List[PartyAccountOption] = []
    bank_accounts: List[PartyAccountOption] = []
    customer_accounts: List[PartyAccountOption] = []
    vendor_accounts: List[PartyAccountOption] = []
    expense_accounts: List[PartyAccountOption] = []
    income_accounts: List[PartyAccountOption] = []


# ==================== Summary Schemas ====================

class VoucherSummary(BaseModel):
    """Summary statistics for vouchers."""
    total_count: int = 0
    draft_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    posted_count: int = 0
    cancelled_count: int = 0

    total_debit: float = 0.0
    total_credit: float = 0.0

    by_type: dict = {}
