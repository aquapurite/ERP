"""Batch Management API endpoints - SAP MSC1N/MSC2N equivalent."""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.batch import BatchMaster
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.vendor import Vendor
from app.models.inventory import StockItem, StockMovement
from app.models.purchase import GoodsReceiptNote, GRNItem
from app.services.batch_picking_service import BatchPickingService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Schemas ====================

class BatchCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    batch_number: str
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    vendor_batch_number: Optional[str] = None
    vendor_id: Optional[UUID] = None
    quality_grade: str = "A"
    quantity_received: int = 0
    unit_cost: float = 0
    notes: Optional[str] = None


class BatchStatusUpdate(BaseModel):
    new_status: str  # UNRESTRICTED, RESTRICTED, BLOCKED


class BatchPickRequest(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity_needed: int
    strategy: str = "FEFO"  # FEFO or FIFO


class BatchReservation(BaseModel):
    batch_id: UUID
    quantity: int


class BatchReserveRequest(BaseModel):
    reservations: List[BatchReservation]


class BatchIssueItem(BaseModel):
    batch_id: UUID
    quantity: int
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None


class BatchIssueRequest(BaseModel):
    issues: List[BatchIssueItem]


# ==================== Endpoints ====================

@router.post("")
async def create_batch(
    payload: BatchCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a batch master record (SAP MSC1N)."""
    # Validate product exists
    product = await db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate warehouse exists
    warehouse = await db.get(Warehouse, payload.warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # Check for duplicate
    existing = await db.execute(
        select(BatchMaster).where(
            and_(
                BatchMaster.batch_number == payload.batch_number,
                BatchMaster.product_id == payload.product_id,
                BatchMaster.warehouse_id == payload.warehouse_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Batch {payload.batch_number} already exists for this product/warehouse"
        )

    # Calculate shelf life
    shelf_life_days = None
    if payload.manufacturing_date and payload.expiry_date:
        shelf_life_days = (payload.expiry_date - payload.manufacturing_date).days

    # Calculate total value
    total_value = payload.quantity_received * payload.unit_cost

    batch = BatchMaster(
        batch_number=payload.batch_number,
        product_id=payload.product_id,
        warehouse_id=payload.warehouse_id,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
        vendor_batch_number=payload.vendor_batch_number,
        vendor_id=payload.vendor_id,
        quality_grade=payload.quality_grade,
        quantity_received=payload.quantity_received,
        quantity_available=payload.quantity_received,
        unit_cost=payload.unit_cost,
        total_value=total_value,
        shelf_life_days=shelf_life_days,
        notes=payload.notes,
    )
    db.add(batch)
    await db.flush()

    return {
        "id": str(batch.id),
        "batch_number": batch.batch_number,
        "product_id": str(batch.product_id),
        "warehouse_id": str(batch.warehouse_id),
        "batch_status": batch.batch_status,
        "quantity_received": batch.quantity_received,
        "quantity_available": batch.quantity_available,
        "unit_cost": float(batch.unit_cost or 0),
        "total_value": float(batch.total_value or 0),
        "shelf_life_days": batch.shelf_life_days,
        "manufacturing_date": batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
        "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
        "message": "Batch created successfully",
    }


@router.get("")
async def list_batches(
    db: DB,
    current_user: User = Depends(get_current_user),
    product_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    batch_status: Optional[str] = None,
    is_expired: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List batches with filters."""
    today = date.today()
    query = select(BatchMaster).options(
        joinedload(BatchMaster.product),
        joinedload(BatchMaster.warehouse),
    )

    if product_id:
        query = query.where(BatchMaster.product_id == product_id)
    if warehouse_id:
        query = query.where(BatchMaster.warehouse_id == warehouse_id)
    if batch_status:
        query = query.where(BatchMaster.batch_status == batch_status)
    if is_expired is True:
        query = query.where(BatchMaster.expiry_date < today)
    if is_expired is False:
        query = query.where(
            or_(BatchMaster.expiry_date >= today, BatchMaster.expiry_date.is_(None))
        )
    if search:
        query = query.where(BatchMaster.batch_number.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(desc(BatchMaster.created_at))
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    batches = result.unique().scalars().all()

    items = []
    for b in batches:
        days_until_expiry = None
        if b.expiry_date:
            days_until_expiry = (b.expiry_date - today).days

        items.append({
            "id": str(b.id),
            "batch_number": b.batch_number,
            "product_id": str(b.product_id),
            "product_name": b.product.name if b.product else None,
            "product_sku": b.product.sku if b.product else None,
            "warehouse_id": str(b.warehouse_id),
            "warehouse_name": b.warehouse.name if b.warehouse else None,
            "batch_status": b.batch_status,
            "manufacturing_date": b.manufacturing_date.isoformat() if b.manufacturing_date else None,
            "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
            "days_until_expiry": days_until_expiry,
            "vendor_batch_number": b.vendor_batch_number,
            "quality_grade": b.quality_grade,
            "quantity_received": b.quantity_received,
            "quantity_available": b.quantity_available,
            "quantity_reserved": b.quantity_reserved,
            "quantity_issued": b.quantity_issued,
            "unit_cost": float(b.unit_cost or 0),
            "total_value": float(b.total_value or 0),
            "shelf_life_days": b.shelf_life_days,
            "notes": b.notes,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if size > 0 else 0,
    }


@router.get("/expiry-alerts")
async def get_expiry_alerts(
    db: DB,
    current_user: User = Depends(get_current_user),
    days_ahead: int = Query(30, ge=1, le=365),
    warehouse_id: Optional[UUID] = None,
):
    """Get batches nearing expiry (within days_ahead days)."""
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    query = (
        select(BatchMaster)
        .options(
            joinedload(BatchMaster.product),
            joinedload(BatchMaster.warehouse),
        )
        .where(
            and_(
                BatchMaster.expiry_date.isnot(None),
                BatchMaster.expiry_date <= cutoff,
                BatchMaster.batch_status == "UNRESTRICTED",
                BatchMaster.quantity_available > 0,
            )
        )
        .order_by(BatchMaster.expiry_date.asc())
    )
    if warehouse_id:
        query = query.where(BatchMaster.warehouse_id == warehouse_id)

    result = await db.execute(query)
    batches = result.unique().scalars().all()

    alerts = []
    for b in batches:
        days_left = (b.expiry_date - today).days if b.expiry_date else None
        severity = "GREEN"
        if days_left is not None:
            if days_left <= 0:
                severity = "RED"
            elif days_left <= 7:
                severity = "RED"
            elif days_left <= 30:
                severity = "YELLOW"

        alerts.append({
            "id": str(b.id),
            "batch_number": b.batch_number,
            "product_name": b.product.name if b.product else None,
            "product_sku": b.product.sku if b.product else None,
            "warehouse_name": b.warehouse.name if b.warehouse else None,
            "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
            "days_until_expiry": days_left,
            "severity": severity,
            "quantity_available": b.quantity_available,
            "total_value": float(b.total_value or 0),
            "quality_grade": b.quality_grade,
        })

    # Summary counts
    red_count = sum(1 for a in alerts if a["severity"] == "RED")
    yellow_count = sum(1 for a in alerts if a["severity"] == "YELLOW")
    green_count = sum(1 for a in alerts if a["severity"] == "GREEN")

    return {
        "alerts": alerts,
        "total": len(alerts),
        "summary": {
            "red": red_count,
            "yellow": yellow_count,
            "green": green_count,
        },
    }


@router.get("/stock-overview")
async def batch_stock_overview(
    db: DB,
    product_id: UUID = Query(...),
    warehouse_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Batch-wise stock overview for a product."""
    today = date.today()
    query = (
        select(BatchMaster)
        .options(joinedload(BatchMaster.warehouse))
        .where(BatchMaster.product_id == product_id)
        .order_by(BatchMaster.expiry_date.asc().nullslast())
    )
    if warehouse_id:
        query = query.where(BatchMaster.warehouse_id == warehouse_id)

    result = await db.execute(query)
    batches = result.unique().scalars().all()

    items = []
    total_available = 0
    total_reserved = 0
    total_issued = 0

    for b in batches:
        days_left = (b.expiry_date - today).days if b.expiry_date else None
        items.append({
            "id": str(b.id),
            "batch_number": b.batch_number,
            "warehouse_name": b.warehouse.name if b.warehouse else None,
            "batch_status": b.batch_status,
            "quantity_available": b.quantity_available,
            "quantity_reserved": b.quantity_reserved,
            "quantity_issued": b.quantity_issued,
            "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
            "days_until_expiry": days_left,
            "quality_grade": b.quality_grade,
            "unit_cost": float(b.unit_cost or 0),
        })
        total_available += b.quantity_available
        total_reserved += b.quantity_reserved
        total_issued += b.quantity_issued

    return {
        "product_id": str(product_id),
        "batches": items,
        "total_batches": len(items),
        "total_available": total_available,
        "total_reserved": total_reserved,
        "total_issued": total_issued,
    }


@router.get("/{batch_id}")
async def get_batch_detail(
    batch_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get batch detail with linked stock items and movement history."""
    batch = await db.execute(
        select(BatchMaster)
        .options(
            joinedload(BatchMaster.product),
            joinedload(BatchMaster.warehouse),
            joinedload(BatchMaster.vendor),
        )
        .where(BatchMaster.id == batch_id)
    )
    b = batch.unique().scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")

    today = date.today()
    days_until_expiry = (b.expiry_date - today).days if b.expiry_date else None

    # Get linked stock items
    stock_items_q = select(StockItem).where(StockItem.batch_id == batch_id).limit(100)
    si_result = await db.execute(stock_items_q)
    stock_items = si_result.scalars().all()

    # Get movements
    movements_q = (
        select(StockMovement)
        .where(StockMovement.batch_id == batch_id)
        .order_by(desc(StockMovement.movement_date))
        .limit(50)
    )
    mv_result = await db.execute(movements_q)
    movements = mv_result.scalars().all()

    return {
        "id": str(b.id),
        "batch_number": b.batch_number,
        "product_id": str(b.product_id),
        "product_name": b.product.name if b.product else None,
        "product_sku": b.product.sku if b.product else None,
        "warehouse_id": str(b.warehouse_id),
        "warehouse_name": b.warehouse.name if b.warehouse else None,
        "batch_status": b.batch_status,
        "manufacturing_date": b.manufacturing_date.isoformat() if b.manufacturing_date else None,
        "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
        "days_until_expiry": days_until_expiry,
        "vendor_batch_number": b.vendor_batch_number,
        "vendor_name": b.vendor.company_name if b.vendor else None,
        "quality_grade": b.quality_grade,
        "quantity_received": b.quantity_received,
        "quantity_available": b.quantity_available,
        "quantity_reserved": b.quantity_reserved,
        "quantity_issued": b.quantity_issued,
        "unit_cost": float(b.unit_cost or 0),
        "total_value": float(b.total_value or 0),
        "shelf_life_days": b.shelf_life_days,
        "minimum_remaining_shelf_life_days": b.minimum_remaining_shelf_life_days,
        "notes": b.notes,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
        "stock_items": [
            {
                "id": str(si.id),
                "serial_number": si.serial_number,
                "status": si.status,
                "batch_number": si.batch_number,
            }
            for si in stock_items
        ],
        "movements": [
            {
                "id": str(m.id),
                "movement_number": m.movement_number,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "movement_date": m.movement_date.isoformat() if m.movement_date else None,
                "reference_type": m.reference_type,
                "notes": m.notes,
            }
            for m in movements
        ],
    }


@router.put("/{batch_id}/status")
async def update_batch_status(
    batch_id: UUID,
    payload: BatchStatusUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Change batch status (UNRESTRICTED, RESTRICTED, BLOCKED)."""
    batch = await db.get(BatchMaster, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    valid_statuses = ["UNRESTRICTED", "RESTRICTED", "BLOCKED"]
    if payload.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    # Can't unblock expired batch
    today = date.today()
    if payload.new_status == "UNRESTRICTED" and batch.expiry_date and batch.expiry_date < today:
        raise HTTPException(
            status_code=400,
            detail="Cannot set expired batch to UNRESTRICTED. Batch expired on "
                   f"{batch.expiry_date.isoformat()}"
        )

    old_status = batch.batch_status
    batch.batch_status = payload.new_status
    batch.updated_at = datetime.now(timezone.utc)

    return {
        "id": str(batch.id),
        "batch_number": batch.batch_number,
        "old_status": old_status,
        "new_status": batch.batch_status,
        "message": f"Batch status changed from {old_status} to {batch.batch_status}",
    }


@router.post("/auto-create-from-grn/{grn_id}")
async def auto_create_batches_from_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Auto-create batch records from a GRN for batch-managed products."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    items_q = select(GRNItem).where(GRNItem.grn_id == grn_id)
    result = await db.execute(items_q)
    grn_items = result.scalars().all()

    created_batches = []
    skipped = []

    for item in grn_items:
        if not item.batch_number:
            skipped.append({"grn_item_id": str(item.id), "reason": "No batch_number"})
            continue

        product = await db.get(Product, item.product_id)
        if not product or not product.is_batch_managed:
            skipped.append({
                "grn_item_id": str(item.id),
                "reason": "Product not batch-managed"
            })
            continue

        # Check if batch already exists
        existing = await db.execute(
            select(BatchMaster).where(
                and_(
                    BatchMaster.batch_number == item.batch_number,
                    BatchMaster.product_id == item.product_id,
                    BatchMaster.warehouse_id == grn.warehouse_id,
                )
            )
        )
        batch = existing.scalar_one_or_none()

        qty_accepted = getattr(item, 'quantity_accepted', None) or item.quantity_received
        unit_price = float(getattr(item, 'unit_price', 0) or 0)

        if batch:
            # Update existing batch
            batch.quantity_received += qty_accepted
            batch.quantity_available += qty_accepted
            batch.total_value = batch.quantity_available * float(batch.unit_cost or 0)
            batch.updated_at = datetime.now(timezone.utc)
            created_batches.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "action": "updated",
                "quantity_added": qty_accepted,
            })
        else:
            # Calculate shelf life
            shelf_life_days = None
            mfg_date = getattr(item, 'manufacturing_date', None)
            exp_date = getattr(item, 'expiry_date', None)
            if mfg_date and exp_date:
                shelf_life_days = (exp_date - mfg_date).days

            batch = BatchMaster(
                batch_number=item.batch_number,
                product_id=item.product_id,
                warehouse_id=grn.warehouse_id,
                manufacturing_date=mfg_date,
                expiry_date=exp_date,
                vendor_id=grn.vendor_id,
                grn_id=grn.id,
                grn_item_id=item.id,
                quantity_received=qty_accepted,
                quantity_available=qty_accepted,
                unit_cost=unit_price,
                total_value=unit_price * qty_accepted,
                shelf_life_days=shelf_life_days,
            )
            db.add(batch)
            await db.flush()

            created_batches.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "action": "created",
                "quantity": qty_accepted,
            })

        # Link stock items to this batch
        stock_items_q = select(StockItem).where(
            and_(
                StockItem.product_id == item.product_id,
                StockItem.warehouse_id == grn.warehouse_id,
                StockItem.batch_number == item.batch_number,
                StockItem.batch_id.is_(None),
            )
        )
        si_result = await db.execute(stock_items_q)
        for si in si_result.scalars().all():
            si.batch_id = batch.id

    return {
        "grn_id": str(grn_id),
        "batches_created_or_updated": created_batches,
        "skipped": skipped,
        "total_processed": len(created_batches),
        "total_skipped": len(skipped),
    }


# ==================== Batch Picking Endpoints ====================

@router.post("/pick")
async def pick_batches(
    payload: BatchPickRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Execute FEFO/FIFO batch picking recommendation (does NOT modify stock)."""
    service = BatchPickingService(db)

    if payload.strategy.upper() == "FIFO":
        picks = await service.pick_batches_fifo(
            payload.product_id, payload.warehouse_id, payload.quantity_needed
        )
    else:
        picks = await service.pick_batches_fefo(
            payload.product_id, payload.warehouse_id, payload.quantity_needed
        )

    total_picked = sum(p["pick_quantity"] for p in picks)
    shortfall = max(0, payload.quantity_needed - total_picked)

    return {
        "strategy": payload.strategy.upper(),
        "quantity_needed": payload.quantity_needed,
        "total_picked": total_picked,
        "shortfall": shortfall,
        "fully_fulfilled": shortfall == 0,
        "picks": picks,
    }


@router.post("/reserve")
async def reserve_batches(
    payload: BatchReserveRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Reserve quantity from specific batches."""
    service = BatchPickingService(db)
    results = await service.reserve_batches(
        [{"batch_id": r.batch_id, "quantity": r.quantity} for r in payload.reservations]
    )
    errors = [r for r in results if "error" in r]
    return {
        "results": results,
        "total_reserved": len([r for r in results if "error" not in r]),
        "errors": len(errors),
    }


@router.post("/issue")
async def issue_batches(
    payload: BatchIssueRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Issue stock from batches (after picking confirmed)."""
    service = BatchPickingService(db)
    results = await service.issue_batches(
        [
            {
                "batch_id": i.batch_id,
                "quantity": i.quantity,
                "reference_type": i.reference_type,
                "reference_id": i.reference_id,
            }
            for i in payload.issues
        ],
        user_id=current_user.id,
    )
    errors = [r for r in results if "error" in r]
    return {
        "results": results,
        "total_issued": len([r for r in results if "error" not in r]),
        "errors": len(errors),
    }
