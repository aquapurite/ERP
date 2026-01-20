"""Pydantic schemas for Sales Channel module."""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.channel import ChannelType, ChannelStatus


# ==================== SalesChannel Schemas ====================

class SalesChannelBase(BaseModel):
    """Base schema for SalesChannel."""
    name: str = Field(..., min_length=2, max_length=200)
    channel_type: ChannelType
    code: Optional[str] = Field(None, min_length=2, max_length=30)
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    status: ChannelStatus = ChannelStatus.ACTIVE

    # Marketplace Integration
    seller_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    webhook_url: Optional[str] = None

    # Fulfillment Settings
    default_warehouse_id: Optional[UUID] = None
    fulfillment_type: Optional[str] = None
    auto_confirm_orders: bool = False
    auto_allocate_inventory: bool = True

    # Commission & Fees
    commission_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    fixed_fee_per_order: Optional[Decimal] = Field(None, ge=0)
    payment_cycle_days: int = Field(7, ge=1)

    # Pricing Rules
    price_markup_percentage: Optional[Decimal] = Field(None, ge=0)
    price_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    use_channel_specific_pricing: bool = False

    # Return Policy
    return_window_days: int = Field(7, ge=0)
    replacement_window_days: int = Field(7, ge=0)
    supports_return_pickup: bool = True

    # Tax Settings
    tax_inclusive_pricing: bool = True
    collect_tcs: bool = False
    tcs_rate: Optional[Decimal] = Field(None, ge=0, le=10)

    # Contact
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    # Sync Settings
    sync_enabled: bool = True
    sync_interval_minutes: int = Field(30, ge=5)


class SalesChannelCreate(SalesChannelBase):
    """Schema for creating SalesChannel."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    config: Optional[dict] = None


class SalesChannelUpdate(BaseModel):
    """Schema for updating SalesChannel."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    status: Optional[ChannelStatus] = None
    seller_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    default_warehouse_id: Optional[UUID] = None
    fulfillment_type: Optional[str] = None
    auto_confirm_orders: Optional[bool] = None
    auto_allocate_inventory: Optional[bool] = None
    commission_percentage: Optional[Decimal] = None
    fixed_fee_per_order: Optional[Decimal] = None
    payment_cycle_days: Optional[int] = None
    price_markup_percentage: Optional[Decimal] = None
    price_discount_percentage: Optional[Decimal] = None
    use_channel_specific_pricing: Optional[bool] = None
    return_window_days: Optional[int] = None
    replacement_window_days: Optional[int] = None
    supports_return_pickup: Optional[bool] = None
    tax_inclusive_pricing: Optional[bool] = None
    collect_tcs: Optional[bool] = None
    tcs_rate: Optional[Decimal] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    config: Optional[dict] = None
    sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None


class SalesChannelResponse(SalesChannelBase):
    """Response schema for SalesChannel."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    config: Optional[dict] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed
    is_marketplace: bool = False


class SalesChannelListResponse(BaseModel):
    """Response for listing channels."""
    items: List[SalesChannelResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== ChannelPricing Schemas ====================

class ChannelPricingBase(BaseModel):
    """Base schema for ChannelPricing."""
    channel_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    mrp: Decimal = Field(..., gt=0)
    selling_price: Decimal = Field(..., gt=0)
    transfer_price: Optional[Decimal] = Field(None, gt=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    max_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: bool = True
    is_listed: bool = True
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ChannelPricingCreate(BaseModel):
    """Schema for creating ChannelPricing. channel_id comes from URL path."""
    product_id: UUID
    variant_id: Optional[UUID] = None
    mrp: Decimal = Field(..., gt=0)
    selling_price: Decimal = Field(..., gt=0)
    transfer_price: Optional[Decimal] = Field(None, gt=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    max_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: bool = True
    is_listed: bool = True
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ChannelPricingUpdate(BaseModel):
    """Schema for updating ChannelPricing."""
    mrp: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    transfer_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    max_discount_percentage: Optional[Decimal] = None
    is_active: Optional[bool] = None
    is_listed: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ChannelPricingResponse(ChannelPricingBase):
    """Response schema for ChannelPricing."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    margin_percentage: Decimal
    created_at: datetime
    updated_at: datetime


