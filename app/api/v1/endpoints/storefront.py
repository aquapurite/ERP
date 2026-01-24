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
from app.models.inventory import InventorySummary
from app.models.channel import ChannelInventory, SalesChannel
from app.services.channel_inventory_service import ChannelInventoryService
from app.schemas.storefront import (
    StorefrontProductImage,
    StorefrontProductVariant,
    StorefrontProductSpecification,
    StorefrontProductDocument,
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
from app.schemas.serviceability import (
    ServiceabilityCheckRequest,
    ServiceabilityCheckResponse,
)
from app.services.cache_service import get_cache
from app.services.serviceability_service import ServiceabilityService

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
        # Get child category IDs to include products from all subcategories
        child_categories_query = (
            select(Category.id)
            .where(Category.parent_id == category_id)
            .where(Category.is_active == True)
        )
        child_categories_result = await db.execute(child_categories_query)
        child_category_ids = [str(row[0]) for row in child_categories_result.fetchall()]

        # Include the parent category and all its children
        all_category_ids = [category_id] + child_category_ids
        query = query.where(Product.category_id.in_(all_category_ids))
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

    # Get stock information for all products from D2C channel inventory
    product_ids = [p.id for p in products]

    # Try to get D2C channel first for channel-specific inventory
    d2c_channel_result = await db.execute(
        select(SalesChannel).where(
            or_(
                SalesChannel.code == "D2C",
                SalesChannel.channel_type == "D2C",
                SalesChannel.channel_type == "D2C_WEBSITE",
            ),
            SalesChannel.status == "ACTIVE",
        ).order_by(SalesChannel.created_at)
    )
    d2c_channel = d2c_channel_result.scalars().first()

    stock_map = {}

    if d2c_channel and getattr(settings, 'CHANNEL_INVENTORY_ENABLED', True):
        # Use channel-specific inventory (new behavior)
        # Available = allocated - buffer - reserved
        channel_stock_query = (
            select(
                ChannelInventory.product_id,
                func.sum(
                    func.greatest(
                        0,
                        func.coalesce(ChannelInventory.allocated_quantity, 0) -
                        func.coalesce(ChannelInventory.buffer_quantity, 0) -
                        func.coalesce(ChannelInventory.reserved_quantity, 0)
                    )
                ).label('total_available')
            )
            .where(
                ChannelInventory.channel_id == d2c_channel.id,
                ChannelInventory.product_id.in_(product_ids),
                ChannelInventory.is_active == True,
            )
            .group_by(ChannelInventory.product_id)
        )
        channel_result = await db.execute(channel_stock_query)
        stock_map = {row.product_id: row.total_available or 0 for row in channel_result.all()}

        # Fallback: For products NOT in channel inventory, use shared pool (InventorySummary)
        # This enables gradual migration - products without channel allocation use shared pool
        products_with_channel_inv = set(stock_map.keys())
        products_without_channel_inv = [pid for pid in product_ids if pid not in products_with_channel_inv]

        if products_without_channel_inv:
            fallback_query = (
                select(
                    InventorySummary.product_id,
                    func.sum(InventorySummary.available_quantity).label('total_available')
                )
                .where(InventorySummary.product_id.in_(products_without_channel_inv))
                .group_by(InventorySummary.product_id)
            )
            fallback_result = await db.execute(fallback_query)
            for row in fallback_result.all():
                stock_map[row.product_id] = row.total_available or 0
    else:
        # Fallback to legacy behavior (shared pool)
        stock_query = (
            select(
                InventorySummary.product_id,
                func.sum(InventorySummary.available_quantity).label('total_available')
            )
            .where(InventorySummary.product_id.in_(product_ids))
            .group_by(InventorySummary.product_id)
        )
        stock_result = await db.execute(stock_query)
        stock_map = {row.product_id: row.total_available or 0 for row in stock_result.all()}

    # Transform to response
    items = []
    for p in products:
        images = [
            StorefrontProductImage(
                id=str(img.id),
                image_url=img.image_url,
                thumbnail_url=img.thumbnail_url,
                alt_text=img.alt_text,
                is_primary=img.is_primary,
                sort_order=img.sort_order or 0,
            )
            for img in (p.images or [])
        ]
        # Get stock quantity from pre-fetched map
        stock_qty = stock_map.get(p.id, 0)
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
            in_stock=stock_qty > 0,
            stock_quantity=stock_qty,
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
        .options(selectinload(Product.variants))
        .options(selectinload(Product.specifications))
        .options(selectinload(Product.documents))
        .where(Product.slug == slug, Product.is_active == True)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    images = [
        StorefrontProductImage(
            id=str(img.id),
            image_url=img.image_url,
            thumbnail_url=img.thumbnail_url,
            alt_text=img.alt_text,
            is_primary=img.is_primary,
            sort_order=img.sort_order or 0,
        )
        for img in (product.images or [])
    ]

    # Build variants list
    variants = [
        StorefrontProductVariant(
            id=str(v.id),
            name=v.name,
            sku=v.sku,
            attributes=v.attributes,
            mrp=float(v.mrp) if v.mrp else None,
            selling_price=float(v.selling_price) if v.selling_price else None,
            stock_quantity=v.stock_quantity,
            image_url=v.image_url,
            is_active=v.is_active,
        )
        for v in (product.variants or []) if v.is_active
    ]

    # Build specifications list
    specifications = [
        StorefrontProductSpecification(
            id=str(s.id),
            group_name=s.group_name,
            key=s.key,
            value=s.value,
            sort_order=s.sort_order or 0,
        )
        for s in (product.specifications or [])
    ]

    # Build documents list
    documents = [
        StorefrontProductDocument(
            id=str(d.id),
            title=d.title,
            document_type=d.document_type,
            file_url=d.file_url,
            file_size_bytes=d.file_size_bytes,
        )
        for d in (product.documents or [])
    ]

    # Get stock quantity for this product from D2C channel inventory
    d2c_channel_result = await db.execute(
        select(SalesChannel).where(
            or_(
                SalesChannel.code == "D2C",
                SalesChannel.channel_type == "D2C",
                SalesChannel.channel_type == "D2C_WEBSITE",
            ),
            SalesChannel.status == "ACTIVE",
        ).order_by(SalesChannel.created_at)
    )
    d2c_channel = d2c_channel_result.scalars().first()

    stock_qty = 0

    if d2c_channel and getattr(settings, 'CHANNEL_INVENTORY_ENABLED', True):
        # Use channel-specific inventory
        channel_stock_query = (
            select(
                func.sum(
                    func.greatest(
                        0,
                        func.coalesce(ChannelInventory.allocated_quantity, 0) -
                        func.coalesce(ChannelInventory.buffer_quantity, 0) -
                        func.coalesce(ChannelInventory.reserved_quantity, 0)
                    )
                ).label('total_available')
            )
            .where(
                ChannelInventory.channel_id == d2c_channel.id,
                ChannelInventory.product_id == product.id,
                ChannelInventory.is_active == True,
            )
        )
        channel_result = await db.execute(channel_stock_query)
        channel_qty = channel_result.scalar()

        if channel_qty is not None and channel_qty > 0:
            stock_qty = channel_qty
        else:
            # Fallback: Product not in channel inventory, use shared pool
            fallback_query = (
                select(func.sum(InventorySummary.available_quantity).label('total_available'))
                .where(InventorySummary.product_id == product.id)
            )
            fallback_result = await db.execute(fallback_query)
            stock_qty = fallback_result.scalar() or 0
    else:
        # Fallback to legacy behavior
        stock_query = (
            select(func.sum(InventorySummary.available_quantity).label('total_available'))
            .where(InventorySummary.product_id == product.id)
        )
        stock_result = await db.execute(stock_query)
        stock_qty = stock_result.scalar() or 0

    # Calculate discount percentage
    discount_pct = None
    if product.mrp and product.selling_price and product.mrp > 0:
        discount_pct = round(((float(product.mrp) - float(product.selling_price)) / float(product.mrp)) * 100, 1)

    result_data = StorefrontProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        sku=product.sku,
        short_description=product.short_description,
        description=product.description,
        features=product.features,
        mrp=float(product.mrp) if product.mrp else 0,
        selling_price=float(product.selling_price) if product.selling_price else None,
        discount_percentage=discount_pct,
        gst_rate=float(product.gst_rate) if product.gst_rate else None,
        hsn_code=product.hsn_code,
        category_id=str(product.category_id) if product.category_id else None,
        category_name=product.category.name if product.category else None,
        brand_id=str(product.brand_id) if product.brand_id else None,
        brand_name=product.brand.name if product.brand else None,
        warranty_months=product.warranty_months or 12,
        warranty_type=product.warranty_terms,
        is_featured=product.is_featured or False,
        is_bestseller=product.is_bestseller or False,
        is_new_arrival=product.is_new_arrival or False,
        images=images,
        variants=variants,
        specifications=specifications,
        documents=documents,
        in_stock=stock_qty > 0,
        stock_quantity=stock_qty,
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
    List all active categories for the public storefront as a tree structure.
    Includes product count for each category (for mega menu).
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

    # Fetch categories with product count in a single query
    query = (
        select(
            Category,
            func.count(Product.id).filter(Product.is_active == True).label('product_count')
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .where(Category.is_active == True)
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    result = await db.execute(query)
    categories_with_counts = result.all()

    # Build category tree with children
    category_map = {}
    root_categories = []

    # First pass: create all category objects with product counts
    for row in categories_with_counts:
        c = row.Category
        product_count = row.product_count or 0
        cat_response = StorefrontCategoryResponse(
            id=str(c.id),
            name=c.name,
            slug=c.slug,
            description=c.description,
            image_url=c.image_url,
            icon=c.icon,
            parent_id=str(c.parent_id) if c.parent_id else None,
            is_active=c.is_active,
            is_featured=c.is_featured or False,
            product_count=product_count,
            children=[],
        )
        category_map[str(c.id)] = {"obj": cat_response, "parent_id": str(c.parent_id) if c.parent_id else None}

    # Second pass: build tree structure
    for cat_id, cat_data in category_map.items():
        if cat_data["parent_id"] and cat_data["parent_id"] in category_map:
            # Add as child to parent
            parent = category_map[cat_data["parent_id"]]["obj"]
            parent.children.append(cat_data["obj"])
        else:
            # Root category
            root_categories.append(cat_data["obj"])

    result_data = root_categories

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
            is_active=b.is_active,
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
            image_url=primary_image.image_url if primary_image else None,
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


# ==================== Serviceability Endpoint ====================

@router.get("/serviceability/{pincode}", response_model=ServiceabilityCheckResponse)
async def check_serviceability(
    pincode: str,
    db: DB,
    response: Response,
):
    """
    Check if a pincode is serviceable for delivery.
    No authentication required. Cached for 30 minutes.

    Returns serviceability status, COD availability, estimated delivery days,
    and available warehouse/transporter options.
    """
    start_time = time.time()
    cache = get_cache()

    # Validate pincode format (6 digits for India)
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid pincode format. Must be 6 digits."
        )

    # Try to get from cache
    cache_key = f"serviceability:d2c:{pincode}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return ServiceabilityCheckResponse(**cached_result)

    # Check serviceability
    service = ServiceabilityService(db)
    request = ServiceabilityCheckRequest(
        pincode=pincode,
        channel_code="D2C"
    )

    result = await service.check_serviceability(request)

    # Cache the result (30 minutes)
    await cache.set(cache_key, result.model_dump(), ttl=1800)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result


# ==================== CMS Content Endpoints ====================

from app.models.cms import (
    CMSBanner, CMSUsp, CMSTestimonial, CMSAnnouncement, CMSPage,
    CMSSiteSetting, CMSMenuItem, CMSFeatureBar, CMSMegaMenuItem
)
from app.schemas.cms import (
    StorefrontBannerResponse,
    StorefrontUspResponse,
    StorefrontTestimonialResponse,
    StorefrontAnnouncementResponse,
    StorefrontPageResponse,
    StorefrontSettingsResponse,
    StorefrontMenuItemResponse,
    StorefrontFeatureBarResponse,
    StorefrontMegaMenuItemResponse,
    StorefrontSubcategoryResponse,
)


@router.get("/banners", response_model=List[StorefrontBannerResponse])
async def get_banners(db: DB, response: Response):
    """
    Get active hero banners for the storefront.
    Respects scheduling (starts_at, ends_at).
    No authentication required. Cached for 5 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = "cms:banners:active"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontBannerResponse(**b) for b in cached_result]

    now = func.now()
    query = (
        select(CMSBanner)
        .where(
            CMSBanner.is_active == True,
            or_(CMSBanner.starts_at.is_(None), CMSBanner.starts_at <= now),
            or_(CMSBanner.ends_at.is_(None), CMSBanner.ends_at >= now),
        )
        .order_by(CMSBanner.sort_order.asc())
    )

    result = await db.execute(query)
    banners = result.scalars().all()

    result_data = [
        StorefrontBannerResponse(
            id=str(b.id),
            title=b.title,
            subtitle=b.subtitle,
            image_url=b.image_url,
            mobile_image_url=b.mobile_image_url,
            cta_text=b.cta_text,
            cta_link=b.cta_link,
            text_position=b.text_position,
            text_color=b.text_color,
        )
        for b in banners
    ]

    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=300)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/usps", response_model=List[StorefrontUspResponse])
async def get_usps(db: DB, response: Response):
    """
    Get active USPs/features for the storefront.
    No authentication required. Cached for 10 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = "cms:usps:active"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontUspResponse(**u) for u in cached_result]

    query = (
        select(CMSUsp)
        .where(CMSUsp.is_active == True)
        .order_by(CMSUsp.sort_order.asc())
    )

    result = await db.execute(query)
    usps = result.scalars().all()

    result_data = [
        StorefrontUspResponse(
            id=str(u.id),
            title=u.title,
            description=u.description,
            icon=u.icon,
            icon_color=u.icon_color,
            link_url=u.link_url,
            link_text=u.link_text,
        )
        for u in usps
    ]

    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=600)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/testimonials", response_model=List[StorefrontTestimonialResponse])
