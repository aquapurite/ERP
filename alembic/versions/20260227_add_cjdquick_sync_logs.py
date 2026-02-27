"""Add CJDQuick OMS sync logs table

Revision ID: cjdquick_sync_001
Revises:
Create Date: 2026-02-27

Table created:
- cjdquick_sync_logs: Audit log for all CJDQuick OMS sync operations
"""

revision = 'cjdquick_sync_001'
down_revision = None  # Will be set by Alembic

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    op.create_table(
        'cjdquick_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False,
                  comment='PRODUCT, ORDER, CUSTOMER, PO, RETURN'),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment='FK-less reference to the Aquapurite entity'),
        sa.Column('oms_id', sa.String(255), nullable=True,
                  comment='ID returned by CJDQuick OMS'),
        sa.Column('operation', sa.String(50), nullable=False,
                  comment='CREATE, UPDATE, DELETE'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING',
                  comment='SUCCESS, FAILED, PENDING'),
        sa.Column('request_payload', postgresql.JSONB(), nullable=True,
                  comment='What we sent to OMS'),
        sa.Column('response_payload', postgresql.JSONB(), nullable=True,
                  comment='What OMS returned'),
        sa.Column('error_message', sa.Text(), nullable=True,
                  comment='Error details if sync failed'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True,
                  comment='When sync completed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )

    # Composite index on entity_type + entity_id for quick lookups
    op.create_index(
        'ix_cjdquick_sync_entity',
        'cjdquick_sync_logs',
        ['entity_type', 'entity_id'],
    )

    # Index on status for filtering
    op.create_index(
        'ix_cjdquick_sync_status',
        'cjdquick_sync_logs',
        ['status'],
    )

    # Index on created_at for date range queries
    op.create_index(
        'ix_cjdquick_sync_created',
        'cjdquick_sync_logs',
        ['created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_cjdquick_sync_created', table_name='cjdquick_sync_logs')
    op.drop_index('ix_cjdquick_sync_status', table_name='cjdquick_sync_logs')
    op.drop_index('ix_cjdquick_sync_entity', table_name='cjdquick_sync_logs')
    op.drop_table('cjdquick_sync_logs')
