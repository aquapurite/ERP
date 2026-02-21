"""API endpoints for Dealer/Distributor management."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dealer import (
    Dealer, DealerType, DealerStatus, DealerTier, CreditStatus,
    DealerPricing, DealerTierPricing, DealerCreditLedger, TransactionType,
    DealerTarget, DealerScheme, SchemeType, DealerSchemeApplication,
)
from app.models.user import User
from app.schemas.dealer import (
    # Dealer
    DealerCreate, DealerUpdate, DealerResponse, DealerBrief, DealerListResponse,
    # Pricing
    DealerPricingCreate, DealerPricingResponse,
    DealerTierPricingCreate, DealerTierPricingResponse,
    # Credit Ledger
    DealerCreditLedgerCreate, DealerCreditLedgerResponse, DealerCreditLedgerListResponse,
    # Target
    DealerTargetCreate, DealerTargetUpdate, DealerTargetResponse,
    # Scheme
    DealerSchemeCreate, DealerSchemeResponse, DealerSchemeListResponse,
    DealerSchemeApplicationCreate, DealerSchemeApplicationResponse,
    # Reports
    DealerPerformanceResponse, DealerAgingResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from app.services.audit_service import AuditService
from app.models.approval import ApprovalEntityType, ApprovalRequest, ApprovalStatus

router = APIRouter()


# Prefix mapping for dealer types
DEALER_PREFIX_MAP = {
    DealerType.DISTRIBUTOR: "DST",
    DealerType.DEALER: "DLR",
    DealerType.SUB_DEALER: "SDL",
    DealerType.RETAILER: "RTL",
    DealerType.FRANCHISE: "FRN",
    DealerType.MODERN_TRADE: "MTR",
    DealerType.INSTITUTIONAL: "INS",
    DealerType.GOVERNMENT: "GOV",
}


async def get_next_dealer_code(db: AsyncSession, dealer_type: DealerType) -> str:
    """Generate next sequential dealer code for a given type (e.g., DLR001, DLR002)."""
    import re

    prefix = DEALER_PREFIX_MAP.get(dealer_type, "DLR")

    # Find existing codes with this prefix
    result = await db.execute(
        select(Dealer.dealer_code)
        .where(Dealer.dealer_code.like(f"{prefix}%"))
        .order_by(Dealer.dealer_code.desc())
    )
    existing_codes = [r[0] for r in result.fetchall()]

    # Extract the max number from existing codes
    max_num = 0
    pattern = re.compile(rf"^{prefix}(\d+)$")

    for code in existing_codes:
        match = pattern.match(code)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    # Generate next code
    next_num = max_num + 1
    return f"{prefix}{str(next_num).zfill(3)}"


# ==================== Next Code Endpoint ====================

@router.get("/next-code")
async def get_next_code(
    db: DB,
    dealer_type: DealerType = Query(..., description="Dealer type (DEALER, DISTRIBUTOR, etc.)"),
    current_user: User = Depends(get_current_user),
):
    """Get the next available dealer code for a given type."""
    next_code = await get_next_dealer_code(db, dealer_type)
    prefix = DEALER_PREFIX_MAP.get(dealer_type, "DLR")

    return {
        "next_code": next_code,
        "prefix": prefix,
        "dealer_type": dealer_type.value,
    }


# ==================== Dealer CRUD ====================

@router.post("", response_model=DealerResponse, status_code=status.HTTP_201_CREATED)
async def create_dealer(
    dealer_in: DealerCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new dealer/distributor."""
    # Check for duplicate GSTIN
    if dealer_in.gstin:
        existing = await db.execute(
            select(Dealer).where(Dealer.gstin == dealer_in.gstin)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Dealer with GSTIN {dealer_in.gstin} already exists"
            )

    # Generate dealer code using sequential numbering
    dealer_code = await get_next_dealer_code(db, dealer_in.dealer_type)

    dealer = Dealer(
        **dealer_in.model_dump(exclude={"opening_balance"}),
        dealer_code=dealer_code,
        outstanding_amount=dealer_in.opening_balance,
    )

    db.add(dealer)
    await db.commit()
    await db.refresh(dealer)

    # Create approval request for dealer onboarding
    from app.api.v1.endpoints.approvals import _create_approval_request
    await _create_approval_request(
        db=db,
        entity_type=ApprovalEntityType.DEALER_ONBOARDING,
        entity_id=dealer.id,
        entity_number=dealer.dealer_code,
        amount=dealer.credit_limit,
        title=f"Dealer Onboarding: {dealer.name} ({dealer.dealer_code})",
        requested_by=current_user.id,
        description=f"New {dealer.dealer_type} onboarding request",
        extra_info={
            "dealer_name": dealer.name,
            "dealer_type": dealer.dealer_type,
            "region": dealer.region,
            "contact_person": dealer.contact_person,
            "phone": dealer.phone,
            "credit_limit": float(dealer.credit_limit),
        },
    )
    await db.commit()

    # Create opening balance ledger entry
    if dealer_in.opening_balance != 0:
        ledger = DealerCreditLedger(
            dealer_id=dealer.id,
            transaction_type=TransactionType.OPENING_BALANCE,
            transaction_date=date.today(),
            reference_type="OPENING",
            reference_number=dealer_code,
            debit_amount=dealer_in.opening_balance if dealer_in.opening_balance > 0 else Decimal("0"),
            credit_amount=abs(dealer_in.opening_balance) if dealer_in.opening_balance < 0 else Decimal("0"),
            balance=dealer_in.opening_balance,
            remarks="Opening balance",
        )
        db.add(ledger)
        await db.commit()

    return dealer


