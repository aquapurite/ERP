"""Purchase/Procurement models for Procure-to-Pay cycle.

Supports:
- Purchase Requisition (Internal request)
- Purchase Order (PO)
- Goods Receipt Note (GRN)
- Vendor Invoice matching
- 3-Way Matching (PO-GRN-Invoice)
"""
import uuid
from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from decimal import Decimal

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Numeric, Date, JSON
from sqlalchemy import Enum as SQLEnum, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.warehouse import Warehouse
    from app.models.product import Product, ProductVariant
    from app.models.vendor import Vendor
    from app.models.wms import WarehouseBin


# ==================== Enums ====================

class RequisitionStatus(str, Enum):
    """Purchase Requisition status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONVERTED = "CONVERTED"  # Converted to PO
    CANCELLED = "CANCELLED"


class POStatus(str, Enum):
    """Purchase Order status."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT_TO_VENDOR = "SENT_TO_VENDOR"
    ACKNOWLEDGED = "ACKNOWLEDGED"  # Vendor acknowledged
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class GRNStatus(str, Enum):
    """Goods Receipt Note status."""
    DRAFT = "DRAFT"
    PENDING_QC = "PENDING_QC"  # Quality check pending
    QC_PASSED = "QC_PASSED"
    QC_FAILED = "QC_FAILED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PUT_AWAY_PENDING = "PUT_AWAY_PENDING"
    PUT_AWAY_COMPLETE = "PUT_AWAY_COMPLETE"
    CANCELLED = "CANCELLED"


