"""
Escalation Management Models.

This module contains models for:
- Escalation levels/tiers
- Escalation matrix configuration
- Escalation tracking
- SLA management
- Auto-escalation rules
"""
import uuid
import enum
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, Date,
    ForeignKey, Numeric, Enum as SQLEnum, JSON, Interval
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EscalationLevel(str, enum.Enum):
    """Escalation level/tier."""
    L1 = "L1"  # First level - Agent/Executive
    L2 = "L2"  # Second level - Team Lead/Supervisor
    L3 = "L3"  # Third level - Manager
    L4 = "L4"  # Fourth level - Senior Manager/Head
    L5 = "L5"  # Fifth level - Director/VP
    CRITICAL = "CRITICAL"  # CEO/Top Management


class EscalationStatus(str, enum.Enum):
    """Status of escalation."""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    PENDING_RESPONSE = "PENDING_RESPONSE"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"
    AUTO_CLOSED = "AUTO_CLOSED"


class EscalationPriority(str, enum.Enum):
    """Priority of escalation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationSource(str, enum.Enum):
    """Source/type of escalation."""
    SERVICE_REQUEST = "SERVICE_REQUEST"
    COMPLAINT = "COMPLAINT"
    ORDER = "ORDER"
    CALL = "CALL"
    LEAD = "LEAD"
    AMC = "AMC"
    WARRANTY = "WARRANTY"
    BILLING = "BILLING"
    DELIVERY = "DELIVERY"
    INSTALLATION = "INSTALLATION"
    QUALITY = "QUALITY"
    CUSTOMER_FEEDBACK = "CUSTOMER_FEEDBACK"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    MANUAL = "MANUAL"


class EscalationReason(str, enum.Enum):
    """Reason for escalation."""
    SLA_BREACH = "SLA_BREACH"
    REPEATED_COMPLAINT = "REPEATED_COMPLAINT"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    COMPLEX_ISSUE = "COMPLEX_ISSUE"
    VIP_CUSTOMER = "VIP_CUSTOMER"
    HIGH_VALUE = "HIGH_VALUE"
    LEGAL_THREAT = "LEGAL_THREAT"
    SOCIAL_MEDIA_COMPLAINT = "SOCIAL_MEDIA_COMPLAINT"
    REGULATORY_ISSUE = "REGULATORY_ISSUE"
    SAFETY_CONCERN = "SAFETY_CONCERN"
    PRODUCT_DEFECT = "PRODUCT_DEFECT"
    NO_RESPONSE = "NO_RESPONSE"
    UNRESOLVED = "UNRESOLVED"
    MANAGER_OVERRIDE = "MANAGER_OVERRIDE"
    AUTO_ESCALATION = "AUTO_ESCALATION"
    OTHER = "OTHER"


class NotificationChannel(str, enum.Enum):
    """Notification channel for escalations."""
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    IN_APP = "IN_APP"
    PUSH = "PUSH"


class EscalationMatrix(Base):
    """Escalation matrix configuration - defines escalation rules."""
    __tablename__ = "escalation_matrix"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Applicable to
    source_type: Mapped[EscalationSource] = mapped_column(SQLEnum(EscalationSource))
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL")
    )
    priority: Mapped[Optional[EscalationPriority]] = mapped_column(SQLEnum(EscalationPriority))
    region_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("regions.id", ondelete="SET NULL")
    )

    # Level configuration
    level: Mapped[EscalationLevel] = mapped_column(SQLEnum(EscalationLevel))

    # Time-based triggers (in minutes)
    trigger_after_minutes: Mapped[int] = mapped_column(Integer)  # Time after which to escalate
    response_sla_minutes: Mapped[int] = mapped_column(Integer)  # Expected response time
    resolution_sla_minutes: Mapped[int] = mapped_column(Integer)  # Expected resolution time

    # Who to notify/assign
    notify_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    notify_role_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="SET NULL")
    )
    assign_to_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    assign_to_role_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="SET NULL")
    )
    additional_notify_emails: Mapped[Optional[dict]] = mapped_column(JSON)  # List of emails

    # Notification settings
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSON)  # List of channels
    notification_template_id: Mapped[Optional[str]] = mapped_column(String(36))

    # Auto-actions
    auto_escalate: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_assign: Mapped[bool] = mapped_column(Boolean, default=False)
    require_acknowledgment: Mapped[bool] = mapped_column(Boolean, default=True)
    acknowledgment_sla_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    notify_user = relationship("User", foreign_keys=[notify_user_id], lazy="selectin")
    assign_to_user = relationship("User", foreign_keys=[assign_to_user_id], lazy="selectin")
    category = relationship("Category", lazy="selectin")
    region = relationship("Region", lazy="selectin")


class Escalation(Base):
    """Escalation record - tracks individual escalations."""
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4
    )
    escalation_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True
    )  # ESC-YYYYMMDD-XXXX

    # Source reference
    source_type: Mapped[EscalationSource] = mapped_column(SQLEnum(EscalationSource))
    source_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., SR number, Order number

    # Customer
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_phone: Mapped[str] = mapped_column(String(20))
    customer_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Escalation details
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    current_level: Mapped[EscalationLevel] = mapped_column(
        SQLEnum(EscalationLevel), default=EscalationLevel.L1
    )
    priority: Mapped[EscalationPriority] = mapped_column(
        SQLEnum(EscalationPriority), default=EscalationPriority.MEDIUM
    )
    reason: Mapped[EscalationReason] = mapped_column(SQLEnum(EscalationReason))
    reason_details: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[EscalationStatus] = mapped_column(
        SQLEnum(EscalationStatus), default=EscalationStatus.NEW, index=True
    )

    # Assignment
    assigned_to_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    assigned_by_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )

    # SLA tracking
    response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    first_response_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_response_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolution_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Acknowledgment
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged_by_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    acknowledgment_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_by_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolution_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Customer feedback on resolution
    customer_satisfied: Mapped[Optional[bool]] = mapped_column(Boolean)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    customer_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Reopening
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reopened_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reopen_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Matrix reference
    matrix_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("escalation_matrix.id", ondelete="SET NULL")
    )

    # Product/Category
    product_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="SET NULL")
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL")
    )

    # Region
    region_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("regions.id", ondelete="SET NULL")
    )

    # Dealer/Franchisee
    dealer_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("dealers.id", ondelete="SET NULL")
    )

    # Internal notes
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[dict]] = mapped_column(JSON)

    # Creator
    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    customer = relationship("Customer", lazy="selectin")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="selectin")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], lazy="selectin")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id], lazy="selectin")
    product = relationship("Product", lazy="selectin")
    category = relationship("Category", lazy="selectin")
    region = relationship("Region", lazy="selectin")
    history = relationship("EscalationHistory", back_populates="escalation", lazy="selectin")
    comments = relationship("EscalationComment", back_populates="escalation", lazy="selectin")


class EscalationHistory(Base):
    """Escalation level change history."""
    __tablename__ = "escalation_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4
    )
    escalation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("escalations.id", ondelete="CASCADE"), index=True
    )

    # Level change
    from_level: Mapped[Optional[EscalationLevel]] = mapped_column(SQLEnum(EscalationLevel))
    to_level: Mapped[EscalationLevel] = mapped_column(SQLEnum(EscalationLevel))

    # Status change
    from_status: Mapped[Optional[EscalationStatus]] = mapped_column(SQLEnum(EscalationStatus))
    to_status: Mapped[EscalationStatus] = mapped_column(SQLEnum(EscalationStatus))

    # Assignment change
    from_assignee_id: Mapped[Optional[str]] = mapped_column(String(36))
    to_assignee_id: Mapped[Optional[str]] = mapped_column(String(36))

    # Reason and notes
    action: Mapped[str] = mapped_column(String(50))  # ESCALATED, DE_ESCALATED, ASSIGNED, STATUS_CHANGE
    reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Auto or manual
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_type: Mapped[Optional[str]] = mapped_column(String(50))  # SLA_BREACH, MANUAL, RULE

    # Who made the change
    changed_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT")
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    escalation = relationship("Escalation", back_populates="history")
    changed_by = relationship("User", lazy="selectin")


class EscalationComment(Base):
    """Comments/updates on escalation."""
    __tablename__ = "escalation_comments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4
    )
    escalation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("escalations.id", ondelete="CASCADE"), index=True
    )

    # Comment details
    comment: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)  # Internal or visible to customer
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System-generated

    # Attachments
    attachments: Mapped[Optional[dict]] = mapped_column(JSON)  # List of attachment URLs

    # Created by
    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    escalation = relationship("Escalation", back_populates="comments")
    created_by = relationship("User", lazy="selectin")


class EscalationNotification(Base):
    """Notification records for escalations."""
    __tablename__ = "escalation_notifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4
    )
    escalation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("escalations.id", ondelete="CASCADE"), index=True
    )

    # Notification details
    channel: Mapped[NotificationChannel] = mapped_column(SQLEnum(NotificationChannel))
    recipient_type: Mapped[str] = mapped_column(String(20))  # USER, CUSTOMER, EXTERNAL
    recipient_id: Mapped[Optional[str]] = mapped_column(String(36))
    recipient_email: Mapped[Optional[str]] = mapped_column(String(255))
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)

    # Status
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Retry
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    escalation = relationship("Escalation", lazy="selectin")


class SLAConfiguration(Base):
    """SLA configuration for different scenarios."""
    __tablename__ = "sla_configurations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Applicable to
    source_type: Mapped[EscalationSource] = mapped_column(SQLEnum(EscalationSource))
    priority: Mapped[EscalationPriority] = mapped_column(SQLEnum(EscalationPriority))
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL")
    )

    # SLA times (in minutes)
    response_time_minutes: Mapped[int] = mapped_column(Integer)
    resolution_time_minutes: Mapped[int] = mapped_column(Integer)

    # Business hours only
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True)
    business_start_hour: Mapped[int] = mapped_column(Integer, default=9)  # 9 AM
    business_end_hour: Mapped[int] = mapped_column(Integer, default=18)  # 6 PM
    exclude_weekends: Mapped[bool] = mapped_column(Boolean, default=True)
    exclude_holidays: Mapped[bool] = mapped_column(Boolean, default=True)

    # Penalty/Impact
    penalty_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    impact_score: Mapped[int] = mapped_column(Integer, default=1)  # 1-10

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
