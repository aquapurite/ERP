"""
Expense Management Schemas
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.schemas.base import BaseResponseSchema


# ==================== EXPENSE CATEGORY ====================

class ExpenseCategoryBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    requires_receipt: bool = True
    max_amount_without_approval: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True


class ExpenseCategoryCreate(ExpenseCategoryBase):
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        return v.upper().strip()


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    requires_receipt: Optional[bool] = None
    max_amount_without_approval: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ExpenseCategoryResponse(BaseResponseSchema):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    requires_receipt: bool
    max_amount_without_approval: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ==================== EXPENSE VOUCHER ====================

class ExpenseVoucherBase(BaseModel):
    voucher_date: date
    expense_category_id: Optional[UUID] = None
    amount: Decimal = Field(..., gt=0)
    gst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tds_amount: Decimal = Field(default=Decimal("0"), ge=0)
    vendor_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    narration: Optional[str] = None
    purpose: Optional[str] = None
    payment_mode: str = Field(default="CASH", pattern="^(CASH|BANK|PETTY_CASH)$")
    bank_account_id: Optional[UUID] = None


class ExpenseVoucherCreate(ExpenseVoucherBase):
    @field_validator("payment_mode")
    @classmethod
    def validate_payment_mode(cls, v):
        return v.upper()


class ExpenseVoucherUpdate(BaseModel):
    voucher_date: Optional[date] = None
    expense_category_id: Optional[UUID] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    gst_amount: Optional[Decimal] = Field(None, ge=0)
    tds_amount: Optional[Decimal] = Field(None, ge=0)
    vendor_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    narration: Optional[str] = None
    purpose: Optional[str] = None
    payment_mode: Optional[str] = None
    bank_account_id: Optional[UUID] = None


class ExpenseVoucherResponse(BaseResponseSchema):
    id: UUID
    voucher_number: str
    voucher_date: date
    financial_year: Optional[str] = None
    period: Optional[str] = None
    expense_category_id: Optional[UUID] = None
    category: Optional[ExpenseCategoryResponse] = None
    amount: Decimal
    gst_amount: Decimal
    tds_amount: Decimal
    net_amount: Decimal
    vendor_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    narration: Optional[str] = None
    purpose: Optional[str] = None
    payment_mode: str
    bank_account_id: Optional[UUID] = None
    status: str
    created_by: Optional[UUID] = None
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approval_level: Optional[str] = None
    rejected_by: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    posted_by: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    journal_entry_id: Optional[UUID] = None
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    attachments: List[dict] = []
    created_at: datetime
    updated_at: datetime


class ExpenseVoucherListResponse(BaseModel):
    items: List[ExpenseVoucherResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== WORKFLOW ACTIONS ====================

class SubmitRequest(BaseModel):
    """Submit voucher for approval"""
    pass


class ApproveRequest(BaseModel):
    """Approve voucher"""
    remarks: Optional[str] = None


class RejectRequest(BaseModel):
    """Reject voucher"""
    reason: str = Field(..., min_length=5)


class PostRequest(BaseModel):
    """Post to GL"""
    pass


class PaymentRequest(BaseModel):
    """Mark as paid"""
    payment_reference: Optional[str] = None
    paid_at: Optional[datetime] = None


# ==================== DASHBOARD ====================

class ExpenseDashboard(BaseModel):
    total_expenses_this_month: Decimal
    total_expenses_this_year: Decimal
    pending_approval_count: int
    pending_approval_amount: Decimal
    category_wise_summary: List[dict]
    recent_vouchers: List[ExpenseVoucherResponse]


