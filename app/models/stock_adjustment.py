"""Stock Adjustment model for inventory corrections."""
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, Float
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base, TimestampMixin


class AdjustmentType(str, Enum):
    """Adjustment type enum."""
    CYCLE_COUNT = "cycle_count"  # Physical count variance
    DAMAGE = "damage"  # Damaged goods
    THEFT = "theft"  # Theft/pilferage
    EXPIRY = "expiry"  # Expired goods
    QUALITY_ISSUE = "quality_issue"  # Quality defects
    CORRECTION = "correction"  # Data correction
    WRITE_OFF = "write_off"  # Complete write-off
    FOUND = "found"  # Found stock (positive)
    OPENING_STOCK = "opening_stock"  # Initial stock entry
    OTHER = "other"


class AdjustmentStatus(str, Enum):
    """Adjustment status enum."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StockAdjustment(Base, TimestampMixin):
    """Stock adjustment/correction header."""

    __tablename__ = "stock_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    adjustment_number = Column(String(50), unique=True, nullable=False, index=True)
    adjustment_type = Column(SQLEnum(AdjustmentType), nullable=False, index=True)
    status = Column(SQLEnum(AdjustmentStatus), default=AdjustmentStatus.DRAFT, index=True)

    # Location
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)

    # Dates
    adjustment_date = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Users
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Approval
    requires_approval = Column(Integer, default=True)
    rejection_reason = Column(Text)

    # Totals
    total_items = Column(Integer, default=0)
    total_quantity_adjusted = Column(Integer, default=0)
    total_value_impact = Column(Float, default=0)  # Can be negative

    # Reason
    reason = Column(Text, nullable=False)
    reference_document = Column(String(100))  # PO, Invoice, etc.

    notes = Column(Text)

    # Relationships
    warehouse = relationship("Warehouse")
    items = relationship("StockAdjustmentItem", back_populates="adjustment", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<StockAdjustment {self.adjustment_number}>"


class StockAdjustmentItem(Base, TimestampMixin):
    """Items in a stock adjustment."""

    __tablename__ = "stock_adjustment_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    adjustment_id = Column(UUID(as_uuid=True), ForeignKey("stock_adjustments.id"), nullable=False, index=True)

    # Product
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    stock_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_items.id"))  # For serial tracked

    # Quantities
    system_quantity = Column(Integer, default=0)  # What system shows
    physical_quantity = Column(Integer, default=0)  # What was counted
    adjustment_quantity = Column(Integer, default=0)  # Difference (can be negative)

    # Cost impact
    unit_cost = Column(Float, default=0)
    value_impact = Column(Float, default=0)

    # Serial number if applicable
    serial_number = Column(String(100))

    reason = Column(Text)

    # Relationships
    adjustment = relationship("StockAdjustment", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    stock_item = relationship("StockItem")

    def __repr__(self):
        return f"<StockAdjustmentItem {self.id}>"


class InventoryAudit(Base, TimestampMixin):
    """Inventory audit/cycle count planning."""

    __tablename__ = "inventory_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    audit_number = Column(String(50), unique=True, nullable=False, index=True)
    audit_name = Column(String(200))

    # Scope
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))  # Optional: specific category

    # Schedule
    scheduled_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Status
    status = Column(String(50), default="planned")  # planned, in_progress, completed, cancelled

    # Users
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Results
    total_items_counted = Column(Integer, default=0)
    variance_items = Column(Integer, default=0)
    total_variance_value = Column(Float, default=0)

    # Linked adjustment
    adjustment_id = Column(UUID(as_uuid=True), ForeignKey("stock_adjustments.id"))

    notes = Column(Text)

    # Relationships
    warehouse = relationship("Warehouse")
    category = relationship("Category")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    adjustment = relationship("StockAdjustment")

    def __repr__(self):
        return f"<InventoryAudit {self.audit_number}>"