async def get_testimonials(
    db: DB,
    response: Response,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get active testimonials for the storefront.
    Featured testimonials appear first.
    No authentication required. Cached for 10 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = f"cms:testimonials:active:{limit}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontTestimonialResponse(**t) for t in cached_result]

    query = (
        select(CMSTestimonial)
        .where(CMSTestimonial.is_active == True)
        .order_by(
            CMSTestimonial.is_featured.desc(),
            CMSTestimonial.sort_order.asc()
        )
        .limit(limit)
    )

    result = await db.execute(query)
    testimonials = result.scalars().all()

    result_data = [
        StorefrontTestimonialResponse(
            id=str(t.id),
            customer_name=t.customer_name,
            customer_location=t.customer_location,
            customer_avatar_url=t.customer_avatar_url,
            customer_designation=t.customer_designation,
            rating=t.rating,
            content=t.content,
            title=t.title,
            product_name=t.product_name,
        )
        for t in testimonials
    ]

    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=600)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/announcements/active", response_model=Optional[StorefrontAnnouncementResponse])
async def get_active_announcement(db: DB, response: Response):
    """
    Get the current active announcement for the header bar.
    Returns the first active, scheduled announcement.
    No authentication required. Cached for 2 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = "cms:announcement:active"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        if cached_result == "none":
            return None
        return StorefrontAnnouncementResponse(**cached_result)

    now = func.now()
    query = (
        select(CMSAnnouncement)
        .where(
            CMSAnnouncement.is_active == True,
            or_(CMSAnnouncement.starts_at.is_(None), CMSAnnouncement.starts_at <= now),
            or_(CMSAnnouncement.ends_at.is_(None), CMSAnnouncement.ends_at >= now),
        )
        .order_by(CMSAnnouncement.sort_order.asc())
        .limit(1)
    )

    result = await db.execute(query)
    announcement = result.scalar_one_or_none()

    if not announcement:
        await cache.set(cache_key, "none", ttl=120)
        response.headers["X-Cache"] = "MISS"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return None

    result_data = StorefrontAnnouncementResponse(
        id=str(announcement.id),
        text=announcement.text,
        link_url=announcement.link_url,
        link_text=announcement.link_text,
        announcement_type=announcement.announcement_type,
        background_color=announcement.background_color,
        text_color=announcement.text_color,
        is_dismissible=announcement.is_dismissible,
    )

    await cache.set(cache_key, result_data.model_dump(), ttl=120)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/pages/{slug}", response_model=StorefrontPageResponse)
async def get_page_by_slug(slug: str, db: DB, response: Response):
    """
    Get a published page by slug.
    No authentication required. Cached for 5 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = f"cms:page:{slug}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return StorefrontPageResponse(**cached_result)

    query = (
        select(CMSPage)
        .where(
            CMSPage.slug == slug,
            CMSPage.status == "PUBLISHED",
        )
    )

    result = await db.execute(query)
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    result_data = StorefrontPageResponse(
        id=str(page.id),
        title=page.title,
        slug=page.slug,
        content=page.content,
        excerpt=page.excerpt,
        meta_title=page.meta_title,
        meta_description=page.meta_description,
        og_image_url=page.og_image_url,
        template=page.template,
        published_at=page.published_at,
    )

    await cache.set(cache_key, result_data.model_dump(), ttl=300)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/footer-pages", response_model=List[dict])
