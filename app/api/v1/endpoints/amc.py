"""AMC (Annual Maintenance Contract) API endpoints.

Enhanced with:
- Comprehensive vs Non-Comprehensive contract types
- Plan-based auto-population (features, SLA, tenure pricing)
- Sales channel tracking (online/offline/dealer/technician)
- Commission calculation for field sales
- Grace period & lapsed contract inspection workflow
- Deferred revenue tracking
- SLA auto-assignment on service requests
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.amc import AMCContract, AMCPlan, AMCStatus
from app.models.customer import Customer
from app.models.product import Product
from app.models.installation import Installation
from uuid import uuid4

router = APIRouter()


# ==================== Inline Schemas (used directly in endpoints) ====================

class AMCPlanCreateInline(BaseModel):
    name: str
    code: str
    amc_type: str = "STANDARD"
    contract_type: str = "COMPREHENSIVE"  # COMPREHENSIVE or NON_COMPREHENSIVE
    category_id: Optional[UUID] = None
    duration_months: int = 12
    base_price: Decimal
    tax_rate: Decimal = Decimal("18")
    services_included: int = 2
    parts_covered: bool = False
    labor_covered: bool = True
    emergency_support: bool = False
    priority_service: bool = False
    discount_on_parts: Decimal = Decimal("0")
    # New Phase 1 fields
    features_included: Optional[List[dict]] = None
    parts_included: Optional[List[dict]] = None
    tenure_options: Optional[List[dict]] = None
    response_sla_hours: int = 48
    resolution_sla_hours: int = 72
    grace_period_days: int = 15
    terms_and_conditions: Optional[str] = None
    description: Optional[str] = None


class AMCPlanUpdateInline(BaseModel):
    name: Optional[str] = None
    contract_type: Optional[str] = None
    base_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    services_included: Optional[int] = None
    parts_covered: Optional[bool] = None
    labor_covered: Optional[bool] = None
    emergency_support: Optional[bool] = None
    priority_service: Optional[bool] = None
    discount_on_parts: Optional[Decimal] = None
    features_included: Optional[List[dict]] = None
    parts_included: Optional[List[dict]] = None
    tenure_options: Optional[List[dict]] = None
    response_sla_hours: Optional[int] = None
    resolution_sla_hours: Optional[int] = None
    grace_period_days: Optional[int] = None
    terms_and_conditions: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class AMCContractCreateInline(BaseModel):
    customer_id: UUID
    product_id: UUID
    installation_id: Optional[UUID] = None
    serial_number: str
    amc_type: str = "STANDARD"
    contract_type: str = "COMPREHENSIVE"
    plan_id: Optional[UUID] = None  # Auto-populate from plan
    start_date: date
    duration_months: int = 12
    total_services: int = 2
    base_price: Decimal
    discount_amount: Decimal = Decimal("0")
    parts_covered: bool = False
    labor_covered: bool = True
    emergency_support: bool = False
    priority_service: bool = False
    discount_on_parts: Decimal = Decimal("0")
    terms_and_conditions: Optional[str] = None
    notes: Optional[str] = None
    # Sales channel
    sales_channel: str = "OFFLINE"  # ONLINE, OFFLINE, DEALER, TECHNICIAN
    sold_by_id: Optional[UUID] = None
    sold_by_type: Optional[str] = None  # USER, DEALER, TECHNICIAN


class AMCInspectionCompleteInline(BaseModel):
    status: str  # COMPLETED or FAILED
    inspection_date: Optional[date] = None
    notes: Optional[str] = None


# ==================== Helper Functions ====================

DEFAULT_COMMISSION_RATES = {
    "TECHNICIAN": Decimal("10"),  # 10% commission for technician field sales
    "DEALER": Decimal("15"),  # 15% for dealers
    "USER": Decimal("5"),  # 5% for internal sales staff
}


def _serialize_plan(plan: AMCPlan) -> dict:
    """Serialize an AMCPlan to dict."""
    return {
        "id": str(plan.id),
        "name": plan.name,
        "code": plan.code,
        "amc_type": plan.amc_type,
        "contract_type": plan.contract_type or "COMPREHENSIVE",
        "category_id": str(plan.category_id) if plan.category_id else None,
        "product_ids": plan.product_ids,
        "duration_months": plan.duration_months,
        "base_price": float(plan.base_price or 0),
        "tax_rate": float(plan.tax_rate or 0),
        "services_included": plan.services_included,
        "parts_covered": plan.parts_covered,
        "labor_covered": plan.labor_covered,
        "emergency_support": plan.emergency_support,
        "priority_service": plan.priority_service,
        "discount_on_parts": float(plan.discount_on_parts or 0),
        "features_included": plan.features_included or [],
        "parts_included": plan.parts_included or [],
        "tenure_options": plan.tenure_options or [],
        "response_sla_hours": plan.response_sla_hours or 48,
        "resolution_sla_hours": plan.resolution_sla_hours or 72,
        "grace_period_days": plan.grace_period_days or 15,
        "terms_and_conditions": plan.terms_and_conditions,
        "description": plan.description,
        "is_active": plan.is_active,
        "sort_order": plan.sort_order or 0,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


def _serialize_contract_list(c: AMCContract) -> dict:
    """Serialize an AMCContract for list view."""
    return {
        "id": str(c.id),
        "contract_number": c.contract_number,
        "amc_type": c.amc_type,
        "contract_type": c.contract_type or "COMPREHENSIVE",
        "status": c.status,
        "customer_id": str(c.customer_id),
        "customer_name": f"{c.customer.first_name} {c.customer.last_name}" if c.customer else None,
        "product_name": c.product.name if c.product else None,
        "plan_id": str(c.plan_id) if c.plan_id else None,
        "plan_name": c.plan.name if c.plan else c.amc_type,
        "serial_number": c.serial_number,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "days_remaining": c.days_remaining,
        "total_services": c.total_services,
        "services_used": c.services_used,
        "services_remaining": c.services_remaining,
        "total_amount": float(c.total_amount or 0),
        "payment_status": c.payment_status,
        "next_service_due": c.next_service_due.isoformat() if c.next_service_due else None,
        # New fields
        "sales_channel": c.sales_channel or "OFFLINE",
        "sold_by_type": c.sold_by_type,
        "grace_end_date": c.grace_end_date.isoformat() if c.grace_end_date else None,
        "requires_inspection": c.requires_inspection or False,
        "inspection_status": c.inspection_status,
        "commission_amount": float(c.commission_amount or 0),
        "commission_paid": c.commission_paid or False,
        "revenue_recognized": float(c.revenue_recognized or 0),
        "revenue_pending": float(c.revenue_pending or 0),
    }


# ==================== Plan Endpoints ====================

@router.get("/plans")
async def list_amc_plans(
    db: DB,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    amc_type: Optional[str] = None,
    contract_type: Optional[str] = None,
    category_id: Optional[UUID] = None,
):
    """List AMC plans with enhanced fields."""
    query = select(AMCPlan)

    conditions = []
    if is_active is not None:
        conditions.append(AMCPlan.is_active == is_active)
    if amc_type:
        conditions.append(AMCPlan.amc_type == amc_type.upper())
    if contract_type:
        conditions.append(AMCPlan.contract_type == contract_type.upper())
    if category_id:
        conditions.append(AMCPlan.category_id == category_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(AMCPlan)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(AMCPlan.sort_order, AMCPlan.name)
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    plans = result.scalars().all()

    return {
        "items": [_serialize_plan(plan) for plan in plans],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/plans/{plan_id}")
async def get_amc_plan(
    plan_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get AMC plan details with features, tenure options, and SLA."""
    plan = await db.get(AMCPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return _serialize_plan(plan)


@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_amc_plan(
    data: AMCPlanCreateInline,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new AMC plan with features, SLA rules, and tenure options."""
    # Check for duplicate code
    existing = await db.execute(
        select(AMCPlan).where(AMCPlan.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Plan code already exists")

    plan = AMCPlan(
        name=data.name,
        code=data.code,
        amc_type=data.amc_type.upper(),
        contract_type=data.contract_type.upper() if data.contract_type else "COMPREHENSIVE",
        category_id=data.category_id,
        duration_months=data.duration_months,
        base_price=data.base_price,
        tax_rate=data.tax_rate,
        services_included=data.services_included,
        parts_covered=data.parts_covered,
        labor_covered=data.labor_covered,
        emergency_support=data.emergency_support,
        priority_service=data.priority_service,
        discount_on_parts=data.discount_on_parts,
        # New Phase 1 fields
        features_included=data.features_included or [],
        parts_included=data.parts_included or [],
        tenure_options=data.tenure_options or [],
        response_sla_hours=data.response_sla_hours,
        resolution_sla_hours=data.resolution_sla_hours,
        grace_period_days=data.grace_period_days,
        terms_and_conditions=data.terms_and_conditions,
        description=data.description,
        is_active=True,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {"id": str(plan.id), "code": plan.code, "message": "Plan created successfully"}


@router.put("/plans/{plan_id}")
async def update_amc_plan(
    plan_id: UUID,
    data: AMCPlanUpdateInline,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update an AMC plan."""
    plan = await db.get(AMCPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "amc_type" and value:
            value = value.upper()
        if field == "contract_type" and value:
            value = value.upper()
        setattr(plan, field, value)

    await db.commit()

    return {"message": "Plan updated successfully"}


# ==================== Contract Endpoints ====================

@router.get("/contracts")
async def list_amc_contracts(
    db: DB,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    amc_type: Optional[str] = None,
    contract_type: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    sales_channel: Optional[str] = None,
    expiring_in_days: Optional[int] = None,
    search: Optional[str] = None,
):
    """List AMC contracts with enhanced filtering."""
    query = select(AMCContract).options(
        selectinload(AMCContract.customer),
        selectinload(AMCContract.product),
        selectinload(AMCContract.plan),
        selectinload(AMCContract.installation),
    )

    conditions = []

    if status:
        conditions.append(AMCContract.status == status.upper())

    if amc_type:
        conditions.append(AMCContract.amc_type == amc_type.upper())

    if contract_type:
        conditions.append(AMCContract.contract_type == contract_type.upper())

    if customer_id:
        conditions.append(AMCContract.customer_id == customer_id)

    if product_id:
        conditions.append(AMCContract.product_id == product_id)

    if sales_channel:
        conditions.append(AMCContract.sales_channel == sales_channel.upper())

    if expiring_in_days:
        expiry_date = date.today() + timedelta(days=expiring_in_days)
        conditions.append(
            and_(
                AMCContract.end_date <= expiry_date,
                AMCContract.end_date >= date.today(),
                AMCContract.status == "ACTIVE"
            )
        )

    if search:
        conditions.append(
            or_(
                AMCContract.contract_number.ilike(f"%{search}%"),
                AMCContract.serial_number.ilike(f"%{search}%"),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(AMCContract)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(desc(AMCContract.start_date))
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    contracts = result.scalars().all()

    return {
        "items": [_serialize_contract_list(c) for c in contracts],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/contracts/stats")
async def get_contract_stats(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get AMC contract statistics including channel-wise breakdown."""
    # By status
    status_query = select(
        AMCContract.status,
        func.count().label("count")
    ).group_by(AMCContract.status)
    status_result = await db.execute(status_query)
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Active contracts value
    active_value_query = select(func.sum(AMCContract.total_amount)).where(
        AMCContract.status == "ACTIVE"
    )
    active_value = await db.scalar(active_value_query) or Decimal("0")

    # Expiring in 30 days
    expiry_date = date.today() + timedelta(days=30)
    expiring_query = select(func.count()).select_from(AMCContract).where(
        and_(
            AMCContract.end_date <= expiry_date,
            AMCContract.end_date >= date.today(),
            AMCContract.status == "ACTIVE"
        )
    )
    expiring_soon = await db.scalar(expiring_query) or 0

    # Services due this month
    month_end = date.today().replace(day=28) + timedelta(days=4)
    month_end = month_end.replace(day=1) - timedelta(days=1)
    services_due_query = select(func.count()).select_from(AMCContract).where(
        and_(
            AMCContract.next_service_due <= month_end,
            AMCContract.next_service_due >= date.today(),
            AMCContract.status == "ACTIVE"
        )
    )
    services_due = await db.scalar(services_due_query) or 0

    # Channel-wise breakdown
    channel_query = select(
        AMCContract.sales_channel,
        func.count().label("count"),
        func.sum(AMCContract.total_amount).label("value")
    ).where(
        AMCContract.status == "ACTIVE"
    ).group_by(AMCContract.sales_channel)
    channel_result = await db.execute(channel_query)
    by_channel = {
        (row[0] or "OFFLINE"): {"count": row[1], "value": float(row[2] or 0)}
        for row in channel_result.all()
    }

    # Commission pending
    commission_pending_query = select(
        func.sum(AMCContract.commission_amount)
    ).where(
        and_(
            AMCContract.commission_paid == False,
            AMCContract.commission_amount > 0,
            AMCContract.status.in_(["ACTIVE", "RENEWED"])
        )
    )
    commission_pending = await db.scalar(commission_pending_query) or Decimal("0")

    # Pending inspections
    pending_inspections = await db.scalar(
        select(func.count()).select_from(AMCContract).where(
            AMCContract.inspection_status == "PENDING"
        )
    ) or 0

    return {
        "by_status": by_status,
        "active_contracts": by_status.get("ACTIVE", 0),
        "active_value": float(active_value),
        "expiring_in_30_days": expiring_soon,
        "services_due_this_month": services_due,
        "total": sum(by_status.values()),
        "by_channel": by_channel,
        "commission_pending": float(commission_pending),
        "pending_inspections": pending_inspections,
    }


@router.get("/contracts/{contract_id}")
async def get_amc_contract(
    contract_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get AMC contract details with all enhanced fields."""
    query = select(AMCContract).options(
        selectinload(AMCContract.customer),
        selectinload(AMCContract.product),
        selectinload(AMCContract.plan),
        selectinload(AMCContract.installation),
        selectinload(AMCContract.service_requests),
        selectinload(AMCContract.creator),
        selectinload(AMCContract.approver),
    ).where(AMCContract.id == contract_id)

    result = await db.execute(query)
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {
        "id": str(contract.id),
        "contract_number": contract.contract_number,
        "amc_type": contract.amc_type,
        "contract_type": contract.contract_type or "COMPREHENSIVE",
        "status": contract.status,
        "customer": {
            "id": str(contract.customer_id),
            "name": f"{contract.customer.first_name} {contract.customer.last_name}" if contract.customer else None,
            "phone": contract.customer.phone if contract.customer else None,
        },
        "product": {
            "id": str(contract.product_id),
            "name": contract.product.name if contract.product else None,
        },
        "plan_id": str(contract.plan_id) if contract.plan_id else None,
        "plan_name": contract.plan.name if contract.plan else None,
        "installation_id": str(contract.installation_id) if contract.installation_id else None,
        "serial_number": contract.serial_number,
        "start_date": contract.start_date.isoformat() if contract.start_date else None,
        "end_date": contract.end_date.isoformat() if contract.end_date else None,
        "duration_months": contract.duration_months,
        "days_remaining": contract.days_remaining,
        "is_active": contract.is_active,
        "total_services": contract.total_services,
        "services_used": contract.services_used,
        "services_remaining": contract.services_remaining,
        "service_schedule": contract.service_schedule,
        "next_service_due": contract.next_service_due.isoformat() if contract.next_service_due else None,
        "base_price": float(contract.base_price or 0),
        "tax_amount": float(contract.tax_amount or 0),
        "discount_amount": float(contract.discount_amount or 0),
        "total_amount": float(contract.total_amount or 0),
        "payment_status": contract.payment_status,
        "payment_mode": contract.payment_mode,
        "payment_reference": contract.payment_reference,
        "paid_at": contract.paid_at.isoformat() if contract.paid_at else None,
        "parts_covered": contract.parts_covered,
        "labor_covered": contract.labor_covered,
        "emergency_support": contract.emergency_support,
        "priority_service": contract.priority_service,
        "discount_on_parts": float(contract.discount_on_parts or 0),
        "terms_and_conditions": contract.terms_and_conditions,
        "is_renewable": contract.is_renewable,
        "renewal_reminder_sent": contract.renewal_reminder_sent,
        "notes": contract.notes,
        # Sales channel
        "sales_channel": contract.sales_channel or "OFFLINE",
        "sold_by_id": str(contract.sold_by_id) if contract.sold_by_id else None,
        "sold_by_type": contract.sold_by_type,
        # Commission
        "commission_rate": float(contract.commission_rate or 0),
        "commission_amount": float(contract.commission_amount or 0),
        "commission_paid": contract.commission_paid or False,
        # Grace & inspection
        "grace_end_date": contract.grace_end_date.isoformat() if contract.grace_end_date else None,
        "requires_inspection": contract.requires_inspection or False,
        "inspection_status": contract.inspection_status,
        "inspection_date": contract.inspection_date.isoformat() if contract.inspection_date else None,
        "inspection_notes": contract.inspection_notes,
        # Deferred revenue
        "revenue_recognized": float(contract.revenue_recognized or 0),
        "revenue_pending": float(contract.revenue_pending or 0),
        # Service requests
        "service_requests": [
            {
                "id": str(sr.id),
                "ticket_number": sr.ticket_number,
                "status": sr.status,
                "service_type": sr.service_type,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
            }
            for sr in (contract.service_requests or [])
        ],
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
    }


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
async def create_amc_contract(
    data: AMCContractCreateInline,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new AMC contract with plan-based auto-population and commission tracking."""
    # Validate customer
    customer = await db.get(Customer, data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate product
    product = await db.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Auto-populate from plan if plan_id provided
    plan = None
    if data.plan_id:
        plan = await db.get(AMCPlan, data.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="AMC Plan not found")
        if not plan.is_active:
            raise HTTPException(status_code=400, detail="AMC Plan is not active")

    # Use plan values as defaults if plan provided
    base_price = data.base_price
    total_services = data.total_services
    duration_months = data.duration_months
    contract_type = data.contract_type
    parts_covered = data.parts_covered
    labor_covered = data.labor_covered
    emergency_support = data.emergency_support
    priority_service = data.priority_service
    discount_on_parts = data.discount_on_parts

    if plan:
        # Check if a tenure option matches the requested duration
        if plan.tenure_options:
            for opt in plan.tenure_options:
                if opt.get("months") == data.duration_months:
                    base_price = Decimal(str(opt["price"]))
                    break
            else:
                base_price = plan.base_price
        else:
            base_price = plan.base_price

        total_services = plan.services_included
        contract_type = plan.contract_type or "COMPREHENSIVE"
        parts_covered = plan.parts_covered
        labor_covered = plan.labor_covered
        emergency_support = plan.emergency_support
        priority_service = plan.priority_service
        discount_on_parts = plan.discount_on_parts

    # Generate contract number (AMC-YYYYMMDD-XXXX format)
    today = date.today()
    random_suffix = str(uuid4())[:8].upper()
    contract_number = f"AMC-{today.strftime('%Y%m%d')}-{random_suffix}"

    # Calculate end date
    end_date = data.start_date + timedelta(days=duration_months * 30)

    # Calculate tax
    tax_rate = Decimal(str(plan.tax_rate)) if plan else Decimal("18")
    tax_amount = base_price * tax_rate / Decimal("100")
    total_amount = base_price + tax_amount - data.discount_amount

    # Calculate commission
    commission_rate = Decimal("0")
    commission_amount = Decimal("0")
    sales_channel = data.sales_channel.upper() if data.sales_channel else "OFFLINE"
    sold_by_type = data.sold_by_type.upper() if data.sold_by_type else None

    if sold_by_type and sold_by_type in DEFAULT_COMMISSION_RATES:
        commission_rate = DEFAULT_COMMISSION_RATES[sold_by_type]
        commission_amount = total_amount * commission_rate / Decimal("100")

    # Calculate grace end date from plan
    grace_period_days = plan.grace_period_days if plan else 15
    grace_end_date = end_date + timedelta(days=grace_period_days)

    # Create service schedule
    service_interval = duration_months // total_services if total_services > 0 else duration_months
    service_schedule = []
    for i in range(total_services):
        service_month = i * service_interval + (service_interval // 2)
        service_schedule.append({
            "service_number": i + 1,
            "due_month": service_month,
            "scheduled_date": None,
            "completed_date": None,
        })

    contract = AMCContract(
        contract_number=contract_number,
        amc_type=data.amc_type.upper() if data.amc_type else "STANDARD",
        contract_type=contract_type.upper(),
        status="DRAFT",
        customer_id=data.customer_id,
        product_id=data.product_id,
        installation_id=data.installation_id,
        plan_id=data.plan_id,
        serial_number=data.serial_number,
        start_date=data.start_date,
        end_date=end_date,
        duration_months=duration_months,
        total_services=total_services,
        services_remaining=total_services,
        base_price=base_price,
        tax_amount=tax_amount,
        discount_amount=data.discount_amount,
        total_amount=total_amount,
        parts_covered=parts_covered,
        labor_covered=labor_covered,
        emergency_support=emergency_support,
        priority_service=priority_service,
        discount_on_parts=discount_on_parts,
        terms_and_conditions=data.terms_and_conditions or (plan.terms_and_conditions if plan else None),
        notes=data.notes,
        service_schedule=service_schedule,
        next_service_due=data.start_date + timedelta(days=service_interval * 30 // 2) if service_interval > 0 else None,
        # Sales channel
        sales_channel=sales_channel,
        sold_by_id=data.sold_by_id,
        sold_by_type=sold_by_type,
        # Commission
        commission_rate=commission_rate,
        commission_amount=commission_amount,
        commission_paid=False,
        # Grace period
        grace_end_date=grace_end_date,
        # Deferred revenue (full amount pending initially)
        revenue_recognized=Decimal("0"),
        revenue_pending=total_amount,
        created_by=current_user.id,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    return {
        "id": str(contract.id),
        "contract_number": contract.contract_number,
        "total_amount": float(contract.total_amount),
        "commission_amount": float(contract.commission_amount),
        "message": "AMC contract created successfully",
    }


@router.post("/contracts/{contract_id}/activate")
async def activate_contract(
    contract_id: UUID,
    payment_mode: str,
    payment_reference: Optional[str] = None,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Activate an AMC contract after payment."""
    contract = await db.get(AMCContract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    allowed_statuses = ["DRAFT", "PENDING_PAYMENT"]
    if contract.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate contract with status {contract.status}"
        )

    contract.status = "ACTIVE"
    contract.payment_status = "PAID"
    contract.payment_mode = payment_mode
    contract.payment_reference = payment_reference
    contract.paid_at = datetime.now(timezone.utc)
    contract.approved_by = current_user.id

    await db.commit()

    return {"message": "Contract activated", "status": contract.status}


@router.post("/contracts/{contract_id}/use-service")
async def use_service(
    contract_id: UUID,
    service_request_id: Optional[UUID] = None,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Record a service used against the contract."""
    contract = await db.get(AMCContract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Contract is not active")

    if contract.services_remaining <= 0:
        raise HTTPException(status_code=400, detail="No services remaining")

    contract.services_used += 1
    contract.services_remaining -= 1

    # Update service schedule
    if contract.service_schedule:
        for service in contract.service_schedule:
            if not service.get("completed_date"):
                service["completed_date"] = date.today().isoformat()
                break

    # Calculate next service due
    if contract.services_remaining > 0:
        remaining_days = (contract.end_date - date.today()).days
        interval = remaining_days // contract.services_remaining
        contract.next_service_due = date.today() + timedelta(days=interval)
    else:
        contract.next_service_due = None

    await db.commit()

    return {
        "message": "Service recorded",
        "services_used": contract.services_used,
        "services_remaining": contract.services_remaining,
    }


@router.post("/contracts/{contract_id}/renew")
async def renew_contract(
    contract_id: UUID,
    new_plan_id: Optional[UUID] = None,
    duration_months: int = 12,
    sales_channel: str = "OFFLINE",
    sold_by_id: Optional[UUID] = None,
    sold_by_type: Optional[str] = None,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Renew an AMC contract with lapsed-contract inspection check."""
    old_contract = await db.get(AMCContract, contract_id)
    if not old_contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if old_contract.status not in ["ACTIVE", "EXPIRED", "RENEWED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot renew contract with status {old_contract.status}"
        )

    # Check if lapsed beyond grace period — requires inspection
    today = date.today()
    grace_end = old_contract.grace_end_date or old_contract.end_date
    if old_contract.status == "EXPIRED" and today > grace_end:
        # Lapsed contract — needs inspection before renewal
        if not old_contract.requires_inspection:
            old_contract.requires_inspection = True
            old_contract.inspection_status = "PENDING"
            old_contract.status = "PENDING_INSPECTION"
            await db.commit()
            raise HTTPException(
                status_code=400,
                detail="Contract has lapsed beyond grace period. Inspection required before renewal. "
                       "Use POST /contracts/{id}/request-inspection to schedule."
            )
        elif old_contract.inspection_status != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"Inspection is {old_contract.inspection_status}. "
                       "Cannot renew until inspection is COMPLETED."
            )

    # Get plan if specified
    base_price = old_contract.base_price
    total_services = old_contract.total_services
    contract_type = old_contract.contract_type or "COMPREHENSIVE"
    plan = None

    if new_plan_id:
        plan = await db.get(AMCPlan, new_plan_id)
        if plan:
            # Check tenure option for pricing
            if plan.tenure_options:
                for opt in plan.tenure_options:
                    if opt.get("months") == duration_months:
                        base_price = Decimal(str(opt["price"]))
                        break
                else:
                    base_price = plan.base_price
            else:
                base_price = plan.base_price
            total_services = plan.services_included
            contract_type = plan.contract_type or "COMPREHENSIVE"

    # Create new contract
    random_suffix = str(uuid4())[:8].upper()
    new_contract_number = f"AMC-{today.strftime('%Y%m%d')}-{random_suffix}"
    start_date = max(old_contract.end_date, today)
    end_date = start_date + timedelta(days=duration_months * 30)
    tax_rate = Decimal(str(plan.tax_rate)) if plan else Decimal("18")
    tax_amount = base_price * tax_rate / Decimal("100")
    total_amount = base_price + tax_amount

    # Commission for renewal
    commission_rate = Decimal("0")
    commission_amount = Decimal("0")
    if sold_by_type and sold_by_type.upper() in DEFAULT_COMMISSION_RATES:
        commission_rate = DEFAULT_COMMISSION_RATES[sold_by_type.upper()]
        commission_amount = total_amount * commission_rate / Decimal("100")

    # Grace period
    grace_period_days = plan.grace_period_days if plan else 15
    grace_end_date = end_date + timedelta(days=grace_period_days)

    new_contract = AMCContract(
        contract_number=new_contract_number,
        amc_type=old_contract.amc_type,
        contract_type=contract_type,
        status="DRAFT",
        customer_id=old_contract.customer_id,
        product_id=old_contract.product_id,
        installation_id=old_contract.installation_id,
        plan_id=new_plan_id or old_contract.plan_id,
        serial_number=old_contract.serial_number,
        start_date=start_date,
        end_date=end_date,
        duration_months=duration_months,
        total_services=total_services,
        services_remaining=total_services,
        base_price=base_price,
        tax_amount=tax_amount,
        total_amount=total_amount,
        parts_covered=plan.parts_covered if plan else old_contract.parts_covered,
        labor_covered=plan.labor_covered if plan else old_contract.labor_covered,
        emergency_support=plan.emergency_support if plan else old_contract.emergency_support,
        priority_service=plan.priority_service if plan else old_contract.priority_service,
        discount_on_parts=plan.discount_on_parts if plan else old_contract.discount_on_parts,
        terms_and_conditions=plan.terms_and_conditions if plan else old_contract.terms_and_conditions,
        renewed_from_id=old_contract.id,
        # Sales channel
        sales_channel=sales_channel.upper(),
        sold_by_id=sold_by_id,
        sold_by_type=sold_by_type.upper() if sold_by_type else None,
        # Commission
        commission_rate=commission_rate,
        commission_amount=commission_amount,
        commission_paid=False,
        # Grace
        grace_end_date=grace_end_date,
        # Deferred revenue
        revenue_recognized=Decimal("0"),
        revenue_pending=total_amount,
        created_by=current_user.id,
    )
    db.add(new_contract)

    # Update old contract
    old_contract.status = "RENEWED"
    old_contract.renewed_to_id = new_contract.id

    await db.commit()
    await db.refresh(new_contract)

    return {
        "id": str(new_contract.id),
        "contract_number": new_contract.contract_number,
        "total_amount": float(new_contract.total_amount),
        "message": "Contract renewed successfully",
    }


@router.post("/contracts/{contract_id}/request-inspection")
async def request_inspection(
    contract_id: UUID,
    preferred_date: Optional[date] = None,
    notes: Optional[str] = None,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Request inspection for a lapsed contract before re-enrollment.

    When an AMC contract expires beyond the grace period, the device must be
    inspected by a technician before a new contract can be issued.
    This is industry standard (Eureka Forbes, Atomberg, Kent all require this).
    """
    contract = await db.get(AMCContract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.requires_inspection:
        raise HTTPException(
            status_code=400,
            detail="This contract does not require inspection"
        )

    if contract.inspection_status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Inspection already completed. Proceed with renewal."
        )

    contract.inspection_status = "SCHEDULED" if preferred_date else "PENDING"
    contract.inspection_date = preferred_date
    contract.inspection_notes = notes
    contract.status = "PENDING_INSPECTION"

    await db.commit()

    return {
        "message": "Inspection requested",
        "inspection_status": contract.inspection_status,
        "inspection_date": contract.inspection_date.isoformat() if contract.inspection_date else None,
    }


@router.post("/contracts/{contract_id}/complete-inspection")
async def complete_inspection(
    contract_id: UUID,
    data: AMCInspectionCompleteInline,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Complete or fail an inspection for a lapsed contract.

    After inspection:
    - COMPLETED: Contract can be renewed
    - FAILED: Contract cannot be renewed (device needs repair first)
    """
    contract = await db.get(AMCContract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.requires_inspection:
        raise HTTPException(status_code=400, detail="No inspection required")

    if data.status.upper() not in ["COMPLETED", "FAILED"]:
        raise HTTPException(status_code=400, detail="Status must be COMPLETED or FAILED")

    contract.inspection_status = data.status.upper()
    contract.inspection_date = data.inspection_date or date.today()
    contract.inspection_notes = data.notes

    if data.status.upper() == "COMPLETED":
        contract.status = "EXPIRED"  # Ready for renewal now
    # If FAILED, stays in PENDING_INSPECTION — customer must get device repaired first

    await db.commit()

    return {
        "message": f"Inspection {data.status.upper()}",
        "inspection_status": contract.inspection_status,
        "can_renew": contract.inspection_status == "COMPLETED",
    }


@router.get("/contracts/{contract_id}/sla")
async def get_contract_sla(
    contract_id: UUID,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Get SLA details for a contract based on its plan tier.

    Used by service request creation to auto-assign priority and SLA.
    """
    query = select(AMCContract).options(
        selectinload(AMCContract.plan)
    ).where(AMCContract.id == contract_id)

    result = await db.execute(query)
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get SLA from plan, or use defaults based on AMC type
    default_sla = {
        "STANDARD": {"response_hours": 48, "resolution_hours": 72, "priority": "NORMAL"},
        "COMPREHENSIVE": {"response_hours": 24, "resolution_hours": 48, "priority": "HIGH"},
        "EXTENDED_WARRANTY": {"response_hours": 24, "resolution_hours": 48, "priority": "HIGH"},
        "PLATINUM": {"response_hours": 4, "resolution_hours": 12, "priority": "URGENT"},
    }

    if contract.plan:
        return {
            "contract_id": str(contract.id),
            "plan_name": contract.plan.name,
            "response_sla_hours": contract.plan.response_sla_hours or 48,
            "resolution_sla_hours": contract.plan.resolution_sla_hours or 72,
            "priority": "URGENT" if contract.plan.priority_service else (
                "HIGH" if contract.plan.emergency_support else "NORMAL"
            ),
            "contract_type": contract.contract_type or "COMPREHENSIVE",
            "parts_covered": contract.parts_covered,
        }

    # Fallback to AMC type defaults
    sla = default_sla.get(contract.amc_type, default_sla["STANDARD"])
    return {
        "contract_id": str(contract.id),
        "plan_name": contract.amc_type,
        "response_sla_hours": sla["response_hours"],
        "resolution_sla_hours": sla["resolution_hours"],
        "priority": sla["priority"],
        "contract_type": contract.contract_type or "COMPREHENSIVE",
        "parts_covered": contract.parts_covered,
    }


# ==================== ANALYTICS ENDPOINTS ====================


@router.get("/analytics/conversion")
async def get_amc_conversion_analytics(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    AMC conversion analytics: warranty-to-AMC conversion rates.

    Returns:
    - Total installations (warranty devices)
    - Installations with active AMC
    - Conversion rate overall and by channel
    - Monthly conversion trend
    """
    from app.models.installation import Installation

    # Total installations
    total_installs = await db.scalar(
        select(func.count()).select_from(Installation).where(
            Installation.status.in_(["COMPLETED", "ACTIVE"])
        )
    ) or 0

    # Installations with active AMC contract
    installs_with_amc = await db.scalar(
        select(func.count(func.distinct(AMCContract.serial_number))).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED"])
        )
    ) or 0

    # Expired warranties without AMC (opportunity)
    today = date.today()
    expired_no_amc_subq = (
        select(AMCContract.serial_number)
        .where(AMCContract.status.in_(["ACTIVE", "PENDING", "RENEWED"]))
    )
    expired_no_amc = await db.scalar(
        select(func.count()).select_from(Installation).where(
            and_(
                Installation.warranty_end_date < today,
                Installation.status.in_(["COMPLETED", "ACTIVE"]),
                ~Installation.serial_number.in_(expired_no_amc_subq),
            )
        )
    ) or 0

    # Conversion by channel
    channel_result = await db.execute(
        select(
            AMCContract.sales_channel,
            func.count().label("count"),
        ).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED", "EXPIRED"])
        ).group_by(AMCContract.sales_channel)
    )
    by_channel = {
        (row[0] or "OFFLINE"): row[1]
        for row in channel_result.all()
    }

    # Monthly trend (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_result = await db.execute(
        select(
            func.date_trunc('month', AMCContract.created_at).label("month"),
            func.count().label("contracts"),
            func.sum(AMCContract.total_amount).label("revenue"),
        ).where(
            and_(
                AMCContract.created_at >= six_months_ago,
                AMCContract.status.in_(["ACTIVE", "RENEWED", "EXPIRED"]),
            )
        ).group_by(
            func.date_trunc('month', AMCContract.created_at)
        ).order_by(
            func.date_trunc('month', AMCContract.created_at)
        )
    )
    monthly_trend = [
        {
            "month": row[0].strftime("%Y-%m") if row[0] else None,
            "contracts": row[1],
            "revenue": float(row[2] or 0),
        }
        for row in monthly_result.all()
    ]

    # Warranty expiry funnel
    funnel = {}
    for window in [7, 15, 30, 60, 90]:
        target = today + timedelta(days=window)
        count = await db.scalar(
            select(func.count()).select_from(Installation).where(
                and_(
                    Installation.warranty_end_date <= target,
                    Installation.warranty_end_date >= today,
                    Installation.status.in_(["COMPLETED", "ACTIVE"]),
                    ~Installation.serial_number.in_(expired_no_amc_subq),
                )
            )
        ) or 0
        funnel[f"expiring_in_{window}_days"] = count

    conversion_rate = round((installs_with_amc / total_installs * 100), 1) if total_installs > 0 else 0

    return {
        "total_installations": total_installs,
        "installations_with_amc": installs_with_amc,
        "conversion_rate": conversion_rate,
        "expired_warranty_no_amc": expired_no_amc,
        "opportunity_count": expired_no_amc,
        "by_channel": by_channel,
        "monthly_trend": monthly_trend,
        "warranty_expiry_funnel": funnel,
    }


@router.get("/analytics/profitability")
async def get_amc_profitability(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Device profitability dashboard: revenue vs cost per AMC contract.

    Returns:
    - Total AMC revenue (recognized + pending)
    - Revenue by plan tier
    - Average contract value
    - Renewal rate
    - Revenue per channel
    """
    from app.models.service_request import ServiceRequest

    # Total revenue from AMC contracts
    total_revenue = await db.scalar(
        select(func.sum(AMCContract.total_amount)).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED", "EXPIRED"])
        )
    ) or Decimal("0")

    # Deferred revenue
    total_recognized = await db.scalar(
        select(func.sum(AMCContract.revenue_recognized)).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED"])
        )
    ) or Decimal("0")

    total_pending = await db.scalar(
        select(func.sum(AMCContract.revenue_pending)).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED"])
        )
    ) or Decimal("0")

    # Average contract value
    avg_value = await db.scalar(
        select(func.avg(AMCContract.total_amount)).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED", "EXPIRED"])
        )
    ) or Decimal("0")

    # Total contracts and active
    total_contracts = await db.scalar(
        select(func.count()).select_from(AMCContract)
    ) or 0

    active_contracts = await db.scalar(
        select(func.count()).select_from(AMCContract).where(
            AMCContract.status == "ACTIVE"
        )
    ) or 0

    # Renewal rate: contracts that were renewed / contracts that expired
    renewed_count = await db.scalar(
        select(func.count()).select_from(AMCContract).where(
            AMCContract.renewed_from_id.isnot(None)
        )
    ) or 0

    expired_count = await db.scalar(
        select(func.count()).select_from(AMCContract).where(
            AMCContract.status == "EXPIRED"
        )
    ) or 0

    renewal_rate = round((renewed_count / (expired_count + renewed_count) * 100), 1) if (expired_count + renewed_count) > 0 else 0

    # Revenue by plan
    plan_result = await db.execute(
        select(
            AMCPlan.name,
            func.count().label("count"),
            func.sum(AMCContract.total_amount).label("revenue"),
            func.avg(AMCContract.total_amount).label("avg_value"),
        ).join(AMCPlan, AMCPlan.id == AMCContract.plan_id, isouter=True)
        .where(AMCContract.status.in_(["ACTIVE", "RENEWED", "EXPIRED"]))
        .group_by(AMCPlan.name)
    )
    by_plan = [
        {
            "plan_name": row[0] or "No Plan",
            "count": row[1],
            "revenue": float(row[2] or 0),
            "avg_value": float(row[3] or 0),
        }
        for row in plan_result.all()
    ]

    # Revenue by channel
    channel_revenue_result = await db.execute(
        select(
            AMCContract.sales_channel,
            func.count().label("count"),
            func.sum(AMCContract.total_amount).label("revenue"),
        ).where(
            AMCContract.status.in_(["ACTIVE", "RENEWED", "EXPIRED"])
        ).group_by(AMCContract.sales_channel)
    )
    by_channel = [
        {
            "channel": row[0] or "OFFLINE",
            "count": row[1],
            "revenue": float(row[2] or 0),
        }
        for row in channel_revenue_result.all()
    ]

    # Service cost estimate (number of service requests completed for AMC contracts)
    service_count = await db.scalar(
        select(func.count()).select_from(ServiceRequest).where(
            and_(
                ServiceRequest.amc_id.isnot(None),
                ServiceRequest.status.in_(["COMPLETED", "CLOSED"]),
            )
        )
    ) or 0

    # Commission paid
    total_commission = await db.scalar(
        select(func.sum(AMCContract.commission_amount)).where(
            AMCContract.commission_amount > 0
        )
    ) or Decimal("0")

    commission_paid_total = await db.scalar(
        select(func.sum(AMCContract.commission_amount)).where(
            and_(
                AMCContract.commission_paid == True,
                AMCContract.commission_amount > 0,
            )
        )
    ) or Decimal("0")

    # SLA breach stats
    sla_breached = await db.scalar(
        select(func.count()).select_from(ServiceRequest).where(
            and_(
                ServiceRequest.amc_id.isnot(None),
                ServiceRequest.is_sla_breached == True,
            )
        )
    ) or 0

    total_amc_services = await db.scalar(
        select(func.count()).select_from(ServiceRequest).where(
            ServiceRequest.amc_id.isnot(None),
        )
    ) or 0

    sla_compliance_rate = round(
        ((total_amc_services - sla_breached) / total_amc_services * 100), 1
    ) if total_amc_services > 0 else 100

    return {
        "total_revenue": float(total_revenue),
        "revenue_recognized": float(total_recognized),
        "revenue_pending": float(total_pending),
        "average_contract_value": float(avg_value),
        "total_contracts": total_contracts,
        "active_contracts": active_contracts,
        "renewal_rate": renewal_rate,
        "renewed_count": renewed_count,
        "expired_count": expired_count,
        "by_plan": by_plan,
        "by_channel": by_channel,
        "total_services_delivered": service_count,
        "total_commission": float(total_commission),
        "commission_paid": float(commission_paid_total),
        "sla_breached_count": sla_breached,
        "sla_compliance_rate": sla_compliance_rate,
    }


@router.get("/analytics/churn-risk")
async def get_amc_churn_risk(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Churn prediction: flag customers likely to not renew.

    Risk factors:
    - Contract expiring soon with no renewal activity
    - Past SLA breaches on their service requests
    - Low service usage (unused visits)
    - No communication/engagement
    """
    today = date.today()
    thirty_days = today + timedelta(days=30)

    # Contracts expiring in next 30 days
    result = await db.execute(
        select(AMCContract, Customer, Product)
        .join(Customer, Customer.id == AMCContract.customer_id)
        .join(Product, Product.id == AMCContract.product_id)
        .where(
            and_(
                AMCContract.status == "ACTIVE",
                AMCContract.end_date <= thirty_days,
                AMCContract.end_date >= today,
                AMCContract.renewed_to_id.is_(None),  # Not yet renewed
            )
        )
        .order_by(AMCContract.end_date)
    )
    expiring = result.all()

    churn_risks = []
    for contract, customer, product in expiring:
        risk_score = 0
        risk_factors = []

        # Factor 1: Days until expiry (closer = higher risk)
        days_left = (contract.end_date - today).days
        if days_left <= 7:
            risk_score += 40
            risk_factors.append("Expires within 7 days")
        elif days_left <= 15:
            risk_score += 25
            risk_factors.append("Expires within 15 days")
        else:
            risk_score += 10
            risk_factors.append(f"Expires in {days_left} days")

        # Factor 2: Low service usage
        usage_rate = (contract.services_used / contract.total_services * 100) if contract.total_services > 0 else 0
        if usage_rate < 25:
            risk_score += 20
            risk_factors.append(f"Low service usage ({contract.services_used}/{contract.total_services})")

        # Factor 3: No renewal reminder response
        if contract.renewal_reminder_sent:
            risk_score += 15
            risk_factors.append("Reminder sent but no renewal")

        # Factor 4: Previous non-renewal history
        prev_expired = await db.scalar(
            select(func.count()).select_from(AMCContract).where(
                and_(
                    AMCContract.customer_id == contract.customer_id,
                    AMCContract.status == "EXPIRED",
                    AMCContract.renewed_to_id.is_(None),
                )
            )
        ) or 0
        if prev_expired > 0:
            risk_score += 20
            risk_factors.append(f"Previously let {prev_expired} contract(s) expire")

        # Cap at 100
        risk_score = min(risk_score, 100)
        risk_level = "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW"

        churn_risks.append({
            "contract_id": str(contract.id),
            "contract_number": contract.contract_number,
            "customer_name": f"{customer.first_name or ''} {customer.last_name or ''}".strip(),
            "customer_phone": customer.phone,
            "product_name": product.name,
            "serial_number": contract.serial_number,
            "end_date": contract.end_date.isoformat(),
            "days_remaining": days_left,
            "services_used": contract.services_used,
            "total_services": contract.total_services,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        })

    # Sort by risk score descending
    churn_risks.sort(key=lambda x: x["risk_score"], reverse=True)

    # Summary
    high_risk = len([c for c in churn_risks if c["risk_level"] == "HIGH"])
    medium_risk = len([c for c in churn_risks if c["risk_level"] == "MEDIUM"])
    low_risk = len([c for c in churn_risks if c["risk_level"] == "LOW"])

    return {
        "total_at_risk": len(churn_risks),
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "customers": churn_risks,
    }
