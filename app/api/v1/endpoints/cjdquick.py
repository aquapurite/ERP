"""
CJDQuick OMS Integration API endpoints.

Two parts:
  (a) Admin endpoints to trigger/view syncs (auth required)
  (b) Webhook receiver for OMS events (HMAC signature verification)
"""

import json
import uuid
import hmac
import hashlib
import logging
from typing import Optional, List
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request, Header
from sqlalchemy import select, desc, and_

from app.api.deps import DB, CurrentUser, require_permissions
from app.config import settings
from app.models.cjdquick_sync_log import CJDQuickSyncLog
from app.models.order import Order, OrderItem
from app.models.shipment import Shipment, ShipmentTracking
from app.models.return_order import ReturnOrder
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.picklist import PicklistItem
from app.models.billing import TaxInvoice, InvoiceStatus, InvoiceType
from app.services.cjdquick_service import CJDQuickAPIError
from app.services.cjdquick_sync_service import CJDQuickSyncService
from app.services.invoice_service import InvoiceService, InvoiceGenerationError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["CJDQuick OMS Integration"])


# ==================== SCHEMAS ====================

class SyncResponse(BaseModel):
    """Response from a sync operation."""
    success: bool
    entity_type: str
    entity_id: str
    oms_id: Optional[str] = None
    status: str
    message: str = ""


class SyncLogResponse(BaseModel):
    """Sync log entry for API response."""
    id: str
    entity_type: str
    entity_id: str
    oms_id: Optional[str] = None
    operation: str
    status: str
    error_message: Optional[str] = None
    retry_count: int = 0
    synced_at: Optional[datetime] = None
    created_at: datetime


class SyncLogListResponse(BaseModel):
    """Paginated sync log list."""
    items: List[SyncLogResponse]
    total: int


class WebhookRegisterRequest(BaseModel):
    """Request to register a webhook with CJDQuick OMS."""
    url: str = Field(..., description="Webhook URL to register")
    events: List[str] = Field(
        default=[
            "order.status_changed",
            "order.shipped",
            "shipment.tracking_updated",
            "shipment.delivered",
            "return.received",
            "return.processed",
            "invoice.created",
            "ndr.raised",
        ],
        description="Events to subscribe to",
    )


class BulkSyncResponse(BaseModel):
    """Response from a bulk sync operation."""
    total: int
    success: int
    failed: int


class RetryResponse(BaseModel):
    """Response from a single retry operation."""
    success: bool
    log_id: str
    new_status: str
    message: str


class RetryAllResponse(BaseModel):
    """Response from retry-all operation."""
    retried: int
    success: int
    failed: int


class SyncStatsResponse(BaseModel):
    """Sync health dashboard stats."""
    total_syncs: int
    success_count: int
    failed_count: int
    pending_count: int
    by_entity: dict  # {"PRODUCT": {"SUCCESS": 10, "FAILED": 2}, ...}
    last_sync_at: Optional[datetime] = None


# ==================== ADMIN SYNC ENDPOINTS ====================

@router.post(
    "/sync/product/{product_id}",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("products:update"))],
)
async def sync_product_to_oms(
    product_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Manually sync a product to CJDQuick OMS as a SKU."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled. Set CJDQUICK_ENABLED=true in .env",
        )

    sync_service = CJDQuickSyncService(db)
    try:
        log = await sync_service.sync_product(product_id)
        return SyncResponse(
            success=True,
            entity_type="PRODUCT",
            entity_id=str(product_id),
            oms_id=log.oms_id,
            status="SUCCESS",
            message="Product synced to CJDQuick OMS",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CJDQuickAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"CJDQuick OMS error: {e.message}",
        )


@router.post(
    "/sync/order/{order_id}",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def sync_order_to_oms(
    order_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Manually sync an order to CJDQuick OMS."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled. Set CJDQUICK_ENABLED=true in .env",
        )

    sync_service = CJDQuickSyncService(db)
    try:
        log = await sync_service.sync_order(order_id)
        return SyncResponse(
            success=True,
            entity_type="ORDER",
            entity_id=str(order_id),
            oms_id=log.oms_id,
            status="SUCCESS",
            message="Order synced to CJDQuick OMS",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CJDQuickAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"CJDQuick OMS error: {e.message}",
        )


@router.post(
    "/sync/customer/{customer_id}",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("customers:update"))],
)
async def sync_customer_to_oms(
    customer_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Manually sync a customer to CJDQuick OMS."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled. Set CJDQUICK_ENABLED=true in .env",
        )

    sync_service = CJDQuickSyncService(db)
    try:
        log = await sync_service.sync_customer(customer_id)
        return SyncResponse(
            success=True,
            entity_type="CUSTOMER",
            entity_id=str(customer_id),
            oms_id=log.oms_id,
            status="SUCCESS",
            message="Customer synced to CJDQuick OMS",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CJDQuickAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"CJDQuick OMS error: {e.message}",
        )