async def get_footer_pages(db: DB, response: Response):
    """
    Get list of published pages that should appear in the footer.
    No authentication required. Cached for 30 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = "cms:pages:footer"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return cached_result

    query = (
        select(CMSPage)
        .where(
            CMSPage.status == "PUBLISHED",
            CMSPage.show_in_footer == True,
        )
        .order_by(CMSPage.sort_order.asc())
    )

    result = await db.execute(query)
    pages = result.scalars().all()

    result_data = [
        {"title": p.title, "slug": p.slug}
        for p in pages
    ]

    await cache.set(cache_key, result_data, ttl=1800)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/settings", response_model=dict)
async def get_site_settings(
    db: DB,
    response: Response,
    group: Optional[str] = Query(default=None, description="Filter by setting group"),
):
    """
    Get public site settings (social media links, contact info, etc.).
    No authentication required. Cached for 30 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = f"cms:settings:{group or 'all'}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return cached_result

    query = select(CMSSiteSetting).order_by(CMSSiteSetting.sort_order.asc())
    if group:
        query = query.where(CMSSiteSetting.setting_group == group)

    result = await db.execute(query)
    settings = result.scalars().all()

    # Return as key-value pairs
    result_data = {s.setting_key: s.setting_value for s in settings}

    await cache.set(cache_key, result_data, ttl=1800)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/menu-items", response_model=List[StorefrontMenuItemResponse])
