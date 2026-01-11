"""
Serialization API Endpoints for Barcode Generation in Procurement

Endpoints for:
- Generating serial numbers for Purchase Orders
- Managing supplier codes
- Managing model code references
- Scanning serials during GRN
- Exporting serials as CSV
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, Permissions
from app.models.user import User
from app.models.serialization import (
    SerialSequence,
    POSerial,
    ModelCodeReference,
    SupplierCode,
    SerialStatus,
    ItemType,
)
from app.schemas.serialization import (
    # Supplier Code
    SupplierCodeCreate,
    SupplierCodeUpdate,
    SupplierCodeResponse,
    # Model Code
    ModelCodeCreate,
    ModelCodeUpdate,
    ModelCodeResponse,
    # Serial Generation
    GenerateSerialsRequest,
    GenerateSerialItem,
    GenerateSerialsResponse,
    # PO Serials
    POSerialResponse,
    POSerialsListResponse,
    # Scanning
    ScanSerialRequest,
    ScanSerialResponse,
    BulkScanRequest,
    BulkScanResponse,
    # Lookup
    SerialLookupResponse,
    # Sequence
    SequenceStatusRequest,
    SequenceStatusResponse,
    # Preview
    CodePreviewRequest,
    CodePreviewResponse,
    # FG Code
    FGCodeGenerateRequest,
    FGCodeGenerateResponse,
    # Create Product with Code
    CreateProductWithCodeRequest,
    CreateProductWithCodeResponse,
)
from app.models.product import Product, ProductItemType, ProductStatus
from app.services.serialization import SerializationService

router = APIRouter()


# ==================== Supplier Code Endpoints ====================

@router.get("/suppliers", response_model=List[SupplierCodeResponse])
async def list_supplier_codes(
    active_only: bool = Query(True, description="Only show active suppliers"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all supplier codes"""
    service = SerializationService(db)
    suppliers = await service.get_supplier_codes(active_only=active_only)
    return suppliers


