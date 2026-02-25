"""Payment schemas for Razorpay API requests/responses."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid


class CreatePaymentOrderRequest(BaseModel):
    """API request to create a payment order."""
    order_id: uuid.UUID = Field(..., description="Internal order ID")
    amount: float = Field(..., gt=0, description="Amount in INR")
    customer_name: str = Field(..., min_length=1, description="Customer name")
    customer_email: Optional[str] = Field(None, description="Customer email (optional)")
    customer_phone: str = Field(..., min_length=10, description="Customer phone")
    notes: Optional[dict] = Field(None, description="Additional notes for Razorpay")


class VerifyPaymentRequest(BaseModel):
    """API request to verify payment."""
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID")
    razorpay_signature: str = Field(..., description="Razorpay signature for verification")
    order_id: uuid.UUID = Field(..., description="Internal order ID")


class InitiateRefundRequest(BaseModel):
    """API request to initiate a refund."""
    payment_id: str = Field(..., description="Razorpay payment ID")
    order_id: uuid.UUID = Field(..., description="Internal order ID")
    amount: Optional[float] = Field(None, gt=0, description="Refund amount (for partial refund)")
    reason: Optional[str] = Field(None, description="Reason for refund")


# ==================== Stripe Payment Schemas ====================

class CreatePaymentIntentRequest(BaseModel):
    """Request to create a Stripe PaymentIntent for an order."""
    order_id: uuid.UUID = Field(..., description="Internal order ID")
    payment_method: str = Field(..., description="Payment method: CARD or UPI")


class PaymentIntentResponse(BaseModel):
    """Response after creating a Stripe PaymentIntent."""
    client_secret: str = Field(..., description="Stripe client secret for frontend confirmation")
    payment_intent_id: str = Field(..., description="Stripe PaymentIntent ID (pi_...)")
    payment_id: uuid.UUID = Field(..., description="Internal payment record ID")


class PaymentStatusResponse(BaseModel):
    """Full payment status for an order."""
    id: uuid.UUID
    order_id: uuid.UUID
    amount: float
    method: str
    status: str
    gateway: Optional[str] = None
    transaction_id: Optional[str] = None
    gateway_response: Optional[dict] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class StripeRefundRequest(BaseModel):
    """Request to initiate a Stripe refund."""
    reason: Optional[str] = Field(None, description="Reason for refund")
    amount: Optional[float] = Field(None, gt=0, description="Partial refund amount in INR (omit for full refund)")


class StripeRefundResponse(BaseModel):
    """Response after Stripe refund initiation."""
    refund_id: str = Field(..., description="Stripe refund ID (re_...)")
    payment_id: uuid.UUID = Field(..., description="Internal payment record ID")
    amount: float = Field(..., description="Refund amount in INR")
    status: str = Field(..., description="Refund status")
