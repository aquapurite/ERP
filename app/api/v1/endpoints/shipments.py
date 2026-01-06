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
    ShipmentLabelResponse,
    ShipmentInvoiceResponse,
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


# ==================== LABEL & INVOICE ====================

@router.get(
    "/{shipment_id}/label",
    response_model=ShipmentLabelResponse,
    dependencies=[Depends(require_permissions("shipping:view"))]
)
async def get_shipping_label(
    shipment_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get shipping label for a shipment."""
    query = (
        select(Shipment)
        .where(Shipment.id == shipment_id)
        .options(
            selectinload(Shipment.order),
            selectinload(Shipment.transporter),
        )
    )
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Generate label URL (in production, this would generate actual PDF/ZPL)
    label_url = f"/api/v1/shipments/{shipment_id}/label/download"

    return ShipmentLabelResponse(
        shipment_id=shipment.id,
        shipment_number=shipment.shipment_number,
        awb_number=shipment.awb_number,
        label_url=label_url,
        format="PDF",
    )


@router.get(
    "/{shipment_id}/label/download",
    # No auth required for label download (demo mode - use signed URLs in production)
)
async def download_shipping_label(
    shipment_id: uuid.UUID,
    db: DB,
):
    """Download shipping label as HTML (for demo - production would generate PDF)."""
    query = (
        select(Shipment)
        .where(Shipment.id == shipment_id)
        .options(
            selectinload(Shipment.order).selectinload(Order.customer),
            selectinload(Shipment.transporter),
            selectinload(Shipment.warehouse),
        )
    )
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    from fastapi.responses import HTMLResponse

    # Get address details
    ship_to = shipment.ship_to_address or {}

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shipping Label - {shipment.shipment_number}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .label {{ border: 2px solid #000; padding: 20px; max-width: 400px; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; }}
            .awb {{ font-size: 24px; font-weight: bold; letter-spacing: 2px; }}
            .barcode {{ text-align: center; font-family: 'Libre Barcode 39', cursive; font-size: 48px; margin: 10px 0; }}
            .section {{ margin: 10px 0; padding: 10px 0; border-bottom: 1px dashed #ccc; }}
            .label-title {{ font-weight: bold; font-size: 12px; color: #666; }}
            .label-value {{ font-size: 14px; margin-top: 5px; }}
            .address {{ font-size: 16px; line-height: 1.5; }}
            .footer {{ text-align: center; margin-top: 15px; font-size: 12px; }}
            .logo {{ font-size: 20px; font-weight: bold; color: #0066cc; }}
        </style>
    </head>
    <body>
        <div class="label">
            <div class="header">
                <div class="logo">{shipment.transporter.name if shipment.transporter else 'AQUAPURITE'}</div>
                <div class="awb">AWB: {shipment.awb_number or shipment.shipment_number}</div>
                <div class="barcode">*{shipment.awb_number or shipment.shipment_number}*</div>
            </div>

            <div class="section">
                <div class="label-title">SHIP TO:</div>
                <div class="address">
                    <strong>{shipment.ship_to_name or 'Customer'}</strong><br>
                    {ship_to.get('address_line1', '')}<br>
                    {ship_to.get('address_line2', '') + '<br>' if ship_to.get('address_line2') else ''}
                    {shipment.ship_to_city or ''}, {shipment.ship_to_state or ''}<br>
                    <strong>PIN: {shipment.ship_to_pincode or ''}</strong><br>
                    Ph: {shipment.ship_to_phone or ''}
                </div>
            </div>

            <div class="section">
                <div class="label-title">FROM:</div>
                <div class="label-value">
                    AQUAPURITE PVT LTD<br>
                    {shipment.warehouse.address if shipment.warehouse and hasattr(shipment.warehouse, 'address') else 'Central Warehouse, Delhi'}<br>
                    Ph: +91-9311939076
                </div>
            </div>

            <div class="section">
                <table style="width:100%">
                    <tr>
                        <td><span class="label-title">Order:</span><br>{shipment.order.order_number if shipment.order else 'N/A'}</td>
                        <td><span class="label-title">Weight:</span><br>{shipment.weight_kg} kg</td>
                        <td><span class="label-title">Boxes:</span><br>{shipment.no_of_boxes}</td>
                    </tr>
                    <tr>
                        <td><span class="label-title">Payment:</span><br>{shipment.payment_mode.value if shipment.payment_mode else 'PREPAID'}</td>
                        <td colspan="2"><span class="label-title">COD Amount:</span><br>₹{shipment.cod_amount or 0}</td>
                    </tr>
                </table>
            </div>

            <div class="footer">
                Shipment Date: {shipment.created_at.strftime('%d-%b-%Y') if shipment.created_at else 'N/A'}<br>
                <small>Handle with care | Fragile</small>
            </div>
        </div>

        <script>window.print();</script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get(
    "/{shipment_id}/invoice",
    response_model=ShipmentInvoiceResponse,
    dependencies=[Depends(require_permissions("shipping:view"))]
)
async def get_shipment_invoice(
    shipment_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get invoice for a shipment."""
    query = (
        select(Shipment)
        .where(Shipment.id == shipment_id)
        .options(selectinload(Shipment.order))
    )
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    invoice_url = f"/api/v1/shipments/{shipment_id}/invoice/download"

    return ShipmentInvoiceResponse(
        shipment_id=shipment.id,
        shipment_number=shipment.shipment_number,
        invoice_url=invoice_url,
    )


@router.get(
    "/{shipment_id}/invoice/download",
    # No auth required for invoice download (demo mode - use signed URLs in production)
)
async def download_shipment_invoice(
    shipment_id: uuid.UUID,
    db: DB,
):
    """Download shipment invoice as HTML (for demo - production would generate PDF)."""
    query = (
        select(Shipment)
        .where(Shipment.id == shipment_id)
        .options(
            selectinload(Shipment.order).selectinload(Order.customer),
            selectinload(Shipment.order).selectinload(Order.items),
            selectinload(Shipment.transporter),
        )
    )
    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    from fastapi.responses import HTMLResponse

    order = shipment.order
    customer = order.customer if order else None
    ship_to = shipment.ship_to_address or {}

    # Build items table
    items_html = ""
    if order and order.items:
        for idx, item in enumerate(order.items, 1):
            unit_price = float(item.unit_price) if item.unit_price else 0.0
            total_amt = float(item.total_amount) if item.total_amount else 0.0
            items_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{item.product_name}<br><small>SKU: {item.product_sku}</small></td>
                <td>{item.hsn_code or 'N/A'}</td>
                <td style="text-align:right">{item.quantity}</td>
                <td style="text-align:right">₹{unit_price:,.2f}</td>
                <td style="text-align:right">₹{total_amt:,.2f}</td>
            </tr>
            """

    invoice_number = f"INV-{shipment.shipment_number.replace('SHP-', '')}"
    invoice_date = shipment.created_at.strftime('%d-%b-%Y') if shipment.created_at else datetime.now().strftime('%d-%b-%Y')

    # Calculate totals (handle Decimal and None)
    subtotal = float(order.subtotal) if order and order.subtotal else 0.0
    tax_amount = float(order.tax_amount) if order and order.tax_amount else 0.0
    shipping_amount = float(order.shipping_amount) if order and order.shipping_amount else 0.0
    discount_amount = float(order.discount_amount) if order and order.discount_amount else 0.0
    total_amount = float(order.total_amount) if order and order.total_amount else 0.0

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tax Invoice - {invoice_number}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; font-size: 12px; }}
            .invoice {{ max-width: 800px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px; }}
            .company {{ }}
            .company-name {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
            .invoice-title {{ font-size: 20px; font-weight: bold; text-align: right; }}
            .invoice-details {{ text-align: right; }}
            .addresses {{ display: flex; justify-content: space-between; margin: 20px 0; }}
            .address-box {{ width: 48%; padding: 10px; border: 1px solid #ddd; }}
            .address-title {{ font-weight: bold; background: #f0f0f0; padding: 5px; margin: -10px -10px 10px -10px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background: #f0f0f0; }}
            .totals {{ width: 300px; margin-left: auto; }}
            .totals td {{ border: none; padding: 5px; }}
            .totals .total-row {{ font-weight: bold; font-size: 16px; border-top: 2px solid #000; }}
            .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}
            .signature {{ text-align: right; margin-top: 50px; }}
            @media print {{ body {{ margin: 0; }} }}
        </style>
    </head>
    <body>
        <div class="invoice">
            <div class="header">
                <div class="company">
                    <div class="company-name">AQUAPURITE PRIVATE LIMITED</div>
                    <div>Plot 36-A KH No 181, Najafgarh</div>
                    <div>Delhi - 110043, India</div>
                    <div>GSTIN: 07ABDCA6170C1Z5</div>
                    <div>Phone: +91-9311939076</div>
                </div>
                <div>
                    <div class="invoice-title">TAX INVOICE</div>
                    <div class="invoice-details">
                        <div><strong>Invoice No:</strong> {invoice_number}</div>
                        <div><strong>Date:</strong> {invoice_date}</div>
                        <div><strong>Order No:</strong> {order.order_number if order else 'N/A'}</div>
                        <div><strong>AWB:</strong> {shipment.awb_number or shipment.shipment_number}</div>
                    </div>
                </div>
            </div>

            <div class="addresses">
                <div class="address-box">
                    <div class="address-title">BILL TO:</div>
                    <strong>{customer.full_name if customer else 'Customer'}</strong><br>
                    {order.billing_address.get('address_line1', ship_to.get('address_line1', '')) if order and order.billing_address else ship_to.get('address_line1', '')}<br>
                    {order.billing_address.get('city', ship_to.get('city', '')) if order and order.billing_address else ship_to.get('city', '')},
                    {order.billing_address.get('state', ship_to.get('state', '')) if order and order.billing_address else ship_to.get('state', '')} -
                    {order.billing_address.get('pincode', ship_to.get('pincode', '')) if order and order.billing_address else ship_to.get('pincode', '')}<br>
                    Phone: {customer.phone if customer else shipment.ship_to_phone or ''}
                </div>
                <div class="address-box">
                    <div class="address-title">SHIP TO:</div>
                    <strong>{shipment.ship_to_name or 'Customer'}</strong><br>
                    {ship_to.get('address_line1', '')}<br>
                    {shipment.ship_to_city or ''}, {shipment.ship_to_state or ''} - {shipment.ship_to_pincode or ''}<br>
                    Phone: {shipment.ship_to_phone or ''}
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width:30px">#</th>
                        <th>Product Description</th>
                        <th style="width:80px">HSN</th>
                        <th style="width:50px">Qty</th>
                        <th style="width:100px">Unit Price</th>
                        <th style="width:100px">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <table class="totals">
                <tr>
                    <td>Subtotal:</td>
                    <td style="text-align:right">₹{subtotal:,.2f}</td>
                </tr>
                <tr>
                    <td>CGST (9%):</td>
                    <td style="text-align:right">₹{tax_amount/2:,.2f}</td>
                </tr>
                <tr>
                    <td>SGST (9%):</td>
                    <td style="text-align:right">₹{tax_amount/2:,.2f}</td>
                </tr>
                <tr>
                    <td>Shipping:</td>
                    <td style="text-align:right">₹{shipping_amount:,.2f}</td>
                </tr>
                <tr>
                    <td>Discount:</td>
                    <td style="text-align:right">-₹{discount_amount:,.2f}</td>
                </tr>
                <tr class="total-row">
                    <td>GRAND TOTAL:</td>
                    <td style="text-align:right">₹{total_amount:,.2f}</td>
                </tr>
            </table>

            <div class="footer">
                <div><strong>Payment Method:</strong> {order.payment_method.value if order else 'N/A'}</div>
                <div><strong>Payment Status:</strong> {order.payment_status.value if order else 'N/A'}</div>
                <br>
                <div><strong>Terms & Conditions:</strong></div>
                <ol style="font-size:10px; color:#666;">
                    <li>Goods once sold will not be taken back.</li>
                    <li>All disputes are subject to Delhi jurisdiction.</li>
                    <li>E&OE - Errors and Omissions Excepted.</li>
                </ol>
            </div>

            <div class="signature">
                <div>For AQUAPURITE PRIVATE LIMITED</div>
                <br><br><br>
                <div>Authorized Signatory</div>
            </div>
        </div>

        <script>window.print();</script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
