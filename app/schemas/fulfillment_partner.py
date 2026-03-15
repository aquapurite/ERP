"""Pydantic schemas for Fulfillment Partner CRUD."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class FulfillmentPartnerCreate(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    provider_type: str = Field(default="SELF_MANAGED", max_length=50)
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True
    config: Optional[Dict[str, Any]] = None


class FulfillmentPartnerUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    webhook_secret: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class FulfillmentPartnerResponse(BaseModel):
    id: UUID
    code: str
    name: str
    provider_type: str
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    webhook_secret: Optional[str] = None
    is_active: bool
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    warehouse_count: int = 0

    model_config = {"from_attributes": True}


class FulfillmentPartnerListResponse(BaseModel):
    items: List[FulfillmentPartnerResponse]
    total: int
