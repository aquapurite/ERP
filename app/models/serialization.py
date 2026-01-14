"""
Serialization Models for Product and Spare Parts Barcodes

Barcode Structure: APFSZAIEL000001 (15 characters)
- AP: Brand Prefix (Aquapurite)
- FS: Supplier Code (2 letters)
- Z: Year Code (A=2000, Z=2025, AA=2026...)
- A: Month Code (A=Jan, L=Dec)
- IEL: Model Code (3 letters)
- 000001: Serial Number (6 digits, 000001-999999)
"""

import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class SerialStatus(str, enum.Enum):
    """Status of a serial/barcode"""
    GENERATED = "GENERATED"      # Serial generated, not yet printed
    PRINTED = "PRINTED"          # Barcode printed/exported
    SENT_TO_VENDOR = "SENT_TO_VENDOR"  # Sent to vendor for application
    RECEIVED = "RECEIVED"        # Received in GRN, scanned
    ASSIGNED = "ASSIGNED"        # Assigned to stock item
    SOLD = "SOLD"               # Item sold to customer
    RETURNED = "RETURNED"        # Item returned
    DAMAGED = "DAMAGED"          # Item damaged/scrapped
    CANCELLED = "CANCELLED"      # Serial cancelled


class ItemType(str, enum.Enum):
    """Type of item being serialized"""
    FINISHED_GOODS = "FG"        # Finished Goods (Water Purifiers)
    SPARE_PART = "SP"            # Spare Parts (Sub Assemblies)
    COMPONENT = "CO"             # Components (Electrical, etc.)


class SerialSequence(Base):
    """
    LEGACY: Tracks serial number by model + supplier + year + month.
    Kept for backward compatibility with existing data.
    New POs should use ProductSerialSequence instead.
    """
    __tablename__ = "serial_sequences"

    # Use String to avoid UUID type casting issues
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Product identification
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    model_code = Column(String(10), nullable=False, index=True)  # IEL, IPR, PRG, etc.
    item_type = Column(Enum(ItemType), default=ItemType.FINISHED_GOODS)

    # Sequence key components
    supplier_code = Column(String(2), nullable=False, index=True)  # FS, AB, TC, etc.
    year_code = Column(String(2), nullable=False)  # A-Z, then AA, AB...
    month_code = Column(String(1), nullable=False)  # A-L

    # Sequence tracking
    last_serial = Column(Integer, default=0, nullable=False)
    total_generated = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", backref="serial_sequences")

    def __repr__(self):
        return f"<SerialSequence {self.supplier_code}{self.year_code}{self.month_code}{self.model_code}: {self.last_serial}>"


class ProductSerialSequence(Base):
    """
    Tracks serial numbers at PRODUCT/MODEL level.
    Each product model (Aura, Elige, etc.) has its own independent serial sequence.

    Serial numbers are continuous and do NOT reset by year/month.
    Each model can have serials from 1 to 99,999,999.

    Separate sequences for FG and SP:
    - FG Aura (IEL): 00000001 to 99999999
    - SP Aura (IEL): 00000001 to 99999999 (separate sequence)

    Example:
    - FG: Aura (IEL): 00000001 to 99999999
    - FG: Elige (ELG): 00000001 to 99999999
    - SP: Motor Assembly (MTR): 00000001 to 99999999
    """
    __tablename__ = "product_serial_sequences"

    # Use String to avoid UUID type casting issues with VARCHAR columns
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Product identification - unique per (model_code + item_type) combination
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    model_code = Column(String(10), nullable=False, index=True)  # IEL, ELG, AUR, MTR, etc.
    item_type = Column(Enum(ItemType), nullable=False, default=ItemType.FINISHED_GOODS)

    # Unique constraint on model_code + item_type (FG and SP can have same model_code)
    __table_args__ = (
        UniqueConstraint('model_code', 'item_type', name='uq_model_code_item_type'),
    )

    # Product info (denormalized for quick access)
    product_name = Column(String(255), nullable=True)
    product_sku = Column(String(50), nullable=True)

    # Sequence tracking - continuous across all time
    last_serial = Column(Integer, default=0, nullable=False)
    total_generated = Column(Integer, default=0)
    max_serial = Column(Integer, default=99999999)  # Default 1 lakh = 100000, can be extended

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", backref="product_serial_sequence")

    @property
    def available_serials(self):
        """How many serial numbers are still available"""
        return self.max_serial - self.last_serial

    @property
    def utilization_percentage(self):
        """Percentage of serial numbers used"""
        if self.max_serial > 0:
            return (self.last_serial / self.max_serial) * 100
        return 0

    def __repr__(self):
        return f"<ProductSerialSequence {self.model_code}: {self.last_serial}/{self.max_serial}>"


