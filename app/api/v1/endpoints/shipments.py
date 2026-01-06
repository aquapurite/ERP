"""Shipment API endpoints for shipping operations."""
from typing import Optional
import uuid
from math import ceil
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.shipment import Shipment, ShipmentTracking, ShipmentStatus, PaymentMode, PackagingType
from app.models.order import Order, OrderStatus
from app.models.warehouse import Warehouse
from app.models.transporter import Transporter
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ShipmentDetailResponse,
    ShipmentListResponse,
    ShipmentBrief,
    ShipmentTrackingResponse,
    ShipmentPackRequest,
    ShipmentPackResponse,
    ShipmentTrackingUpdate,
    ShipmentDeliveryMarkRequest,
    ShipmentDeliveryMarkResponse,
    ShipmentRTOInitiateRequest,
    ShipmentRTOResponse,
    ShipmentCancelRequest,
    BulkShipmentCreate,
    BulkShipmentResponse,
    TrackShipmentRequest,
    TrackShipmentResponse,
)
from app.schemas.transporter import TransporterBrief


router = APIRouter()


def generate_shipment_number() -> str:
    """Generate unique shipment number."""
    from datetime import datetime
    import random
    date_str = datetime.now().strftime("%Y%m%d")
    random_suffix = random.randint(10000, 99999)
    return f"SHP-{date_str}-{random_suffix}"


# ==================== SHIPMENT CRUD ====================

