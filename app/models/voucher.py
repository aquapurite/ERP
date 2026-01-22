"""Voucher models for unified accounting voucher system.

Implements Tally/SAP-style voucher patterns with:
- Contra: Cash <-> Bank transfers
- Payment: Outward payments to vendors
- Receipt: Inward receipts from customers
- RCM Payment: Reverse Charge Mechanism tax payment
- Journal: General double-entry vouchers (links to existing JournalEntry)
- GST Sale/Purchase: Links to existing TaxInvoice/VendorInvoice

Each voucher type follows a consistent workflow:
DRAFT -> PENDING_APPROVAL -> APPROVED -> POSTED (to GL)
"""
import uuid
from datetime import datetime, date, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from decimal import Decimal

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.accounting import ChartOfAccount, JournalEntry, FinancialPeriod, CostCenter


class VoucherType(str, Enum):
    """Voucher type classification following Tally/SAP patterns."""
    CONTRA = "CONTRA"              # Cash <-> Bank transfers
    CREDIT_NOTE = "CREDIT_NOTE"    # Against sales invoices
    DEBIT_NOTE = "DEBIT_NOTE"      # Against purchase invoices
    GST_SALE = "GST_SALE"          # B2B/B2C sales with GST
    JOURNAL = "JOURNAL"            # General double-entry
    PAYMENT = "PAYMENT"            # Outward payments to vendors
    PURCHASE = "PURCHASE"          # Purchase invoice
    PURCHASE_RCM = "PURCHASE_RCM"  # Purchase under reverse charge
    RCM_PAYMENT = "RCM_PAYMENT"    # RCM tax payment to government
    RECEIPT = "RECEIPT"            # Inward receipts from customers
    SALES = "SALES"                # Sales invoice


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
    GOVERNMENT = "GOVERNMENT"  # For RCM payments


class PaymentMode(str, Enum):
    """Payment mode for Payment/Receipt/Contra vouchers."""
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    RTGS = "RTGS"
    NEFT = "NEFT"
    UPI = "UPI"
    DD = "DD"  # Demand Draft
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"


