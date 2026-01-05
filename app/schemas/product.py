from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.product import ProductStatus, DocumentType


# ==================== IMAGE SCHEMAS ====================

class ProductImageCreate(BaseModel):
    """Product image creation."""
    image_url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    alt_text: Optional[str] = Field(None, max_length=255)
    is_primary: bool = False
    sort_order: int = 0


class ProductImageResponse(BaseModel):
    """Product image response."""
    id: uuid.UUID
    image_url: str
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    is_primary: bool
    sort_order: int

    class Config:
        from_attributes = True


# ==================== SPECIFICATION SCHEMAS ====================

class ProductSpecCreate(BaseModel):
    """Product specification creation."""
    group_name: str = Field(default="General", max_length=100)
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=500)
    sort_order: int = 0


class ProductSpecResponse(BaseModel):
    """Product specification response."""
    id: uuid.UUID
    group_name: str
    key: str
    value: str
    sort_order: int

    class Config:
        from_attributes = True


# ==================== VARIANT SCHEMAS ====================

class ProductVariantCreate(BaseModel):
    """Product variant creation."""
    name: str = Field(..., max_length=255)
    sku: str = Field(..., max_length=50)
    attributes: Optional[dict] = None
    mrp: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0


class ProductVariantUpdate(BaseModel):
    """Product variant update."""
    name: Optional[str] = Field(None, max_length=255)
    attributes: Optional[dict] = None
    mrp: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ProductVariantResponse(BaseModel):
    """Product variant response."""
    id: uuid.UUID
    name: str
    sku: str
    attributes: Optional[dict] = None
    mrp: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    stock_quantity: int
    image_url: Optional[str] = None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== DOCUMENT SCHEMAS ====================

class ProductDocumentCreate(BaseModel):
    """Product document creation."""
    title: str = Field(..., max_length=255)
    document_type: DocumentType = DocumentType.OTHER
    file_url: str = Field(..., max_length=500)
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    sort_order: int = 0


class ProductDocumentResponse(BaseModel):
    """Product document response."""
    id: uuid.UUID
    title: str
    document_type: DocumentType
    file_url: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PRODUCT SCHEMAS ====================

class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=280)
    sku: str = Field(..., min_length=1, max_length=50)
    model_number: Optional[str] = Field(None, max_length=100)

    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    features: Optional[str] = None

    category_id: uuid.UUID
    brand_id: uuid.UUID

    mrp: Decimal = Field(..., ge=0, description="Maximum Retail Price")
    selling_price: Decimal = Field(..., ge=0, description="Selling price")
    dealer_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)

    hsn_code: Optional[str] = Field(None, max_length=20)
    gst_rate: Optional[Decimal] = Field(default=18.00, ge=0, le=100)

    warranty_months: int = Field(default=12, ge=0)
    extended_warranty_available: bool = False
    warranty_terms: Optional[str] = None

    weight_kg: Optional[Decimal] = Field(None, ge=0)
    length_cm: Optional[Decimal] = Field(None, ge=0)
    width_cm: Optional[Decimal] = Field(None, ge=0)
    height_cm: Optional[Decimal] = Field(None, ge=0)

    min_stock_level: int = Field(default=10, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)

    is_featured: bool = False
    is_bestseller: bool = False
    is_new_arrival: bool = False
    sort_order: int = 0

    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=255)

    @field_validator("selling_price")
    @classmethod
    def selling_price_less_than_mrp(cls, v, info):
        """Validate selling price is not greater than MRP."""
        mrp = info.data.get("mrp")
        if mrp is not None and v > mrp:
            raise ValueError("Selling price cannot be greater than MRP")
        return v


class ProductCreate(ProductBase):
    """Product creation schema."""
    status: ProductStatus = ProductStatus.DRAFT
    images: Optional[List[ProductImageCreate]] = []
    specifications: Optional[List[ProductSpecCreate]] = []
    variants: Optional[List[ProductVariantCreate]] = []
    documents: Optional[List[ProductDocumentCreate]] = []
    extra_data: Optional[dict] = None


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=280)
    model_number: Optional[str] = Field(None, max_length=100)

    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    features: Optional[str] = None

    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None

    mrp: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    dealer_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)

    hsn_code: Optional[str] = None
    gst_rate: Optional[Decimal] = Field(None, ge=0, le=100)

    warranty_months: Optional[int] = Field(None, ge=0)
    extended_warranty_available: Optional[bool] = None
    warranty_terms: Optional[str] = None

    weight_kg: Optional[Decimal] = None
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None

    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)

    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    sort_order: Optional[int] = None

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None

    extra_data: Optional[dict] = None


class CategoryBrief(BaseModel):
    """Brief category info for product response."""
    id: uuid.UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


class BrandBrief(BaseModel):
    """Brief brand info for product response."""
    id: uuid.UUID
    name: str
    slug: str
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Product response schema."""
    id: uuid.UUID
    name: str
    slug: str
    sku: str
    model_number: Optional[str] = None

    short_description: Optional[str] = None
    description: Optional[str] = None
    features: Optional[str] = None

    category: CategoryBrief
    brand: BrandBrief

    mrp: Decimal
    selling_price: Decimal
    dealer_price: Optional[Decimal] = None
    discount_percentage: float

    hsn_code: Optional[str] = None
    gst_rate: Optional[Decimal] = None

    warranty_months: int
    extended_warranty_available: bool
    warranty_terms: Optional[str] = None

    weight_kg: Optional[Decimal] = None
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None

    status: ProductStatus
    is_active: bool
    is_featured: bool
    is_bestseller: bool
    is_new_arrival: bool
    sort_order: int

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None

    images: List[ProductImageResponse] = []

    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductDetailResponse(ProductResponse):
    """Detailed product response with all relations."""
    specifications: List[ProductSpecResponse] = []
    variants: List[ProductVariantResponse] = []
    documents: List[ProductDocumentResponse] = []
    extra_data: Optional[dict] = None


class ProductListResponse(BaseModel):
    """Paginated product list."""
    items: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class ProductBriefResponse(BaseModel):
    """Brief product response for lists/dropdowns."""
    id: uuid.UUID
    name: str
    sku: str
    slug: str
    mrp: Decimal
    selling_price: Decimal
    primary_image_url: Optional[str] = None
    category_name: str
    brand_name: str
    is_active: bool
    status: ProductStatus

    class Config:
        from_attributes = True
