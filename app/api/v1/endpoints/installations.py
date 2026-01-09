"""Installation API endpoints for managing product installations."""
from typing import Optional
import uuid
from math import ceil
from datetime import datetime, date, timedelta

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.installation import Installation, InstallationStatus, WarrantyClaim
from app.models.order import Order
from app.models.customer import Customer
from app.models.product import Product
from app.models.technician import Technician, TechnicianStatus
from app.models.service_request import ServiceRequest, ServiceType, ServicePriority, ServiceStatus, ServiceSource


router = APIRouter()


# ==================== SCHEMAS ====================

class InstallationBase(BaseModel):
    """Base installation schema."""
    customer_id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    product_id: uuid.UUID
    serial_number: Optional[str] = None
    installation_pincode: str
    installation_city: Optional[str] = None
    installation_address: Optional[dict] = None
    preferred_date: Optional[date] = None
    preferred_time_slot: Optional[str] = None
    notes: Optional[str] = None


class InstallationCreate(InstallationBase):
    """Create installation schema."""
    pass


class InstallationUpdate(BaseModel):
    """Update installation schema."""
    status: Optional[InstallationStatus] = None
    technician_id: Optional[uuid.UUID] = None
    scheduled_date: Optional[date] = None
    scheduled_time_slot: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class InstallationScheduleRequest(BaseModel):
    """Schedule installation request."""
    scheduled_date: date
    scheduled_time_slot: str
    technician_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class InstallationAssignRequest(BaseModel):
    """Assign technician request."""
    technician_id: uuid.UUID


class InstallationCompleteRequest(BaseModel):
    """Complete installation request."""
    installation_notes: Optional[str] = None
    pre_installation_checklist: Optional[dict] = None
    post_installation_checklist: Optional[dict] = None
    installation_photos: Optional[list] = None
    accessories_used: Optional[list] = None
    input_tds: Optional[int] = None
    output_tds: Optional[int] = None
    customer_signature_url: Optional[str] = None
    customer_feedback: Optional[str] = None
    customer_rating: Optional[int] = Field(None, ge=1, le=5)
    demo_given: bool = True
    demo_notes: Optional[str] = None
    warranty_months: int = 12


