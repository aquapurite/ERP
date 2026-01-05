from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
import uuid

from app.models.customer import CustomerType, CustomerSource, AddressType


# ==================== ADDRESS SCHEMAS ====================

class AddressBase(BaseModel):
    """Base address schema."""
    address_type: AddressType = AddressType.HOME
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., max_length=10)
    country: str = Field(default="India", max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False


class AddressCreate(AddressBase):
    """Address creation schema."""
    pass


class AddressUpdate(BaseModel):
    """Address update schema."""
    address_type: Optional[AddressType] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AddressResponse(BaseModel):
    """Address response schema."""
    id: uuid.UUID
    address_type: AddressType
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool
    is_active: bool
    full_address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== CUSTOMER SCHEMAS ====================

class CustomerBase(BaseModel):
    """Base customer schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    source: CustomerSource = CustomerSource.WEBSITE
    company_name: Optional[str] = Field(None, max_length=200)
    gst_number: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    anniversary_date: Optional[date] = None
    region_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Customer creation schema."""
    addresses: Optional[List[AddressCreate]] = []


class CustomerUpdate(BaseModel):
    """Customer update schema."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    source: Optional[CustomerSource] = None
    company_name: Optional[str] = None
    gst_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary_date: Optional[date] = None
    region_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    """Customer response schema."""
    id: uuid.UUID
    customer_code: str
    first_name: str
    last_name: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    customer_type: CustomerType
    source: CustomerSource
    company_name: Optional[str] = None
    gst_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    anniversary_date: Optional[date] = None
    is_active: bool
    is_verified: bool
    notes: Optional[str] = None
    addresses: List[AddressResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerBrief(BaseModel):
    """Brief customer info."""
    id: uuid.UUID
    customer_code: str
    full_name: str
    phone: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Paginated customer list."""
    items: List[CustomerResponse]
    total: int
    page: int
    size: int
    pages: int
