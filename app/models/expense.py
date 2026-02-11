"""
Expense Management Models

Handles:
- Expense Categories (mapped to GL accounts)
- Expense Vouchers with approval workflow
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base


class ExpenseCategory(Base):
    """
    Expense category master - maps to GL expense accounts.
    Examples: Travel, Office Supplies, Utilities, Professional Fees
    """
    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # GL Account mapping
    gl_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    # Controls
    requires_receipt: Mapped[bool] = mapped_column(Boolean, default=True)
    max_amount_without_approval: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Relationships
    vouchers = relationship("ExpenseVoucher", back_populates="category")

    def __repr__(self):
        return f"<ExpenseCategory {self.code}: {self.name}>"


class ExpenseVoucher(Base):
    """
    Expense voucher with approval workflow.

    Status Flow: DRAFT → PENDING_APPROVAL → APPROVED → POSTED → PAID
                                         ↘ REJECTED
    """
    __tablename__ = "expense_vouchers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Voucher identification
    voucher_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False)
    financial_year: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    period: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Expense details
    expense_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expense_categories.id"),
        nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Vendor (optional - for vendor expenses)
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Cost allocation
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Description
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment
    payment_mode: Mapped[str] = mapped_column(String(20), default="CASH")
    bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)

    # Maker
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    submitted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Checker
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Rejection
    rejected_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # GL Posting
    posted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Payment tracking
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Attachments (receipts)
    attachments: Mapped[dict] = mapped_column(JSONB, default=list)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    category = relationship("ExpenseCategory", back_populates="vouchers")

    def __repr__(self):
        return f"<ExpenseVoucher {self.voucher_number}: {self.status}>"
