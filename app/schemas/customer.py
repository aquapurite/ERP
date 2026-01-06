from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
import uuid

from app.models.customer import CustomerType, CustomerSource, AddressType


# ==================== ADDRESS SCHEMAS ====================

class AddressBase(BaseModel):
    """Base address schema."""
    address_type: AddressType = AddressType.HOME
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., max_length=10)
    country: str = Field(default="India", max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False


class AddressCreate(AddressBase):
    """Address creation schema."""
    pass


class AddressUpdate(BaseModel):
    """Address update schema."""
    address_type: Optional[AddressType] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AddressResponse(BaseModel):
    """Address response schema."""
    id: uuid.UUID
    address_type: AddressType
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool
    is_active: bool
    full_address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== CUSTOMER SCHEMAS ====================

class CustomerBase(BaseModel):
    """Base customer schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    source: CustomerSource = CustomerSource.WEBSITE
    company_name: Optional[str] = Field(None, max_length=200)
    gst_number: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    anniversary_date: Optional[date] = None
    region_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Customer creation schema."""
    addresses: Optional[List[AddressCreate]] = []


class CustomerUpdate(BaseModel):
    """Customer update schema."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    source: Optional[CustomerSource] = None
    company_name: Optional[str] = None
    gst_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary_date: Optional[date] = None
    region_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    """Customer response schema."""
    id: uuid.UUID
    customer_code: str
    first_name: str
    last_name: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    customer_type: CustomerType
    source: CustomerSource
    company_name: Optional[str] = None
    gst_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary_date: Optional[date] = None
    is_active: bool
    is_verified: bool
    notes: Optional[str] = None
    addresses: List[AddressResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerBrief(BaseModel):
    """Brief customer info."""
    id: uuid.UUID
    customer_code: str
    full_name: str
    phone: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Paginated customer list."""
    items: List[CustomerResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== CUSTOMER 360 SCHEMAS ====================

class Customer360OrderSummary(BaseModel):
    """Order summary for Customer 360."""
    id: uuid.UUID
    order_number: str
    status: str
    total_amount: float
    payment_status: Optional[str] = None
    items_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360OrderStatusHistory(BaseModel):
    """Order status history entry."""
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    changed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360ShipmentSummary(BaseModel):
    """Shipment summary for Customer 360."""
    id: uuid.UUID
    shipment_number: str
    order_number: Optional[str] = None
    status: str
    awb_number: Optional[str] = None
    transporter_name: Optional[str] = None
    delivered_to: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360ShipmentTracking(BaseModel):
    """Shipment tracking entry."""
    status: str
    location: Optional[str] = None
    city: Optional[str] = None
    remarks: Optional[str] = None
    event_time: datetime

    class Config:
        from_attributes = True


class Customer360InstallationSummary(BaseModel):
    """Installation summary for Customer 360."""
    id: uuid.UUID
    installation_number: str
    status: str
    product_name: Optional[str] = None
    installation_pincode: Optional[str] = None
    franchisee_name: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    customer_rating: Optional[int] = None
    warranty_end_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360ServiceRequestSummary(BaseModel):
    """Service request summary for Customer 360."""
    id: uuid.UUID
    ticket_number: str
    service_type: str
    status: str
    priority: Optional[str] = None
    title: str
    franchisee_name: Optional[str] = None
    technician_name: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    customer_rating: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360ServiceStatusHistory(BaseModel):
    """Service request status history entry."""
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    changed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360CallSummary(BaseModel):
    """Call summary for Customer 360."""
    id: uuid.UUID
    call_id: str
    call_type: str
    category: str
    status: str
    outcome: Optional[str] = None
    duration_seconds: Optional[int] = None
    agent_name: Optional[str] = None
    call_start_time: datetime
    sentiment: Optional[str] = None

    class Config:
        from_attributes = True


class Customer360PaymentSummary(BaseModel):
    """Payment summary for Customer 360."""
    id: uuid.UUID
    order_number: Optional[str] = None
    amount: float
    method: str
    status: str
    transaction_id: Optional[str] = None
    gateway: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Customer360AMCSummary(BaseModel):
    """AMC contract summary for Customer 360."""
    id: uuid.UUID
    contract_number: str
    plan_name: str
    status: str
    start_date: date
    end_date: date
    total_services: int
    services_used: int
    services_remaining: int
    next_service_due: Optional[date] = None

    class Config:
        from_attributes = True


class Customer360LeadSummary(BaseModel):
    """Lead summary (if converted from lead)."""
    id: uuid.UUID
    lead_number: str
    status: str
    source: str
    converted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Customer360LeadActivity(BaseModel):
    """Lead activity entry."""
    activity_type: str
    subject: str
    outcome: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    activity_date: datetime

    class Config:
        from_attributes = True


class Customer360Stats(BaseModel):
    """Customer statistics summary."""
    total_orders: int = 0
    total_order_value: float = 0.0
    delivered_orders: int = 0
    pending_orders: int = 0
    total_installations: int = 0
    completed_installations: int = 0
    total_service_requests: int = 0
    open_service_requests: int = 0
    total_calls: int = 0
    active_amc_contracts: int = 0
    average_rating: Optional[float] = None
    customer_since_days: int = 0


class Customer360Timeline(BaseModel):
    """Timeline event for customer journey."""
    event_type: str  # ORDER, SHIPMENT, INSTALLATION, SERVICE, CALL, PAYMENT
    event_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    timestamp: datetime
    metadata: Optional[dict] = None


class Customer360Response(BaseModel):
    """
    Complete Customer 360 view with all journey data.
    """
    # Customer Profile
    customer: CustomerResponse

    # Statistics Summary
    stats: Customer360Stats

    # Journey Timeline (chronological events)
    timeline: List[Customer360Timeline] = []

    # Orders
    orders: List[Customer360OrderSummary] = []
    recent_order_history: List[Customer360OrderStatusHistory] = []

    # Shipments
    shipments: List[Customer360ShipmentSummary] = []
    recent_shipment_tracking: List[Customer360ShipmentTracking] = []

    # Installations
    installations: List[Customer360InstallationSummary] = []

    # Service Requests
    service_requests: List[Customer360ServiceRequestSummary] = []
    recent_service_history: List[Customer360ServiceStatusHistory] = []

    # Calls
    calls: List[Customer360CallSummary] = []

    # Payments
    payments: List[Customer360PaymentSummary] = []

    # AMC Contracts
    amc_contracts: List[Customer360AMCSummary] = []

    # Lead Info (if converted from lead)
    lead: Optional[Customer360LeadSummary] = None
    lead_activities: List[Customer360LeadActivity] = []

    class Config:
        from_attributes = True
