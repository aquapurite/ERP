"""
Pydantic schemas for Community Partner (Meesho-style sales channel).

This module defines request/response schemas for:
- Partner registration & KYC
- Commission tracking
- Payouts
- Referrals
- Training
- Order attribution
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Enums (for input validation - stored as VARCHAR in DB)
# ============================================================================

class PartnerStatus(str, Enum):
    """Partner account status"""
    PENDING_KYC = "PENDING_KYC"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_REJECTED = "KYC_REJECTED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"
    INACTIVE = "INACTIVE"


class KYCStatus(str, Enum):
    """KYC verification status"""
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class CommissionStatus(str, Enum):
    """Commission status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"


class PayoutStatus(str, Enum):
    """Payout status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PayoutMethod(str, Enum):
    """Payout method"""
    BANK_TRANSFER = "BANK_TRANSFER"
    UPI = "UPI"
    WALLET = "WALLET"


# ============================================================================
# Partner Tier Schemas
# ============================================================================

class PartnerTierBase(BaseModel):
    """Base schema for partner tiers"""
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    min_orders: int = Field(default=0, ge=0)
    min_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    commission_rate: Decimal = Field(..., ge=0, le=100, description="Commission % (0-100)")
    bonus_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    benefits: Optional[dict] = None
    is_active: bool = True


class PartnerTierCreate(PartnerTierBase):
    """Schema for creating a partner tier"""
    pass


class PartnerTierUpdate(BaseModel):
    """Schema for updating a partner tier"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    min_orders: Optional[int] = Field(None, ge=0)
    min_revenue: Optional[Decimal] = Field(None, ge=0)
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    bonus_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    benefits: Optional[dict] = None
    is_active: Optional[bool] = None


class PartnerTierResponse(PartnerTierBase):
    """Schema for partner tier response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Community Partner Schemas
# ============================================================================

class CommunityPartnerBase(BaseModel):
    """Base schema for community partner"""
    # Basic Info
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")
    email: Optional[str] = Field(None, max_length=255)
    whatsapp_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{9,14}$")

    # Address
    address_line1: Optional[str] = Field(None, max_length=500)
    address_line2: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")

    # Profile
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    language_preference: str = Field(default="hi", max_length=10)


class CommunityPartnerCreate(CommunityPartnerBase):
    """Schema for partner registration"""
    # KYC Documents (submitted during registration)
    aadhaar_number: Optional[str] = Field(None, pattern=r"^\d{12}$")
    pan_number: Optional[str] = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

    # Bank Details
    bank_account_number: Optional[str] = Field(None, max_length=20)
    bank_ifsc: Optional[str] = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    bank_account_name: Optional[str] = Field(None, max_length=200)
    bank_name: Optional[str] = Field(None, max_length=200)

    # Referral
    referral_code: Optional[str] = Field(None, max_length=20)

    @field_validator('aadhaar_number')
    @classmethod
    def validate_aadhaar(cls, v):
        if v and len(v) != 12:
            raise ValueError('Aadhaar number must be 12 digits')
        return v


class CommunityPartnerUpdate(BaseModel):
    """Schema for updating partner profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    whatsapp_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    profile_photo_url: Optional[str] = None
    language_preference: Optional[str] = None


