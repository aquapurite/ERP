"""
Community Partner API Endpoints

Endpoints for the Meesho-style Community Sales Channel:
- Partner registration (public)
- KYC submission
- Profile management
- Commission tracking
- Payout requests
- Admin management
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.partner_service import PartnerService
from app.schemas.community_partner import (
    CommunityPartnerCreate,
    CommunityPartnerUpdate,
    CommunityPartnerResponse,
    CommunityPartnerList,
    KYCSubmission,
    KYCVerification,
    PartnerTierResponse,
    PartnerCommissionResponse,
    CommissionSummary,
    PayoutRequest,
    PartnerPayoutResponse,
    PayoutList,
    ReferralSummary,
    PartnerOrderResponse,
    PartnerOrderList,
    PartnerDashboard,
    PartnerAnalytics,
)


router = APIRouter(prefix="/partners", tags=["Community Partners"])


# ============================================================================
# Public Endpoints (Partner App)
# ============================================================================

@router.post("/register", response_model=CommunityPartnerResponse, status_code=status.HTTP_201_CREATED)
async def register_partner(
    data: CommunityPartnerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new community partner.

    Public endpoint - no authentication required.

    Steps:
    1. Submit basic details (name, phone, email, address)
    2. Optionally provide referral code
    3. System generates partner code and referral code
    4. Partner starts in PENDING_KYC status
    """
    service = PartnerService(db)
    try:
        partner = await service.register_partner(data)
        return partner
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login/otp")
async def send_login_otp(
    phone: str = Query(..., pattern=r"^\+?[1-9]\d{9,14}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Send OTP for partner login.
    Returns success if partner exists.
    """
    service = PartnerService(db)
    partner = await service.get_partner_by_phone(phone)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found. Please register first.")

    # TODO: Integrate with SMS gateway to send OTP
    # For now, return success
    return {
        "message": "OTP sent successfully",
        "phone": phone,
        "partner_code": partner.partner_code
    }


@router.post("/login/verify")
async def verify_login_otp(
    phone: str = Query(...),
    otp: str = Query(..., min_length=4, max_length=6),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and return partner session.
    """
    service = PartnerService(db)
    partner = await service.get_partner_by_phone(phone)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    # TODO: Verify OTP with SMS gateway
    # For demo, accept any 4-6 digit OTP
    if len(otp) < 4:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Return partner details (in production, return JWT token)
    return {
        "partner_id": str(partner.id),
        "partner_code": partner.partner_code,
        "name": partner.full_name,
        "status": partner.status,
        "kyc_status": partner.kyc_status,
        # "token": generate_jwt_token(partner)  # TODO
    }


# ============================================================================
# Partner Profile Endpoints (Authenticated)
# ============================================================================

@router.get("/me", response_model=CommunityPartnerResponse)
async def get_my_profile(
    partner_id: UUID = Query(..., description="Partner ID from login"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current partner's profile.
    """
    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    return partner


@router.put("/me", response_model=CommunityPartnerResponse)
async def update_my_profile(
    partner_id: UUID,
    data: CommunityPartnerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update current partner's profile.
    """
    service = PartnerService(db)
    try:
        partner = await service.update_partner(partner_id, data)
        return partner
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/kyc", response_model=CommunityPartnerResponse)
async def submit_kyc(
    partner_id: UUID,
    data: KYCSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit KYC documents for verification.

    Required documents:
    - Aadhaar (front and back images)
    - Bank account details
    - PAN card (optional but recommended)
    - Selfie (optional)
    """
    service = PartnerService(db)
    try:
        partner = await service.submit_kyc(partner_id, data)
        return partner
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Commission & Earnings Endpoints
# ============================================================================

@router.get("/me/commissions", response_model=CommissionSummary)
async def get_my_commission_summary(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get commission summary for current partner.
    """
    service = PartnerService(db)
    summary = await service.get_commission_summary(partner_id)
    return summary


@router.get("/me/commission-history")
async def get_commission_history(
    partner_id: UUID,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get commission transaction history.
    """
    from sqlalchemy import select
    from app.models.community_partner import PartnerCommission

    query = select(PartnerCommission).where(PartnerCommission.partner_id == partner_id)

    if status:
        query = query.where(PartnerCommission.status == status)

    query = query.order_by(PartnerCommission.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    commissions = result.scalars().all()

    return {
        "items": [PartnerCommissionResponse.model_validate(c) for c in commissions],
        "page": page,
        "page_size": page_size,
    }


# ============================================================================
# Payout Endpoints
# ============================================================================

@router.post("/me/payouts", response_model=PartnerPayoutResponse)
async def request_payout(
    partner_id: UUID,
    request: PayoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request payout for approved commissions.
    """
    service = PartnerService(db)
    try:
        payout = await service.create_payout(partner_id, request)
        return payout
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me/payouts")
async def get_my_payouts(
    partner_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payout history.
    """
    from sqlalchemy import select
    from app.models.community_partner import PartnerPayout

    query = select(PartnerPayout).where(PartnerPayout.partner_id == partner_id)
    query = query.order_by(PartnerPayout.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    payouts = result.scalars().all()

    return {
        "items": [PartnerPayoutResponse.model_validate(p) for p in payouts],
        "page": page,
        "page_size": page_size,
    }


# ============================================================================
# Tier & Progress Endpoints
# ============================================================================

@router.get("/me/tier-progress")
async def get_tier_progress(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress towards next tier.
    """
    service = PartnerService(db)
    progress = await service.get_tier_progress(partner_id)
    return progress


@router.get("/tiers", response_model=list[PartnerTierResponse])
async def get_all_tiers(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all partner tiers with benefits.
    """
    from sqlalchemy import select
    from app.models.community_partner import PartnerTier

    result = await db.execute(
        select(PartnerTier)
        .where(PartnerTier.is_active == True)
        .order_by(PartnerTier.commission_rate.asc())
    )
    tiers = result.scalars().all()
    return tiers


# ============================================================================
# Referral Endpoints
# ============================================================================

@router.get("/me/referrals")
async def get_my_referrals(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get referral summary and list of referred partners.
    """
    from sqlalchemy import select, func
    from app.models.community_partner import PartnerReferral, CommunityPartner

    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    # Get referrals
    referrals_result = await db.execute(
        select(PartnerReferral, CommunityPartner)
        .join(CommunityPartner, CommunityPartner.id == PartnerReferral.referred_id)
        .where(PartnerReferral.referrer_id == partner_id)
        .order_by(PartnerReferral.created_at.desc())
    )
    referrals = referrals_result.fetchall()

    # Count qualified
    qualified_count = sum(1 for r in referrals if r[0].is_qualified)

    # Total bonus earned
    total_bonus = sum(r[0].referral_bonus for r in referrals)

    return {
        "referral_code": partner.referral_code,
        "total_referrals": len(referrals),
        "qualified_referrals": qualified_count,
        "pending_referrals": len(referrals) - qualified_count,
        "total_bonus_earned": float(total_bonus),
        "referrals": [
            {
                "name": r[1].full_name,
                "registered_at": r[0].created_at,
                "is_qualified": r[0].is_qualified,
                "qualified_at": r[0].qualified_at,
                "bonus": float(r[0].referral_bonus),
            }
            for r in referrals
        ]
    }


# ============================================================================
# Orders Endpoints
# ============================================================================

@router.get("/me/orders")
async def get_my_orders(
    partner_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get orders attributed to this partner.
    """
    from sqlalchemy import select
    from app.models.community_partner import PartnerOrder
    from app.models.order import Order

    query = (
        select(PartnerOrder, Order)
        .join(Order, Order.id == PartnerOrder.order_id)
        .where(PartnerOrder.partner_id == partner_id)
        .order_by(PartnerOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    orders = result.fetchall()

    return {
        "items": [
            {
                "id": str(po.id),
                "order_id": str(po.order_id),
                "order_number": o.order_number,
                "order_amount": float(po.order_amount),
                "commission_amount": float(po.commission_amount) if po.commission_id else 0,
                "customer_name": o.customer_name,
                "order_status": o.status,
                "created_at": po.created_at,
            }
            for po, o in orders
        ],
        "page": page,
        "page_size": page_size,
    }


# ============================================================================
# Dashboard Endpoint
# ============================================================================

@router.get("/me/dashboard")
async def get_partner_dashboard(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete dashboard data for partner mobile app.
    """
    service = PartnerService(db)

    partner = await service.get_partner_by_id(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    commission_summary = await service.get_commission_summary(partner_id)
    tier_progress = await service.get_tier_progress(partner_id)

    # Recent orders (last 5)
    from sqlalchemy import select
    from app.models.community_partner import PartnerOrder
    from app.models.order import Order

    orders_result = await db.execute(
        select(PartnerOrder, Order)
        .join(Order, Order.id == PartnerOrder.order_id)
        .where(PartnerOrder.partner_id == partner_id)
        .order_by(PartnerOrder.created_at.desc())
        .limit(5)
    )
    recent_orders = [
        {
            "order_id": str(po.order_id),
            "order_number": o.order_number,
            "amount": float(po.order_amount),
            "status": o.status,
            "date": po.created_at.isoformat(),
        }
        for po, o in orders_result.fetchall()
    ]

    return {
        "partner": CommunityPartnerResponse.model_validate(partner),
        "commission_summary": commission_summary,
        "tier_progress": tier_progress,
        "recent_orders": recent_orders,
        "referral_code": partner.referral_code,
    }


# ============================================================================
# Admin Endpoints (ERP Users)
# ============================================================================

@router.get("", response_model=CommunityPartnerList)
async def list_partners(
    status: Optional[str] = Query(None, description="Filter by status"),
    kyc_status: Optional[str] = Query(None, description="Filter by KYC status"),
    state: Optional[str] = Query(None, description="Filter by state"),
    search: Optional[str] = Query(None, description="Search by name, phone, code, email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all partners with filters (Admin only).
    """
    service = PartnerService(db)
    partners, total = await service.list_partners(
        status=status,
        kyc_status=kyc_status,
        state=state,
        search=search,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return CommunityPartnerList(
        items=[CommunityPartnerResponse.model_validate(p) for p in partners],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{partner_id}", response_model=CommunityPartnerResponse)
async def get_partner(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get partner details by ID (Admin only).
    """
    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    return partner


@router.post("/{partner_id}/verify-kyc", response_model=CommunityPartnerResponse)
async def verify_partner_kyc(
    partner_id: UUID,
    verification: KYCVerification,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify or reject partner KYC (Admin only).
    """
    service = PartnerService(db)
    try:
        partner = await service.verify_kyc(partner_id, verification, current_user.id)
        return partner
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{partner_id}/suspend", response_model=CommunityPartnerResponse)
async def suspend_partner(
    partner_id: UUID,
    reason: str = Query(..., description="Reason for suspension"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Suspend a partner (Admin only).
    """
    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    partner.status = "SUSPENDED"
    partner.notes = f"Suspended by {current_user.email}: {reason}"

    await db.commit()
    await db.refresh(partner)

    return partner


@router.post("/{partner_id}/activate", response_model=CommunityPartnerResponse)
async def activate_partner(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reactivate a suspended partner (Admin only).
    """
    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    if partner.kyc_status != "VERIFIED":
        raise HTTPException(status_code=400, detail="Partner KYC is not verified")

    partner.status = "ACTIVE"
    from datetime import datetime, timezone
    partner.activated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(partner)

    return partner


@router.get("/analytics/summary", response_model=PartnerAnalytics)
async def get_partner_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overall partner program analytics (Admin only).
    """
    service = PartnerService(db)
    analytics = await service.get_partner_analytics()
    return analytics


# ============================================================================
# Commission Admin Endpoints
# ============================================================================

@router.get("/{partner_id}/commissions")
async def get_partner_commissions(
    partner_id: UUID,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get commission history for a partner (Admin only).
    """
    from sqlalchemy import select
    from app.models.community_partner import PartnerCommission

    query = select(PartnerCommission).where(PartnerCommission.partner_id == partner_id)

    if status:
        query = query.where(PartnerCommission.status == status)

    query = query.order_by(PartnerCommission.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    commissions = result.scalars().all()

    return {
        "items": [PartnerCommissionResponse.model_validate(c) for c in commissions],
        "page": page,
        "page_size": page_size,
    }


@router.post("/commissions/{commission_id}/approve")
async def approve_commission(
    commission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a pending commission (Admin only).
    """
    service = PartnerService(db)
    try:
        commission = await service.approve_commission(commission_id)
        return PartnerCommissionResponse.model_validate(commission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payouts/{payout_id}/process")
async def process_payout(
    payout_id: UUID,
    reference: str = Query(None, description="Bank transfer reference"),
    success: bool = Query(True, description="Whether transfer was successful"),
    failure_reason: str = Query(None, description="Reason for failure"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark payout as processed after bank transfer (Admin only).
    """
    service = PartnerService(db)
    try:
        payout = await service.process_payout(payout_id, reference, success, failure_reason)
        return PartnerPayoutResponse.model_validate(payout)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
