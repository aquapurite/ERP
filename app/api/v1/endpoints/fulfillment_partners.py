"""Fulfillment Partners CRUD endpoints (SUPER_ADMIN only)."""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy import select, func, desc

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.fulfillment_partner import FulfillmentPartner
from app.models.warehouse import Warehouse
from app.schemas.fulfillment_partner import (
    FulfillmentPartnerCreate,
    FulfillmentPartnerUpdate,
    FulfillmentPartnerResponse,
    FulfillmentPartnerListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Fulfillment Partners"])


@router.get(
    "/",
    response_model=FulfillmentPartnerListResponse,
    dependencies=[Depends(require_permissions("logistics:view"))],
)
async def list_fulfillment_partners(
    db: DB,
    user: CurrentUser,
    is_active: Optional[bool] = None,
    provider_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all fulfillment partners."""
    query = select(FulfillmentPartner)
    count_query = select(func.count(FulfillmentPartner.id))

    if is_active is not None:
        query = query.where(FulfillmentPartner.is_active == is_active)
        count_query = count_query.where(FulfillmentPartner.is_active == is_active)
    if provider_type:
        query = query.where(FulfillmentPartner.provider_type == provider_type)
        count_query = count_query.where(FulfillmentPartner.provider_type == provider_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(desc(FulfillmentPartner.created_at)).offset(skip).limit(limit)
    )
    partners = result.scalars().all()

    # Get warehouse counts
    wh_counts = {}
    if partners:
        partner_ids = [p.id for p in partners]
        wh_result = await db.execute(
            select(
                Warehouse.fulfillment_partner_id,
                func.count(Warehouse.id).label("cnt"),
            )
            .where(Warehouse.fulfillment_partner_id.in_(partner_ids))
            .group_by(Warehouse.fulfillment_partner_id)
        )
        for row in wh_result:
            wh_counts[row[0]] = row[1]

    items = []
    for p in partners:
        resp = FulfillmentPartnerResponse.model_validate(p)
        resp.warehouse_count = wh_counts.get(p.id, 0)
        items.append(resp)

    return FulfillmentPartnerListResponse(items=items, total=total)


@router.get(
    "/{partner_id}",
    response_model=FulfillmentPartnerResponse,
    dependencies=[Depends(require_permissions("logistics:view"))],
)
async def get_fulfillment_partner(partner_id: uuid.UUID, db: DB, user: CurrentUser):
    """Get a fulfillment partner by ID."""
    result = await db.execute(
        select(FulfillmentPartner).where(FulfillmentPartner.id == partner_id)
    )
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Fulfillment partner not found")

    wh_count = (
        await db.execute(
            select(func.count(Warehouse.id)).where(
                Warehouse.fulfillment_partner_id == partner_id
            )
        )
    ).scalar() or 0

    resp = FulfillmentPartnerResponse.model_validate(partner)
    resp.warehouse_count = wh_count
    return resp


@router.post(
    "/",
    response_model=FulfillmentPartnerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("settings:manage"))],
)
async def create_fulfillment_partner(
    payload: FulfillmentPartnerCreate, db: DB, user: CurrentUser
):
    """Create a new fulfillment partner (SUPER_ADMIN)."""
    # Check unique code
    existing = await db.execute(
        select(FulfillmentPartner).where(FulfillmentPartner.code == payload.code.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Partner with code '{payload.code}' already exists"
        )

    partner = FulfillmentPartner(
        code=payload.code.upper(),
        name=payload.name,
        provider_type=payload.provider_type,
        api_base_url=payload.api_base_url,
        api_key=payload.api_key,
        auth_config=payload.auth_config or {},
        webhook_secret=payload.webhook_secret,
        is_active=payload.is_active,
        config=payload.config or {},
    )
    db.add(partner)
    await db.flush()
    await db.refresh(partner)
    logger.info("Created fulfillment partner: %s (%s)", partner.code, partner.id)
    return FulfillmentPartnerResponse.model_validate(partner)


@router.patch(
    "/{partner_id}",
    response_model=FulfillmentPartnerResponse,
    dependencies=[Depends(require_permissions("settings:manage"))],
)
async def update_fulfillment_partner(
    partner_id: uuid.UUID,
    payload: FulfillmentPartnerUpdate,
    db: DB,
    user: CurrentUser,
):
    """Update a fulfillment partner (SUPER_ADMIN)."""
    result = await db.execute(
        select(FulfillmentPartner).where(FulfillmentPartner.id == partner_id)
    )
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Fulfillment partner not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partner, field, value)

    await db.flush()
    await db.refresh(partner)
    logger.info("Updated fulfillment partner: %s", partner.code)
    return FulfillmentPartnerResponse.model_validate(partner)


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("settings:manage"))],
)
async def delete_fulfillment_partner(
    partner_id: uuid.UUID, db: DB, user: CurrentUser
):
    """Delete a fulfillment partner (only if no warehouses linked)."""
    result = await db.execute(
        select(FulfillmentPartner).where(FulfillmentPartner.id == partner_id)
    )
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Fulfillment partner not found")

    wh_count = (
        await db.execute(
            select(func.count(Warehouse.id)).where(
                Warehouse.fulfillment_partner_id == partner_id
            )
        )
    ).scalar() or 0

    if wh_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete: {wh_count} warehouse(s) still linked to this partner",
        )

    await db.delete(partner)
    await db.flush()
    logger.info("Deleted fulfillment partner: %s", partner.code)