class AllocationSourceType(str, Enum):
    """Source document types for voucher allocations."""
    TAX_INVOICE = "TAX_INVOICE"
    VENDOR_INVOICE = "VENDOR_INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    DEBIT_NOTE = "DEBIT_NOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class Voucher(Base):
    """
    Unified voucher model for all accounting transactions.

    This is the entry point for all voucher types in the Finance module,
    following Tally/SAP accounting voucher patterns.
    """
    __tablename__ = "vouchers"

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
        comment="Auto-generated: VCH-YYYYMMDD-XXXX"
    )
    voucher_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="CONTRA, CREDIT_NOTE, DEBIT_NOTE, GST_SALE, JOURNAL, PAYMENT, PURCHASE, PURCHASE_RCM, RCM_PAYMENT, RECEIPT, SALES"
    )
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_periods.id", ondelete="RESTRICT"),
        nullable=True
    )
    narration: Mapped[str] = mapped_column(Text, nullable=False)

    # Amounts
    total_debit: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )
    total_credit: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )

    # Party Reference
    party_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CUSTOMER, VENDOR, BANK, CASH, EMPLOYEE, GOVERNMENT"
    )
    party_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    party_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Denormalized party name for quick reference"
    )

    # Document References
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="INVOICE, CREDIT_NOTE, DEBIT_NOTE, PURCHASE_ORDER, GRN, etc."
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # GST Fields
    is_gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    place_of_supply: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    place_of_supply_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        comment="2-digit state code"
    )
    is_rcm: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Reverse Charge Mechanism applicable"
    )
    is_interstate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # GST Amounts
    taxable_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    cgst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    sgst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    igst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    cess_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    tds_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="TDS deducted if applicable"
    )

    # Payment Details (for Payment/Receipt/Contra vouchers)
    payment_mode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CASH, CHEQUE, RTGS, NEFT, UPI, DD"
    )
    bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="SET NULL"),
        nullable=True
    )
    cheque_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cheque_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="UTR/Transaction reference"
    )

    # Workflow & Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="DRAFT",
        nullable=False,
        comment="DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, POSTED, CANCELLED"
    )

    # Maker (Creator)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Submission
    submitted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Approval
    approval_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="LEVEL_1, LEVEL_2, LEVEL_3"
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
        comment="Generated journal entry after posting"
    )

    # Cancellation
    cancelled_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reversal
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reversal_voucher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vouchers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Voucher that reversed this one"
    )
    original_voucher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vouchers.id", ondelete="SET NULL"),
        nullable=True,
        comment="If this is a reversal, points to original"
    )

    # Additional Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of attachment URLs"
    )

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
    period: Mapped[Optional["FinancialPeriod"]] = relationship(
        "FinancialPeriod",
        foreign_keys=[period_id]
    )
    bank_account: Mapped[Optional["ChartOfAccount"]] = relationship(
        "ChartOfAccount",
        foreign_keys=[bank_account_id]
    )
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship(
        "JournalEntry",
        foreign_keys=[journal_entry_id]
    )
    lines: Mapped[List["VoucherLine"]] = relationship(
        "VoucherLine",
        back_populates="voucher",
        cascade="all, delete-orphan"
    )
    allocations: Mapped[List["VoucherAllocation"]] = relationship(
        "VoucherAllocation",
        back_populates="voucher",
        cascade="all, delete-orphan"
    )

    # User relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    submitter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[submitted_by])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
    poster: Mapped[Optional["User"]] = relationship("User", foreign_keys=[posted_by])

    @property
    def is_balanced(self) -> bool:
        """Check if voucher is balanced (debits = credits)."""
        return self.total_debit == self.total_credit

    @property
    def total_amount(self) -> Decimal:
        """Get total amount (max of debit/credit for balanced vouchers)."""
        return max(self.total_debit, self.total_credit)

    @property
    def tax_total(self) -> Decimal:
        """Get total tax amount."""
        return (
            (self.cgst_amount or Decimal("0")) +
            (self.sgst_amount or Decimal("0")) +
            (self.igst_amount or Decimal("0")) +
            (self.cess_amount or Decimal("0"))
        )

    def __repr__(self) -> str:
        return f"<Voucher(number='{self.voucher_number}', type='{self.voucher_type}', status='{self.status}')>"


class VoucherLine(Base):
    """
    Voucher line item for double-entry bookkeeping.

    Each line has either a debit or credit amount (one must be zero).
    """
    __tablename__ = "voucher_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    voucher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vouchers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    line_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Account
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Amounts
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        nullable=False
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost Center (optional)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Tax Details (for GST lines)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_tax_line: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if this is a GST tax line"
    )

    # Reference to invoice line (for Payment against Invoice)
    reference_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Reference to invoice item if allocating against specific item"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    voucher: Mapped["Voucher"] = relationship("Voucher", back_populates="lines")
    account: Mapped["ChartOfAccount"] = relationship("ChartOfAccount")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")

    @property
    def amount(self) -> Decimal:
        """Get the non-zero amount."""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit entry."""
        return self.debit_amount > 0

    def __repr__(self) -> str:
        return f"<VoucherLine(account={self.account_id}, dr={self.debit_amount}, cr={self.credit_amount})>"


class VoucherAllocation(Base):
    """
    Tracks payment allocations against invoices.

    When a Payment/Receipt voucher is created, it can be allocated
    against one or more invoices. This table tracks those allocations.
    """
    __tablename__ = "voucher_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    voucher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vouchers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Source Document (Invoice being paid/adjusted)
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="TAX_INVOICE, VENDOR_INVOICE, CREDIT_NOTE, DEBIT_NOTE"
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    source_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Allocation Amount
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )

    # TDS (if applicable)
    tds_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    voucher: Mapped["Voucher"] = relationship("Voucher", back_populates="allocations")

    def __repr__(self) -> str:
        return f"<VoucherAllocation(voucher={self.voucher_id}, source={self.source_type}, amount={self.allocated_amount})>"