@router.get(
    "",
    response_model=ShipmentListResponse,
    dependencies=[Depends(require_permissions("shipping:view"))]
)
async def list_shipments(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    transporter_id: Optional[uuid.UUID] = Query(None),
    status: Optional[ShipmentStatus] = Query(None),
    payment_mode: Optional[PaymentMode] = Query(None),
    search: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
):
    """Get paginated list of shipments."""
    query = select(Shipment)
    count_query = select(func.count(Shipment.id))

    if warehouse_id:
        query = query.where(Shipment.warehouse_id == warehouse_id)
        count_query = count_query.where(Shipment.warehouse_id == warehouse_id)

    if transporter_id:
        query = query.where(Shipment.transporter_id == transporter_id)
        count_query = count_query.where(Shipment.transporter_id == transporter_id)

    if status:
        query = query.where(Shipment.status == status)
        count_query = count_query.where(Shipment.status == status)

    if payment_mode:
        query = query.where(Shipment.payment_mode == payment_mode)
        count_query = count_query.where(Shipment.payment_mode == payment_mode)

    if search:
        search_filter = or_(
            Shipment.shipment_number.ilike(f"%{search}%"),
            Shipment.awb_number.ilike(f"%{search}%"),
            Shipment.ship_to_phone.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if from_date:
        query = query.where(Shipment.created_at >= from_date)
        count_query = count_query.where(Shipment.created_at >= from_date)

    if to_date:
        query = query.where(Shipment.created_at <= to_date)
        count_query = count_query.where(Shipment.created_at <= to_date)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * size
    query = query.options(selectinload(Shipment.transporter))
    query = query.order_by(Shipment.created_at.desc())
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    shipments = result.scalars().all()

    return ShipmentListResponse(
        items=[ShipmentResponse.model_validate(s) for s in shipments],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get(
    "/{shipment_id}",
    response_model=ShipmentDetailResponse,
    dependencies=[Depends(require_permissions("shipping:view"))]
)
async def get_shipment(
    shipment_id: uuid.UUID,
    db: DB,
):
    """Get shipment with tracking history."""
    query = (
        select(Shipment)
        .where(Shipment.id == shipment_id)
        .options(
            selectinload(Shipment.transporter),
            selectinload(Shipment.tracking_history),
        )
    )
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    response_data = ShipmentResponse.model_validate(shipment).model_dump()
    response_data["tracking_history"] = [
        ShipmentTrackingResponse.model_validate(t) for t in shipment.tracking_history
    ]

    return ShipmentDetailResponse(**response_data)


@router.post(
    "",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("shipping:create"))]
)
async def create_shipment(
    data: ShipmentCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new shipment for an order."""
    # Verify order exists and is ready
    order_query = select(Order).where(Order.id == data.order_id)
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Check if shipment already exists for this order
    existing_query = select(Shipment).where(
        and_(
            Shipment.order_id == data.order_id,
            Shipment.status.notin_([ShipmentStatus.CANCELLED, ShipmentStatus.RTO_DELIVERED]),
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active shipment already exists for this order"
        )

    # Calculate volumetric weight
    volumetric_weight = None
    if data.length_cm and data.breadth_cm and data.height_cm:
        volumetric_weight = (data.length_cm * data.breadth_cm * data.height_cm) / 5000

    # Calculate chargeable weight
    chargeable_weight = max(data.weight_kg, volumetric_weight or 0)

    shipment = Shipment(
        shipment_number=generate_shipment_number(),
        order_id=data.order_id,
        warehouse_id=data.warehouse_id,
        transporter_id=data.transporter_id,
        status=ShipmentStatus.CREATED,
        payment_mode=data.payment_mode,
        cod_amount=data.cod_amount if data.payment_mode == PaymentMode.COD else None,
        packaging_type=data.packaging_type,
        no_of_boxes=data.no_of_boxes,
        weight_kg=data.weight_kg,
        volumetric_weight_kg=volumetric_weight,
        chargeable_weight_kg=chargeable_weight,
        length_cm=data.length_cm,
        breadth_cm=data.breadth_cm,
        height_cm=data.height_cm,
        ship_to_name=data.ship_to_name,
        ship_to_phone=data.ship_to_phone,
        ship_to_email=data.ship_to_email,
        ship_to_address=data.ship_to_address,
        ship_to_pincode=data.ship_to_pincode,
        ship_to_city=data.ship_to_city,
        ship_to_state=data.ship_to_state,
        expected_delivery_date=data.expected_delivery_date,
        created_by=current_user.id,
    )

    db.add(shipment)
    await db.flush()  # Flush to get shipment.id

    # Add tracking entry
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=ShipmentStatus.CREATED,
        remarks="Shipment created",
        event_time=datetime.utcnow(),
        source="SYSTEM",
        updated_by=current_user.id,
    )
    db.add(tracking)

    await db.commit()

    # Reload with transporter relationship
    query = (
        select(Shipment)
        .where(Shipment.id == shipment.id)
        .options(selectinload(Shipment.transporter))
    )
    result = await db.execute(query)
    shipment = result.scalar_one()

    return ShipmentResponse.model_validate(shipment)


@router.put(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    dependencies=[Depends(require_permissions("shipping:update"))]
)
async def update_shipment(
    shipment_id: uuid.UUID,
    data: ShipmentUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update shipment details."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    if shipment.status not in [ShipmentStatus.CREATED, ShipmentStatus.PACKED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipment cannot be updated in current status"
        )

    update_data = data.model_dump(exclude_unset=True)

    # Recalculate weights if dimensions changed
    if any(k in update_data for k in ["weight_kg", "length_cm", "breadth_cm", "height_cm"]):
        length = update_data.get("length_cm", shipment.length_cm)
        breadth = update_data.get("breadth_cm", shipment.breadth_cm)
        height = update_data.get("height_cm", shipment.height_cm)
        weight = update_data.get("weight_kg", shipment.weight_kg)

        if length and breadth and height:
            volumetric = (length * breadth * height) / 5000
            update_data["volumetric_weight_kg"] = volumetric
            update_data["chargeable_weight_kg"] = max(weight, volumetric)

    for field, value in update_data.items():
        setattr(shipment, field, value)

    await db.commit()
    await db.refresh(shipment)

    return ShipmentResponse.model_validate(shipment)


# ==================== SHIPMENT OPERATIONS ====================

@router.post(
    "/{shipment_id}/pack",
    response_model=ShipmentPackResponse,
    dependencies=[Depends(require_permissions("shipping:update"))]
)
async def pack_shipment(
    shipment_id: uuid.UUID,
    data: ShipmentPackRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Mark shipment as packed."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    if shipment.status != ShipmentStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipment is not in created status"
        )

    # Update shipment
    shipment.status = ShipmentStatus.PACKED
    shipment.packed_at = datetime.utcnow()
    shipment.packaging_type = data.packaging_type
    shipment.no_of_boxes = data.no_of_boxes
    shipment.weight_kg = data.weight_kg
    if data.length_cm:
        shipment.length_cm = data.length_cm
    if data.breadth_cm:
        shipment.breadth_cm = data.breadth_cm
    if data.height_cm:
        shipment.height_cm = data.height_cm

    # Recalculate volumetric
    if shipment.length_cm and shipment.breadth_cm and shipment.height_cm:
        shipment.volumetric_weight_kg = (
            shipment.length_cm * shipment.breadth_cm * shipment.height_cm
        ) / 5000
        shipment.chargeable_weight_kg = max(
            shipment.weight_kg, shipment.volumetric_weight_kg
        )

    # Add tracking
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=ShipmentStatus.PACKED,
        remarks=data.notes or "Shipment packed",
        event_time=datetime.utcnow(),
        source="SYSTEM",
        updated_by=current_user.id,
    )
    db.add(tracking)

    await db.commit()
    await db.refresh(shipment)

    return ShipmentPackResponse(
        success=True,
        shipment_id=shipment.id,
        shipment_number=shipment.shipment_number,
        status=shipment.status,
        message="Shipment packed successfully",
    )


@router.post(
    "/{shipment_id}/generate-awb",
    response_model=ShipmentResponse,
    dependencies=[Depends(require_permissions("shipping:update"))]
)
async def generate_awb(
    shipment_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Generate AWB number for shipment."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    if shipment.awb_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AWB already generated"
        )

    if not shipment.transporter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transporter not assigned"
        )

    # Get transporter
    transporter_query = select(Transporter).where(Transporter.id == shipment.transporter_id)
    transporter_result = await db.execute(transporter_query)
    transporter = transporter_result.scalar_one()

    # Generate AWB
    prefix = transporter.awb_prefix or transporter.code[:3].upper()
    sequence = transporter.awb_sequence_current
    awb_number = f"{prefix}{sequence:010d}"

    transporter.awb_sequence_current = sequence + 1

    shipment.awb_number = awb_number
    shipment.tracking_number = awb_number
    shipment.status = ShipmentStatus.READY_FOR_PICKUP

    # Add tracking
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=ShipmentStatus.READY_FOR_PICKUP,
        remarks=f"AWB generated: {awb_number}",
        event_time=datetime.utcnow(),
        source="SYSTEM",
        updated_by=current_user.id,
    )
    db.add(tracking)

    await db.commit()
    await db.refresh(shipment)

    return ShipmentResponse.model_validate(shipment)


@router.post(
    "/{shipment_id}/track",
    response_model=ShipmentTrackingResponse,
    dependencies=[Depends(require_permissions("shipping:update"))]
)
async def update_tracking(
    shipment_id: uuid.UUID,
    data: ShipmentTrackingUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Add tracking update to shipment."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Update shipment status
    shipment.status = data.status

    # Mark shipped if transitioning to shipped
    if data.status == ShipmentStatus.SHIPPED and not shipment.shipped_at:
        shipment.shipped_at = datetime.utcnow()

    # Add tracking entry
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=data.status,
        status_code=data.status_code,
        location=data.location,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        remarks=data.remarks,
        event_time=data.event_time or datetime.utcnow(),
        source=data.source,
        updated_by=current_user.id,
    )
    db.add(tracking)

    await db.commit()
    await db.refresh(tracking)

    return ShipmentTrackingResponse.model_validate(tracking)


@router.post(
    "/{shipment_id}/deliver",
    response_model=ShipmentDeliveryMarkResponse,
    dependencies=[Depends(require_permissions("shipping:update"))]
)
async def mark_delivered(
    shipment_id: uuid.UUID,
    data: ShipmentDeliveryMarkRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Mark shipment as delivered."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    if shipment.status == ShipmentStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipment already delivered"
        )

    # Update shipment
    now = datetime.utcnow()
    shipment.status = ShipmentStatus.DELIVERED
    shipment.delivered_at = now
    shipment.actual_delivery_date = now.date()
    shipment.delivered_to = data.delivered_to
    shipment.delivery_relation = data.delivery_relation
    shipment.delivery_remarks = data.delivery_remarks
    shipment.pod_image_url = data.pod_image_url
    shipment.pod_signature_url = data.pod_signature_url

    if data.cod_collected:
        shipment.cod_collected = True

    shipment.delivery_attempts += 1

    # Add tracking
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=ShipmentStatus.DELIVERED,
        remarks=f"Delivered to {data.delivered_to}",
        event_time=now,
        source="SYSTEM",
        updated_by=current_user.id,
    )
    db.add(tracking)

    # Update order status
    order_query = select(Order).where(Order.id == shipment.order_id)
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    if order:
        order.status = OrderStatus.DELIVERED

    await db.commit()
    await db.refresh(shipment)

    return ShipmentDeliveryMarkResponse(
        success=True,
        shipment_id=shipment.id,
        shipment_number=shipment.shipment_number,
        order_id=shipment.order_id,
        status=shipment.status,
        delivered_at=shipment.delivered_at,
        message="Shipment marked as delivered",
    )


@router.post(
    "/{shipment_id}/rto",
    response_model=ShipmentRTOResponse,
    dependencies=[Depends(require_permissions("shipping:update"))]
)
async def initiate_rto(
    shipment_id: uuid.UUID,
    data: ShipmentRTOInitiateRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Initiate Return to Origin (RTO)."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    if shipment.status in [ShipmentStatus.DELIVERED, ShipmentStatus.RTO_DELIVERED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot initiate RTO for delivered shipment"
        )

    shipment.status = ShipmentStatus.RTO_INITIATED
    shipment.rto_reason = data.reason
    shipment.rto_initiated_at = datetime.utcnow()

    # Add tracking
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=ShipmentStatus.RTO_INITIATED,
        remarks=f"RTO initiated: {data.reason}",
        event_time=datetime.utcnow(),
        source="SYSTEM",
        updated_by=current_user.id,
    )
    db.add(tracking)

    await db.commit()
    await db.refresh(shipment)

    return ShipmentRTOResponse(
        success=True,
        shipment_id=shipment.id,
        shipment_number=shipment.shipment_number,
        status=shipment.status,
        rto_reason=data.reason,
        message="RTO initiated successfully",
    )


@router.post(
    "/{shipment_id}/cancel",
    response_model=ShipmentResponse,
    dependencies=[Depends(require_permissions("shipping:delete"))]
)
async def cancel_shipment(
    shipment_id: uuid.UUID,
    data: ShipmentCancelRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Cancel a shipment."""
    query = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    if shipment.status in [ShipmentStatus.DELIVERED, ShipmentStatus.SHIPPED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel shipped/delivered shipment"
        )

    shipment.status = ShipmentStatus.CANCELLED
    shipment.cancelled_at = datetime.utcnow()
    shipment.cancellation_reason = data.reason

    # Add tracking
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=ShipmentStatus.CANCELLED,
        remarks=f"Cancelled: {data.reason}",
        event_time=datetime.utcnow(),
        source="SYSTEM",
        updated_by=current_user.id,
    )
    db.add(tracking)

    await db.commit()
    await db.refresh(shipment)

    return ShipmentResponse.model_validate(shipment)


