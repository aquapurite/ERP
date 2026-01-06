"""Accounting and Finance models for double-entry bookkeeping.

Implements: Chart of Accounts, General Ledger, Journal Entries,
Financial Periods, Cost Centers, and GST compliance.
"""
import uuid
from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from decimal import Decimal

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Numeric, Date, JSON
from sqlalchemy import Enum as SQLEnum, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AccountType(str, Enum):
    """Account type classification."""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountSubType(str, Enum):
    """Account sub-type for detailed classification."""
    # Assets
    CURRENT_ASSET = "CURRENT_ASSET"
    FIXED_ASSET = "FIXED_ASSET"
    BANK = "BANK"
    CASH = "CASH"
    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    INVENTORY = "INVENTORY"
    PREPAID_EXPENSE = "PREPAID_EXPENSE"
    # Liabilities
    CURRENT_LIABILITY = "CURRENT_LIABILITY"
    LONG_TERM_LIABILITY = "LONG_TERM_LIABILITY"
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"
    TAX_PAYABLE = "TAX_PAYABLE"
    # Equity
    SHARE_CAPITAL = "SHARE_CAPITAL"
    RETAINED_EARNINGS = "RETAINED_EARNINGS"
    # Revenue
    SALES_REVENUE = "SALES_REVENUE"
    SERVICE_REVENUE = "SERVICE_REVENUE"
    OTHER_INCOME = "OTHER_INCOME"
    # Expense
    COST_OF_GOODS = "COST_OF_GOODS"
    OPERATING_EXPENSE = "OPERATING_EXPENSE"
    ADMINISTRATIVE_EXPENSE = "ADMINISTRATIVE_EXPENSE"
    SELLING_EXPENSE = "SELLING_EXPENSE"
    TAX_EXPENSE = "TAX_EXPENSE"