class ChannelPricingBulkCreate(BaseModel):
    """Bulk create channel pricing."""
    channel_id: UUID
    items: List[dict]  # [{"product_id": uuid, "mrp": 1000, "selling_price": 900}]


class ChannelPricingListResponse(BaseModel):
    """Response for listing channel pricing."""
    items: List[ChannelPricingResponse]
    total: int
    skip: int = 0
    limit: int = 50


# ==================== ChannelInventory Schemas ====================

class ChannelInventoryBase(BaseModel):
    """Base schema for ChannelInventory."""
    channel_id: UUID
    warehouse_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    allocated_quantity: int = Field(0, ge=0)
    buffer_quantity: int = Field(0, ge=0)
    reserved_quantity: int = Field(0, ge=0)
    is_active: bool = True


class ChannelInventoryCreate(BaseModel):
    """Schema for creating ChannelInventory. channel_id comes from URL path."""
    warehouse_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    allocated_quantity: int = Field(0, ge=0)
    buffer_quantity: int = Field(0, ge=0)
    reserved_quantity: int = Field(0, ge=0)
    is_active: bool = True


class ChannelInventoryUpdate(BaseModel):
    """Schema for updating ChannelInventory."""
    allocated_quantity: Optional[int] = None
    buffer_quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    is_active: Optional[bool] = None


class ChannelInventoryResponse(ChannelInventoryBase):
    """Response schema for ChannelInventory."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    marketplace_quantity: int
    available_quantity: int
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChannelInventorySyncRequest(BaseModel):
    """Request to sync inventory to marketplace. channel_id comes from URL path."""
    product_ids: Optional[List[UUID]] = None  # If None, sync all


# ==================== ChannelOrder Schemas ====================

class ChannelOrderBase(BaseModel):
    """Base schema for ChannelOrder."""
    channel_id: UUID
    order_id: UUID
    channel_order_id: str
    channel_order_item_id: Optional[str] = None
    channel_selling_price: Decimal
    channel_shipping_fee: Decimal = Decimal("0")
    channel_commission: Decimal = Decimal("0")
    channel_tcs: Decimal = Decimal("0")
    net_receivable: Decimal
    channel_status: Optional[str] = None


class ChannelOrderCreate(BaseModel):
    """Schema for creating ChannelOrder. channel_id comes from URL path."""
    order_id: UUID
    channel_order_id: str
    channel_order_item_id: Optional[str] = None
    channel_selling_price: Decimal
    channel_shipping_fee: Decimal = Decimal("0")
    channel_commission: Decimal = Decimal("0")
    channel_tcs: Decimal = Decimal("0")
    net_receivable: Decimal
    channel_status: Optional[str] = None
    raw_order_data: Optional[dict] = None


class ChannelOrderResponse(ChannelOrderBase):
    """Response schema for ChannelOrder."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_order_data: Optional[dict] = None
    synced_at: datetime
    last_status_sync_at: Optional[datetime] = None
    settlement_id: Optional[str] = None
    settlement_date: Optional[datetime] = None
    is_settled: bool
    created_at: datetime


class ChannelOrderListResponse(BaseModel):
    """Response for listing channel orders."""
    items: List[ChannelOrderResponse]
    total: int
    total_value: Decimal = Decimal("0")
    skip: int = 0
    limit: int = 50
    pages: int = 1


class ChannelOrderUpdate(BaseModel):
    """Update schema for ChannelOrder."""
    channel_status: Optional[str] = None
    settlement_id: Optional[str] = None
    settlement_date: Optional[datetime] = None
    is_settled: Optional[bool] = None


