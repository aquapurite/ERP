"""
Call Center CRM Models.

This module contains models for:
- Call logging (inbound/outbound)
- Call dispositions
- Callback scheduling
- Call quality scoring
"""
import uuid
import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, Date, Time,
    ForeignKey, Numeric, Enum as SQLEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CallType(str, enum.Enum):
    """Type of call."""
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class CallCategory(str, enum.Enum):
    """Category of call."""
    INSTALLATION = "INSTALLATION"
    REINSTALLATION = "REINSTALLATION"
    BREAKDOWN = "BREAKDOWN"
    DEMO = "DEMO"
    DEALER_SUPPORT = "DEALER_SUPPORT"
    COMPLAINT = "COMPLAINT"
    INQUIRY = "INQUIRY"
    FEEDBACK = "FEEDBACK"
    AMC = "AMC"
    WARRANTY = "WARRANTY"
    SPARE_PARTS = "SPARE_PARTS"
    BILLING = "BILLING"
    GENERAL = "GENERAL"
    SALES = "SALES"
    FOLLOW_UP = "FOLLOW_UP"
    CAMPAIGN = "CAMPAIGN"


class CallStatus(str, enum.Enum):
    """Status of call."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    TRANSFERRED = "TRANSFERRED"
    VOICEMAIL = "VOICEMAIL"


class CallOutcome(str, enum.Enum):
    """Outcome of the call."""
    RESOLVED = "RESOLVED"
    TICKET_CREATED = "TICKET_CREATED"
    LEAD_CREATED = "LEAD_CREATED"
    CALLBACK_SCHEDULED = "CALLBACK_SCHEDULED"
    ESCALATED = "ESCALATED"
    TRANSFERRED = "TRANSFERRED"
    NO_ACTION = "NO_ACTION"
    CUSTOMER_NOT_AVAILABLE = "CUSTOMER_NOT_AVAILABLE"
    WRONG_NUMBER = "WRONG_NUMBER"
    NOT_INTERESTED = "NOT_INTERESTED"
    INFORMATION_PROVIDED = "INFORMATION_PROVIDED"


class CustomerSentiment(str, enum.Enum):
    """Customer sentiment during call."""
    VERY_POSITIVE = "VERY_POSITIVE"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    VERY_NEGATIVE = "VERY_NEGATIVE"


class CallPriority(str, enum.Enum):
    """Call priority level."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class CallbackStatus(str, enum.Enum):
    """Status of callback."""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"


class QAStatus(str, enum.Enum):
    """QA review status."""
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    DISPUTED = "DISPUTED"


class CallDisposition(Base):
    """
    Call disposition codes.
    Standardized outcomes for call categorization.
    """
    __tablename__ = "call_dispositions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Disposition Details
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[CallCategory] = mapped_column(
        SQLEnum(CallCategory),
        nullable=False
    )

    # Behavior Flags
    requires_callback: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_create_ticket: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_create_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_escalation: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolution: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Counts towards FCR"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

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
    calls: Mapped[List["Call"]] = relationship("Call", back_populates="disposition")


