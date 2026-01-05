"""Service Request model for after-sales service."""
from enum import Enum
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, DateTime, Date, Float, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base, TimestampMixin


class ServiceType(str, Enum):
    """Service type enum."""
    INSTALLATION = "installation"
    WARRANTY_REPAIR = "warranty_repair"
    PAID_REPAIR = "paid_repair"
    AMC_SERVICE = "amc_service"
    DEMO = "demo"
    PREVENTIVE_MAINTENANCE = "preventive_maintenance"
    COMPLAINT = "complaint"
    FILTER_CHANGE = "filter_change"
    INSPECTION = "inspection"
    UNINSTALLATION = "uninstallation"


class ServicePriority(str, Enum):
    """Service priority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ServiceStatus(str, Enum):
    """Service request status enum."""
    DRAFT = "draft"
    PENDING = "pending"
    ASSIGNED = "assigned"
    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    IN_PROGRESS = "in_progress"
    PARTS_REQUIRED = "parts_required"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    REOPENED = "reopened"


class ServiceSource(str, Enum):
    """Service request source enum."""
    CALL_CENTER = "call_center"
    WEBSITE = "website"
    MOBILE_APP = "mobile_app"
    WALK_IN = "walk_in"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    AUTO_AMC = "auto_amc"  # Auto-generated from AMC
    REFERRAL = "referral"


class ServiceRequest(Base, TimestampMixin):
    """Service request/ticket model."""

    __tablename__ = "service_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    service_type = Column(SQLEnum(ServiceType), nullable=False, index=True)
    source = Column(SQLEnum(ServiceSource), default=ServiceSource.CALL_CENTER)
    priority = Column(SQLEnum(ServicePriority), default=ServicePriority.NORMAL, index=True)
    status = Column(SQLEnum(ServiceStatus), default=ServiceStatus.PENDING, index=True)

    # Customer
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    customer_address_id = Column(UUID(as_uuid=True), ForeignKey("customer_addresses.id"))

    # Product/Order reference
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    order_item_id = Column(UUID(as_uuid=True))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    serial_number = Column(String(100), index=True)

    # Installation details (for installation type)
    installation_id = Column(UUID(as_uuid=True), ForeignKey("installations.id"))

    # AMC reference (if applicable)
    amc_id = Column(UUID(as_uuid=True), ForeignKey("amc_contracts.id"))

    # Problem description
    title = Column(String(255), nullable=False)
    description = Column(Text)
    symptoms = Column(JSON)  # List of symptoms selected
    customer_reported_issue = Column(Text)

    # Location (snapshot of address)
    service_address = Column(JSON)  # Full address JSON
    service_pincode = Column(String(10), index=True)
    service_city = Column(String(100))
    service_state = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)

    # Assignment
    technician_id = Column(UUID(as_uuid=True), ForeignKey("technicians.id"))
    assigned_at = Column(DateTime)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Scheduling
    preferred_date = Column(Date)
    preferred_time_slot = Column(String(50))  # "9AM-12PM", "12PM-3PM", etc.
    scheduled_date = Column(Date)
    scheduled_time_slot = Column(String(50))

    # Region
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"))

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    closed_at = Column(DateTime)
    sla_breach_at = Column(DateTime)
    is_sla_breached = Column(Boolean, default=False)

    # Resolution
    resolution_type = Column(String(50))  # repaired, replaced, no_issue_found, etc.
    resolution_notes = Column(Text)
    root_cause = Column(Text)
    action_taken = Column(Text)

    # Parts used
    parts_used = Column(JSON)  # [{"part_id": "", "quantity": 1, "serial": ""}]
    total_parts_cost = Column(Float, default=0)

    # Charges
    labor_charges = Column(Float, default=0)
    service_charges = Column(Float, default=0)
    travel_charges = Column(Float, default=0)
    total_charges = Column(Float, default=0)
    is_chargeable = Column(Boolean, default=False)
    payment_status = Column(String(50))  # pending, paid, waived
    payment_collected = Column(Float, default=0)
    payment_mode = Column(String(50))

    # Feedback
    customer_rating = Column(Integer)  # 1-5
    customer_feedback = Column(Text)
    feedback_date = Column(DateTime)

    # Attachments
    images_before = Column(JSON)  # URLs
    images_after = Column(JSON)
    customer_signature_url = Column(String(500))

    # Internal
    internal_notes = Column(Text)
    escalation_level = Column(Integer, default=0)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    escalation_reason = Column(Text)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    customer = relationship("Customer", back_populates="service_requests")
    customer_address = relationship("CustomerAddress")
    order = relationship("Order")
    product = relationship("Product")
    installation = relationship("Installation", back_populates="service_requests")
    amc = relationship("AMCContract", back_populates="service_requests")
    technician = relationship("Technician", back_populates="service_requests")
    region = relationship("Region")
    assigner = relationship("User", foreign_keys=[assigned_by])
    escalation_user = relationship("User", foreign_keys=[escalated_to])
    creator = relationship("User", foreign_keys=[created_by])
    status_history = relationship("ServiceStatusHistory", back_populates="service_request", cascade="all, delete-orphan")
    technician_history = relationship("TechnicianJobHistory", back_populates="service_request")
    parts_requests = relationship("PartsRequest", back_populates="service_request")

    def __repr__(self):
        return f"<ServiceRequest {self.ticket_number}>"


class ServiceStatusHistory(Base, TimestampMixin):
    """Service request status history."""

    __tablename__ = "service_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    service_request_id = Column(UUID(as_uuid=True), ForeignKey("service_requests.id"), nullable=False, index=True)

    from_status = Column(SQLEnum(ServiceStatus))
    to_status = Column(SQLEnum(ServiceStatus), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="status_history")
    changer = relationship("User")

    def __repr__(self):
        return f"<ServiceStatusHistory {self.id}>"


class PartsRequest(Base, TimestampMixin):
    """Parts request for a service job."""

    __tablename__ = "parts_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    request_number = Column(String(50), unique=True, nullable=False, index=True)
    service_request_id = Column(UUID(as_uuid=True), ForeignKey("service_requests.id"), nullable=False, index=True)

    status = Column(String(50), default="pending")  # pending, approved, dispatched, delivered, returned

    # Items
    items = Column(JSON)  # [{"product_id": "", "quantity": 1, "notes": ""}]

    # Warehouse
    from_warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"))

    # Approval
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Delivery
    dispatched_at = Column(DateTime)
    delivered_at = Column(DateTime)

    notes = Column(Text)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="parts_requests")
    warehouse = relationship("Warehouse")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<PartsRequest {self.request_number}>"
