"""Public Storefront API endpoints.

These endpoints are accessible without authentication for the D2C website.
"""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import DB
from app.models.company import Company
from app.models.product import Product, ProductImage
from app.models.category import Category
from app.models.brand import Brand

router = APIRouter()


# ==================== Response Schemas ====================

class StorefrontProductImage(BaseModel):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False

    class Config:
        from_attributes = True


class StorefrontProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    sku: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    mrp: float
    selling_price: Optional[float] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    warranty_months: int = 12
    is_featured: bool = False
    is_bestseller: bool = False
    is_new_arrival: bool = False
    images: List[StorefrontProductImage] = []

    class Config:
        from_attributes = True


class StorefrontCategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[str] = None

    class Config:
        from_attributes = True


class StorefrontBrandResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedProductsResponse(BaseModel):
    items: List[StorefrontProductResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== Products Endpoints ====================

@router.get("/products", response_model=PaginatedProductsResponse)
async def list_products(
    db: DB,
    category_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    is_bestseller: Optional[bool] = None,
    is_new_arrival: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="created_at", regex="^(name|mrp|selling_price|created_at)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=12, ge=1, le=100),
):
    """
    List products for the public storefront.
    No authentication required.
    """
    query = (
        select(Product)
        .options(selectinload(Product.images))
        .options(selectinload(Product.category))
        .options(selectinload(Product.brand))
        .where(Product.is_active == True)
    )

    # Apply filters
    if category_id:
        query = query.where(Product.category_id == category_id)
    if brand_id:
        query = query.where(Product.brand_id == brand_id)
    if min_price is not None:
        query = query.where(Product.selling_price >= min_price)
    if max_price is not None:
        query = query.where(Product.selling_price <= max_price)
    if is_featured:
        query = query.where(Product.is_featured == True)
    if is_bestseller:
        query = query.where(Product.is_bestseller == True)
    if is_new_arrival:
        query = query.where(Product.is_new_arrival == True)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.description.ilike(search_term),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = getattr(Product, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    products = result.scalars().all()

    # Transform to response
    items = []
    for p in products:
        images = [
            StorefrontProductImage(
                url=img.url,
                alt_text=img.alt_text,
                is_primary=img.is_primary
            )
            for img in (p.images or [])
        ]
        items.append(StorefrontProductResponse(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            sku=p.sku,
            short_description=p.short_description,
            description=p.description,
            mrp=float(p.mrp) if p.mrp else 0,
            selling_price=float(p.selling_price) if p.selling_price else None,
            category_id=str(p.category_id) if p.category_id else None,
            category_name=p.category.name if p.category else None,
            brand_id=str(p.brand_id) if p.brand_id else None,
            brand_name=p.brand.name if p.brand else None,
            warranty_months=p.warranty_months or 12,
            is_featured=p.is_featured or False,
            is_bestseller=p.is_bestseller or False,
            is_new_arrival=p.is_new_arrival or False,
            images=images,
        ))

    pages = (total + size - 1) // size

    return PaginatedProductsResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/products/{slug}", response_model=StorefrontProductResponse)
async def get_product_by_slug(slug: str, db: DB):
    """
    Get a single product by slug for the public storefront.
    No authentication required.
    """
    query = (
        select(Product)
        .options(selectinload(Product.images))
        .options(selectinload(Product.category))
        .options(selectinload(Product.brand))
        .where(Product.slug == slug, Product.is_active == True)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    images = [
        StorefrontProductImage(
            url=img.url,
            alt_text=img.alt_text,
            is_primary=img.is_primary
        )
        for img in (product.images or [])
    ]

    return StorefrontProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        sku=product.sku,
        short_description=product.short_description,
        description=product.description,
        mrp=float(product.mrp) if product.mrp else 0,
        selling_price=float(product.selling_price) if product.selling_price else None,
        category_id=str(product.category_id) if product.category_id else None,
        category_name=product.category.name if product.category else None,
        brand_id=str(product.brand_id) if product.brand_id else None,
        brand_name=product.brand.name if product.brand else None,
        warranty_months=product.warranty_months or 12,
        is_featured=product.is_featured or False,
        is_bestseller=product.is_bestseller or False,
        is_new_arrival=product.is_new_arrival or False,
        images=images,
    )


# ==================== Categories Endpoint ====================

@router.get("/categories", response_model=List[StorefrontCategoryResponse])
async def list_categories(db: DB):
    """
    List all active categories for the public storefront.
    No authentication required.
    """
    query = (
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    result = await db.execute(query)
    categories = result.scalars().all()

    return [
        StorefrontCategoryResponse(
            id=str(c.id),
            name=c.name,
            slug=c.slug,
            description=c.description,
            image_url=c.image_url,
            parent_id=str(c.parent_id) if c.parent_id else None,
        )
        for c in categories
    ]


# ==================== Brands Endpoint ====================

@router.get("/brands", response_model=List[StorefrontBrandResponse])
async def list_brands(db: DB):
    """
    List all active brands for the public storefront.
    No authentication required.
    """
    query = (
        select(Brand)
        .where(Brand.is_active == True)
        .order_by(Brand.sort_order.asc(), Brand.name.asc())
    )
    result = await db.execute(query)
    brands = result.scalars().all()

    return [
        StorefrontBrandResponse(
            id=str(b.id),
            name=b.name,
            slug=b.slug,
            description=b.description,
            logo_url=b.logo_url,
        )
        for b in brands
    ]


class StorefrontCompanyInfo(BaseModel):
    """Public company info for storefront."""
    name: str
    trade_name: Optional[str] = None
    logo_url: Optional[str] = None
    logo_small_url: Optional[str] = None
    favicon_url: Optional[str] = None
    email: str
    phone: str
    website: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str

    class Config:
        from_attributes = True


@router.get("/company", response_model=StorefrontCompanyInfo)
async def get_storefront_company(db: DB):
    """
    Get public company info for the storefront.
    No authentication required.
    """
    # Get primary company or first active company
    query = (
        select(Company)
        .where(Company.is_primary == True, Company.is_active == True)
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        # Try to get any active company
        query = (
            select(Company)
            .where(Company.is_active == True)
            .order_by(Company.created_at.asc())
        )
        result = await db.execute(query)
        company = result.scalar_one_or_none()

    if not company:
        # Return default company info if none configured
        return StorefrontCompanyInfo(
            name="AQUAPURITE",
            trade_name="AQUAPURITE",
            logo_url=None,
            email="support@aquapurite.com",
            phone="1800-123-4567",
            website="https://aquapurite.com",
            address="123 Industrial Area, Sector 62",
            city="Noida",
            state="Uttar Pradesh",
            pincode="201301"
        )

    return StorefrontCompanyInfo(
        name=company.legal_name,
        trade_name=company.trade_name or company.legal_name,
        logo_url=company.logo_url,
        logo_small_url=company.logo_small_url,
        favicon_url=company.favicon_url,
        email=company.email,
        phone=company.phone,
        website=company.website,
        address=company.address_line1 + (f", {company.address_line2}" if company.address_line2 else ""),
        city=company.city,
        state=company.state,
        pincode=company.pincode
    )
