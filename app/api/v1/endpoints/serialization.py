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

from app.api.deps import get_db, get_current_user
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
)
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
