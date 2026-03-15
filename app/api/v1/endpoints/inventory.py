"""Inventory API endpoints for stock management."""
from typing import Optional, List
import uuid
from math import ceil
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Query, Depends, Body
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.inventory import StockItemStatus, StockMovementType
from app.schemas.inventory import (
    StockItemCreate,
    StockItemUpdate,
    StockItemResponse,
    StockItemDetailResponse,
    StockItemListResponse,
    InventorySummaryResponse,
    InventorySummaryDetail,
    InventorySummaryListResponse,
    InventoryThresholdUpdate,
    StockMovementResponse,
    StockMovementDetail,
    StockMovementListResponse,
    BulkStockReceipt,
    BulkStockReceiptResponse,
    InventoryStats,
    InventoryDashboardStats,
    StockVerificationRequest,
    StockVerificationResponse,
    BulkStockVerificationRequest,
    BulkStockVerificationResponse,
)
from app.services.inventory_service import InventoryService
from app.services.audit_service import AuditService


router = APIRouter(tags=["Inventory"])


# ==================== PUBLIC STOCK VERIFICATION (Phase 2) ====================

@router.post(
    "/verify-stock",
    response_model=StockVerificationResponse,
    summary="Verify product stock availability (Phase 2)",
    description="Real-time stock verification for Add to Cart. No authentication required."
)
async def verify_stock(
    data: StockVerificationRequest,
    db: DB,
):
    """
    Phase 2: Live stock verification for Add to Cart.

    Target response time: 300-500ms

    This endpoint checks real-time stock availability for a product.
    Used by the storefront when a customer adds items to cart.

    No authentication required for public access.
    """
    service = InventoryService(db)

    # Get inventory summary for the product
    summaries, _ = await service.get_inventory_summary(
        product_id=data.product_id,
        warehouse_id=data.warehouse_id,
        skip=0,
        limit=100,
    )

    # Calculate total available across warehouses
    total_available = 0
    primary_warehouse_id = None

    for summary in summaries:
        available = summary.available_quantity - (summary.reserved_quantity or 0)
        if available > 0:
            total_available += available
            if primary_warehouse_id is None:
                primary_warehouse_id = summary.warehouse_id

    in_stock = total_available >= data.quantity

    # Build response
    response = StockVerificationResponse(
        product_id=data.product_id,
        in_stock=in_stock,
        available_quantity=total_available,
        requested_quantity=data.quantity,
        warehouse_id=primary_warehouse_id,
    )

    if in_stock:
        # Calculate delivery estimate based on pincode if provided
        if data.pincode:
            response.delivery_estimate = "2-4 business days"
            response.message = f"In stock! Delivery available to {data.pincode}"
        else:
            response.message = "In stock and ready to ship"
    else:
        if total_available > 0:
            response.message = f"Only {total_available} units available (requested {data.quantity})"
        else:
            response.message = "Currently out of stock"

    return response


@router.post(
    "/verify-stock/bulk",
    response_model=BulkStockVerificationResponse,
    summary="Bulk verify stock for multiple products",
    description="Check stock availability for multiple products at once (e.g., for cart checkout)."
)
async def verify_stock_bulk(
    data: BulkStockVerificationRequest,
    db: DB,
):
    """
    Bulk stock verification for checkout validation.

    Checks stock availability for all items in the cart before checkout.
    """
    service = InventoryService(db)
    results = []
    all_in_stock = True

    for item in data.items:
        # Get inventory summary for each product
        summaries, _ = await service.get_inventory_summary(
            product_id=item.product_id,
            warehouse_id=item.warehouse_id,
            skip=0,
            limit=100,
        )

        # Calculate total available
        total_available = 0
        primary_warehouse_id = None

        for summary in summaries:
            available = summary.available_quantity - (summary.reserved_quantity or 0)
            if available > 0:
                total_available += available
                if primary_warehouse_id is None:
                    primary_warehouse_id = summary.warehouse_id

        in_stock = total_available >= item.quantity
        if not in_stock:
            all_in_stock = False

        results.append(StockVerificationResponse(
            product_id=item.product_id,
            in_stock=in_stock,
            available_quantity=total_available,
            requested_quantity=item.quantity,
            warehouse_id=primary_warehouse_id,
            message="In stock" if in_stock else f"Only {total_available} available",
        ))

    return BulkStockVerificationResponse(
        all_in_stock=all_in_stock,
        items=results,
    )


# ==================== STOCK RESERVATION (Checkout) ====================

from app.services.stock_reservation_service import (
    StockReservationService,
    ReservationItem,
)
from pydantic import BaseModel


class StockReservationRequest(BaseModel):
    """Request to create a stock reservation for checkout."""
    items: List[StockVerificationRequest]
    customer_id: Optional[str] = None
    session_id: Optional[str] = None