class VendorInvoiceStatus(str, Enum):
    """Vendor Invoice status."""
    RECEIVED = "RECEIVED"
    UNDER_VERIFICATION = "UNDER_VERIFICATION"
    MATCHED = "MATCHED"  # 3-way matched
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MISMATCH = "MISMATCH"  # Discrepancy found
    APPROVED = "APPROVED"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAID = "PAID"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class QualityCheckResult(str, Enum):
    """Quality inspection result."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    CONDITIONAL = "CONDITIONAL"  # Accepted with deviation
    PENDING = "PENDING"


# ==================== Purchase Requisition ====================

class PurchaseRequisition(Base):
    """
    Internal purchase request model.
    Created by departments to request purchases.
    """
    __tablename__ = "purchase_requisitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Identification
    requisition_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="PR-YYYYMMDD-XXXX"
    )

    # Status
    status: Mapped[RequisitionStatus] = mapped_column(
        SQLEnum(RequisitionStatus),
        default=RequisitionStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Requesting Details
    requesting_department: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="WAREHOUSE, SERVICE, MARKETING etc."
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    request_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False
    )

    # Delivery Requirements
    required_by_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Priority
    priority: Mapped[int] = mapped_column(
        Integer,
        default=5,
        comment="1=Urgent, 5=Normal, 10=Low"
    )

    # Total (for approval limits)
    estimated_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0")
    )

    # Reason/Justification
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Approval
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Conversion to PO
    converted_to_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="PO ID if converted"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    requested_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by]
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by]
    )
    delivery_warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    items: Mapped[List["PurchaseRequisitionItem"]] = relationship(
        "PurchaseRequisitionItem",
        back_populates="requisition",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PurchaseRequisition(number='{self.requisition_number}')>"


class PurchaseRequisitionItem(Base):
    """Line items in a Purchase Requisition."""
    __tablename__ = "purchase_requisition_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    requisition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True
    )

    # Snapshot
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)

    # Quantity
    quantity_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    uom: Mapped[str] = mapped_column(
        String(20),
        default="PCS",
        comment="Unit of measure"
    )

    # Estimated Price
    estimated_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    estimated_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )

    # Preferred Vendor (optional suggestion)
    preferred_vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    requisition: Mapped["PurchaseRequisition"] = relationship(
        "PurchaseRequisition",
        back_populates="items"
    )
    product: Mapped["Product"] = relationship("Product")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant")
    preferred_vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")


# ==================== Purchase Order ====================

class PurchaseOrder(Base):
    """
    Purchase Order model.
    Official order placed with vendor.
    """
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_vendor_date", "vendor_id", "po_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Identification
    po_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="PO-YYYYMMDD-XXXX"
    )
    po_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Status
    status: Mapped[POStatus] = mapped_column(
        SQLEnum(POStatus),
        default=POStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Vendor
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # From Requisition (optional)
    requisition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Delivery
    delivery_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_address: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Delivery address if different from warehouse"
    )

    # Vendor Details Snapshot
    vendor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vendor_gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    vendor_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Amounts (Taxable)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        comment="Sum of line totals before tax"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        comment="Subtotal - Discount"
    )

    # GST Breakup
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    total_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )

    # Other Charges
    freight_charges: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    packing_charges: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    other_charges: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )

    # Grand Total
    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    # Received Tracking
    total_received_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0")
    )

    # Payment Terms
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, default=30)
    advance_required: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        comment="Advance amount if required"
    )
    advance_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )

    # Reference
    quotation_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Vendor's quotation reference"
    )
    quotation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Terms & Conditions
    terms_and_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Communication
    sent_to_vendor_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    vendor_acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Documents
    po_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Approval Workflow
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Internal Notes
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="purchase_orders")
    requisition: Mapped[Optional["PurchaseRequisition"]] = relationship("PurchaseRequisition")
    delivery_warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    grns: Mapped[List["GoodsReceiptNote"]] = relationship(
        "GoodsReceiptNote",
        back_populates="purchase_order"
    )

    @property
    def is_fully_received(self) -> bool:
        """Check if PO is fully received."""
        return all(
            item.quantity_received >= item.quantity_ordered
            for item in self.items
        )

    @property
    def receipt_percentage(self) -> Decimal:
        """Calculate receipt completion percentage."""
        if self.grand_total > 0:
            return (self.total_received_value / self.grand_total) * 100
        return Decimal("0")

    def __repr__(self) -> str:
        return f"<PurchaseOrder(number='{self.po_number}', status='{self.status}')>"


class PurchaseOrderItem(Base):
    """Line items in a Purchase Order."""
    __tablename__ = "purchase_order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True
    )

    # Snapshot
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Line Number
    line_number: Mapped[int] = mapped_column(Integer, default=1)

    # Quantity
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0)
    quantity_accepted: Mapped[int] = mapped_column(Integer, default=0)
    quantity_rejected: Mapped[int] = mapped_column(Integer, default=0)
    quantity_pending: Mapped[int] = mapped_column(Integer, default=0)
    uom: Mapped[str] = mapped_column(String(20), default="PCS")

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    # GST
    gst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("18")
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0")
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )

    # Line Total
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    # Delivery
    expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Manually closed (no more receipts expected)"
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="items"
    )
    product: Mapped["Product"] = relationship("Product")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant")

    def __repr__(self) -> str:
        return f"<PurchaseOrderItem(sku='{self.sku}', qty={self.quantity_ordered})>"


# ==================== Goods Receipt Note (GRN) ====================

class GoodsReceiptNote(Base):
    """
    Goods Receipt Note model.
    Records material received against PO.
    """
    __tablename__ = "goods_receipt_notes"
    __table_args__ = (
        Index("ix_grn_po", "purchase_order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Identification
    grn_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="GRN-YYYYMMDD-XXXX"
    )
    grn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Status
    status: Mapped[GRNStatus] = mapped_column(
        SQLEnum(GRNStatus),
        default=GRNStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Against PO
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Vendor
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Receiving Warehouse
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Vendor's Delivery Reference
    vendor_challan_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Vendor's delivery challan/DC number"
    )
    vendor_challan_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Transport Details
    transporter_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    lr_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Lorry Receipt number"
    )
    e_way_bill_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Quantities Summary
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    total_quantity_received: Mapped[int] = mapped_column(Integer, default=0)
    total_quantity_accepted: Mapped[int] = mapped_column(Integer, default=0)
    total_quantity_rejected: Mapped[int] = mapped_column(Integer, default=0)

    # Value
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0"),
        comment="Value of accepted goods"
    )

    # Quality Check
    qc_required: Mapped[bool] = mapped_column(Boolean, default=True)
    qc_status: Mapped[Optional[QualityCheckResult]] = mapped_column(
        SQLEnum(QualityCheckResult),
        nullable=True
    )
    qc_done_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    qc_done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    qc_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Receiving
    received_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    receiving_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Put Away Status
    put_away_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    put_away_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Documents
    grn_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    photos_urls: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Photos of received goods"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="grns"
    )
    vendor: Mapped["Vendor"] = relationship("Vendor")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    received_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[received_by]
    )
    qc_done_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[qc_done_by]
    )
    items: Mapped[List["GRNItem"]] = relationship(
        "GRNItem",
        back_populates="grn",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GoodsReceiptNote(number='{self.grn_number}', status='{self.status}')>"


class GRNItem(Base):
    """Line items in a GRN."""
    __tablename__ = "grn_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    grn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goods_receipt_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to PO Item
    po_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_items.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Product
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True
    )

    # Snapshot
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)

    # Quantities
    quantity_expected: Mapped[int] = mapped_column(
        Integer,
        comment="Qty expected from PO"
    )
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_accepted: Mapped[int] = mapped_column(Integer, default=0)
    quantity_rejected: Mapped[int] = mapped_column(Integer, default=0)
    uom: Mapped[str] = mapped_column(String(20), default="PCS")

    # Unit Price (from PO)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accepted_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )

    # Batch/Serial
    batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    manufacturing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    serial_numbers: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="List of serial numbers received"
    )

    # Put Away Location
    bin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_bins.id", ondelete="SET NULL"),
        nullable=True
    )
    bin_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Quality Check
    qc_result: Mapped[Optional[QualityCheckResult]] = mapped_column(
        SQLEnum(QualityCheckResult),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    grn: Mapped["GoodsReceiptNote"] = relationship("GoodsReceiptNote", back_populates="items")
    po_item: Mapped["PurchaseOrderItem"] = relationship("PurchaseOrderItem")
    product: Mapped["Product"] = relationship("Product")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant")
    bin: Mapped[Optional["WarehouseBin"]] = relationship("WarehouseBin")

    def __repr__(self) -> str:
        return f"<GRNItem(sku='{self.sku}', received={self.quantity_received})>"


# ==================== Vendor Invoice ====================

class VendorInvoice(Base):
    """
    Vendor Invoice model for 3-way matching.
    Records invoices received from vendors.
    """
    __tablename__ = "vendor_invoices"
    __table_args__ = (
        UniqueConstraint("vendor_id", "invoice_number", name="uq_vendor_invoice"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Vendor's Invoice Details
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Vendor's invoice number"
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Our Reference
    our_reference: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Our internal reference VI-YYYYMMDD-XXXX"
    )

    # Status
    status: Mapped[VendorInvoiceStatus] = mapped_column(
        SQLEnum(VendorInvoiceStatus),
        default=VendorInvoiceStatus.RECEIVED,
        nullable=False,
        index=True
    )

    # Vendor
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Linked Documents
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True
    )
    grn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goods_receipt_notes.id", ondelete="SET NULL"),
        nullable=True
    )

    # Invoice Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # GST
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    cess_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    total_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # Other Charges
    freight_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    other_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    # Round Off
    round_off: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0")
    )

    # Grand Total
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Payment
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0")
    )
    balance_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # TDS
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    tds_section: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    tds_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    net_payable: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        comment="Grand Total - TDS"
    )

    # 3-Way Matching
    po_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    grn_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fully_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    matching_variance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        comment="Difference if any"
    )
    variance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # E-Invoice Details (if received from vendor)
    vendor_irn: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    vendor_ack_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Documents
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Workflow
    received_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Internal
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    grn: Mapped[Optional["GoodsReceiptNote"]] = relationship("GoodsReceiptNote")
    received_by_user: Mapped["User"] = relationship("User", foreign_keys=[received_by])
    verified_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by])
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        return date.today() > self.due_date and self.balance_due > 0

    @property
    def days_overdue(self) -> int:
        """Calculate days overdue."""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0

    def __repr__(self) -> str:
        return f"<VendorInvoice(ref='{self.our_reference}', vendor_inv='{self.invoice_number}')>"
