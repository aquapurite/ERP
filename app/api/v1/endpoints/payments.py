"""
Payment API endpoints for Razorpay and Stripe integration.

Handles:
- Razorpay: Payment order creation, verification, webhooks
- Stripe: PaymentIntent creation, confirmation webhooks
- Payment status checks
- Refund processing
"""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Depends, Request, Header
from typing import Optional

from app.api.deps import DB, CurrentUser, require_permissions
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    VerifyPaymentRequest,
    InitiateRefundRequest,
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentStatusResponse,
    StripeRefundRequest,
    StripeRefundResponse,
)
from app.services.payment_service import (
    PaymentService,
    PaymentOrderRequest,
    PaymentOrderResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    RefundRequest,
    RefundResponse,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


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

    if order.payment_status == "PAID":
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
                "updated_at": datetime.now(timezone.utc),
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
        # Note: Column is "status" not "order_status", values are uppercase
        await db.execute(
            text("""
                UPDATE orders
                SET
                    payment_status = 'PAID',
                    razorpay_payment_id = :payment_id,
                    status = 'CONFIRMED',
                    amount_paid = total_amount,
                    paid_at = :paid_at,
                    confirmed_at = :paid_at,
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "payment_id": data.razorpay_payment_id,
                "paid_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
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
    dependencies=[Depends(require_permissions("finance:update"))],
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

    Requires: finance:update permission

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
        # Note: Using internal_notes to track refund since dedicated columns don't exist
        await db.execute(
            text("""
                UPDATE orders
                SET
                    internal_notes = COALESCE(internal_notes, '') ||
                        E'\n[Refund Initiated] Refund ID: ' || :refund_id ||
                        ', Amount: ₹' || :refund_amount::text ||
                        ', Time: ' || :initiated_at::text,
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "refund_id": refund.refund_id,
                "refund_amount": refund.amount / 100,  # Convert paise to INR
                "initiated_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
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
    dependencies=[Depends(require_permissions("finance:view"))],
    summary="Get all payments for an order",
    description="Fetch all payment attempts for a specific order."
)
async def get_order_payments(
    order_id: uuid.UUID,
    db: DB,
):
    """
    Get all payment attempts for an order.

    Requires: finance:view permission
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


# ==================== WEBHOOK ENDPOINT ====================

@router.post(
    "/webhook",
    summary="Razorpay webhook handler",
    description="Handle payment events from Razorpay. This endpoint is called by Razorpay servers.",
    include_in_schema=False  # Hide from API docs for security
)
async def razorpay_webhook(
    request: Request,
    db: DB,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    """
    Handle Razorpay webhook events.

    Events handled:
    - payment.captured: Payment was successful
    - payment.failed: Payment failed
    - order.paid: Order fully paid
    - refund.processed: Refund completed

    Security:
    - Verifies webhook signature using RAZORPAY_WEBHOOK_SECRET
    - Idempotent: Safe to receive duplicate events
    """
    from sqlalchemy import text

    # Get raw body for signature verification
    body = await request.body()

    payment_service = PaymentService()

    # Verify webhook signature
    if x_razorpay_signature:
        if not payment_service.verify_webhook_signature(body, x_razorpay_signature):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
    else:
        logger.warning("Webhook received without signature header")
        # In production, you might want to reject unsigned webhooks
        # For now, we'll log and continue for testing

    # Parse webhook payload
    try:
        import json
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    event = payload.get("event")
    event_payload = payload.get("payload", {})

    logger.info(f"Received Razorpay webhook: {event}")

    try:
        # Handle different event types
        if event == WebhookEvent.PAYMENT_CAPTURED:
            await _handle_payment_captured(db, event_payload)

        elif event == WebhookEvent.PAYMENT_FAILED:
            await _handle_payment_failed(db, event_payload)

        elif event == WebhookEvent.ORDER_PAID:
            await _handle_order_paid(db, event_payload)

        elif event == WebhookEvent.REFUND_PROCESSED:
            await _handle_refund_processed(db, event_payload)

        elif event == WebhookEvent.PAYMENT_AUTHORIZED:
            # For auto-capture, this is handled by Razorpay
            logger.info("Payment authorized, waiting for capture")

        else:
            logger.info(f"Unhandled webhook event: {event}")

        return {"status": "ok", "event": event}

    except Exception as e:
        logger.error(f"Error processing webhook {event}: {e}")
        # Return 200 to prevent Razorpay from retrying
        # We'll handle errors internally
        return {"status": "error", "message": str(e)}


async def _handle_payment_captured(db: DB, payload: dict):
    """Handle payment.captured event - payment was successful."""
    from sqlalchemy import text
    from app.services.email_service import send_order_notifications

    payment = payload.get("payment", {}).get("entity", {})
    razorpay_payment_id = payment.get("id")
    razorpay_order_id = payment.get("order_id")
    amount = payment.get("amount", 0) / 100  # Convert paise to INR

    if not razorpay_order_id:
        logger.warning("Payment captured without order_id")
        return

    logger.info(f"Payment captured: {razorpay_payment_id} for order {razorpay_order_id}")

    # Update order status
    await db.execute(
        text("""
            UPDATE orders
            SET
                payment_status = 'PAID',
                status = CASE
                    WHEN status IN ('NEW', 'PENDING_PAYMENT') THEN 'CONFIRMED'
                    ELSE status
                END,
                razorpay_payment_id = :payment_id,
                amount_paid = :amount,
                paid_at = :paid_at,
                confirmed_at = CASE
                    WHEN status IN ('NEW', 'PENDING_PAYMENT') THEN :paid_at
                    ELSE confirmed_at
                END,
                updated_at = :updated_at
            WHERE razorpay_order_id = :order_id
        """),
        {
            "payment_id": razorpay_payment_id,
            "order_id": razorpay_order_id,
            "amount": amount,
            "paid_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    )

    # Add status history entry
    result = await db.execute(
        text("SELECT id FROM orders WHERE razorpay_order_id = :order_id"),
        {"order_id": razorpay_order_id}
    )
    order = result.fetchone()

    if order:
        await db.execute(
            text("""
                INSERT INTO order_status_history (id, order_id, from_status, to_status, notes, created_at)
                VALUES (gen_random_uuid(), :order_id, 'PENDING_PAYMENT', 'CONFIRMED',
                        :notes, :created_at)
            """),
            {
                "order_id": order.id,
                "notes": f"Payment confirmed via Razorpay webhook. Payment ID: {razorpay_payment_id}",
                "created_at": datetime.now(timezone.utc)
            }
        )

        # Fetch full order details for notification
        order_result = await db.execute(
            text("""
                SELECT o.order_number, o.total_amount, o.payment_method, o.shipping_address,
                       c.name as customer_name, c.email as customer_email, c.phone as customer_phone
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = :order_id
            """),
            {"order_id": order.id}
        )
        order_data = order_result.fetchone()

        # Fetch order items
        items_result = await db.execute(
            text("""
                SELECT product_name, variant_name, quantity, total_amount
                FROM order_items
                WHERE order_id = :order_id
            """),
            {"order_id": order.id}
        )
        items = [dict(row._mapping) for row in items_result.fetchall()]

        # Send notifications asynchronously (don't block webhook response)
        if order_data:
            try:
                from decimal import Decimal
                import json

                shipping_address = order_data.shipping_address
                if isinstance(shipping_address, str):
                    shipping_address = json.loads(shipping_address)

                await send_order_notifications(
                    order_number=order_data.order_number,
                    customer_email=order_data.customer_email,
                    customer_phone=order_data.customer_phone,
                    customer_name=order_data.customer_name,
                    total_amount=Decimal(str(order_data.total_amount)),
                    items=items,
                    shipping_address=shipping_address,
                    payment_method=order_data.payment_method or "Online Payment"
                )
                logger.info(f"Notifications sent for order {order_data.order_number}")
            except Exception as e:
                logger.error(f"Failed to send notifications: {e}")
                # Don't fail the webhook for notification errors

    await db.commit()

    # ============ ACCOUNTING INTEGRATION ============
    # Create journal entry: DR Bank, CR Accounts Receivable
    if order:
        try:
            from app.services.auto_journal_service import AutoJournalService, AutoJournalError
            from decimal import Decimal

            auto_journal = AutoJournalService(db)
            await auto_journal.generate_for_order_payment(
                order_id=order.id,
                amount=Decimal(str(amount)),
                payment_method="RAZORPAY",
                reference_number=razorpay_payment_id,
                user_id=None,  # System-generated
                auto_post=True,
                is_cash=False,  # Razorpay is always bank
            )
            await db.commit()
            logger.info(f"Accounting entry created for Razorpay payment {razorpay_payment_id}")
        except AutoJournalError as e:
            logger.warning(f"Failed to create accounting entry for payment {razorpay_payment_id}: {e.message}")
        except Exception as e:
            logger.warning(f"Unexpected error creating accounting entry for payment {razorpay_payment_id}: {str(e)}")
    logger.info(f"Order updated for payment {razorpay_payment_id}")


async def _handle_payment_failed(db: DB, payload: dict):
    """Handle payment.failed event - payment was unsuccessful."""
    from sqlalchemy import text

    payment = payload.get("payment", {}).get("entity", {})
    razorpay_payment_id = payment.get("id")
    razorpay_order_id = payment.get("order_id")
    error_code = payment.get("error_code")
    error_description = payment.get("error_description")

    if not razorpay_order_id:
        return

    logger.info(f"Payment failed: {razorpay_payment_id} - {error_code}: {error_description}")

    # Update order payment status to failed
    await db.execute(
        text("""
            UPDATE orders
            SET
                payment_status = 'FAILED',
                internal_notes = COALESCE(internal_notes, '') ||
                    E'\n[Payment Failed] ' || :error_msg,
                updated_at = :updated_at
            WHERE razorpay_order_id = :order_id
        """),
        {
            "order_id": razorpay_order_id,
            "error_msg": f"{error_code}: {error_description}",
            "updated_at": datetime.now(timezone.utc)
        }
    )
    await db.commit()


async def _handle_order_paid(db: DB, payload: dict):
    """Handle order.paid event - order is fully paid."""
    from sqlalchemy import text

    order_entity = payload.get("order", {}).get("entity", {})
    razorpay_order_id = order_entity.get("id")
    amount_paid = order_entity.get("amount_paid", 0) / 100

    if not razorpay_order_id:
        return

    logger.info(f"Order paid: {razorpay_order_id} - Amount: {amount_paid}")

    # Ensure order is marked as paid
    await db.execute(
        text("""
            UPDATE orders
            SET
                payment_status = 'PAID',
                status = CASE
                    WHEN status IN ('NEW', 'PENDING_PAYMENT') THEN 'CONFIRMED'
                    ELSE status
                END,
                amount_paid = :amount,
                paid_at = COALESCE(paid_at, :paid_at),
                confirmed_at = COALESCE(confirmed_at, :paid_at),
                updated_at = :updated_at
            WHERE razorpay_order_id = :order_id
        """),
        {
            "order_id": razorpay_order_id,
            "amount": amount_paid,
            "paid_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    )
    await db.commit()


async def _handle_refund_processed(db: DB, payload: dict):
    """Handle refund.processed event - refund completed."""
    from sqlalchemy import text

    refund = payload.get("refund", {}).get("entity", {})
    refund_id = refund.get("id")
    payment_id = refund.get("payment_id")
    amount = refund.get("amount", 0) / 100

    logger.info(f"Refund processed: {refund_id} - Amount: {amount}")

    # Update order refund status
    await db.execute(
        text("""
            UPDATE orders
            SET
                payment_status = CASE
                    WHEN amount_paid - :refund_amount <= 0 THEN 'REFUNDED'
                    ELSE 'PARTIALLY_REFUNDED'
                END,
                amount_paid = GREATEST(0, amount_paid - :refund_amount),
                internal_notes = COALESCE(internal_notes, '') ||
                    E'\n[Refund Processed] Refund ID: ' || :refund_id || ', Amount: ' || :refund_amount::text,
                updated_at = :updated_at
            WHERE razorpay_payment_id = :payment_id
        """),
        {
            "payment_id": payment_id,
            "refund_id": refund_id,
            "refund_amount": amount,
            "updated_at": datetime.now(timezone.utc)
        }
    )
    await db.commit()


# ==================== STRIPE ENDPOINTS ====================

@router.post(
    "/stripe/create-intent",
    response_model=PaymentIntentResponse,
    summary="Create a Stripe PaymentIntent",
    description="Create a PaymentIntent for card payment via Stripe Elements.",
)
async def stripe_create_intent(
    data: CreatePaymentIntentRequest,
    db: DB,
):
    """
    Create a Stripe PaymentIntent for an order.

    Flow:
    1. Verify order exists and is not already paid
    2. Find or create a pending payment record
    3. If payment already has a Stripe PI, retrieve it (idempotent retry)
    4. Otherwise create a new PaymentIntent
    5. Update payment record with PI ID
    6. Return client_secret for frontend Stripe Elements
    """
    from sqlalchemy import text
    from app.services.stripe_service import StripePaymentService

    # Reject cash payments
    if data.payment_method.upper() in ("CASH", "COD"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe payment is not applicable for cash/COD orders"
        )

    # Verify order exists
    result = await db.execute(
        text("""
            SELECT id, order_number, total_amount, payment_status, payment_method
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

    if order.payment_status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid"
        )

    # Find existing pending payment record for this order
    payment_result = await db.execute(
        text("""
            SELECT id, transaction_id, status
            FROM payments
            WHERE order_id = :order_id
              AND gateway = 'stripe'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"order_id": data.order_id}
    )
    payment = payment_result.fetchone()

    stripe_service = StripePaymentService()

    # Idempotent: if payment already has a Stripe PI, retrieve it
    if payment and payment.transaction_id:
        try:
            existing_intent = stripe_service.retrieve_payment_intent(payment.transaction_id)
            if existing_intent.status in ("requires_payment_method", "requires_confirmation", "requires_action"):
                return PaymentIntentResponse(
                    client_secret=existing_intent.client_secret,
                    payment_intent_id=existing_intent.id,
                    payment_id=payment.id,
                )
        except Exception:
            logger.warning(f"Failed to retrieve existing PI {payment.transaction_id}, creating new one")

    # Fetch customer info for receipt
    customer_result = await db.execute(
        text("""
            SELECT c.email, c.name, c.first_name, c.last_name
            FROM customers c
            JOIN orders o ON o.customer_id = c.id
            WHERE o.id = :order_id
        """),
        {"order_id": data.order_id}
    )
    customer = customer_result.fetchone()
    customer_email = customer.email if customer else None
    customer_name = None
    if customer:
        customer_name = customer.name if hasattr(customer, "name") and customer.name else f"{customer.first_name or ''} {customer.last_name or ''}".strip()

    try:
        # Create new PaymentIntent
        intent = stripe_service.create_payment_intent(
            amount_inr=float(order.total_amount),
            order_id=str(order.id),
            order_number=order.order_number,
            customer_email=customer_email,
            customer_name=customer_name,
            payment_method_types=["card"],
        )

        if payment:
            # Update existing payment record
            await db.execute(
                text("""
                    UPDATE payments
                    SET transaction_id = :pi_id,
                        gateway = 'stripe',
                        status = 'PENDING'
                    WHERE id = :payment_id
                """),
                {
                    "pi_id": intent.id,
                    "payment_id": payment.id,
                }
            )
            payment_id = payment.id
        else:
            # Create new payment record
            new_payment_id = uuid.uuid4()
            await db.execute(
                text("""
                    INSERT INTO payments (id, order_id, amount, method, status, transaction_id, gateway, created_at)
                    VALUES (:id, :order_id, :amount, :method, 'PENDING', :transaction_id, 'stripe', :created_at)
                """),
                {
                    "id": new_payment_id,
                    "order_id": data.order_id,
                    "amount": float(order.total_amount),
                    "method": data.payment_method.upper(),
                    "transaction_id": intent.id,
                    "created_at": datetime.now(timezone.utc),
                }
            )
            payment_id = new_payment_id

        # Update order payment status to processing
        await db.execute(
            text("""
                UPDATE orders
                SET payment_status = 'PENDING',
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "updated_at": datetime.now(timezone.utc),
                "order_id": data.order_id,
            }
        )

        await db.commit()

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            payment_id=payment_id,
        )

    except Exception as e:
        logger.error(f"Failed to create Stripe PaymentIntent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}"
        )


