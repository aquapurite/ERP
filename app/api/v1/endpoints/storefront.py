"""Public Storefront API endpoints.

These endpoints are accessible without authentication for the D2C website.
Includes Redis caching for improved performance.
"""
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.api.deps import DB
from app.config import settings
from app.models.company import Company
from app.models.product import Product, ProductImage
from app.models.category import Category
from app.models.brand import Brand
from app.schemas.storefront import (
    StorefrontProductImage,
    StorefrontProductResponse,
    StorefrontCategoryResponse,
    StorefrontBrandResponse,
    PaginatedProductsResponse,
    StorefrontCompanyInfo,
    SearchProductSuggestion,
    SearchCategorySuggestion,
    SearchBrandSuggestion,
    SearchSuggestionsResponse,
)
from app.services.cache_service import get_cache

router = APIRouter()


# ==================== Products Endpoints ====================

@router.get("/products", response_model=PaginatedProductsResponse)
async def list_products(
    db: DB,
    response: Response,
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
    No authentication required. Results are cached for 5 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    # Build cache key from query params
    cache_params = {
        "category_id": category_id,
        "brand_id": brand_id,
        "min_price": min_price,
        "max_price": max_price,
        "is_featured": is_featured,
        "is_bestseller": is_bestseller,
        "is_new_arrival": is_new_arrival,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
        "size": size,
    }

    # Try to get from cache
    cached_result = await cache.get_product_list(cache_params)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return PaginatedProductsResponse(**cached_result)
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

    result_data = PaginatedProductsResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )

    # Cache the result
    await cache.set_product_list(cache_params, result_data.model_dump())

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/products/{slug}", response_model=StorefrontProductResponse)
async def get_product_by_slug(slug: str, db: DB, response: Response):
    """
    Get a single product by slug for the public storefront.
    No authentication required. Cached for 5 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    # Try to get from cache using slug as key
    cache_key = f"product:slug:{slug}"
    cached_product = await cache.get(cache_key)
    if cached_product:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return StorefrontProductResponse(**cached_product)

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

    result_data = StorefrontProductResponse(
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

    # Cache the result
    await cache.set(cache_key, result_data.model_dump(), ttl=settings.PRODUCT_CACHE_TTL)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


# ==================== Categories Endpoint ====================

@router.get("/categories", response_model=List[StorefrontCategoryResponse])
async def list_categories(db: DB, response: Response):
    """
    List all active categories for the public storefront.
    No authentication required. Cached for 30 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    # Try to get from cache
    cache_key = "categories:all"
    cached_categories = await cache.get(cache_key)
    if cached_categories:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontCategoryResponse(**c) for c in cached_categories]

    query = (
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    result = await db.execute(query)
    categories = result.scalars().all()

    result_data = [
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

    # Cache the result
    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=settings.CATEGORY_CACHE_TTL)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


# ==================== Brands Endpoint ====================

@router.get("/brands", response_model=List[StorefrontBrandResponse])
async def list_brands(db: DB, response: Response):
    """
    List all active brands for the public storefront.
    No authentication required. Cached for 30 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    # Try to get from cache
    cache_key = "brands:all"
    cached_brands = await cache.get(cache_key)
    if cached_brands:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontBrandResponse(**b) for b in cached_brands]

    query = (
        select(Brand)
        .where(Brand.is_active == True)
        .order_by(Brand.sort_order.asc(), Brand.name.asc())
    )
    result = await db.execute(query)
    brands = result.scalars().all()

    result_data = [
        StorefrontBrandResponse(
            id=str(b.id),
            name=b.name,
            slug=b.slug,
            description=b.description,
            logo_url=b.logo_url,
        )
        for b in brands
    ]

    # Cache the result
    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=settings.CATEGORY_CACHE_TTL)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/company", response_model=StorefrontCompanyInfo)
async def get_storefront_company(db: DB, response: Response):
    """
    Get public company info for the storefront.
    No authentication required. Cached for 1 hour.
    """
    start_time = time.time()
    cache = get_cache()

    # Try to get from cache
    cache_key = "company:info"
    cached_company = await cache.get(cache_key)
    if cached_company:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return StorefrontCompanyInfo(**cached_company)

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
        result_data = StorefrontCompanyInfo(
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
    else:
        result_data = StorefrontCompanyInfo(
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

    # Cache the result
    await cache.set(cache_key, result_data.model_dump(), ttl=settings.COMPANY_CACHE_TTL)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


# ==================== Search Suggestions Endpoint ====================

@router.get("/search/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    db: DB,
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(default=6, ge=1, le=10, description="Max results per category"),
):
    """
    Get search suggestions for autocomplete.
    Returns matching products, categories, and brands.
    No authentication required.
    """
    search_term = f"%{q.lower()}%"

    # Search products
    products_query = (
        select(Product)
        .options(selectinload(Product.images))
        .where(
            Product.is_active == True,
            or_(
                func.lower(Product.name).like(search_term),
                func.lower(Product.sku).like(search_term),
            )
        )
        .order_by(Product.is_bestseller.desc(), Product.name.asc())
        .limit(limit)
    )
    products_result = await db.execute(products_query)
    products = products_result.scalars().all()

    product_suggestions = []
    for p in products:
        primary_image = next(
            (img for img in (p.images or []) if img.is_primary),
            (p.images[0] if p.images else None)
        )
        product_suggestions.append(SearchProductSuggestion(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            image_url=primary_image.url if primary_image else None,
            price=float(p.selling_price) if p.selling_price else float(p.mrp),
            mrp=float(p.mrp) if p.mrp else 0,
        ))

    # Search categories
    categories_query = (
        select(Category, func.count(Product.id).label('product_count'))
        .outerjoin(Product, Product.category_id == Category.id)
        .where(
            Category.is_active == True,
            func.lower(Category.name).like(search_term)
        )
        .group_by(Category.id)
        .order_by(func.count(Product.id).desc())
        .limit(limit)
    )
    categories_result = await db.execute(categories_query)
    categories = categories_result.all()

    category_suggestions = [
        SearchCategorySuggestion(
            id=str(c.Category.id),
            name=c.Category.name,
            slug=c.Category.slug,
            image_url=c.Category.image_url,
            product_count=c.product_count or 0,
        )
        for c in categories
    ]

    # Search brands
    brands_query = (
        select(Brand)
        .where(
            Brand.is_active == True,
            func.lower(Brand.name).like(search_term)
        )
        .order_by(Brand.sort_order.asc(), Brand.name.asc())
        .limit(limit)
    )
    brands_result = await db.execute(brands_query)
    brands = brands_result.scalars().all()

    brand_suggestions = [
        SearchBrandSuggestion(
            id=str(b.id),
            name=b.name,
            slug=b.slug,
            logo_url=b.logo_url,
        )
        for b in brands
    ]

    return SearchSuggestionsResponse(
        products=product_suggestions,
        categories=category_suggestions,
        brands=brand_suggestions,
        query=q,
    )
