"""Batch Management models - SAP MSC1N/MSC2N equivalent."""
import uuid
from datetime import datetime, date, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, DateTime, Date, ForeignKey, Integer, Text, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.warehouse import Warehouse
    from app.models.vendor import Vendor
    from app.models.purchase import GoodsReceiptNote, GRNItem
    from app.models.inventory import StockItem, StockMovement


class BatchStatus(str, Enum):
    """Batch status - SAP equivalent."""
    UNRESTRICTED = "UNRESTRICTED"  # Available for use
    RESTRICTED = "RESTRICTED"      # Limited use (e.g., pending QC)
    BLOCKED = "BLOCKED"            # Blocked from use
    EXPIRED = "EXPIRED"            # Past expiry date


class BatchMaster(Base):
    """
    Batch Master Record - SAP MSC1N equivalent.
    Tracks batch-level inventory for batch-managed products.
    """
    __tablename__ = "batch_master"
    __table_args__ = (
        UniqueConstraint("batch_number", "product_id", "warehouse_id", name="uq_batch_product_warehouse"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Batch identification
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True
    )

    # Status
    batch_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="UNRESTRICTED",
        index=True,
        comment="UNRESTRICTED, RESTRICTED, BLOCKED, EXPIRED"
    )

    # Dates
    manufacturing_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True, index=True)

    # Vendor info
    vendor_batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id"),
        nullable=True
    )

    # Quality
    quality_grade: Mapped[Optional[str]] = mapped_column(String(10), default="A")

    # GRN linkage
    grn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goods_receipt_notes.id"),
        nullable=True
    )
    grn_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grn_items.id"),
        nullable=True
    )

    # Quantities
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_issued: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cost
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), default=0)
    total_value: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), default=0)

    # Shelf life
    shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minimum_remaining_shelf_life_days: Mapped[int] = mapped_column(Integer, default=30)

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
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")
    grn: Mapped[Optional["GoodsReceiptNote"]] = relationship("GoodsReceiptNote")

    @property
    def is_expired(self) -> bool:
        """Check if batch is past expiry date."""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry. Negative means expired."""
        if self.expiry_date:
            delta = self.expiry_date - date.today()
            return delta.days
        return None

    def __repr__(self) -> str:
        return f"<BatchMaster(batch={self.batch_number}, product_id={self.product_id}, status={self.batch_status})>"