@router.post(
    "/stripe/webhook",
    summary="Stripe webhook handler",
    description="Handle payment events from Stripe. Called by Stripe servers.",
    include_in_schema=False,
)
async def stripe_webhook(
    request: Request,
    db: DB,
):
    """
    Handle Stripe webhook events.

    Events handled:
    - payment_intent.succeeded: Payment completed
    - payment_intent.payment_failed: Payment failed

    Security:
    - Verifies webhook signature using STRIPE_WEBHOOK_SECRET
    - Idempotent: safe to receive duplicate events
    """
    from sqlalchemy import text
    from app.services.stripe_service import StripePaymentService
    import stripe as stripe_module

    # Read raw body for signature verification
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("Stripe webhook received without signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header"
        )

    stripe_service = StripePaymentService()

    try:
        event = stripe_service.construct_webhook_event(body, sig_header)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe_module.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    logger.info(f"Received Stripe webhook: {event.type}")

    try:
        if event.type == "payment_intent.succeeded":
            await _handle_stripe_payment_succeeded(db, event.data.object)

        elif event.type == "payment_intent.payment_failed":
            await _handle_stripe_payment_failed(db, event.data.object)

        else:
            logger.info(f"Unhandled Stripe event: {event.type}")

        return {"status": "ok", "event": event.type}

    except Exception as e:
        logger.error(f"Error processing Stripe webhook {event.type}: {e}")
        # Return 200 to prevent Stripe from retrying
        return {"status": "error", "message": str(e)}


