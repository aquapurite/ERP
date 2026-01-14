"""
Auto Journal Entry Generation Service

Automatically generates journal entries for common business transactions:
- Sales invoices -> Sales Revenue, Tax Payable, Accounts Receivable
- Purchase bills -> Inventory/Expense, Tax Receivable, Accounts Payable
- Payment receipts -> Cash/Bank, Accounts Receivable
- Payment made -> Accounts Payable, Cash/Bank
- Bank transactions -> Bank account, Appropriate head

Based on pre-configured accounting rules and templates.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounting import (
    JournalEntry, JournalLine, LedgerAccount,
    JournalType, JournalStatus
)
from app.models.billing import TaxInvoice, InvoiceType


class TransactionType(str, Enum):
    """Transaction types for auto journal generation."""
    SALES_INVOICE = "SALES_INVOICE"
    SALES_RETURN = "SALES_RETURN"
    PURCHASE_BILL = "PURCHASE_BILL"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_MADE = "PAYMENT_MADE"
    BANK_DEPOSIT = "BANK_DEPOSIT"
    BANK_WITHDRAWAL = "BANK_WITHDRAWAL"
    EXPENSE = "EXPENSE"
    STOCK_ADJUSTMENT = "STOCK_ADJUSTMENT"


class AutoJournalError(Exception):
    """Custom exception for auto journal errors."""
    def __init__(self, message: str, details: Dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AutoJournalService:
    """
    Service for automatically generating journal entries.

    Uses pre-configured rules to determine debit/credit accounts
    based on transaction type and context.
    """

    # Default ledger account codes (should be configurable per company)
    DEFAULT_ACCOUNTS = {
        # Revenue accounts
        "SALES_REVENUE": "SALES-001",
        "SERVICE_REVENUE": "SALES-002",

        # Asset accounts
        "ACCOUNTS_RECEIVABLE": "AR-001",
        "CASH": "CASH-001",
        "BANK": "BANK-001",
        "INVENTORY": "INV-001",

        # Liability accounts
        "ACCOUNTS_PAYABLE": "AP-001",
        "GST_OUTPUT": "GST-OUT",
        "GST_INPUT": "GST-IN",
        "CGST_PAYABLE": "CGST-OUT",
        "SGST_PAYABLE": "SGST-OUT",
        "IGST_PAYABLE": "IGST-OUT",
        "CGST_RECEIVABLE": "CGST-IN",
        "SGST_RECEIVABLE": "SGST-IN",
        "IGST_RECEIVABLE": "IGST-IN",
        "TDS_PAYABLE": "TDS-OUT",
        "TDS_RECEIVABLE": "TDS-IN",

        # Expense accounts
        "PURCHASE": "PUR-001",
        "COST_OF_GOODS_SOLD": "COGS-001",
        "DISCOUNT_ALLOWED": "DISC-001",
        "DISCOUNT_RECEIVED": "DISC-002",
        "ROUND_OFF": "ROUND-001",
    }

    def __init__(self, db: AsyncSession, company_id: UUID):
        self.db = db
        self.company_id = company_id

    async def get_account_by_code(self, code: str) -> Optional[LedgerAccount]:
        """Get ledger account by code."""
        result = await self.db.execute(
            select(LedgerAccount).where(
                and_(
                    LedgerAccount.code == code,
                    LedgerAccount.company_id == self.company_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_account(self, code: str, name: str, account_type: str) -> LedgerAccount:
        """Get or create a ledger account."""
        account = await self.get_account_by_code(code)

        if not account:
            account = LedgerAccount(
                company_id=self.company_id,
                code=code,
                name=name,
                account_type=account_type,
                is_active=True
            )
            self.db.add(account)
            await self.db.flush()

        return account

    async def generate_for_sales_invoice(
        self,
        invoice_id: UUID,
        user_id: Optional[UUID] = None
    ) -> JournalEntry:
        """
        Generate journal entry for a sales invoice.

        Debit: Accounts Receivable
        Credit: Sales Revenue, CGST/SGST/IGST Payable
        """
        # Get invoice with items
        result = await self.db.execute(
            select(TaxInvoice)
            .options(selectinload(TaxInvoice.items))
            .where(TaxInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise AutoJournalError("Invoice not found")

        if invoice.invoice_type != InvoiceType.STANDARD:
            raise AutoJournalError("Only standard invoices supported")

        # Check if journal entry already exists
        existing = await self.db.execute(
            select(JournalEntry).where(
                and_(
                    JournalEntry.reference_type == "TaxInvoice",
                    JournalEntry.reference_id == invoice_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise AutoJournalError("Journal entry already exists for this invoice")

        # Get accounts
        ar_account = await self.get_or_create_account(
            self.DEFAULT_ACCOUNTS["ACCOUNTS_RECEIVABLE"],
            "Accounts Receivable",
            "ASSET"
        )
        sales_account = await self.get_or_create_account(
            self.DEFAULT_ACCOUNTS["SALES_REVENUE"],
            "Sales Revenue",
            "REVENUE"
        )

        # Create journal entry
        journal = JournalEntry(
            company_id=self.company_id,
            journal_type=JournalType.SALES,
            entry_number=f"JV-SALE-{invoice.invoice_number}",
            entry_date=invoice.invoice_date,
            reference_type="TaxInvoice",
            reference_id=invoice_id,
            reference_number=invoice.invoice_number,
            narration=f"Sales invoice {invoice.invoice_number} to {invoice.customer_name}",
            status=JournalStatus.DRAFT,
            created_by=user_id,
        )
        self.db.add(journal)
        await self.db.flush()

        journal_lines = []

        # Debit: Accounts Receivable (full amount)
        ar_line = JournalLine(
            journal_entry_id=journal.id,
            account_id=ar_account.id,
            account_name=ar_account.name,
            debit=invoice.grand_total,
            credit=Decimal("0"),
            narration=f"From {invoice.customer_name}"
        )
        journal_lines.append(ar_line)

        # Credit: Sales Revenue (taxable amount)
        sales_line = JournalLine(
            journal_entry_id=journal.id,
            account_id=sales_account.id,
            account_name=sales_account.name,
            debit=Decimal("0"),
            credit=invoice.taxable_amount,
            narration=f"Sales to {invoice.customer_name}"
        )
        journal_lines.append(sales_line)

        # Credit: Tax accounts
        if invoice.cgst_amount and invoice.cgst_amount > 0:
            cgst_account = await self.get_or_create_account(
                self.DEFAULT_ACCOUNTS["CGST_PAYABLE"],
                "CGST Payable",
                "LIABILITY"
            )
            cgst_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=cgst_account.id,
                account_name=cgst_account.name,
                debit=Decimal("0"),
                credit=invoice.cgst_amount,
                narration="CGST on sales"
            )
            journal_lines.append(cgst_line)

        if invoice.sgst_amount and invoice.sgst_amount > 0:
            sgst_account = await self.get_or_create_account(
                self.DEFAULT_ACCOUNTS["SGST_PAYABLE"],
                "SGST Payable",
                "LIABILITY"
            )
            sgst_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=sgst_account.id,
                account_name=sgst_account.name,
                debit=Decimal("0"),
                credit=invoice.sgst_amount,
                narration="SGST on sales"
            )
            journal_lines.append(sgst_line)

        if invoice.igst_amount and invoice.igst_amount > 0:
            igst_account = await self.get_or_create_account(
                self.DEFAULT_ACCOUNTS["IGST_PAYABLE"],
                "IGST Payable",
                "LIABILITY"
            )
            igst_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=igst_account.id,
                account_name=igst_account.name,
                debit=Decimal("0"),
                credit=invoice.igst_amount,
                narration="IGST on sales"
            )
            journal_lines.append(igst_line)

        # Handle round-off
        if invoice.round_off and invoice.round_off != 0:
            roundoff_account = await self.get_or_create_account(
                self.DEFAULT_ACCOUNTS["ROUND_OFF"],
                "Round Off",
                "EXPENSE" if invoice.round_off > 0 else "REVENUE"
            )
            roundoff_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=roundoff_account.id,
                account_name=roundoff_account.name,
                debit=Decimal("0") if invoice.round_off > 0 else abs(invoice.round_off),
                credit=invoice.round_off if invoice.round_off > 0 else Decimal("0"),
                narration="Round off adjustment"
            )
            journal_lines.append(roundoff_line)

        # Add all lines
        for line in journal_lines:
            self.db.add(line)

        # Calculate totals
        total_debit = sum(line.debit for line in journal_lines)
        total_credit = sum(line.credit for line in journal_lines)
        journal.total_debit = total_debit
        journal.total_credit = total_credit

        # Verify balanced
        if abs(total_debit - total_credit) > Decimal("0.01"):
            raise AutoJournalError(
                f"Journal entry not balanced. Debit: {total_debit}, Credit: {total_credit}",
                {"difference": float(total_debit - total_credit)}
            )

        await self.db.commit()
        await self.db.refresh(journal)

        return journal

    async def generate_for_payment_receipt(
        self,
        receipt_id: UUID,
        bank_account_code: str = None,
        user_id: Optional[UUID] = None
    ) -> JournalEntry:
        """
        Generate journal entry for payment receipt.

        Debit: Cash/Bank
        Credit: Accounts Receivable
        """
        from app.models.billing import PaymentReceipt

        result = await self.db.execute(
            select(PaymentReceipt).where(PaymentReceipt.id == receipt_id)
        )
        receipt = result.scalar_one_or_none()

        if not receipt:
            raise AutoJournalError("Payment receipt not found")

        # Check if journal entry already exists
        existing = await self.db.execute(
            select(JournalEntry).where(
                and_(
                    JournalEntry.reference_type == "PaymentReceipt",
                    JournalEntry.reference_id == receipt_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise AutoJournalError("Journal entry already exists for this receipt")

        # Determine cash/bank account
        if receipt.payment_mode in ["CASH", "COD"]:
            debit_account = await self.get_or_create_account(
                self.DEFAULT_ACCOUNTS["CASH"],
                "Cash in Hand",
                "ASSET"
            )
        else:
            bank_code = bank_account_code or self.DEFAULT_ACCOUNTS["BANK"]
            debit_account = await self.get_or_create_account(
                bank_code,
                "Bank Account",
                "ASSET"
            )

        ar_account = await self.get_or_create_account(
            self.DEFAULT_ACCOUNTS["ACCOUNTS_RECEIVABLE"],
            "Accounts Receivable",
            "ASSET"
        )

        # Create journal entry
        journal = JournalEntry(
            company_id=self.company_id,
            journal_type=JournalType.RECEIPT,
            entry_number=f"JV-REC-{receipt.receipt_number}",
            entry_date=receipt.receipt_date,
            reference_type="PaymentReceipt",
            reference_id=receipt_id,
            reference_number=receipt.receipt_number,
            narration=f"Payment received via {receipt.payment_mode}",
            status=JournalStatus.DRAFT,
            created_by=user_id,
        )
        self.db.add(journal)
        await self.db.flush()

        # Debit: Cash/Bank
        debit_line = JournalLine(
            journal_entry_id=journal.id,
            account_id=debit_account.id,
            account_name=debit_account.name,
            debit=receipt.amount,
            credit=Decimal("0"),
            narration=f"Payment from customer"
        )
        self.db.add(debit_line)

        # Credit: Accounts Receivable
        credit_line = JournalLine(
            journal_entry_id=journal.id,
            account_id=ar_account.id,
            account_name=ar_account.name,
            debit=Decimal("0"),
            credit=receipt.amount,
            narration=f"Receipt against invoices"
        )
        self.db.add(credit_line)

        journal.total_debit = receipt.amount
        journal.total_credit = receipt.amount

        await self.db.commit()
        await self.db.refresh(journal)

        return journal

    async def generate_for_bank_transaction(
        self,
        bank_transaction_id: UUID,
        contra_account_code: str,
        user_id: Optional[UUID] = None
    ) -> JournalEntry:
        """
        Generate journal entry for bank transaction.

        For deposits: Debit Bank, Credit Contra Account
        For withdrawals: Debit Contra Account, Credit Bank
        """
        from app.models.banking import BankTransaction, BankAccount, TransactionType

        result = await self.db.execute(
            select(BankTransaction).where(BankTransaction.id == bank_transaction_id)
        )
        txn = result.scalar_one_or_none()

        if not txn:
            raise AutoJournalError("Bank transaction not found")

        # Get bank account
        bank_result = await self.db.execute(
            select(BankAccount).where(BankAccount.id == txn.bank_account_id)
        )
        bank_account = bank_result.scalar_one_or_none()

        if not bank_account:
            raise AutoJournalError("Bank account not found")

        # Check if journal already exists
        existing = await self.db.execute(
            select(JournalEntry).where(
                and_(
                    JournalEntry.reference_type == "BankTransaction",
                    JournalEntry.reference_id == bank_transaction_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise AutoJournalError("Journal entry already exists for this transaction")

        # Get accounts
        bank_ledger = await self.get_or_create_account(
            f"BANK-{bank_account.account_number[-4:]}",
            f"{bank_account.bank_name} - {bank_account.account_number[-4:]}",
            "ASSET"
        )

        contra_ledger = await self.get_account_by_code(contra_account_code)
        if not contra_ledger:
            raise AutoJournalError(f"Contra account not found: {contra_account_code}")

        # Create journal
        journal = JournalEntry(
            company_id=self.company_id,
            journal_type=JournalType.BANK,
            entry_number=f"JV-BANK-{txn.id.hex[:8].upper()}",
            entry_date=txn.transaction_date,
            reference_type="BankTransaction",
            reference_id=bank_transaction_id,
            reference_number=txn.reference_number,
            narration=txn.description[:500] if txn.description else "Bank transaction",
            status=JournalStatus.DRAFT,
            created_by=user_id,
        )
        self.db.add(journal)
        await self.db.flush()

        if txn.transaction_type == TransactionType.CREDIT:
            # Deposit: Debit Bank, Credit Contra
            bank_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=bank_ledger.id,
                account_name=bank_ledger.name,
                debit=txn.amount,
                credit=Decimal("0"),
                narration="Bank deposit"
            )
            contra_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=contra_ledger.id,
                account_name=contra_ledger.name,
                debit=Decimal("0"),
                credit=txn.amount,
                narration=txn.description[:200] if txn.description else ""
            )
        else:
            # Withdrawal: Debit Contra, Credit Bank
            contra_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=contra_ledger.id,
                account_name=contra_ledger.name,
                debit=txn.amount,
                credit=Decimal("0"),
                narration=txn.description[:200] if txn.description else ""
            )
            bank_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=bank_ledger.id,
                account_name=bank_ledger.name,
                debit=Decimal("0"),
                credit=txn.amount,
                narration="Bank withdrawal"
            )

        self.db.add(bank_line)
        self.db.add(contra_line)

        journal.total_debit = txn.amount
        journal.total_credit = txn.amount

        await self.db.commit()
        await self.db.refresh(journal)

        # Mark bank transaction as having journal
        txn.matched_journal_entry_id = journal.id
        await self.db.commit()

        return journal

    async def post_journal_entry(self, journal_id: UUID) -> JournalEntry:
        """Post a draft journal entry."""
        result = await self.db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == journal_id)
        )
        journal = result.scalar_one_or_none()

        if not journal:
            raise AutoJournalError("Journal entry not found")

        if journal.status != JournalStatus.DRAFT:
            raise AutoJournalError(f"Cannot post journal in {journal.status} status")

        # Verify balanced
        total_debit = sum(line.debit or Decimal("0") for line in journal.lines)
        total_credit = sum(line.credit or Decimal("0") for line in journal.lines)

        if abs(total_debit - total_credit) > Decimal("0.01"):
            raise AutoJournalError(
                "Journal entry is not balanced",
                {"debit": float(total_debit), "credit": float(total_credit)}
            )

        journal.status = JournalStatus.POSTED
        journal.posted_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(journal)

        return journal
