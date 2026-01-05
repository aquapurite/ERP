import uuid
from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.region import Region
    from app.models.service_request import ServiceRequest
    from app.models.installation import Installation
    from app.models.amc import AMCContract


class CustomerType(str, Enum):
    """Customer type enumeration."""
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"
    DEALER = "DEALER"
    DISTRIBUTOR = "DISTRIBUTOR"


class CustomerSource(str, Enum):
    """Customer acquisition source."""
    WEBSITE = "WEBSITE"
    WALK_IN = "WALK_IN"
    REFERRAL = "REFERRAL"
    DEALER = "DEALER"
    CAMPAIGN = "CAMPAIGN"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    OTHER = "OTHER"


class AddressType(str, Enum):
    """Address type enumeration."""
    HOME = "HOME"
    OFFICE = "OFFICE"
    BILLING = "BILLING"
    SHIPPING = "SHIPPING"
    OTHER = "OTHER"


class Customer(Base):
    """
    Customer model for CRM and orders.
    Stores customer information and relationships.
    """
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic Info
    customer_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Type & Source
    customer_type: Mapped[CustomerType] = mapped_column(
        SQLEnum(CustomerType),
        default=CustomerType.INDIVIDUAL,
        nullable=False
    )
    source: Mapped[CustomerSource] = mapped_column(
        SQLEnum(CustomerSource),
        default=CustomerSource.WEBSITE,
        nullable=False
    )

    # Business Info (for business customers)
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Demographics
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    anniversary_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Region for filtering
    region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    region: Mapped[Optional["Region"]] = relationship("Region")
    addresses: Mapped[List["CustomerAddress"]] = relationship(
        "CustomerAddress",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="customer"
    )
    service_requests: Mapped[List["ServiceRequest"]] = relationship(
        "ServiceRequest",
        back_populates="customer"
    )
    installations: Mapped[List["Installation"]] = relationship(
        "Installation",
        back_populates="customer"
    )
    amc_contracts: Mapped[List["AMCContract"]] = relationship(
        "AMCContract",
        back_populates="customer"
    )

    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def default_address(self) -> Optional["CustomerAddress"]:
        """Get default address."""
        for addr in self.addresses:
            if addr.is_default:
                return addr
        return self.addresses[0] if self.addresses else None

    def __repr__(self) -> str:
        return f"<Customer(code='{self.customer_code}', name='{self.full_name}')>"


class CustomerAddress(Base):
    """Customer address model."""
    __tablename__ = "customer_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Address Type
    address_type: Mapped[AddressType] = mapped_column(
        SQLEnum(AddressType),
        default=AddressType.HOME,
        nullable=False
    )

    # Contact for this address
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Address Lines
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Location
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)

    # Coordinates (for delivery tracking)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Flags
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

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
    customer: Mapped["Customer"] = relationship("Customer", back_populates="addresses")

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        parts.append(f"{self.city}, {self.state} - {self.pincode}")
        return ", ".join(parts)

    def __repr__(self) -> str:
        return f"<CustomerAddress(type='{self.address_type}', city='{self.city}')>"