class InstallationResponse(BaseModel):
    """Installation response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    installation_number: str
    status: InstallationStatus
    customer_id: uuid.UUID
    order_id: Optional[uuid.UUID]
    product_id: uuid.UUID
    serial_number: Optional[str]
    installation_pincode: Optional[str]
    installation_city: Optional[str]
    installation_address: Optional[dict]
    preferred_date: Optional[date]
    preferred_time_slot: Optional[str]
    scheduled_date: Optional[date]
    scheduled_time_slot: Optional[str]
    technician_id: Optional[uuid.UUID]
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    installation_date: Optional[date]
    warranty_start_date: Optional[date]
    warranty_end_date: Optional[date]
    warranty_card_number: Optional[str]
    customer_rating: Optional[int]
    notes: Optional[str]
    created_at: Optional[datetime]


class InstallationDetailResponse(InstallationResponse):
    """Detailed installation response."""
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    technician_name: Optional[str] = None
    order_number: Optional[str] = None
    installation_notes: Optional[str] = None
    input_tds: Optional[int] = None
    output_tds: Optional[int] = None
    demo_given: Optional[bool] = None
    demo_notes: Optional[str] = None
    customer_feedback: Optional[str] = None


class InstallationListResponse(BaseModel):
    """Paginated installation list."""
    items: list[InstallationResponse]
    total: int
    page: int
    size: int
    pages: int


class InstallationDashboardResponse(BaseModel):
    """Installation dashboard stats."""
    total_pending: int
    total_scheduled: int
    total_in_progress: int
    total_completed_today: int
    total_completed_week: int
    total_completed_month: int
    avg_completion_days: float
    avg_customer_rating: float
    pending_assignments: int


# ==================== HELPERS ====================

def generate_installation_number() -> str:
    """Generate unique installation number."""
    import random
    date_str = datetime.now().strftime("%Y%m%d")
    random_suffix = random.randint(10000, 99999)
    return f"INST-{date_str}-{random_suffix}"


def generate_warranty_card_number() -> str:
    """Generate unique warranty card number."""
    import random
    return f"WC-{datetime.now().strftime('%Y')}-{random.randint(100000, 999999)}"


# ==================== CRUD ENDPOINTS ====================

@router.get(
    "",
    response_model=InstallationListResponse,
    dependencies=[Depends(require_permissions("installation:view"))]
)
async def list_installations(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[InstallationStatus] = Query(None),
    technician_id: Optional[uuid.UUID] = Query(None),
    pincode: Optional[str] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
):
    """Get paginated list of installations."""
    query = select(Installation)
    count_query = select(func.count(Installation.id))

    if status:
        query = query.where(Installation.status == status)
        count_query = count_query.where(Installation.status == status)

    if technician_id:
        query = query.where(Installation.technician_id == technician_id)
        count_query = count_query.where(Installation.technician_id == technician_id)

    if pincode:
        query = query.where(Installation.installation_pincode == pincode)
        count_query = count_query.where(Installation.installation_pincode == pincode)

    if customer_id:
        query = query.where(Installation.customer_id == customer_id)
        count_query = count_query.where(Installation.customer_id == customer_id)

    if from_date:
        query = query.where(Installation.created_at >= datetime.combine(from_date, datetime.min.time()))
        count_query = count_query.where(Installation.created_at >= datetime.combine(from_date, datetime.min.time()))

    if to_date:
        query = query.where(Installation.created_at <= datetime.combine(to_date, datetime.max.time()))
        count_query = count_query.where(Installation.created_at <= datetime.combine(to_date, datetime.max.time()))

    if search:
        search_filter = or_(
            Installation.installation_number.ilike(f"%{search}%"),
            Installation.serial_number.ilike(f"%{search}%"),
            Installation.warranty_card_number.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * size
    query = query.order_by(Installation.created_at.desc())
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    installations = result.scalars().all()

    return InstallationListResponse(
        items=[InstallationResponse.model_validate(i) for i in installations],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get(
    "/dashboard",
    response_model=InstallationDashboardResponse,
    dependencies=[Depends(require_permissions("installation:view"))]
)
async def get_installation_dashboard(db: DB):
    """Get installation dashboard statistics."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Pending count
    pending_result = await db.execute(
        select(func.count(Installation.id)).where(
            Installation.status == InstallationStatus.PENDING
        )
    )
    total_pending = pending_result.scalar() or 0

    # Scheduled count
    scheduled_result = await db.execute(
        select(func.count(Installation.id)).where(
            Installation.status == InstallationStatus.SCHEDULED
        )
    )
    total_scheduled = scheduled_result.scalar() or 0

    # In progress count
    in_progress_result = await db.execute(
        select(func.count(Installation.id)).where(
            Installation.status == InstallationStatus.IN_PROGRESS
        )
    )
    total_in_progress = in_progress_result.scalar() or 0

    # Completed today
    completed_today_result = await db.execute(
        select(func.count(Installation.id)).where(
            and_(
                Installation.status == InstallationStatus.COMPLETED,
                Installation.installation_date == today
            )
        )
    )
    total_completed_today = completed_today_result.scalar() or 0

    # Completed this week
    completed_week_result = await db.execute(
        select(func.count(Installation.id)).where(
            and_(
                Installation.status == InstallationStatus.COMPLETED,
                Installation.installation_date >= week_start
            )
        )
    )
    total_completed_week = completed_week_result.scalar() or 0

    # Completed this month
    completed_month_result = await db.execute(
        select(func.count(Installation.id)).where(
            and_(
                Installation.status == InstallationStatus.COMPLETED,
                Installation.installation_date >= month_start
            )
        )
    )
    total_completed_month = completed_month_result.scalar() or 0

    # Average customer rating
    rating_result = await db.execute(
        select(func.avg(Installation.customer_rating)).where(
            Installation.customer_rating.isnot(None)
        )
    )
    avg_rating = rating_result.scalar() or 0.0

    # Pending assignments (pending without technician)
    pending_assignment_result = await db.execute(
        select(func.count(Installation.id)).where(
            and_(
                Installation.status.in_([InstallationStatus.PENDING, InstallationStatus.SCHEDULED]),
                Installation.technician_id.is_(None)
            )
        )
    )
    pending_assignments = pending_assignment_result.scalar() or 0

    return InstallationDashboardResponse(
        total_pending=total_pending,
        total_scheduled=total_scheduled,
        total_in_progress=total_in_progress,
        total_completed_today=total_completed_today,
        total_completed_week=total_completed_week,
        total_completed_month=total_completed_month,
        avg_completion_days=3.5,  # Placeholder - would need to calculate from actual data
        avg_customer_rating=round(float(avg_rating), 2),
        pending_assignments=pending_assignments,
    )