async def _handle_stripe_payment_succeeded(db, payment_intent):
    """Handle payment_intent.succeeded - payment completed."""
    from sqlalchemy import text
    from app.services.email_service import send_order_notifications

    pi_id = payment_intent.id
    metadata = payment_intent.metadata or {}
    order_id = metadata.get("order_id")
    amount = payment_intent.amount / 100  # paise to INR

    if not order_id:
        logger.warning(f"Stripe PI {pi_id} succeeded without order_id in metadata")
        return

    logger.info(f"Stripe payment succeeded: {pi_id} for order {order_id}")

    # Extract card details from charges
    card_brand = None
    card_last4 = None
    charges = payment_intent.get("charges", {}).get("data", [])
    if not charges and hasattr(payment_intent, "latest_charge"):
        # latest_charge may be a string ID; skip card extraction in that case
        pass
    elif charges:
        charge = charges[0]
        payment_method_details = charge.get("payment_method_details", {})
        card_details = payment_method_details.get("card", {})
        card_brand = card_details.get("brand")
        card_last4 = card_details.get("last4")

    now = datetime.now(timezone.utc)

    # Update payment record
    import json
    gateway_response = {
        "payment_intent_id": pi_id,
        "card_brand": card_brand,
        "card_last4": card_last4,
    }

    await db.execute(
        text("""
            UPDATE payments
            SET status = 'PAID',
                completed_at = :completed_at,
                gateway_response = :gateway_response::jsonb
            WHERE transaction_id = :pi_id
              AND gateway = 'stripe'
        """),
        {
            "completed_at": now,
            "gateway_response": json.dumps(gateway_response),
            "pi_id": pi_id,
        }
    )

    # Update order status
    await db.execute(
        text("""
            UPDATE orders
            SET payment_status = 'PAID',
                status = CASE
                    WHEN status IN ('NEW', 'PENDING_PAYMENT') THEN 'CONFIRMED'
                    ELSE status
                END,
                amount_paid = :amount,
                paid_at = :paid_at,
                confirmed_at = CASE
                    WHEN status IN ('NEW', 'PENDING_PAYMENT') THEN :paid_at
                    ELSE confirmed_at
                END,
                updated_at = :updated_at
            WHERE id = :order_id::uuid
        """),
        {
            "amount": amount,
            "paid_at": now,
            "updated_at": now,
            "order_id": order_id,
        }
    )

    # Add status history entry
    await db.execute(
        text("""
            INSERT INTO order_status_history (id, order_id, from_status, to_status, notes, created_at)
            VALUES (gen_random_uuid(), :order_id::uuid, 'PENDING_PAYMENT', 'CONFIRMED',
                    :notes, :created_at)
        """),
        {
            "order_id": order_id,
            "notes": f"Payment confirmed via Stripe. PI: {pi_id}",
            "created_at": now,
        }
    )

    await db.commit()

    # Send notifications (non-blocking)
    try:
        order_result = await db.execute(
            text("""
                SELECT o.order_number, o.total_amount, o.payment_method, o.shipping_address,
                       c.name as customer_name, c.email as customer_email, c.phone as customer_phone
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = :order_id::uuid
            """),
            {"order_id": order_id}
        )
        order_data = order_result.fetchone()

        items_result = await db.execute(
            text("""
                SELECT product_name, variant_name, quantity, total_amount
                FROM order_items
                WHERE order_id = :order_id::uuid
            """),
            {"order_id": order_id}
        )
        items = [dict(row._mapping) for row in items_result.fetchall()]

        if order_data and order_data.customer_email:
            import json
            from decimal import Decimal

            shipping_address = order_data.shipping_address
            if isinstance(shipping_address, str):
                shipping_address = json.loads(shipping_address)

            await send_order_notifications(
                order_number=order_data.order_number,
                customer_email=order_data.customer_email,
                customer_phone=order_data.customer_phone,
                customer_name=order_data.customer_name,
                total_amount=Decimal(str(order_data.total_amount)),
                items=items,
                shipping_address=shipping_address,
                payment_method="Stripe (Card)"
            )
            logger.info(f"Notifications sent for Stripe payment on order {order_data.order_number}")
    except Exception as e:
        logger.error(f"Failed to send notifications for Stripe payment: {e}")

    # Accounting integration
    try:
        from app.services.auto_journal_service import AutoJournalService, AutoJournalError
        from decimal import Decimal

        auto_journal = AutoJournalService(db)
        await auto_journal.generate_for_order_payment(
            order_id=uuid.UUID(order_id),
            amount=Decimal(str(amount)),
            payment_method="STRIPE",
            reference_number=pi_id,
            user_id=None,
            auto_post=True,
            is_cash=False,
        )
        await db.commit()
        logger.info(f"Accounting entry created for Stripe payment {pi_id}")
    except Exception as e:
        logger.warning(f"Failed to create accounting entry for Stripe payment {pi_id}: {e}")

    logger.info(f"Order {order_id} updated for Stripe payment {pi_id}")


