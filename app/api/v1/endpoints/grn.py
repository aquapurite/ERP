"""Goods Receipt Note (GRN) API endpoints."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.purchase import (
    GoodsReceiptNote, GRNItem, PurchaseOrder, PurchaseOrderItem,
    GRNStatus, QualityCheckResult
)
from app.models.vendor import Vendor
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.services.document_sequence_service import DocumentSequenceService
from app.services.costing_service import CostingService

router = APIRouter()


# ==================== Schemas ====================

class GRNItemCreate(BaseModel):
    po_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity_received: int
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    serial_numbers: Optional[List[str]] = None
    remarks: Optional[str] = None


class GRNCreate(BaseModel):
    purchase_order_id: UUID
    grn_date: date
    warehouse_id: UUID
    vendor_challan_number: Optional[str] = None
    vendor_challan_date: Optional[date] = None
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    receiving_remarks: Optional[str] = None
    items: List[GRNItemCreate]


class GRNQCUpdate(BaseModel):
    items: List[dict]  # [{"item_id": uuid, "qc_result": "PASSED/FAILED", "quantity_accepted": int, "quantity_rejected": int, "rejection_reason": str}]
    qc_remarks: Optional[str] = None


# ==================== Endpoints ====================

@router.get("/next-number")
async def get_next_grn_number(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get the next GRN number."""
    seq_service = DocumentSequenceService(db)
    next_number = await seq_service.get_next_number("GRN")
    return {"grn_number": next_number}