class KYCSubmission(BaseModel):
    """Schema for KYC document submission"""
    aadhaar_number: str = Field(..., pattern=r"^\d{12}$")
    aadhaar_front_url: str
    aadhaar_back_url: str
    pan_number: Optional[str] = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    pan_card_url: Optional[str] = None
    selfie_url: Optional[str] = None

    # Bank Details
    bank_account_number: str = Field(..., max_length=20)
    bank_ifsc: str = Field(..., pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    bank_account_name: str = Field(..., max_length=200)
    bank_name: str = Field(..., max_length=200)
    cancelled_cheque_url: Optional[str] = None


class KYCVerification(BaseModel):
    """Schema for admin KYC verification"""
    kyc_status: KYCStatus
    kyc_rejection_reason: Optional[str] = None
    kyc_verified_by: Optional[UUID] = None


class CommunityPartnerResponse(CommunityPartnerBase):
    """Schema for partner response"""
    id: UUID
    partner_code: str
    status: str
    tier_id: Optional[UUID] = None

    # KYC Status
    kyc_status: str
    kyc_submitted_at: Optional[datetime] = None
    kyc_verified_at: Optional[datetime] = None
    kyc_rejection_reason: Optional[str] = None

    # Performance Metrics
    total_orders: int = 0
    total_sales: Decimal = Decimal("0")
    total_commission_earned: Decimal = Decimal("0")
    total_commission_paid: Decimal = Decimal("0")
    average_rating: Optional[Decimal] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime] = None

    # Related
    tier: Optional[PartnerTierResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CommunityPartnerList(BaseModel):
    """Schema for paginated partner list"""
    items: List[CommunityPartnerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Commission Schemas
# ============================================================================

class PartnerCommissionBase(BaseModel):
    """Base schema for partner commission"""
    order_id: UUID
    order_amount: Decimal = Field(..., ge=0)
    commission_rate: Decimal = Field(..., ge=0, le=100)
    commission_amount: Decimal = Field(..., ge=0)
    bonus_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tds_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tds_amount: Decimal = Field(default=Decimal("0"), ge=0)
    net_amount: Decimal = Field(..., ge=0)


class PartnerCommissionResponse(PartnerCommissionBase):
    """Schema for commission response"""
    id: UUID
    partner_id: UUID
    status: str
    payout_id: Optional[UUID] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CommissionSummary(BaseModel):
    """Schema for commission summary"""
    total_earned: Decimal = Decimal("0")
    pending_amount: Decimal = Decimal("0")
    paid_amount: Decimal = Decimal("0")
    tds_deducted: Decimal = Decimal("0")
    this_month_earned: Decimal = Decimal("0")


# ============================================================================
# Payout Schemas
# ============================================================================

class PartnerPayoutBase(BaseModel):
    """Base schema for partner payout"""
    payout_method: PayoutMethod = PayoutMethod.BANK_TRANSFER
    payout_details: Optional[dict] = None


class PayoutRequest(BaseModel):
    """Schema for requesting a payout"""
    amount: Optional[Decimal] = Field(None, gt=0, description="Amount to withdraw (None = all pending)")
    payout_method: PayoutMethod = PayoutMethod.BANK_TRANSFER


class PartnerPayoutResponse(BaseModel):
    """Schema for payout response"""
    id: UUID
    partner_id: UUID
    payout_number: str
    gross_amount: Decimal
    tds_amount: Decimal
    net_amount: Decimal
    status: str
    payout_method: str
    payout_reference: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PayoutList(BaseModel):
    """Schema for paginated payout list"""
    items: List[PartnerPayoutResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Referral Schemas
# ============================================================================

class PartnerReferralResponse(BaseModel):
    """Schema for referral response"""
    id: UUID
    referrer_id: UUID
    referred_id: UUID
    referral_code: str
    referral_bonus: Decimal
    is_qualified: bool
    qualified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReferralSummary(BaseModel):
    """Schema for referral summary"""
    total_referrals: int = 0
    qualified_referrals: int = 0
    pending_referrals: int = 0
    total_bonus_earned: Decimal = Decimal("0")
    referral_code: str


# ============================================================================
# Training Schemas
# ============================================================================

class PartnerTrainingBase(BaseModel):
    """Base schema for partner training"""
    training_name: str = Field(..., max_length=200)
    training_type: str = Field(..., max_length=50)
    description: Optional[str] = None
    video_url: Optional[str] = None
    document_url: Optional[str] = None
    is_mandatory: bool = False
    passing_score: Optional[int] = Field(None, ge=0, le=100)


class PartnerTrainingResponse(PartnerTrainingBase):
    """Schema for training response"""
    id: UUID
    partner_id: UUID
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    score: Optional[int] = None
    certificate_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingCompletion(BaseModel):
    """Schema for marking training as complete"""
    score: Optional[int] = Field(None, ge=0, le=100)


# ============================================================================
# Order Attribution Schemas
# ============================================================================

class PartnerOrderResponse(BaseModel):
    """Schema for partner order attribution"""
    id: UUID
    partner_id: UUID
    order_id: UUID
    order_number: str
    order_amount: Decimal
    commission_amount: Decimal
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PartnerOrderList(BaseModel):
    """Schema for paginated order list"""
    items: List[PartnerOrderResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Dashboard & Analytics Schemas
# ============================================================================

class PartnerDashboard(BaseModel):
    """Schema for partner mobile app dashboard"""
    partner: CommunityPartnerResponse
    commission_summary: CommissionSummary
    referral_summary: ReferralSummary
    recent_orders: List[PartnerOrderResponse]
    pending_training: List[PartnerTrainingResponse]
    tier_progress: dict  # Progress towards next tier


class PartnerAnalytics(BaseModel):
    """Schema for partner analytics"""
    total_partners: int = 0
    active_partners: int = 0
    pending_kyc: int = 0
    total_sales: Decimal = Decimal("0")
    total_commissions: Decimal = Decimal("0")
    this_month_sales: Decimal = Decimal("0")
    top_partners: List[dict] = []
    tier_distribution: dict = {}
    region_distribution: dict = {}