class FinancialPeriodStatus(str, Enum):
    """Financial period status."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    LOCKED = "LOCKED"


class JournalEntryStatus(str, Enum):
    """Journal entry status."""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class ChartOfAccount(Base):
    """
    Chart of Accounts (COA) master.
    Hierarchical account structure for double-entry bookkeeping.
    """
    __tablename__ = "chart_of_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Account Identification
    account_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Account code e.g., 1000, 2000, 3000"
    )
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType),
        nullable=False,
        index=True
    )
    account_sub_type: Mapped[Optional[AccountSubType]] = mapped_column(
        SQLEnum(AccountSubType),
        nullable=True
    )

    # Hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    is_group: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="True if this is a group account (not transactable)"
    )

    # Balance
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        comment="Opening balance for the current period"
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0"),
        comment="Current balance (auto-calculated)"
    )

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="System account - cannot be deleted"
    )
    allow_direct_posting: Mapped[bool] = mapped_column(Boolean, default=True)

    # Linked entities (optional)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # GST mapping (for tax accounts)
    gst_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="CGST, SGST, IGST, CESS"
    )

    # Display
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    parent: Mapped[Optional["ChartOfAccount"]] = relationship(
        "ChartOfAccount",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["ChartOfAccount"]] = relationship(
        "ChartOfAccount",
        back_populates="parent"
    )
    ledger_entries: Mapped[List["GeneralLedger"]] = relationship(
        "GeneralLedger",
        back_populates="account"
    )

    @property
    def is_debit_account(self) -> bool:
        """Assets and Expenses have debit normal balance."""
        return self.account_type in [AccountType.ASSET, AccountType.EXPENSE]

    @property
    def is_credit_account(self) -> bool:
        """Liabilities, Equity, Revenue have credit normal balance."""
        return self.account_type in [AccountType.LIABILITY, AccountType.EQUITY, AccountType.REVENUE]

    def __repr__(self) -> str:
        return f"<ChartOfAccount(code='{self.account_code}', name='{self.account_name}')>"


class FinancialPeriod(Base):
    """
    Financial period/year management.
    Controls which periods are open for posting.
    """
    __tablename__ = "financial_periods"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Period Identification
    period_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="e.g., FY2024-25, Q1-2024"
    )
    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="YEAR, QUARTER, MONTH"
    )

    # Date Range
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Status
    status: Mapped[FinancialPeriodStatus] = mapped_column(
        SQLEnum(FinancialPeriodStatus),
        default=FinancialPeriodStatus.OPEN,
        nullable=False
    )

    # Flags
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_adjustment_period: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Year-end adjustment period"
    )

    # Closing
    closed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<FinancialPeriod(name='{self.period_name}', status='{self.status}')>"


class CostCenter(Base):
    """
    Cost center for departmental accounting.
    Tracks expenses by department/location.
    """
    __tablename__ = "cost_centers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Identification
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="RESTRICT"),
        nullable=True
    )

    # Type
    cost_center_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="DEPARTMENT, LOCATION, PROJECT, etc."
    )

    # Budget
    annual_budget: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0")
    )
    current_spend: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0")
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Manager
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    parent: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter",
        remote_side=[id]
    )

    def __repr__(self) -> str:
        return f"<CostCenter(code='{self.code}', name='{self.name}')>"


class JournalEntry(Base):
    """
    Journal entry header for double-entry bookkeeping.
    Each entry must balance (total debits = total credits).
    """
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Entry Identification
    entry_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Auto-generated: JE-YYYYMMDD-XXXX"
    )

    # Entry Details
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_periods.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Type and Source
    entry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="MANUAL, SALES, PURCHASE, RECEIPT, PAYMENT, ADJUSTMENT, CLOSING"
    )
    source_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="order, invoice, payment, etc."
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Reference to source document"
    )
    source_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Description
    narration: Mapped[str] = mapped_column(Text, nullable=False)

    # Totals
    total_debit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Status
    status: Mapped[JournalEntryStatus] = mapped_column(
        SQLEnum(JournalEntryStatus),
        default=JournalEntryStatus.DRAFT,
        nullable=False
    )

    # Reversal
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversal_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
        comment="If this is a reversal entry"
    )
    reversed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
        comment="Entry that reversed this"
    )

    # Approval
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    posted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    period: Mapped["FinancialPeriod"] = relationship("FinancialPeriod")
    lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    @property
    def is_balanced(self) -> bool:
        """Check if entry is balanced."""
        return self.total_debit == self.total_credit

    def __repr__(self) -> str:
        return f"<JournalEntry(number='{self.entry_number}', status='{self.status}')>"


class JournalEntryLine(Base):
    """
    Journal entry line item.
    Individual debit/credit entries.
    """
    __tablename__ = "journal_entry_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Account
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Amount (one must be zero)
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

    # Cost Center (optional)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Line number for ordering
    line_number: Mapped[int] = mapped_column(Integer, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship(
        "JournalEntry",
        back_populates="lines"
    )
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
        return f"<JournalEntryLine(account={self.account_id}, dr={self.debit_amount}, cr={self.credit_amount})>"


class GeneralLedger(Base):
    """
    General Ledger - Running balance for each account.
    Auto-populated when journal entries are posted.
    """
    __tablename__ = "general_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Account
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Period
    period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_periods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Transaction Date
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Source
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False
    )
    journal_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entry_lines.id", ondelete="CASCADE"),
        nullable=False
    )

    # Amounts
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # Running Balance
    running_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Balance after this transaction"
    )

    # Reference
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost Center
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    account: Mapped["ChartOfAccount"] = relationship(
        "ChartOfAccount",
        back_populates="ledger_entries"
    )
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry")
    period: Mapped["FinancialPeriod"] = relationship("FinancialPeriod")

    def __repr__(self) -> str:
        return f"<GeneralLedger(account={self.account_id}, balance={self.running_balance})>"


class TaxConfiguration(Base):
    """
    Tax rate configuration for GST compliance.
    Maps HSN codes to tax rates.
    """
    __tablename__ = "tax_configurations"
    __table_args__ = (
        UniqueConstraint("hsn_code", "state_code", name="uq_tax_hsn_state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # HSN/SAC Code
    hsn_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="HSN code for goods, SAC for services"
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # State (for state-specific rates)
    state_code: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="State code or NULL for default"
    )

    # Tax Rates
    cgst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    sgst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    igst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    cess_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))

    # Reverse Charge
    is_rcm_applicable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Reverse Charge Mechanism applicable"
    )

    # Exemption
    is_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    exemption_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Validity
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    @property
    def total_gst_rate(self) -> Decimal:
        """Calculate total GST rate."""
        return self.cgst_rate + self.sgst_rate + self.igst_rate + self.cess_rate

    def __repr__(self) -> str:
        return f"<TaxConfiguration(hsn='{self.hsn_code}', rate={self.total_gst_rate}%)>"
