"""Storefront schemas for public D2C website API."""
from pydantic import BaseModel, Field
from typing import Optional, List


class StorefrontProductImage(BaseModel):
    """Product image for storefront."""
    url: str = Field(..., description="Image URL")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")
    is_primary: bool = Field(False, description="Whether this is the primary image")

    class Config:
        from_attributes = True


class StorefrontProductResponse(BaseModel):
    """Product response for storefront."""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    slug: str = Field(..., description="URL slug")
    sku: str = Field(..., description="SKU code")
    short_description: Optional[str] = Field(None, description="Short description")
    description: Optional[str] = Field(None, description="Full description")
    mrp: float = Field(..., description="Maximum retail price")
    selling_price: Optional[float] = Field(None, description="Selling price")
    category_id: Optional[str] = Field(None, description="Category ID")
    category_name: Optional[str] = Field(None, description="Category name")
    brand_id: Optional[str] = Field(None, description="Brand ID")
    brand_name: Optional[str] = Field(None, description="Brand name")
    warranty_months: int = Field(12, description="Warranty in months")
    is_featured: bool = Field(False, description="Featured product flag")
    is_bestseller: bool = Field(False, description="Bestseller flag")
    is_new_arrival: bool = Field(False, description="New arrival flag")
    images: List[StorefrontProductImage] = Field([], description="Product images")
    # Stock information
    in_stock: bool = Field(True, description="Whether product is in stock")
    stock_quantity: int = Field(0, description="Available stock quantity")

    class Config:
        from_attributes = True


class StorefrontCategoryResponse(BaseModel):
    """Category response for storefront."""
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL slug")
    description: Optional[str] = Field(None, description="Category description")
    image_url: Optional[str] = Field(None, description="Category image URL")
    parent_id: Optional[str] = Field(None, description="Parent category ID")

    class Config:
        from_attributes = True


class StorefrontBrandResponse(BaseModel):
    """Brand response for storefront."""
    id: str = Field(..., description="Brand ID")
    name: str = Field(..., description="Brand name")
    slug: str = Field(..., description="URL slug")
    description: Optional[str] = Field(None, description="Brand description")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")

    class Config:
        from_attributes = True


class PaginatedProductsResponse(BaseModel):
    """Paginated products response."""
    items: List[StorefrontProductResponse] = Field(..., description="Product items")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class StorefrontCompanyInfo(BaseModel):
    """Public company info for storefront."""
    name: str = Field(..., description="Company legal name")
    trade_name: Optional[str] = Field(None, description="Trade name")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    logo_small_url: Optional[str] = Field(None, description="Small logo URL")
    favicon_url: Optional[str] = Field(None, description="Favicon URL")
    email: str = Field(..., description="Contact email")
    phone: str = Field(..., description="Contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    address: str = Field(..., description="Address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    pincode: str = Field(..., description="Pincode")

    class Config:
        from_attributes = True


# ==================== Search Suggestions ====================

class SearchProductSuggestion(BaseModel):
    """Product suggestion in search results."""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    slug: str = Field(..., description="URL slug")
    image_url: Optional[str] = Field(None, description="Primary image URL")
    price: float = Field(..., description="Selling price")
    mrp: float = Field(..., description="MRP")

    class Config:
        from_attributes = True


class SearchCategorySuggestion(BaseModel):
    """Category suggestion in search results."""
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL slug")
    image_url: Optional[str] = Field(None, description="Category image")
    product_count: int = Field(0, description="Number of products in category")

    class Config:
        from_attributes = True


class SearchBrandSuggestion(BaseModel):
    """Brand suggestion in search results."""
    id: str = Field(..., description="Brand ID")
    name: str = Field(..., description="Brand name")
    slug: str = Field(..., description="URL slug")
    logo_url: Optional[str] = Field(None, description="Brand logo")

    class Config:
        from_attributes = True


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response with products, categories, and brands."""
    products: List[SearchProductSuggestion] = Field([], description="Product suggestions")
    categories: List[SearchCategorySuggestion] = Field([], description="Category suggestions")
    brands: List[SearchBrandSuggestion] = Field([], description="Brand suggestions")
    query: str = Field(..., description="Original search query")
