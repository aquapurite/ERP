"""Add vouchers and voucher_lines tables for unified voucher system.

Implements Tally/SAP-style voucher system with:
- Contra, Payment, Receipt, RCM Payment vouchers
- Links to existing models (JournalEntry, TaxInvoice, etc.)
- Full workflow support (DRAFT -> PENDING -> APPROVED -> POSTED)

Revision ID: 20260122_vouchers
Revises: 2026012201
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260122_vouchers'
down_revision: Union[str, None] = '2026012201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== Vouchers Table ====================
    op.create_table(
        'vouchers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Voucher Identification
        sa.Column('voucher_number', sa.String(30), unique=True, nullable=False, index=True,
                  comment='Auto-generated: VCH-YYYYMMDD-XXXX'),
        sa.Column('voucher_type', sa.String(50), nullable=False, index=True,
                  comment='CONTRA, CREDIT_NOTE, DEBIT_NOTE, GST_SALE, JOURNAL, PAYMENT, PURCHASE, PURCHASE_RCM, RCM_PAYMENT, RECEIPT, SALES'),
        sa.Column('voucher_date', sa.Date, nullable=False, index=True),
        sa.Column('period_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('financial_periods.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('narration', sa.Text, nullable=False),

        # Amounts
        sa.Column('total_debit', sa.Numeric(15, 2), nullable=False, default=0),
        sa.Column('total_credit', sa.Numeric(15, 2), nullable=False, default=0),

        # Party Reference
        sa.Column('party_type', sa.String(50), nullable=True,
                  comment='CUSTOMER, VENDOR, BANK, CASH, EMPLOYEE'),
        sa.Column('party_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('party_name', sa.String(200), nullable=True,
                  comment='Denormalized party name for quick reference'),

        # Document References
        sa.Column('reference_type', sa.String(50), nullable=True,
                  comment='INVOICE, CREDIT_NOTE, DEBIT_NOTE, PURCHASE_ORDER, GRN, etc.'),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_number', sa.String(50), nullable=True),

        # GST Fields
        sa.Column('is_gst_applicable', sa.Boolean, server_default='false', nullable=False),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('place_of_supply', sa.String(100), nullable=True),
        sa.Column('place_of_supply_code', sa.String(2), nullable=True,
                  comment='2-digit state code'),
        sa.Column('is_rcm', sa.Boolean, server_default='false', nullable=False,
                  comment='Reverse Charge Mechanism applicable'),
        sa.Column('is_interstate', sa.Boolean, server_default='false', nullable=False),

        # GST Amounts
        sa.Column('taxable_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('cgst_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('sgst_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('igst_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('cess_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('tds_amount', sa.Numeric(15, 2), nullable=True,
                  comment='TDS deducted if applicable'),

        # Payment Details (for Payment/Receipt/Contra vouchers)
        sa.Column('payment_mode', sa.String(50), nullable=True,
                  comment='CASH, CHEQUE, RTGS, NEFT, UPI, DD'),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('chart_of_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cheque_number', sa.String(20), nullable=True),
        sa.Column('cheque_date', sa.Date, nullable=True),
        sa.Column('transaction_reference', sa.String(100), nullable=True,
                  comment='UTR/Transaction reference'),

        # Workflow & Status
        sa.Column('status', sa.String(50), server_default='DRAFT', nullable=False,
                  comment='DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, POSTED, CANCELLED'),

        # Maker (Creator)
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),

        # Submission
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),

        # Approval
        sa.Column('approval_level', sa.String(20), nullable=True,
                  comment='LEVEL_1, LEVEL_2, LEVEL_3'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),

        # Posting to GL
        sa.Column('posted_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('journal_entries.id', ondelete='SET NULL'), nullable=True,
                  comment='Generated journal entry after posting'),

        # Cancellation
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text, nullable=True),

        # Reversal
        sa.Column('is_reversed', sa.Boolean, server_default='false', nullable=False),
        sa.Column('reversal_voucher_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vouchers.id', ondelete='SET NULL'), nullable=True,
                  comment='Voucher that reversed this one'),
        sa.Column('original_voucher_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vouchers.id', ondelete='SET NULL'), nullable=True,
                  comment='If this is a reversal, points to original'),

        # Additional Metadata
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('attachments', postgresql.JSONB, nullable=True,
                  comment='Array of attachment URLs'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Indexes for vouchers (voucher_number, voucher_type, voucher_date already indexed via index=True)
    op.create_index('ix_vouchers_status', 'vouchers', ['status'])
    op.create_index('ix_vouchers_party', 'vouchers', ['party_type', 'party_id'])
    op.create_index('ix_vouchers_reference', 'vouchers', ['reference_type', 'reference_id'])
    op.create_index('ix_vouchers_period_id', 'vouchers', ['period_id'])
    op.create_index('ix_vouchers_journal_entry_id', 'vouchers', ['journal_entry_id'])

    # ==================== Voucher Lines Table ====================
    op.create_table(
        'voucher_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vouchers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('line_number', sa.Integer, server_default='1', nullable=False),

        # Account
        sa.Column('account_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('chart_of_accounts.id', ondelete='RESTRICT'), nullable=False, index=True),

        # Amounts
        sa.Column('debit_amount', sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column('credit_amount', sa.Numeric(15, 2), server_default='0', nullable=False),

        # Description
        sa.Column('description', sa.Text, nullable=True),

        # Cost Center (optional)
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('cost_centers.id', ondelete='SET NULL'), nullable=True),

        # Tax Details (for GST lines)
        sa.Column('hsn_code', sa.String(10), nullable=True),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_tax_line', sa.Boolean, server_default='false', nullable=False,
                  comment='True if this is a GST tax line'),

        # Reference to invoice line (for Payment against Invoice)
        sa.Column('reference_line_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='Reference to invoice item if allocating against specific item'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Note: voucher_id and account_id indexes already created via index=True in column definitions

    # ==================== Voucher Allocations Table ====================
    # For tracking payment allocations against invoices
    op.create_table(
        'voucher_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vouchers.id', ondelete='CASCADE'), nullable=False, index=True),

        # Source Document (Invoice being paid/adjusted)
        sa.Column('source_type', sa.String(50), nullable=False,
                  comment='TAX_INVOICE, VENDOR_INVOICE, CREDIT_NOTE, DEBIT_NOTE'),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_number', sa.String(50), nullable=True),

        # Allocation Amount
        sa.Column('allocated_amount', sa.Numeric(15, 2), nullable=False),

        # TDS (if applicable)
        sa.Column('tds_amount', sa.Numeric(15, 2), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )

    # Indexes for voucher_allocations (voucher_id index already created via index=True)
    op.create_index('ix_voucher_allocations_source', 'voucher_allocations', ['source_type', 'source_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('voucher_allocations')
    op.drop_table('voucher_lines')
    op.drop_table('vouchers')