class POSerial(Base):
    """
    Individual serial numbers/barcodes generated for Purchase Orders.
    Each row represents one unique barcode that will be applied to one unit.
    """
    __tablename__ = "po_serials"

    # Use String to avoid UUID type casting issues with VARCHAR columns
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # PO linkage
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    po_item_id = Column(String(36), ForeignKey("purchase_order_items.id"), nullable=True)

    # Product identification
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    product_sku = Column(String(50), nullable=True)
    model_code = Column(String(10), nullable=False)
    item_type = Column(Enum(ItemType), default=ItemType.FINISHED_GOODS)

    # Barcode components
    brand_prefix = Column(String(2), default="AP")  # AP for Aquapurite
    supplier_code = Column(String(2), nullable=False)
    year_code = Column(String(2), nullable=False)
    month_code = Column(String(1), nullable=False)
    serial_number = Column(Integer, nullable=False)  # 1-999999

    # Full barcode (computed: APFSZAIEL000001)
    barcode = Column(String(20), unique=True, nullable=False, index=True)

    # Status tracking
    status = Column(Enum(SerialStatus), default=SerialStatus.GENERATED)

    # GRN linkage (when received)
    grn_id = Column(String(36), ForeignKey("goods_receipt_notes.id"), nullable=True)
    grn_item_id = Column(String(36), nullable=True)
    received_at = Column(DateTime, nullable=True)
    received_by = Column(String(36), nullable=True)

    # Stock item linkage (when assigned to inventory)
    stock_item_id = Column(String(36), ForeignKey("stock_items.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # Sale linkage (when sold)
    order_id = Column(String(36), nullable=True)
    order_item_id = Column(String(36), nullable=True)
    sold_at = Column(DateTime, nullable=True)
    customer_id = Column(String(36), nullable=True)

    # Warranty tracking
    warranty_start_date = Column(DateTime, nullable=True)
    warranty_end_date = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", backref="serials")
    product = relationship("Product", backref="serials")
    stock_item = relationship("StockItem", backref="serial_info")
    grn = relationship("GoodsReceiptNote", backref="scanned_serials")

    def __repr__(self):
        return f"<POSerial {self.barcode} ({self.status.value})>"


class ModelCodeReference(Base):
    """
    Reference table mapping product SKUs to their 3-letter model codes.
    This helps in generating correct barcodes for products.
    """
    __tablename__ = "model_code_references"

    # Use String to avoid UUID type casting issues
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Product linkage
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True, unique=True)
    product_sku = Column(String(50), nullable=True, index=True)

    # FG/Item Code (full code like WPRAIEL001)
    fg_code = Column(String(20), nullable=True, unique=True, index=True)

    # Model code for barcode (3 letters: IEL, IPR, PRG)
    model_code = Column(String(10), nullable=False, index=True)

    # Item type
    item_type = Column(Enum(ItemType), default=ItemType.FINISHED_GOODS)

    # Description
    description = Column(String(255), nullable=True)

    # Active flag
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    product = relationship("Product", backref="model_code_ref")

    def __repr__(self):
        return f"<ModelCodeReference {self.fg_code} -> {self.model_code}>"


class SupplierCode(Base):
    """
    Supplier codes for barcode generation.
    Each supplier gets a unique 2-letter code.
    """
    __tablename__ = "supplier_codes"

    # Use String to avoid UUID type casting issues
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Vendor linkage
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=True, unique=True)

    # 2-letter supplier code
    code = Column(String(2), unique=True, nullable=False, index=True)

    # Supplier name
    name = Column(String(100), nullable=False)

    # Description
    description = Column(String(255), nullable=True)

    # Active flag
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    vendor = relationship("Vendor", backref="supplier_code_ref")

    def __repr__(self):
        return f"<SupplierCode {self.code} ({self.name})>"
