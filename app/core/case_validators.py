"""
Case Sensitivity Validators for Pydantic Schemas.

All enum-like string values in the database are stored in UPPERCASE.
These validators ensure case-insensitive input acceptance while
maintaining UPPERCASE storage convention.

Usage in Pydantic schemas:
    from app.core.case_validators import create_uppercase_validator

    class MySchema(BaseModel):
        status: StatusType

        _normalize_status = create_uppercase_validator('status', VALID_STATUSES)
"""
from typing import Set, Optional, Callable, Any


def normalize_to_uppercase(value: Any, valid_values: Set[str]) -> Any:
    """
    Normalize a string value to UPPERCASE if it's a valid enum value.

    Args:
        value: The input value (may be any type)
        valid_values: Set of valid UPPERCASE values

    Returns:
        UPPERCASE string if valid, original value otherwise (for Pydantic to handle)
    """
    if value is None:
        return value
    if isinstance(value, str):
        upper_v = value.upper()
        if upper_v in valid_values:
            return upper_v
    return value


def create_uppercase_validator(field_name: str, valid_values: Set[str]) -> classmethod:
    """
    Create a Pydantic field_validator that normalizes values to UPPERCASE.

    Usage:
        class MySchema(BaseModel):
            status: StatusType

            _normalize_status = create_uppercase_validator('status', {'ACTIVE', 'INACTIVE'})

    Args:
        field_name: Name of the field to validate
        valid_values: Set of valid UPPERCASE values

    Returns:
        A classmethod decorator that can be assigned to the schema
    """
    from pydantic import field_validator

    @field_validator(field_name, mode='before')
    @classmethod
    def validate(cls, v):
        return normalize_to_uppercase(v, valid_values)

    return validate


# =============================================================================
# Pre-defined valid value sets for common enums
# =============================================================================

# Role hierarchy
VALID_ROLE_LEVELS = {
    "SUPER_ADMIN", "DIRECTOR", "HEAD", "MANAGER", "EXECUTIVE"
}

# Order management
VALID_ORDER_STATUSES = {
    "NEW", "PENDING_PAYMENT", "CONFIRMED", "ALLOCATED", "PICKLIST_CREATED",
    "PICKING", "PACKED", "READY_TO_SHIP", "SHIPPED", "IN_TRANSIT",
    "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED", "RETURNED", "REFUNDED"
}

VALID_PAYMENT_STATUSES = {
    "PENDING", "AUTHORIZED", "CAPTURED", "PAID", "PARTIALLY_PAID",
    "REFUNDED", "PARTIALLY_REFUNDED", "CANCELLED", "FAILED"
}

VALID_PAYMENT_METHODS = {
    "CASH", "CARD", "UPI", "NET_BANKING", "WALLET", "EMI", "COD", "CHEQUE"
}

VALID_ORDER_SOURCES = {
    "WEBSITE", "MOBILE_APP", "STORE", "PHONE", "DEALER",
    "AMAZON", "FLIPKART", "OTHER"
}

# Company
VALID_COMPANY_TYPES = {
    "PRIVATE_LIMITED", "PUBLIC_LIMITED", "LLP", "PARTNERSHIP",
    "PROPRIETORSHIP", "OPC", "TRUST", "SOCIETY", "HUF", "GOVERNMENT"
}

VALID_GST_REGISTRATION_TYPES = {
    "REGULAR", "COMPOSITION", "CASUAL", "SEZ_UNIT", "SEZ_DEVELOPER",
    "ISD", "TDS_DEDUCTOR", "TCS_COLLECTOR", "NON_RESIDENT", "UNREGISTERED"
}

VALID_BANK_ACCOUNT_TYPES = {"CURRENT", "SAVINGS", "OD", "CC"}

# Dealer
VALID_DEALER_TYPES = {
    "DISTRIBUTOR", "DEALER", "SUB_DEALER", "RETAILER",
    "FRANCHISE", "MODERN_TRADE", "INSTITUTIONAL", "GOVERNMENT"
}

VALID_DEALER_STATUSES = {
    "PENDING_APPROVAL", "ACTIVE", "INACTIVE", "SUSPENDED",
    "BLACKLISTED", "TERMINATED"
}

VALID_DEALER_TIERS = {"PLATINUM", "GOLD", "SILVER", "BRONZE", "STANDARD"}

# Vendor
VALID_VENDOR_TYPES = {
    "MANUFACTURER", "IMPORTER", "DISTRIBUTOR", "TRADING",
    "SERVICE_PROVIDER", "CONTRACTOR", "TRANSPORTER", "OTHER"
}

VALID_VENDOR_STATUSES = {"ACTIVE", "INACTIVE", "PENDING_APPROVAL", "BLACKLISTED"}

# Shipment
VALID_SHIPMENT_STATUSES = {
    "CREATED", "PACKED", "READY_FOR_PICKUP", "PICKED_UP", "IN_TRANSIT",
    "OUT_FOR_DELIVERY", "DELIVERED", "FAILED_DELIVERY", "RTO_INITIATED",
    "RTO_IN_TRANSIT", "RTO_DELIVERED", "CANCELLED", "LOST"
}

VALID_PACKAGING_TYPES = {"BOX", "ENVELOPE", "POLY_BAG", "PALLET", "CUSTOM"}

# Purchase
VALID_PO_STATUSES = {
    "DRAFT", "PENDING_APPROVAL", "APPROVED", "SENT_TO_VENDOR",
    "ACKNOWLEDGED", "PARTIALLY_RECEIVED", "FULLY_RECEIVED", "CLOSED", "CANCELLED"
}

VALID_GRN_STATUSES = {
    "DRAFT", "PENDING_QC", "QC_PASSED", "QC_FAILED",
    "ACCEPTED", "REJECTED", "PUT_AWAY_COMPLETE"
}

# Service
VALID_SERVICE_STATUSES = {
    "OPEN", "ASSIGNED", "IN_PROGRESS", "ON_HOLD", "RESOLVED",
    "CLOSED", "CANCELLED", "ESCALATED"
}

VALID_INSTALLATION_STATUSES = {
    "PENDING", "SCHEDULED", "IN_PROGRESS", "COMPLETED",
    "FAILED", "CANCELLED", "RESCHEDULED"
}

# Lead/CRM
VALID_LEAD_STATUSES = {
    "NEW", "CONTACTED", "QUALIFIED", "PROPOSAL_SENT", "NEGOTIATION",
    "WON", "LOST", "DISQUALIFIED"
}

# Approval workflow
VALID_APPROVAL_STATUSES = {
    "PENDING", "APPROVED", "REJECTED", "RETURNED", "ESCALATED"
}

# Picklist
VALID_PICKLIST_STATUSES = {
    "PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED",
    "PARTIALLY_PICKED", "CANCELLED"
}

VALID_PICKLIST_TYPES = {"SINGLE_ORDER", "BATCH", "WAVE"}