@router.get(
    "/sync/logs",
    response_model=SyncLogListResponse,
    dependencies=[Depends(require_permissions("orders:view"))],
)
async def list_sync_logs(
    db: DB,
    current_user: CurrentUser,
    entity_type: Optional[str] = Query(None, description="Filter by entity type: PRODUCT, ORDER, CUSTOMER, PO, RETURN"),
    sync_status: Optional[str] = Query(None, alias="status", description="Filter by status: SUCCESS, FAILED, PENDING"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO 8601)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List CJDQuick sync logs with filters."""
    query = select(CJDQuickSyncLog)

    if entity_type:
        query = query.where(CJDQuickSyncLog.entity_type == entity_type.upper())
    if sync_status:
        query = query.where(CJDQuickSyncLog.status == sync_status.upper())
    if date_from:
        query = query.where(CJDQuickSyncLog.created_at >= date_from)
    if date_to:
        query = query.where(CJDQuickSyncLog.created_at <= date_to)

    # Count total
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(desc(CJDQuickSyncLog.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return SyncLogListResponse(
        items=[
            SyncLogResponse(
                id=str(log.id),
                entity_type=log.entity_type,
                entity_id=str(log.entity_id),
                oms_id=log.oms_id,
                operation=log.operation,
                status=log.status,
                error_message=log.error_message,
                retry_count=log.retry_count,
                synced_at=log.synced_at,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
    )


# ==================== RETRY & BULK SYNC ENDPOINTS ====================

@router.post(
    "/sync/retry/{log_id}",
    response_model=RetryResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def retry_sync_log(
    log_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Retry a single failed sync log entry."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    sync_service = CJDQuickSyncService(db)
    try:
        new_log = await sync_service.retry_failed_sync(log_id)
        await db.commit()
        return RetryResponse(
            success=True,
            log_id=str(log_id),
            new_status=new_log.status,
            message="Retry successful",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CJDQuickAPIError as e:
        return RetryResponse(
            success=False,
            log_id=str(log_id),
            new_status="FAILED",
            message=f"Retry failed: {e.message}",
        )


@router.post(
    "/sync/retry-all",
    response_model=RetryAllResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def retry_all_failed_syncs(
    db: DB,
    current_user: CurrentUser,
    max_retries: int = Query(3, ge=1, le=10, description="Max retry attempts per log"),
):
    """Retry all failed sync logs (up to 100, limited by max_retries)."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    sync_service = CJDQuickSyncService(db)
    result = await sync_service.retry_all_failed(max_retries=max_retries)
    return RetryAllResponse(**result)


@router.post(
    "/sync/bulk/products",
    response_model=BulkSyncResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def bulk_sync_products(
    db: DB,
    current_user: CurrentUser,
):
    """Bulk sync all active products to CJDQuick OMS."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    sync_service = CJDQuickSyncService(db)
    result = await sync_service.bulk_sync_products()
    return BulkSyncResponse(**result)


@router.post(
    "/sync/bulk/purchase-orders",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("purchase_orders:update"))],
)
async def bulk_sync_purchase_orders(
    db: DB,
    current_user: CurrentUser,
):
    """Bulk push all POs to CJDQuick OMS via /external-pos.

    Finds all post-approval POs and pushes them with line items (SKUs, quantities, prices).
    CJDQuick will show them as 'Open POs' for GRN processing.
    """
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    from sqlalchemy.orm import selectinload

    SYNCABLE_STATUSES = ["APPROVED", "SENT_TO_VENDOR", "PARTIALLY_RECEIVED", "FULLY_RECEIVED", "CLOSED"]
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
            selectinload(PurchaseOrder.vendor),
        )
        .where(PurchaseOrder.status.in_(SYNCABLE_STATUSES))
        .order_by(PurchaseOrder.created_at)
    )
    pos = result.scalars().all()

    if not pos:
        return {"success": True, "message": "No POs to sync.", "total": 0, "synced": 0, "failed": 0}

    svc = CJDQuickSyncService(db)
    synced = 0
    failed = 0
    details = []

    for po in pos:
        try:
            log = await svc.sync_purchase_order(po.id)
            synced += 1
            details.append({
                "po_number": po.po_number,
                "vendor": po.vendor.name if po.vendor else "N/A",
                "items_count": len(po.items) if po.items else 0,
                "oms_id": log.oms_id,
                "sync_status": "SUCCESS",
            })
        except Exception as e:
            failed += 1
            details.append({
                "po_number": po.po_number,
                "sync_status": "FAILED",
                "error": str(e),
            })

    await db.commit()

    return {
        "success": True,
        "message": f"PO sync completed: {synced} synced, {failed} failed out of {len(pos)} POs",
        "total": len(pos),
        "synced": synced,
        "failed": failed,
        "details": details,
    }


@router.post(
    "/sync/bulk/orders",
    response_model=BulkSyncResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def bulk_sync_orders(
    db: DB,
    current_user: CurrentUser,
    order_status: str = Query("CONFIRMED", alias="status", description="Order status to sync"),
):
    """Bulk sync orders with given status to CJDQuick OMS."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    sync_service = CJDQuickSyncService(db)
    result = await sync_service.bulk_sync_orders(status_filter=order_status)
    return BulkSyncResponse(**result)


@router.get(
    "/sync/stats",
    response_model=SyncStatsResponse,
    dependencies=[Depends(require_permissions("orders:view"))],
)
async def get_sync_stats(
    db: DB,
    current_user: CurrentUser,
):
    """Get CJDQuick sync health statistics for the dashboard."""
    sync_service = CJDQuickSyncService(db)
    stats = await sync_service.get_sync_stats()
    return SyncStatsResponse(**stats)


# ==================== RECONCILIATION ENDPOINTS ====================

class UninvoicedOrderResponse(BaseModel):
    """Order that was shipped but has no active TAX_INVOICE."""
    id: str
    order_number: str
    customer_name: str
    status: str
    total_amount: float
    shipped_at: Optional[datetime] = None
    created_at: datetime
    item_count: int = 0
    has_serials: bool = False


class ReconciliationListResponse(BaseModel):
    """List of uninvoiced orders."""
    orders: List[UninvoicedOrderResponse]
    total: int


class ReconciliationActionResponse(BaseModel):
    """Result of bulk invoice generation."""
    total: int
    success: int
    failed: int
    errors: List[str] = []


@router.get(
    "/reconciliation/uninvoiced-orders",
    response_model=ReconciliationListResponse,
    dependencies=[Depends(require_permissions("orders:view"))],
)
async def get_uninvoiced_orders(
    db: DB,
    current_user: CurrentUser,
    days_back: int = Query(30, ge=1, le=365, description="Look back N days"),
):
    """
    Find orders that were shipped/manifested/delivered but have NO active TAX_INVOICE.

    This is the safety net — catches any orders where the CJDQuick webhook
    failed to trigger auto-invoice or the manifest confirm flow was missed.
    """
    from sqlalchemy import func

    cutoff = datetime.now(timezone.utc) - __import__('datetime').timedelta(days=days_back)

    # Subquery: orders that DO have an active TAX_INVOICE
    invoiced_subq = (
        select(TaxInvoice.order_id)
        .where(
            and_(
                TaxInvoice.invoice_type == InvoiceType.TAX_INVOICE.value,
                TaxInvoice.status != InvoiceStatus.CANCELLED.value,
                TaxInvoice.status != InvoiceStatus.VOID.value,
            )
        )
        .correlate(None)
    )

    # Orders shipped but not invoiced
    query = (
        select(Order)
        .where(
            and_(
                Order.status.in_(["MANIFESTED", "SHIPPED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"]),
                Order.created_at >= cutoff,
                ~Order.id.in_(invoiced_subq),
            )
        )
        .order_by(desc(Order.created_at))
        .limit(200)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    # Check if each order has serial numbers in picklist
    response_orders = []
    for o in orders:
        serial_result = await db.execute(
            select(func.count()).select_from(PicklistItem).where(
                and_(
                    PicklistItem.order_id == o.id,
                    PicklistItem.picked_serials.isnot(None),
                )
            )
        )
        has_serials = (serial_result.scalar() or 0) > 0

        response_orders.append(UninvoicedOrderResponse(
            id=str(o.id),
            order_number=o.order_number,
            customer_name=o.customer_name or "",
            status=o.status,
            total_amount=float(o.total_amount or 0),
            shipped_at=getattr(o, 'shipped_at', None),
            created_at=o.created_at,
            item_count=o.item_count if hasattr(o, 'item_count') else 0,
            has_serials=has_serials,
        ))

    return ReconciliationListResponse(orders=response_orders, total=len(response_orders))


@router.post(
    "/reconciliation/generate-missing-invoices",
    response_model=ReconciliationActionResponse,
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def generate_missing_invoices(
    db: DB,
    current_user: CurrentUser,
    order_ids: List[str] = Query(..., description="Order IDs to generate invoices for"),
):
    """
    Bulk-generate TAX_INVOICEs for shipped orders that were missed.

    This is the manual reconciliation action — select uninvoiced orders
    from the list above and generate invoices for them.
    """
    success = 0
    failed = 0
    errors = []

    invoice_service = InvoiceService(db)

    for order_id_str in order_ids:
        try:
            order_id = uuid.UUID(order_id_str)
            invoice = await invoice_service.generate_invoice_from_order(
                order_id=order_id,
                invoice_type=InvoiceType.TAX_INVOICE,
                generated_by=current_user.id,
                generation_trigger="RECONCILIATION",
                internal_notes="Generated via reconciliation — missed auto-invoice",
            )
            success += 1
            logger.info(
                "Reconciliation: Generated %s for order %s",
                invoice.invoice_number, order_id_str
            )
        except InvoiceGenerationError as e:
            failed += 1
            errors.append(f"Order {order_id_str}: {str(e)}")
            logger.warning("Reconciliation failed for order %s: %s", order_id_str, str(e))
        except Exception as e:
            failed += 1
            errors.append(f"Order {order_id_str}: Unexpected error — {str(e)}")
            logger.error("Reconciliation unexpected error for order %s: %s", order_id_str, str(e))

    if success > 0:
        await db.commit()

    return ReconciliationActionResponse(
        total=len(order_ids),
        success=success,
        failed=failed,
        errors=errors,
    )


# ==================== WEBHOOK REGISTRATION ====================

@router.post(
    "/webhook/register",
    dependencies=[Depends(require_permissions("orders:update"))],
)
async def register_webhook(
    req: WebhookRegisterRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Register a webhook URL with CJDQuick OMS."""
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    from app.services.cjdquick_service import CJDQuickService
    client = CJDQuickService()
    try:
        result = await client.register_webhook({
            "url": req.url,
            "events": req.events,
            "secret": settings.CJDQUICK_WEBHOOK_SECRET or "",
        })
        return {"success": True, "webhook": result}
    except CJDQuickAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"CJDQuick OMS error: {e.message}",
        )


# ==================== GOODS RECEIPT SYNC ====================

@router.post(
    "/sync/goods-receipt/bulk",
    dependencies=[Depends(require_permissions("purchase_orders:update"))],
)
async def bulk_sync_goods_receipts(
    db: DB,
    current_user: CurrentUser,
):
    """Sync all existing POs to CJDQuick as Goods Receipts.

    Finds all POs that are post-approval and haven't been synced yet
    (cjdquick_gr_id is NULL), then pushes them to CJDQuick Delhi warehouse.
    """
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    SYNCABLE_STATUSES = ["APPROVED", "SENT_TO_VENDOR", "PARTIALLY_RECEIVED", "FULLY_RECEIVED", "CLOSED"]

    # Find all unsynced POs
    result = await db.execute(
        select(PurchaseOrder)
        .where(
            PurchaseOrder.status.in_(SYNCABLE_STATUSES),
            PurchaseOrder.cjdquick_gr_id.is_(None),
        )
        .order_by(PurchaseOrder.created_at)
    )
    pos = result.scalars().all()

    if not pos:
        return {
            "success": True,
            "message": "No unsynced POs found. All POs are already synced.",
            "total": 0,
            "synced": 0,
            "failed": 0,
        }

    svc = CJDQuickSyncService(db)
    synced = 0
    failed = 0
    results = []

    for po in pos:
        try:
            log = await svc.sync_goods_receipt_for_po(po.id)
            synced += 1
            results.append({
                "po_number": po.po_number,
                "po_status": po.status,
                "gr_id": po.cjdquick_gr_id,
                "sync_status": "SUCCESS",
            })
        except Exception as e:
            failed += 1
            results.append({
                "po_number": po.po_number,
                "po_status": po.status,
                "sync_status": "FAILED",
                "error": str(e),
            })

    await db.commit()

    return {
        "success": True,
        "message": f"Bulk GR sync completed: {synced} synced, {failed} failed out of {len(pos)} POs",
        "total": len(pos),
        "synced": synced,
        "failed": failed,
        "details": results,
    }


@router.post(
    "/sync/goods-receipt/{po_id}",
    dependencies=[Depends(require_permissions("purchase_orders:update"))],
)
async def sync_goods_receipt_for_po(
    po_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Manually trigger CJDQuick Goods Receipt sync for a PO.

    Creates a GR in CJDQuick Delhi warehouse so they can prepare for incoming goods.
    """
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    # Verify PO exists and is post-approval
    SYNCABLE_STATUSES = {"APPROVED", "SENT_TO_VENDOR", "PARTIALLY_RECEIVED", "FULLY_RECEIVED", "CLOSED"}
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    if po.status not in SYNCABLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"PO must be in a post-approval status to sync GR. Current status: {po.status}")

    try:
        svc = CJDQuickSyncService(db)
        log = await svc.sync_goods_receipt_for_po(po_id)
        await db.commit()
        return {
            "success": True,
            "gr_id": po.cjdquick_gr_id,
            "gr_status": po.cjdquick_gr_status,
            "sync_log_id": str(log.id),
            "message": f"Goods Receipt created in CJDQuick for PO {po.po_number}",
        }
    except CJDQuickAPIError as e:
        await db.commit()  # Commit the FAILED status update
        raise HTTPException(
            status_code=e.status_code,
            detail=f"CJDQuick GR sync failed: {e.message}",
        )


# ==================== INVENTORY PULL SYNC (CJDQuick → ERP) ====================

@router.post(
    "/sync/inventory",
    dependencies=[Depends(require_permissions("inventory:update"))],
)
async def pull_inventory_from_cjdquick(
    db: DB,
    current_user: CurrentUser,
):
    """Pull current inventory levels from CJDQuick OMS into Aquapurite ERP.

    Calls CJDQuick GET /inventory, maps SKUs and locations, and upserts
    inventory_summary records with real quantities.
    """
    if not settings.CJDQUICK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CJDQuick OMS integration is disabled.",
        )

    try:
        svc = CJDQuickSyncService(db)
        stats = await svc.pull_inventory_from_cjdquick()
        return {
            "success": True,
            "message": f"Inventory sync complete: {stats['synced']} synced, {stats['skipped']} skipped, {stats['failed']} failed",
            **stats,
        }
    except Exception as e:
        logger.error("Inventory pull sync failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inventory sync failed: {str(e)}",
        )


# ==================== WEBHOOK RECEIVER ====================

def _verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature.

    Handles both formats:
      - New format: "sha256=<hex_digest>" (per updated integration guide)
      - Legacy format: raw hex digest
    """
    computed = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    # New format: "sha256=<hex_digest>"
    if signature.startswith("sha256="):
        expected = f"sha256={computed}"
        return hmac.compare_digest(expected, signature)

    # Legacy format: raw hex digest
    return hmac.compare_digest(computed, signature)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def cjdquick_webhook(
    request: Request,
    db: DB,
    x_webhook_signature: Optional[str] = Header(None),
    x_oms_event: Optional[str] = Header(None),
):
    """
    Receive webhook events from CJDQuick OMS.

    No auth required — verified via HMAC-SHA256 signature.

    Headers:
      - X-Webhook-Signature: sha256=<hmac_hex_digest>
      - X-OMS-Event: event type (e.g., order.shipped)
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    webhook_secret = settings.CJDQUICK_WEBHOOK_SECRET
    if webhook_secret:
        if not x_webhook_signature:
            logger.warning("CJDQuick webhook received without signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Webhook-Signature header",
            )
        if not _verify_webhook_signature(body, x_webhook_signature, webhook_secret):
            logger.warning("CJDQuick webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        logger.warning("CJDQUICK_WEBHOOK_SECRET not configured — skipping signature verification")

    # Parse event payload
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Event type: prefer X-OMS-Event header, then payload field
    event_type = x_oms_event or event.get("event") or event.get("type") or ""
    event_data = event.get("data") or event.get("payload") or {}

    logger.info("CJDQuick webhook received: %s", event_type)

    # Log the webhook event (dual logging: CJDQuickSyncLog + webhook_events)
    event_id = event.get("id") or request.headers.get("X-OMS-Event-Id")
    try:
        log = CJDQuickSyncLog(
            entity_type="WEBHOOK",
            entity_id=uuid.uuid4(),
            operation="WEBHOOK_RECEIVED",
            status="SUCCESS",
            request_payload=event,
            synced_at=datetime.now(timezone.utc),
        )
        db.add(log)

        # Also log to webhook_events table for structured debugging
        from sqlalchemy import text
        await db.execute(
            text("""
                INSERT INTO webhook_events (event_id, event_type, source, payload, status, received_at)
                VALUES (:event_id, :event_type, 'cjdquick', CAST(:payload AS jsonb), 'RECEIVED', NOW())
            """),
            {"event_id": event_id, "event_type": event_type, "payload": json.dumps(event)},
        )
    except Exception as e:
        logger.error("Failed to log webhook event: %s", e)

    # Process event by type
    try:
        # --- Order lifecycle ---
        if event_type in ("order.confirmed", "order.status_changed", "order.shipped"):
            await _handle_order_status_event(db, event_data, event_type)
        elif event_type == "order.cancelled":
            await _handle_order_cancelled_event(db, event_data)
        elif event_type == "order.created":
            logger.info("Order created in CJDQuick: %s", event_data.get("orderNo"))
        elif event_type == "order.invoiced":
            logger.info("Order invoiced in CJDQuick: %s %s", event_data.get("orderId"), event_data.get("invoiceNo"))

        # --- Shipment & Delivery lifecycle (CJDQuick v2 event names) ---
        elif event_type == "shipment.status_changed":
            await _handle_shipment_status_changed(db, event_data)
        elif event_type == "shipment.tracking_updated":
            await _handle_tracking_event(db, event_data)
        elif event_type == "shipment.delivered":
            await _handle_delivery_event(db, event_data)
        elif event_type == "delivery.shipped":
            await _handle_order_status_event(db, event_data, "order.shipped")
        elif event_type == "delivery.in_transit":
            await _handle_delivery_status_event(db, event_data, "IN_TRANSIT")
        elif event_type == "delivery.out_for_delivery":
            await _handle_delivery_status_event(db, event_data, "OUT_FOR_DELIVERY")
        elif event_type == "delivery.delivered":
            await _handle_delivery_event(db, event_data)
        elif event_type == "delivery.attempt_failed":
            await _handle_delivery_status_event(db, event_data, "NDR")
        elif event_type == "delivery.rto_initiated":
            await _handle_delivery_status_event(db, event_data, "RTO_INITIATED")
        elif event_type == "delivery.rto_delivered":
            await _handle_delivery_status_event(db, event_data, "RTO_DELIVERED")

        # --- Returns ---
        elif event_type in ("return.received", "return.processed", "return.qc_completed"):
            await _handle_return_event(db, event_type, event_data)

        # --- NDR ---
        elif event_type in ("ndr.raised", "ndr.resolved", "ndr.created"):
            await _handle_ndr_event(db, event_type, event_data)
        elif event_type == "order.rto":
            await _handle_delivery_status_event(db, event_data, "RTO_INITIATED")

        # --- Goods Receipt (both old gr.* and new goods_receipt.* event names) ---
        elif event_type in ("gr.posted", "gr.completed", "gr.status_changed",
                            "goods_receipt.posted", "goods_receipt.completed"):
            await _handle_gr_event(db, event_type, event_data)

        # --- Inventory ---
        elif event_type == "inventory.updated":
            await _handle_inventory_updated_event(db, event_data)
        elif event_type == "inventory.level_changed":
            await _handle_inventory_level_changed_event(db, event_data)

        # --- Invoices ---
        elif event_type in ("invoice.created", "invoice.paid"):
            logger.info("Invoice event received: %s %s", event_type, event_data.get("invoiceNo"))

        # --- Test ---
        elif event_type == "webhook.test":
            logger.info("Webhook test ping received successfully")
        else:
            logger.info("Unhandled CJDQuick event type: %s", event_type)
    except Exception as e:
        logger.error("Error processing CJDQuick webhook event %s: %s", event_type, e)

    return {"received": True, "event": event_type}


# ==================== WEBHOOK EVENT HANDLERS ====================

def _find_order_number(data: dict) -> Optional[str]:
    """Extract order number from webhook data.

    Integration guide uses 'externalOrderId'; legacy uses 'externalOrderNo'/'orderNo'.
    """
    return (
        data.get("externalOrderId")
        or data.get("externalOrderNo")
        or data.get("orderNo")
    )


async def _handle_order_status_event(db: DB, data: dict, event_type: str = "") -> None:
    """Handle order.confirmed, order.status_changed, and order.shipped events.

    On order.shipped:
    1. Capture serial numbers from CJDQuick payload → store in PicklistItem.picked_serials
    2. Auto-generate TAX_INVOICE via InvoiceService (zero sale loss guarantee)
    """
    order_number = _find_order_number(data)
    new_status = data.get("status") or data.get("newStatus")

    if not order_number or not new_status:
        logger.warning("Order status event missing required fields: %s", data)
        return

    result = await db.execute(
        select(Order).where(Order.order_number == order_number)
    )
    order = result.scalar_one_or_none()
    if not order:
        logger.warning("Order not found for webhook: %s", order_number)
        return

    erp_status = CJDQuickSyncService._map_oms_status_to_erp(new_status)
    order.status = erp_status

    # Capture RTO risk score from CJDQuick (v3 feature)
    rto_score = data.get("rtoRiskScore")
    rto_level = data.get("rtoRiskLevel")
    if rto_score is not None and hasattr(order, "rto_risk_score"):
        order.rto_risk_score = rto_score
    if rto_level and hasattr(order, "rto_risk_level"):
        order.rto_risk_level = rto_level

    # Store AWB/tracking info if shipped
    if event_type == "order.shipped":
        awb = data.get("awbNumber") or data.get("awbCode")
        if awb and hasattr(order, "awb_code"):
            order.awb_code = awb
        courier = data.get("courierName")
        if courier and hasattr(order, "courier_name"):
            order.courier_name = courier
        shipped_at = data.get("shippedAt")
        if shipped_at and hasattr(order, "shipped_at"):
            try:
                order.shipped_at = datetime.fromisoformat(shipped_at.replace("+05:30", "+0530"))
            except (ValueError, AttributeError):
                order.shipped_at = datetime.now(timezone.utc)

        # --- CJDQuick Serial Number Capture ---
        # CJDQuick sends serial numbers in the shipped webhook payload
        # Format: data.items[].serialNumbers[] or data.items[].serials[]
        # or data.serialNumbers[] (flat list for single-item orders)
        await _capture_serials_from_cjdquick(db, order, data)

        # Flush so picked_serials are visible to the invoice generation query
        # (autoflush=False means the SELECT in get_picked_serial_numbers would
        # otherwise read stale NULL values from the database)
        await db.flush()

        # --- Auto-generate TAX_INVOICE on shipment ---
        # This ensures zero sale loss: every shipped order gets an invoice
        await _auto_generate_invoice_on_shipped(db, order, data)

    logger.info("Order %s status updated to %s (OMS: %s)", order_number, erp_status, new_status)


async def _capture_serials_from_cjdquick(db, order: Order, data: dict) -> None:
    """Extract serial numbers from CJDQuick webhook and store in PicklistItem.

    CJDQuick may send serials in different formats:
    - data.items[].serialNumbers: ["SN001", "SN002"]
    - data.items[].serials: ["SN001", "SN002"]
    - data.serialNumbers: ["SN001"] (flat, for single-item orders)
    - data.items[].sku + serialNumbers: matched by SKU to order items
    """
    items_data = data.get("items") or data.get("lineItems") or []
    flat_serials = data.get("serialNumbers") or data.get("serials") or []

    if not items_data and not flat_serials:
        logger.info("No serial numbers in CJDQuick shipped event for order %s", order.order_number)
        return

    # Get order items for SKU matching
    order_items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    order_items = order_items_result.scalars().all()
    sku_to_order_item = {oi.product_sku: oi for oi in order_items if oi.product_sku}

    serials_captured = 0

    if items_data:
        # Match by SKU from CJDQuick items
        for item_data in items_data:
            sku = item_data.get("sku") or item_data.get("skuCode") or ""
            serials = item_data.get("serialNumbers") or item_data.get("serials") or []

            if not serials:
                continue

            serial_str = ",".join(str(s).strip() for s in serials if s)
            order_item = sku_to_order_item.get(sku)

            if order_item:
                # Update picklist item with CJDQuick serials
                picklist_result = await db.execute(
                    select(PicklistItem).where(
                        and_(
                            PicklistItem.order_item_id == order_item.id,
                            PicklistItem.order_id == order.id,
                        )
                    )
                )
                picklist_item = picklist_result.scalar_one_or_none()
                if picklist_item:
                    picklist_item.picked_serials = serial_str
                    picklist_item.is_picked = True
                    picklist_item.quantity_picked = picklist_item.quantity_required
                    picklist_item.picked_at = datetime.now(timezone.utc)
                    serials_captured += len(serials)
                    logger.info(
                        "Captured %d serials from CJDQuick for SKU %s, order %s",
                        len(serials), sku, order.order_number
                    )
                else:
                    logger.warning(
                        "No picklist item found for SKU %s, order %s — serials: %s",
                        sku, order.order_number, serial_str
                    )
            else:
                logger.warning(
                    "SKU %s from CJDQuick not matched to order %s items",
                    sku, order.order_number
                )

    elif flat_serials and len(order_items) == 1:
        # Single-item order with flat serial list
        serial_str = ",".join(str(s).strip() for s in flat_serials if s)
        order_item = order_items[0]
        picklist_result = await db.execute(
            select(PicklistItem).where(
                and_(
                    PicklistItem.order_item_id == order_item.id,
                    PicklistItem.order_id == order.id,
                )
            )
        )
        picklist_item = picklist_result.scalar_one_or_none()
        if picklist_item:
            picklist_item.picked_serials = serial_str
            picklist_item.is_picked = True
            picklist_item.quantity_picked = picklist_item.quantity_required
            picklist_item.picked_at = datetime.now(timezone.utc)
            serials_captured += len(flat_serials)
            logger.info(
                "Captured %d flat serials from CJDQuick for order %s",
                len(flat_serials), order.order_number
            )

    if serials_captured > 0:
        logger.info(
            "Total %d serial numbers captured from CJDQuick for order %s",
            serials_captured, order.order_number
        )
    else:
        logger.warning(
            "CJDQuick sent serial data but none could be matched for order %s",
            order.order_number
        )


async def _auto_generate_invoice_on_shipped(db, order: Order, data: dict) -> None:
    """Auto-generate TAX_INVOICE when CJDQuick confirms shipment.

    This is the zero-sale-loss guarantee: every order that CJDQuick ships
    automatically gets a TAX_INVOICE in the ERP.

    Skips if:
    - Order already has an active TAX_INVOICE
    - Order status is not eligible (cancelled, etc.)
    """
    # Check if active TAX_INVOICE already exists
    existing_result = await db.execute(
        select(TaxInvoice.id).where(
            and_(
                TaxInvoice.order_id == order.id,
                TaxInvoice.invoice_type == InvoiceType.TAX_INVOICE.value,
                TaxInvoice.status != InvoiceStatus.CANCELLED.value,
                TaxInvoice.status != InvoiceStatus.VOID.value,
            )
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        logger.info(
            "TAX_INVOICE already exists for order %s — skipping auto-generation on shipped",
            order.order_number
        )
        return

    # Skip if order is cancelled/returned
    if order.status in ("CANCELLED", "RTO_INITIATED", "RTO_DELIVERED", "RETURNED"):
        logger.info("Order %s status is %s — skipping invoice generation", order.order_number, order.status)
        return

    try:
        invoice_service = InvoiceService(db)
        invoice = await invoice_service.generate_invoice_from_order(
            order_id=order.id,
            invoice_type=InvoiceType.TAX_INVOICE,
            generated_by=order.created_by or uuid.uuid4(),  # System user fallback
            generation_trigger="CJDQUICK_SHIPPED",
            internal_notes=f"Auto-generated on CJDQuick shipment. AWB: {data.get('awbNumber', 'N/A')}",
        )
        logger.info(
            "AUTO-INVOICE SUCCESS: Generated %s for order %s via CJDQuick shipped webhook",
            invoice.invoice_number, order.order_number
        )
    except InvoiceGenerationError as e:
        logger.error(
            "AUTO-INVOICE FAILED for order %s on CJDQuick shipped: %s. "
            "ACTION REQUIRED: Manual invoice needed via reconciliation.",
            order.order_number, str(e)
        )
    except Exception as e:
        logger.error(
            "AUTO-INVOICE UNEXPECTED ERROR for order %s: %s. "
            "ACTION REQUIRED: Check logs and generate invoice manually.",
            order.order_number, str(e)
        )


async def _handle_tracking_event(db: DB, data: dict) -> None:
    """Handle shipment.tracking_updated events."""
    order_number = _find_order_number(data)
    awb_code = data.get("awbNumber") or data.get("awbCode") or data.get("trackingNo")
    tracking = data.get("tracking", {})
    tracking_status = tracking.get("status") or data.get("status", "")
    tracking_location = tracking.get("location") or data.get("location", "")

    logger.info(
        "Tracking update for order %s / AWB %s: %s at %s",
        order_number, awb_code, tracking_status, tracking_location,
    )

    # Update order's last tracking info if we can find it
    if order_number:
        result = await db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        order = result.scalar_one_or_none()
        if order:
            if hasattr(order, "tracking_status") and tracking_status:
                order.tracking_status = tracking_status
            if hasattr(order, "last_tracking_location") and tracking_location:
                order.last_tracking_location = tracking_location
            if hasattr(order, "last_tracking_update"):
                order.last_tracking_update = datetime.now(timezone.utc)


async def _handle_delivery_event(db: DB, data: dict) -> None:
    """Handle shipment.delivered events."""
    order_number = _find_order_number(data)
    if not order_number:
        return

    result = await db.execute(
        select(Order).where(Order.order_number == order_number)
    )
    order = result.scalar_one_or_none()
    if order:
        order.status = "DELIVERED"
        delivered_at = data.get("deliveredAt")
        if delivered_at:
            try:
                order.delivered_at = datetime.fromisoformat(delivered_at.replace("+05:30", "+0530"))
            except (ValueError, AttributeError):
                order.delivered_at = datetime.now(timezone.utc)
        else:
            order.delivered_at = datetime.now(timezone.utc)
        logger.info("Order %s marked as DELIVERED via webhook", order_number)


async def _handle_order_cancelled_event(db: DB, data: dict) -> None:
    """Handle order.cancelled events."""
    order_number = _find_order_number(data)
    if not order_number:
        return

    result = await db.execute(
        select(Order).where(Order.order_number == order_number)
    )
    order = result.scalar_one_or_none()
    if order:
        order.status = "CANCELLED"
        reason = data.get("reason", "")
        if hasattr(order, "cancellation_reason") and reason:
            order.cancellation_reason = reason
        order.cancelled_at = datetime.now(timezone.utc)
        logger.info("Order %s CANCELLED via webhook: %s", order_number, reason)


async def _handle_gr_event(db: DB, event_type: str, data: dict) -> None:
    """Handle gr.posted, gr.completed, gr.status_changed events from CJDQuick.

    Updates the PurchaseOrder's cjdquick_gr_status based on warehouse GR status.
    """
    po_number = (
        data.get("externalPoNumber")
        or data.get("poNumber")
        or data.get("poNo")
    )
    gr_no = data.get("grNo") or data.get("grNumber") or data.get("id")
    new_status = data.get("status") or event_type.split(".")[-1].upper()

    if not po_number:
        logger.warning("GR webhook missing PO number: %s", data)
        return

    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
    )
    po = result.scalar_one_or_none()
    if not po:
        logger.warning("PO not found for GR webhook: %s", po_number)
        return

    # Update GR tracking fields
    if gr_no and not po.cjdquick_gr_id:
        po.cjdquick_gr_id = str(gr_no)

    status_mapping = {
        "posted": "POSTED",
        "completed": "COMPLETED",
        "POSTED": "POSTED",
        "COMPLETED": "COMPLETED",
        "IN_PROGRESS": "IN_PROGRESS",
        "QC_PENDING": "QC_PENDING",
    }
    po.cjdquick_gr_status = status_mapping.get(new_status, new_status)

    logger.info(
        "PO %s GR status updated to %s (grNo: %s) via webhook",
        po_number, po.cjdquick_gr_status, gr_no,
    )

    # On GR completion, trigger inventory pull sync
    if po.cjdquick_gr_status in ("COMPLETED", "POSTED"):
        try:
            svc = CJDQuickSyncService(db)
            stats = await svc.pull_inventory_from_cjdquick()
            logger.info("Auto inventory pull triggered by GR event: %s", stats)
        except Exception as e:
            logger.error("Auto inventory pull failed after GR event: %s", e)


async def _handle_inventory_updated_event(db: DB, data: dict) -> None:
    """Handle inventory.updated event from CJDQuick.

    Per v3 guide: Fires when GRN is posted by warehouse team.
    Payload contains: skuId, locationId, companyId, grNo, quantityAdded.
    Used to auto-update PO received quantities in Aquapurite ERP.
    """
    gr_no = data.get("grNo") or data.get("grNumber")
    quantity_added = data.get("quantityAdded", 0)
    sku_id = data.get("skuId")

    logger.info(
        "Inventory updated event: grNo=%s, skuId=%s, quantityAdded=%s",
        gr_no, sku_id, quantity_added,
    )

    if not gr_no:
        logger.warning("inventory.updated webhook missing grNo: %s", data)
        return

    # Find PO by CJDQuick GR ID or GR number
    result = await db.execute(
        select(PurchaseOrder).where(
            (PurchaseOrder.cjdquick_gr_id == gr_no)
            | (PurchaseOrder.cjdquick_gr_id == str(data.get("id", "")))
        )
    )
    po = result.scalar_one_or_none()
    if po:
        po.cjdquick_gr_status = "POSTED"
        logger.info(
            "PO %s marked as POSTED via inventory.updated (grNo: %s, qty: %s)",
            po.po_number, gr_no, quantity_added,
        )
    else:
        logger.info("No PO found for inventory.updated grNo: %s (informational only)", gr_no)

    # Trigger inventory pull sync to update ERP stock levels
    try:
        svc = CJDQuickSyncService(db)
        stats = await svc.pull_inventory_from_cjdquick()
        logger.info("Auto inventory pull triggered by webhook: %s", stats)
    except Exception as e:
        logger.error("Auto inventory pull failed after webhook: %s", e)


async def _handle_inventory_level_changed_event(db: DB, data: dict) -> None:
    """Handle inventory.level_changed event from CJDQuick.

    This is the PRIMARY real-time inventory sync event.
    Fires whenever stock levels change (GRN, adjustment, transfer, allocation, return).

    Payload:
      skuCode, warehouseCode, quantity, reservedQty, availableQty, reason, timestamp
    """
    from app.models.inventory import InventorySummary, StockMovement
    from app.models.product import Product
    from app.models.warehouse import Warehouse

    sku_code = data.get("skuCode")
    warehouse_code = data.get("warehouseCode") or settings.CJDQUICK_WAREHOUSE_CODE
    on_hand = int(data.get("quantity", 0))
    reserved = int(data.get("reservedQty", 0))
    available = int(data.get("availableQty", on_hand - reserved))
    reason = data.get("reason", "unknown")

    logger.info(
        "inventory.level_changed: SKU=%s, warehouse=%s, qty=%s, available=%s, reason=%s",
        sku_code, warehouse_code, on_hand, available, reason,
    )

    if not sku_code:
        logger.warning("inventory.level_changed missing skuCode: %s", data)
        return

    # Resolve product
    result = await db.execute(
        select(Product.id).where(Product.sku == sku_code)
    )
    product_id = result.scalar_one_or_none()
    if not product_id:
        logger.warning("inventory.level_changed: SKU %s not found in ERP", sku_code)
        return

    # Resolve warehouse
    result = await db.execute(
        select(Warehouse.id).where(Warehouse.code == warehouse_code)
    )
    warehouse_id = result.scalar_one_or_none()
    if not warehouse_id:
        logger.warning("inventory.level_changed: warehouse %s not found in ERP", warehouse_code)
        return

    # Upsert inventory_summary
    result = await db.execute(
        select(InventorySummary).where(
            InventorySummary.product_id == product_id,
            InventorySummary.warehouse_id == warehouse_id,
            InventorySummary.variant_id.is_(None),
        )
    )
    summary = result.scalar_one_or_none()

    old_qty = 0
    if summary:
        old_qty = summary.total_quantity or 0
        summary.total_quantity = on_hand
        summary.available_quantity = available
        summary.reserved_quantity = reserved
        summary.last_stock_in_date = datetime.now(timezone.utc)
    else:
        summary = InventorySummary(
            warehouse_id=warehouse_id,
            product_id=product_id,
            variant_id=None,
            total_quantity=on_hand,
            available_quantity=available,
            reserved_quantity=reserved,
            allocated_quantity=0,
            damaged_quantity=0,
            in_transit_quantity=0,
            last_stock_in_date=datetime.now(timezone.utc),
        )
        db.add(summary)

    # Create stock movement if quantity changed
    qty_diff = on_hand - old_qty
    if qty_diff != 0:
        from sqlalchemy import func as sa_func

        now = datetime.now(timezone.utc)
        date_prefix = now.strftime("%Y%m%d")
        count_result = await db.execute(
            select(sa_func.count(StockMovement.id)).where(
                StockMovement.movement_number.like(f"MOV-{date_prefix}-%")
            )
        )
        count = count_result.scalar() or 0
        movement_number = f"MOV-{date_prefix}-{count + 1:04d}"

        movement = StockMovement(
            movement_number=movement_number,
            movement_type="RECEIPT" if qty_diff > 0 else "ISSUE",
            movement_date=now,
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=qty_diff,
            balance_before=old_qty,
            balance_after=on_hand,
            reference_type="cjdquick_webhook",
            reference_number=f"CJDQ-{reason}-{date_prefix}",
            unit_cost=0,
            total_cost=0,
            notes=f"Real-time sync from CJDQuick webhook. SKU: {sku_code}, Reason: {reason}",
        )
        db.add(movement)

    logger.info(
        "inventory.level_changed processed: SKU=%s, %d → %d (diff: %+d, reason: %s)",
        sku_code, old_qty, on_hand, qty_diff, reason,
    )


async def _handle_ndr_event(db: DB, event_type: str, data: dict) -> None:
    """Handle ndr.raised and ndr.resolved events."""
    order_number = _find_order_number(data)
    if not order_number:
        return

    result = await db.execute(
        select(Order).where(Order.order_number == order_number)
    )
    order = result.scalar_one_or_none()
    if not order:
        logger.warning("Order not found for NDR event: %s", order_number)
        return

    if event_type in ("ndr.raised", "ndr.created"):
        order.status = "NDR"
        logger.info("NDR raised for order %s: %s", order_number, data.get("reason", ""))
    elif event_type == "ndr.resolved":
        resolution = data.get("resolution", "")
        if resolution == "RTO":
            order.status = "RTO_INITIATED"
        else:
            order.status = "OUT_FOR_DELIVERY"
        logger.info("NDR resolved for order %s: %s", order_number, resolution)


async def _handle_shipment_status_changed(db: DB, data: dict) -> None:
    """Handle shipment.status_changed — the primary tracking event from CJDQuick.

    Payload: awbNo, orderId, deliveryId, carrierCode, fromStatus, toStatus,
             statusBucket, statusLabel, location, carrierRemark, timestamp
    """
    order_number = _find_order_number(data)
    awb_code = data.get("awbNo") or data.get("awbCode")
    to_status = data.get("toStatus", "")
    status_label = data.get("statusLabel", "")
    location = data.get("location", "")
    carrier_remark = data.get("carrierRemark", "")
    status_bucket = data.get("statusBucket", "")

    logger.info(
        "shipment.status_changed: order=%s, AWB=%s, %s → %s (%s) at %s",
        order_number, awb_code, data.get("fromStatus"), to_status, status_label, location,
    )

    # Find order by order number or AWB
    order = None
    if order_number:
        result = await db.execute(select(Order).where(Order.order_number == order_number))
        order = result.scalar_one_or_none()
    if not order and awb_code:
        result = await db.execute(select(Order).where(Order.awb_code == awb_code))
        order = result.scalar_one_or_none()

    if not order:
        logger.warning("Order not found for shipment.status_changed: order=%s, AWB=%s", order_number, awb_code)
        return

    # Update tracking fields
    if hasattr(order, "tracking_status") and status_label:
        order.tracking_status = status_label
    if hasattr(order, "last_tracking_location") and location:
        order.last_tracking_location = location
    if hasattr(order, "last_tracking_activity") and carrier_remark:
        order.last_tracking_activity = carrier_remark
    if hasattr(order, "last_tracking_update"):
        order.last_tracking_update = datetime.now(timezone.utc)

    # Map status_bucket to ERP order status
    bucket_to_erp = {
        "shipped": "SHIPPED",
        "in_transit": "IN_TRANSIT",
        "out_for_delivery": "OUT_FOR_DELIVERY",
        "delivered": "DELIVERED",
        "ndr": "NDR",
        "rto_initiated": "RTO_INITIATED",
        "rto_in_transit": "RTO_IN_TRANSIT",
        "rto_delivered": "RTO_DELIVERED",
    }
    erp_status = bucket_to_erp.get(status_bucket)
    if erp_status:
        order.status = erp_status
        if erp_status == "DELIVERED" and hasattr(order, "delivered_at"):
            order.delivered_at = datetime.now(timezone.utc)

    logger.info("Order %s tracking updated: %s (%s)", order.order_number, status_label, erp_status or to_status)


async def _handle_delivery_status_event(db: DB, data: dict, erp_status: str) -> None:
    """Handle delivery.* events (in_transit, out_for_delivery, attempt_failed, rto_initiated, rto_delivered).

    Simple status update handler for the delivery lifecycle events.
    """
    order_number = _find_order_number(data)
    awb_code = data.get("awbNo") or data.get("awbCode")

    order = None
    if order_number:
        result = await db.execute(select(Order).where(Order.order_number == order_number))
        order = result.scalar_one_or_none()
    if not order and awb_code:
        result = await db.execute(select(Order).where(Order.awb_code == awb_code))
        order = result.scalar_one_or_none()

    if not order:
        logger.warning("Order not found for delivery event (status=%s): order=%s, AWB=%s", erp_status, order_number, awb_code)
        return

    order.status = erp_status

    # Update tracking fields
    location = data.get("location", "")
    if hasattr(order, "last_tracking_location") and location:
        order.last_tracking_location = location
    if hasattr(order, "last_tracking_update"):
        order.last_tracking_update = datetime.now(timezone.utc)
    if hasattr(order, "tracking_status"):
        order.tracking_status = data.get("statusLabel", erp_status)

    # RTO_DELIVERED: flag for refund + inventory update
    if erp_status == "RTO_DELIVERED":
        if hasattr(order, "rto_delivered_at"):
            order.rto_delivered_at = datetime.now(timezone.utc)
        logger.info("Order %s RTO delivered — flag for refund & inventory restock", order.order_number)

    logger.info("Order %s status updated to %s via delivery event", order.order_number, erp_status)


async def _handle_return_event(db: DB, event_type: str, data: dict) -> None:
    """Handle return.received, return.qc_completed, and return.processed events."""
    rma_number = data.get("rmaNumber") or data.get("returnNo") or data.get("returnId")
    if not rma_number:
        return

    result = await db.execute(
        select(ReturnOrder).where(ReturnOrder.rma_number == rma_number)
    )
    return_order = result.scalar_one_or_none()
    if not return_order:
        logger.warning("Return order not found for webhook: %s", rma_number)
        return

    if event_type == "return.received":
        return_order.status = "RECEIVED"
        logger.info("Return %s marked as RECEIVED via webhook", rma_number)
    elif event_type == "return.qc_completed":
        qc_status = data.get("qcStatus", "")
        logger.info("Return %s QC completed: %s", rma_number, qc_status)
    elif event_type == "return.processed":
        return_order.status = "PROCESSED"
        logger.info("Return %s marked as PROCESSED via webhook", rma_number)
