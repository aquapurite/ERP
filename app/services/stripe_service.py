"""
Stripe Payment Service

Handles Stripe payment processing for the D2C storefront:
- Create PaymentIntents
- Verify webhook signatures
- Process refunds
- Fetch payment status
"""

import logging
from typing import Optional, Dict, Any

import stripe

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe API key at module level
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service for handling Stripe payments."""

    def __init__(self):
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    def create_payment_intent(
        self,
        amount_inr: float,
        order_id: str,
        order_number: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        payment_method_types: Optional[list] = None,
    ) -> stripe.PaymentIntent:
        """
        Create a Stripe PaymentIntent.

        Args:
            amount_inr: Amount in INR (will be converted to paise)
            order_id: Internal order ID
            order_number: Human-readable order number
            customer_email: Customer email for receipt
            customer_name: Customer name
            payment_method_types: Allowed payment methods (default: ['card'])

        Returns:
            Stripe PaymentIntent object
        """
        amount_paise = int(round(amount_inr * 100))

        if payment_method_types is None:
            payment_method_types = ["card"]

        intent_params: Dict[str, Any] = {
            "amount": amount_paise,
            "currency": "inr",
            "payment_method_types": payment_method_types,
            "metadata": {
                "order_id": str(order_id),
                "order_number": order_number,
            },
        }

        if customer_email:
            intent_params["receipt_email"] = customer_email
        if customer_name:
            intent_params["metadata"]["customer_name"] = customer_name

        intent = stripe.PaymentIntent.create(**intent_params)

        logger.info(
            f"Created Stripe PaymentIntent {intent.id} for order {order_id} "
            f"(amount: {amount_paise} paise)"
        )

        return intent

    def retrieve_payment_intent(self, payment_intent_id: str) -> stripe.PaymentIntent:
        """Retrieve an existing PaymentIntent."""
        return stripe.PaymentIntent.retrieve(payment_intent_id)

    def construct_webhook_event(
        self, payload: bytes, sig_header: str
    ) -> stripe.Event:
        """
        Verify and construct a Stripe webhook event.

        Args:
            payload: Raw request body bytes
            sig_header: Stripe-Signature header value

        Returns:
            Verified Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
            ValueError: If payload is invalid
        """
        return stripe.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )

    def create_refund(
        self,
        payment_intent_id: str,
        amount_inr: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> stripe.Refund:
        """
        Create a refund for a PaymentIntent.

        Args:
            payment_intent_id: Stripe PaymentIntent ID
            amount_inr: Partial refund amount in INR (None for full refund)
            reason: Refund reason

        Returns:
            Stripe Refund object
        """
        refund_params: Dict[str, Any] = {
            "payment_intent": payment_intent_id,
        }

        if amount_inr is not None:
            refund_params["amount"] = int(round(amount_inr * 100))

        if reason:
            refund_params["metadata"] = {"reason": reason}

        refund = stripe.Refund.create(**refund_params)

        logger.info(
            f"Created Stripe refund {refund.id} for PI {payment_intent_id} "
            f"(amount: {refund.amount} paise, status: {refund.status})"
        )

        return refund
