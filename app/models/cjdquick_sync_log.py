"""
CJDQuick OMS Sync Log Model.

Tracks every sync operation between Aquapurite ERP and CJDQuick OMS
for debugging, reconciliation, and retry management.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class CJDQuickSyncLog(Base):
    """Audit log for CJDQuick OMS sync operations."""

    __tablename__ = "cjdquick_sync_logs"
    __table_args__ = (
        Index("ix_cjdquick_sync_entity", "entity_type", "entity_id"),
        Index("ix_cjdquick_sync_status", "status"),
        Index("ix_cjdquick_sync_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # What was synced
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="PRODUCT, ORDER, CUSTOMER, PO, RETURN",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="FK-less reference to the Aquapurite entity",
    )

    # OMS reference
    oms_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="ID returned by CJDQuick OMS (null if sync failed)",
    )

    # Operation details
    operation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="CREATE, UPDATE, DELETE",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        comment="SUCCESS, FAILED, PENDING",
    )

    # Payloads for debugging
    request_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="What we sent to OMS",
    )
    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="What OMS returned",
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if sync failed",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Timestamps
    synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When sync completed",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
