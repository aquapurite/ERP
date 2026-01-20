"""Technician API endpoints."""
from typing import Optional
import uuid
from math import ceil

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.technician import Technician, TechnicianStatus, TechnicianType, SkillLevel
from app.schemas.technician import (
    TechnicianCreate,
    TechnicianUpdate,
    TechnicianResponse,
    TechnicianDetail,
    TechnicianBrief,
    TechnicianListResponse,
    TechnicianLocationUpdate,
)
from datetime import datetime


router = APIRouter(tags=["Technicians"])


async def _generate_employee_code(db) -> str:
    """Generate unique employee code."""
    query = select(func.count()).select_from(Technician)
    count = await db.scalar(query)
    return f"TECH-{(count or 0) + 1:04d}"


@router.get(
    "",
    response_model=TechnicianListResponse,
    dependencies=[Depends(require_permissions("service:view"))]
)
async def list_technicians(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[TechnicianStatus] = Query(None),
    technician_type: Optional[TechnicianType] = Query(None),
    skill_level: Optional[SkillLevel] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None),
    is_available: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
):
    """
    Get paginated list of technicians.
    Requires: service:view permission
    """
    query = select(Technician)

    conditions = []
    if status:
        conditions.append(Technician.status == status)
    if technician_type:
        conditions.append(Technician.technician_type == technician_type)
    if skill_level:
        conditions.append(Technician.skill_level == skill_level)
    if region_id:
        conditions.append(Technician.region_id == region_id)
    if is_available is not None:
        conditions.append(Technician.is_available == is_available)
    if search:
        conditions.append(
            or_(
                Technician.first_name.ilike(f"%{search}%"),
                Technician.last_name.ilike(f"%{search}%"),
                Technician.phone.ilike(f"%{search}%"),
                Technician.employee_code.ilike(f"%{search}%"),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    skip = (page - 1) * size
    query = query.order_by(Technician.employee_code).offset(skip).limit(size)
    result = await db.execute(query)
    technicians = result.scalars().all()

    return TechnicianListResponse(
        items=[TechnicianResponse.model_validate(t) for t in technicians],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get(
    "/dropdown",
    response_model=list[TechnicianBrief],
    dependencies=[Depends(require_permissions("service:view"))]
)
async def get_technicians_dropdown(
    db: DB,
    region_id: Optional[uuid.UUID] = Query(None),
    pincode: Optional[str] = Query(None),
    is_available: bool = Query(True),
):
    """Get available technicians for dropdown."""
    query = select(Technician).where(
        and_(
            Technician.status == TechnicianStatus.ACTIVE,
            Technician.is_available == is_available,
        )
    )

    if region_id:
        query = query.where(Technician.region_id == region_id)

    query = query.order_by(Technician.average_rating.desc()).limit(50)
    result = await db.execute(query)
    technicians = result.scalars().all()

    # Filter by serviceable pincode if provided
    if pincode:
        technicians = [
            t for t in technicians
            if not t.service_pincodes or pincode in t.service_pincodes
        ]

    return [TechnicianBrief.model_validate(t) for t in technicians]


@router.get(
    "/{technician_id}",
    response_model=TechnicianDetail,
    dependencies=[Depends(require_permissions("service:view"))]
)
async def get_technician(
    technician_id: uuid.UUID,
    db: DB,
):
    """Get technician by ID."""
    query = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(query)
    technician = result.scalar_one_or_none()

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found"
        )

    return TechnicianDetail.model_validate(technician)


@router.post(
    "",
    response_model=TechnicianDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("service:create"))]
)
async def create_technician(
    data: TechnicianCreate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Create a new technician.
    Requires: service:create permission
    """
    # Check for duplicate phone
    existing_query = select(Technician).where(Technician.phone == data.phone)
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Technician with this phone number already exists"
        )

    # Generate employee code
    employee_code = await _generate_employee_code(db)

    technician = Technician(
        employee_code=employee_code,
        **data.model_dump(),
    )
    db.add(technician)
    await db.commit()
    await db.refresh(technician)

    return TechnicianDetail.model_validate(technician)


@router.put(
    "/{technician_id}",
    response_model=TechnicianDetail,
    dependencies=[Depends(require_permissions("service:update"))]
)
async def update_technician(
    technician_id: uuid.UUID,
    data: TechnicianUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Update a technician.
    Requires: service:update permission
    """
    query = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(query)
    technician = result.scalar_one_or_none()

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(technician, key):
            setattr(technician, key, value)

    await db.commit()
    await db.refresh(technician)
    return TechnicianDetail.model_validate(technician)


@router.put(
    "/{technician_id}/location",
    response_model=TechnicianBrief,
    dependencies=[Depends(require_permissions("service:update"))]
)
async def update_technician_location(
    technician_id: uuid.UUID,
    data: TechnicianLocationUpdate,
    db: DB,
):
    """Update technician's current location."""
    query = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(query)
    technician = result.scalar_one_or_none()

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found"
        )

    technician.current_location_lat = data.latitude
    technician.current_location_lng = data.longitude
    technician.location_updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(technician)
    return TechnicianBrief.model_validate(technician)


@router.put(
    "/{technician_id}/availability",
    response_model=TechnicianBrief,
    dependencies=[Depends(require_permissions("service:update"))]
)
async def toggle_availability(
    technician_id: uuid.UUID,
    is_available: bool,
    db: DB,
):
    """Toggle technician availability."""
    query = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(query)
    technician = result.scalar_one_or_none()

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found"
        )

    technician.is_available = is_available
    await db.commit()
    await db.refresh(technician)
    return TechnicianBrief.model_validate(technician)


@router.delete(
    "/{technician_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("service:delete"))]
)
async def deactivate_technician(
    technician_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Deactivate a technician.
    Requires: service:delete permission
    """
    query = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(query)
    technician = result.scalar_one_or_none()

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found"
        )

    technician.status = TechnicianStatus.INACTIVE.value
    technician.is_available = False
    await db.commit()