@router.post("/suppliers", response_model=SupplierCodeResponse)
async def create_supplier_code(
    data: SupplierCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new supplier code (2-letter code)"""
    service = SerializationService(db)
    try:
        supplier = await service.create_supplier_code(
            code=data.code,
            name=data.name,
            vendor_id=data.vendor_id,
            description=data.description,
        )
        return supplier
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/suppliers/{code}", response_model=SupplierCodeResponse)
async def get_supplier_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get supplier code by code"""
    result = await db.execute(
        select(SupplierCode).where(SupplierCode.code == code.upper())
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier code {code} not found")
    return supplier


# ==================== Model Code Reference Endpoints ====================

@router.get("/model-codes", response_model=List[ModelCodeResponse])
async def list_model_codes(
    active_only: bool = Query(True, description="Only show active model codes"),
    item_type: Optional[ItemType] = Query(None, description="Filter by item type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all model code references"""
    query = select(ModelCodeReference)
    if active_only:
        query = query.where(ModelCodeReference.is_active == True)
    if item_type:
        query = query.where(ModelCodeReference.item_type == item_type)
    query = query.order_by(ModelCodeReference.fg_code)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/model-codes", response_model=ModelCodeResponse)
async def create_model_code(
    data: ModelCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new model code reference"""
    service = SerializationService(db)
    try:
        model_ref = await service.create_model_code_reference(
            fg_code=data.fg_code,
            model_code=data.model_code,
            item_type=data.item_type,
            product_id=data.product_id,
            product_sku=data.product_sku,
            description=data.description,
        )
        return model_ref
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/model-codes/{fg_code}", response_model=ModelCodeResponse)
async def get_model_code(
    fg_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get model code reference by FG code"""
    result = await db.execute(
        select(ModelCodeReference).where(ModelCodeReference.fg_code == fg_code.upper())
    )
    model_ref = result.scalar_one_or_none()
    if not model_ref:
        raise HTTPException(status_code=404, detail=f"Model code {fg_code} not found")
    return model_ref


# ==================== FG Code Generation ====================

@router.post("/fg-code/generate", response_model=FGCodeGenerateResponse)
async def generate_fg_code(
    data: FGCodeGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a new FG Code for a product.

    Example: WPRAIEL001
    - category_code: WP (Water Purifier)
    - subcategory_code: R (RO)
    - brand_code: A (Aquapurite)
    - model_name: IELITZ -> generates IEL as model code
    """
    service = SerializationService(db)
    result = await service.generate_fg_code(
        category_code=data.category_code,
        subcategory_code=data.subcategory_code,
        brand_code=data.brand_code,
        model_name=data.model_name,
    )
    return result


# ==================== Create Product with Code ====================

@router.post("/create-product", response_model=CreateProductWithCodeResponse)
async def create_product_with_code(
    data: CreateProductWithCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new product with auto-generated codes.

    This is the master product creation flow from the Serialization section.
    The system will:
    1. Generate FG Code / Item Code based on category, subcategory, brand, model
    2. Create the Product in the products table
    3. Create the ModelCodeReference linking the codes
    4. Return all generated codes and product details

    FG Code Format:
    - Finished Goods: WPRAIEL001 (WP=Category, R=Subcategory, A=Brand, IEL=Model, 001=Seq)
    - Spare Parts: SPSDFSD001 (SP=Category, SD=Subcategory, F=Brand, SDF=Model, 001=Seq)
    """
    import uuid
    import re

    # Map item type from schema to product model enum
    product_item_type = (
        ProductItemType.FINISHED_GOODS if data.item_type.value == "FG"
        else ProductItemType.SPARE_PART
    )

    # Generate FG Code / Item Code
    # Format: {category_code}{subcategory_code}{brand_code}{model_code}{sequence}
    base_code = f"{data.category_code}{data.subcategory_code}{data.brand_code}{data.model_code}"

    # Find next available sequence number for this base code
    existing_codes = await db.execute(
        select(ModelCodeReference.fg_code)
        .where(ModelCodeReference.fg_code.like(f"{base_code}%"))
        .order_by(ModelCodeReference.fg_code.desc())
    )
    existing_list = [row[0] for row in existing_codes.fetchall()]

    # Determine next sequence number
    next_seq = 1
    if existing_list:
        # Extract sequence numbers from existing codes
        for code in existing_list:
            match = re.search(r'(\d+)$', code)
            if match:
                seq_num = int(match.group(1))
                if seq_num >= next_seq:
                    next_seq = seq_num + 1

    # Generate the full FG Code with sequence
    fg_code = f"{base_code}{next_seq:03d}"

    # Check if FG code already exists
    existing_fg = await db.execute(
        select(Product).where(Product.fg_code == fg_code)
    )
    if existing_fg.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"FG Code {fg_code} already exists"
        )

    # Check if model code reference already exists
    existing_model_ref = await db.execute(
        select(ModelCodeReference).where(ModelCodeReference.fg_code == fg_code)
    )
    if existing_model_ref.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Model code reference for {fg_code} already exists"
        )

    # Generate slug from name
    slug = re.sub(r'[^a-z0-9]+', '-', data.name.lower()).strip('-')
    # Ensure unique slug
    existing_slug = await db.execute(
        select(Product).where(Product.slug.like(f"{slug}%"))
    )
    slug_count = len(existing_slug.fetchall())
    if slug_count > 0:
        slug = f"{slug}-{slug_count + 1}"

    # Create the Product
    product_id = str(uuid.uuid4())
    product = Product(
        id=product_id,
        name=data.name,
        slug=slug,
        sku=fg_code,  # SKU = FG Code
        fg_code=fg_code,
        model_code=data.model_code,
        model_number=data.model_code,
        item_type=product_item_type,
        description=data.description,
        short_description=data.description[:500] if data.description and len(data.description) > 500 else data.description,
        category_id=data.category_id,
        brand_id=data.brand_id,
        mrp=data.mrp,
        selling_price=data.selling_price or data.mrp,
        cost_price=data.cost_price,
        hsn_code=data.hsn_code,
        gst_rate=data.gst_rate,
        warranty_months=data.warranty_months,
        status=ProductStatus.ACTIVE,
        is_active=True,
    )
    db.add(product)

    # Create the ModelCodeReference
    model_ref_id = str(uuid.uuid4()).replace("-", "")
    model_ref = ModelCodeReference(
        id=model_ref_id,
        product_id=product_id,
        product_sku=fg_code,
        fg_code=fg_code,
        model_code=data.model_code,
        item_type=ItemType.FINISHED_GOODS if data.item_type.value == "FG" else ItemType.SPARE_PART,
        description=data.name,
        is_active=True,
    )
    db.add(model_ref)

    await db.commit()

    # Generate barcode format and example
    service = SerializationService(db)
    year_code = service.get_year_code()
    month_code = service.get_month_code()

    if data.item_type.value == "FG":
        barcode_format = f"AP + Year(2) + Month(1) + {data.model_code}(3) + Serial(8)"
        barcode_example = f"AP{year_code}{month_code}{data.model_code}00000001"
    else:
        barcode_format = f"AP + Supplier(2) + Year(1) + Month(1) + Channel(2) + Serial(8)"
        barcode_example = f"APFS{year_code[1]}{month_code}EC00000001"

    return CreateProductWithCodeResponse(
        success=True,
        message=f"Product created successfully with FG Code: {fg_code}",
        fg_code=fg_code,
        model_code=data.model_code,
        product_sku=fg_code,
        product_id=product_id,
        product_name=data.name,
        item_type=data.item_type,
        model_code_reference_id=model_ref_id,
        barcode_format=barcode_format,
        barcode_example=barcode_example,
    )


# ==================== Barcode Generation ====================

@router.post("/generate", response_model=GenerateSerialsResponse)
async def generate_serials(
    data: GenerateSerialsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate serial numbers/barcodes for a Purchase Order.

    Call this when a PO is approved and sent to vendor.
    The serials are sequential and continue from the last generated serial
    for the same model+supplier+year+month combination.
    """
    service = SerializationService(db)
    try:
        result = await service.generate_serials_for_po(data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preview", response_model=CodePreviewResponse)
async def preview_codes(
    data: CodePreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Preview what barcodes would be generated without saving.

    Useful for checking the next available serial numbers.
    """
    service = SerializationService(db)
    result = await service.preview_codes(
        supplier_code=data.supplier_code,
        model_code=data.model_code,
        quantity=data.quantity,
    )
    return result


# ==================== PO Serials ====================

@router.get("/po/{po_id}", response_model=POSerialsListResponse)
async def get_po_serials(
    po_id: str,
    status: Optional[SerialStatus] = Query(None, description="Filter by status"),
    limit: int = Query(1000, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all serials for a Purchase Order"""
    service = SerializationService(db)

    serials = await service.get_serials_by_po(po_id, status=status, limit=limit, offset=offset)
    counts = await service.get_serials_count_by_po(po_id)

    return POSerialsListResponse(
        po_id=po_id,
        total=counts.get("total", 0),
        by_status=counts,
        serials=[POSerialResponse.model_validate(s) for s in serials],
    )


@router.get("/po/{po_id}/export")
async def export_po_serials(
    po_id: str,
    format: str = Query("csv", pattern="^(csv|txt)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export serials for a PO as CSV/TXT file.

    This can be sent to the vendor for barcode printing.
    """
    service = SerializationService(db)
    serials = await service.get_serials_by_po(po_id, limit=100000)

    if not serials:
        raise HTTPException(status_code=404, detail="No serials found for this PO")

    if format == "csv":
        # Generate CSV
        lines = ["Barcode,Model,Serial,Status"]
        for s in serials:
            lines.append(f"{s.barcode},{s.model_code},{s.serial_number},{s.status.value}")
        content = "\n".join(lines)
        media_type = "text/csv"
        filename = f"serials_{po_id}.csv"
    else:
        # Generate plain text (one barcode per line)
        content = "\n".join([s.barcode for s in serials])
        media_type = "text/plain"
        filename = f"serials_{po_id}.txt"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/po/{po_id}/send-to-vendor")
async def mark_serials_sent_to_vendor(
    po_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all generated serials for a PO as sent to vendor"""
    service = SerializationService(db)
    count = await service.mark_serials_sent_to_vendor(po_id)
    return {"po_id": po_id, "serials_updated": count, "status": "sent_to_vendor"}


# ==================== Serial Scanning (GRN) ====================

@router.post("/scan", response_model=ScanSerialResponse)
async def scan_serial(
    data: ScanSerialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scan and validate a barcode during GRN receiving.

    Marks the serial as RECEIVED if valid.
    """
    service = SerializationService(db)
    result = await service.scan_serial(
        barcode=data.barcode,
        grn_id=data.grn_id,
        grn_item_id=data.grn_item_id,
        user_id=current_user.id,
    )
    return result


@router.post("/scan/bulk", response_model=BulkScanResponse)
async def bulk_scan_serials(
    data: BulkScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan multiple barcodes at once"""
    service = SerializationService(db)
    results = await service.bulk_scan_serials(
        barcodes=data.barcodes,
        grn_id=data.grn_id,
        user_id=current_user.id,
    )

    valid_count = sum(1 for r in results if r.is_valid)

    return BulkScanResponse(
        grn_id=data.grn_id,
        total_scanned=len(results),
        valid_count=valid_count,
        invalid_count=len(results) - valid_count,
        results=results,
    )


# ==================== Serial Lookup ====================

@router.get("/lookup/{barcode}", response_model=SerialLookupResponse)
async def lookup_serial(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Look up full details of a serial by barcode.

    Returns PO info, product info, current location, warranty status, etc.
    """
    service = SerializationService(db)
    serial = await service.get_serial_by_barcode(barcode)

    if not serial:
        return SerialLookupResponse(
            barcode=barcode,
            found=False,
            serial=None,
        )

    # TODO: Fetch additional details (PO number, vendor name, product name, etc.)
    # For now, return basic info
    warranty_status = None
    if serial.warranty_end_date:
        if serial.warranty_end_date > datetime.utcnow():
            warranty_status = "active"
        else:
            warranty_status = "expired"

    return SerialLookupResponse(
        barcode=barcode,
        found=True,
        serial=POSerialResponse.model_validate(serial),
        warranty_status=warranty_status,
    )


@router.post("/validate/{barcode}")
async def validate_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate a barcode format and check if it exists.

    Does NOT update any status - just checks validity.
    """
    service = SerializationService(db)

    # Parse barcode to validate format
    try:
        parsed = service.parse_barcode(barcode)
    except ValueError as e:
        return {
            "barcode": barcode,
            "is_valid_format": False,
            "exists_in_db": False,
            "error": str(e),
        }

    # Check if exists in DB
    serial = await service.get_serial_by_barcode(barcode)

    return {
        "barcode": barcode,
        "is_valid_format": True,
        "exists_in_db": serial is not None,
        "parsed": parsed,
        "status": serial.status.value if serial else None,
    }


# ==================== Sequence Status ====================

@router.get("/sequence/{model_code}", response_model=SequenceStatusResponse)
async def get_sequence_status(
    model_code: str,
    supplier_code: str = Query(..., min_length=2, max_length=2),
    year_code: Optional[str] = Query(None),
    month_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current status of a serial sequence.

    Shows last serial used and next available serial.
    """
    service = SerializationService(db)
    result = await service.get_sequence_status(
        model_code=model_code,
        supplier_code=supplier_code,
        year_code=year_code,
        month_code=month_code,
    )
    return result


@router.post("/sequence/reset/{model_code}")
async def reset_sequence(
    model_code: str,
    supplier_code: str = Query(..., min_length=2, max_length=2),
    new_last_serial: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset a sequence to a specific serial number.

    WARNING: This should only be used for corrections.
    Resetting to a lower number may cause duplicate barcodes!
    """
    service = SerializationService(db)
    year_code = service.get_year_code()
    month_code = service.get_month_code()

    result = await db.execute(
        select(SerialSequence).where(
            SerialSequence.model_code == model_code.upper(),
            SerialSequence.supplier_code == supplier_code.upper(),
            SerialSequence.year_code == year_code,
            SerialSequence.month_code == month_code,
        )
    )
    sequence = result.scalar_one_or_none()

    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")

    old_serial = sequence.last_serial
    sequence.last_serial = new_last_serial
    sequence.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "model_code": model_code.upper(),
        "supplier_code": supplier_code.upper(),
        "year_code": year_code,
        "month_code": month_code,
        "old_last_serial": old_serial,
        "new_last_serial": new_last_serial,
    }


# ==================== Dashboard / Stats ====================

@router.get("/dashboard")
async def serialization_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get serialization dashboard stats"""

    # Total serials by status
    status_result = await db.execute(
        select(
            POSerial.status,
            func.count(POSerial.id).label("count")
        ).group_by(POSerial.status)
    )
    status_counts = {row.status.value: row.count for row in status_result}

    # Total by month (current year)
    service = SerializationService(db)
    current_year_code = service.get_year_code()

    monthly_result = await db.execute(
        select(
            SerialSequence.month_code,
            func.sum(SerialSequence.total_generated).label("total")
        ).where(SerialSequence.year_code == current_year_code)
        .group_by(SerialSequence.month_code)
    )
    monthly_totals = {row.month_code: row.total or 0 for row in monthly_result}

    # Total supplier codes
    supplier_count = await db.execute(
        select(func.count(SupplierCode.id)).where(SupplierCode.is_active == True)
    )

    # Total model codes
    model_count = await db.execute(
        select(func.count(ModelCodeReference.id)).where(ModelCodeReference.is_active == True)
    )

    # Total serials
    total_serials = await db.execute(select(func.count(POSerial.id)))

    return {
        "total_serials": total_serials.scalar() or 0,
        "by_status": status_counts,
        "monthly_generation": monthly_totals,
        "active_supplier_codes": supplier_count.scalar() or 0,
        "active_model_codes": model_count.scalar() or 0,
        "current_year_code": current_year_code,
        "current_month_code": service.get_month_code(),
    }


# ==================== Seed / Reset Codes ====================

@router.post("/seed-codes")
async def seed_serialization_codes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permissions: Permissions = None,
):
    """
    Reset and seed all model codes and supplier codes.

    WARNING: This deletes all existing codes and creates new ones.
    Only accessible by SUPER_ADMIN users.

    Creates proper codes for:
    - Water Purifier category (FG)
    - Spare Parts category (SP)
    - Supplier codes for vendors
    """
    # Only super admin can seed codes
    if not permissions or not permissions.is_super_admin():
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can seed serialization codes"
        )
    import uuid

    # Delete existing codes
    await db.execute(select(ModelCodeReference).execution_options(synchronize_session="fetch"))
    await db.execute(select(SupplierCode).execution_options(synchronize_session="fetch"))

    # Delete all model codes
    result = await db.execute(select(ModelCodeReference))
    for code in result.scalars().all():
        await db.delete(code)

    # Delete all supplier codes
    result = await db.execute(select(SupplierCode))
    for code in result.scalars().all():
        await db.delete(code)

    await db.flush()

    # ==================== SUPPLIER CODES ====================
    # These are 2-character codes for vendors/manufacturers

    supplier_codes_data = [
        # FG Suppliers (Finished Goods manufacturers)
        {"code": "FS", "name": "FastTrack Manufacturing", "description": "Primary FG manufacturer"},
        {"code": "ST", "name": "STOS Industries", "description": "Premium product manufacturer"},
        {"code": "AP", "name": "Aquapurite In-house", "description": "In-house manufacturing"},

        # Spare Parts Suppliers
        {"code": "EC", "name": "Economical Spares", "description": "Budget spare parts supplier"},
        {"code": "PR", "name": "Premium Spares", "description": "Premium spare parts supplier"},
        {"code": "GN", "name": "Generic Parts", "description": "Generic replacement parts"},
    ]

    created_suppliers = []
    for data in supplier_codes_data:
        supplier = SupplierCode(
            id=str(uuid.uuid4()).replace("-", ""),
            code=data["code"],
            name=data["name"],
            description=data["description"],
            is_active=True,
        )
        db.add(supplier)
        created_suppliers.append(data["code"])

    # ==================== MODEL CODES - WATER PURIFIERS (FG) ====================
    # Format: WPRAIEL001 -> WP(Category) R(Subcategory) A(Brand) IEL(Model) 001(Seq)
    # Barcode Model Code: IEL (3 chars)

    water_purifier_codes = [
        # RO Water Purifiers - product_sku matches actual catalog SKU
        {"fg_code": "WPRAIEL001", "model_code": "IEL", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPIEL001", "description": "IELITZ RO Water Purifier"},
        {"fg_code": "WPRAIPX001", "model_code": "IPX", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPIPX001", "description": "IPX RO Water Purifier"},
        {"fg_code": "WPRAPRM001", "model_code": "PRM", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPPRM001", "description": "Premium RO Water Purifier"},

        # UV Water Purifiers
        {"fg_code": "WPUAUVX001", "model_code": "UVX", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPUVX001", "description": "UVX UV Water Purifier"},
        {"fg_code": "WPUAULX001", "model_code": "ULX", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPULX001", "description": "Ultra UV Water Purifier"},

        # Gravity Water Purifiers
        {"fg_code": "WPGAGRY001", "model_code": "GRY", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPGRY001", "description": "Gravity Water Purifier"},

        # RO+UV Combo
        {"fg_code": "WPCARUV001", "model_code": "RUV", "item_type": ItemType.FINISHED_GOODS,
         "product_sku": "WPRUV001", "description": "RO+UV Combo Water Purifier"},
    ]

    # ==================== MODEL CODES - SPARE PARTS (SP) ====================
    # Format: SPSDFSDF001 -> SP(Category) SD(Subcategory) F(Brand) SDF(Model) 001(Seq)
    # Barcode Channel Code: EC or PR (based on supplier)

    spare_parts_codes = [
        # Sediment Filters - product_sku matches actual catalog SKU
        {"fg_code": "SPSDFSD001", "model_code": "SDF", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPSDF001", "description": "Sediment Filter (PP Yarn Wound) 10\""},
        {"fg_code": "SPSDFSD002", "model_code": "SD2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPSDF002", "description": "Sediment Filter 20\""},

        # Carbon Filters
        {"fg_code": "SPCBFCB001", "model_code": "CBF", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPCBF001", "description": "Carbon Block Filter 10\""},
        {"fg_code": "SPCBFCB002", "model_code": "CB2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPCBF002", "description": "Granular Activated Carbon Filter"},

        # Alkaline Filters
        {"fg_code": "SPALFAL001", "model_code": "ALK", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPALK001", "description": "Alkaline Mineral Block"},
        {"fg_code": "SPALFAL002", "model_code": "AL2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPALK002", "description": "Alkaline Cartridge"},

        # RO Membranes
        {"fg_code": "SPMBFMB001", "model_code": "MBR", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPMBR001", "description": "RO Membrane 80 GPD"},
        {"fg_code": "SPMBFMB002", "model_code": "MB2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPMBR002", "description": "RO Membrane 100 GPD"},

        # UV Lamps
        {"fg_code": "SPUVLUL001", "model_code": "UVL", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPUVL001", "description": "UV Lamp 11W"},
        {"fg_code": "SPUVLUL002", "model_code": "UV2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPUVL002", "description": "UV Lamp 16W"},

        # Pumps
        {"fg_code": "SPPMPPM001", "model_code": "PMP", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPPMP001", "description": "Booster Pump 100 GPD"},
        {"fg_code": "SPPMPPM002", "model_code": "PM2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPPMP002", "description": "Booster Pump 75 GPD"},

        # SMPS / Adapters
        {"fg_code": "SPSMPSM001", "model_code": "SMP", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPSMP001", "description": "SMPS 24V 2.5A"},
        {"fg_code": "SPSMPSM002", "model_code": "SM2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPSMP002", "description": "SMPS 36V 2A"},

        # Solenoid Valves
        {"fg_code": "SPSVLSV001", "model_code": "SVL", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPSVL001", "description": "Solenoid Valve 24V"},

        # Flow Restrictors
        {"fg_code": "SPFRFFR001", "model_code": "FRF", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPFRF001", "description": "Flow Restrictor 300ml"},

        # Connectors & Fittings
        {"fg_code": "SPCNFCN001", "model_code": "CNF", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPCNF001", "description": "Quick Connect Fittings Set"},

        # Tubing
        {"fg_code": "SPTBGTB001", "model_code": "TBG", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPTBG001", "description": "PE Tubing 1/4\" (10m)"},

        # Tanks
        {"fg_code": "SPTNKTN001", "model_code": "TNK", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPTNK001", "description": "Storage Tank 8L"},
        {"fg_code": "SPTNKTN002", "model_code": "TN2", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPTNK002", "description": "Storage Tank 12L"},

        # Pre-Filter Housing
        {"fg_code": "SPPFHPF001", "model_code": "PFH", "item_type": ItemType.SPARE_PART,
         "product_sku": "SPPFH001", "description": "Pre-Filter Housing 10\""},
    ]

    created_model_codes = []

    # Add Water Purifier codes
    for data in water_purifier_codes:
        model_ref = ModelCodeReference(
            id=str(uuid.uuid4()).replace("-", ""),
            fg_code=data["fg_code"],
            model_code=data["model_code"],
            item_type=data["item_type"],
            product_sku=data["product_sku"],
            description=data["description"],
            is_active=True,
        )
        db.add(model_ref)
        created_model_codes.append({"fg_code": data["fg_code"], "model_code": data["model_code"], "type": "FG"})

    # Add Spare Parts codes
    for data in spare_parts_codes:
        model_ref = ModelCodeReference(
            id=str(uuid.uuid4()).replace("-", ""),
            fg_code=data["fg_code"],
            model_code=data["model_code"],
            item_type=data["item_type"],
            product_sku=data["product_sku"],
            description=data["description"],
            is_active=True,
        )
        db.add(model_ref)
        created_model_codes.append({"fg_code": data["fg_code"], "model_code": data["model_code"], "type": "SP"})

    await db.commit()

    return {
        "success": True,
        "message": "Serialization codes seeded successfully",
        "supplier_codes_created": len(created_suppliers),
        "supplier_codes": created_suppliers,
        "model_codes_created": len(created_model_codes),
        "model_codes": {
            "water_purifiers": [c for c in created_model_codes if c["type"] == "FG"],
            "spare_parts": [c for c in created_model_codes if c["type"] == "SP"],
        },
        "barcode_format": {
            "finished_goods": "AP + YearCode(2) + MonthCode(1) + ModelCode(3) + Serial(8) = 16 chars",
            "spare_parts": "AP + SupplierCode(2) + YearCode(1) + MonthCode(1) + ChannelCode(2) + Serial(8) = 16 chars",
        },
        "examples": {
            "fg_barcode": "APAAAIIEL00000001 (IELITZ Water Purifier, Jan 2026, Serial 1)",
            "sp_barcode_economical": "APFSAAEC00000001 (Economical spare from FastTrack)",
            "sp_barcode_premium": "APSTAAPR00000001 (Premium spare from STOS)",
        }
    }
