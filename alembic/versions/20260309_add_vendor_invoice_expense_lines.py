"""Add vendor_invoice_expense_lines table for multi-GL expense coding

Revision ID: vi_expense_lines_001
Revises:
Create Date: 2026-03-09

Table created:
- vendor_invoice_expense_lines: Multiple GL account lines per vendor invoice
"""

revision = 'vi_expense_lines_001'
down_revision = None  # Will be set by Alembic

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    op.create_table(
        'vendor_invoice_expense_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('vendor_invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vendor_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('gl_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chart_of_accounts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('expense_category', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('vendor_invoice_expense_lines')
