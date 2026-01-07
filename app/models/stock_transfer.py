"""Stock Transfer model for warehouse-to-warehouse movements."""
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, Float
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base, TimestampMixin


class TransferStatus(str, Enum):
    """Transfer status enum."""
    DRAFT = "draft"  # Being created
    PENDING_APPROVAL = "pending_approval"  # Awaiting approval
    APPROVED = "approved"  # Approved, ready to dispatch
    REJECTED = "rejected"  # Rejected
    IN_TRANSIT = "in_transit"  # Goods dispatched
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"  # Fully received
    CANCELLED = "cancelled"


class TransferType(str, Enum):
    """Transfer type enum."""
    STOCK_TRANSFER = "stock_transfer"  # Regular transfer
    REPLENISHMENT = "replenishment"  # Auto-replenishment
    RETURN_TO_MAIN = "return_to_main"  # Return to central warehouse
    INTER_REGION = "inter_region"  # Between regions
    DEALER_SUPPLY = "dealer_supply"  # To dealer


class StockTransfer(Base, TimestampMixin):
    """Stock transfer between warehouses."""

    __tablename__ = "stock_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Transfer identification
    transfer_number = Column(String(50), unique=True, nullable=False, index=True)
    transfer_type = Column(SQLEnum(TransferType), default=TransferType.STOCK_TRANSFER)
    status = Column(SQLEnum(TransferStatus), default=TransferStatus.DRAFT, index=True)

    # Warehouses
    from_warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    to_warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)

    # Dates
    request_date = Column(DateTime, default=datetime.utcnow)
    expected_date = Column(DateTime)
    dispatch_date = Column(DateTime)
    received_date = Column(DateTime)

    # Users involved
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    dispatched_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Approval
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Totals
    total_items = Column(Integer, default=0)
    total_quantity = Column(Integer, default=0)
    total_value = Column(Float, default=0)
    received_quantity = Column(Integer, default=0)

    # Logistics
    vehicle_number = Column(String(50))
    driver_name = Column(String(100))
    driver_phone = Column(String(20))
    challan_number = Column(String(50))
    eway_bill_number = Column(String(50))

    notes = Column(Text)
    internal_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_warehouse = relationship(
        "Warehouse",
        foreign_keys=[from_warehouse_id],
        back_populates="outgoing_transfers"
    )
    to_warehouse = relationship(
        "Warehouse",
        foreign_keys=[to_warehouse_id],
        back_populates="incoming_transfers"
    )
    items = relationship("StockTransferItem", back_populates="transfer", cascade="all, delete-orphan")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    dispatcher = relationship("User", foreign_keys=[dispatched_by])
    receiver = relationship("User", foreign_keys=[received_by])

    def __repr__(self):
        return f"<StockTransfer {self.transfer_number}>"


class StockTransferItem(Base, TimestampMixin):
    """Items in a stock transfer."""

    __tablename__ = "stock_transfer_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transfer_id = Column(UUID(as_uuid=True), ForeignKey("stock_transfers.id"), nullable=False, index=True)

    # Product
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))

    # Quantities
    requested_quantity = Column(Integer, nullable=False)
    approved_quantity = Column(Integer)
    dispatched_quantity = Column(Integer)
    received_quantity = Column(Integer, default=0)
    damaged_quantity = Column(Integer, default=0)

    # Unit cost for valuation
    unit_cost = Column(Float, default=0)
    total_cost = Column(Float, default=0)

    notes = Column(Text)

    # Relationships
    transfer = relationship("StockTransfer", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    serial_items = relationship("StockTransferSerial", back_populates="transfer_item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StockTransferItem {self.id}>"


class StockTransferSerial(Base, TimestampMixin):
    """Serial numbers in a transfer item."""

    __tablename__ = "stock_transfer_serials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transfer_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_transfer_items.id"), nullable=False)
    stock_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_items.id"), nullable=False)

    # Status
    is_dispatched = Column(Integer, default=False)
    is_received = Column(Integer, default=False)
    is_damaged = Column(Integer, default=False)

    received_at = Column(DateTime)
    damage_notes = Column(Text)

    # Relationships
    transfer_item = relationship("StockTransferItem", back_populates="serial_items")
    stock_item = relationship("StockItem")

    def __repr__(self):
        return f"<StockTransferSerial {self.id}>"
