"""Expense Voucher module models.

Supports:
- Expense categories with GL account mapping
- Expense vouchers with approval workflow
- Multiple payment modes (Cash, Bank, Petty Cash)
- GST and TDS handling
- Receipt/document attachments
"""
import uuid
from datetime import datetime, date, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from decimal import Decimal

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Numeric, Date
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.accounting import ChartOfAccount, CostCenter


# ==================== Enums ====================

class ExpenseVoucherStatus(str, Enum):
    """Expense voucher lifecycle status."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentMode(str, Enum):
    """Payment mode for expense settlement."""
    CASH = "CASH"
    BANK = "BANK"
    PETTY_CASH = "PETTY_CASH"
    CREDIT_CARD = "CREDIT_CARD"


# ==================== Expense Category ====================

class ExpenseCategory(Base):
    """
    Categories for expenses with GL account mapping.
    Examples: Travel, Office Supplies, Utilities, Professional Fees
    """
    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Category Details
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # GL Account Mapping
    gl_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="SET NULL"),
        nullable=True,
        comment="Expense GL Account to debit"
    )

    # Approval Settings
    requires_receipt: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether receipt/invoice is mandatory"
    )
    max_amount_without_approval: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        comment="Max amount that can be auto-approved"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    gl_account: Mapped[Optional["ChartOfAccount"]] = relationship(
        "ChartOfAccount",
        foreign_keys=[gl_account_id]
    )
    vouchers: Mapped[List["ExpenseVoucher"]] = relationship(
        "ExpenseVoucher",
        back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<ExpenseCategory(code='{self.code}', name='{self.name}')>"


# ==================== Expense Voucher ====================

class ExpenseVoucher(Base):
    """
    Expense voucher with full approval workflow.
    Supports maker-checker and multi-level approval.
    """
    __tablename__ = "expense_vouchers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Voucher Identification
    voucher_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="EXP-YYYYMM-XXXX"
    )
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="e.g., 2025-26"
    )
    period: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="e.g., APR-2025"
    )

    # Expense Category
    expense_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expense_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Amount Details
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        comment="Base expense amount"
    )
    gst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        comment="GST input credit (if applicable)"
    )
    tds_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        comment="TDS to be deducted"
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        comment="Amount + GST - TDS"
    )

    # Vendor (optional - for vendor expenses)
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Vendor if applicable"
    )
    vendor_invoice_no: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Vendor invoice/bill number"
    )
    vendor_invoice_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    # Cost Center
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Description
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Business purpose/justification"
    )

    # Payment Details
    payment_mode: Mapped[str] = mapped_column(
        String(50),
        default="BANK",
        nullable=False,
        comment="CASH, BANK, PETTY_CASH, CREDIT_CARD"
    )
    bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Bank account if payment mode is BANK"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="DRAFT",
        nullable=False,
        index=True,
        comment="DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, POSTED, PAID, CANCELLED"
    )

    # Maker-Checker Workflow
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Maker - who created the voucher"
    )
    submitted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Who submitted for approval"
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Approval level based on amount
    approval_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="LEVEL_1, LEVEL_2, LEVEL_3 based on amount"
    )

    # Checker approval/rejection
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Checker - who approved"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    rejected_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Posting to GL
    posted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Related journal entry after posting"
    )

    # Payment
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Cheque no, UTR, transaction ref"
    )
    paid_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Attachments (receipts, invoices)
    attachments: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Array of attachment URLs"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    category: Mapped["ExpenseCategory"] = relationship(
        "ExpenseCategory",
        back_populates="vouchers"
    )
    cost_center: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter",
        foreign_keys=[cost_center_id]
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by]
    )
    submitter: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[submitted_by]
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by]
    )
    poster: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[posted_by]
    )

    __table_args__ = (
        Index('idx_expense_voucher_status', 'status'),
        Index('idx_expense_voucher_date', 'voucher_date'),
        Index('idx_expense_voucher_category', 'expense_category_id'),
        Index('idx_expense_voucher_cost_center', 'cost_center_id'),
        Index('idx_expense_voucher_fy', 'financial_year'),
    )

    def __repr__(self) -> str:
        return f"<ExpenseVoucher(number='{self.voucher_number}', status='{self.status}')>"
