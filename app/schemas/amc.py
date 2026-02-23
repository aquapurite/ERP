"""AMC (Annual Maintenance Contract) schemas for API requests/responses."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
import uuid

from app.models.amc import AMCType, AMCStatus, ContractType, SalesChannel, SoldByType
from app.schemas.customer import CustomerBrief
from app.schemas.base import BaseResponseSchema


# ==================== NESTED SCHEMAS ====================

class PlanFeature(BaseModel):
    """A feature included in an AMC plan."""
    name: str
    quantity: int = 1
    frequency: str = "yearly"  # yearly, half_yearly, quarterly, per_visit


class PlanPart(BaseModel):
    """A part covered/not-covered in an AMC plan."""
    part_name: str
    part_id: Optional[uuid.UUID] = None
    covered: bool = True


class TenureOption(BaseModel):
    """Multi-year tenure pricing option."""
    months: int = 12
    price: float
    discount_pct: float = 0  # Percentage discount for multi-year


# ==================== AMC CONTRACT SCHEMAS ====================

class AMCContractCreate(BaseModel):
    """AMC contract creation schema."""
    amc_type: AMCType = AMCType.STANDARD
    contract_type: str = "COMPREHENSIVE"  # COMPREHENSIVE or NON_COMPREHENSIVE
    customer_id: uuid.UUID
    customer_address_id: Optional[uuid.UUID] = None
    product_id: uuid.UUID
    installation_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None  # If from a plan, auto-populate fields
    serial_number: str = Field(
        ...,
        min_length=1,
        description="Serial number of the product. Required to link AMC to specific unit."
    )
    start_date: date
    duration_months: int = Field(12, ge=1, le=60)
    total_services: int = Field(2, ge=1, le=12)
    base_price: float = Field(..., ge=0)
    tax_amount: float = Field(0, ge=0)
    discount_amount: float = Field(0, ge=0)
    parts_covered: bool = False
    labor_covered: bool = True
    emergency_support: bool = False
    priority_service: bool = False
    discount_on_parts: float = Field(0, ge=0, le=100)
    terms_and_conditions: Optional[str] = None
    notes: Optional[str] = None

    # Sales channel tracking
    sales_channel: str = "OFFLINE"  # ONLINE, OFFLINE, DEALER, TECHNICIAN
    sold_by_id: Optional[uuid.UUID] = None
    sold_by_type: Optional[str] = None  # USER, DEALER, TECHNICIAN


class AMCContractUpdate(BaseModel):
    """AMC contract update schema."""
    customer_address_id: Optional[uuid.UUID] = None
    total_services: Optional[int] = None
    parts_covered: Optional[bool] = None
    labor_covered: Optional[bool] = None
    emergency_support: Optional[bool] = None
    priority_service: Optional[bool] = None
    discount_on_parts: Optional[float] = None
    terms_and_conditions: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class AMCPayment(BaseModel):
    """AMC payment data."""
    payment_mode: str
    payment_reference: Optional[str] = None


class AMCServiceSchedule(BaseModel):
    """AMC service scheduling."""
    scheduled_date: date
    notes: Optional[str] = None


class AMCInspectionRequest(BaseModel):
    """Request inspection for lapsed contract re-enrollment."""
    preferred_date: Optional[date] = None
    notes: Optional[str] = None


class AMCInspectionComplete(BaseModel):
    """Complete inspection for lapsed contract."""
    status: str  # COMPLETED or FAILED
    inspection_date: date
    notes: Optional[str] = None


class AMCContractResponse(BaseResponseSchema):
    """AMC contract response schema."""
    id: uuid.UUID
    contract_number: str
    amc_type: str  # VARCHAR in DB
    contract_type: Optional[str] = "COMPREHENSIVE"
    status: str
    customer: CustomerBrief
    product_id: uuid.UUID
    plan_id: Optional[uuid.UUID] = None
    serial_number: str  # Required - links AMC to specific product unit
    start_date: date
    end_date: date
    duration_months: int
    total_services: int
    services_used: int
    services_remaining: int
    total_amount: float
    payment_status: str
    is_active: bool
    days_remaining: int
    next_service_due: Optional[date] = None

    # Sales channel
    sales_channel: Optional[str] = "OFFLINE"
    sold_by_type: Optional[str] = None

    # Grace & inspection
    grace_end_date: Optional[date] = None
    requires_inspection: bool = False
    inspection_status: Optional[str] = None

    # Commission
    commission_amount: Optional[float] = 0
    commission_paid: bool = False

    # Deferred revenue
    revenue_recognized: Optional[float] = 0
    revenue_pending: Optional[float] = 0

    created_at: datetime
    updated_at: datetime


class AMCContractDetail(AMCContractResponse):
    """Detailed AMC contract response."""
    installation_id: Optional[uuid.UUID] = None
    base_price: float
    tax_amount: float
    discount_amount: float
    payment_mode: Optional[str] = None
    payment_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    parts_covered: bool
    labor_covered: bool
    emergency_support: bool
    priority_service: bool
    discount_on_parts: float
    terms_and_conditions: Optional[str] = None
    is_renewable: bool
    renewal_reminder_sent: bool
    renewed_from_id: Optional[uuid.UUID] = None
    renewed_to_id: Optional[uuid.UUID] = None
    service_schedule: Optional[List[dict]] = None
    notes: Optional[str] = None
    product_name: Optional[str] = None
    plan_name: Optional[str] = None

    # Sales details
    sold_by_id: Optional[uuid.UUID] = None
    commission_rate: Optional[float] = 0

    # Inspection details
    inspection_date: Optional[date] = None
    inspection_notes: Optional[str] = None


class AMCContractListResponse(BaseModel):
    """Paginated AMC contract list."""
    items: List[AMCContractResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== AMC PLAN SCHEMAS ====================

class AMCPlanCreate(BaseModel):
    """AMC plan creation schema."""
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=20)
    amc_type: AMCType = AMCType.STANDARD
    contract_type: str = "COMPREHENSIVE"  # COMPREHENSIVE or NON_COMPREHENSIVE
    category_id: Optional[uuid.UUID] = None
    product_ids: Optional[List[uuid.UUID]] = None
    duration_months: int = 12
    base_price: float = Field(..., ge=0)
    tax_rate: float = Field(18, ge=0, le=100)
    services_included: int = Field(2, ge=1)
    parts_covered: bool = False
    labor_covered: bool = True
    emergency_support: bool = False
    priority_service: bool = False
    discount_on_parts: float = Field(0, ge=0, le=100)

    # New Phase 1 fields
    features_included: Optional[List[PlanFeature]] = None
    parts_included: Optional[List[PlanPart]] = None
    tenure_options: Optional[List[TenureOption]] = None
    response_sla_hours: int = Field(48, ge=1, description="Max hours for first response")
    resolution_sla_hours: int = Field(72, ge=1, description="Max hours for resolution")
    grace_period_days: int = Field(15, ge=0, le=90, description="Days after expiry for renewal without inspection")

    terms_and_conditions: Optional[str] = None
    description: Optional[str] = None


class AMCPlanUpdate(BaseModel):
    """AMC plan update schema."""
    name: Optional[str] = None
    contract_type: Optional[str] = None
    base_price: Optional[float] = None
    tax_rate: Optional[float] = None
    services_included: Optional[int] = None
    parts_covered: Optional[bool] = None
    labor_covered: Optional[bool] = None
    emergency_support: Optional[bool] = None
    priority_service: Optional[bool] = None
    discount_on_parts: Optional[float] = None
    features_included: Optional[List[PlanFeature]] = None
    parts_included: Optional[List[PlanPart]] = None
    tenure_options: Optional[List[TenureOption]] = None
    response_sla_hours: Optional[int] = None
    resolution_sla_hours: Optional[int] = None
    grace_period_days: Optional[int] = None
    terms_and_conditions: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class AMCPlanResponse(BaseResponseSchema):
    """AMC plan response schema."""
    id: uuid.UUID
    name: str
    code: str
    amc_type: str  # VARCHAR in DB
    contract_type: Optional[str] = "COMPREHENSIVE"
    category_id: Optional[uuid.UUID] = None
    duration_months: int
    base_price: float
    tax_rate: float
    services_included: int
    parts_covered: bool
    labor_covered: bool
    emergency_support: bool
    priority_service: bool
    discount_on_parts: float

    # New Phase 1 fields
    features_included: Optional[List[dict]] = None
    parts_included: Optional[List[dict]] = None
    tenure_options: Optional[List[dict]] = None
    response_sla_hours: int = 48
    resolution_sla_hours: int = 72
    grace_period_days: int = 15

    description: Optional[str] = None
    is_active: bool
    sort_order: int
    created_at: datetime


class AMCPlanListResponse(BaseModel):
    """Paginated AMC plan list."""
    items: List[AMCPlanResponse]
    total: int
    page: int
    size: int
    pages: int
