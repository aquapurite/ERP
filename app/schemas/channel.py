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
    code: str = Field(..., min_length=2, max_length=30)
    name: str = Field(..., min_length=2, max_length=200)
    display_name: str = Field(..., min_length=2, max_length=200)
    channel_type: ChannelType
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


class ChannelPricingCreate(ChannelPricingBase):
    """Schema for creating ChannelPricing."""
    pass


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
    page: int = 1
    size: int = 50
    pages: int = 1


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


class ChannelInventoryCreate(ChannelInventoryBase):
    """Schema for creating ChannelInventory."""
    pass


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
    """Request to sync inventory to marketplace."""
    channel_id: UUID
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


class ChannelOrderCreate(ChannelOrderBase):
    """Schema for creating ChannelOrder."""
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
    page: int = 1
    size: int = 50
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
    page: int = 1
    size: int = 50
    pages: int = 1


# ==================== Sync Schemas ====================

class InventorySyncRequest(BaseModel):
    """Request to sync inventory to channel."""
    channel_id: UUID
    product_ids: Optional[List[UUID]] = None
    sync_all: bool = False


class PriceSyncRequest(BaseModel):
    """Request to sync prices to channel."""
    channel_id: UUID
    product_ids: Optional[List[UUID]] = None
    sync_all: bool = False


class OrderSyncResponse(BaseModel):
    """Response from order sync."""
    channel_id: UUID
    orders_synced: int
    orders_failed: int
    errors: List[str] = []
    sync_timestamp: datetime