@router.get("")
async def list_grns(
    db: DB,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    vendor_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    po_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
):
    """List GRNs with filtering and pagination."""
    query = select(GoodsReceiptNote).options(
        selectinload(GoodsReceiptNote.vendor),
        selectinload(GoodsReceiptNote.warehouse),
        selectinload(GoodsReceiptNote.purchase_order),
        selectinload(GoodsReceiptNote.received_by_user),
    )

    conditions = []

    if status:
        conditions.append(GoodsReceiptNote.status == status.upper())

    if vendor_id:
        conditions.append(GoodsReceiptNote.vendor_id == vendor_id)

    if warehouse_id:
        conditions.append(GoodsReceiptNote.warehouse_id == warehouse_id)

    if po_id:
        conditions.append(GoodsReceiptNote.purchase_order_id == po_id)

    if start_date:
        conditions.append(GoodsReceiptNote.grn_date >= start_date)

    if end_date:
        conditions.append(GoodsReceiptNote.grn_date <= end_date)

    if search:
        conditions.append(
            or_(
                GoodsReceiptNote.grn_number.ilike(f"%{search}%"),
                GoodsReceiptNote.vendor_challan_number.ilike(f"%{search}%"),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Count total
    count_query = select(func.count()).select_from(GoodsReceiptNote)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(desc(GoodsReceiptNote.created_at))
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    grns = result.scalars().all()

    return {
        "items": [
            {
                "id": str(grn.id),
                "grn_number": grn.grn_number,
                "grn_date": grn.grn_date.isoformat() if grn.grn_date else None,
                "status": grn.status,
                "purchase_order_id": str(grn.purchase_order_id),
                "po_number": grn.purchase_order.po_number if grn.purchase_order else None,
                "vendor_id": str(grn.vendor_id),
                "vendor_name": grn.vendor.name if grn.vendor else None,
                "warehouse_id": str(grn.warehouse_id),
                "warehouse_name": grn.warehouse.name if grn.warehouse else None,
                "vendor_challan_number": grn.vendor_challan_number,
                "total_items": grn.total_items,
                "total_quantity_received": grn.total_quantity_received,
                "total_quantity_accepted": grn.total_quantity_accepted,
                "total_quantity_rejected": grn.total_quantity_rejected,
                "total_value": float(grn.total_value) if grn.total_value else 0,
                "qc_status": grn.qc_status,
                "received_by": grn.received_by_user.email if grn.received_by_user else None,
                "created_at": grn.created_at.isoformat() if grn.created_at else None,
            }
            for grn in grns
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/stats")
async def get_grn_stats(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get GRN statistics."""
    # Count by status
    status_query = select(
        GoodsReceiptNote.status,
        func.count().label("count")
    ).group_by(GoodsReceiptNote.status)

    status_result = await db.execute(status_query)
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Pending QC count
    pending_qc = by_status.get("PENDING_QC", 0)

    # Today's GRNs
    today = date.today()
    today_query = select(func.count()).select_from(GoodsReceiptNote).where(
        GoodsReceiptNote.grn_date == today
    )
    today_count = await db.scalar(today_query) or 0

    # Pending put-away
    put_away_pending = by_status.get("PUT_AWAY_PENDING", 0)

    return {
        "by_status": by_status,
        "pending_qc": pending_qc,
        "today_received": today_count,
        "put_away_pending": put_away_pending,
        "total": sum(by_status.values()),
    }


@router.get("/{grn_id}")
async def get_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get GRN details."""
    query = select(GoodsReceiptNote).options(
        selectinload(GoodsReceiptNote.vendor),
        selectinload(GoodsReceiptNote.warehouse),
        selectinload(GoodsReceiptNote.purchase_order),
        selectinload(GoodsReceiptNote.received_by_user),
        selectinload(GoodsReceiptNote.qc_done_by_user),
        selectinload(GoodsReceiptNote.items).selectinload(GRNItem.product),
    ).where(GoodsReceiptNote.id == grn_id)

    result = await db.execute(query)
    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )

    return {
        "id": str(grn.id),
        "grn_number": grn.grn_number,
        "grn_date": grn.grn_date.isoformat() if grn.grn_date else None,
        "status": grn.status,
        "purchase_order": {
            "id": str(grn.purchase_order_id),
            "po_number": grn.purchase_order.po_number if grn.purchase_order else None,
        },
        "vendor": {
            "id": str(grn.vendor_id),
            "name": grn.vendor.name if grn.vendor else None,
        },
        "warehouse": {
            "id": str(grn.warehouse_id),
            "name": grn.warehouse.name if grn.warehouse else None,
        },
        "vendor_challan_number": grn.vendor_challan_number,
        "vendor_challan_date": grn.vendor_challan_date.isoformat() if grn.vendor_challan_date else None,
        "transporter_name": grn.transporter_name,
        "vehicle_number": grn.vehicle_number,
        "lr_number": grn.lr_number,
        "e_way_bill_number": grn.e_way_bill_number,
        "total_items": grn.total_items,
        "total_quantity_received": grn.total_quantity_received,
        "total_quantity_accepted": grn.total_quantity_accepted,
        "total_quantity_rejected": grn.total_quantity_rejected,
        "total_value": float(grn.total_value) if grn.total_value else 0,
        "qc_required": grn.qc_required,
        "qc_status": grn.qc_status,
        "qc_done_by": grn.qc_done_by_user.email if grn.qc_done_by_user else None,
        "qc_done_at": grn.qc_done_at.isoformat() if grn.qc_done_at else None,
        "qc_remarks": grn.qc_remarks,
        "receiving_remarks": grn.receiving_remarks,
        "put_away_complete": grn.put_away_complete,
        "put_away_at": grn.put_away_at.isoformat() if grn.put_away_at else None,
        "received_by": grn.received_by_user.email if grn.received_by_user else None,
        "photos_urls": grn.photos_urls,
        "items": [
            {
                "id": str(item.id),
                "po_item_id": str(item.po_item_id),
                "product_id": str(item.product_id),
                "product_name": item.product_name,
                "sku": item.sku,
                "part_code": item.part_code,
                "hsn_code": item.hsn_code,
                "quantity_expected": item.quantity_expected,
                "quantity_received": item.quantity_received,
                "quantity_accepted": item.quantity_accepted,
                "quantity_rejected": item.quantity_rejected,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "accepted_value": float(item.accepted_value) if item.accepted_value else 0,
                "batch_number": item.batch_number,
                "manufacturing_date": item.manufacturing_date.isoformat() if item.manufacturing_date else None,
                "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                "serial_numbers": item.serial_numbers,
                "bin_location": item.bin_location,
                "qc_result": item.qc_result,
                "rejection_reason": item.rejection_reason,
                "remarks": item.remarks,
            }
            for item in grn.items
        ],
        "created_at": grn.created_at.isoformat() if grn.created_at else None,
        "updated_at": grn.updated_at.isoformat() if grn.updated_at else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_grn(
    data: GRNCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new GRN against a Purchase Order."""
    # Validate PO exists
    po = await db.get(PurchaseOrder, data.purchase_order_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )

    if po.status not in ["APPROVED", "SENT_TO_VENDOR", "ACKNOWLEDGED", "PARTIALLY_RECEIVED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create GRN for PO with status {po.status}"
        )

    # Get next GRN number
    seq_service = DocumentSequenceService(db)
    grn_number = await seq_service.get_next_number("GRN")

    # Create GRN
    grn = GoodsReceiptNote(
        grn_number=grn_number,
        grn_date=data.grn_date,
        status="DRAFT",
        purchase_order_id=data.purchase_order_id,
        vendor_id=po.vendor_id,
        warehouse_id=data.warehouse_id,
        vendor_challan_number=data.vendor_challan_number,
        vendor_challan_date=data.vendor_challan_date,
        transporter_name=data.transporter_name,
        vehicle_number=data.vehicle_number,
        lr_number=data.lr_number,
        e_way_bill_number=data.e_way_bill_number,
        receiving_remarks=data.receiving_remarks,
        received_by=current_user.id,
        qc_required=True,
        total_items=len(data.items),
    )
    db.add(grn)
    await db.flush()

    # Create GRN items
    total_quantity = 0
    total_value = Decimal("0")

    for item_data in data.items:
        # Get PO item for product details
        po_item = await db.get(PurchaseOrderItem, item_data.po_item_id)
        if not po_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PO Item {item_data.po_item_id} not found"
            )

        grn_item = GRNItem(
            grn_id=grn.id,
            po_item_id=item_data.po_item_id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            product_name=po_item.product_name,
            sku=po_item.sku,
            part_code=po_item.part_code,
            hsn_code=po_item.hsn_code,
            quantity_expected=po_item.quantity_ordered - po_item.quantity_received,
            quantity_received=item_data.quantity_received,
            unit_price=po_item.unit_price,
            batch_number=item_data.batch_number,
            manufacturing_date=item_data.manufacturing_date,
            expiry_date=item_data.expiry_date,
            serial_numbers=item_data.serial_numbers,
            remarks=item_data.remarks,
            qc_result="PENDING",
        )
        db.add(grn_item)

        total_quantity += item_data.quantity_received

    grn.total_quantity_received = total_quantity
    grn.qc_status = "PENDING"

    await db.commit()
    await db.refresh(grn)

    return {
        "id": str(grn.id),
        "grn_number": grn.grn_number,
        "status": grn.status,
        "message": "GRN created successfully",
    }


@router.post("/{grn_id}/submit")
async def submit_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Submit GRN for QC."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )

    if grn.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit GRN with status {grn.status}"
        )

    grn.status = "PENDING_QC"
    await db.commit()

    return {"message": "GRN submitted for QC", "status": grn.status}


@router.post("/{grn_id}/qc")
async def complete_qc(
    grn_id: UUID,
    data: GRNQCUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Complete QC for GRN items."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )

    if grn.status != "PENDING_QC":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot perform QC on GRN with status {grn.status}"
        )

    total_accepted = 0
    total_rejected = 0
    all_passed = True
    all_failed = True

    for item_update in data.items:
        item = await db.get(GRNItem, item_update["item_id"])
        if item and item.grn_id == grn_id:
            item.qc_result = item_update.get("qc_result", "PENDING")
            item.quantity_accepted = item_update.get("quantity_accepted", 0)
            item.quantity_rejected = item_update.get("quantity_rejected", 0)
            item.rejection_reason = item_update.get("rejection_reason")
            item.accepted_value = item.quantity_accepted * item.unit_price

            total_accepted += item.quantity_accepted
            total_rejected += item.quantity_rejected

            if item.qc_result != "PASSED":
                all_passed = False
            if item.qc_result != "FAILED":
                all_failed = False

    # Update GRN totals
    grn.total_quantity_accepted = total_accepted
    grn.total_quantity_rejected = total_rejected

    # Calculate total value
    items_query = select(GRNItem).where(GRNItem.grn_id == grn_id)
    result = await db.execute(items_query)
    items = result.scalars().all()
    grn.total_value = sum(item.accepted_value or Decimal("0") for item in items)

    # Set QC status
    if all_passed:
        grn.qc_status = "PASSED"
        grn.status = "QC_PASSED"
    elif all_failed:
        grn.qc_status = "FAILED"
        grn.status = "QC_FAILED"
    else:
        grn.qc_status = "CONDITIONAL"
        grn.status = "PARTIALLY_ACCEPTED"

    grn.qc_done_by = current_user.id
    grn.qc_done_at = datetime.now(timezone.utc)
    grn.qc_remarks = data.qc_remarks

    await db.commit()

    return {
        "message": "QC completed",
        "qc_status": grn.qc_status,
        "status": grn.status,
        "total_accepted": total_accepted,
        "total_rejected": total_rejected,
    }


@router.post("/{grn_id}/accept")
async def accept_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Accept GRN after QC and update PO quantities and product costs (COGS)."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )

    if grn.status not in ["QC_PASSED", "PARTIALLY_ACCEPTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept GRN with status {grn.status}"
        )

    # Update PO item received quantities
    items_query = select(GRNItem).where(GRNItem.grn_id == grn_id)
    result = await db.execute(items_query)
    items = result.scalars().all()

    for item in items:
        po_item = await db.get(PurchaseOrderItem, item.po_item_id)
        if po_item:
            po_item.quantity_received += item.quantity_accepted
            po_item.quantity_accepted += item.quantity_accepted
            po_item.quantity_rejected += item.quantity_rejected

    # Update PO status
    po = await db.get(PurchaseOrder, grn.purchase_order_id)
    if po:
        po.total_received_value += grn.total_value

        # Check if fully received
        po_items_query = select(PurchaseOrderItem).where(
            PurchaseOrderItem.purchase_order_id == po.id
        )
        po_result = await db.execute(po_items_query)
        po_items = po_result.scalars().all()

        fully_received = all(
            item.quantity_received >= item.quantity_ordered
            for item in po_items
        )

        if fully_received:
            po.status = "FULLY_RECEIVED"
        else:
            po.status = "PARTIALLY_RECEIVED"

    grn.status = "ACCEPTED"
    await db.commit()

    # Update Product Costs (COGS) using Weighted Average Cost
    costing_result = None
    try:
        costing_service = CostingService(db)
        costing_result = await costing_service.update_cost_on_grn_acceptance(grn_id)
    except Exception as e:
        # Log error but don't fail the GRN acceptance
        import logging
        logging.getLogger(__name__).error(f"Failed to update product costs for GRN {grn_id}: {e}")

    return {
        "message": "GRN accepted and PO updated",
        "status": grn.status,
        "po_status": po.status if po else None,
        "cost_update": costing_result,
    }


@router.post("/{grn_id}/put-away")
async def complete_put_away(
    grn_id: UUID,
    items: List[dict],  # [{"item_id": uuid, "bin_id": uuid, "bin_location": str}]
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Complete put-away for GRN items."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )

    if grn.status != "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot put away GRN with status {grn.status}"
        )

    for item_data in items:
        item = await db.get(GRNItem, item_data["item_id"])
        if item and item.grn_id == grn_id:
            item.bin_id = item_data.get("bin_id")
            item.bin_location = item_data.get("bin_location")

    grn.put_away_complete = True
    grn.put_away_at = datetime.now(timezone.utc)
    grn.status = "PUT_AWAY_COMPLETE"

    await db.commit()

    return {"message": "Put-away completed", "status": grn.status}


@router.post("/{grn_id}/cancel")
async def cancel_grn(
    grn_id: UUID,
    reason: str,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Cancel a GRN."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )

    if grn.status in ["ACCEPTED", "PUT_AWAY_COMPLETE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel GRN that has been accepted or put away"
        )

    grn.status = "CANCELLED"
    grn.receiving_remarks = f"Cancelled: {reason}"

    await db.commit()

    return {"message": "GRN cancelled", "status": grn.status}
