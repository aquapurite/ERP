"""API endpoints for Multi-Channel Commerce (D2C, Marketplaces, etc.)."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.channel import (
    SalesChannel, ChannelType, ChannelStatus,
    ChannelPricing, ChannelInventory, ChannelOrder,
)
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.user import User
from app.schemas.channel import (
    # Channel
    SalesChannelCreate, SalesChannelUpdate, SalesChannelResponse, SalesChannelListResponse,
    # Pricing
    ChannelPricingCreate, ChannelPricingUpdate, ChannelPricingResponse, ChannelPricingListResponse,
    # Inventory
    ChannelInventoryCreate, ChannelInventoryUpdate, ChannelInventoryResponse, ChannelInventoryListResponse,
    # Channel Order
    ChannelOrderCreate, ChannelOrderUpdate, ChannelOrderResponse, ChannelOrderListResponse,
    # Sync
    InventorySyncRequest, PriceSyncRequest, OrderSyncResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from app.services.audit_service import AuditService

router = APIRouter()


# ==================== Sales Channels ====================

@router.post("", response_model=SalesChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_sales_channel(
    channel_in: SalesChannelCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new sales channel."""
    # Generate channel code if not provided
    count_result = await db.execute(select(func.count(SalesChannel.id)))
    count = count_result.scalar() or 0

    prefix_map = {
        ChannelType.D2C: "D2C",
        ChannelType.D2C_WEBSITE: "D2C",
        ChannelType.D2C_APP: "D2C",
        ChannelType.MARKETPLACE: "MKT",
        ChannelType.AMAZON: "AMZ",
        ChannelType.FLIPKART: "FLK",
        ChannelType.MYNTRA: "MYN",
        ChannelType.MEESHO: "MSH",
        ChannelType.JIOMART: "JIO",
        ChannelType.TATACLIQ: "TTA",
        ChannelType.AJIO: "AJI",
        ChannelType.NYKAA: "NYK",
        ChannelType.B2B: "B2B",
        ChannelType.B2B_PORTAL: "B2B",
        ChannelType.DEALER: "DLR",
        ChannelType.DEALER_PORTAL: "DLR",
        ChannelType.OFFLINE: "OFL",
        ChannelType.RETAIL_STORE: "RET",
        ChannelType.OTHER: "OTH",
    }
    prefix = prefix_map.get(channel_in.channel_type, "CHN")

    # Use provided code or generate one
    channel_code = channel_in.code if channel_in.code else f"{prefix}-{str(count + 1).zfill(3)}"

    # Use name as display_name if not provided
    display_name = channel_in.display_name if channel_in.display_name else channel_in.name

    # Prepare channel data
    channel_data = channel_in.model_dump(exclude={'code', 'display_name', 'api_key', 'api_secret', 'config'})

    channel = SalesChannel(
        code=channel_code,
        display_name=display_name,
        **channel_data,
    )

    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return channel


