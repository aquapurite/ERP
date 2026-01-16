"""Inventory API endpoints for stock management."""
from typing import Optional, List
import uuid
from math import ceil
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query, Depends, Body

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
    StockVerificationRequest,
    StockVerificationResponse,
    BulkStockVerificationRequest,
    BulkStockVerificationResponse,
)
from app.services.inventory_service import InventoryService


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


# ==================== STOCK ITEMS ====================

@router.get(
    "/stock-items",
    response_model=StockItemListResponse,
    dependencies=[Depends(require_permissions("inventory:view"))]
)
async def list_stock_items(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    product_id: Optional[uuid.UUID] = Query(None),
    status: Optional[StockItemStatus] = Query(None),
    serial_number: Optional[str] = Query(None),
    batch_number: Optional[str] = Query(None),
):
    """
    Get paginated list of stock items.
    Requires: inventory:view permission
    """
    service = InventoryService(db)
    skip = (page - 1) * size

    items, total = await service.get_stock_items(
        warehouse_id=warehouse_id,
        product_id=product_id,
        status=status,
        serial_number=serial_number,
        batch_number=batch_number,
        skip=skip,
        limit=size,
    )

    return StockItemListResponse(
        items=[StockItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


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
    item.notes = f"Deleted by user on {datetime.utcnow().isoformat()}"

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
    Get inventory statistics.
    Requires: inventory:view permission
    """
    service = InventoryService(db)
    stats = await service.get_inventory_stats(warehouse_id=warehouse_id)
    return InventoryStats(**stats)
