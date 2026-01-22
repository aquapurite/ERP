"""
Voucher Service for unified voucher management.

Handles business logic for all voucher types:
- Contra: Cash <-> Bank transfers
- Payment: Outward payments to vendors
- Receipt: Inward receipts from customers
- RCM Payment: Reverse Charge Mechanism tax payments
- Journal/GST Sale/Purchase: Links to existing models
"""
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.voucher import (
    Voucher, VoucherLine, VoucherAllocation,
    VoucherType, VoucherStatus, PartyType, PaymentMode
)
from app.models.accounting import (
    ChartOfAccount, JournalEntry, JournalEntryLine,
    GeneralLedger, FinancialPeriod,
    AccountType, JournalEntryStatus, FinancialPeriodStatus
)
from app.models.user import User
from app.schemas.voucher import (
    VoucherCreate, VoucherUpdate,
    VoucherLineCreate, VoucherAllocationCreate,
    VoucherTypeMetadata
)


class VoucherService:
    """Service for voucher operations following Tally/SAP patterns."""

    # Approval level thresholds (in INR)
    APPROVAL_THRESHOLDS = {
        "LEVEL_1": Decimal("50000"),      # Up to 50,000
        "LEVEL_2": Decimal("500000"),     # Up to 5,00,000
        "LEVEL_3": Decimal("999999999"),  # Above 5,00,000
    }

    # Voucher type metadata
    VOUCHER_TYPE_METADATA = {
        VoucherType.CONTRA.value: VoucherTypeMetadata(
            type=VoucherType.CONTRA.value,
            name="Contra",
            description="Cash to Bank or Bank to Cash transfers",
            requires_party=False,
            party_types=[PartyType.CASH.value, PartyType.BANK.value],
            requires_bank=True,
            requires_gst=False,
            supports_allocation=False
        ),
        VoucherType.PAYMENT.value: VoucherTypeMetadata(
            type=VoucherType.PAYMENT.value,
            name="Payment",
            description="Outward payments to vendors/suppliers",
            requires_party=True,
            party_types=[PartyType.VENDOR.value],
            requires_bank=True,
            requires_gst=True,
            supports_allocation=True
        ),
        VoucherType.RECEIPT.value: VoucherTypeMetadata(
            type=VoucherType.RECEIPT.value,
            name="Receipt",
            description="Inward receipts from customers",
            requires_party=True,
            party_types=[PartyType.CUSTOMER.value],
            requires_bank=True,
            requires_gst=True,
            supports_allocation=True
        ),
        VoucherType.RCM_PAYMENT.value: VoucherTypeMetadata(
            type=VoucherType.RCM_PAYMENT.value,
            name="RCM Payment",
            description="Reverse Charge Mechanism tax payment to government",
            requires_party=True,
            party_types=[PartyType.GOVERNMENT.value],
            requires_bank=True,
            requires_gst=True,
            supports_allocation=False
        ),
        VoucherType.JOURNAL.value: VoucherTypeMetadata(
            type=VoucherType.JOURNAL.value,
            name="Journal",
            description="General double-entry journal voucher",
            requires_party=False,
            party_types=[],
            requires_bank=False,
            requires_gst=False,
            supports_allocation=False
        ),
        VoucherType.GST_SALE.value: VoucherTypeMetadata(
            type=VoucherType.GST_SALE.value,
            name="GST Sale",
            description="B2B/B2C sales with GST",
            requires_party=True,
            party_types=[PartyType.CUSTOMER.value],
            requires_bank=False,
            requires_gst=True,
            supports_allocation=False
        ),
        VoucherType.SALES.value: VoucherTypeMetadata(
            type=VoucherType.SALES.value,
            name="Sales",
            description="Sales invoice voucher",
            requires_party=True,
            party_types=[PartyType.CUSTOMER.value],
            requires_bank=False,
            requires_gst=True,
            supports_allocation=False
        ),
        VoucherType.PURCHASE.value: VoucherTypeMetadata(
            type=VoucherType.PURCHASE.value,
            name="Purchase",
            description="Purchase invoice voucher",
            requires_party=True,
            party_types=[PartyType.VENDOR.value],
            requires_bank=False,
            requires_gst=True,
            supports_allocation=False
        ),
        VoucherType.PURCHASE_RCM.value: VoucherTypeMetadata(
            type=VoucherType.PURCHASE_RCM.value,
            name="Purchase RCM",
            description="Purchase under Reverse Charge Mechanism",
            requires_party=True,
            party_types=[PartyType.VENDOR.value],
            requires_bank=False,
            requires_gst=True,
            supports_allocation=False
        ),
        VoucherType.CREDIT_NOTE.value: VoucherTypeMetadata(
            type=VoucherType.CREDIT_NOTE.value,
            name="Credit Note",
            description="Credit note against sales invoice",
            requires_party=True,
            party_types=[PartyType.CUSTOMER.value],
            requires_bank=False,
            requires_gst=True,
            supports_allocation=True
        ),
        VoucherType.DEBIT_NOTE.value: VoucherTypeMetadata(
            type=VoucherType.DEBIT_NOTE.value,
            name="Debit Note",
            description="Debit note against purchase invoice",
            requires_party=True,
            party_types=[PartyType.VENDOR.value],
            requires_bank=False,
            requires_gst=True,
            supports_allocation=True
        ),
    }

    def __init__(self, db: AsyncSession, user_id: Optional[uuid.UUID] = None):
        self.db = db
        self.user_id = user_id
        self._account_cache: Dict[str, uuid.UUID] = {}

    # ==================== Helper Methods ====================

    async def _get_current_period(self, target_date: date) -> Optional[FinancialPeriod]:
        """Get the open financial period for a given date."""
        result = await self.db.execute(
            select(FinancialPeriod).where(
                and_(
                    FinancialPeriod.start_date <= target_date,
                    FinancialPeriod.end_date >= target_date,
                    FinancialPeriod.status == FinancialPeriodStatus.OPEN
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def _generate_voucher_number(self, voucher_type: str, voucher_date: date) -> str:
        """Generate unique voucher number."""
        # Format: VCH-TYPE-YYYYMMDD-XXXX
        prefix_map = {
            VoucherType.CONTRA.value: "CTR",
            VoucherType.PAYMENT.value: "PAY",
            VoucherType.RECEIPT.value: "RCP",
            VoucherType.RCM_PAYMENT.value: "RCM",
            VoucherType.JOURNAL.value: "JNL",
            VoucherType.GST_SALE.value: "GSL",
            VoucherType.SALES.value: "SAL",
            VoucherType.PURCHASE.value: "PUR",
            VoucherType.PURCHASE_RCM.value: "PRM",
            VoucherType.CREDIT_NOTE.value: "CRN",
            VoucherType.DEBIT_NOTE.value: "DBN",
        }
        prefix = prefix_map.get(voucher_type, "VCH")

        # Count vouchers of this type today
        count_result = await self.db.execute(
            select(func.count(Voucher.id)).where(
                and_(
                    Voucher.voucher_type == voucher_type,
                    func.date(Voucher.created_at) == date.today()
                )
            )
        )
        count = (count_result.scalar() or 0) + 1

        return f"{prefix}-{voucher_date.strftime('%Y%m%d')}-{str(count).zfill(4)}"

    def _get_approval_level(self, amount: Decimal) -> str:
        """Determine approval level based on amount."""
        if amount <= self.APPROVAL_THRESHOLDS["LEVEL_1"]:
            return "LEVEL_1"
        elif amount <= self.APPROVAL_THRESHOLDS["LEVEL_2"]:
            return "LEVEL_2"
        else:
            return "LEVEL_3"

    async def _get_account_by_id(self, account_id: uuid.UUID) -> Optional[ChartOfAccount]:
        """Get account by ID with caching."""
        if str(account_id) in self._account_cache:
            result = await self.db.execute(
                select(ChartOfAccount).where(ChartOfAccount.id == account_id)
            )
            return result.scalar_one_or_none()

        result = await self.db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        if account:
            self._account_cache[str(account_id)] = account
        return account

    def _get_user_name(self, user: Optional[User]) -> Optional[str]:
        """Get formatted user name."""
        if not user:
            return None
        return f"{user.first_name} {user.last_name or ''}".strip()

    # ==================== CRUD Operations ====================

    async def create_voucher(self, voucher_data: VoucherCreate) -> Voucher:
        """Create a new voucher in DRAFT status."""
        # Validate period
        period = await self._get_current_period(voucher_data.voucher_date)
        if not period:
            raise ValueError(f"No open financial period for date {voucher_data.voucher_date}")

        # Calculate totals from lines
        total_debit = sum(line.debit_amount for line in voucher_data.lines)
        total_credit = sum(line.credit_amount for line in voucher_data.lines)

        if total_debit != total_credit:
            raise ValueError(f"Voucher must balance. Debit: {total_debit}, Credit: {total_credit}")

        # Generate voucher number
        voucher_number = await self._generate_voucher_number(
            voucher_data.voucher_type,
            voucher_data.voucher_date
        )

        # Create voucher
        voucher = Voucher(
            id=uuid.uuid4(),
            voucher_number=voucher_number,
            voucher_type=voucher_data.voucher_type,
            voucher_date=voucher_data.voucher_date,
            period_id=period.id,
            narration=voucher_data.narration,
            total_debit=total_debit,
            total_credit=total_credit,
            party_type=voucher_data.party_type,
            party_id=voucher_data.party_id,
            party_name=voucher_data.party_name,
            reference_type=voucher_data.reference_type,
            reference_id=voucher_data.reference_id,
            reference_number=voucher_data.reference_number,
            is_gst_applicable=voucher_data.is_gst_applicable,
            gstin=voucher_data.gstin,
            place_of_supply=voucher_data.place_of_supply,
            place_of_supply_code=voucher_data.place_of_supply_code,
            is_rcm=voucher_data.is_rcm,
            is_interstate=voucher_data.is_interstate,
            taxable_amount=voucher_data.taxable_amount,
            cgst_amount=voucher_data.cgst_amount,
            sgst_amount=voucher_data.sgst_amount,
            igst_amount=voucher_data.igst_amount,
            cess_amount=voucher_data.cess_amount,
            tds_amount=voucher_data.tds_amount,
            payment_mode=voucher_data.payment_mode,
            bank_account_id=voucher_data.bank_account_id,
            cheque_number=voucher_data.cheque_number,
            cheque_date=voucher_data.cheque_date,
            transaction_reference=voucher_data.transaction_reference,
            notes=voucher_data.notes,
            status=VoucherStatus.DRAFT.value,
            created_by=self.user_id,
        )

        self.db.add(voucher)
        await self.db.flush()

        # Create voucher lines
        for idx, line_data in enumerate(voucher_data.lines, 1):
            # Validate account exists and is postable
            account = await self._get_account_by_id(line_data.account_id)
            if not account:
                raise ValueError(f"Account {line_data.account_id} not found")
            if account.is_group:
                raise ValueError(f"Cannot post to group account: {account.account_name}")

            line = VoucherLine(
                id=uuid.uuid4(),
                voucher_id=voucher.id,
                line_number=idx,
                account_id=line_data.account_id,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                description=line_data.description,
                cost_center_id=line_data.cost_center_id,
                hsn_code=line_data.hsn_code,
                tax_rate=line_data.tax_rate,
                is_tax_line=line_data.is_tax_line,
                reference_line_id=line_data.reference_line_id,
            )
            self.db.add(line)

        # Create allocations if provided
        if voucher_data.allocations:
            for alloc_data in voucher_data.allocations:
                allocation = VoucherAllocation(
                    id=uuid.uuid4(),
                    voucher_id=voucher.id,
                    source_type=alloc_data.source_type,
                    source_id=alloc_data.source_id,
                    source_number=alloc_data.source_number,
                    allocated_amount=alloc_data.allocated_amount,
                    tds_amount=alloc_data.tds_amount,
                    created_by=self.user_id,
                )
                self.db.add(allocation)

        await self.db.commit()
        return await self.get_voucher(voucher.id)

    async def get_voucher(self, voucher_id: uuid.UUID) -> Optional[Voucher]:
        """Get voucher by ID with all relationships."""
        result = await self.db.execute(
            select(Voucher)
            .options(
                selectinload(Voucher.lines).selectinload(VoucherLine.account),
                selectinload(Voucher.allocations),
                selectinload(Voucher.creator),
                selectinload(Voucher.submitter),
                selectinload(Voucher.approver),
                selectinload(Voucher.bank_account),
                selectinload(Voucher.period),
            )
            .where(Voucher.id == voucher_id)
        )
        return result.scalar_one_or_none()

    async def list_vouchers(
        self,
        voucher_type: Optional[str] = None,
        status: Optional[str] = None,
        party_type: Optional[str] = None,
        party_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Voucher], int]:
        """List vouchers with filters and pagination."""
        query = select(Voucher).options(
            selectinload(Voucher.lines).selectinload(VoucherLine.account),
            selectinload(Voucher.allocations),
            selectinload(Voucher.creator),
        )
        count_query = select(func.count(Voucher.id))

        filters = []
        if voucher_type:
            filters.append(Voucher.voucher_type == voucher_type)
        if status:
            filters.append(Voucher.status == status)
        if party_type:
            filters.append(Voucher.party_type == party_type)
        if party_id:
            filters.append(Voucher.party_id == party_id)
        if start_date:
            filters.append(Voucher.voucher_date >= start_date)
        if end_date:
            filters.append(Voucher.voucher_date <= end_date)
        if search:
            filters.append(or_(
                Voucher.voucher_number.ilike(f"%{search}%"),
                Voucher.narration.ilike(f"%{search}%"),
                Voucher.party_name.ilike(f"%{search}%"),
            ))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * size
        query = query.order_by(Voucher.voucher_date.desc(), Voucher.created_at.desc())
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        vouchers = result.scalars().all()

        return list(vouchers), total

    async def update_voucher(
        self,
        voucher_id: uuid.UUID,
        update_data: VoucherUpdate
    ) -> Voucher:
        """Update a DRAFT voucher."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot update voucher with status '{voucher.status}'. Only DRAFT vouchers can be updated.")

        # Update basic fields
        update_dict = update_data.model_dump(exclude_unset=True, exclude={'lines', 'allocations'})
        for field, value in update_dict.items():
            setattr(voucher, field, value)

        # Update lines if provided
        if update_data.lines is not None:
            # Delete existing lines
            for line in voucher.lines:
                await self.db.delete(line)

            # Create new lines
            total_debit = Decimal("0")
            total_credit = Decimal("0")

            for idx, line_data in enumerate(update_data.lines, 1):
                account = await self._get_account_by_id(line_data.account_id)
                if not account:
                    raise ValueError(f"Account {line_data.account_id} not found")

                line = VoucherLine(
                    id=uuid.uuid4(),
                    voucher_id=voucher.id,
                    line_number=idx,
                    account_id=line_data.account_id,
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount,
                    description=line_data.description,
                    cost_center_id=line_data.cost_center_id,
                    hsn_code=line_data.hsn_code,
                    tax_rate=line_data.tax_rate,
                    is_tax_line=line_data.is_tax_line,
                )
                self.db.add(line)

                total_debit += line_data.debit_amount
                total_credit += line_data.credit_amount

            voucher.total_debit = total_debit
            voucher.total_credit = total_credit

        # Update allocations if provided
        if update_data.allocations is not None:
            # Delete existing allocations
            for alloc in voucher.allocations:
                await self.db.delete(alloc)

            # Create new allocations
            for alloc_data in update_data.allocations:
                allocation = VoucherAllocation(
                    id=uuid.uuid4(),
                    voucher_id=voucher.id,
                    source_type=alloc_data.source_type,
                    source_id=alloc_data.source_id,
                    source_number=alloc_data.source_number,
                    allocated_amount=alloc_data.allocated_amount,
                    tds_amount=alloc_data.tds_amount,
                    created_by=self.user_id,
                )
                self.db.add(allocation)

        voucher.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return await self.get_voucher(voucher_id)

    async def delete_voucher(self, voucher_id: uuid.UUID) -> bool:
        """Delete a DRAFT voucher."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Cannot delete voucher with status '{voucher.status}'. Only DRAFT vouchers can be deleted.")

        await self.db.delete(voucher)
        await self.db.commit()
        return True

    # ==================== Workflow Operations ====================

    async def submit_voucher(
        self,
        voucher_id: uuid.UUID,
        remarks: Optional[str] = None
    ) -> Voucher:
        """Submit voucher for approval (Maker action)."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status != VoucherStatus.DRAFT.value:
            raise ValueError(f"Only DRAFT vouchers can be submitted. Current status: {voucher.status}")

        # Validate voucher is balanced
        if voucher.total_debit != voucher.total_credit:
            raise ValueError("Voucher must be balanced before submission")

        # Determine approval level
        approval_level = self._get_approval_level(voucher.total_debit)

        voucher.status = VoucherStatus.PENDING_APPROVAL.value
        voucher.submitted_by = self.user_id
        voucher.submitted_at = datetime.now(timezone.utc)
        voucher.approval_level = approval_level
        voucher.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return await self.get_voucher(voucher_id)

    async def approve_voucher(
        self,
        voucher_id: uuid.UUID,
        auto_post: bool = True,
        remarks: Optional[str] = None
    ) -> Voucher:
        """Approve a voucher (Checker action)."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status != VoucherStatus.PENDING_APPROVAL.value:
            raise ValueError(f"Only PENDING_APPROVAL vouchers can be approved. Current status: {voucher.status}")

        # Maker-Checker validation
        if voucher.created_by == self.user_id:
            raise ValueError("Maker-Checker violation: You cannot approve your own voucher")

        voucher.status = VoucherStatus.APPROVED.value
        voucher.approved_by = self.user_id
        voucher.approved_at = datetime.now(timezone.utc)
        voucher.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        # Auto-post if requested
        if auto_post:
            voucher = await self.post_voucher(voucher_id)

        return await self.get_voucher(voucher_id)

    async def reject_voucher(
        self,
        voucher_id: uuid.UUID,
        reason: str
    ) -> Voucher:
        """Reject a voucher (Checker action)."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status != VoucherStatus.PENDING_APPROVAL.value:
            raise ValueError(f"Only PENDING_APPROVAL vouchers can be rejected. Current status: {voucher.status}")

        # Maker-Checker validation
        if voucher.created_by == self.user_id:
            raise ValueError("Maker-Checker violation: You cannot reject your own voucher")

        voucher.status = VoucherStatus.REJECTED.value
        voucher.approved_by = self.user_id  # Record who rejected
        voucher.approved_at = datetime.now(timezone.utc)
        voucher.rejection_reason = reason
        voucher.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return await self.get_voucher(voucher_id)

    async def post_voucher(self, voucher_id: uuid.UUID) -> Voucher:
        """Post voucher to General Ledger."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status not in [VoucherStatus.APPROVED.value]:
            raise ValueError(f"Only APPROVED vouchers can be posted. Current status: {voucher.status}")

        # Create journal entry
        entry_number = f"JV-{voucher.voucher_number}"

        journal_entry = JournalEntry(
            id=uuid.uuid4(),
            entry_number=entry_number,
            entry_type=voucher.voucher_type,
            entry_date=voucher.voucher_date,
            period_id=voucher.period_id,
            narration=voucher.narration,
            source_type="VOUCHER",
            source_id=voucher.id,
            source_number=voucher.voucher_number,
            total_debit=voucher.total_debit,
            total_credit=voucher.total_credit,
            status=JournalEntryStatus.POSTED.value,
            created_by=voucher.created_by,
            approved_by=voucher.approved_by,
            approved_at=voucher.approved_at,
            posted_by=self.user_id,
            posted_at=datetime.now(timezone.utc),
        )

        self.db.add(journal_entry)
        await self.db.flush()

        # Create journal entry lines and GL entries
        for line in voucher.lines:
            # Get account for balance calculation
            account = await self._get_account_by_id(line.account_id)

            # Create journal entry line
            je_line = JournalEntryLine(
                id=uuid.uuid4(),
                journal_entry_id=journal_entry.id,
                line_number=line.line_number,
                account_id=line.account_id,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                description=line.description,
                cost_center_id=line.cost_center_id,
            )
            self.db.add(je_line)

            # Calculate balance change
            if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                balance_change = line.debit_amount - line.credit_amount
            else:
                balance_change = line.credit_amount - line.debit_amount

            new_balance = account.current_balance + balance_change

            # Create GL entry
            gl_entry = GeneralLedger(
                id=uuid.uuid4(),
                account_id=line.account_id,
                period_id=voucher.period_id,
                transaction_date=voucher.voucher_date,
                journal_entry_id=journal_entry.id,
                journal_line_id=je_line.id,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                running_balance=new_balance,
                narration=line.description or voucher.narration,
                cost_center_id=line.cost_center_id,
            )
            self.db.add(gl_entry)

            # Update account balance
            account.current_balance = new_balance

        # Update voucher status
        voucher.status = VoucherStatus.POSTED.value
        voucher.posted_by = self.user_id
        voucher.posted_at = datetime.now(timezone.utc)
        voucher.journal_entry_id = journal_entry.id
        voucher.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return await self.get_voucher(voucher_id)

    async def cancel_voucher(
        self,
        voucher_id: uuid.UUID,
        reason: str
    ) -> Voucher:
        """Cancel a DRAFT or REJECTED voucher."""
        voucher = await self.get_voucher(voucher_id)
        if not voucher:
            raise ValueError("Voucher not found")

        if voucher.status not in [VoucherStatus.DRAFT.value, VoucherStatus.REJECTED.value]:
            raise ValueError(f"Cannot cancel voucher with status '{voucher.status}'. Only DRAFT or REJECTED vouchers can be cancelled.")

        voucher.status = VoucherStatus.CANCELLED.value
        voucher.cancelled_by = self.user_id
        voucher.cancelled_at = datetime.now(timezone.utc)
        voucher.cancellation_reason = reason
        voucher.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return await self.get_voucher(voucher_id)

    async def reverse_voucher(
        self,
        voucher_id: uuid.UUID,
        reversal_date: date,
        reason: str
    ) -> Voucher:
        """Create a reversal voucher for a POSTED voucher."""
        original = await self.get_voucher(voucher_id)
        if not original:
            raise ValueError("Voucher not found")

        if original.status != VoucherStatus.POSTED.value:
            raise ValueError("Only POSTED vouchers can be reversed")

        if original.is_reversed:
            raise ValueError("Voucher has already been reversed")

        # Validate period for reversal date
        period = await self._get_current_period(reversal_date)
        if not period:
            raise ValueError(f"No open financial period for reversal date {reversal_date}")

        # Generate reversal voucher number
        reversal_number = await self._generate_voucher_number(
            original.voucher_type,
            reversal_date
        )
        reversal_number = f"REV-{reversal_number}"

        # Create reversal voucher
        reversal = Voucher(
            id=uuid.uuid4(),
            voucher_number=reversal_number,
            voucher_type=original.voucher_type,
            voucher_date=reversal_date,
            period_id=period.id,
            narration=f"Reversal of {original.voucher_number}: {reason}",
            total_debit=original.total_credit,  # Swap
            total_credit=original.total_debit,
            party_type=original.party_type,
            party_id=original.party_id,
            party_name=original.party_name,
            original_voucher_id=original.id,
            status=VoucherStatus.APPROVED.value,
            created_by=self.user_id,
            approved_by=self.user_id,
            approved_at=datetime.now(timezone.utc),
        )

        self.db.add(reversal)
        await self.db.flush()

        # Create reversed lines (swap debit/credit)
        for line in original.lines:
            reversed_line = VoucherLine(
                id=uuid.uuid4(),
                voucher_id=reversal.id,
                line_number=line.line_number,
                account_id=line.account_id,
                debit_amount=line.credit_amount,  # Swap
                credit_amount=line.debit_amount,
                description=f"Reversal: {line.description or ''}",
                cost_center_id=line.cost_center_id,
            )
            self.db.add(reversed_line)

        # Mark original as reversed
        original.is_reversed = True
        original.reversal_voucher_id = reversal.id
        original.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        # Post the reversal voucher
        return await self.post_voucher(reversal.id)

    # ==================== Utility Methods ====================

    def get_voucher_types_metadata(self) -> List[VoucherTypeMetadata]:
        """Get metadata for all voucher types."""
        return list(self.VOUCHER_TYPE_METADATA.values())

    async def get_party_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get accounts categorized for party selection dropdowns."""
        # Cash accounts
        cash_query = select(ChartOfAccount).where(
            and_(
                ChartOfAccount.is_active == True,
                ChartOfAccount.is_group == False,
                or_(
                    ChartOfAccount.account_code.like("1010%"),
                    ChartOfAccount.gst_type == "CASH"
                )
            )
        ).order_by(ChartOfAccount.account_code)

        # Bank accounts
        bank_query = select(ChartOfAccount).where(
            and_(
                ChartOfAccount.is_active == True,
                ChartOfAccount.is_group == False,
                or_(
                    ChartOfAccount.account_code.like("102%"),
                    ChartOfAccount.bank_name.isnot(None)
                )
            )
        ).order_by(ChartOfAccount.account_code)

        # Customer accounts (AR)
        customer_query = select(ChartOfAccount).where(
            and_(
                ChartOfAccount.is_active == True,
                ChartOfAccount.is_group == False,
                ChartOfAccount.account_code.like("111%")
            )
        ).order_by(ChartOfAccount.account_code)

        # Vendor accounts (AP)
        vendor_query = select(ChartOfAccount).where(
            and_(
                ChartOfAccount.is_active == True,
                ChartOfAccount.is_group == False,
                ChartOfAccount.account_code.like("211%")
            )
        ).order_by(ChartOfAccount.account_code)

        # Expense accounts
        expense_query = select(ChartOfAccount).where(
            and_(
                ChartOfAccount.is_active == True,
                ChartOfAccount.is_group == False,
                ChartOfAccount.account_type == AccountType.EXPENSE
            )
        ).order_by(ChartOfAccount.account_code)

        # Income/Revenue accounts
        income_query = select(ChartOfAccount).where(
            and_(
                ChartOfAccount.is_active == True,
                ChartOfAccount.is_group == False,
                ChartOfAccount.account_type == AccountType.REVENUE
            )
        ).order_by(ChartOfAccount.account_code)

        def format_account(acc: ChartOfAccount) -> Dict[str, Any]:
            return {
                "id": str(acc.id),
                "code": acc.account_code,
                "name": acc.account_name,
                "full_name": f"{acc.account_code} - {acc.account_name}",
                "type": acc.account_type,
                "balance": float(acc.current_balance or 0),
            }

        cash_result = await self.db.execute(cash_query)
        bank_result = await self.db.execute(bank_query)
        customer_result = await self.db.execute(customer_query)
        vendor_result = await self.db.execute(vendor_query)
        expense_result = await self.db.execute(expense_query)
        income_result = await self.db.execute(income_query)

        return {
            "cash_accounts": [format_account(a) for a in cash_result.scalars().all()],
            "bank_accounts": [format_account(a) for a in bank_result.scalars().all()],
            "customer_accounts": [format_account(a) for a in customer_result.scalars().all()],
            "vendor_accounts": [format_account(a) for a in vendor_result.scalars().all()],
            "expense_accounts": [format_account(a) for a in expense_result.scalars().all()],
            "income_accounts": [format_account(a) for a in income_result.scalars().all()],
        }

    async def get_voucher_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        voucher_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary statistics for vouchers."""
        base_filters = []
        if start_date:
            base_filters.append(Voucher.voucher_date >= start_date)
        if end_date:
            base_filters.append(Voucher.voucher_date <= end_date)
        if voucher_type:
            base_filters.append(Voucher.voucher_type == voucher_type)

        # Count by status
        status_query = select(
            Voucher.status,
            func.count(Voucher.id).label("count"),
            func.sum(Voucher.total_debit).label("total_debit"),
            func.sum(Voucher.total_credit).label("total_credit"),
        ).group_by(Voucher.status)

        if base_filters:
            status_query = status_query.where(and_(*base_filters))

        status_result = await self.db.execute(status_query)
        status_rows = status_result.all()

        status_counts = {row.status: row.count for row in status_rows}
        total_debit = sum(float(row.total_debit or 0) for row in status_rows)
        total_credit = sum(float(row.total_credit or 0) for row in status_rows)

        # Count by type
        type_query = select(
            Voucher.voucher_type,
            func.count(Voucher.id).label("count"),
        ).group_by(Voucher.voucher_type)

        if base_filters:
            type_query = type_query.where(and_(*base_filters))

        type_result = await self.db.execute(type_query)
        type_counts = {row.voucher_type: row.count for row in type_result.all()}

        return {
            "total_count": sum(status_counts.values()),
            "draft_count": status_counts.get(VoucherStatus.DRAFT.value, 0),
            "pending_approval_count": status_counts.get(VoucherStatus.PENDING_APPROVAL.value, 0),
            "approved_count": status_counts.get(VoucherStatus.APPROVED.value, 0),
            "posted_count": status_counts.get(VoucherStatus.POSTED.value, 0),
            "cancelled_count": status_counts.get(VoucherStatus.CANCELLED.value, 0),
            "total_debit": total_debit,
            "total_credit": total_credit,
            "by_type": type_counts,
        }


# Helper function
async def get_voucher_service(db: AsyncSession, user_id: uuid.UUID) -> VoucherService:
    """Get voucher service instance."""
    return VoucherService(db, user_id)