@router.get(
    "/{installation_id}",
    response_model=InstallationDetailResponse,
    dependencies=[Depends(require_permissions("installation:view"))]
)
async def get_installation(
    installation_id: uuid.UUID,
    db: DB,
):
    """Get installation details."""
    query = (
        select(Installation)
        .where(Installation.id == installation_id)
        .options(
            selectinload(Installation.customer),
            selectinload(Installation.product),
            selectinload(Installation.technician),
            selectinload(Installation.order),
        )
    )
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation not found"
        )

    response = InstallationResponse.model_validate(installation).model_dump()
    response["customer_name"] = installation.customer.full_name if installation.customer else None
    response["product_name"] = installation.product.name if installation.product else None
    response["technician_name"] = installation.technician.name if installation.technician else None
    response["order_number"] = installation.order.order_number if installation.order else None
    response["installation_notes"] = installation.installation_notes
    response["input_tds"] = installation.input_tds
    response["output_tds"] = installation.output_tds
    response["demo_given"] = installation.demo_given
    response["demo_notes"] = installation.demo_notes
    response["customer_feedback"] = installation.customer_feedback

    return InstallationDetailResponse(**response)


@router.post(
    "",
    response_model=InstallationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("installation:create"))]
)
async def create_installation(
    data: InstallationCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new installation request."""
    # Verify customer exists
    customer_query = select(Customer).where(Customer.id == data.customer_id)
    customer_result = await db.execute(customer_query)
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Verify product exists
    product_query = select(Product).where(Product.id == data.product_id)
    product_result = await db.execute(product_query)
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    installation = Installation(
        installation_number=generate_installation_number(),
        status=InstallationStatus.PENDING,
        customer_id=data.customer_id,
        order_id=data.order_id,
        product_id=data.product_id,
        serial_number=data.serial_number,
        installation_pincode=data.installation_pincode,
        installation_city=data.installation_city,
        installation_address=data.installation_address,
        preferred_date=data.preferred_date,
        preferred_time_slot=data.preferred_time_slot,
        notes=data.notes,
        created_by=current_user.id,
    )

    db.add(installation)
    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


@router.put(
    "/{installation_id}",
    response_model=InstallationResponse,
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def update_installation(
    installation_id: uuid.UUID,
    data: InstallationUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update installation details."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(installation, field, value)

    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


# ==================== WORKFLOW ENDPOINTS ====================

@router.post(
    "/{installation_id}/schedule",
    response_model=InstallationResponse,
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def schedule_installation(
    installation_id: uuid.UUID,
    data: InstallationScheduleRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Schedule an installation."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    if installation.status not in [InstallationStatus.PENDING, InstallationStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot schedule installation in {installation.status} status"
        )

    installation.scheduled_date = data.scheduled_date
    installation.scheduled_time_slot = data.scheduled_time_slot
    installation.status = InstallationStatus.SCHEDULED

    if data.technician_id:
        # Verify technician exists and is active
        tech_query = select(Technician).where(
            and_(
                Technician.id == data.technician_id,
                Technician.status == TechnicianStatus.ACTIVE
            )
        )
        tech_result = await db.execute(tech_query)
        technician = tech_result.scalar_one_or_none()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found or not active")

        installation.technician_id = data.technician_id
        installation.assigned_at = datetime.utcnow()

    if data.notes:
        installation.notes = f"{installation.notes or ''}\n[Scheduled] {data.notes}".strip()

    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


@router.post(
    "/{installation_id}/assign",
    response_model=InstallationResponse,
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def assign_technician(
    installation_id: uuid.UUID,
    data: InstallationAssignRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Assign a technician to installation."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    # Verify technician exists and is active
    tech_query = select(Technician).where(
        and_(
            Technician.id == data.technician_id,
            Technician.status == TechnicianStatus.ACTIVE
        )
    )
    tech_result = await db.execute(tech_query)
    technician = tech_result.scalar_one_or_none()
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found or not active")

    installation.technician_id = data.technician_id
    installation.assigned_at = datetime.utcnow()

    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


@router.post(
    "/{installation_id}/start",
    response_model=InstallationResponse,
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def start_installation(
    installation_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Mark installation as started (in progress)."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    if installation.status not in [InstallationStatus.PENDING, InstallationStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start installation in {installation.status} status"
        )

    installation.status = InstallationStatus.IN_PROGRESS
    installation.started_at = datetime.utcnow()

    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


@router.post(
    "/{installation_id}/complete",
    response_model=InstallationResponse,
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def complete_installation(
    installation_id: uuid.UUID,
    data: InstallationCompleteRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Complete an installation with all details."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    if installation.status == InstallationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Installation already completed")

    now = datetime.utcnow()
    today = date.today()

    # Update installation details
    installation.status = InstallationStatus.COMPLETED
    installation.completed_at = now
    installation.installation_date = today
    installation.installation_notes = data.installation_notes
    installation.pre_installation_checklist = data.pre_installation_checklist
    installation.post_installation_checklist = data.post_installation_checklist
    installation.installation_photos = data.installation_photos
    installation.accessories_used = data.accessories_used
    installation.input_tds = data.input_tds
    installation.output_tds = data.output_tds
    installation.customer_signature_url = data.customer_signature_url
    installation.customer_feedback = data.customer_feedback
    installation.customer_rating = data.customer_rating
    installation.demo_given = data.demo_given
    installation.demo_notes = data.demo_notes

    # Set warranty dates
    warranty_months = data.warranty_months or 12
    installation.warranty_months = warranty_months
    installation.warranty_start_date = today
    installation.warranty_end_date = today + timedelta(days=warranty_months * 30)
    installation.warranty_card_number = generate_warranty_card_number()

    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


@router.post(
    "/{installation_id}/cancel",
    response_model=InstallationResponse,
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def cancel_installation(
    installation_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    reason: str = Query(..., min_length=5),
):
    """Cancel an installation."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    if installation.status == InstallationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel completed installation")

    installation.status = InstallationStatus.CANCELLED
    installation.notes = f"{installation.notes or ''}\n[Cancelled] {reason}".strip()

    await db.commit()
    await db.refresh(installation)

    return InstallationResponse.model_validate(installation)


