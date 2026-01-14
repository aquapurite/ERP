"""Shipment models for order fulfillment and delivery tracking."""
import uuid
from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Float, Date, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.warehouse import Warehouse
    from app.models.transporter import Transporter
    from app.models.manifest import Manifest, ManifestItem
    from app.models.user import User


class ShipmentStatus(str, Enum):
    """Shipment status enumeration."""
    CREATED = "CREATED"               # Shipment created
    PACKED = "PACKED"                 # Order packed
    READY_FOR_PICKUP = "READY_FOR_PICKUP"  # Ready for transporter pickup
    MANIFESTED = "MANIFESTED"         # Added to manifest
    PICKED_UP = "PICKED_UP"           # Picked up by transporter
    IN_TRANSIT = "IN_TRANSIT"         # In transit
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"  # Out for delivery
    DELIVERED = "DELIVERED"           # Successfully delivered
    DELIVERY_FAILED = "DELIVERY_FAILED"    # Delivery attempt failed
    RTO_INITIATED = "RTO_INITIATED"   # Return to origin initiated
    RTO_IN_TRANSIT = "RTO_IN_TRANSIT"  # RTO shipment in transit
    RTO_DELIVERED = "RTO_DELIVERED"   # Returned to warehouse
    CANCELLED = "CANCELLED"           # Shipment cancelled
    LOST = "LOST"                     # Shipment lost


class PaymentMode(str, Enum):
    """Payment mode enumeration."""
    PREPAID = "PREPAID"
    COD = "COD"


class PackagingType(str, Enum):
    """Packaging type enumeration."""
    BOX = "BOX"
    ENVELOPE = "ENVELOPE"
    POLY_BAG = "POLY_BAG"
    PALLET = "PALLET"
    CUSTOM = "CUSTOM"


class Shipment(Base):
    """
    Shipment model for tracking individual packages/consignments.
    Represents a physical package being shipped to customer.
    """
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Identification
    shipment_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique shipment number e.g., SH-20240101-0001"
    )

    # Order reference
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Warehouse (origin)
    warehouse_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Transporter
    transporter_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("transporters.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Manifest reference
    manifest_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("manifests.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # AWB/Tracking
    awb_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Air Waybill number from transporter"
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    # Status
    status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus),
        default=ShipmentStatus.CREATED,
        nullable=False,
        index=True
    )

    # Payment
    payment_mode: Mapped[PaymentMode] = mapped_column(
        SQLEnum(PaymentMode),
        default=PaymentMode.PREPAID,
        nullable=False
    )
    cod_amount: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="COD amount to collect"
    )
    cod_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    cod_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Package details
    packaging_type: Mapped[PackagingType] = mapped_column(
        SQLEnum(PackagingType),
        default=PackagingType.BOX,
        nullable=False
    )
    no_of_boxes: Mapped[int] = mapped_column(Integer, default=1)

    # Weight (in kg)
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    volumetric_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chargeable_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimensions (in cm)
    length_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    breadth_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Shipping address (snapshot at time of shipment)
    ship_to_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ship_to_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    ship_to_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ship_to_address: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Full shipping address JSON"
    )
    ship_to_pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    ship_to_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ship_to_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Delivery scheduling
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    promised_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Delivery details
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_delivery_attempts: Mapped[int] = mapped_column(Integer, default=3)
    delivered_to: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of person who received the package"
    )
    delivery_relation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Relationship with customer e.g., Self, Family, Security"
    )
    delivery_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Proof of delivery
    pod_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pod_signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pod_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pod_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Documents
    shipping_label_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    invoice_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # RTO (Return to Origin) details
    rto_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rto_initiated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rto_delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Shipping charges
    shipping_charge: Mapped[float] = mapped_column(Float, default=0.0)
    cod_charge: Mapped[float] = mapped_column(Float, default=0.0)
    insurance_charge: Mapped[float] = mapped_column(Float, default=0.0)
    total_shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Created/Packed by
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    packed_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    packed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="shipments")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    transporter: Mapped[Optional["Transporter"]] = relationship(
        "Transporter",
        back_populates="shipments"
    )
    manifest: Mapped[Optional["Manifest"]] = relationship(
        "Manifest",
        back_populates="shipments"
    )
    manifest_item: Mapped[Optional["ManifestItem"]] = relationship(
        "ManifestItem",
        back_populates="shipment",
        uselist=False
    )
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by]
    )
    packed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[packed_by]
    )
    tracking_history: Mapped[List["ShipmentTracking"]] = relationship(
        "ShipmentTracking",
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="ShipmentTracking.created_at.desc()"
    )

    @property
    def is_delivered(self) -> bool:
        """Check if shipment is delivered."""
        return self.status == ShipmentStatus.DELIVERED

    @property
    def is_in_transit(self) -> bool:
        """Check if shipment is in transit."""
        return self.status in [
            ShipmentStatus.PICKED_UP,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.OUT_FOR_DELIVERY
        ]

    @property
    def is_rto(self) -> bool:
        """Check if shipment is RTO."""
        return self.status in [
            ShipmentStatus.RTO_INITIATED,
            ShipmentStatus.RTO_IN_TRANSIT,
            ShipmentStatus.RTO_DELIVERED
        ]

    @property
    def can_reattempt_delivery(self) -> bool:
        """Check if delivery can be reattempted."""
        return (
            self.status == ShipmentStatus.DELIVERY_FAILED and
            self.delivery_attempts < self.max_delivery_attempts
        )

    def __repr__(self) -> str:
        return f"<Shipment(number='{self.shipment_number}', status='{self.status}')>"


class ShipmentTracking(Base):
    """
    Shipment tracking history model.
    Records all status updates and tracking events.
    """
    __tablename__ = "shipment_tracking"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    shipment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Status
    status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus),
        nullable=False
    )
    status_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Transporter-specific status code"
    )

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transporter_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Remarks from transporter API"
    )

    # Event time
    event_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Time of the tracking event"
    )

    # Source
    source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Source of update: MANUAL, API, WEBHOOK"
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="tracking_history"
    )
    updated_by_user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<ShipmentTracking(status='{self.status}', location='{self.location}')>"
