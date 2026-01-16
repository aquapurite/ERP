from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.order import OrderStatus, PaymentStatus, PaymentMethod, OrderSource
from app.schemas.customer import CustomerBrief, AddressResponse


# ==================== ORDER ITEM SCHEMAS ====================

class OrderItemCreate(BaseModel):
    """Order item creation schema."""
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: int = Field(..., ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0)  # Override price if needed


class OrderItemResponse(BaseModel):
    """Order item response schema."""
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    product_name: str
    product_sku: str
    variant_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    unit_mrp: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    hsn_code: Optional[str] = None
    warranty_months: int
    serial_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PAYMENT SCHEMAS ====================

class PaymentCreate(BaseModel):
    """Payment creation schema."""
    amount: Decimal = Field(..., ge=0)
    method: PaymentMethod
    transaction_id: Optional[str] = None
    gateway: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response schema."""
    id: uuid.UUID
    amount: Decimal
    method: PaymentMethod
    status: str
    transaction_id: Optional[str] = None
    gateway: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== STATUS HISTORY SCHEMAS ====================

class StatusHistoryResponse(BaseModel):
    """Order status history response."""
    id: uuid.UUID
    from_status: Optional[OrderStatus] = None
    to_status: OrderStatus
    changed_by: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== INVOICE SCHEMAS ====================

class InvoiceResponse(BaseModel):
    """Invoice response schema."""
    id: uuid.UUID
    invoice_number: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    pdf_url: Optional[str] = None
    invoice_date: datetime
    due_date: Optional[datetime] = None
    is_cancelled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== ORDER SCHEMAS ====================

class AddressInput(BaseModel):
    """Address input for order (can be existing address ID or new address data)."""
    address_id: Optional[uuid.UUID] = None
    # Or provide full address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class OrderCreate(BaseModel):
    """Order creation schema."""
    customer_id: uuid.UUID
    source: OrderSource = OrderSource.WEBSITE
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: AddressInput
    billing_address: Optional[AddressInput] = None
    payment_method: PaymentMethod = PaymentMethod.COD
    discount_code: Optional[str] = None
    customer_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    region_id: Optional[uuid.UUID] = None


class OrderUpdate(BaseModel):
    """Order update schema."""
    status: Optional[OrderStatus] = None
    payment_method: Optional[PaymentMethod] = None
    expected_delivery_date: Optional[datetime] = None
    customer_notes: Optional[str] = None
    internal_notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Order status update schema."""
    status: OrderStatus
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response schema."""
    id: uuid.UUID
    order_number: str
    customer: Optional[CustomerBrief] = None
    status: str
    source: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    total_amount: Decimal
    discount_code: Optional[str] = None
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    amount_paid: Decimal
    balance_due: Decimal
    shipping_address: dict
    billing_address: Optional[dict] = None
    expected_delivery_date: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    customer_notes: Optional[str] = None
    item_count: int
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    """Detailed order response with items and history."""
    items: List[OrderItemResponse] = []
    status_history: List[StatusHistoryResponse] = []
    payments: List[PaymentResponse] = []
    invoice: Optional[InvoiceResponse] = None
    internal_notes: Optional[str] = None


class OrderListResponse(BaseModel):
    """Paginated order list."""
    items: List[OrderResponse]
    total: int
    page: int
    size: int
    pages: int


class OrderSummary(BaseModel):
    """Order summary statistics."""
    total_orders: int
    pending_orders: int
    processing_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    average_order_value: Decimal


# ==================== D2C ORDER SCHEMAS ====================

class D2CCustomerInfo(BaseModel):
    """Customer info for D2C orders."""
    name: str = Field(..., min_length=2, description="Customer full name")
    phone: str = Field(..., pattern=r"^\d{10}$", description="10-digit phone number")
    email: str = Field(..., description="Customer email")


class D2CAddressInfo(BaseModel):
    """Address info for D2C orders."""
    name: str = Field(..., description="Contact name")
    phone: str = Field(..., description="Contact phone")
    address_line_1: str = Field(..., description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    pincode: str = Field(..., pattern=r"^\d{6}$", description="6-digit pincode")
    landmark: Optional[str] = Field(None, description="Landmark")
    country: str = Field("India", description="Country")


class D2COrderItem(BaseModel):
    """Item for D2C order."""
    product_id: uuid.UUID = Field(..., description="Product ID")
    sku: str = Field(..., description="Product SKU")
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    mrp: Decimal = Field(..., ge=0, description="MRP")


class D2COrderCreate(BaseModel):
    """D2C order creation - no authentication required."""
    channel: str = Field("D2C", description="Sales channel")
    customer: D2CCustomerInfo = Field(..., description="Customer information")
    shipping_address: D2CAddressInfo = Field(..., description="Shipping address")
    billing_address: Optional[D2CAddressInfo] = Field(None, description="Billing address")
    items: List[D2COrderItem] = Field(..., min_length=1, description="Order items")
    payment_method: str = Field("cod", description="Payment method")
    subtotal: Decimal = Field(..., description="Subtotal")
    discount_amount: Decimal = Field(Decimal("0"), description="Discount amount")
    shipping_amount: Decimal = Field(Decimal("0"), description="Shipping amount")
    total_amount: Decimal = Field(..., description="Total amount")


class D2COrderResponse(BaseModel):
    """Simple response for D2C order."""
    id: uuid.UUID = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    total_amount: Decimal = Field(..., description="Total amount")
    status: str = Field(..., description="Order status")
