from typing import Optional
import uuid
import json
from math import ceil

from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.api.deps import DB, CurrentUser, Permissions, require_permissions
from app.services.cache_service import get_cache
from app.models.product import ProductStatus
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductDetailResponse,
    ProductListResponse,
    ProductImageCreate,
    ProductImageResponse,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    CategoryBrief,
    BrandBrief,
)
from app.services.product_service import ProductService
from app.services.costing_service import CostingService
from app.services.product_orchestration_service import ProductOrchestrationService
from app.schemas.product_cost import (
    ProductCostResponse,
    ProductCostBriefResponse,
    CostHistoryResponse,
    CostHistoryEntry,
    ProductCostSummary,
    WeightedAverageCostRequest,
    WeightedAverageCostResponse,
)


router = APIRouter(tags=["Products"])


# ==================== PRODUCT CRUD ====================

@router.get("", response_model=ProductListResponse)
async def list_products(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
    brand_id: Optional[uuid.UUID] = Query(None, description="Filter by brand"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name, SKU, description"),
    is_featured: Optional[bool] = Query(None, description="Filter featured products"),
    is_active: Optional[bool] = Query(True, description="Filter active products"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
):
    """
    Get paginated list of products with filters.
    Public endpoint for catalog browsing.
    """
    service = ProductService(db)
    skip = (page - 1) * size

    products, total = await service.get_products(
        category_id=category_id,
        brand_id=brand_id,
        status=status,
        search=search,
        is_featured=is_featured,
        is_active=is_active,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = []
    for p in products:
        items.append(ProductResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            sku=p.sku,
            model_number=p.model_number,
            # Master Product File fields
            fg_code=p.fg_code,
            model_code=p.model_code,
            item_type=p.item_type,
            short_description=p.short_description,
            description=p.description,
            features=p.features,
            category=CategoryBrief.model_validate(p.category) if p.category else None,
            brand=BrandBrief.model_validate(p.brand) if p.brand else None,
            mrp=p.mrp,
            dealer_price=p.dealer_price,
            discount_percentage=p.discount_percentage,
            hsn_code=p.hsn_code,
            gst_rate=p.gst_rate,
            warranty_months=p.warranty_months,
            extended_warranty_available=p.extended_warranty_available,
            warranty_terms=p.warranty_terms,
            # Physical attributes - weight and dimensions
            dead_weight_kg=p.dead_weight_kg,
            length_cm=p.length_cm,
            width_cm=p.width_cm,
            height_cm=p.height_cm,
            # Computed weight fields from Master Product File
            volumetric_weight_kg=p.volumetric_weight_kg,
            chargeable_weight_kg=p.chargeable_weight_kg,
            status=p.status,
            is_active=p.is_active,
            is_featured=p.is_featured,
            is_bestseller=p.is_bestseller,
            is_new_arrival=p.is_new_arrival,
            sort_order=p.sort_order,
            meta_title=p.meta_title,
            meta_description=p.meta_description,
            meta_keywords=p.meta_keywords,
            images=[{
                "id": img.id,
                "image_url": img.image_url,
                "thumbnail_url": img.thumbnail_url,
                "alt_text": img.alt_text,
                "is_primary": img.is_primary,
                "sort_order": img.sort_order,
            } for img in p.images],
            created_at=p.created_at,
            updated_at=p.updated_at,
            published_at=p.published_at,
        ))

    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1,
    )


@router.get("/stats", dependencies=[Depends(require_permissions("products:view"))])
async def get_product_stats(db: DB):
    """
    Get product statistics.
    Requires: products:view permission
    """
    service = ProductService(db)
    return await service.get_product_stats()


@router.get("/top-selling", dependencies=[Depends(require_permissions("products:view"))])
async def get_top_selling_products(
    db: DB,
    limit: int = Query(5, ge=1, le=20),
):
    """
    Get top selling products for dashboard.
    Requires: products:view permission
    """
    service = ProductService(db)
    products = await service.get_top_selling_products(limit=limit)
    return {"items": products}


# ==================== MODEL CODE CHECK ====================

@router.get("/check-model-code")
async def check_model_code(
    db: DB,
    code: str = Query(..., min_length=1, max_length=5, description="Model code to check"),
    exclude_id: Optional[uuid.UUID] = Query(None, description="Product ID to exclude (for updates)"),
):
    """
    Check if a model code is already in use by another product.
    Returns {available: true} if code is free, {available: false, used_by: <sku>} if taken.
    """
    from sqlalchemy import select
    from app.models.product import Product

    code_upper = code.upper().strip()
    query = select(Product).where(Product.model_code == code_upper)
    if exclude_id:
        query = query.where(Product.id != exclude_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return {"available": False, "used_by": existing.sku, "message": f"Model code '{code_upper}' is already used by product {existing.sku}"}
    return {"available": True, "message": f"Model code '{code_upper}' is available"}


# ==================== SKU GENERATION ====================

@router.get("/next-sku")
async def get_next_sku(
    db: DB,
    brand_id: uuid.UUID = Query(..., description="Brand ID"),
    category_id: uuid.UUID = Query(..., description="Subcategory ID"),
    item_type: str = Query(..., regex="^(FG|SP)$", description="Item type: FG (Finished Goods) or SP (Spare Parts)"),
    model_code: str = Query(..., min_length=1, max_length=5, description="Model name code (1-5 uppercase letters)"),
):
    """
    Generate the next sequential SKU based on brand, category, item type, and model code.

    SKU Format: [BRAND_CODE]-[PARENT_CAT_CODE]-[SUBCAT_CODE]-[ITEM_TYPE]-[MODEL_CODE]-[SEQUENCE]
    Example: AP-WP-RU-FG-ELITZ-001

    The sequence number is determined by counting existing products with the same
    brand, subcategory, item type, and model code combination.
    """
    from sqlalchemy import select, func, and_
    from app.models.brand import Brand
    from app.models.category import Category
    from app.models.product import Product
    import re

    # Validate and uppercase model_code
    model_code = model_code.upper().strip()
    if not model_code.isalpha():
        raise HTTPException(status_code=400, detail="Model code must contain only letters")

    # Get brand with code
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Get subcategory with code and parent
    subcat_result = await db.execute(select(Category).where(Category.id == category_id))
    subcategory = subcat_result.scalar_one_or_none()
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")

    # Get parent category (product line) if exists
    parent_category = None
    if subcategory.parent_id:
        parent_result = await db.execute(select(Category).where(Category.id == subcategory.parent_id))
        parent_category = parent_result.scalar_one_or_none()

    # Generate codes - use code field if available, otherwise derive from slug
    brand_code = brand.code or brand.slug[:2].upper() if brand.slug else "BR"
    parent_code = ""
    if parent_category:
        parent_code = parent_category.code or parent_category.slug[:2].upper() if parent_category.slug else "PL"
    subcat_code = subcategory.code or subcategory.slug[:2].upper() if subcategory.slug else "SC"

    # Build SKU prefix with model code
    # For Spare Parts (SP), omit item_type since product line already indicates SP
    if parent_code:
        if item_type == "SP" and parent_code == "SP":
            # Spare Parts: AP-SP-PR-PURIO-001 (no item type, already implied by product line)
            sku_prefix = f"{brand_code}-{parent_code}-{subcat_code}-{model_code}"
        else:
            # Finished Goods: AP-WP-RU-FG-ELITZ-001 (include item type)
            sku_prefix = f"{brand_code}-{parent_code}-{subcat_code}-{item_type}-{model_code}"
    else:
        sku_prefix = f"{brand_code}-{subcat_code}-{item_type}-{model_code}"

    # Count existing products with this prefix pattern
    # We need to find the highest sequence number for this prefix
    sku_pattern = f"{sku_prefix}-%"

    # Query to find all SKUs starting with this prefix
    result = await db.execute(
        select(Product.sku)
        .where(Product.sku.like(sku_pattern))
        .order_by(Product.sku.desc())
    )
    existing_skus = [r[0] for r in result.fetchall()]

    # Find the highest sequence number
    max_sequence = 0
    sequence_pattern = re.compile(rf"^{re.escape(sku_prefix)}-(\d+)$")

    for sku in existing_skus:
        match = sequence_pattern.match(sku)
        if match:
            seq = int(match.group(1))
            if seq > max_sequence:
                max_sequence = seq

    # Next sequence number
    next_sequence = max_sequence + 1
    next_sku = f"{sku_prefix}-{str(next_sequence).zfill(3)}"

    return {
        "sku": next_sku,
        "sequence": next_sequence,
        "brand_code": brand_code,
        "parent_category_code": parent_code,
        "subcategory_code": subcat_code,
        "item_type": item_type,
        "model_code": model_code,
        "prefix": sku_prefix,
    }


# ==================== PRODUCT COST ENDPOINTS (Static Routes First) ====================

@router.get(
    "/costs/summary",
    response_model=ProductCostSummary,
    dependencies=[Depends(require_permissions("products:view"))]
)
async def get_inventory_valuation_summary(
    db: DB,
    current_user: CurrentUser,
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Filter by warehouse"),
):
    """
    Get inventory valuation summary.

    Shows total inventory value, average stock value per product,
    and counts by valuation method.

    Requires: products:view permission
    """
    costing_service = CostingService(db)
    summary = await costing_service.get_inventory_valuation_summary(warehouse_id=warehouse_id)

    return ProductCostSummary(
        total_products=summary["total_products"],
        total_inventory_value=summary["total_inventory_value"],
        average_stock_value_per_product=summary["average_stock_value_per_product"],
        products_with_cost=summary["products_with_cost"],
        products_without_cost=summary["products_without_cost"],
        weighted_avg_count=summary["weighted_avg_count"],
        fifo_count=summary["fifo_count"],
        specific_id_count=summary["specific_id_count"],
    )


@router.post(
    "/costs/initialize",
    dependencies=[Depends(require_permissions("products:update"))]
)
async def initialize_product_costs(
    db: DB,
    current_user: CurrentUser,
):
    """
    Initialize ProductCost records for all products without one.

    Uses product's static cost_price as initial average_cost.
    Run this once after migration to populate initial cost records.

    Requires: products:update permission
    """
    costing_service = CostingService(db)
    result = await costing_service.initialize_costs_from_products()
    return result


# ==================== PRODUCT DETAIL ENDPOINTS ====================

@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: uuid.UUID,
    db: DB,
):
    """Get a product by ID with all details."""
    service = ProductService(db)
    product = await service.get_product_by_id(product_id, include_all=True)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return _build_product_detail_response(product)


@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: DB,
):
    """Get a product by SKU."""
    service = ProductService(db)
    product = await service.get_product_by_sku(sku)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return _build_product_response(product)


