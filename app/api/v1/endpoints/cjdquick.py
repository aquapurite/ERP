"""
CJDQuick OMS Integration API endpoints.

Two parts:
  (a) Admin endpoints to trigger/view syncs (auth required)
  (b) Webhook receiver for OMS events (HMAC signature verification)
"""

import uuid
import hmac
import hashlib
import logging
from typing import Optional, List
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request, Header
from sqlalchemy import select, desc

from app.api.deps import DB, CurrentUser, require_permissions
from app.config import settings
from app.models.cjdquick_sync_log import CJDQuickSyncLog
from app.models.order import Order
from app.models.shipment import Shipment, ShipmentTracking
from app.models.return_order import ReturnOrder
from app.services.cjdquick_service import CJDQuickAPIError
from app.services.cjdquick_sync_service import CJDQuickSyncService

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


# ==================== WEBHOOK RECEIVER ====================

def _verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def cjdquick_webhook(
    request: Request,
    db: DB,
    x_webhook_signature: Optional[str] = Header(None),
):
    """
    Receive webhook events from CJDQuick OMS.

    No auth required — verified via HMAC signature in X-Webhook-Signature header.
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

    event_type = event.get("event") or event.get("type") or ""
    event_data = event.get("data") or event.get("payload") or {}

    logger.info("CJDQuick webhook received: %s", event_type)

    # Log the webhook event
    try:
        log = CJDQuickSyncLog(
            entity_type="WEBHOOK",
            entity_id=uuid.uuid4(),  # No specific entity for inbound webhooks
            operation="WEBHOOK_RECEIVED",
            status="SUCCESS",
            request_payload=event,
            synced_at=datetime.now(timezone.utc),
        )
        db.add(log)
    except Exception as e:
        logger.error("Failed to log webhook event: %s", e)

    # Process event by type
    try:
        if event_type in ("order.status_changed", "order.shipped"):
            await _handle_order_status_event(db, event_data)
        elif event_type == "shipment.tracking_updated":
            await _handle_tracking_event(db, event_data)
        elif event_type == "shipment.delivered":
            await _handle_delivery_event(db, event_data)
        elif event_type in ("return.received", "return.processed"):
            await _handle_return_event(db, event_type, event_data)
        elif event_type == "invoice.created":
            logger.info("Invoice created event received: %s", event_data.get("invoiceNo"))
        elif event_type == "ndr.raised":
            logger.info("NDR raised for order: %s", event_data.get("orderNo"))
        else:
            logger.info("Unhandled CJDQuick event type: %s", event_type)
    except Exception as e:
        logger.error("Error processing CJDQuick webhook event %s: %s", event_type, e)

    return {"status": "ok", "event": event_type}


# ==================== WEBHOOK EVENT HANDLERS ====================

async def _handle_order_status_event(db: DB, data: dict) -> None:
    """Handle order.status_changed and order.shipped events."""
    external_order_no = data.get("externalOrderNo") or data.get("orderNo")
    new_status = data.get("status") or data.get("newStatus")

    if not external_order_no or not new_status:
        logger.warning("Order status event missing required fields: %s", data)
        return

    result = await db.execute(
        select(Order).where(Order.order_number == external_order_no)
    )
    order = result.scalar_one_or_none()
    if not order:
        logger.warning("Order not found for webhook: %s", external_order_no)
        return

    erp_status = CJDQuickSyncService._map_oms_status_to_erp(new_status)
    order.status = erp_status
    logger.info("Order %s status updated to %s (OMS: %s)", external_order_no, erp_status, new_status)


async def _handle_tracking_event(db: DB, data: dict) -> None:
    """Handle shipment.tracking_updated events."""
    awb_code = data.get("awbCode") or data.get("trackingNo")
    tracking_status = data.get("status")
    tracking_location = data.get("location", "")
    tracking_description = data.get("description", "")

    if not awb_code:
        logger.warning("Tracking event missing AWB code: %s", data)
        return

    logger.info(
        "Tracking update for AWB %s: %s at %s",
        awb_code, tracking_status, tracking_location,
    )


async def _handle_delivery_event(db: DB, data: dict) -> None:
    """Handle shipment.delivered events."""
    external_order_no = data.get("externalOrderNo") or data.get("orderNo")
    if not external_order_no:
        return

    result = await db.execute(
        select(Order).where(Order.order_number == external_order_no)
    )
    order = result.scalar_one_or_none()
    if order:
        order.status = "DELIVERED"
        order.delivered_at = datetime.now(timezone.utc)
        logger.info("Order %s marked as DELIVERED via webhook", external_order_no)


async def _handle_return_event(db: DB, event_type: str, data: dict) -> None:
    """Handle return.received and return.processed events."""
    rma_number = data.get("rmaNumber") or data.get("returnNo")
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
    elif event_type == "return.processed":
        return_order.status = "PROCESSED"
        logger.info("Return %s marked as PROCESSED via webhook", rma_number)