class Call(Base):
    """
    Call log for inbound and outbound calls.
    Central record for all customer interactions via phone.
    """
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Call Identification
    call_id: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Auto-generated: CALL-YYYYMMDD-XXXX"
    )

    # Call Type & Category
    call_type: Mapped[CallType] = mapped_column(
        SQLEnum(CallType),
        nullable=False
    )
    category: Mapped[CallCategory] = mapped_column(
        SQLEnum(CallCategory),
        nullable=False
    )
    sub_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Customer Information
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    customer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Agent Information
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Call Timing
    call_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    call_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Call duration in seconds"
    )
    hold_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    talk_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Call Status & Outcome
    status: Mapped[CallStatus] = mapped_column(
        SQLEnum(CallStatus),
        default=CallStatus.IN_PROGRESS,
        nullable=False
    )
    outcome: Mapped[Optional[CallOutcome]] = mapped_column(
        SQLEnum(CallOutcome),
        nullable=True
    )
    disposition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_dispositions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Priority & Sentiment
    priority: Mapped[CallPriority] = mapped_column(
        SQLEnum(CallPriority),
        default=CallPriority.NORMAL,
        nullable=False
    )
    sentiment: Mapped[Optional[CustomerSentiment]] = mapped_column(
        SQLEnum(CustomerSentiment),
        nullable=True
    )
    urgency_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="1-5 scale"
    )

    # Call Notes
    call_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    call_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes for internal teams"
    )

    # Linked Records
    linked_ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_requests.id", ondelete="SET NULL"),
        nullable=True,
        comment="Created or referenced service ticket"
    )
    linked_lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Created or referenced lead"
    )
    linked_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True
    )

    # Product Context
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True
    )
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Transfer Information
    transferred_from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    transferred_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    transfer_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    recording_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # FCR Tracking
    is_first_contact: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="First contact for this issue"
    )
    is_resolved_first_call: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Resolved in first call (FCR)"
    )
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Campaign (if outbound)
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Campaign for outbound calls"
    )

    # Compliance
    consent_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Customer consent confirmed"
    )
    disclosure_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Mandatory disclosures read"
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
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer",
        foreign_keys=[customer_id]
    )
    agent: Mapped["User"] = relationship(
        "User",
        foreign_keys=[agent_id]
    )
    disposition: Mapped[Optional["CallDisposition"]] = relationship(
        "CallDisposition",
        back_populates="calls"
    )
    linked_ticket: Mapped[Optional["ServiceRequest"]] = relationship(
        "ServiceRequest",
        foreign_keys=[linked_ticket_id]
    )
    linked_order: Mapped[Optional["Order"]] = relationship(
        "Order",
        foreign_keys=[linked_order_id]
    )
    product: Mapped[Optional["Product"]] = relationship("Product")
    callbacks: Mapped[List["CallbackSchedule"]] = relationship(
        "CallbackSchedule",
        back_populates="call"
    )
    qa_reviews: Mapped[List["CallQAReview"]] = relationship(
        "CallQAReview",
        back_populates="call"
    )

    @property
    def average_handle_time(self) -> int:
        """Calculate AHT (talk time + hold time)."""
        talk = self.talk_time_seconds or 0
        hold = self.hold_time_seconds or 0
        return talk + hold


class CallbackSchedule(Base):
    """
    Scheduled callbacks for follow-up.
    """
    __tablename__ = "callback_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Reference
    call_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original call if any"
    )

    # Customer
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Assignment
    assigned_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Scheduling
    scheduled_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True)
    scheduled_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    time_window_start: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True)
    time_window_end: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True)

    # Callback Details
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[CallCategory] = mapped_column(
        SQLEnum(CallCategory),
        nullable=False
    )
    priority: Mapped[CallPriority] = mapped_column(
        SQLEnum(CallPriority),
        default=CallPriority.NORMAL,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[CallbackStatus] = mapped_column(
        SQLEnum(CallbackStatus),
        default=CallbackStatus.SCHEDULED,
        nullable=False
    )

    # Completion
    completed_call_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Call that completed this callback"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Attempts
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Rescheduling
    rescheduled_from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("callback_schedules.id", ondelete="SET NULL"),
        nullable=True
    )
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)

    # Reminders
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

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
    call: Mapped[Optional["Call"]] = relationship(
        "Call",
        back_populates="callbacks",
        foreign_keys=[call_id]
    )
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    assigned_agent: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_agent_id]
    )
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id]
    )


class CallQAReview(Base):
    """
    Quality Assurance review for calls.
    """
    __tablename__ = "call_qa_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Call Reference
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Reviewer
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Scores (1-5 scale)
    greeting_score: Mapped[int] = mapped_column(Integer, nullable=False)
    communication_score: Mapped[int] = mapped_column(Integer, nullable=False)
    product_knowledge_score: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_solving_score: Mapped[int] = mapped_column(Integer, nullable=False)
    empathy_score: Mapped[int] = mapped_column(Integer, nullable=False)
    compliance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    closing_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Overall
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Average of all scores"
    )
    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
    max_points: Mapped[int] = mapped_column(Integer, default=35)

    # Feedback
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    areas_for_improvement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[QAStatus] = mapped_column(
        SQLEnum(QAStatus),
        default=QAStatus.PENDING,
        nullable=False
    )

    # Agent Acknowledgment
    acknowledged_by_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    agent_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dispute
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    dispute_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dispute_resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dispute_resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
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
    call: Mapped["Call"] = relationship("Call", back_populates="qa_reviews")
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewer_id])


# Import for type hints
from app.models.customer import Customer
from app.models.user import User
from app.models.service_request import ServiceRequest
from app.models.order import Order
from app.models.product import Product
