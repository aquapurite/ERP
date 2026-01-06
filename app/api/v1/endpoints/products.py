from typing import Optional
import uuid
from math import ceil

from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.api.deps import DB, CurrentUser, Permissions, require_permissions
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


router = APIRouter(prefix="/products", tags=["Products"])


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
            category=CategoryBrief.model_validate(p.category),
            brand=BrandBrief.model_validate(p.brand),
            mrp=p.mrp,
            selling_price=p.selling_price,
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
    service = ProductService(db)

    # Check SKU uniqueness
    existing = await service.get_product_by_sku(data.sku)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{data.sku}' already exists"
        )

    # Check slug uniqueness
    existing_slug = await service.get_product_by_slug(data.slug)
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{data.slug}' already exists"
        )

    # Validate category exists
    category = await service.get_category_by_id(data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )

    # Validate brand exists
    brand = await service.get_brand_by_id(data.brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand not found"
        )

    product = await service.create_product(data)
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

    updated = await service.update_product(product_id, data)
    return _build_product_detail_response(updated)


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
        category=CategoryBrief.model_validate(p.category),
        brand=BrandBrief.model_validate(p.brand),
        mrp=p.mrp,
        selling_price=p.selling_price,
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
        category=CategoryBrief.model_validate(p.category),
        brand=BrandBrief.model_validate(p.brand),
        mrp=p.mrp,
        selling_price=p.selling_price,
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
        extra_data=p.extra_data,
        created_at=p.created_at,
        updated_at=p.updated_at,
        published_at=p.published_at,
    )