class StockReservationResponse(BaseModel):
    """Response from stock reservation."""
    success: bool
    reservation_id: Optional[str] = None
    message: str
    reserved_items: List[dict] = []
    failed_items: List[dict] = []
    expires_in_seconds: int = 600


@router.post(
    "/reserve-stock",
    response_model=StockReservationResponse,
    summary="Reserve stock for checkout",
    description="Create a temporary stock reservation when customer proceeds to checkout. Reservations auto-expire after 10 minutes."
)
async def reserve_stock_for_checkout(
    data: StockReservationRequest,
    db: DB,
):
    """
    Reserve stock for checkout process.

    Call this endpoint when customer clicks "Proceed to Checkout".
    The reservation prevents overselling by temporarily holding stock.

    - Reservation expires after 10 minutes if not confirmed
    - Call /confirm-reservation after successful payment
    - Call /release-reservation if payment fails

    No authentication required (uses session_id for guests).
    """
    service = StockReservationService(db)

    reservation_items = [
        ReservationItem(
            product_id=item.product_id,
            quantity=item.quantity,
            warehouse_id=item.warehouse_id,
        )
        for item in data.items
    ]

    result = await service.create_reservation(
        items=reservation_items,
        customer_id=data.customer_id,
        session_id=data.session_id,
    )

    return StockReservationResponse(
        success=result.success,
        reservation_id=result.reservation_id,
        message=result.message,
        reserved_items=result.reserved_items,
        failed_items=result.failed_items,
        expires_in_seconds=600,
    )


class ConfirmReservationRequest(BaseModel):
    """Request to confirm a reservation after payment."""
    reservation_id: str
    order_id: str


@router.post(
    "/confirm-reservation",
    summary="Confirm stock reservation after payment",
    description="Convert temporary reservation to permanent allocation after successful payment."
)
async def confirm_stock_reservation(
    data: ConfirmReservationRequest,
    db: DB,
):
    """
    Confirm a stock reservation after successful payment.

    This converts the soft reservation to a hard allocation in the database.
    Call this after Razorpay payment success webhook.
    """
    service = StockReservationService(db)
    success = await service.confirm_reservation(
        reservation_id=data.reservation_id,
        order_id=data.order_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation not found or already processed"
        )

    return {"success": True, "message": "Reservation confirmed and stock allocated"}


class ReleaseReservationRequest(BaseModel):
    """Request to release a reservation."""
    reservation_id: str


@router.post(
    "/release-reservation",
    summary="Release stock reservation",
    description="Release a stock reservation when payment fails or is cancelled."
)
async def release_stock_reservation(
    data: ReleaseReservationRequest,
    db: DB,
):
    """
    Release a stock reservation.

    Call this when:
    - Payment fails
    - Customer cancels checkout
    - Payment times out

    This frees up the reserved stock for other customers.
    """
    service = StockReservationService(db)
    success = await service.release_reservation(data.reservation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation not found or already released"
        )

    return {"success": True, "message": "Reservation released"}


@router.get(
    "/reservation/{reservation_id}",
    summary="Get reservation details",
    description="Check the status of a stock reservation."
)
async def get_reservation_status(
    reservation_id: str,
    db: DB,
):
    """Get the current status of a stock reservation."""
    service = StockReservationService(db)
    reservation = await service.get_reservation(reservation_id)

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found or expired"
        )

    return reservation


# ==================== WAREHOUSE AVAILABILITY CHECK ====================

class WarehouseAvailabilityItem(BaseModel):
    """Item to check availability for."""
    product_id: str
    quantity: int = 1


class WarehouseAvailabilityRequest(BaseModel):
    """Request to check warehouse availability."""
    pincode: str
    items: List[WarehouseAvailabilityItem]
    payment_mode: Optional[str] = None  # PREPAID or COD


@router.post(
    "/check-warehouse-availability",
    summary="Check inventory availability across warehouses",
    description="Find the best warehouse that can fulfill all items for a given pincode."
)
async def check_warehouse_availability(
    data: WarehouseAvailabilityRequest,
    db: DB,
):
    """
    Check which warehouse can fulfill the order items.

    This endpoint:
    1. Finds warehouses that service the given pincode
    2. Checks inventory availability for each item (including soft reservations)
    3. Returns the best warehouse that can fulfill all items

    Use this before checkout to verify delivery is possible.
    """
    from app.services.allocation_service import AllocationService

    service = AllocationService(db)

    # Convert to items format expected by the service
    items = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in data.items
    ]

    result = await service.find_best_warehouse_for_items(
        pincode=data.pincode,
        items=items,
        payment_mode=data.payment_mode
    )

    if result["found"]:
        warehouse = result["warehouse"]
        return {
            "available": True,
            "warehouse": {
                "id": warehouse["warehouse_id"],
                "code": warehouse["warehouse_code"],
                "name": warehouse["warehouse_name"],
                "estimated_days": warehouse["estimated_days"],
                "shipping_cost": warehouse["shipping_cost"]
            },
            "items": warehouse["items"],
            "warehouses_checked": result["warehouses_checked"],
            "message": f"All items available from {warehouse['warehouse_name']}"
        }
    else:
        return {
            "available": False,
            "reason": result["reason"],
            "warehouses_checked": result["warehouses_checked"],
            "all_results": result.get("all_results", []),
            "message": result["reason"]
        }