async def get_menu_items(
    db: DB,
    response: Response,
    location: Optional[str] = Query(default=None, description="Filter by location (header, footer_quick, footer_service)"),
):
    """
    Get navigation menu items for header and footer.
    No authentication required. Cached for 30 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = f"cms:menu:{location or 'all'}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontMenuItemResponse(**m) for m in cached_result]

    query = (
        select(CMSMenuItem)
        .where(
            CMSMenuItem.is_active == True,
            CMSMenuItem.parent_id.is_(None),  # Only top-level items
        )
        .order_by(CMSMenuItem.sort_order.asc())
    )

    if location:
        query = query.where(CMSMenuItem.menu_location == location)

    result = await db.execute(query)
    menu_items = result.scalars().all()

    # Get all child items
    parent_ids = [str(m.id) for m in menu_items]
    children_query = (
        select(CMSMenuItem)
        .where(
            CMSMenuItem.is_active == True,
            CMSMenuItem.parent_id.in_([m.id for m in menu_items]) if menu_items else False,
        )
        .order_by(CMSMenuItem.sort_order.asc())
    )

    children_result = await db.execute(children_query)
    children = children_result.scalars().all()

    # Group children by parent
    children_map = {}
    for child in children:
        parent_id = str(child.parent_id)
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(StorefrontMenuItemResponse(
            id=str(child.id),
            menu_location=child.menu_location,
            title=child.title,
            url=child.url,
            icon=child.icon,
            target=child.target,
            children=[],
        ))

    result_data = [
        StorefrontMenuItemResponse(
            id=str(m.id),
            menu_location=m.menu_location,
            title=m.title,
            url=m.url,
            icon=m.icon,
            target=m.target,
            children=children_map.get(str(m.id), []),
        )
        for m in menu_items
    ]

    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=1800)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


@router.get("/feature-bars", response_model=List[StorefrontFeatureBarResponse])
async def get_feature_bars(db: DB, response: Response):
    """
    Get feature bar items (Free Shipping, Secure Payment, etc.) for footer.
    No authentication required. Cached for 30 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = "cms:feature-bars:active"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontFeatureBarResponse(**f) for f in cached_result]

    query = (
        select(CMSFeatureBar)
        .where(CMSFeatureBar.is_active == True)
        .order_by(CMSFeatureBar.sort_order.asc())
    )

    result = await db.execute(query)
    feature_bars = result.scalars().all()

    result_data = [
        StorefrontFeatureBarResponse(
            id=str(f.id),
            icon=f.icon,
            title=f.title,
            subtitle=f.subtitle,
        )
        for f in feature_bars
    ]

    await cache.set(cache_key, [r.model_dump() for r in result_data], ttl=1800)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