@router.get("", response_model=SalesChannelListResponse)
async def list_sales_channels(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    channel_type: Optional[ChannelType] = None,
    status: Optional[ChannelStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List sales channels."""
    query = select(SalesChannel)
    count_query = select(func.count(SalesChannel.id))

    filters = []
    if channel_type:
        filters.append(SalesChannel.channel_type == channel_type)
    if status:
        filters.append(SalesChannel.status == status)
    if search:
        filters.append(or_(
            SalesChannel.name.ilike(f"%{search}%"),
            SalesChannel.channel_code.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    skip = (page - 1) * size
    query = query.order_by(SalesChannel.created_at.desc()).offset(skip).limit(size)
    result = await db.execute(query)
    channels = result.scalars().all()

    return SalesChannelListResponse(
        items=[SalesChannelResponse.model_validate(c) for c in channels],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1
    )


@router.get("/dropdown")
async def get_channels_dropdown(
    db: DB,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
):
    """Get channels for dropdown selection."""
    query = select(SalesChannel)

    if active_only:
        query = query.where(SalesChannel.status == ChannelStatus.ACTIVE)

    query = query.order_by(SalesChannel.name)
    result = await db.execute(query)
    channels = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "code": c.channel_code,
            "name": c.name,
            "type": c.channel_type.value,
        }
        for c in channels
    ]


# ==================== Reports (must be before /{channel_id}) ====================

@router.get("/reports/summary")
async def get_channel_summary(
    start_date: date,
    end_date: date,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get sales summary by channel."""
    # Orders by channel
    orders_query = select(
        SalesChannel.name,
        SalesChannel.channel_type,
        func.count(ChannelOrder.id).label("order_count"),
        func.coalesce(func.sum(ChannelOrder.order_value), 0).label("order_value"),
    ).join(
        ChannelOrder, ChannelOrder.channel_id == SalesChannel.id
    ).where(
        and_(
            ChannelOrder.channel_order_date >= start_date,
            ChannelOrder.channel_order_date <= end_date,
        )
    ).group_by(SalesChannel.id, SalesChannel.name, SalesChannel.channel_type)

    orders_result = await db.execute(orders_query)
    by_channel = [
        {
            "channel_name": row.name,
            "channel_type": row.channel_type.value if row.channel_type else None,
            "order_count": row.order_count,
            "order_value": float(row.order_value),
        }
        for row in orders_result.all()
    ]

    # Totals
    total_query = select(
        func.count(ChannelOrder.id).label("total_orders"),
        func.coalesce(func.sum(ChannelOrder.order_value), 0).label("total_value"),
    ).where(
        and_(
            ChannelOrder.channel_order_date >= start_date,
            ChannelOrder.channel_order_date <= end_date,
        )
    )
    total_result = await db.execute(total_query)
    totals = total_result.one()

    # Channel counts
    channel_counts = await db.execute(
        select(
            SalesChannel.status,
            func.count(SalesChannel.id).label("count"),
        ).group_by(SalesChannel.status)
    )
    status_counts = {
        row.status.value: row.count
        for row in channel_counts.all()
    }

    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "by_channel": by_channel,
        "totals": {
            "order_count": totals.total_orders,
            "order_value": float(totals.total_value),
        },
        "channels": {
            "total": sum(status_counts.values()),
            "by_status": status_counts,
        }
    }


@router.get("/reports/inventory-status")
async def get_channel_inventory_status(
    db: DB,
    channel_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Get inventory sync status across channels."""
    query = select(
        SalesChannel.id,
        SalesChannel.name,
        func.count(ChannelInventory.id).label("products_allocated"),
        func.coalesce(func.sum(ChannelInventory.allocated_quantity), 0).label("total_allocated"),
        func.coalesce(func.sum(ChannelInventory.available_quantity), 0).label("total_available"),
    ).outerjoin(
        ChannelInventory, ChannelInventory.channel_id == SalesChannel.id
    ).group_by(SalesChannel.id, SalesChannel.name)

    if channel_id:
        query = query.where(SalesChannel.id == channel_id)

    result = await db.execute(query)
    channels = result.all()

    return {
        "channels": [
            {
                "channel_id": str(row.id),
                "channel_name": row.name,
                "products_allocated": row.products_allocated,
                "total_allocated": int(row.total_allocated),
                "total_available": int(row.total_available),
            }
            for row in channels
        ]
    }


# ==================== Global Channel Inventory (All Channels) ====================

@router.get("/inventory")
async def list_all_channel_inventory(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    channel_id: Optional[UUID] = None,
    sync_status: Optional[str] = None,
    product_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """List channel inventory across all channels with optional filters."""
    # Base query with joins
    query = (
        select(ChannelInventory)
        .options(
            selectinload(ChannelInventory.channel),
            selectinload(ChannelInventory.product),
            selectinload(ChannelInventory.warehouse),
        )
    )

    # Apply filters
    conditions = []
    if channel_id:
        conditions.append(ChannelInventory.channel_id == channel_id)
    if product_id:
        conditions.append(ChannelInventory.product_id == product_id)
    if sync_status:
        # Map sync status to conditions
        if sync_status == "SYNCED":
            conditions.append(ChannelInventory.last_synced_at.isnot(None))
            conditions.append(ChannelInventory.is_active == True)
        elif sync_status == "PENDING":
            conditions.append(ChannelInventory.last_synced_at.is_(None))
        elif sync_status == "OUT_OF_SYNC":
            # Items where marketplace_quantity differs from available
            conditions.append(ChannelInventory.marketplace_quantity != ChannelInventory.available_quantity)
        elif sync_status == "FAILED":
            conditions.append(ChannelInventory.is_active == False)

    if conditions:
        query = query.where(and_(*conditions))

    # Count total
    count_query = select(func.count(ChannelInventory.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(ChannelInventory.updated_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    # Transform to response format
    inventory_items = []
    for inv in items:
        # Determine sync status
        if not inv.is_active:
            status = "FAILED"
        elif inv.last_synced_at is None:
            status = "PENDING"
        elif inv.marketplace_quantity != inv.available_quantity:
            status = "OUT_OF_SYNC"
        else:
            status = "SYNCED"

        inventory_items.append({
            "id": str(inv.id),
            "channel_id": str(inv.channel_id),
            "channel_name": inv.channel.name if inv.channel else "Unknown",
            "product_id": str(inv.product_id),
            "product_name": inv.product.name if inv.product else "Unknown",
            "product_sku": inv.product.sku if inv.product else "",
            "warehouse_id": str(inv.warehouse_id) if inv.warehouse_id else None,
            "warehouse_name": inv.warehouse.name if inv.warehouse else None,
            "allocated_quantity": inv.allocated_quantity or 0,
            "warehouse_quantity": inv.allocated_quantity or 0,  # Alias for frontend
            "channel_quantity": inv.marketplace_quantity or 0,
            "reserved_quantity": inv.reserved_quantity or 0,
            "available_quantity": inv.available_quantity or 0,
            "buffer_stock": inv.buffer_quantity or 0,
            "sync_status": status,
            "last_synced_at": inv.last_synced_at.isoformat() if inv.last_synced_at else None,
            "is_active": inv.is_active,
        })

    return {
        "items": inventory_items,
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if size > 0 else 0,
    }


@router.get("/inventory/stats")
async def get_channel_inventory_stats(
    db: DB,
    channel_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Get channel inventory statistics."""
    # Base condition
    conditions = []
    if channel_id:
        conditions.append(ChannelInventory.channel_id == channel_id)

    # Total products mapped
    total_query = select(func.count(ChannelInventory.id))
    if conditions:
        total_query = total_query.where(and_(*conditions))
    total_result = await db.execute(total_query)
    total_products = total_result.scalar() or 0

    # Synced count (has last_synced_at and is_active)
    synced_query = select(func.count(ChannelInventory.id)).where(
        and_(
            ChannelInventory.last_synced_at.isnot(None),
            ChannelInventory.is_active == True,
            ChannelInventory.marketplace_quantity == ChannelInventory.available_quantity,
            *conditions
        )
    )
    synced_result = await db.execute(synced_query)
    synced_count = synced_result.scalar() or 0

    # Out of sync count
    out_of_sync_query = select(func.count(ChannelInventory.id)).where(
        and_(
            ChannelInventory.last_synced_at.isnot(None),
            ChannelInventory.is_active == True,
            ChannelInventory.marketplace_quantity != ChannelInventory.available_quantity,
            *conditions
        )
    )
    out_of_sync_result = await db.execute(out_of_sync_query)
    out_of_sync_count = out_of_sync_result.scalar() or 0

    # Failed count (inactive)
    failed_query = select(func.count(ChannelInventory.id)).where(
        and_(
            ChannelInventory.is_active == False,
            *conditions
        )
    )
    failed_result = await db.execute(failed_query)
    failed_count = failed_result.scalar() or 0

    return {
        "total_products": total_products,
        "synced_count": synced_count,
        "out_of_sync_count": out_of_sync_count,
        "failed_count": failed_count,
    }


@router.post("/inventory/{inventory_id}/sync")
async def sync_single_inventory(
    inventory_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Sync a single inventory item to its channel."""
    result = await db.execute(
        select(ChannelInventory)
        .options(selectinload(ChannelInventory.channel))
        .where(ChannelInventory.id == inventory_id)
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(status_code=404, detail="Channel inventory not found")

    # In a real implementation, this would call the marketplace API
    # For now, we simulate sync by updating marketplace_quantity to match available
    inventory.marketplace_quantity = inventory.available_quantity
    inventory.last_synced_at = datetime.utcnow()
    inventory.is_active = True

    await db.commit()
    await db.refresh(inventory)

    return {
        "success": True,
        "message": "Inventory synced successfully",
        "inventory_id": str(inventory.id),
        "synced_quantity": inventory.marketplace_quantity,
    }


@router.post("/inventory/sync-all")
async def sync_all_inventory(
    db: DB,
    channel_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Sync all inventory items to their channels."""
    # Build query
    query = select(ChannelInventory).where(ChannelInventory.is_active == True)
    if channel_id:
        query = query.where(ChannelInventory.channel_id == channel_id)

    result = await db.execute(query)
    items = result.scalars().all()

    synced_count = 0
    failed_count = 0

    for item in items:
        try:
            # In real implementation, call marketplace API here
            item.marketplace_quantity = item.available_quantity
            item.last_synced_at = datetime.utcnow()
            synced_count += 1
        except Exception:
            failed_count += 1

    await db.commit()

    return {
        "success": True,
        "message": f"Synced {synced_count} items, {failed_count} failed",
        "synced_count": synced_count,
        "failed_count": failed_count,
    }


@router.put("/inventory/{inventory_id}/buffer")
async def update_inventory_buffer(
    inventory_id: UUID,
    db: DB,
    buffer_stock: int = Query(..., ge=0, description="Buffer stock quantity"),
    current_user: User = Depends(get_current_user),
):
    """Update buffer stock for a channel inventory item."""
    result = await db.execute(
        select(ChannelInventory).where(ChannelInventory.id == inventory_id)
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(status_code=404, detail="Channel inventory not found")

    inventory.buffer_quantity = buffer_stock
    # Recalculate available quantity
    inventory.available_quantity = max(0, (inventory.allocated_quantity or 0) - buffer_stock - (inventory.reserved_quantity or 0))

    await db.commit()
    await db.refresh(inventory)

    return {
        "success": True,
        "message": "Buffer stock updated successfully",
        "inventory_id": str(inventory.id),
        "buffer_stock": inventory.buffer_quantity,
        "available_quantity": inventory.available_quantity,
    }


# ==================== Single Channel Operations ====================

@router.get("/{channel_id}", response_model=SalesChannelResponse)
async def get_sales_channel(
    channel_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get sales channel by ID."""
    result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    return channel


@router.put("/{channel_id}", response_model=SalesChannelResponse)
async def update_sales_channel(
    channel_id: UUID,
    channel_in: SalesChannelUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update sales channel."""
    result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    update_data = channel_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales_channel(
    channel_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete a sales channel (soft delete by setting status to INACTIVE)."""
    result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # Check if channel has active orders
    orders_result = await db.execute(
        select(func.count(ChannelOrder.id)).where(
            and_(
                ChannelOrder.channel_id == channel_id,
                ChannelOrder.channel_status.in_(["PENDING", "PROCESSING", "SHIPPED"])
            )
        )
    )
    active_orders = orders_result.scalar() or 0

    if active_orders > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete channel with {active_orders} active orders"
        )

    channel.status = ChannelStatus.INACTIVE

    await db.commit()
    return None


@router.post("/{channel_id}/activate", response_model=SalesChannelResponse)
async def activate_channel(
    channel_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Activate a sales channel."""
    result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    channel.status = ChannelStatus.ACTIVE

    await db.commit()
    await db.refresh(channel)

    return channel


@router.post("/{channel_id}/deactivate", response_model=SalesChannelResponse)
async def deactivate_channel(
    channel_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Deactivate a sales channel."""
    result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    channel.status = ChannelStatus.INACTIVE

    await db.commit()
    await db.refresh(channel)

    return channel


# ==================== Channel Pricing ====================

@router.get("/{channel_id}/pricing", response_model=ChannelPricingListResponse)
async def get_channel_pricing(
    channel_id: UUID,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    product_id: Optional[UUID] = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
):
    """Get pricing for a sales channel."""
    query = select(ChannelPricing).where(ChannelPricing.channel_id == channel_id)
    count_query = select(func.count(ChannelPricing.id)).where(
        ChannelPricing.channel_id == channel_id
    )

    if product_id:
        query = query.where(ChannelPricing.product_id == product_id)
        count_query = count_query.where(ChannelPricing.product_id == product_id)
    if is_active is not None:
        query = query.where(ChannelPricing.is_active == is_active)
        count_query = count_query.where(ChannelPricing.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    pricing = result.scalars().all()

    return ChannelPricingListResponse(
        items=[ChannelPricingResponse.model_validate(p) for p in pricing],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/{channel_id}/pricing", response_model=ChannelPricingResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_pricing(
    channel_id: UUID,
    pricing_in: ChannelPricingCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create channel-specific pricing for a product."""
    # Verify channel
    channel_result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    if not channel_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # Check for existing pricing
    existing = await db.execute(
        select(ChannelPricing).where(
            and_(
                ChannelPricing.channel_id == channel_id,
                ChannelPricing.product_id == pricing_in.product_id,
                ChannelPricing.variant_id == pricing_in.variant_id,
                ChannelPricing.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Active pricing already exists for this product on this channel"
        )

    pricing = ChannelPricing(
        channel_id=channel_id,
        **pricing_in.model_dump(),
    )

    db.add(pricing)
    await db.commit()
    await db.refresh(pricing)

    return pricing


@router.put("/{channel_id}/pricing/{pricing_id}", response_model=ChannelPricingResponse)
async def update_channel_pricing(
    channel_id: UUID,
    pricing_id: UUID,
    pricing_in: ChannelPricingUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update channel pricing."""
    result = await db.execute(
        select(ChannelPricing).where(
            and_(
                ChannelPricing.id == pricing_id,
                ChannelPricing.channel_id == channel_id,
            )
        )
    )
    pricing = result.scalar_one_or_none()

    if not pricing:
        raise HTTPException(status_code=404, detail="Channel pricing not found")

    update_data = pricing_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pricing, field, value)

    await db.commit()
    await db.refresh(pricing)

    return pricing


@router.delete("/{channel_id}/pricing/{pricing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_pricing(
    channel_id: UUID,
    pricing_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete channel pricing."""
    result = await db.execute(
        select(ChannelPricing).where(
            and_(
                ChannelPricing.id == pricing_id,
                ChannelPricing.channel_id == channel_id,
            )
        )
    )
    pricing = result.scalar_one_or_none()

    if not pricing:
        raise HTTPException(status_code=404, detail="Channel pricing not found")

    await db.delete(pricing)
    await db.commit()
    return None


@router.post("/{channel_id}/pricing/sync")
async def sync_channel_pricing(
    channel_id: UUID,
    sync_request: PriceSyncRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Sync pricing to channel (push to marketplace API)."""
    # Verify channel
    channel_result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = channel_result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # Get pricing to sync
    query = select(ChannelPricing).where(
        and_(
            ChannelPricing.channel_id == channel_id,
            ChannelPricing.is_active == True,
        )
    )

    if sync_request.product_ids:
        query = query.where(ChannelPricing.product_id.in_(sync_request.product_ids))

    result = await db.execute(query)
    pricing_list = result.scalars().all()

    # TODO: Integrate with actual marketplace APIs
    # For now, mark as synced
    synced_count = 0
    for pricing in pricing_list:
        pricing.last_synced_at = datetime.utcnow()
        pricing.sync_status = "SYNCED"
        synced_count += 1

    await db.commit()

    return {
        "channel_id": str(channel_id),
        "channel_name": channel.name,
        "synced_count": synced_count,
        "sync_time": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
    }


# ==================== Channel Inventory ====================

@router.get("/{channel_id}/inventory", response_model=ChannelInventoryListResponse)
async def get_channel_inventory(
    channel_id: UUID,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    product_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Get inventory allocation for a channel."""
    query = select(ChannelInventory).where(ChannelInventory.channel_id == channel_id)
    count_query = select(func.count(ChannelInventory.id)).where(
        ChannelInventory.channel_id == channel_id
    )

    if product_id:
        query = query.where(ChannelInventory.product_id == product_id)
        count_query = count_query.where(ChannelInventory.product_id == product_id)
    if warehouse_id:
        query = query.where(ChannelInventory.warehouse_id == warehouse_id)
        count_query = count_query.where(ChannelInventory.warehouse_id == warehouse_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    inventory = result.scalars().all()

    return ChannelInventoryListResponse(
        items=[ChannelInventoryResponse.model_validate(i) for i in inventory],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/{channel_id}/inventory", response_model=ChannelInventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_inventory(
    channel_id: UUID,
    inventory_in: ChannelInventoryCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Allocate inventory to a channel."""
    # Verify channel
    channel_result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    if not channel_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # Check for existing allocation
    existing = await db.execute(
        select(ChannelInventory).where(
            and_(
                ChannelInventory.channel_id == channel_id,
                ChannelInventory.product_id == inventory_in.product_id,
                ChannelInventory.warehouse_id == inventory_in.warehouse_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Inventory allocation already exists for this product/warehouse"
        )

    inventory = ChannelInventory(
        channel_id=channel_id,
        **inventory_in.model_dump(),
    )

    db.add(inventory)
    await db.commit()
    await db.refresh(inventory)

    return inventory


@router.put("/{channel_id}/inventory/{inventory_id}", response_model=ChannelInventoryResponse)
async def update_channel_inventory(
    channel_id: UUID,
    inventory_id: UUID,
    inventory_in: ChannelInventoryUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update channel inventory allocation."""
    result = await db.execute(
        select(ChannelInventory).where(
            and_(
                ChannelInventory.id == inventory_id,
                ChannelInventory.channel_id == channel_id,
            )
        )
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(status_code=404, detail="Channel inventory not found")

    update_data = inventory_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inventory, field, value)

    await db.commit()
    await db.refresh(inventory)

    return inventory


@router.delete("/{channel_id}/inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_inventory(
    channel_id: UUID,
    inventory_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete channel inventory allocation."""
    result = await db.execute(
        select(ChannelInventory).where(
            and_(
                ChannelInventory.id == inventory_id,
                ChannelInventory.channel_id == channel_id,
            )
        )
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise HTTPException(status_code=404, detail="Channel inventory not found")

    await db.delete(inventory)
    await db.commit()
    return None


@router.post("/{channel_id}/inventory/sync")
async def sync_channel_inventory(
    channel_id: UUID,
    sync_request: InventorySyncRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Sync inventory to channel (push to marketplace API)."""
    channel_result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = channel_result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # Get inventory to sync
    query = select(ChannelInventory).where(
        and_(
            ChannelInventory.channel_id == channel_id,
            ChannelInventory.is_active == True,
        )
    )

    if sync_request.product_ids:
        query = query.where(ChannelInventory.product_id.in_(sync_request.product_ids))

    result = await db.execute(query)
    inventory_list = result.scalars().all()

    # TODO: Integrate with actual marketplace APIs
    synced_count = 0
    for inv in inventory_list:
        inv.last_synced_at = datetime.utcnow()
        inv.sync_status = "SYNCED"
        synced_count += 1

    await db.commit()

    return {
        "channel_id": str(channel_id),
        "channel_name": channel.name,
        "synced_count": synced_count,
        "sync_time": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
    }


# ==================== Channel Orders ====================

@router.get("/{channel_id}/orders", response_model=ChannelOrderListResponse)
async def get_channel_orders(
    channel_id: UUID,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get orders from a channel."""
    query = select(ChannelOrder).where(ChannelOrder.channel_id == channel_id)
    count_query = select(func.count(ChannelOrder.id)).where(
        ChannelOrder.channel_id == channel_id
    )
    value_query = select(func.coalesce(func.sum(ChannelOrder.order_value), 0)).where(
        ChannelOrder.channel_id == channel_id
    )

    filters = []
    if status:
        filters.append(ChannelOrder.channel_status == status)
    if start_date:
        filters.append(ChannelOrder.channel_order_date >= start_date)
    if end_date:
        filters.append(ChannelOrder.channel_order_date <= end_date)
    if search:
        filters.append(or_(
            ChannelOrder.channel_order_id.ilike(f"%{search}%"),
            ChannelOrder.customer_name.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
        value_query = value_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_value_result = await db.execute(value_query)
    total_value = total_value_result.scalar() or Decimal("0")

    query = query.order_by(ChannelOrder.channel_order_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    return ChannelOrderListResponse(
        items=[ChannelOrderResponse.model_validate(o) for o in orders],
        total=total,
        total_value=total_value,
        skip=skip,
        limit=limit
    )


@router.post("/{channel_id}/orders", response_model=ChannelOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_order(
    channel_id: UUID,
    order_in: ChannelOrderCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create/import an order from a channel."""
    # Verify channel
    channel_result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = channel_result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # Check for duplicate channel order
    existing = await db.execute(
        select(ChannelOrder).where(
            and_(
                ChannelOrder.channel_id == channel_id,
                ChannelOrder.channel_order_id == order_in.channel_order_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Order {order_in.channel_order_id} already exists for this channel"
        )

    order = ChannelOrder(
        channel_id=channel_id,
        channel_name=channel.name,
        **order_in.model_dump(),
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    return order


@router.put("/{channel_id}/orders/{order_id}", response_model=ChannelOrderResponse)
async def update_channel_order(
    channel_id: UUID,
    order_id: UUID,
    order_in: ChannelOrderUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update channel order status."""
    result = await db.execute(
        select(ChannelOrder).where(
            and_(
                ChannelOrder.id == order_id,
                ChannelOrder.channel_id == channel_id,
            )
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Channel order not found")

    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    await db.commit()
    await db.refresh(order)

    return order


@router.delete("/{channel_id}/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_order(
    channel_id: UUID,
    order_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete channel order (only if not converted to internal order)."""
    result = await db.execute(
        select(ChannelOrder).where(
            and_(
                ChannelOrder.id == order_id,
                ChannelOrder.channel_id == channel_id,
            )
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Channel order not found")

    if order.internal_order_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete order that has been converted to internal order"
        )

    await db.delete(order)
    await db.commit()
    return None


@router.post("/{channel_id}/orders/{order_id}/convert")
async def convert_channel_order_to_internal(
    channel_id: UUID,
    order_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Convert channel order to internal OMS order."""
    result = await db.execute(
        select(ChannelOrder).where(
            and_(
                ChannelOrder.id == order_id,
                ChannelOrder.channel_id == channel_id,
            )
        )
    )
    channel_order = result.scalar_one_or_none()

    if not channel_order:
        raise HTTPException(status_code=404, detail="Channel order not found")

    if channel_order.internal_order_id:
        raise HTTPException(
            status_code=400,
            detail="Order already converted to internal order"
        )

    # TODO: Create internal Order from ChannelOrder
    # This would involve:
    # 1. Creating/finding customer
    # 2. Creating Order with items
    # 3. Linking channel_order to internal order

    # For now, return placeholder
    return {
        "channel_order_id": str(order_id),
        "channel_order_number": channel_order.channel_order_id,
        "status": "PENDING_IMPLEMENTATION",
        "message": "Order conversion to internal order needs implementation based on your Order model"
    }


@router.post("/{channel_id}/orders/sync", response_model=OrderSyncResponse)
async def sync_channel_orders(
    channel_id: UUID,
    db: DB,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """Sync orders from channel (pull from marketplace API)."""
    channel_result = await db.execute(
        select(SalesChannel).where(SalesChannel.id == channel_id)
    )
    channel = channel_result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")

    # TODO: Integrate with actual marketplace APIs
    # Each marketplace has its own API:
    # - Amazon SP-API
    # - Flipkart Seller API
    # - Meesho Partner API
    # etc.

    # For now, return mock response
    return OrderSyncResponse(
        channel_id=channel_id,
        channel_name=channel.name,
        orders_fetched=0,
        orders_created=0,
        orders_updated=0,
        orders_failed=0,
        sync_time=datetime.utcnow(),
        status="SUCCESS",
        message="Integration with channel API pending implementation",
    )