@router.post("/backfill-approvals")
async def backfill_dealer_approvals(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """One-time: Create approval requests for existing PENDING_APPROVAL dealers that don't have one."""
    from app.api.v1.endpoints.approvals import _create_approval_request

    # Find PENDING_APPROVAL dealers without an approval request
    result = await db.execute(
        select(Dealer).where(Dealer.status == DealerStatus.PENDING_APPROVAL)
    )
    pending_dealers = result.scalars().all()

    created = []
    for dealer in pending_dealers:
        # Check if approval request already exists
        existing = await db.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.entity_type == ApprovalEntityType.DEALER_ONBOARDING,
                ApprovalRequest.entity_id == dealer.id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        await _create_approval_request(
            db=db,
            entity_type=ApprovalEntityType.DEALER_ONBOARDING,
            entity_id=dealer.id,
            entity_number=dealer.dealer_code,
            amount=dealer.credit_limit,
            title=f"Dealer Onboarding: {dealer.name} ({dealer.dealer_code})",
            requested_by=current_user.id,
            description=f"Existing {dealer.dealer_type} onboarding request (backfilled)",
            extra_info={
                "dealer_name": dealer.name,
                "dealer_type": dealer.dealer_type,
                "region": dealer.region,
                "contact_person": dealer.contact_person,
                "phone": dealer.phone,
                "credit_limit": float(dealer.credit_limit),
            },
        )
        created.append({"dealer_code": dealer.dealer_code, "name": dealer.name})

    await db.commit()
    return {"backfilled": len(created), "dealers": created}


@router.get("", response_model=DealerListResponse)
async def list_dealers(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    dealer_type: Optional[DealerType] = None,
    status: Optional[DealerStatus] = None,
    tier: Optional[DealerTier] = None,
    region: Optional[str] = None,
    city: Optional[str] = None,
    credit_status: Optional[CreditStatus] = None,
    current_user: User = Depends(get_current_user),
):
    """List dealers with filters."""
    skip = (page - 1) * size
    query = select(Dealer)
    count_query = select(func.count(Dealer.id))

    filters = []
    if search:
        filters.append(or_(
            Dealer.name.ilike(f"%{search}%"),
            Dealer.dealer_code.ilike(f"%{search}%"),
            Dealer.gstin.ilike(f"%{search}%"),
        ))
    if dealer_type:
        filters.append(Dealer.dealer_type == dealer_type)
    if status:
        filters.append(Dealer.status == status)
    if tier:
        filters.append(Dealer.tier == tier)
    if region:
        filters.append(Dealer.region == region)
    if city:
        filters.append(Dealer.registered_city.ilike(f"%{city}%"))
    if credit_status:
        filters.append(Dealer.credit_status == credit_status)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Dealer.created_at.desc()).offset(skip).limit(size)
    result = await db.execute(query)
    dealers = result.scalars().all()

    pages = (total + size - 1) // size if total > 0 else 1

    return DealerListResponse(
        items=[DealerResponse.model_validate(d) for d in dealers],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/dropdown", response_model=List[DealerBrief])
async def get_dealers_dropdown(
    db: DB,
    dealer_type: Optional[DealerType] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
):
    """Get dealers for dropdown selection."""
    query = select(Dealer)

    if active_only:
        query = query.where(Dealer.status == DealerStatus.ACTIVE)
    if dealer_type:
        query = query.where(Dealer.dealer_type == dealer_type)

    query = query.order_by(Dealer.name)
    result = await db.execute(query)
    dealers = result.scalars().all()

    return [DealerBrief.model_validate(d) for d in dealers]


@router.get("/{dealer_id}", response_model=DealerResponse)
async def get_dealer(
    dealer_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get dealer by ID."""
    result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    dealer = result.scalar_one_or_none()

    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    return dealer


@router.put("/{dealer_id}", response_model=DealerResponse)
async def update_dealer(
    dealer_id: UUID,
    dealer_in: DealerUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update dealer details."""
    result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    dealer = result.scalar_one_or_none()

    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    update_data = dealer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dealer, field, value)

    await db.commit()
    await db.refresh(dealer)

    return dealer


@router.delete("/{dealer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dealer(
    dealer_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete a dealer. Only PENDING_APPROVAL dealers can be deleted."""
    result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    dealer = result.scalar_one_or_none()

    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    if dealer.status not in (DealerStatus.PENDING_APPROVAL, DealerStatus.INACTIVE):
        raise HTTPException(
            status_code=400,
            detail="Only PENDING_APPROVAL or INACTIVE dealers can be deleted"
        )

    await db.delete(dealer)
    await db.commit()


@router.post("/{dealer_id}/approve", response_model=DealerResponse)
async def approve_dealer(
    dealer_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve a pending dealer."""
    result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    dealer = result.scalar_one_or_none()

    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    if dealer.status != DealerStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Dealer is not pending approval")

    dealer.status = DealerStatus.ACTIVE.value
    dealer.onboarded_at = datetime.now(timezone.utc)

    # Also update linked approval_request if one exists
    approval_result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.entity_type == ApprovalEntityType.DEALER_ONBOARDING,
            ApprovalRequest.entity_id == dealer_id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    linked_approval = approval_result.scalar_one_or_none()
    if linked_approval:
        linked_approval.status = ApprovalStatus.APPROVED.value
        linked_approval.approved_by = current_user.id
        linked_approval.approved_at = datetime.now(timezone.utc)
        linked_approval.approval_comments = "Approved directly from dealer management"

    # ORCHESTRATION: Send welcome email with brochure
    from app.services.dealer_orchestration_service import DealerOrchestrationService
    orchestration = DealerOrchestrationService(db)
    await orchestration.on_dealer_approved(dealer, current_user.id)

    await db.commit()
    await db.refresh(dealer)

    return dealer


# ==================== Dealer Pricing ====================

@router.get("/{dealer_id}/pricing", response_model=List[DealerPricingResponse])
async def get_dealer_pricing(
    dealer_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get special pricing for a dealer, including product details."""
    from app.models.product import Product
    result = await db.execute(
        select(DealerPricing)
        .options(selectinload(DealerPricing.product))
        .where(DealerPricing.dealer_id == dealer_id)
        .order_by(DealerPricing.created_at.desc())
    )
    pricing_list = result.scalars().all()

    items = []
    for p in pricing_list:
        item_dict = {
            "id": p.id,
            "dealer_id": p.dealer_id,
            "product_id": p.product_id,
            "variant_id": p.variant_id,
            "mrp": p.mrp,
            "dealer_price": p.dealer_price,
            "special_price": p.special_price,
            "margin_percentage": p.margin_percentage,
            "minimum_margin": p.minimum_margin,
            "moq": p.moq,
            "effective_from": p.effective_from,
            "effective_to": p.effective_to,
            "is_active": p.is_active,
            "dealer_margin": p.dealer_margin,
            "product_name": p.product.name if p.product else None,
            "product_sku": p.product.sku if p.product else None,
            "master_mrp": p.product.mrp if p.product else None,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        items.append(DealerPricingResponse.model_validate(item_dict))
    return items


@router.post("/{dealer_id}/pricing", response_model=DealerPricingResponse, status_code=status.HTTP_201_CREATED)
async def create_dealer_pricing(
    dealer_id: UUID,
    pricing_in: DealerPricingCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create special pricing for a dealer."""
    # Verify dealer
    dealer_result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    if not dealer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dealer not found")

    # Check for existing pricing
    existing = await db.execute(
        select(DealerPricing).where(
            and_(
                DealerPricing.dealer_id == dealer_id,
                DealerPricing.product_id == pricing_in.product_id,
                DealerPricing.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Active pricing already exists for this product"
        )

    # Exclude dealer_id from model_dump since it comes from URL path
    pricing_data = pricing_in.model_dump(exclude={"dealer_id"})
    pricing = DealerPricing(
        dealer_id=dealer_id,
        **pricing_data,
    )

    db.add(pricing)
    await db.commit()
    await db.refresh(pricing)

    return DealerPricingResponse.model_validate({
        "id": pricing.id,
        "dealer_id": pricing.dealer_id,
        "product_id": pricing.product_id,
        "variant_id": pricing.variant_id,
        "mrp": pricing.mrp,
        "dealer_price": pricing.dealer_price,
        "special_price": pricing.special_price,
        "margin_percentage": pricing.margin_percentage,
        "minimum_margin": pricing.minimum_margin,
        "moq": pricing.moq,
        "effective_from": pricing.effective_from,
        "effective_to": pricing.effective_to,
        "is_active": pricing.is_active,
        "dealer_margin": pricing.dealer_margin,
        "product_name": None,
        "product_sku": None,
        "master_mrp": None,
        "created_at": pricing.created_at,
        "updated_at": pricing.updated_at,
    })


@router.delete("/{dealer_id}/pricing/{pricing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dealer_pricing(
    dealer_id: UUID,
    pricing_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete (deactivate) dealer pricing."""
    result = await db.execute(
        select(DealerPricing).where(
            and_(
                DealerPricing.id == pricing_id,
                DealerPricing.dealer_id == dealer_id,
            )
        )
    )
    pricing = result.scalar_one_or_none()
    if not pricing:
        raise HTTPException(status_code=404, detail="Dealer pricing not found")

    pricing.is_active = False
    await db.commit()


# ==================== Tier Pricing ====================

@router.get("/tiers/pricing", response_model=List[DealerTierPricingResponse])
async def get_tier_pricing(
    db: DB,
    tier: Optional[str] = None,
    product_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Get tier-based pricing."""
    query = select(DealerTierPricing)

    if tier:
        query = query.where(DealerTierPricing.tier == tier)  # VARCHAR comparison
    if product_id:
        query = query.where(DealerTierPricing.product_id == product_id)

    query = query.order_by(DealerTierPricing.tier, DealerTierPricing.product_id)
    result = await db.execute(query)
    pricing = result.scalars().all()

    return [DealerTierPricingResponse.model_validate(p) for p in pricing]


@router.post("/tiers/pricing", response_model=DealerTierPricingResponse, status_code=status.HTTP_201_CREATED)
async def create_tier_pricing(
    pricing_in: DealerTierPricingCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create tier-based pricing."""
    # Check for existing
    existing = await db.execute(
        select(DealerTierPricing).where(
            and_(
                DealerTierPricing.tier == pricing_in.tier,
                DealerTierPricing.product_id == pricing_in.product_id,
                DealerTierPricing.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Active tier pricing already exists for this product"
        )

    pricing = DealerTierPricing(
        **pricing_in.model_dump(),
    )

    db.add(pricing)
    await db.commit()
    await db.refresh(pricing)

    return pricing


# ==================== Credit Ledger ====================

@router.get("/{dealer_id}/ledger", response_model=DealerCreditLedgerListResponse)
async def get_dealer_ledger(
    dealer_id: UUID,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """Get dealer credit ledger."""
    # Verify dealer
    dealer_result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    dealer = dealer_result.scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    query = select(DealerCreditLedger).where(DealerCreditLedger.dealer_id == dealer_id)
    count_query = select(func.count(DealerCreditLedger.id)).where(
        DealerCreditLedger.dealer_id == dealer_id
    )

    if start_date:
        query = query.where(DealerCreditLedger.transaction_date >= start_date)
        count_query = count_query.where(DealerCreditLedger.transaction_date >= start_date)
    if end_date:
        query = query.where(DealerCreditLedger.transaction_date <= end_date)
        count_query = count_query.where(DealerCreditLedger.transaction_date <= end_date)

    # Get totals
    totals_query = select(
        func.coalesce(func.sum(DealerCreditLedger.debit_amount), 0).label("total_debit"),
        func.coalesce(func.sum(DealerCreditLedger.credit_amount), 0).label("total_credit"),
    ).where(DealerCreditLedger.dealer_id == dealer_id)

    totals_result = await db.execute(totals_query)
    totals = totals_result.one()

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(
        DealerCreditLedger.transaction_date.desc(),
        DealerCreditLedger.created_at.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    entries = result.scalars().all()

    return DealerCreditLedgerListResponse(
        items=[DealerCreditLedgerResponse.model_validate(e) for e in entries],
        total=total,
        opening_balance=Decimal("0"),
        total_debit=totals.total_debit,
        total_credit=totals.total_credit,
        closing_balance=dealer.outstanding_amount,
    )


@router.post("/{dealer_id}/payment", response_model=DealerCreditLedgerResponse)
async def record_dealer_payment(
    dealer_id: UUID,
    payment_in: DealerCreditLedgerCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Record payment from dealer."""
    # Verify dealer
    dealer_result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    dealer = dealer_result.scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    new_balance = dealer.outstanding_amount - payment_in.credit_amount + payment_in.debit_amount

    ledger = DealerCreditLedger(
        dealer_id=dealer_id,
        transaction_type=payment_in.transaction_type,
        transaction_date=payment_in.transaction_date,
        reference_type=payment_in.reference_type,
        reference_number=payment_in.reference_number,
        reference_id=payment_in.reference_id,
        debit_amount=payment_in.debit_amount,
        credit_amount=payment_in.credit_amount,
        balance=new_balance,
        payment_mode=payment_in.payment_mode,
        transaction_reference=payment_in.transaction_reference,
        remarks=payment_in.remarks,
    )

    db.add(ledger)

    # Update dealer balance
    dealer.outstanding_amount = new_balance

    # Update credit status
    if new_balance > dealer.credit_limit:
        dealer.credit_status = CreditStatus.BLOCKED.value
    elif new_balance > dealer.credit_limit * Decimal("0.8"):
        dealer.credit_status = CreditStatus.ON_HOLD.value
    else:
        dealer.credit_status = CreditStatus.ACTIVE.value

    await db.commit()
    await db.refresh(ledger)

    return ledger


# ==================== Targets ====================

@router.get("/{dealer_id}/targets", response_model=List[DealerTargetResponse])
async def get_dealer_targets(
    dealer_id: UUID,
    db: DB,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """Get dealer targets."""
    query = select(DealerTarget).where(DealerTarget.dealer_id == dealer_id)

    if year:
        query = query.where(DealerTarget.year == year)

    query = query.order_by(DealerTarget.year.desc(), DealerTarget.month.desc())
    result = await db.execute(query)
    targets = result.scalars().all()

    return [DealerTargetResponse.model_validate(t) for t in targets]


@router.post("/{dealer_id}/targets", response_model=DealerTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_dealer_target(
    dealer_id: UUID,
    target_in: DealerTargetCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create/update dealer target for a month."""
    # Verify dealer
    dealer_result = await db.execute(
        select(Dealer).where(Dealer.id == dealer_id)
    )
    if not dealer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dealer not found")

    # Check for existing target
    existing = await db.execute(
        select(DealerTarget).where(
            and_(
                DealerTarget.dealer_id == dealer_id,
                DealerTarget.year == target_in.year,
                DealerTarget.month == target_in.month,
            )
        )
    )
    existing_target = existing.scalar_one_or_none()

    if existing_target:
        # Update existing
        existing_target.target_quantity = target_in.target_quantity
        existing_target.target_value = target_in.target_value
        existing_target.updated_by = current_user.id
        target = existing_target
    else:
        # Create new
        target = DealerTarget(
            dealer_id=dealer_id,
            **target_in.model_dump(),
            created_by=current_user.id,
        )
        db.add(target)

    await db.commit()
    await db.refresh(target)

    return target


# ==================== Schemes ====================

@router.get("/schemes", response_model=DealerSchemeListResponse)
async def list_dealer_schemes(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    scheme_type: Optional[SchemeType] = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
):
    """List dealer schemes."""
    query = select(DealerScheme)
    count_query = select(func.count(DealerScheme.id))

    filters = []
    if scheme_type:
        filters.append(DealerScheme.scheme_type == scheme_type)
    if is_active:
        today = date.today()
        filters.append(DealerScheme.is_active == True)
        filters.append(DealerScheme.start_date <= today)
        filters.append(DealerScheme.end_date >= today)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(DealerScheme.start_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    schemes = result.scalars().all()

    page = (skip // limit) + 1
    pages = (total + limit - 1) // limit if total > 0 else 1

    return DealerSchemeListResponse(
        items=[DealerSchemeResponse.model_validate(s) for s in schemes],
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.post("/schemes", response_model=DealerSchemeResponse, status_code=status.HTTP_201_CREATED)
async def create_dealer_scheme(
    scheme_in: DealerSchemeCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new dealer scheme."""
    # Generate scheme code
    count_result = await db.execute(select(func.count(DealerScheme.id)))
    count = count_result.scalar() or 0
    scheme_code = f"SCH-{date.today().strftime('%Y')}-{str(count + 1).zfill(4)}"

    scheme = DealerScheme(
        scheme_code=scheme_code,
        **scheme_in.model_dump(),
        created_by=current_user.id,
    )

    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)

    return scheme


@router.post("/schemes/{scheme_id}/apply", response_model=DealerSchemeApplicationResponse)
async def apply_scheme_to_dealer(
    scheme_id: UUID,
    application_in: DealerSchemeApplicationCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Apply scheme benefits to a dealer."""
    # Verify scheme
    scheme_result = await db.execute(
        select(DealerScheme).where(DealerScheme.id == scheme_id)
    )
    scheme = scheme_result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Verify dealer
    dealer_result = await db.execute(
        select(Dealer).where(Dealer.id == application_in.dealer_id)
    )
    dealer = dealer_result.scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    application = DealerSchemeApplication(
        scheme_id=scheme_id,
        dealer_id=application_in.dealer_id,
        achieved_value=application_in.achieved_value,
        achieved_quantity=application_in.achieved_quantity,
        benefit_earned=application_in.benefit_earned,
        benefit_type=application_in.benefit_type,
        status="APPROVED",
        approved_by=current_user.id,
        approved_at=datetime.now(timezone.utc),
        created_by=current_user.id,
    )

    db.add(application)
    await db.commit()
    await db.refresh(application)

    return application


# ==================== Reports ====================

@router.get("/reports/performance")
async def get_dealer_performance_report(
    start_date: date,
    end_date: date,
    db: DB,
    dealer_id: Optional[UUID] = None,
    region: Optional[str] = None,
    tier: Optional[DealerTier] = None,
    current_user: User = Depends(get_current_user),
):
    """Get dealer performance report."""
    from app.models.order import Order, OrderStatus

    query = select(Dealer)

    filters = []
    if dealer_id:
        filters.append(Dealer.id == dealer_id)
    if region:
        filters.append(Dealer.region == region)
    if tier:
        filters.append(Dealer.tier == tier)

    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    dealers = result.scalars().all()

    performance_data = []

    for dealer in dealers:
        # Get orders in period
        orders_query = select(
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("order_value"),
        ).where(
            and_(
                Order.dealer_id == dealer.id,
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED]),
            )
        )
        orders_result = await db.execute(orders_query)
        orders = orders_result.one()

        # Get targets for period
        targets_query = select(
            func.coalesce(func.sum(DealerTarget.target_value), 0).label("target_value"),
            func.coalesce(func.sum(DealerTarget.target_quantity), 0).label("target_qty"),
        ).where(
            and_(
                DealerTarget.dealer_id == dealer.id,
                DealerTarget.year >= start_date.year,
                DealerTarget.year <= end_date.year,
            )
        )
        targets_result = await db.execute(targets_query)
        targets = targets_result.one()

        achievement_pct = (
            (float(orders.order_value) / float(targets.target_value) * 100)
            if targets.target_value > 0 else 0
        )

        performance_data.append({
            "dealer_id": str(dealer.id),
            "dealer_code": dealer.dealer_code,
            "dealer_name": dealer.name,
            "tier": dealer.tier if dealer.tier else None,
            "order_count": orders.order_count,
            "order_value": float(orders.order_value),
            "target_value": float(targets.target_value),
            "achievement_percentage": round(achievement_pct, 2),
            "credit_limit": float(dealer.credit_limit),
            "current_balance": float(dealer.outstanding_amount),
            "available_credit": float(dealer.credit_limit - dealer.outstanding_amount),
        })

    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "dealers": performance_data,
        "summary": {
            "total_dealers": len(performance_data),
            "total_order_value": sum(d["order_value"] for d in performance_data),
            "total_target_value": sum(d["target_value"] for d in performance_data),
            "avg_achievement": (
                sum(d["achievement_percentage"] for d in performance_data) / len(performance_data)
                if performance_data else 0
            ),
        }
    }


@router.get("/reports/aging")
async def get_dealer_aging_report(
    db: DB,
    as_of_date: date = Query(default_factory=date.today),
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get dealer aging report (Accounts Receivable)."""
    query = select(Dealer).where(Dealer.outstanding_amount > 0)

    if region:
        query = query.where(Dealer.region == region)

    result = await db.execute(query)
    dealers = result.scalars().all()

    aging_data = []
    summary_buckets = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}

    for dealer in dealers:
        # Get unsettled ledger entries
        ledger_query = select(DealerCreditLedger).where(
            and_(
                DealerCreditLedger.dealer_id == dealer.id,
                DealerCreditLedger.is_settled == False,
                DealerCreditLedger.debit_amount > 0,
            )
        )
        ledger_result = await db.execute(ledger_query)
        entries = ledger_result.scalars().all()

        buckets = {"0-30": Decimal("0"), "31-60": Decimal("0"), "61-90": Decimal("0"), "90+": Decimal("0")}

        for entry in entries:
            days = (as_of_date - entry.transaction_date).days
            amount = entry.debit_amount

            if days <= 30:
                buckets["0-30"] += amount
            elif days <= 60:
                buckets["31-60"] += amount
            elif days <= 90:
                buckets["61-90"] += amount
            else:
                buckets["90+"] += amount

        total = sum(buckets.values())
        if total > 0:
            aging_data.append({
                "dealer_id": str(dealer.id),
                "dealer_code": dealer.dealer_code,
                "dealer_name": dealer.name,
                "total_outstanding": float(total),
                "buckets": {k: float(v) for k, v in buckets.items()},
            })

            for k, v in buckets.items():
                summary_buckets[k] += float(v)

    return {
        "as_of_date": as_of_date.isoformat(),
        "dealers": aging_data,
        "summary": summary_buckets,
        "total_outstanding": sum(summary_buckets.values()),
    }