# ==================== PUBLIC TRACKING ====================

@router.post(
    "/track",
    response_model=TrackShipmentResponse,
)
async def track_shipment_public(
    data: TrackShipmentRequest,
    db: DB,
):
    """Public tracking API (no auth required)."""
    query = select(Shipment).options(selectinload(Shipment.tracking_history))

    if data.awb_number:
        query = query.where(Shipment.awb_number == data.awb_number)
    elif data.order_number:
        query = query.join(Order).where(Order.order_number == data.order_number)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide awb_number or order_number"
        )

    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    status_descriptions = {
        ShipmentStatus.CREATED: "Order is being processed",
        ShipmentStatus.PACKED: "Order has been packed",
        ShipmentStatus.READY_FOR_PICKUP: "Ready for pickup by courier",
        ShipmentStatus.MANIFESTED: "Handed over to courier",
        ShipmentStatus.SHIPPED: "In transit",
        ShipmentStatus.IN_TRANSIT: "In transit to destination",
        ShipmentStatus.OUT_FOR_DELIVERY: "Out for delivery",
        ShipmentStatus.DELIVERED: "Delivered successfully",
        ShipmentStatus.RTO_INITIATED: "Return initiated",
        ShipmentStatus.RTO_IN_TRANSIT: "Return in progress",
        ShipmentStatus.RTO_DELIVERED: "Returned to seller",
        ShipmentStatus.CANCELLED: "Cancelled",
    }

    return TrackShipmentResponse(
        awb_number=shipment.awb_number or shipment.shipment_number,
        order_number=shipment.shipment_number,
        status=shipment.status,
        status_description=status_descriptions.get(shipment.status, "Unknown"),
        current_location=shipment.tracking_history[-1].location if shipment.tracking_history else None,
        expected_delivery=shipment.expected_delivery_date,
        delivered_at=shipment.delivered_at,
        delivered_to=shipment.delivered_to,
        tracking_history=[
            ShipmentTrackingResponse.model_validate(t) for t in shipment.tracking_history
        ],
    )