# ==================== STOCK ITEMS ====================

@router.get(
    "/stock-items",
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def list_stock_items(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    product_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    batch_number: Optional[str] = Query(None),
    grn_number: Optional[str] = Query(None, description="Filter by GRN number"),
    item_type: Optional[str] = Query(None, description="Filter by item type: FG, SP, CO, CN, AC"),
    view: str = Query("aggregate", description="View mode: 'aggregate' for inventory_summary, 'serialized' for stock_items"),
):
    """
    Get paginated list of stock items.

    Two view modes:
    - aggregate (default): Returns inventory_summary data (product-level aggregates)
    - serialized: Returns individual stock_items with serial numbers

    Requires: inventory:view permission
    """
    from app.models.inventory import InventorySummary, StockItem
    from app.models.product import Product
    from app.models.warehouse import Warehouse
    from sqlalchemy.orm import selectinload

    skip = (page - 1) * size

    if view == "serialized":
        # Serialized view - query stock_items table with all filters
        query = select(StockItem).options(
            selectinload(StockItem.product),
            selectinload(StockItem.warehouse),
        )

        conditions = []
        if warehouse_id:
            conditions.append(StockItem.warehouse_id == warehouse_id)
        if product_id:
            conditions.append(StockItem.product_id == product_id)
        if status:
            conditions.append(StockItem.status == status)
        if serial_number:
            conditions.append(StockItem.serial_number.ilike(f"%{serial_number}%"))
        if batch_number:
            conditions.append(StockItem.batch_number == batch_number)
        if grn_number:
            conditions.append(StockItem.grn_number.ilike(f"%{grn_number}%"))
        if item_type:
            # Join with Product to filter by item_type
            query = query.join(Product, StockItem.product_id == Product.id)
            conditions.append(Product.item_type == item_type)

        if conditions:
            query = query.where(and_(*conditions))

        # Count query
        count_query = select(func.count(StockItem.id))
        if item_type:
            count_query = count_query.join(Product, StockItem.product_id == Product.id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = await db.scalar(count_query) or 0

        # Paginate
        query = query.order_by(StockItem.created_at.desc()).offset(skip).limit(size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "items": [
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "warehouse_id": str(item.warehouse_id),
                    "product": {
                        "id": str(item.product_id),
                        "name": item.product.name if item.product else None,
                        "sku": item.product.sku if item.product else None,
                    },
                    "warehouse": {
                        "id": str(item.warehouse_id),
                        "name": item.warehouse.name if item.warehouse else None,
                        "code": item.warehouse.code if item.warehouse else None,
                    },
                    "serial_number": item.serial_number,
                    "barcode": item.barcode,
                    "batch_number": item.batch_number,
                    "grn_number": item.grn_number,
                    "purchase_order_id": str(item.purchase_order_id) if item.purchase_order_id else None,
                    "quantity": 1,  # Each stock_item is 1 unit
                    "reserved_quantity": 1 if item.status in ["RESERVED", "ALLOCATED"] else 0,
                    "available_quantity": 1 if item.status == "AVAILABLE" else 0,
                    "reorder_level": 0,
                    "status": item.status,
                    "received_date": item.received_date.isoformat() if item.received_date else None,
                    "item_type": item.product.item_type if item.product else None,
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": ceil(total / size) if total > 0 else 1,
        }

    else:
        # Aggregate view - query inventory_summary table
        query = select(InventorySummary).options(
            selectinload(InventorySummary.product),
            selectinload(InventorySummary.warehouse),
        )

        conditions = []
        if warehouse_id:
            conditions.append(InventorySummary.warehouse_id == warehouse_id)
        if product_id:
            conditions.append(InventorySummary.product_id == product_id)
        if status:
            # Map status to inventory condition
            if status == "LOW_STOCK":
                conditions.append(InventorySummary.available_quantity <= InventorySummary.reorder_level)
            elif status == "OUT_OF_STOCK":
                conditions.append(InventorySummary.available_quantity == 0)
            elif status == "IN_STOCK":
                conditions.append(InventorySummary.available_quantity > 0)
        if item_type:
            # Join with Product to filter by item_type
            query = query.join(Product, InventorySummary.product_id == Product.id)
            conditions.append(Product.item_type == item_type)

        if conditions:
            query = query.where(and_(*conditions))

        # Count
        count_query = select(func.count(InventorySummary.id))
        if item_type:
            count_query = count_query.join(Product, InventorySummary.product_id == Product.id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = await db.scalar(count_query) or 0

        # Paginate
        query = query.order_by(InventorySummary.product_id).offset(skip).limit(size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "items": [
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "warehouse_id": str(item.warehouse_id),
                    "product": {
                        "id": str(item.product_id),
                        "name": item.product.name if item.product else None,
                        "sku": item.product.sku if item.product else None,
                        "item_type": item.product.item_type if item.product else None,
                    },
                    "warehouse": {
                        "id": str(item.warehouse_id),
                        "name": item.warehouse.name if item.warehouse else None,
                        "code": item.warehouse.code if item.warehouse else None,
                    },
                    "serial_number": None,  # Aggregate view doesn't have serials
                    "batch_number": None,
                    "quantity": item.total_quantity,
                    "reserved_quantity": item.reserved_quantity,
                    "available_quantity": item.available_quantity,
                    "reorder_level": item.reorder_level,
                    "status": "AVAILABLE" if item.available_quantity > 0 else "OUT_OF_STOCK",
                    "item_type": item.product.item_type if item.product else None,
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": ceil(total / size) if total > 0 else 1,
        }


@router.get(
    "/stock-items/{item_id}",
    response_model=StockItemDetailResponse,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_stock_item(
    item_id: uuid.UUID,
    db: DB,
):
    """Get stock item by ID."""
    service = InventoryService(db)
    item = await service.get_stock_item_by_id(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock item not found"
        )

    response = StockItemDetailResponse.model_validate(item)
    if item.product:
        response.product_name = item.product.name
        response.product_sku = item.product.sku
    if item.warehouse:
        response.warehouse_name = item.warehouse.name
        response.warehouse_code = item.warehouse.code

    return response


@router.get(
    "/stock-items/serial/{serial_number}",
    response_model=StockItemDetailResponse,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_stock_item_by_serial(
    serial_number: str,
    db: DB,
):
    """Get stock item by serial number."""
    service = InventoryService(db)
    item = await service.get_stock_item_by_serial(serial_number)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock item not found"
        )

    response = StockItemDetailResponse.model_validate(item)
    if item.product:
        response.product_name = item.product.name
        response.product_sku = item.product.sku
    if item.warehouse:
        response.warehouse_name = item.warehouse.name
        response.warehouse_code = item.warehouse.code

    return response


@router.post(
    "/stock-items",
    response_model=StockItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("inventory:create"))]
)
async def create_stock_item(
    data: StockItemCreate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Create a single stock item.
    Requires: inventory:create permission
    """
    service = InventoryService(db)

    # Check for duplicate serial number
    if data.serial_number:
        existing = await service.get_stock_item_by_serial(data.serial_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Serial number already exists"
            )

    item = await service.create_stock_item(data.model_dump(), created_by=current_user.id)

    await AuditService(db).log(
        action="CREATE", entity_type="StockItem", entity_id=item.id,
        user_id=current_user.id,
        new_values={"serial_number": data.serial_number, "product_id": str(data.product_id), "warehouse_id": str(data.warehouse_id)},
        description=f"Created stock item {data.serial_number or 'N/A'}",
    )
    await db.commit()

    return StockItemResponse.model_validate(item)


@router.post(
    "/stock-items/bulk-receive",
    response_model=BulkStockReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("inventory:create"))]
)
async def bulk_receive_stock(
    data: BulkStockReceipt,
    db: DB,
    current_user: CurrentUser,
):
    """
    Bulk receive stock items (GRN).
    Requires: inventory:create permission
    """
    service = InventoryService(db)

    items = await service.bulk_receive_stock(
        warehouse_id=data.warehouse_id,
        grn_number=data.grn_number,
        items=[item.model_dump() for item in data.items],
        purchase_order_id=data.purchase_order_id,
        vendor_id=data.vendor_id,
        created_by=current_user.id,
    )

    await AuditService(db).log(
        action="BULK_RECEIVE", entity_type="StockItem", entity_id=data.warehouse_id,
        user_id=current_user.id,
        new_values={"grn_number": data.grn_number, "items_count": len(items), "warehouse_id": str(data.warehouse_id)},
        description=f"Bulk received {len(items)} stock items (GRN: {data.grn_number})",
    )
    await db.commit()

    return BulkStockReceiptResponse(
        message=f"Successfully received {len(items)} stock items",
        grn_number=data.grn_number,
        items_count=len(items),
    )


@router.put(
    "/stock-items/{item_id}",
    response_model=StockItemResponse,
    dependencies=[Depends(require_permissions("inventory:update"))]
)
async def update_stock_item(
    item_id: uuid.UUID,
    data: StockItemUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Update a stock item.
    Requires: inventory:update permission
    """
    service = InventoryService(db)
    item = await service.get_stock_item_by_id(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock item not found"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(item, key):
            setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return StockItemResponse.model_validate(item)


@router.delete(
    "/stock-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("inventory:delete"))]
)
async def delete_stock_item(
    item_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Delete a stock item (soft delete - marks as DISPOSED).
    Requires: inventory:delete permission
    """
    service = InventoryService(db)
    item = await service.get_stock_item_by_id(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock item not found"
        )

    # Check if item is allocated to an order
    if item.order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete stock item that is allocated to an order"
        )

    # Soft delete - mark as DISPOSED
    item.status = StockItemStatus.DISPOSED.value
    item.notes = f"Deleted by user on {datetime.now(timezone.utc).isoformat()}"

    await AuditService(db).log(
        action="DELETE", entity_type="StockItem", entity_id=item_id,
        user_id=current_user.id,
        old_values={"serial_number": item.serial_number, "status": "DISPOSED"},
        description=f"Disposed stock item {item.serial_number or str(item_id)[:8]}",
    )

    await db.commit()
    return None


# ==================== INVENTORY SUMMARY ====================

@router.get(
    "/summary",
    response_model=InventorySummaryListResponse,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_inventory_summary(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    product_id: Optional[uuid.UUID] = Query(None),
    low_stock_only: bool = Query(False),
    out_of_stock_only: bool = Query(False),
):
    """
    Get inventory summary per product per warehouse.
    Requires: inventory:view permission
    """
    service = InventoryService(db)
    skip = (page - 1) * size

    summaries, total = await service.get_inventory_summary(
        warehouse_id=warehouse_id,
        product_id=product_id,
        low_stock_only=low_stock_only,
        out_of_stock_only=out_of_stock_only,
        skip=skip,
        limit=size,
    )

    items = []
    for s in summaries:
        detail = InventorySummaryDetail.model_validate(s)
        if s.product:
            detail.product_name = s.product.name
            detail.product_sku = s.product.sku
        if s.warehouse:
            detail.warehouse_name = s.warehouse.name
            detail.warehouse_code = s.warehouse.code
        items.append(detail)

    return InventorySummaryListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get(
    "/low-stock",
    response_model=InventorySummaryListResponse,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_low_stock_items(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    warehouse_id: Optional[uuid.UUID] = Query(None),
):
    """Get items below reorder level."""
    service = InventoryService(db)
    skip = (page - 1) * size

    summaries, total = await service.get_inventory_summary(
        warehouse_id=warehouse_id,
        low_stock_only=True,
        skip=skip,
        limit=size,
    )

    items = []
    for s in summaries:
        detail = InventorySummaryDetail.model_validate(s)
        if s.product:
            detail.product_name = s.product.name
            detail.product_sku = s.product.sku
        if s.warehouse:
            detail.warehouse_name = s.warehouse.name
            detail.warehouse_code = s.warehouse.code
        items.append(detail)

    return InventorySummaryListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


# ==================== STOCK MOVEMENTS ====================

@router.get(
    "/movements",
    response_model=StockMovementListResponse,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_stock_movements(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    product_id: Optional[uuid.UUID] = Query(None),
    movement_type: Optional[StockMovementType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """
    Get stock movement history.
    Requires: inventory:view permission
    """
    service = InventoryService(db)
    skip = (page - 1) * size

    movements, total = await service.get_stock_movements(
        warehouse_id=warehouse_id,
        product_id=product_id,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=size,
    )

    items = []
    for m in movements:
        detail = StockMovementDetail.model_validate(m)
        if m.product:
            detail.product_name = m.product.name
            detail.product_sku = m.product.sku
        if m.warehouse:
            detail.warehouse_name = m.warehouse.name
        if m.stock_item:
            detail.serial_number = m.stock_item.serial_number
        items.append(detail)

    return StockMovementListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


# ==================== STATS ====================

@router.get(
    "/stats",
    response_model=InventoryStats,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_inventory_stats(
    db: DB,
    warehouse_id: Optional[uuid.UUID] = Query(None),
):
    """
    Get inventory statistics for Stock Items page.
    Returns: total_skus, in_stock, low_stock, out_of_stock
    Requires: inventory:view permission
    """
    service = InventoryService(db)
    stats = await service.get_inventory_stats(warehouse_id=warehouse_id)
    return stats


@router.get(
    "/dashboard-stats",
    response_model=InventoryDashboardStats,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def get_inventory_dashboard_stats(
    db: DB,
    warehouse_id: Optional[uuid.UUID] = Query(None),
):
    """
    Get inventory statistics for Dashboard Summary page.
    Returns: total_items, total_warehouses, pending_transfers, low_stock_items
    Requires: inventory:view permission
    """
    service = InventoryService(db)
    stats = await service.get_dashboard_stats(warehouse_id=warehouse_id)
    return InventoryDashboardStats(**stats)


# ==================== STOCK ALERTS ====================

@router.post(
    "/alerts/send",
    dependencies=[Depends(require_permissions("inventory:update"))]
)
async def send_stock_alerts(
    db: DB,
    current_user: CurrentUser,
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Filter by warehouse"),
    manager_email: str = Query("inventory@aquapurite.com", description="Email for alerts"),
    manager_phone: Optional[str] = Query(None, description="Phone for SMS alerts"),
):
    """
    Check inventory levels and send notifications for low/out of stock items.

    This endpoint can be called:
    - Manually by inventory managers
    - Automatically via scheduled jobs/cron

    Requires: inventory:update permission
    """
    from app.services.notification_service import check_and_send_stock_alerts

    result = await check_and_send_stock_alerts(
        db=db,
        warehouse_id=str(warehouse_id) if warehouse_id else None,
        manager_email=manager_email,
        manager_phone=manager_phone,
    )

    return {
        "success": True,
        "message": "Stock alert check completed",
        "alerts_sent": result["alerts_sent"],
        "total_items_checked": result["total_items_checked"],
    }


@router.get(
    "/alerts/preview",
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def preview_stock_alerts(
    db: DB,
    warehouse_id: Optional[uuid.UUID] = Query(None),
):
    """
    Preview which items would trigger alerts without actually sending notifications.

    Returns list of items that are low stock or out of stock.
    Requires: inventory:view permission
    """
    from app.models.inventory import InventorySummary
    from app.models.product import Product
    from app.models.warehouse import Warehouse
    from sqlalchemy.orm import selectinload

    query = select(InventorySummary).options(
        selectinload(InventorySummary.product),
        selectinload(InventorySummary.warehouse),
    ).where(
        InventorySummary.available_quantity <= InventorySummary.reorder_level
    )

    if warehouse_id:
        query = query.where(InventorySummary.warehouse_id == warehouse_id)

    query = query.order_by(InventorySummary.available_quantity.asc())

    result = await db.execute(query)
    items = result.scalars().unique().all()

    alerts = []
    for item in items:
        alert_type = "out_of_stock" if item.available_quantity == 0 else "low_stock"
        alerts.append({
            "product_id": str(item.product_id),
            "product_name": item.product.name if item.product else "Unknown",
            "product_sku": item.product.sku if item.product else "N/A",
            "warehouse_id": str(item.warehouse_id),
            "warehouse_name": item.warehouse.name if item.warehouse else "Unknown",
            "current_quantity": item.available_quantity,
            "reorder_level": item.reorder_level or 10,
            "alert_type": alert_type,
        })

    return {
        "total_alerts": len(alerts),
        "out_of_stock_count": len([a for a in alerts if a["alert_type"] == "out_of_stock"]),
        "low_stock_count": len([a for a in alerts if a["alert_type"] == "low_stock"]),
        "items": alerts,
    }


# ==================== PHYSICAL INVENTORY / CYCLE COUNT (SAP MI01/MI04/MI07) ====================

from app.models.inventory import PhysicalInventoryCount, PhysicalInventoryItem, InventorySummary, StockMovement
from app.models.product import Product
from app.models.warehouse import Warehouse


async def _generate_count_number(db) -> str:
    """Generate unique physical count number."""
    from datetime import date as date_type
    today = date_type.today()
    prefix = f"PC-{today.strftime('%Y%m')}-"
    result = await db.execute(
        select(func.count(PhysicalInventoryCount.id)).where(
            PhysicalInventoryCount.count_number.like(f"{prefix}%")
        )
    )
    count = result.scalar() or 0
    return f"{prefix}{str(count + 1).zfill(4)}"


@router.post(
    "/physical-counts",
    summary="Create physical inventory count",
    description="Create a new physical count. Auto-populates items from inventory summary for the selected warehouse."
)
async def create_physical_count(
    db: DB,
    current_user: CurrentUser,
    warehouse_id: uuid.UUID = Body(..., embed=True),
    count_type: str = Body("FULL", embed=True),
    planned_date: str = Body(..., embed=True),
    notes: Optional[str] = Body(None, embed=True),
):
    from datetime import date as date_type

    # Validate warehouse exists
    wh = await db.get(Warehouse, warehouse_id)
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    count_number = await _generate_count_number(db)
    parsed_date = date_type.fromisoformat(planned_date)

    count = PhysicalInventoryCount(
        count_number=count_number,
        count_type=count_type,
        status="PLANNED",
        warehouse_id=warehouse_id,
        planned_date=parsed_date,
        notes=notes,
        created_by=current_user.id,
    )
    db.add(count)
    await db.flush()

    # Auto-populate items from InventorySummary
    inv_query = select(InventorySummary).options(
        selectinload(InventorySummary.product)
    ).where(InventorySummary.warehouse_id == warehouse_id)
    inv_result = await db.execute(inv_query)
    summaries = inv_result.scalars().unique().all()

    for s in summaries:
        item = PhysicalInventoryItem(
            count_id=count.id,
            product_id=s.product_id,
            variant_id=s.variant_id,
            sku=s.product.sku if s.product else "N/A",
            product_name=s.product.name if s.product else "Unknown",
            system_quantity=s.total_quantity or 0,
            unit_cost=float(s.average_cost or 0),
            count_status="PENDING",
        )
        db.add(item)

    await db.commit()
    await db.refresh(count)

    return {
        "id": str(count.id),
        "count_number": count.count_number,
        "count_type": count.count_type,
        "status": count.status,
        "warehouse_id": str(count.warehouse_id),
        "planned_date": str(count.planned_date),
        "total_items": len(summaries),
        "message": f"Physical count {count.count_number} created with {len(summaries)} items"
    }


@router.get(
    "/physical-counts",
    summary="List physical inventory counts"
)
async def list_physical_counts(
    db: DB,
    current_user: CurrentUser,
    status_filter: Optional[str] = Query(None, alias="status"),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    query = select(PhysicalInventoryCount).options(
        selectinload(PhysicalInventoryCount.warehouse)
    )
    count_query = select(func.count(PhysicalInventoryCount.id))

    if status_filter:
        query = query.where(PhysicalInventoryCount.status == status_filter.upper())
        count_query = count_query.where(PhysicalInventoryCount.status == status_filter.upper())
    if warehouse_id:
        query = query.where(PhysicalInventoryCount.warehouse_id == warehouse_id)
        count_query = count_query.where(PhysicalInventoryCount.warehouse_id == warehouse_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(PhysicalInventoryCount.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    counts = result.scalars().unique().all()

    return {
        "items": [
            {
                "id": str(c.id),
                "count_number": c.count_number,
                "count_type": c.count_type,
                "status": c.status,
                "warehouse_id": str(c.warehouse_id),
                "warehouse_name": c.warehouse.name if c.warehouse else None,
                "planned_date": str(c.planned_date),
                "total_items_counted": c.total_items_counted or 0,
                "total_variances": c.total_variances or 0,
                "variance_value": float(c.variance_value or 0),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in counts
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if size > 0 else 0,
    }


@router.get(
    "/physical-counts/{count_id}",
    summary="Get physical count detail with items"
)
async def get_physical_count(
    count_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    query = select(PhysicalInventoryCount).options(
        selectinload(PhysicalInventoryCount.items),
        selectinload(PhysicalInventoryCount.warehouse),
    ).where(PhysicalInventoryCount.id == count_id)

    result = await db.execute(query)
    count = result.scalars().unique().first()
    if not count:
        raise HTTPException(status_code=404, detail="Physical count not found")

    return {
        "id": str(count.id),
        "count_number": count.count_number,
        "count_type": count.count_type,
        "status": count.status,
        "warehouse_id": str(count.warehouse_id),
        "warehouse_name": count.warehouse.name if count.warehouse else None,
        "planned_date": str(count.planned_date),
        "started_at": count.started_at.isoformat() if count.started_at else None,
        "completed_at": count.completed_at.isoformat() if count.completed_at else None,
        "total_items_counted": count.total_items_counted or 0,
        "total_variances": count.total_variances or 0,
        "variance_value": float(count.variance_value or 0),
        "notes": count.notes,
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "sku": item.sku,
                "product_name": item.product_name,
                "bin_location": item.bin_location,
                "system_quantity": item.system_quantity,
                "counted_quantity": item.counted_quantity,
                "variance": item.variance,
                "variance_value": float(item.variance_value or 0),
                "unit_cost": float(item.unit_cost or 0),
                "count_status": item.count_status,
                "recount_required": item.recount_required,
                "remarks": item.remarks,
                "counted_at": item.counted_at.isoformat() if item.counted_at else None,
            }
            for item in (count.items or [])
        ],
    }


@router.put(
    "/physical-counts/{count_id}/items/{item_id}",
    summary="Record counted quantity for an item"
)
async def update_physical_count_item(
    count_id: uuid.UUID,
    item_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    counted_quantity: int = Body(..., embed=True),
    remarks: Optional[str] = Body(None, embed=True),
):
    # Verify count exists and is in correct status
    count = await db.get(PhysicalInventoryCount, count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Physical count not found")
    if count.status not in ("PLANNED", "IN_PROGRESS", "COUNTING"):
        raise HTTPException(status_code=400, detail=f"Cannot update items when count status is {count.status}")

    item = await db.get(PhysicalInventoryItem, item_id)
    if not item or item.count_id != count_id:
        raise HTTPException(status_code=404, detail="Item not found in this count")

    # Update the item
    item.counted_quantity = counted_quantity
    item.variance = counted_quantity - item.system_quantity
    item.variance_value = round(item.variance * float(item.unit_cost or 0), 2)
    item.count_status = "VARIANCE" if item.variance != 0 else "COUNTED"
    item.counted_by = current_user.id
    item.counted_at = datetime.now(timezone.utc)
    item.remarks = remarks

    # Update count status to IN_PROGRESS if still PLANNED
    if count.status == "PLANNED":
        count.status = "IN_PROGRESS"
        count.started_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "id": str(item.id),
        "sku": item.sku,
        "system_quantity": item.system_quantity,
        "counted_quantity": item.counted_quantity,
        "variance": item.variance,
        "variance_value": float(item.variance_value or 0),
        "count_status": item.count_status,
        "message": "Item updated successfully"
    }


@router.post(
    "/physical-counts/{count_id}/approve",
    summary="Approve physical count and create stock adjustments"
)
async def approve_physical_count(
    count_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    query = select(PhysicalInventoryCount).options(
        selectinload(PhysicalInventoryCount.items)
    ).where(PhysicalInventoryCount.id == count_id)

    result = await db.execute(query)
    count = result.scalars().unique().first()
    if not count:
        raise HTTPException(status_code=404, detail="Physical count not found")
    if count.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Count already approved")
    if count.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot approve a cancelled count")

    # Calculate totals
    items_counted = 0
    variance_items = 0
    total_variance_value = 0.0
    movements_created = 0

    for item in count.items:
        if item.counted_quantity is not None:
            items_counted += 1
            if item.variance != 0:
                variance_items += 1
                total_variance_value += float(item.variance_value or 0)
                item.count_status = "APPROVED"

                # Create StockMovement for variance
                movement_type = "ADJUSTMENT_PLUS" if item.variance > 0 else "ADJUSTMENT_MINUS"
                # Generate movement number
                from datetime import date as date_type
                today = date_type.today()
                mv_prefix = f"CC-{today.strftime('%Y%m%d')}-"
                mv_count_result = await db.execute(
                    select(func.count(StockMovement.id)).where(
                        StockMovement.movement_number.like(f"{mv_prefix}%")
                    )
                )
                mv_seq = (mv_count_result.scalar() or 0) + 1

                movement = StockMovement(
                    movement_number=f"{mv_prefix}{str(mv_seq).zfill(4)}",
                    movement_type="CYCLE_COUNT",
                    warehouse_id=count.warehouse_id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    quantity=item.variance,
                    reference_type="physical_count",
                    reference_id=count.id,
                    reference_number=count.count_number,
                    unit_cost=float(item.unit_cost or 0),
                    total_cost=float(item.variance_value or 0),
                    created_by=current_user.id,
                    notes=f"Cycle count adjustment: system={item.system_quantity}, counted={item.counted_quantity}",
                )
                db.add(movement)
                movements_created += 1

                # Update InventorySummary
                inv_query = select(InventorySummary).where(
                    and_(
                        InventorySummary.warehouse_id == count.warehouse_id,
                        InventorySummary.product_id == item.product_id,
                    )
                )
                inv_result = await db.execute(inv_query)
                inv_summary = inv_result.scalars().first()
                if inv_summary:
                    inv_summary.total_quantity = (inv_summary.total_quantity or 0) + item.variance
                    inv_summary.available_quantity = (inv_summary.available_quantity or 0) + item.variance
                    inv_summary.last_audit_date = datetime.now(timezone.utc)

    # Update count
    count.status = "APPROVED"
    count.completed_at = datetime.now(timezone.utc)
    count.approved_by = current_user.id
    count.total_items_counted = items_counted
    count.total_variances = variance_items
    count.variance_value = round(total_variance_value, 2)

    await db.commit()

    return {
        "id": str(count.id),
        "count_number": count.count_number,
        "status": "APPROVED",
        "total_items_counted": items_counted,
        "total_variances": variance_items,
        "variance_value": round(total_variance_value, 2),
        "movements_created": movements_created,
        "message": f"Count approved. {movements_created} stock adjustments created."
    }