class ChannelInventoryListResponse(BaseModel):
    """Response for listing channel inventory."""
    items: List[ChannelInventoryResponse]
    total: int
    skip: int = 0
    limit: int = 50


# ==================== Sync Schemas ====================

class InventorySyncRequest(BaseModel):
    """Request to sync inventory to channel. channel_id comes from URL path."""
    product_ids: Optional[List[UUID]] = None
    sync_all: bool = False


class PriceSyncRequest(BaseModel):
    """Request to sync prices to channel. channel_id comes from URL path."""
    product_ids: Optional[List[UUID]] = None
    sync_all: bool = False


class OrderSyncResponse(BaseModel):
    """Response from order sync."""
    channel_id: UUID
    channel_name: str
    orders_fetched: int = 0
    orders_created: int = 0
    orders_updated: int = 0
    orders_failed: int = 0
    sync_time: datetime
    status: str = "SUCCESS"
    message: Optional[str] = None


# ==================== Product Channel Settings Schemas ====================

class ProductChannelSettingsBase(BaseModel):
    """Base schema for ProductChannelSettings."""
    product_id: UUID
    channel_id: UUID
    warehouse_id: UUID
    # Allocation defaults
    default_allocation_percentage: Optional[int] = Field(None, ge=0, le=100)
    default_allocation_qty: int = Field(0, ge=0)
    # Auto-replenish settings
    safety_stock: int = Field(0, ge=0, description="Target level to maintain")
    reorder_point: int = Field(0, ge=0, description="Trigger replenishment when below this")
    max_allocation: Optional[int] = Field(None, ge=0)
    # Flags
    auto_replenish_enabled: bool = True
    replenish_from_shared_pool: bool = True
    # Sync settings
    sync_enabled: bool = True
    sync_buffer_percentage: Optional[int] = Field(None, ge=0, le=100)
    is_active: bool = True


class ProductChannelSettingsCreate(BaseModel):
    """Schema for creating ProductChannelSettings."""
    product_id: UUID
    channel_id: UUID
    warehouse_id: UUID
    default_allocation_percentage: Optional[int] = None
    default_allocation_qty: int = 0
    safety_stock: int = 0
    reorder_point: int = 0
    max_allocation: Optional[int] = None
    auto_replenish_enabled: bool = True
    replenish_from_shared_pool: bool = True
    sync_enabled: bool = True
    sync_buffer_percentage: Optional[int] = None
    is_active: bool = True


class ProductChannelSettingsUpdate(BaseModel):
    """Schema for updating ProductChannelSettings."""
    default_allocation_percentage: Optional[int] = None
    default_allocation_qty: Optional[int] = None
    safety_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    max_allocation: Optional[int] = None
    auto_replenish_enabled: Optional[bool] = None
    replenish_from_shared_pool: Optional[bool] = None
    sync_enabled: Optional[bool] = None
    sync_buffer_percentage: Optional[int] = None
    is_active: Optional[bool] = None