@router.get("/slug/{slug}", response_model=ProductDetailResponse)
async def get_product_by_slug(
    slug: str,
    db: DB,
):
    """Get a product by slug with all details."""
    service = ProductService(db)
    product = await service.get_product_by_slug(slug)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return _build_product_detail_response(product)


@router.post(
    "",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("products:create"))]
)
async def create_product(
    data: ProductCreate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Create a new product.
    Requires: products:create permission
    """
    import logging
    logger = logging.getLogger(__name__)

    # Log full request data for debugging
    logger.info(f"[CREATE_PRODUCT] ========== START ==========")
    logger.info(f"[CREATE_PRODUCT] name={data.name}")
    logger.info(f"[CREATE_PRODUCT] sku={data.sku}")
    logger.info(f"[CREATE_PRODUCT] slug={data.slug}")
    logger.info(f"[CREATE_PRODUCT] category_id={data.category_id}")
    logger.info(f"[CREATE_PRODUCT] brand_id={data.brand_id}")
    logger.info(f"[CREATE_PRODUCT] mrp={data.mrp}, selling_price={data.selling_price}")
    logger.info(f"[CREATE_PRODUCT] item_type={data.item_type}, model_code={data.model_code}")

    service = ProductService(db)

    # Check model_code uniqueness
    if data.model_code:
        from sqlalchemy import select
        from app.models.product import Product as ProductModel
        mc_result = await db.execute(
            select(ProductModel).where(ProductModel.model_code == data.model_code.upper())
        )
        mc_existing = mc_result.scalar_one_or_none()
        if mc_existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model code '{data.model_code.upper()}' is already in use by product '{mc_existing.sku}'. Each product must have a unique model code."
            )

    # Check SKU uniqueness
    logger.info(f"[CREATE_PRODUCT] Checking SKU uniqueness: {data.sku}")
    existing = await service.get_product_by_sku(data.sku)
    if existing:
        logger.error(f"[CREATE_PRODUCT] FAILED: SKU '{data.sku}' already exists (existing product id: {existing.id})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{data.sku}' already exists"
        )

    # Check slug uniqueness
    logger.info(f"[CREATE_PRODUCT] Checking slug uniqueness: {data.slug}")
    existing_slug = await service.get_product_by_slug(data.slug)
    if existing_slug:
        logger.error(f"[CREATE_PRODUCT] FAILED: Slug '{data.slug}' already exists (existing product id: {existing_slug.id})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{data.slug}' already exists"
        )

    # Validate category exists
    logger.info(f"[CREATE_PRODUCT] Checking category exists: {data.category_id}")
    category = await service.get_category_by_id(data.category_id)
    if not category:
        logger.error(f"[CREATE_PRODUCT] FAILED: Category not found for id={data.category_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category not found. The selected category (id: {data.category_id}) does not exist in the database."
        )
    logger.info(f"[CREATE_PRODUCT] Category found: {category.name}")

    # Validate brand exists
    logger.info(f"[CREATE_PRODUCT] Checking brand exists: {data.brand_id}")
    brand = await service.get_brand_by_id(data.brand_id)
    if not brand:
        logger.error(f"[CREATE_PRODUCT] FAILED: Brand not found for id={data.brand_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand not found. The selected brand (id: {data.brand_id}) does not exist in the database."
        )
    logger.info(f"[CREATE_PRODUCT] Brand found: {brand.name}")

    # Step 1: Create product (this is the critical step)
    logger.info(f"[CREATE_PRODUCT] Creating product...")
    product = await service.create_product(data)
    logger.info(f"[CREATE_PRODUCT] Product created with id: {product.id}")

    # Step 2: ORCHESTRATION - Non-critical, don't fail if this errors
    try:
        orchestration = ProductOrchestrationService(db)
        orchestration_result = await orchestration.on_product_created(product)
        logger.info(f"[CREATE_PRODUCT] Orchestration complete: {orchestration_result}")
        await db.commit()
    except Exception as e:
        logger.warning(f"[CREATE_PRODUCT] Orchestration failed (non-critical): {type(e).__name__}: {str(e)}")
        # Don't fail the request - product was created successfully

    # Step 3: Cache invalidation - Non-critical
    try:
        cache = get_cache()
        await cache.invalidate_products()
    except Exception as e:
        logger.warning(f"[CREATE_PRODUCT] Cache invalidation failed (non-critical): {str(e)}")

    # Step 4: Re-fetch with all relationships
    try:
        final_product = await service.get_product_by_id(product.id, include_all=True)
        logger.info(f"[CREATE_PRODUCT] ========== SUCCESS ==========")
        return _build_product_detail_response(final_product)
    except Exception as e:
        logger.error(f"[CREATE_PRODUCT] Re-fetch failed: {str(e)}")
        # Return basic product info if re-fetch fails
        return _build_product_detail_response(product)


@router.put(
    "/{product_id}",
    response_model=ProductDetailResponse,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """
    Update a product.
    Requires: products:update permission
    """
    service = ProductService(db)

    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Track old model_code for orchestration
    old_model_code = product.model_code

    # Validate category if changing
    if data.category_id:
        category = await service.get_category_by_id(data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )

    # Validate brand if changing
    if data.brand_id:
        brand = await service.get_brand_by_id(data.brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand not found"
            )

    # Check model_code uniqueness (only if being changed)
    if data.model_code and data.model_code.upper() != (old_model_code or '').upper():
        from sqlalchemy import select
        from app.models.product import Product as ProductModel
        mc_result = await db.execute(
            select(ProductModel).where(
                ProductModel.model_code == data.model_code.upper(),
                ProductModel.id != product_id
            )
        )
        mc_existing = mc_result.scalar_one_or_none()
        if mc_existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model code '{data.model_code.upper()}' is already in use by product '{mc_existing.sku}'."
            )

    updated = await service.update_product(product_id, data)

    # ORCHESTRATION: Update serialization if model_code changed
    orchestration = ProductOrchestrationService(db)
    await orchestration.on_product_updated(updated, old_model_code)

    # Commit orchestration changes
    await db.commit()

    # Invalidate product caches
    cache = get_cache()
    await cache.invalidate_products()

    # Re-fetch with all relationships loaded (refresh strips relationships)
    final_product = await service.get_product_by_id(product_id, include_all=True)
    return _build_product_detail_response(final_product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("products:delete"))]
)
async def delete_product(
    product_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """
    Delete (deactivate) a product.
    Requires: products:delete permission
    """
    service = ProductService(db)

    success = await service.delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Invalidate product caches
    cache = get_cache()
    await cache.invalidate_products()


# ==================== PRODUCT IMAGES ====================

@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def add_product_image(
    product_id: uuid.UUID,
    data: ProductImageCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Add an image to a product."""
    service = ProductService(db)

    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    image = await service.add_product_image(product_id, data)
    return ProductImageResponse.model_validate(image)


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def delete_product_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete a product image."""
    service = ProductService(db)

    success = await service.delete_product_image(image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )


@router.put(
    "/{product_id}/images/{image_id}/primary",
    dependencies=[Depends(require_permissions("products:update"))]
)
async def set_primary_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Set an image as primary."""
    service = ProductService(db)

    await service.set_primary_image(product_id, image_id)
    return {"message": "Primary image updated"}


# ==================== PRODUCT VARIANTS ====================

@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def add_product_variant(
    product_id: uuid.UUID,
    data: ProductVariantCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Add a variant to a product."""
    service = ProductService(db)

    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    variant = await service.add_product_variant(product_id, data)
    return ProductVariantResponse.model_validate(variant)


@router.put(
    "/{product_id}/variants/{variant_id}",
    response_model=ProductVariantResponse,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def update_product_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    data: ProductVariantUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update a product variant."""
    service = ProductService(db)

    variant = await service.update_product_variant(variant_id, data)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )

    return ProductVariantResponse.model_validate(variant)


@router.delete(
    "/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def delete_product_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete a product variant."""
    service = ProductService(db)

    success = await service.delete_product_variant(variant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )


# ==================== HELPER FUNCTIONS ====================

def _build_product_response(p) -> ProductResponse:
    """Build ProductResponse from Product model."""
    return ProductResponse(
        id=p.id,
        name=p.name,
        slug=p.slug,
        sku=p.sku,
        model_number=p.model_number,
        # Master Product File fields
        fg_code=p.fg_code,
        model_code=p.model_code,
        item_type=p.item_type,
        short_description=p.short_description,
        description=p.description,
        features=p.features,
        category=CategoryBrief.model_validate(p.category) if p.category else None,
        brand=BrandBrief.model_validate(p.brand) if p.brand else None,
        mrp=p.mrp,
        dealer_price=p.dealer_price,
        discount_percentage=p.discount_percentage,
        hsn_code=p.hsn_code,
        gst_rate=p.gst_rate,
        warranty_months=p.warranty_months,
        extended_warranty_available=p.extended_warranty_available,
        warranty_terms=p.warranty_terms,
        # Weight fields
        dead_weight_kg=p.dead_weight_kg,
        length_cm=p.length_cm,
        width_cm=p.width_cm,
        height_cm=p.height_cm,
        volumetric_weight_kg=p.volumetric_weight_kg,
        chargeable_weight_kg=p.chargeable_weight_kg,
        status=p.status,
        is_active=p.is_active,
        is_featured=p.is_featured,
        is_bestseller=p.is_bestseller,
        is_new_arrival=p.is_new_arrival,
        sort_order=p.sort_order,
        meta_title=p.meta_title,
        meta_description=p.meta_description,
        meta_keywords=p.meta_keywords,
        images=[ProductImageResponse.model_validate(img) for img in p.images],
        created_at=p.created_at,
        updated_at=p.updated_at,
        published_at=p.published_at,
    )


def _build_product_detail_response(p) -> ProductDetailResponse:
    """Build ProductDetailResponse from Product model."""
    return ProductDetailResponse(
        id=p.id,
        name=p.name,
        slug=p.slug,
        sku=p.sku,
        model_number=p.model_number,
        # Master Product File fields
        fg_code=p.fg_code,
        model_code=p.model_code,
        item_type=p.item_type,
        short_description=p.short_description,
        description=p.description,
        features=p.features,
        category=CategoryBrief.model_validate(p.category) if p.category else None,
        brand=BrandBrief.model_validate(p.brand) if p.brand else None,
        mrp=p.mrp,
        dealer_price=p.dealer_price,
        discount_percentage=p.discount_percentage,
        hsn_code=p.hsn_code,
        gst_rate=p.gst_rate,
        warranty_months=p.warranty_months,
        extended_warranty_available=p.extended_warranty_available,
        warranty_terms=p.warranty_terms,
        # Weight fields
        dead_weight_kg=p.dead_weight_kg,
        length_cm=p.length_cm,
        width_cm=p.width_cm,
        height_cm=p.height_cm,
        volumetric_weight_kg=p.volumetric_weight_kg,
        chargeable_weight_kg=p.chargeable_weight_kg,
        status=p.status,
        is_active=p.is_active,
        is_featured=p.is_featured,
        is_bestseller=p.is_bestseller,
        is_new_arrival=p.is_new_arrival,
        sort_order=p.sort_order,
        meta_title=p.meta_title,
        meta_description=p.meta_description,
        meta_keywords=p.meta_keywords,
        images=[ProductImageResponse.model_validate(img) for img in p.images],
        specifications=[{
            "id": spec.id,
            "group_name": spec.group_name,
            "key": spec.key,
            "value": spec.value,
            "sort_order": spec.sort_order,
        } for spec in p.specifications],
        variants=[ProductVariantResponse.model_validate(v) for v in p.variants],
        documents=[{
            "id": doc.id,
            "title": doc.title,
            "document_type": doc.document_type,
            "file_url": doc.file_url,
            "file_size_bytes": doc.file_size_bytes,
            "mime_type": doc.mime_type,
            "sort_order": doc.sort_order,
            "created_at": doc.created_at,
        } for doc in p.documents],
        # Handle extra_data being stored as JSON string in some records
        extra_data=json.loads(p.extra_data) if isinstance(p.extra_data, str) else p.extra_data,
        created_at=p.created_at,
        updated_at=p.updated_at,
        published_at=p.published_at,
    )


# ==================== PRODUCT COSTING (COGS) ====================

@router.get(
    "/{product_id}/cost",
    response_model=ProductCostResponse,
    dependencies=[Depends(require_permissions("products:view"))]
)
async def get_product_cost(
    product_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    variant_id: Optional[uuid.UUID] = Query(None, description="Filter by variant"),
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Filter by warehouse"),
):
    """
    Get current COGS (Cost of Goods Sold) for a product.

    The cost is auto-calculated using Weighted Average Cost method
    from GRN receipts (Purchase Orders).

    Requires: products:view permission
    """
    costing_service = CostingService(db)

    product_cost = await costing_service.get_product_cost(
        product_id=product_id,
        variant_id=variant_id,
        warehouse_id=warehouse_id,
    )

    if not product_cost:
        # Try to create one with initial zero cost
        product_cost = await costing_service.get_or_create_product_cost(
            product_id=product_id,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
        )

    return ProductCostResponse(
        id=product_cost.id,
        product_id=product_cost.product_id,
        variant_id=product_cost.variant_id,
        warehouse_id=product_cost.warehouse_id,
        valuation_method=product_cost.valuation_method,
        average_cost=product_cost.average_cost,
        last_purchase_cost=product_cost.last_purchase_cost,
        standard_cost=product_cost.standard_cost,
        quantity_on_hand=product_cost.quantity_on_hand,
        total_value=product_cost.total_value,
        last_grn_id=product_cost.last_grn_id,
        last_calculated_at=product_cost.last_calculated_at,
        cost_variance=product_cost.cost_variance,
        cost_variance_percentage=product_cost.cost_variance_percentage,
        created_at=product_cost.created_at,
        updated_at=product_cost.updated_at,
    )


@router.get(
    "/{product_id}/cost-history",
    dependencies=[Depends(require_permissions("products:view"))]
)
async def get_product_cost_history(
    product_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    variant_id: Optional[uuid.UUID] = Query(None),
    warehouse_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get cost history for a product (GRN receipt history).

    Shows all cost movements from GRN acceptances,
    including running average after each receipt.

    Requires: products:view permission
    """
    costing_service = CostingService(db)

    history = await costing_service.get_cost_history(
        product_id=product_id,
        variant_id=variant_id,
        warehouse_id=warehouse_id,
        limit=limit,
    )

    return history


@router.post(
    "/{product_id}/cost/calculate-preview",
    response_model=WeightedAverageCostResponse,
    dependencies=[Depends(require_permissions("products:update"))]
)
async def preview_cost_calculation(
    product_id: uuid.UUID,
    data: WeightedAverageCostRequest,
    db: DB,
    current_user: CurrentUser,
):
    """
    Preview weighted average cost calculation without updating.

    Use this to see what the new average cost would be
    if a GRN with given quantity and price is accepted.

    Formula:
    New Avg = (Current Stock Value + New Purchase Value) / (Current Qty + New Qty)

    Requires: products:update permission
    """
    costing_service = CostingService(db)

    result = await costing_service.calculate_weighted_average(
        product_id=product_id,
        new_qty=data.new_quantity,
        new_unit_cost=data.new_unit_cost,
        variant_id=data.variant_id,
        warehouse_id=data.warehouse_id,
    )

    return WeightedAverageCostResponse(**result)


@router.put(
    "/{product_id}/cost/standard-cost",
    dependencies=[Depends(require_permissions("products:update"))]
)
async def set_standard_cost(
    product_id: uuid.UUID,
    standard_cost: float,
    db: DB,
    current_user: CurrentUser,
    variant_id: Optional[uuid.UUID] = Query(None),
    warehouse_id: Optional[uuid.UUID] = Query(None),
):
    """
    Set standard (budgeted) cost for variance analysis.

    The standard cost is compared against the actual average cost
    to show cost variance in reports.

    Requires: products:update permission
    """
    from decimal import Decimal

    costing_service = CostingService(db)

    product_cost = await costing_service.get_or_create_product_cost(
        product_id=product_id,
        variant_id=variant_id,
        warehouse_id=warehouse_id,
    )

    product_cost.standard_cost = Decimal(str(standard_cost))
    await db.commit()

    return {
        "message": "Standard cost updated",
        "product_id": str(product_id),
        "standard_cost": float(product_cost.standard_cost),
        "average_cost": float(product_cost.average_cost),
        "variance": float(product_cost.cost_variance) if product_cost.cost_variance else None,
        "variance_percentage": product_cost.cost_variance_percentage,
    }


# ==================== SKU MIGRATION ====================

@router.post(
    "/migrate-sku",
    dependencies=[Depends(require_permissions("products:update"))]
)
async def migrate_sku_format(
    db: DB,
    current_user: CurrentUser,
    dry_run: bool = Query(True, description="Preview changes without applying"),
):
    """
    Migrate product SKUs from old format to new standardized format.

    Old format examples:
    - WPRAOPT001 (FG)
    - SPECPOC001 (SP)

    New format:
    - FG: AP-WP-RU-FG-OPT-001 (Brand-ProductLine-SubCat-ItemType-Model-Seq)
    - SP: AP-SP-EC-POC-001 (Brand-ProductLine-SubCat-Model-Seq)

    Requires: products:update permission
    """
    from sqlalchemy import text
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[SKU_MIGRATION] Starting migration (dry_run={dry_run})")

    # Get category hierarchy
    cat_result = await db.execute(text('''
        SELECT
            c.id as cat_id,
            c.code as cat_code,
            c.name as cat_name,
            p.id as parent_id,
            p.code as parent_code,
            p.name as parent_name
        FROM categories c
        LEFT JOIN categories p ON c.parent_id = p.id
    '''))

    category_hierarchy = {}
    for row in cat_result.fetchall():
        cat_id = str(row[0])
        cat_code = row[1] or 'XX'
        parent_code = row[4] or cat_code
        category_hierarchy[cat_id] = {
            'cat_code': cat_code,
            'parent_code': parent_code,
        }

    # Get brand codes
    brand_result = await db.execute(text('SELECT id, code FROM brands'))
    brand_codes = {str(row[0]): row[1] or 'XX' for row in brand_result.fetchall()}

    # Get products to migrate (those NOT in new format)
    products_result = await db.execute(text('''
        SELECT
            p.id,
            p.sku,
            p.name,
            p.model_code,
            p.item_type,
            p.category_id,
            p.brand_id
        FROM products p
        WHERE p.sku NOT LIKE 'AP-%-%-%-%-___'
          AND p.sku NOT LIKE 'AP-%-%-%-___'
        ORDER BY p.created_at
    '''))
    products = products_result.fetchall()

    if not products:
        return {
            "message": "No products need migration. All SKUs are already in new format.",
            "migrated_count": 0,
            "dry_run": dry_run,
            "migrations": []
        }

    # Track SKU counters for sequence numbers
    sku_counters = {}
    migration_report = []

    for product in products:
        product_id = product[0]
        old_sku = product[1]
        product_name = product[2]
        model_code = product[3] or 'XXX'
        item_type = product[4] or 'FG'
        category_id = str(product[5])
        brand_id = str(product[6])

        # Get brand code
        brand_code = brand_codes.get(brand_id, 'XX')

        # Get category hierarchy
        cat_info = category_hierarchy.get(category_id, {})
        parent_code = cat_info.get('parent_code', 'XX')
        subcat_code = cat_info.get('cat_code', 'XX')

        # Ensure model_code is exactly 3 characters (uppercase)
        model_code = model_code[:3].upper()

        # Build SKU prefix
        if parent_code == 'SP' or item_type == 'SP':
            # Spare Parts: No item_type in SKU
            sku_prefix = f"{brand_code}-{parent_code}-{subcat_code}-{model_code}"
        else:
            # Finished Goods: Include item_type
            sku_prefix = f"{brand_code}-{parent_code}-{subcat_code}-{item_type}-{model_code}"

        # Get next sequence number for this prefix
        if sku_prefix not in sku_counters:
            sku_counters[sku_prefix] = 0
        sku_counters[sku_prefix] += 1
        seq = sku_counters[sku_prefix]

        new_sku = f"{sku_prefix}-{str(seq).zfill(3)}"

        migration_report.append({
            'product_id': str(product_id),
            'old_sku': old_sku,
            'new_sku': new_sku,
            'product_name': product_name
        })

        if not dry_run:
            try:
                # Convert product_id to string for SQL parameter
                pid_str = str(product_id)

                # Update product SKU
                await db.execute(text(
                    "UPDATE products SET sku = :new_sku, updated_at = NOW() WHERE id = CAST(:product_id AS UUID)"
                ), {'new_sku': new_sku, 'product_id': pid_str})

                # Update model_code_references (product_id is UUID after schema fix)
                await db.execute(text(
                    "UPDATE model_code_references SET product_sku = :new_sku, updated_at = NOW() WHERE product_id = CAST(:product_id AS UUID)"
                ), {'new_sku': new_sku, 'product_id': pid_str})

                # Update product_serial_sequences (product_id is UUID after schema fix)
                await db.execute(text(
                    "UPDATE product_serial_sequences SET product_sku = :new_sku, updated_at = NOW() WHERE product_id = CAST(:product_id AS UUID)"
                ), {'new_sku': new_sku, 'product_id': pid_str})

                logger.info(f"[SKU_MIGRATION] Updated: {old_sku} -> {new_sku}")
            except Exception as e:
                logger.error(f"[SKU_MIGRATION] Failed to update {old_sku}: {str(e)}")
                raise

    if not dry_run:
        await db.commit()
        logger.info(f"[SKU_MIGRATION] Migration complete! {len(products)} products updated.")

    return {
        "message": f"{'DRY RUN - ' if dry_run else ''}Migration {'preview' if dry_run else 'complete'}",
        "migrated_count": len(products),
        "dry_run": dry_run,
        "sku_prefix_counts": sku_counters,
        "migrations": migration_report
    }
