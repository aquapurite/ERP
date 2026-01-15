"""
Payment API endpoints for Razorpay integration.

Handles:
- Payment order creation
- Payment verification
- Payment status checks
- Refund processing
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends

from app.api.deps import DB, CurrentUser, require_permissions
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    VerifyPaymentRequest,
    InitiateRefundRequest,
)
from app.services.payment_service import (
    PaymentService,
    PaymentOrderRequest,
    PaymentOrderResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    RefundRequest,
    RefundResponse,
)


router = APIRouter(tags=["Payments"])


# ==================== PUBLIC ENDPOINTS ====================

@router.post(
    "/create-order",
    response_model=PaymentOrderResponse,
    summary="Create a Razorpay payment order",
    description="Create a new payment order with Razorpay for checkout."
)
async def create_payment_order(
    data: CreatePaymentOrderRequest,
    db: DB,
):
    """
    Create a Razorpay order for payment.

    This endpoint is called during checkout to initialize payment.
    The returned order details are used by the frontend to launch
    Razorpay's payment modal.
    """
    from sqlalchemy import text

    # Verify order exists and belongs to user
    result = await db.execute(
        text("""
            SELECT id, order_number, total_amount, payment_status
            FROM orders
            WHERE id = :order_id
        """),
        {"order_id": data.order_id}
    )
    order = result.fetchone()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid"
        )

    # Create Razorpay order
    payment_service = PaymentService()

    try:
        payment_order = payment_service.create_order(
            PaymentOrderRequest(
                order_id=data.order_id,
                amount=data.amount,
                customer_email=data.customer_email,
                customer_phone=data.customer_phone,
                customer_name=data.customer_name,
                notes={
                    "order_number": order.order_number,
                    **(data.notes or {})
                }
            )
        )

        # Update order with Razorpay order ID
        await db.execute(
            text("""
                UPDATE orders
                SET
                    razorpay_order_id = :razorpay_order_id,
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "razorpay_order_id": payment_order.razorpay_order_id,
                "updated_at": datetime.now(),
                "order_id": data.order_id
            }
        )
        await db.commit()

        return payment_order

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment order: {str(e)}"
        )


@router.post(
    "/verify",
    response_model=PaymentVerificationResponse,
    summary="Verify payment after completion",
    description="Verify Razorpay payment signature and update order status."
)
async def verify_payment(
    data: VerifyPaymentRequest,
    db: DB,
):
    """
    Verify payment signature from Razorpay.

    Called by frontend after successful payment to verify authenticity.
    Updates order status to 'paid' if verification succeeds.
    """
    from sqlalchemy import text

    payment_service = PaymentService()

    # Verify payment signature
    verification = payment_service.verify_payment(
        PaymentVerificationRequest(
            razorpay_order_id=data.razorpay_order_id,
            razorpay_payment_id=data.razorpay_payment_id,
            razorpay_signature=data.razorpay_signature,
            order_id=data.order_id
        )
    )

    if verification.verified:
        # Update order with payment details
        await db.execute(
            text("""
                UPDATE orders
                SET
                    payment_status = 'paid',
                    razorpay_payment_id = :payment_id,
                    order_status = 'confirmed',
                    paid_at = :paid_at,
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "payment_id": data.razorpay_payment_id,
                "paid_at": datetime.now(),
                "updated_at": datetime.now(),
                "order_id": data.order_id
            }
        )
        await db.commit()

    return verification


@router.get(
    "/status/{payment_id}",
    summary="Get payment status",
    description="Fetch current status of a payment from Razorpay."
)
async def get_payment_status(
    payment_id: str,
):
    """Get current status of a payment from Razorpay."""
    payment_service = PaymentService()

    try:
        status = payment_service.get_payment_status(payment_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment status: {str(e)}"
        )


# ==================== ADMIN ENDPOINTS ====================

@router.post(
    "/refund",
    response_model=RefundResponse,
    dependencies=[Depends(require_permissions("payments:refund"))],
    summary="Initiate a refund",
    description="Initiate a full or partial refund for a payment."
)
async def initiate_refund(
    data: InitiateRefundRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Initiate a refund for a payment.

    Requires: payments:refund permission

    - Full refund if amount is not specified
    - Partial refund if amount is provided
    """
    from sqlalchemy import text

    payment_service = PaymentService()

    try:
        # Initiate refund with Razorpay
        refund = payment_service.initiate_refund(
            RefundRequest(
                payment_id=data.payment_id,
                amount=data.amount,
                notes={
                    "order_id": str(data.order_id),
                    "reason": data.reason or "Customer request",
                    "initiated_by": str(current_user.id)
                }
            )
        )

        # Update order with refund details
        await db.execute(
            text("""
                UPDATE orders
                SET
                    refund_status = 'processing',
                    refund_id = :refund_id,
                    refund_amount = :refund_amount,
                    refund_initiated_at = :initiated_at,
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "refund_id": refund.refund_id,
                "refund_amount": refund.amount / 100,  # Convert paise to INR
                "initiated_at": datetime.now(),
                "updated_at": datetime.now(),
                "order_id": data.order_id
            }
        )
        await db.commit()

        return refund

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate refund: {str(e)}"
        )


@router.get(
    "/order/{order_id}/payments",
    dependencies=[Depends(require_permissions("payments:view"))],
    summary="Get all payments for an order",
    description="Fetch all payment attempts for a specific order."
)
async def get_order_payments(
    order_id: uuid.UUID,
    db: DB,
):
    """
    Get all payment attempts for an order.

    Requires: payments:view permission
    """
    from sqlalchemy import text

    # Get Razorpay order ID
    result = await db.execute(
        text("SELECT razorpay_order_id FROM orders WHERE id = :order_id"),
        {"order_id": order_id}
    )
    order = result.fetchone()

    if not order or not order.razorpay_order_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment order found for this order"
        )

    payment_service = PaymentService()

    try:
        payments = payment_service.get_order_payments(order.razorpay_order_id)
        return {"order_id": order_id, "payments": payments}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payments: {str(e)}"
        )
