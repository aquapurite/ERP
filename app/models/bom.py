"""Bill of Materials (BOM) models - SAP CS01/CS02 equivalent."""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from decimal import Decimal

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class BillOfMaterials(Base):
    """Bill of Materials header - defines component structure for a product."""
    __tablename__ = "bill_of_materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    parent_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    bom_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bom_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PRODUCTION")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    base_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_component_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    parent_product: Mapped["Product"] = relationship("Product", foreign_keys=[parent_product_id])
    items: Mapped[List["BOMItem"]] = relationship(
        "BOMItem", back_populates="bom", cascade="all, delete-orphan"
    )
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<BillOfMaterials(number='{self.bom_number}', name='{self.name}')>"


class BOMItem(Base):
    """BOM line item - individual component in the bill of materials."""
    __tablename__ = "bom_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bill_of_materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("1"))
    uom: Mapped[str] = mapped_column(String(20), default="PCS")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    scrap_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    bom: Mapped["BillOfMaterials"] = relationship("BillOfMaterials", back_populates="items")
    component_product: Mapped["Product"] = relationship("Product", foreign_keys=[component_product_id])

    def __repr__(self) -> str:
        return f"<BOMItem(bom={self.bom_id}, component={self.component_product_id}, qty={self.quantity})>"
