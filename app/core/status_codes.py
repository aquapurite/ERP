"""
SINGLE SOURCE OF TRUTH for Status Values.

All status values used in the system MUST be defined here.
DO NOT hardcode status strings anywhere else in the codebase.

This file serves as:
1. Central registry of all valid status values
2. Documentation of allowed status transitions
3. Validation reference for API inputs
"""

from enum import Enum


class OrderStatus(str, Enum):
    """Order lifecycle status values."""
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    ALLOCATED = "ALLOCATED"
    PICKING = "PICKING"
    PACKED = "PACKED"
    READY_TO_SHIP = "READY_TO_SHIP"
    SHIPPED = "SHIPPED"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"
    REFUNDED = "REFUNDED"
    ON_HOLD = "ON_HOLD"

    @classmethod
    def active_statuses(cls) -> list:
        """Statuses that represent active orders."""
        return [cls.NEW, cls.CONFIRMED, cls.PROCESSING, cls.ALLOCATED,
                cls.PICKING, cls.PACKED, cls.READY_TO_SHIP, cls.SHIPPED,
                cls.IN_TRANSIT, cls.OUT_FOR_DELIVERY]

    @classmethod
    def completed_statuses(cls) -> list:
        """Statuses that represent completed orders."""
        return [cls.DELIVERED, cls.CANCELLED, cls.RETURNED, cls.REFUNDED]


class PaymentStatus(str, Enum):
    """Payment status values."""
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    CANCELLED = "CANCELLED"
    COD_PENDING = "COD_PENDING"


class InvoiceStatus(str, Enum):
    """Invoice/voucher status values."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    CANCELLED = "CANCELLED"
    VOID = "VOID"


class JournalStatus(str, Enum):
    """Journal entry status values."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status values."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT_TO_VENDOR = "SENT_TO_VENDOR"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class GRNStatus(str, Enum):
    """Goods Receipt Note status values."""
    DRAFT = "DRAFT"
    PENDING_QC = "PENDING_QC"
    QC_PASSED = "QC_PASSED"
    QC_FAILED = "QC_FAILED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    REJECTED = "REJECTED"


class ShipmentStatus(str, Enum):
    """Shipment status values."""
    CREATED = "CREATED"
    MANIFESTED = "MANIFESTED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED_DELIVERY = "FAILED_DELIVERY"
    RTO_INITIATED = "RTO_INITIATED"
    RTO_IN_TRANSIT = "RTO_IN_TRANSIT"
    RTO_DELIVERED = "RTO_DELIVERED"
    CANCELLED = "CANCELLED"


class ServiceRequestStatus(str, Enum):
    """Service request status values."""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_PARTS = "PENDING_PARTS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class ExpenseVoucherStatus(str, Enum):
    """Expense voucher workflow status values."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    PAID = "PAID"


class CapexRequestStatus(str, Enum):
    """CAPEX request workflow status values."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PO_CREATED = "PO_CREATED"
    RECEIVED = "RECEIVED"
    CAPITALIZED = "CAPITALIZED"


class PartnerStatus(str, Enum):
    """Partner/dealer status values."""
    PENDING_KYC = "PENDING_KYC"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_VERIFIED = "KYC_VERIFIED"
    KYC_REJECTED = "KYC_REJECTED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class CommissionStatus(str, Enum):
    """Commission status values."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


class PayoutStatus(str, Enum):
    """Payout status values."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StockReservationStatus(str, Enum):
    """Stock reservation status values."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class SyncStatus(str, Enum):
    """Data synchronization status values."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class TDSStatus(str, Enum):
    """TDS deduction status values."""
    PENDING = "PENDING"
    DEPOSITED = "DEPOSITED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"


class ApprovalLevel(str, Enum):
    """Approval level identifiers."""
    L1 = "L1"  # First level - typically manager
    L2 = "L2"  # Second level - typically senior manager/HOD
    L3 = "L3"  # Third level - typically director/MD


# ==================== VALIDATION HELPERS ====================

def is_valid_status(status: str, status_enum: type) -> bool:
    """Check if a status value is valid for a given enum."""
    try:
        status_enum(status)
        return True
    except ValueError:
        return False


def get_status_values(status_enum: type) -> list:
    """Get all valid values for a status enum."""
    return [s.value for s in status_enum]


# ==================== STATUS TRANSITIONS ====================

# Define allowed status transitions to enforce business rules
ORDER_STATUS_TRANSITIONS = {
    OrderStatus.NEW: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.ON_HOLD],
    OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED, OrderStatus.ON_HOLD],
    OrderStatus.PROCESSING: [OrderStatus.ALLOCATED, OrderStatus.CANCELLED, OrderStatus.ON_HOLD],
    OrderStatus.ALLOCATED: [OrderStatus.PICKING, OrderStatus.CANCELLED],
    OrderStatus.PICKING: [OrderStatus.PACKED, OrderStatus.CANCELLED],
    OrderStatus.PACKED: [OrderStatus.READY_TO_SHIP, OrderStatus.CANCELLED],
    OrderStatus.READY_TO_SHIP: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED: [OrderStatus.IN_TRANSIT, OrderStatus.DELIVERED, OrderStatus.RETURNED],
    OrderStatus.IN_TRANSIT: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED, OrderStatus.RETURNED],
    OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
    OrderStatus.DELIVERED: [OrderStatus.RETURNED],
    OrderStatus.ON_HOLD: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
}

INVOICE_STATUS_TRANSITIONS = {
    InvoiceStatus.DRAFT: [InvoiceStatus.PENDING_APPROVAL, InvoiceStatus.CANCELLED],
    InvoiceStatus.PENDING_APPROVAL: [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED],
    InvoiceStatus.APPROVED: [InvoiceStatus.POSTED],
    InvoiceStatus.REJECTED: [InvoiceStatus.DRAFT],
    InvoiceStatus.POSTED: [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.VOID],
    InvoiceStatus.PARTIALLY_PAID: [InvoiceStatus.PAID],
}


def can_transition(current_status: str, new_status: str, transitions: dict) -> bool:
    """Check if a status transition is allowed."""
    try:
        # Get enum type from transitions dict
        enum_type = type(list(transitions.keys())[0])
        current = enum_type(current_status)
        new = enum_type(new_status)
        return new in transitions.get(current, [])
    except (ValueError, KeyError):
        return False