# ==================== WARRANTY ENDPOINTS ====================

@router.get(
    "/{installation_id}/warranty",
    dependencies=[Depends(require_permissions("installation:view"))]
)
async def get_warranty_status(
    installation_id: uuid.UUID,
    db: DB,
):
    """Get warranty status for an installation."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    return {
        "installation_id": installation.id,
        "installation_number": installation.installation_number,
        "serial_number": installation.serial_number,
        "warranty_card_number": installation.warranty_card_number,
        "warranty_start_date": installation.warranty_start_date,
        "warranty_end_date": installation.warranty_end_date,
        "warranty_months": installation.warranty_months,
        "extended_warranty_months": installation.extended_warranty_months,
        "is_under_warranty": installation.is_under_warranty,
        "days_remaining": installation.warranty_days_remaining,
    }


@router.post(
    "/{installation_id}/extend-warranty",
    dependencies=[Depends(require_permissions("installation:update"))]
)
async def extend_warranty(
    installation_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    months: int = Query(..., ge=1, le=60),
):
    """Extend warranty for an installation."""
    query = select(Installation).where(Installation.id == installation_id)
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    if not installation.warranty_end_date:
        raise HTTPException(status_code=400, detail="Installation has no warranty set")

    # Extend warranty
    installation.extended_warranty_months = (installation.extended_warranty_months or 0) + months
    installation.warranty_end_date = installation.warranty_end_date + timedelta(days=months * 30)

    await db.commit()
    await db.refresh(installation)

    return {
        "success": True,
        "installation_id": installation.id,
        "new_warranty_end_date": installation.warranty_end_date,
        "total_warranty_months": installation.warranty_months + installation.extended_warranty_months,
        "message": f"Warranty extended by {months} months",
    }


# ==================== LOOKUP ENDPOINTS ====================

@router.get(
    "/lookup/serial/{serial_number}",
    response_model=InstallationDetailResponse,
    dependencies=[Depends(require_permissions("installation:view"))]
)
async def lookup_by_serial(
    serial_number: str,
    db: DB,
):
    """Lookup installation by serial number."""
    query = (
        select(Installation)
        .where(Installation.serial_number == serial_number)
        .options(
            selectinload(Installation.customer),
            selectinload(Installation.product),
            selectinload(Installation.technician),
        )
    )
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found for this serial number")

    response = InstallationResponse.model_validate(installation).model_dump()
    response["customer_name"] = installation.customer.full_name if installation.customer else None
    response["product_name"] = installation.product.name if installation.product else None
    response["technician_name"] = installation.technician.name if installation.technician else None

    return InstallationDetailResponse(**response)


@router.get(
    "/lookup/warranty/{warranty_card}",
    dependencies=[Depends(require_permissions("installation:view"))]
)
async def lookup_by_warranty_card(
    warranty_card: str,
    db: DB,
):
    """Lookup installation by warranty card number."""
    query = (
        select(Installation)
        .where(Installation.warranty_card_number == warranty_card)
        .options(
            selectinload(Installation.customer),
            selectinload(Installation.product),
        )
    )
    result = await db.execute(query)
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found for this warranty card")

    return {
        "installation_id": installation.id,
        "installation_number": installation.installation_number,
        "serial_number": installation.serial_number,
        "product_name": installation.product.name if installation.product else None,
        "customer_name": installation.customer.full_name if installation.customer else None,
        "warranty_start_date": installation.warranty_start_date,
        "warranty_end_date": installation.warranty_end_date,
        "is_under_warranty": installation.is_under_warranty,
        "days_remaining": installation.warranty_days_remaining,
    }