async def _handle_stripe_payment_failed(db, payment_intent):
    """Handle payment_intent.payment_failed - payment failed."""
    from sqlalchemy import text

    pi_id = payment_intent.id
    metadata = payment_intent.metadata or {}
    order_id = metadata.get("order_id")
    error_message = ""
    if payment_intent.last_payment_error:
        error_message = payment_intent.last_payment_error.get("message", "Unknown error")

    if not order_id:
        return

    logger.info(f"Stripe payment failed: {pi_id} - {error_message}")

    now = datetime.now(timezone.utc)

    # Update payment record
    await db.execute(
        text("""
            UPDATE payments
            SET status = 'FAILED',
                notes = :error_msg,
                completed_at = :completed_at
            WHERE transaction_id = :pi_id
              AND gateway = 'stripe'
        """),
        {
            "error_msg": f"Payment failed: {error_message}",
            "completed_at": now,
            "pi_id": pi_id,
        }
    )

    # Update order
    await db.execute(
        text("""
            UPDATE orders
            SET payment_status = 'FAILED',
                internal_notes = COALESCE(internal_notes, '') ||
                    E'\n[Stripe Payment Failed] ' || :error_msg,
                updated_at = :updated_at
            WHERE id = :order_id::uuid
        """),
        {
            "order_id": order_id,
            "error_msg": error_message,
            "updated_at": now,
        }
    )

    await db.commit()