# ==================== Composite Homepage Endpoint ====================

import asyncio
from pydantic import BaseModel


class HomepageDataResponse(BaseModel):
    """Composite response for homepage - all data in single request."""
    categories: List[StorefrontCategoryResponse]
    featured_products: List[StorefrontProductResponse]
    bestseller_products: List[StorefrontProductResponse]
    new_arrivals: List[StorefrontProductResponse]
    banners: List[StorefrontBannerResponse]
    brands: List[StorefrontBrandResponse]
    usps: List[StorefrontUspResponse]
    testimonials: List[StorefrontTestimonialResponse]


async def _get_featured_products(db, limit: int = 8):
    """Helper to get featured products with stock."""
    query = (
        select(Product)
        .options(selectinload(Product.images))
        .options(selectinload(Product.category))
        .options(selectinload(Product.brand))
        .where(Product.is_active == True, Product.is_featured == True)
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    products = result.scalars().all()

    # Batch get stock
    product_ids = [p.id for p in products]
    if product_ids:
        stock_query = (
            select(
                InventorySummary.product_id,
                func.sum(InventorySummary.available_quantity).label('total_available')
            )
            .where(InventorySummary.product_id.in_(product_ids))
            .group_by(InventorySummary.product_id)
        )
        stock_result = await db.execute(stock_query)
        stock_map = {row.product_id: row.total_available or 0 for row in stock_result.all()}
    else:
        stock_map = {}

    return [
        StorefrontProductResponse(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            sku=p.sku,
            short_description=p.short_description,
            mrp=float(p.mrp) if p.mrp else 0,
            selling_price=float(p.selling_price) if p.selling_price else None,
            category_id=str(p.category_id) if p.category_id else None,
            category_name=p.category.name if p.category else None,
            brand_id=str(p.brand_id) if p.brand_id else None,
            brand_name=p.brand.name if p.brand else None,
            is_featured=True,
            is_bestseller=p.is_bestseller or False,
            is_new_arrival=p.is_new_arrival or False,
            images=[
                StorefrontProductImage(
                    id=str(img.id),
                    image_url=img.image_url,
                    thumbnail_url=img.thumbnail_url,
                    alt_text=img.alt_text,
                    is_primary=img.is_primary,
                    sort_order=img.sort_order or 0,
                )
                for img in (p.images or [])
            ],
            in_stock=stock_map.get(p.id, 0) > 0,
            stock_quantity=stock_map.get(p.id, 0),
        )
        for p in products
    ]


async def _get_bestseller_products(db, limit: int = 8):
    """Helper to get bestseller products with stock."""
    query = (
        select(Product)
        .options(selectinload(Product.images))
        .options(selectinload(Product.category))
        .options(selectinload(Product.brand))
        .where(Product.is_active == True, Product.is_bestseller == True)
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    products = result.scalars().all()

    product_ids = [p.id for p in products]
    if product_ids:
        stock_query = (
            select(
                InventorySummary.product_id,
                func.sum(InventorySummary.available_quantity).label('total_available')
            )
            .where(InventorySummary.product_id.in_(product_ids))
            .group_by(InventorySummary.product_id)
        )
        stock_result = await db.execute(stock_query)
        stock_map = {row.product_id: row.total_available or 0 for row in stock_result.all()}
    else:
        stock_map = {}

    return [
        StorefrontProductResponse(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            sku=p.sku,
            short_description=p.short_description,
            mrp=float(p.mrp) if p.mrp else 0,
            selling_price=float(p.selling_price) if p.selling_price else None,
            category_id=str(p.category_id) if p.category_id else None,
            category_name=p.category.name if p.category else None,
            brand_id=str(p.brand_id) if p.brand_id else None,
            brand_name=p.brand.name if p.brand else None,
            is_featured=p.is_featured or False,
            is_bestseller=True,
            is_new_arrival=p.is_new_arrival or False,
            images=[
                StorefrontProductImage(
                    id=str(img.id),
                    image_url=img.image_url,
                    thumbnail_url=img.thumbnail_url,
                    alt_text=img.alt_text,
                    is_primary=img.is_primary,
                    sort_order=img.sort_order or 0,
                )
                for img in (p.images or [])
            ],
            in_stock=stock_map.get(p.id, 0) > 0,
            stock_quantity=stock_map.get(p.id, 0),
        )
        for p in products
    ]


async def _get_new_arrival_products(db, limit: int = 8):
    """Helper to get new arrival products with stock."""
    query = (
        select(Product)
        .options(selectinload(Product.images))
        .options(selectinload(Product.category))
        .options(selectinload(Product.brand))
        .where(Product.is_active == True, Product.is_new_arrival == True)
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    products = result.scalars().all()

    product_ids = [p.id for p in products]
    if product_ids:
        stock_query = (
            select(
                InventorySummary.product_id,
                func.sum(InventorySummary.available_quantity).label('total_available')
            )
            .where(InventorySummary.product_id.in_(product_ids))
            .group_by(InventorySummary.product_id)
        )
        stock_result = await db.execute(stock_query)
        stock_map = {row.product_id: row.total_available or 0 for row in stock_result.all()}
    else:
        stock_map = {}

    return [
        StorefrontProductResponse(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            sku=p.sku,
            short_description=p.short_description,
            mrp=float(p.mrp) if p.mrp else 0,
            selling_price=float(p.selling_price) if p.selling_price else None,
            category_id=str(p.category_id) if p.category_id else None,
            category_name=p.category.name if p.category else None,
            brand_id=str(p.brand_id) if p.brand_id else None,
            brand_name=p.brand.name if p.brand else None,
            is_featured=p.is_featured or False,
            is_bestseller=p.is_bestseller or False,
            is_new_arrival=True,
            images=[
                StorefrontProductImage(
                    id=str(img.id),
                    image_url=img.image_url,
                    thumbnail_url=img.thumbnail_url,
                    alt_text=img.alt_text,
                    is_primary=img.is_primary,
                    sort_order=img.sort_order or 0,
                )
                for img in (p.images or [])
            ],
            in_stock=stock_map.get(p.id, 0) > 0,
            stock_quantity=stock_map.get(p.id, 0),
        )
        for p in products
    ]


@router.get("/homepage", response_model=HomepageDataResponse)
async def get_homepage_data(db: DB, response: Response):
    """
    Get all data needed for homepage in a single API call.
    Includes: categories, featured products, bestsellers, new arrivals,
    banners, brands, USPs, and testimonials.

    This composite endpoint reduces multiple HTTP requests to just one,
    significantly improving homepage load time.

    No authentication required. Cached for 5 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    # Try to get from cache
    cache_key = "storefront:homepage"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return HomepageDataResponse(**cached_result)

    # Fetch all data in parallel using asyncio.gather
    # Categories
    async def get_categories():
        query = (
            select(
                Category,
                func.count(Product.id).filter(Product.is_active == True).label('product_count')
            )
            .outerjoin(Product, Product.category_id == Category.id)
            .where(Category.is_active == True)
            .group_by(Category.id)
            .order_by(Category.sort_order.asc(), Category.name.asc())
        )
        result = await db.execute(query)
        categories_with_counts = result.all()

        # Build tree
        category_map = {}
        root_categories = []
        for row in categories_with_counts:
            c = row.Category
            product_count = row.product_count or 0
            cat_response = StorefrontCategoryResponse(
                id=str(c.id),
                name=c.name,
                slug=c.slug,
                description=c.description,
                image_url=c.image_url,
                icon=c.icon,
                parent_id=str(c.parent_id) if c.parent_id else None,
                is_active=c.is_active,
                is_featured=c.is_featured or False,
                product_count=product_count,
                children=[],
            )
            category_map[str(c.id)] = {"obj": cat_response, "parent_id": str(c.parent_id) if c.parent_id else None}

        for cat_id, cat_data in category_map.items():
            if cat_data["parent_id"] and cat_data["parent_id"] in category_map:
                parent = category_map[cat_data["parent_id"]]["obj"]
                parent.children.append(cat_data["obj"])
            else:
                root_categories.append(cat_data["obj"])

        return root_categories

    # Brands
    async def get_brands():
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
                is_active=b.is_active,
            )
            for b in brands
        ]

    # Banners
    async def get_banners():
        now = func.now()
        query = (
            select(CMSBanner)
            .where(
                CMSBanner.is_active == True,
                or_(CMSBanner.starts_at.is_(None), CMSBanner.starts_at <= now),
                or_(CMSBanner.ends_at.is_(None), CMSBanner.ends_at >= now),
            )
            .order_by(CMSBanner.sort_order.asc())
        )
        result = await db.execute(query)
        banners = result.scalars().all()
        return [
            StorefrontBannerResponse(
                id=str(b.id),
                title=b.title,
                subtitle=b.subtitle,
                image_url=b.image_url,
                mobile_image_url=b.mobile_image_url,
                cta_text=b.cta_text,
                cta_link=b.cta_link,
                text_position=b.text_position,
                text_color=b.text_color,
            )
            for b in banners
        ]

    # USPs
    async def get_usps():
        query = (
            select(CMSUsp)
            .where(CMSUsp.is_active == True)
            .order_by(CMSUsp.sort_order.asc())
        )
        result = await db.execute(query)
        usps = result.scalars().all()
        return [
            StorefrontUspResponse(
                id=str(u.id),
                title=u.title,
                description=u.description,
                icon=u.icon,
                icon_color=u.icon_color,
                link_url=u.link_url,
                link_text=u.link_text,
            )
            for u in usps
        ]

    # Testimonials
    async def get_testimonials():
        query = (
            select(CMSTestimonial)
            .where(CMSTestimonial.is_active == True)
            .order_by(CMSTestimonial.is_featured.desc(), CMSTestimonial.sort_order.asc())
            .limit(6)
        )
        result = await db.execute(query)
        testimonials = result.scalars().all()
        return [
            StorefrontTestimonialResponse(
                id=str(t.id),
                customer_name=t.customer_name,
                customer_location=t.customer_location,
                customer_avatar_url=t.customer_avatar_url,
                customer_designation=t.customer_designation,
                rating=t.rating,
                content=t.content,
                title=t.title,
                product_name=t.product_name,
            )
            for t in testimonials
        ]

    # Execute queries sequentially (SQLAlchemy async sessions don't support concurrent operations)
    # Even though sequential, this is still faster than multiple HTTP requests from frontend
    categories = await get_categories()
    featured_products = await _get_featured_products(db, limit=8)
    bestseller_products = await _get_bestseller_products(db, limit=8)
    new_arrivals = await _get_new_arrival_products(db, limit=8)
    banners = await get_banners()
    brands = await get_brands()
    usps = await get_usps()
    testimonials = await get_testimonials()

    result_data = HomepageDataResponse(
        categories=categories,
        featured_products=featured_products,
        bestseller_products=bestseller_products,
        new_arrivals=new_arrivals,
        banners=banners,
        brands=brands,
        usps=usps,
        testimonials=testimonials,
    )

    # Cache for 5 minutes
    await cache.set(cache_key, result_data.model_dump(), ttl=300)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return result_data


# ==================== Mega Menu Endpoint ====================

@router.get("/mega-menu", response_model=List[StorefrontMegaMenuItemResponse])
async def get_mega_menu(db: DB, response: Response):
    """
    Get CMS-managed mega menu items for storefront navigation.
    Returns active menu items with resolved category data and subcategories.

    Unlike the categories endpoint which returns ALL categories,
    this endpoint returns only the curated navigation structure
    defined by admins in the CMS (similar to Eureka Forbes / Atomberg).

    No authentication required. Cached for 10 minutes.
    """
    start_time = time.time()
    cache = get_cache()

    cache_key = "storefront:mega-menu"
    cached_result = await cache.get(cache_key)
    if cached_result:
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return [StorefrontMegaMenuItemResponse(**item) for item in cached_result]

    # Fetch active mega menu items
    query = (
        select(CMSMegaMenuItem)
        .where(CMSMegaMenuItem.is_active == True)
        .order_by(CMSMegaMenuItem.sort_order.asc())
    )
    result = await db.execute(query)
    menu_items = result.scalars().all()

    # Build response with resolved category data
    response_items = []
    for item in menu_items:
        menu_response = StorefrontMegaMenuItemResponse(
            id=str(item.id),
            title=item.title,
            icon=item.icon,
            image_url=item.image_url,
            menu_type=item.menu_type,
            url=item.url,
            target=item.target,
            is_highlighted=item.is_highlighted,
            highlight_text=item.highlight_text,
            category_slug=None,
            subcategories=[],
        )

        # For CATEGORY type, resolve the category and its subcategories
        if item.menu_type == "CATEGORY" and item.category_id:
            # Get the main category
            cat_result = await db.execute(
                select(Category).where(Category.id == item.category_id)
            )
            category = cat_result.scalar_one_or_none()
            if category:
                menu_response.category_slug = category.slug

                # Determine which subcategories to show
                if item.show_subcategories:
                    if item.subcategory_ids and isinstance(item.subcategory_ids, dict):
                        # Show specific subcategories
                        specific_ids = item.subcategory_ids.get("ids", [])
                        if specific_ids:
                            # Get specific subcategories with product counts
                            subcat_query = (
                                select(
                                    Category,
                                    func.count(Product.id).filter(Product.is_active == True).label('product_count')
                                )
                                .outerjoin(Product, Product.category_id == Category.id)
                                .where(
                                    Category.id.in_(specific_ids),
                                    Category.is_active == True
                                )
                                .group_by(Category.id)
                                .order_by(Category.sort_order.asc(), Category.name.asc())
                            )
                            subcat_result = await db.execute(subcat_query)
                            subcategories = subcat_result.all()

                            menu_response.subcategories = [
                                StorefrontSubcategoryResponse(
                                    id=str(sc.Category.id),
                                    name=sc.Category.name,
                                    slug=sc.Category.slug,
                                    image_url=sc.Category.image_url,
                                    product_count=sc.product_count or 0,
                                )
                                for sc in subcategories
                            ]
                    else:
                        # Show all children of this category
                        subcat_query = (
                            select(
                                Category,
                                func.count(Product.id).filter(Product.is_active == True).label('product_count')
                            )
                            .outerjoin(Product, Product.category_id == Category.id)
                            .where(
                                Category.parent_id == item.category_id,
                                Category.is_active == True
                            )
                            .group_by(Category.id)
                            .order_by(Category.sort_order.asc(), Category.name.asc())
                        )
                        subcat_result = await db.execute(subcat_query)
                        subcategories = subcat_result.all()

                        menu_response.subcategories = [
                            StorefrontSubcategoryResponse(
                                id=str(sc.Category.id),
                                name=sc.Category.name,
                                slug=sc.Category.slug,
                                image_url=sc.Category.image_url,
                                product_count=sc.product_count or 0,
                            )
                            for sc in subcategories
                        ]

        response_items.append(menu_response)

    # Cache for 10 minutes (navigation changes infrequently)
    await cache.set(cache_key, [item.model_dump() for item in response_items], ttl=600)

    response.headers["X-Cache"] = "MISS"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    return response_items
