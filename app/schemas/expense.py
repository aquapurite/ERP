"""Pydantic schemas for Expense Voucher module."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseResponseSchema
from app.models.expense import ExpenseVoucherStatus, PaymentMode


# ==================== Expense Category Schemas ====================

class ExpenseCategoryBase(BaseModel):
    """Base schema for Expense Category."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    requires_receipt: bool = True
    max_amount_without_approval: Decimal = Field(Decimal("0"), ge=0)


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating Expense Category."""
    pass


class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating Expense Category."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    requires_receipt: Optional[bool] = None
    max_amount_without_approval: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ExpenseCategoryResponse(BaseResponseSchema):
    """Response schema for Expense Category."""
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    gl_account_name: Optional[str] = None
    gl_account_code: Optional[str] = None
    requires_receipt: bool
    max_amount_without_approval: Decimal
    is_active: bool
    voucher_count: int = 0
    created_at: datetime
    updated_at: datetime


class ExpenseCategoryListResponse(BaseModel):
    """Response for listing Expense Categories."""
    items: List[ExpenseCategoryResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== Expense Voucher Schemas ====================

class ExpenseVoucherBase(BaseModel):
    """Base schema for Expense Voucher."""
    voucher_date: date
    expense_category_id: UUID
    amount: Decimal = Field(..., ge=0)
    gst_amount: Decimal = Field(Decimal("0"), ge=0)
    tds_amount: Decimal = Field(Decimal("0"), ge=0)
    vendor_id: Optional[UUID] = None
    vendor_invoice_no: Optional[str] = Field(None, max_length=50)
    vendor_invoice_date: Optional[date] = None
    cost_center_id: Optional[UUID] = None
    narration: str
    purpose: Optional[str] = None
    payment_mode: PaymentMode = PaymentMode.BANK
    bank_account_id: Optional[UUID] = None
    notes: Optional[str] = None


class ExpenseVoucherCreate(ExpenseVoucherBase):
    """Schema for creating Expense Voucher."""

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class ExpenseVoucherUpdate(BaseModel):
    """Schema for updating Expense Voucher (only DRAFT status)."""
    voucher_date: Optional[date] = None
    expense_category_id: Optional[UUID] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    gst_amount: Optional[Decimal] = Field(None, ge=0)
    tds_amount: Optional[Decimal] = Field(None, ge=0)
    vendor_id: Optional[UUID] = None
    vendor_invoice_no: Optional[str] = Field(None, max_length=50)
    vendor_invoice_date: Optional[date] = None
    cost_center_id: Optional[UUID] = None
    narration: Optional[str] = None
    purpose: Optional[str] = None
    payment_mode: Optional[PaymentMode] = None
    bank_account_id: Optional[UUID] = None
    notes: Optional[str] = None


class ExpenseVoucherResponse(BaseResponseSchema):
    """Response schema for Expense Voucher (list view)."""
    id: UUID
    voucher_number: str
    voucher_date: date
    financial_year: str
    period: Optional[str] = None

    expense_category_id: UUID
    category_code: Optional[str] = None
    category_name: Optional[str] = None

    amount: Decimal
    gst_amount: Decimal
    tds_amount: Decimal
    net_amount: Decimal

    vendor_name: Optional[str] = None
    cost_center_name: Optional[str] = None

    narration: str
    payment_mode: str
    status: str

    created_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class ExpenseVoucherDetailResponse(ExpenseVoucherResponse):
    """Detailed response schema for Expense Voucher."""
    purpose: Optional[str] = None
    vendor_id: Optional[UUID] = None
    vendor_invoice_no: Optional[str] = None
    vendor_invoice_date: Optional[date] = None
    cost_center_id: Optional[UUID] = None
    bank_account_id: Optional[UUID] = None
    bank_account_name: Optional[str] = None

    approval_level: Optional[str] = None
    rejection_reason: Optional[str] = None
    rejected_by_name: Optional[str] = None
    rejected_at: Optional[datetime] = None

    posted_by_name: Optional[str] = None
    posted_at: Optional[datetime] = None
    journal_entry_id: Optional[UUID] = None
    journal_entry_number: Optional[str] = None

    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    paid_by_name: Optional[str] = None

    attachments: Optional[dict] = None
    notes: Optional[str] = None

    submitted_at: Optional[datetime] = None
    submitted_by_name: Optional[str] = None


class ExpenseVoucherListResponse(BaseModel):
    """Response for listing Expense Vouchers."""
    items: List[ExpenseVoucherResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== Workflow Schemas ====================

class ExpenseSubmitRequest(BaseModel):
    """Request to submit expense for approval."""
    pass  # No additional data needed


class ExpenseApprovalRequest(BaseModel):
    """Request to approve expense."""
    pass  # No additional data needed


class ExpenseRejectionRequest(BaseModel):
    """Request to reject expense."""
    reason: str = Field(..., min_length=10, max_length=500)


class ExpensePostRequest(BaseModel):
    """Request to post expense to GL."""
    pass  # No additional data needed


class ExpensePaymentRequest(BaseModel):
    """Request to mark expense as paid."""
    payment_reference: str = Field(..., max_length=100)
    payment_mode: Optional[PaymentMode] = None
    bank_account_id: Optional[UUID] = None


class ExpenseAttachmentRequest(BaseModel):
    """Request to add attachment to expense."""
    file_url: str
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None


# ==================== Dashboard Schemas ====================

class ExpenseDashboard(BaseModel):
    """Expense Dashboard statistics."""
    total_vouchers: int
    draft_count: int
    pending_approval_count: int
    approved_count: int
    posted_count: int
    paid_count: int
    rejected_count: int

    total_amount_this_month: Decimal
    total_amount_this_year: Decimal
    pending_approval_amount: Decimal

    category_wise_spending: List[dict]
    cost_center_wise_spending: List[dict]
    monthly_trend: List[dict]


class ExpenseCategoryDropdown(BaseModel):
    """Dropdown item for expense category."""
    id: UUID
    code: str
    name: str
    gl_account_id: Optional[UUID] = None
    requires_receipt: bool