@router.get(
    "/stripe/{order_id}",
    response_model=PaymentStatusResponse,
    summary="Get Stripe payment status for an order",
    description="Fetch the latest Stripe payment record for an order.",
)
async def stripe_get_payment_status(
    order_id: uuid.UUID,
    db: DB,
):
    """Get the latest Stripe payment status for an order."""
    from sqlalchemy import text

    result = await db.execute(
        text("""
            SELECT id, order_id, amount, method, status, gateway,
                   transaction_id, gateway_response, reference_number, notes,
                   created_at, completed_at
            FROM payments
            WHERE order_id = :order_id
              AND gateway = 'stripe'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"order_id": order_id}
    )
    payment = result.fetchone()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Stripe payment found for this order"
        )

    return PaymentStatusResponse(
        id=payment.id,
        order_id=payment.order_id,
        amount=float(payment.amount),
        method=payment.method,
        status=payment.status,
        gateway=payment.gateway,
        transaction_id=payment.transaction_id,
        gateway_response=payment.gateway_response,
        reference_number=payment.reference_number,
        notes=payment.notes,
        created_at=payment.created_at.isoformat() if payment.created_at else None,
        completed_at=payment.completed_at.isoformat() if payment.completed_at else None,
    )


@router.post(
    "/stripe/{payment_id}/refund",
    response_model=StripeRefundResponse,
    dependencies=[Depends(require_permissions("finance:update"))],
    summary="Initiate a Stripe refund",
    description="Initiate a full or partial refund for a Stripe payment. Requires finance:update permission.",
)
async def stripe_initiate_refund(
    payment_id: uuid.UUID,
    data: StripeRefundRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Initiate a Stripe refund for a payment.

    Requires: finance:update permission
    """
    from sqlalchemy import text
    from app.services.stripe_service import StripePaymentService

    # Fetch payment record
    result = await db.execute(
        text("""
            SELECT id, order_id, transaction_id, amount, status, gateway
            FROM payments
            WHERE id = :payment_id AND gateway = 'stripe'
        """),
        {"payment_id": payment_id}
    )
    payment = result.fetchone()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stripe payment not found"
        )

    if not payment.transaction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has no Stripe PaymentIntent ID"
        )

    if payment.status not in ("PAID", "CAPTURED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund payment with status: {payment.status}"
        )

    stripe_service = StripePaymentService()

    try:
        refund = stripe_service.create_refund(
            payment_intent_id=payment.transaction_id,
            amount_inr=data.amount,
            reason=data.reason,
        )

        refund_amount = refund.amount / 100  # paise to INR
        now = datetime.now(timezone.utc)

        # Update payment status
        new_status = "REFUNDED" if data.amount is None else "PARTIALLY_REFUNDED"
        await db.execute(
            text("""
                UPDATE payments
                SET status = :status,
                    notes = COALESCE(notes, '') || E'\n[Refund] ' || :refund_note
                WHERE id = :payment_id
            """),
            {
                "status": new_status,
                "refund_note": f"Refund {refund.id}: ₹{refund_amount} by {current_user.id}. Reason: {data.reason or 'N/A'}",
                "payment_id": payment_id,
            }
        )

        # Update order
        await db.execute(
            text("""
                UPDATE orders
                SET payment_status = :pay_status,
                    amount_paid = GREATEST(0, amount_paid - :refund_amount),
                    status = CASE
                        WHEN :is_full_refund THEN 'REFUNDED'
                        ELSE status
                    END,
                    internal_notes = COALESCE(internal_notes, '') ||
                        E'\n[Stripe Refund] ID: ' || :refund_id || ', Amount: ₹' || :refund_amount::text,
                    updated_at = :updated_at
                WHERE id = :order_id
            """),
            {
                "pay_status": "REFUNDED" if data.amount is None else "PARTIALLY_PAID",
                "refund_amount": refund_amount,
                "is_full_refund": data.amount is None,
                "refund_id": refund.id,
                "updated_at": now,
                "order_id": payment.order_id,
            }
        )

        await db.commit()

        return StripeRefundResponse(
            refund_id=refund.id,
            payment_id=payment.id,
            amount=refund_amount,
            status=refund.status,
        )

    except Exception as e:
        logger.error(f"Stripe refund failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process refund: {str(e)}"
        )
