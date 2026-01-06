from typing import Optional
import uuid
from math import ceil
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.api.deps import DB, CurrentUser, Permissions, require_permissions
from app.models.order import OrderStatus, PaymentStatus, PaymentMethod, OrderSource
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderStatusUpdate,
    OrderResponse,
    OrderDetailResponse,
    OrderListResponse,
    OrderItemResponse,
    PaymentCreate,
    PaymentResponse,
    StatusHistoryResponse,
    InvoiceResponse,
    OrderSummary,
)
from app.schemas.customer import CustomerBrief
from app.services.order_service import OrderService


router = APIRouter(prefix="/orders", tags=["Orders"])


def _build_order_response(order) -> OrderResponse:
    """Build OrderResponse from Order model."""
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer=CustomerBrief(
            id=order.customer.id,
            customer_code=order.customer.customer_code,
            full_name=order.customer.full_name,
            phone=order.customer.phone,
            email=order.customer.email,
        ),
        status=order.status,
        source=order.source,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        discount_amount=order.discount_amount,
        shipping_amount=order.shipping_amount,
        total_amount=order.total_amount,
        discount_code=order.discount_code,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        amount_paid=order.amount_paid,
        balance_due=order.balance_due,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        expected_delivery_date=order.expected_delivery_date,
        delivered_at=order.delivered_at,
        customer_notes=order.customer_notes,
        item_count=order.item_count,
        created_at=order.created_at,
        updated_at=order.updated_at,
        confirmed_at=order.confirmed_at,
    )


def _build_order_detail_response(order) -> OrderDetailResponse:
    """Build OrderDetailResponse from Order model."""
    return OrderDetailResponse(
        id=order.id,
        order_number=order.order_number,
        customer=CustomerBrief(
            id=order.customer.id,
            customer_code=order.customer.customer_code,
            full_name=order.customer.full_name,
            phone=order.customer.phone,
            email=order.customer.email,
        ),
        status=order.status,
        source=order.source,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        discount_amount=order.discount_amount,
        shipping_amount=order.shipping_amount,
        total_amount=order.total_amount,
        discount_code=order.discount_code,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        amount_paid=order.amount_paid,
        balance_due=order.balance_due,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        expected_delivery_date=order.expected_delivery_date,
        delivered_at=order.delivered_at,
        customer_notes=order.customer_notes,
        internal_notes=order.internal_notes,
        item_count=order.item_count,
        created_at=order.created_at,
        updated_at=order.updated_at,
        confirmed_at=order.confirmed_at,
        items=[OrderItemResponse.model_validate(item) for item in order.items],
        status_history=[StatusHistoryResponse.model_validate(h) for h in order.status_history],
        payments=[PaymentResponse.model_validate(p) for p in order.payments],
        invoice=InvoiceResponse.model_validate(order.invoice) if order.invoice else None,
    )


@router.get(
    "",
    response_model=OrderListResponse,
    dependencies=[Depends(require_permissions("orders:view"))]
)
async def list_orders(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    customer_id: Optional[uuid.UUID] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    source: Optional[OrderSource] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None, description="Search by order number"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
):
    """
    Get paginated list of orders.
    Requires: orders:view permission
    """
    service = OrderService(db)
    skip = (page - 1) * size

    orders, total = await service.get_orders(
        customer_id=customer_id,
        status=status,
        payment_status=payment_status,
        source=source,
        region_id=region_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return OrderListResponse(
        items=[_build_order_response(o) for o in orders],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get(
    "/stats",
    response_model=OrderSummary,
    dependencies=[Depends(require_permissions("orders:view"))]
)
async def get_order_stats(
    db: DB,
    region_id: Optional[uuid.UUID] = Query(None),
):
    """Get order statistics."""
    service = OrderService(db)
    stats = await service.get_order_stats(region_id=region_id)
    return OrderSummary(**stats)


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
    dependencies=[Depends(require_permissions("orders:view"))]
)
async def get_order(
    order_id: uuid.UUID,
    db: DB,
):
    """Get order details by ID."""
    service = OrderService(db)
    order = await service.get_order_by_id(order_id, include_all=True)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return _build_order_detail_response(order)


@router.get(
    "/number/{order_number}",
    response_model=OrderDetailResponse,
    dependencies=[Depends(require_permissions("orders:view"))]
)
async def get_order_by_number(
    order_number: str,
    db: DB,
):
    """Get order details by order number."""
    service = OrderService(db)
    order = await service.get_order_by_number(order_number)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return _build_order_detail_response(order)


@router.post(
    "",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("orders:create"))]
)
async def create_order(
    data: OrderCreate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Create a new order.
    Requires: orders:create permission
    """
    service = OrderService(db)

    try:
        order = await service.create_order(data, created_by=current_user.id)
        return _build_order_detail_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{order_id}/status",
    response_model=OrderDetailResponse,
    dependencies=[Depends(require_permissions("orders:update"))]
)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Update order status.
    Requires: orders:update permission
    """
    service = OrderService(db)

    order = await service.update_order_status(
        order_id,
        data.status,
        changed_by=current_user.id,
        notes=data.notes,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return _build_order_detail_response(order)


@router.post(
    "/{order_id}/approve",
    response_model=OrderDetailResponse,
    dependencies=[Depends(require_permissions("orders:approve"))]
)
async def approve_order(
    order_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Approve/confirm an order.
    Requires: orders:approve permission
    """
    service = OrderService(db)

    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status != OrderStatus.NEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only new orders can be approved"
        )

    order = await service.update_order_status(
        order_id,
        OrderStatus.CONFIRMED,
        changed_by=current_user.id,
        notes="Order approved",
    )

    return _build_order_detail_response(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderDetailResponse,
    dependencies=[Depends(require_permissions("orders:cancel"))]
)
async def cancel_order(
    order_id: uuid.UUID,
    notes: Optional[str] = None,
    db: DB = None,
    current_user: CurrentUser = None,
):
    """
    Cancel an order.
    Requires: orders:cancel permission
    """
    service = OrderService(db)

    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel this order"
        )

    order = await service.update_order_status(
        order_id,
        OrderStatus.CANCELLED,
        changed_by=current_user.id,
        notes=notes or "Order cancelled",
    )

    return _build_order_detail_response(order)


@router.post(
    "/{order_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("orders:update"))]
)
async def add_payment(
    order_id: uuid.UUID,
    data: PaymentCreate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Add a payment to an order.
    Requires: orders:update permission
    """
    service = OrderService(db)

    try:
        payment = await service.add_payment(
            order_id,
            amount=data.amount,
            method=data.method,
            transaction_id=data.transaction_id,
            gateway=data.gateway,
            reference_number=data.reference_number,
            notes=data.notes,
        )
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{order_id}/invoice",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("orders:update"))]
)
async def generate_invoice(
    order_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Generate invoice for an order.
    Requires: orders:update permission
    """
    service = OrderService(db)

    try:
        invoice = await service.generate_invoice(order_id)
        return InvoiceResponse.model_validate(invoice)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