class ProductChannelSettingsResponse(ProductChannelSettingsBase):
    """Response schema for ProductChannelSettings."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ProductChannelSettingsListResponse(BaseModel):
    """Response for listing ProductChannelSettings."""
    items: List[ProductChannelSettingsResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== GRN Channel Allocation Schemas ====================

class GRNChannelAllocationItem(BaseModel):
    """Single channel allocation for GRN."""
    channel_id: UUID
    channel_code: Optional[str] = None
    quantity: int = Field(..., ge=0)
    buffer_quantity: int = Field(0, ge=0)
    safety_stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)


class GRNChannelAllocationRequest(BaseModel):
    """Request to allocate GRN received quantity to channels."""
    grn_id: UUID
    warehouse_id: UUID
    product_id: UUID
    total_quantity: int = Field(..., ge=0)
    allocations: List[GRNChannelAllocationItem]


class GRNChannelAllocationResponse(BaseModel):
    """Response from GRN channel allocation."""
    grn_id: UUID
    product_id: UUID
    total_received: int
    total_allocated: int
    unallocated: int
    channel_allocations: List[dict]
    success: bool
    message: Optional[str] = None


# ==================== Channel Availability Schemas ====================

class ChannelAvailabilityRequest(BaseModel):
    """Request to check channel availability."""
    channel_code: str
    product_ids: List[UUID]
    warehouse_id: Optional[UUID] = None


class ChannelAvailabilityItem(BaseModel):
    """Availability for a single product on a channel."""
    product_id: UUID
    channel_code: str
    channel_id: Optional[UUID] = None
    is_available: bool
    available_quantity: int
    allocated_quantity: int = 0
    buffer_quantity: int = 0
    reserved_quantity: int = 0
    soft_reserved: int = 0
    warehouse_id: Optional[UUID] = None
    error: Optional[str] = None


class ChannelAvailabilityResponse(BaseModel):
    """Response with channel availability for multiple products."""
    channel_code: str
    items: List[ChannelAvailabilityItem]
    timestamp: datetime


# ==================== Channel Reservation Schemas ====================

class ChannelReservationItem(BaseModel):
    """Item to reserve on a channel."""
    product_id: UUID
    quantity: int = Field(..., ge=1)


class ChannelReservationRequest(BaseModel):
    """Request to create channel reservation."""
    channel_code: str
    items: List[ChannelReservationItem]
    customer_id: Optional[UUID] = None
    session_id: Optional[str] = None
    ttl_seconds: int = Field(600, ge=60, le=3600)


class ChannelReservationResponse(BaseModel):
    """Response from channel reservation."""
    success: bool
    reservation_id: Optional[str] = None
    channel_code: str
    reserved_items: List[dict] = []
    failed_items: List[dict] = []
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


# ==================== Auto-Replenish Schemas ====================

class AutoReplenishRequest(BaseModel):
    """Request to trigger auto-replenishment."""
    channel_id: UUID
    product_id: UUID
    safety_stock: Optional[int] = None
    reorder_point: Optional[int] = None


class AutoReplenishResponse(BaseModel):
    """Response from auto-replenishment."""
    channel_id: UUID
    product_id: UUID
    replenished: bool
    quantity_replenished: int = 0
    quantity_needed: int = 0
    new_available: int = 0
    reason: Optional[str] = None
    details: List[dict] = []


# ==================== Marketplace Sync Schemas ====================

class MarketplaceSyncRequest(BaseModel):
    """Request to sync inventory to marketplace."""
    channel_id: UUID
    product_ids: Optional[List[UUID]] = None
    force_sync: bool = False


class MarketplaceSyncResponse(BaseModel):
    """Response from marketplace sync."""
    channel_id: UUID
    channel_name: str
    synced_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    sync_time: datetime
    status: str = "SUCCESS"
    errors: List[str] = []


# ==================== Channel Inventory Extended Schemas ====================

class ChannelInventoryExtendedResponse(ChannelInventoryResponse):
    """Extended channel inventory response with additional computed fields."""
    model_config = ConfigDict(from_attributes=True)

    # Product details
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    # Channel details
    channel_name: Optional[str] = None
    channel_code: Optional[str] = None
    # Warehouse details
    warehouse_name: Optional[str] = None
    warehouse_code: Optional[str] = None
    # Auto-replenish settings
    safety_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    auto_replenish_enabled: Optional[bool] = None
    # Sync status
    sync_status: Optional[str] = None  # SYNCED, PENDING, OUT_OF_SYNC, FAILED


class ChannelInventorySummary(BaseModel):
    """Summary of channel inventory across all products."""
    channel_id: UUID
    channel_name: str
    channel_code: str
    total_products: int = 0
    total_allocated: int = 0
    total_available: int = 0
    total_reserved: int = 0
    total_buffer: int = 0
    synced_products: int = 0
    out_of_sync_products: int = 0
    low_stock_products: int = 0
