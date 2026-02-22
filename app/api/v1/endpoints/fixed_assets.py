"""API endpoints for Fixed Assets module."""
from datetime import date, datetime, timezone
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets import (
    AssetCategory, Asset, DepreciationEntry, AssetTransfer, AssetMaintenance, CapexRequest,
    DepreciationMethod, AssetStatus, TransferStatus, MaintenanceStatus, CapexRequestStatus
)
from app.models.accounting import (
    JournalEntry, JournalEntryLine, JournalEntryStatus as JournalStatus,
    GeneralLedger, ChartOfAccount,
    FinancialPeriod, FinancialPeriodStatus as PeriodStatus,
)
from app.models.user import User
from app.schemas.fixed_assets import (
    # Category
    AssetCategoryCreate, AssetCategoryUpdate, AssetCategoryResponse, AssetCategoryListResponse,
    # Asset
    AssetCreate, AssetUpdate, AssetResponse, AssetDetailResponse, AssetListResponse,
    # Depreciation
    DepreciationRunRequest, DepreciationEntryResponse, DepreciationListResponse,
    # Transfer
    AssetTransferCreate, AssetTransferResponse, AssetTransferListResponse,
    # Maintenance
    AssetMaintenanceCreate, AssetMaintenanceUpdate, AssetMaintenanceResponse, AssetMaintenanceListResponse,
    # Other
    AssetDisposeRequest, FixedAssetsDashboard,
    # CAPEX
    CapexRequestCreate, CapexRequestUpdate, CapexRequestResponse, CapexRequestDetailResponse,
    CapexRequestListResponse, CapexSubmitRequest, CapexApprovalRequest, CapexRejectionRequest,
    CapexCreatePORequest, CapexReceiveRequest, CapexCapitalizeRequest, CapexAttachmentRequest,
    CapexDashboard,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions

router = APIRouter()


# ==================== Helper Functions ====================

async def generate_asset_code(db: AsyncSession) -> str:
    """Generate unique asset code."""
    today = date.today()
    prefix = f"FA-{today.strftime('%Y%m')}"

    result = await db.execute(
        select(func.count(Asset.id))
        .where(Asset.asset_code.like(f"{prefix}%"))
    )
    count = result.scalar() or 0

    return f"{prefix}-{(count + 1):04d}"


async def generate_transfer_number(db: AsyncSession) -> str:
    """Generate unique transfer number."""
    today = date.today()
    prefix = f"AT-{today.strftime('%Y%m%d')}"

    result = await db.execute(
        select(func.count(AssetTransfer.id))
        .where(AssetTransfer.transfer_number.like(f"{prefix}%"))
    )
    count = result.scalar() or 0

    return f"{prefix}-{(count + 1):04d}"


async def generate_maintenance_number(db: AsyncSession) -> str:
    """Generate unique maintenance number."""
    today = date.today()
    prefix = f"AM-{today.strftime('%Y%m%d')}"

    result = await db.execute(
        select(func.count(AssetMaintenance.id))
        .where(AssetMaintenance.maintenance_number.like(f"{prefix}%"))
    )
    count = result.scalar() or 0

    return f"{prefix}-{(count + 1):04d}"


def calculate_depreciation(
    book_value: Decimal,
    method: DepreciationMethod,
    rate: Decimal,
    salvage_value: Decimal = Decimal("0")
) -> Decimal:
    """Calculate monthly depreciation amount."""
    if method == DepreciationMethod.SLM:
        # Straight Line Method: Annual depreciation / 12
        annual_depreciation = (book_value - salvage_value) * (rate / 100)
        return round(annual_depreciation / 12, 2)
    else:  # WDV
        # Written Down Value: Book value * rate / 12
        annual_depreciation = book_value * (rate / 100)
        return round(annual_depreciation / 12, 2)


# ==================== Asset Categories ====================

@router.get("/categories", response_model=AssetCategoryListResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def list_asset_categories(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
):
    """List asset categories."""
    query = select(AssetCategory)

    if is_active is not None:
        query = query.where(AssetCategory.is_active == is_active)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(AssetCategory.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    items = []
    for cat in categories:
        # Get asset count
        asset_count_result = await db.execute(
            select(func.count(Asset.id))
            .where(Asset.category_id == cat.id)
        )
        asset_count = asset_count_result.scalar() or 0

        items.append(AssetCategoryResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            depreciation_method=cat.depreciation_method,
            depreciation_rate=cat.depreciation_rate,
            useful_life_years=cat.useful_life_years,
            asset_account_id=cat.asset_account_id,
            depreciation_account_id=cat.depreciation_account_id,
            expense_account_id=cat.expense_account_id,
            is_active=cat.is_active,
            asset_count=asset_count,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        ))

    pages = (total + size - 1) // size
    return AssetCategoryListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/categories", response_model=AssetCategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("assets:create"))])
async def create_asset_category(
    category_in: AssetCategoryCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create asset category."""
    # Check code uniqueness
    existing = await db.execute(
        select(AssetCategory).where(AssetCategory.code == category_in.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category code already exists"
        )

    category = AssetCategory(
        code=category_in.code,
        name=category_in.name,
        description=category_in.description,
        depreciation_method=category_in.depreciation_method,
        depreciation_rate=category_in.depreciation_rate,
        useful_life_years=category_in.useful_life_years,
        asset_account_id=category_in.asset_account_id,
        depreciation_account_id=category_in.depreciation_account_id,
        expense_account_id=category_in.expense_account_id,
        is_active=True,
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return AssetCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        depreciation_method=category.depreciation_method,
        depreciation_rate=category.depreciation_rate,
        useful_life_years=category.useful_life_years,
        asset_account_id=category.asset_account_id,
        depreciation_account_id=category.depreciation_account_id,
        expense_account_id=category.expense_account_id,
        is_active=category.is_active,
        asset_count=0,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("/categories/dropdown", dependencies=[Depends(require_permissions("assets:view"))])
async def get_categories_dropdown(
    db: DB,
    current_user: CurrentUser,
):
    """Get asset categories for dropdown selection."""
    result = await db.execute(
        select(AssetCategory)
        .where(AssetCategory.is_active == True)
        .order_by(AssetCategory.name)
    )
    categories = result.scalars().all()

    return [
        {
            "id": str(cat.id),
            "code": cat.code,
            "name": cat.name,
            "depreciation_method": cat.depreciation_method,
            "depreciation_rate": float(cat.depreciation_rate),
        }
        for cat in categories
    ]


@router.put("/categories/{category_id}", response_model=AssetCategoryResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def update_asset_category(
    category_id: UUID,
    category_in: AssetCategoryUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update asset category."""
    result = await db.execute(
        select(AssetCategory).where(AssetCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)

    # Get asset count
    asset_count_result = await db.execute(
        select(func.count(Asset.id))
        .where(Asset.category_id == category.id)
    )
    asset_count = asset_count_result.scalar() or 0

    return AssetCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        depreciation_method=category.depreciation_method,
        depreciation_rate=category.depreciation_rate,
        useful_life_years=category.useful_life_years,
        asset_account_id=category.asset_account_id,
        depreciation_account_id=category.depreciation_account_id,
        expense_account_id=category.expense_account_id,
        is_active=category.is_active,
        asset_count=asset_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


# ==================== Assets ====================

@router.get("/assets", response_model=AssetListResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def list_assets(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    category_id: Optional[UUID] = None,
    status_filter: Optional[AssetStatus] = Query(None, alias="status"),
    warehouse_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    search: Optional[str] = None,
):
    """List assets with filters."""
    query = select(Asset).options(selectinload(Asset.category))

    if category_id:
        query = query.where(Asset.category_id == category_id)
    if status_filter:
        query = query.where(Asset.status == status_filter)
    if warehouse_id:
        query = query.where(Asset.warehouse_id == warehouse_id)
    if department_id:
        query = query.where(Asset.department_id == department_id)
    if search:
        query = query.where(
            (Asset.asset_code.ilike(f"%{search}%")) |
            (Asset.name.ilike(f"%{search}%")) |
            (Asset.serial_number.ilike(f"%{search}%"))
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(Asset.asset_code)

    result = await db.execute(query)
    assets = result.scalars().all()

    items = []
    for asset in assets:
        # For non-warehouse types, show location_address name as warehouse_name
        display_warehouse_name = None
        if asset.location_type != "WAREHOUSE" and asset.location_address:
            addr = asset.location_address
            parts = [addr.get("name", "")]
            if addr.get("city"):
                parts.append(addr["city"])
            display_warehouse_name = ", ".join(p for p in parts if p)
        items.append(AssetResponse(
            id=asset.id,
            asset_code=asset.asset_code,
            name=asset.name,
            description=asset.description,
            category_id=asset.category_id,
            category_name=asset.category.name if asset.category else None,
            serial_number=asset.serial_number,
            manufacturer=asset.manufacturer,
            location_type=asset.location_type or "WAREHOUSE",
            warehouse_name=display_warehouse_name,  # Would need join for warehouse type
            department_name=None,  # Would need join
            custodian_name=None,  # Would need join
            purchase_date=asset.purchase_date,
            purchase_price=asset.purchase_price,
            capitalized_value=asset.capitalized_value,
            accumulated_depreciation=asset.accumulated_depreciation,
            current_book_value=asset.current_book_value,
            status=asset.status,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        ))

    pages = (total + size - 1) // size
    return AssetListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/assets", response_model=AssetDetailResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("assets:create"))])
async def create_asset(
    asset_in: AssetCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new asset."""
    # Verify category exists
    cat_result = await db.execute(
        select(AssetCategory).where(AssetCategory.id == asset_in.category_id)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Generate asset code
    asset_code = await generate_asset_code(db)

    # Calculate capitalized value
    capitalized_value = asset_in.purchase_price + asset_in.installation_cost + asset_in.other_costs

    # If location type is not WAREHOUSE, clear warehouse_id
    effective_warehouse_id = asset_in.warehouse_id if asset_in.location_type == "WAREHOUSE" else None
    effective_location_address = asset_in.location_address if asset_in.location_type != "WAREHOUSE" else None

    asset = Asset(
        asset_code=asset_code,
        name=asset_in.name,
        description=asset_in.description,
        category_id=asset_in.category_id,
        serial_number=asset_in.serial_number,
        model_number=asset_in.model_number,
        manufacturer=asset_in.manufacturer,
        warehouse_id=effective_warehouse_id,
        location_type=asset_in.location_type,
        location_address=effective_location_address,
        location_details=asset_in.location_details,
        custodian_employee_id=asset_in.custodian_employee_id,
        department_id=asset_in.department_id,
        purchase_date=asset_in.purchase_date,
        purchase_price=asset_in.purchase_price,
        purchase_invoice_no=asset_in.purchase_invoice_no,
        vendor_id=asset_in.vendor_id,
        po_number=asset_in.po_number,
        capitalization_date=asset_in.capitalization_date,
        installation_cost=asset_in.installation_cost,
        other_costs=asset_in.other_costs,
        capitalized_value=capitalized_value,
        depreciation_method=asset_in.depreciation_method,
        depreciation_rate=asset_in.depreciation_rate,
        useful_life_years=asset_in.useful_life_years,
        salvage_value=asset_in.salvage_value,
        accumulated_depreciation=Decimal("0"),
        current_book_value=capitalized_value,
        warranty_start_date=asset_in.warranty_start_date,
        warranty_end_date=asset_in.warranty_end_date,
        warranty_details=asset_in.warranty_details,
        insured=asset_in.insured,
        insurance_policy_no=asset_in.insurance_policy_no,
        insurance_value=asset_in.insurance_value,
        insurance_expiry=asset_in.insurance_expiry,
        status=AssetStatus.ACTIVE,
        notes=asset_in.notes,
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return AssetDetailResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        category_id=asset.category_id,
        category_name=category.name,
        serial_number=asset.serial_number,
        model_number=asset.model_number,
        manufacturer=asset.manufacturer,
        warehouse_id=asset.warehouse_id,
        location_type=asset.location_type or "WAREHOUSE",
        location_address=asset.location_address,
        location_details=asset.location_details,
        custodian_employee_id=asset.custodian_employee_id,
        department_id=asset.department_id,
        purchase_date=asset.purchase_date,
        purchase_price=asset.purchase_price,
        purchase_invoice_no=asset.purchase_invoice_no,
        vendor_id=asset.vendor_id,
        po_number=asset.po_number,
        capitalization_date=asset.capitalization_date,
        installation_cost=asset.installation_cost,
        other_costs=asset.other_costs,
        capitalized_value=asset.capitalized_value,
        depreciation_method=asset.depreciation_method,
        depreciation_rate=asset.depreciation_rate,
        useful_life_years=asset.useful_life_years,
        salvage_value=asset.salvage_value,
        accumulated_depreciation=asset.accumulated_depreciation,
        current_book_value=asset.current_book_value,
        last_depreciation_date=asset.last_depreciation_date,
        warranty_start_date=asset.warranty_start_date,
        warranty_end_date=asset.warranty_end_date,
        warranty_details=asset.warranty_details,
        insured=asset.insured,
        insurance_policy_no=asset.insurance_policy_no,
        insurance_value=asset.insurance_value,
        insurance_expiry=asset.insurance_expiry,
        status=asset.status,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.get("/assets/{asset_id}", response_model=AssetDetailResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def get_asset(
    asset_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get asset by ID."""
    result = await db.execute(
        select(Asset)
        .options(selectinload(Asset.category))
        .where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    return AssetDetailResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        category_id=asset.category_id,
        category_name=asset.category.name if asset.category else None,
        serial_number=asset.serial_number,
        model_number=asset.model_number,
        manufacturer=asset.manufacturer,
        warehouse_id=asset.warehouse_id,
        location_type=asset.location_type or "WAREHOUSE",
        location_address=asset.location_address,
        location_details=asset.location_details,
        custodian_employee_id=asset.custodian_employee_id,
        department_id=asset.department_id,
        purchase_date=asset.purchase_date,
        purchase_price=asset.purchase_price,
        purchase_invoice_no=asset.purchase_invoice_no,
        vendor_id=asset.vendor_id,
        po_number=asset.po_number,
        capitalization_date=asset.capitalization_date,
        installation_cost=asset.installation_cost,
        other_costs=asset.other_costs,
        capitalized_value=asset.capitalized_value,
        depreciation_method=asset.depreciation_method,
        depreciation_rate=asset.depreciation_rate,
        useful_life_years=asset.useful_life_years,
        salvage_value=asset.salvage_value,
        accumulated_depreciation=asset.accumulated_depreciation,
        current_book_value=asset.current_book_value,
        last_depreciation_date=asset.last_depreciation_date,
        warranty_start_date=asset.warranty_start_date,
        warranty_end_date=asset.warranty_end_date,
        warranty_details=asset.warranty_details,
        insured=asset.insured,
        insurance_policy_no=asset.insurance_policy_no,
        insurance_value=asset.insurance_value,
        insurance_expiry=asset.insurance_expiry,
        status=asset.status,
        disposal_date=asset.disposal_date,
        disposal_price=asset.disposal_price,
        disposal_reason=asset.disposal_reason,
        gain_loss_on_disposal=asset.gain_loss_on_disposal,
        documents=asset.documents,
        images=asset.images,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.put("/assets/{asset_id}", response_model=AssetDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def update_asset(
    asset_id: UUID,
    asset_in: AssetUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update asset."""
    result = await db.execute(
        select(Asset)
        .options(selectinload(Asset.category))
        .where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    update_data = asset_in.model_dump(exclude_unset=True)

    # If location_type changed, enforce consistency
    new_location_type = update_data.get("location_type", asset.location_type)
    if new_location_type == "WAREHOUSE":
        update_data.pop("location_address", None)
    else:
        update_data["warehouse_id"] = None

    for key, value in update_data.items():
        setattr(asset, key, value)

    await db.commit()
    await db.refresh(asset)

    return AssetDetailResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        category_id=asset.category_id,
        category_name=asset.category.name if asset.category else None,
        serial_number=asset.serial_number,
        model_number=asset.model_number,
        manufacturer=asset.manufacturer,
        warehouse_id=asset.warehouse_id,
        location_type=asset.location_type or "WAREHOUSE",
        location_address=asset.location_address,
        location_details=asset.location_details,
        custodian_employee_id=asset.custodian_employee_id,
        department_id=asset.department_id,
        purchase_date=asset.purchase_date,
        purchase_price=asset.purchase_price,
        purchase_invoice_no=asset.purchase_invoice_no,
        vendor_id=asset.vendor_id,
        po_number=asset.po_number,
        capitalization_date=asset.capitalization_date,
        installation_cost=asset.installation_cost,
        other_costs=asset.other_costs,
        capitalized_value=asset.capitalized_value,
        depreciation_method=asset.depreciation_method,
        depreciation_rate=asset.depreciation_rate,
        useful_life_years=asset.useful_life_years,
        salvage_value=asset.salvage_value,
        accumulated_depreciation=asset.accumulated_depreciation,
        current_book_value=asset.current_book_value,
        last_depreciation_date=asset.last_depreciation_date,
        warranty_start_date=asset.warranty_start_date,
        warranty_end_date=asset.warranty_end_date,
        warranty_details=asset.warranty_details,
        insured=asset.insured,
        insurance_policy_no=asset.insurance_policy_no,
        insurance_value=asset.insurance_value,
        insurance_expiry=asset.insurance_expiry,
        status=asset.status,
        disposal_date=asset.disposal_date,
        disposal_price=asset.disposal_price,
        disposal_reason=asset.disposal_reason,
        gain_loss_on_disposal=asset.gain_loss_on_disposal,
        documents=asset.documents,
        images=asset.images,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.post("/assets/{asset_id}/dispose", response_model=AssetDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def dispose_asset(
    asset_id: UUID,
    dispose_in: AssetDisposeRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Dispose an asset."""
    result = await db.execute(
        select(Asset)
        .options(selectinload(Asset.category))
        .where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    if asset.status != AssetStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispose asset with status {asset.status}"
        )

    # Calculate gain/loss on disposal
    gain_loss = dispose_in.disposal_price - asset.current_book_value

    asset.status = AssetStatus.DISPOSED.value
    asset.disposal_date = dispose_in.disposal_date
    asset.disposal_price = dispose_in.disposal_price
    asset.disposal_reason = dispose_in.disposal_reason
    asset.gain_loss_on_disposal = gain_loss

    await db.commit()
    await db.refresh(asset)

    return AssetDetailResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        category_id=asset.category_id,
        category_name=asset.category.name if asset.category else None,
        serial_number=asset.serial_number,
        model_number=asset.model_number,
        manufacturer=asset.manufacturer,
        warehouse_id=asset.warehouse_id,
        location_type=asset.location_type or "WAREHOUSE",
        location_address=asset.location_address,
        location_details=asset.location_details,
        custodian_employee_id=asset.custodian_employee_id,
        department_id=asset.department_id,
        purchase_date=asset.purchase_date,
        purchase_price=asset.purchase_price,
        purchase_invoice_no=asset.purchase_invoice_no,
        vendor_id=asset.vendor_id,
        po_number=asset.po_number,
        capitalization_date=asset.capitalization_date,
        installation_cost=asset.installation_cost,
        other_costs=asset.other_costs,
        capitalized_value=asset.capitalized_value,
        depreciation_method=asset.depreciation_method,
        depreciation_rate=asset.depreciation_rate,
        useful_life_years=asset.useful_life_years,
        salvage_value=asset.salvage_value,
        accumulated_depreciation=asset.accumulated_depreciation,
        current_book_value=asset.current_book_value,
        last_depreciation_date=asset.last_depreciation_date,
        warranty_start_date=asset.warranty_start_date,
        warranty_end_date=asset.warranty_end_date,
        warranty_details=asset.warranty_details,
        insured=asset.insured,
        insurance_policy_no=asset.insurance_policy_no,
        insurance_value=asset.insurance_value,
        insurance_expiry=asset.insurance_expiry,
        status=asset.status,
        disposal_date=asset.disposal_date,
        disposal_price=asset.disposal_price,
        disposal_reason=asset.disposal_reason,
        gain_loss_on_disposal=asset.gain_loss_on_disposal,
        documents=asset.documents,
        images=asset.images,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permissions("assets:delete"))])
async def delete_asset(
    asset_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete an asset. Only allowed if no depreciation entries or transfers exist."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # Check for depreciation entries
    dep_count = await db.execute(
        select(func.count(DepreciationEntry.id)).where(DepreciationEntry.asset_id == asset_id)
    )
    if dep_count.scalar() or 0 > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete asset with depreciation entries. Dispose it instead."
        )

    # Check for transfers
    transfer_count = await db.execute(
        select(func.count(AssetTransfer.id)).where(AssetTransfer.asset_id == asset_id)
    )
    if transfer_count.scalar() or 0 > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete asset with transfer records. Dispose it instead."
        )

    await db.delete(asset)
    await db.commit()


# ==================== Depreciation ====================

@router.post("/depreciation/run", response_model=List[DepreciationEntryResponse], dependencies=[Depends(require_permissions("assets:update"))])
async def run_depreciation(
    run_in: DepreciationRunRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Run depreciation for a period."""
    # Get assets to depreciate
    query = select(Asset).options(selectinload(Asset.category)).where(Asset.status == AssetStatus.ACTIVE)

    if run_in.asset_ids:
        query = query.where(Asset.id.in_(run_in.asset_ids))

    result = await db.execute(query)
    assets = result.scalars().all()

    entries = []

    for asset in assets:
        # Check if already depreciated for this period
        existing = await db.execute(
            select(DepreciationEntry)
            .where(DepreciationEntry.asset_id == asset.id)
            .where(DepreciationEntry.period_date == run_in.period_date)
        )
        if existing.scalar_one_or_none():
            continue  # Skip if already processed

        # Get depreciation settings (asset overrides or category defaults)
        method = asset.depreciation_method or asset.category.depreciation_method
        rate = asset.depreciation_rate or asset.category.depreciation_rate
        salvage = asset.salvage_value

        # Calculate depreciation
        opening_value = asset.current_book_value
        depreciation_amount = calculate_depreciation(opening_value, method, rate, salvage)

        # Don't depreciate below salvage value
        if opening_value - depreciation_amount < salvage:
            depreciation_amount = opening_value - salvage
            if depreciation_amount <= 0:
                continue  # Fully depreciated

        closing_value = opening_value - depreciation_amount
        new_accumulated = asset.accumulated_depreciation + depreciation_amount

        # Create entry
        entry = DepreciationEntry(
            asset_id=asset.id,
            period_date=run_in.period_date,
            financial_year=run_in.financial_year,
            opening_book_value=opening_value,
            depreciation_method=method,
            depreciation_rate=rate,
            depreciation_amount=depreciation_amount,
            closing_book_value=closing_value,
            accumulated_depreciation=new_accumulated,
            is_posted=False,
            processed_by=current_user.id,
            processed_at=datetime.now(timezone.utc),
        )

        db.add(entry)

        # Update asset
        asset.accumulated_depreciation = new_accumulated
        asset.current_book_value = closing_value
        asset.last_depreciation_date = run_in.period_date

        entries.append((entry, asset))

    # Flush depreciation entries to get their IDs
    await db.flush()

    # ─── GL Posting for depreciation entries ───

    if entries:
        import uuid as uuid_module

        # Validate open financial period for the depreciation date
        period_r = await db.execute(
            select(FinancialPeriod).where(
                and_(
                    FinancialPeriod.start_date <= run_in.period_date,
                    FinancialPeriod.end_date >= run_in.period_date,
                    FinancialPeriod.status == PeriodStatus.OPEN,
                )
            ).limit(1)
        )
        period = period_r.scalar_one_or_none()

        gl_affected_accounts = set()

        for dep_entry, asset in entries:
            # Get GL accounts from asset category
            expense_account_id = asset.category.expense_account_id
            dep_account_id = asset.category.depreciation_account_id

            if not expense_account_id or not dep_account_id or not period:
                # Cannot post to GL without proper account mapping or period
                continue

            # Generate journal entry number
            today = date.today()
            count_r = await db.execute(
                select(func.count(JournalEntry.id)).where(
                    func.date(JournalEntry.created_at) == today
                )
            )
            jv_count = count_r.scalar() or 0
            entry_number = f"JV-{today.strftime('%Y%m%d')}-{str(jv_count + 1).zfill(4)}"

            # Create journal entry
            journal = JournalEntry(
                id=uuid_module.uuid4(),
                entry_number=entry_number,
                entry_type="DEPRECIATION",
                entry_date=run_in.period_date,
                period_id=period.id,
                narration=f"Depreciation for {asset.name} - {run_in.period_date.strftime('%B %Y')}",
                source_type="depreciation",
                source_id=dep_entry.id,
                total_debit=dep_entry.depreciation_amount,
                total_credit=dep_entry.depreciation_amount,
                created_by=current_user.id,
                status=JournalStatus.DRAFT.value,
            )
            db.add(journal)
            await db.flush()

            # Debit: Depreciation Expense (6700)
            line_dr = JournalEntryLine(
                id=uuid_module.uuid4(),
                journal_entry_id=journal.id,
                line_number=1,
                account_id=expense_account_id,
                debit_amount=dep_entry.depreciation_amount,
                credit_amount=Decimal("0"),
                description=f"Depreciation expense - {asset.name}",
            )
            db.add(line_dr)

            # Credit: Accumulated Depreciation (1600)
            line_cr = JournalEntryLine(
                id=uuid_module.uuid4(),
                journal_entry_id=journal.id,
                line_number=2,
                account_id=dep_account_id,
                debit_amount=Decimal("0"),
                credit_amount=dep_entry.depreciation_amount,
                description=f"Accumulated depreciation - {asset.name}",
            )
            db.add(line_cr)
            await db.flush()

            # Post to GL
            for line in [line_dr, line_cr]:
                gl_entry = GeneralLedger(
                    id=uuid_module.uuid4(),
                    account_id=line.account_id,
                    period_id=period.id,
                    transaction_date=run_in.period_date,
                    journal_entry_id=journal.id,
                    journal_line_id=line.id,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    running_balance=Decimal("0"),  # Will be recalculated
                    narration=line.description,
                )
                db.add(gl_entry)
                gl_affected_accounts.add(line.account_id)

            await db.flush()

            # Mark journal as POSTED
            journal.status = JournalStatus.POSTED.value
            journal.posted_by = current_user.id
            journal.posted_at = datetime.now(timezone.utc)

            # Link depreciation entry to journal
            dep_entry.journal_entry_id = journal.id
            dep_entry.is_posted = True

        # Recalculate running balances for all affected GL accounts
        for account_id in gl_affected_accounts:
            # Recalculate current_balance
            acct_r = await db.execute(
                select(ChartOfAccount).where(ChartOfAccount.id == account_id)
            )
            account = acct_r.scalar_one()
            opening_balance = account.opening_balance or Decimal("0")

            gl_sum_r = await db.execute(
                select(
                    func.coalesce(func.sum(GeneralLedger.debit_amount), 0).label("total_debit"),
                    func.coalesce(func.sum(GeneralLedger.credit_amount), 0).label("total_credit"),
                ).where(GeneralLedger.account_id == account_id)
            )
            gl_sum = gl_sum_r.one()
            account.current_balance = opening_balance + Decimal(str(gl_sum.total_debit)) - Decimal(str(gl_sum.total_credit))

            # Recalculate running balances for all GL entries
            gl_entries_r = await db.execute(
                select(GeneralLedger)
                .where(GeneralLedger.account_id == account_id)
                .order_by(GeneralLedger.transaction_date, GeneralLedger.created_at)
            )
            all_gl = gl_entries_r.scalars().all()
            running = opening_balance
            for gl in all_gl:
                running = running + (gl.debit_amount or Decimal("0")) - (gl.credit_amount or Decimal("0"))
                gl.running_balance = running

    await db.commit()

    # Build response
    response_entries = []
    for dep_entry, asset in entries:
        response_entries.append(DepreciationEntryResponse(
            id=dep_entry.id,
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.name,
            period_date=dep_entry.period_date,
            financial_year=dep_entry.financial_year,
            opening_book_value=dep_entry.opening_book_value,
            depreciation_method=dep_entry.depreciation_method,
            depreciation_rate=dep_entry.depreciation_rate,
            depreciation_amount=dep_entry.depreciation_amount,
            closing_book_value=dep_entry.closing_book_value,
            accumulated_depreciation=dep_entry.accumulated_depreciation,
            is_posted=dep_entry.is_posted,
            processed_at=dep_entry.processed_at,
            created_at=dep_entry.created_at,
        ))

    return response_entries


@router.get("/depreciation", response_model=DepreciationListResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def list_depreciation_entries(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    asset_id: Optional[UUID] = None,
    period_date: Optional[date] = None,
    financial_year: Optional[str] = None,
):
    """List depreciation entries."""
    query = select(DepreciationEntry).options(selectinload(DepreciationEntry.asset))

    if asset_id:
        query = query.where(DepreciationEntry.asset_id == asset_id)
    if period_date:
        query = query.where(DepreciationEntry.period_date == period_date)
    if financial_year:
        query = query.where(DepreciationEntry.financial_year == financial_year)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(DepreciationEntry.period_date.desc())

    result = await db.execute(query)
    entries = result.scalars().all()

    items = [
        DepreciationEntryResponse(
            id=entry.id,
            asset_id=entry.asset_id,
            asset_code=entry.asset.asset_code if entry.asset else None,
            asset_name=entry.asset.name if entry.asset else None,
            period_date=entry.period_date,
            financial_year=entry.financial_year,
            opening_book_value=entry.opening_book_value,
            depreciation_method=entry.depreciation_method,
            depreciation_rate=entry.depreciation_rate,
            depreciation_amount=entry.depreciation_amount,
            closing_book_value=entry.closing_book_value,
            accumulated_depreciation=entry.accumulated_depreciation,
            is_posted=entry.is_posted,
            journal_entry_id=entry.journal_entry_id,
            processed_at=entry.processed_at,
            created_at=entry.created_at,
        )
        for entry in entries
    ]

    pages = (total + size - 1) // size
    return DepreciationListResponse(items=items, total=total, page=page, size=size, pages=pages)


# ==================== Asset Transfers ====================

@router.get("/transfers", response_model=AssetTransferListResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def list_asset_transfers(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    asset_id: Optional[UUID] = None,
    status_filter: Optional[TransferStatus] = Query(None, alias="status"),
):
    """List asset transfers."""
    query = select(AssetTransfer).options(selectinload(AssetTransfer.asset))

    if asset_id:
        query = query.where(AssetTransfer.asset_id == asset_id)
    if status_filter:
        query = query.where(AssetTransfer.status == status_filter)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(AssetTransfer.created_at.desc())

    result = await db.execute(query)
    transfers = result.scalars().all()

    items = [
        AssetTransferResponse(
            id=t.id,
            transfer_number=t.transfer_number,
            asset_id=t.asset_id,
            asset_code=t.asset.asset_code if t.asset else None,
            asset_name=t.asset.name if t.asset else None,
            from_location_details=t.from_location_details,
            to_location_details=t.to_location_details,
            transfer_date=t.transfer_date,
            reason=t.reason,
            status=t.status,
            approved_at=t.approved_at,
            completed_at=t.completed_at,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in transfers
    ]

    pages = (total + size - 1) // size
    return AssetTransferListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/transfers", response_model=AssetTransferResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("assets:create"))])
async def create_asset_transfer(
    transfer_in: AssetTransferCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create asset transfer request."""
    # Verify asset exists and is active
    asset_result = await db.execute(
        select(Asset).where(Asset.id == transfer_in.asset_id)
    )
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    if asset.status != AssetStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transfer asset with status {asset.status}"
        )

    transfer_number = await generate_transfer_number(db)

    transfer = AssetTransfer(
        asset_id=transfer_in.asset_id,
        transfer_number=transfer_number,
        from_warehouse_id=asset.warehouse_id,
        from_department_id=asset.department_id,
        from_custodian_id=asset.custodian_employee_id,
        from_location_details=asset.location_details,
        to_warehouse_id=transfer_in.to_warehouse_id,
        to_department_id=transfer_in.to_department_id,
        to_custodian_id=transfer_in.to_custodian_id,
        to_location_details=transfer_in.to_location_details,
        transfer_date=transfer_in.transfer_date,
        reason=transfer_in.reason,
        status=TransferStatus.PENDING,
        requested_by=current_user.id,
    )

    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)

    return AssetTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        asset_id=transfer.asset_id,
        asset_code=asset.asset_code,
        asset_name=asset.name,
        from_location_details=transfer.from_location_details,
        to_location_details=transfer.to_location_details,
        transfer_date=transfer.transfer_date,
        reason=transfer.reason,
        status=transfer.status,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.put("/transfers/{transfer_id}/approve", response_model=AssetTransferResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def approve_transfer(
    transfer_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Approve asset transfer."""
    result = await db.execute(
        select(AssetTransfer)
        .options(selectinload(AssetTransfer.asset))
        .where(AssetTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()

    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )

    if transfer.status != TransferStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve transfer with status {transfer.status}"
        )

    transfer.status = TransferStatus.IN_TRANSIT.value
    transfer.approved_by = current_user.id
    transfer.approved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(transfer)

    return AssetTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        asset_id=transfer.asset_id,
        asset_code=transfer.asset.asset_code if transfer.asset else None,
        asset_name=transfer.asset.name if transfer.asset else None,
        from_location_details=transfer.from_location_details,
        to_location_details=transfer.to_location_details,
        transfer_date=transfer.transfer_date,
        reason=transfer.reason,
        status=transfer.status,
        approved_at=transfer.approved_at,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.put("/transfers/{transfer_id}/complete", response_model=AssetTransferResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def complete_transfer(
    transfer_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Complete asset transfer and update asset location."""
    result = await db.execute(
        select(AssetTransfer)
        .options(selectinload(AssetTransfer.asset))
        .where(AssetTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()

    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )

    if transfer.status != TransferStatus.IN_TRANSIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete transfer with status {transfer.status}"
        )

    # Update asset location
    asset = transfer.asset
    asset.warehouse_id = transfer.to_warehouse_id
    asset.department_id = transfer.to_department_id
    asset.custodian_employee_id = transfer.to_custodian_id
    asset.location_details = transfer.to_location_details

    transfer.status = TransferStatus.COMPLETED.value
    transfer.completed_at = datetime.now(timezone.utc)
    transfer.received_by = current_user.id

    await db.commit()
    await db.refresh(transfer)

    return AssetTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        asset_id=transfer.asset_id,
        asset_code=asset.asset_code,
        asset_name=asset.name,
        from_location_details=transfer.from_location_details,
        to_location_details=transfer.to_location_details,
        transfer_date=transfer.transfer_date,
        reason=transfer.reason,
        status=transfer.status,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


# ==================== Asset Maintenance ====================

@router.get("/maintenance", response_model=AssetMaintenanceListResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def list_asset_maintenance(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    asset_id: Optional[UUID] = None,
    status_filter: Optional[MaintenanceStatus] = Query(None, alias="status"),
):
    """List asset maintenance records."""
    query = select(AssetMaintenance).options(selectinload(AssetMaintenance.asset))

    if asset_id:
        query = query.where(AssetMaintenance.asset_id == asset_id)
    if status_filter:
        query = query.where(AssetMaintenance.status == status_filter)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(AssetMaintenance.scheduled_date.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    items = [
        AssetMaintenanceResponse(
            id=m.id,
            maintenance_number=m.maintenance_number,
            asset_id=m.asset_id,
            asset_code=m.asset.asset_code if m.asset else None,
            asset_name=m.asset.name if m.asset else None,
            maintenance_type=m.maintenance_type,
            description=m.description,
            scheduled_date=m.scheduled_date,
            started_date=m.started_date,
            completed_date=m.completed_date,
            estimated_cost=m.estimated_cost,
            actual_cost=m.actual_cost,
            vendor_invoice_no=m.vendor_invoice_no,
            status=m.status,
            findings=m.findings,
            parts_replaced=m.parts_replaced,
            recommendations=m.recommendations,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in records
    ]

    pages = (total + size - 1) // size
    return AssetMaintenanceListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/maintenance", response_model=AssetMaintenanceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("assets:create"))])
async def create_asset_maintenance(
    maintenance_in: AssetMaintenanceCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create asset maintenance record."""
    # Verify asset exists
    asset_result = await db.execute(
        select(Asset).where(Asset.id == maintenance_in.asset_id)
    )
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    maintenance_number = await generate_maintenance_number(db)

    maintenance = AssetMaintenance(
        asset_id=maintenance_in.asset_id,
        maintenance_number=maintenance_number,
        maintenance_type=maintenance_in.maintenance_type,
        description=maintenance_in.description,
        scheduled_date=maintenance_in.scheduled_date,
        estimated_cost=maintenance_in.estimated_cost,
        vendor_id=maintenance_in.vendor_id,
        assigned_to=maintenance_in.assigned_to,
        status=MaintenanceStatus.SCHEDULED,
    )

    db.add(maintenance)
    await db.commit()
    await db.refresh(maintenance)

    return AssetMaintenanceResponse(
        id=maintenance.id,
        maintenance_number=maintenance.maintenance_number,
        asset_id=maintenance.asset_id,
        asset_code=asset.asset_code,
        asset_name=asset.name,
        maintenance_type=maintenance.maintenance_type,
        description=maintenance.description,
        scheduled_date=maintenance.scheduled_date,
        estimated_cost=maintenance.estimated_cost,
        actual_cost=maintenance.actual_cost,
        status=maintenance.status,
        created_at=maintenance.created_at,
        updated_at=maintenance.updated_at,
    )


@router.put("/maintenance/{maintenance_id}", response_model=AssetMaintenanceResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def update_asset_maintenance(
    maintenance_id: UUID,
    maintenance_in: AssetMaintenanceUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update asset maintenance record."""
    result = await db.execute(
        select(AssetMaintenance)
        .options(selectinload(AssetMaintenance.asset))
        .where(AssetMaintenance.id == maintenance_id)
    )
    maintenance = result.scalar_one_or_none()

    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found"
        )

    update_data = maintenance_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(maintenance, key, value)

    await db.commit()
    await db.refresh(maintenance)

    return AssetMaintenanceResponse(
        id=maintenance.id,
        maintenance_number=maintenance.maintenance_number,
        asset_id=maintenance.asset_id,
        asset_code=maintenance.asset.asset_code if maintenance.asset else None,
        asset_name=maintenance.asset.name if maintenance.asset else None,
        maintenance_type=maintenance.maintenance_type,
        description=maintenance.description,
        scheduled_date=maintenance.scheduled_date,
        started_date=maintenance.started_date,
        completed_date=maintenance.completed_date,
        estimated_cost=maintenance.estimated_cost,
        actual_cost=maintenance.actual_cost,
        vendor_invoice_no=maintenance.vendor_invoice_no,
        status=maintenance.status,
        findings=maintenance.findings,
        parts_replaced=maintenance.parts_replaced,
        recommendations=maintenance.recommendations,
        created_at=maintenance.created_at,
        updated_at=maintenance.updated_at,
    )


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=FixedAssetsDashboard, dependencies=[Depends(require_permissions("assets:view"))])
async def get_fixed_assets_dashboard(
    db: DB,
    current_user: CurrentUser,
):
    """Get fixed assets dashboard statistics."""
    today = date.today()

    # Asset counts
    total_result = await db.execute(select(func.count(Asset.id)))
    total_assets = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.status == AssetStatus.ACTIVE)
    )
    active_assets = active_result.scalar() or 0

    disposed_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.status == AssetStatus.DISPOSED)
    )
    disposed_assets = disposed_result.scalar() or 0

    maintenance_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.status == AssetStatus.UNDER_MAINTENANCE)
    )
    under_maintenance = maintenance_result.scalar() or 0

    # Value totals
    values_result = await db.execute(
        select(
            func.sum(Asset.capitalized_value),
            func.sum(Asset.accumulated_depreciation),
            func.sum(Asset.current_book_value)
        ).where(Asset.status == AssetStatus.ACTIVE)
    )
    values = values_result.first()
    total_capitalized_value = values[0] or Decimal("0")
    total_accumulated_depreciation = values[1] or Decimal("0")
    total_current_book_value = values[2] or Decimal("0")

    # Monthly depreciation (current month)
    current_month = today.replace(day=1)
    monthly_dep_result = await db.execute(
        select(func.sum(DepreciationEntry.depreciation_amount))
        .where(DepreciationEntry.period_date == current_month)
    )
    monthly_depreciation = monthly_dep_result.scalar() or Decimal("0")

    # YTD depreciation
    fy_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)
    ytd_dep_result = await db.execute(
        select(func.sum(DepreciationEntry.depreciation_amount))
        .where(DepreciationEntry.period_date >= fy_start)
    )
    ytd_depreciation = ytd_dep_result.scalar() or Decimal("0")

    # Pending items
    pending_maintenance_result = await db.execute(
        select(func.count(AssetMaintenance.id))
        .where(AssetMaintenance.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS]))
    )
    pending_maintenance = pending_maintenance_result.scalar() or 0

    pending_transfers_result = await db.execute(
        select(func.count(AssetTransfer.id))
        .where(AssetTransfer.status.in_([TransferStatus.PENDING, TransferStatus.IN_TRANSIT]))
    )
    pending_transfers = pending_transfers_result.scalar() or 0

    # Category-wise distribution
    category_result = await db.execute(
        select(AssetCategory.name, func.count(Asset.id), func.coalesce(func.sum(Asset.current_book_value), 0))
        .outerjoin(Asset, and_(Asset.category_id == AssetCategory.id, Asset.status == AssetStatus.ACTIVE))
        .group_by(AssetCategory.id)
    )
    category_wise = [{"category_name": name, "count": count or 0, "book_value": float(book_val)} for name, count, book_val in category_result.all()]

    # Warranty expiring in 30 days
    thirty_days_later = date.today()
    thirty_days_later = date(today.year, today.month, today.day)
    from datetime import timedelta
    thirty_days_later = today + timedelta(days=30)
    warranty_result = await db.execute(
        select(func.count(Asset.id))
        .where(Asset.status == AssetStatus.ACTIVE)
        .where(Asset.warranty_end_date.isnot(None))
        .where(Asset.warranty_end_date <= thirty_days_later)
        .where(Asset.warranty_end_date >= today)
    )
    warranty_expiring_soon = warranty_result.scalar() or 0

    # Insurance expiring in 30 days
    insurance_result = await db.execute(
        select(func.count(Asset.id))
        .where(Asset.status == AssetStatus.ACTIVE)
        .where(Asset.insurance_expiry.isnot(None))
        .where(Asset.insurance_expiry <= thirty_days_later)
        .where(Asset.insurance_expiry >= today)
    )
    insurance_expiring_soon = insurance_result.scalar() or 0

    return FixedAssetsDashboard(
        total_assets=total_assets,
        active_assets=active_assets,
        disposed_assets=disposed_assets,
        under_maintenance=under_maintenance,
        total_capitalized_value=total_capitalized_value,
        total_accumulated_depreciation=total_accumulated_depreciation,
        total_current_book_value=total_current_book_value,
        monthly_depreciation=monthly_depreciation,
        ytd_depreciation=ytd_depreciation,
        pending_maintenance=pending_maintenance,
        pending_transfers=pending_transfers,
        category_wise=category_wise,
        warranty_expiring_soon=warranty_expiring_soon,
        insurance_expiring_soon=insurance_expiring_soon,
    )


# ==================== CAPEX Request Helper Functions ====================

async def generate_capex_number(db: AsyncSession) -> str:
    """Generate unique CAPEX request number."""
    today = date.today()
    prefix = f"CAPEX-{today.strftime('%Y%m')}"

    result = await db.execute(
        select(func.count(CapexRequest.id))
        .where(CapexRequest.request_number.like(f"{prefix}%"))
    )
    count = result.scalar() or 0

    return f"{prefix}-{(count + 1):04d}"


def get_capex_financial_year(dt: date) -> str:
    """Get financial year string for a date."""
    if dt.month >= 4:  # April onwards
        return f"{dt.year}-{str(dt.year + 1)[2:]}"
    else:
        return f"{dt.year - 1}-{str(dt.year)[2:]}"


def get_capex_approval_level(amount: Decimal) -> str:
    """Determine approval level based on estimated cost."""
    if amount <= Decimal("50000"):
        return "LEVEL_1"
    elif amount <= Decimal("500000"):
        return "LEVEL_2"
    else:
        return "LEVEL_3"


# ==================== CAPEX Requests ====================

@router.get("/capex", response_model=CapexRequestListResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def list_capex_requests(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status_filter: Optional[CapexRequestStatus] = Query(None, alias="status"),
    category_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
):
    """List CAPEX requests with filters."""
    query = select(CapexRequest).options(
        selectinload(CapexRequest.asset_category),
        selectinload(CapexRequest.requester),
        selectinload(CapexRequest.approver),
    )

    if status_filter:
        query = query.where(CapexRequest.status == status_filter)
    if category_id:
        query = query.where(CapexRequest.asset_category_id == category_id)
    if cost_center_id:
        query = query.where(CapexRequest.cost_center_id == cost_center_id)
    if date_from:
        query = query.where(CapexRequest.request_date >= date_from)
    if date_to:
        query = query.where(CapexRequest.request_date <= date_to)
    if search:
        query = query.where(
            (CapexRequest.request_number.ilike(f"%{search}%")) |
            (CapexRequest.asset_name.ilike(f"%{search}%"))
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(CapexRequest.request_date.desc(), CapexRequest.request_number.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    items = [
        CapexRequestResponse(
            id=r.id,
            request_number=r.request_number,
            request_date=r.request_date,
            financial_year=r.financial_year,
            asset_category_id=r.asset_category_id,
            category_code=r.asset_category.code if r.asset_category else None,
            category_name=r.asset_category.name if r.asset_category else None,
            asset_name=r.asset_name,
            description=r.description,
            quantity=r.quantity,
            estimated_cost=r.estimated_cost,
            estimated_gst=r.estimated_gst,
            estimated_total=r.estimated_total,
            actual_cost=r.actual_cost,
            urgency=r.urgency,
            status=r.status,
            approval_level=r.approval_level,
            requested_by_name=r.requester.full_name if r.requester else None,
            approved_by_name=r.approver.full_name if r.approver else None,
            approved_at=r.approved_at,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in requests
    ]

    pages = (total + size - 1) // size
    return CapexRequestListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/capex", response_model=CapexRequestDetailResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("assets:create"))])
async def create_capex_request(
    capex_in: CapexRequestCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create CAPEX request (DRAFT status)."""
    # Verify asset category exists
    cat_result = await db.execute(
        select(AssetCategory).where(AssetCategory.id == capex_in.asset_category_id)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset category not found"
        )

    # Generate request number
    request_number = await generate_capex_number(db)

    # Calculate estimated total
    estimated_total = capex_in.estimated_cost + capex_in.estimated_gst

    capex = CapexRequest(
        request_number=request_number,
        request_date=capex_in.request_date,
        financial_year=get_capex_financial_year(capex_in.request_date),
        asset_category_id=capex_in.asset_category_id,
        asset_name=capex_in.asset_name,
        description=capex_in.description,
        justification=capex_in.justification,
        quantity=capex_in.quantity,
        estimated_cost=capex_in.estimated_cost,
        estimated_gst=capex_in.estimated_gst,
        estimated_total=estimated_total,
        vendor_id=capex_in.vendor_id,
        vendor_quotation_no=capex_in.vendor_quotation_no,
        quotation_date=capex_in.quotation_date,
        expected_delivery_date=capex_in.expected_delivery_date,
        urgency=capex_in.urgency,
        cost_center_id=capex_in.cost_center_id,
        department_id=capex_in.department_id,
        notes=capex_in.notes,
        roi_analysis=capex_in.roi_analysis,
        status=CapexRequestStatus.DRAFT,
        requested_by=current_user.id,
    )

    db.add(capex)
    await db.commit()
    await db.refresh(capex)

    return CapexRequestDetailResponse(
        id=capex.id,
        request_number=capex.request_number,
        request_date=capex.request_date,
        financial_year=capex.financial_year,
        asset_category_id=capex.asset_category_id,
        category_code=category.code,
        category_name=category.name,
        asset_name=capex.asset_name,
        description=capex.description,
        quantity=capex.quantity,
        estimated_cost=capex.estimated_cost,
        estimated_gst=capex.estimated_gst,
        estimated_total=capex.estimated_total,
        justification=capex.justification,
        vendor_id=capex.vendor_id,
        vendor_quotation_no=capex.vendor_quotation_no,
        quotation_date=capex.quotation_date,
        expected_delivery_date=capex.expected_delivery_date,
        urgency=capex.urgency,
        cost_center_id=capex.cost_center_id,
        department_id=capex.department_id,
        notes=capex.notes,
        roi_analysis=capex.roi_analysis,
        status=capex.status,
        requested_by_name=current_user.full_name,
        created_at=capex.created_at,
        updated_at=capex.updated_at,
    )


@router.get("/capex/{capex_id}", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:view"))])
async def get_capex_request(
    capex_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get CAPEX request by ID."""
    result = await db.execute(
        select(CapexRequest)
        .options(
            selectinload(CapexRequest.asset_category),
            selectinload(CapexRequest.requester),
            selectinload(CapexRequest.approver),
            selectinload(CapexRequest.asset),
        )
        .where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    # Get rejected by name if rejected
    rejected_by_name = None
    if capex.rejected_by:
        rejected_result = await db.execute(
            select(User).where(User.id == capex.rejected_by)
        )
        rejected_user = rejected_result.scalar_one_or_none()
        rejected_by_name = rejected_user.full_name if rejected_user else None

    # Get capitalized by name
    capitalized_by_name = None
    if capex.capitalized_by:
        cap_result = await db.execute(
            select(User).where(User.id == capex.capitalized_by)
        )
        cap_user = cap_result.scalar_one_or_none()
        capitalized_by_name = cap_user.full_name if cap_user else None

    return CapexRequestDetailResponse(
        id=capex.id,
        request_number=capex.request_number,
        request_date=capex.request_date,
        financial_year=capex.financial_year,
        asset_category_id=capex.asset_category_id,
        category_code=capex.asset_category.code if capex.asset_category else None,
        category_name=capex.asset_category.name if capex.asset_category else None,
        asset_name=capex.asset_name,
        description=capex.description,
        quantity=capex.quantity,
        estimated_cost=capex.estimated_cost,
        estimated_gst=capex.estimated_gst,
        estimated_total=capex.estimated_total,
        actual_cost=capex.actual_cost,
        justification=capex.justification,
        vendor_id=capex.vendor_id,
        vendor_quotation_no=capex.vendor_quotation_no,
        quotation_date=capex.quotation_date,
        expected_delivery_date=capex.expected_delivery_date,
        urgency=capex.urgency,
        cost_center_id=capex.cost_center_id,
        department_id=capex.department_id,
        notes=capex.notes,
        roi_analysis=capex.roi_analysis,
        attachments=capex.attachments,
        status=capex.status,
        approval_level=capex.approval_level,
        rejection_reason=capex.rejection_reason,
        rejected_by_name=rejected_by_name,
        rejected_at=capex.rejected_at,
        purchase_order_id=capex.purchase_order_id,
        po_number=capex.po_number,
        po_created_at=capex.po_created_at,
        grn_id=capex.grn_id,
        received_at=capex.received_at,
        asset_id=capex.asset_id,
        asset_code=capex.asset.asset_code if capex.asset else None,
        capitalized_at=capex.capitalized_at,
        capitalized_by_name=capitalized_by_name,
        submitted_at=capex.submitted_at,
        requested_by_name=capex.requester.full_name if capex.requester else None,
        approved_by_name=capex.approver.full_name if capex.approver else None,
        approved_at=capex.approved_at,
        created_at=capex.created_at,
        updated_at=capex.updated_at,
    )


@router.put("/capex/{capex_id}", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def update_capex_request(
    capex_id: UUID,
    capex_in: CapexRequestUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update CAPEX request (only DRAFT status)."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update CAPEX request with status {capex.status}"
        )

    update_data = capex_in.model_dump(exclude_unset=True)

    # Recalculate estimated total if costs changed
    estimated_cost = update_data.get('estimated_cost', capex.estimated_cost)
    estimated_gst = update_data.get('estimated_gst', capex.estimated_gst)
    update_data['estimated_total'] = estimated_cost + estimated_gst

    # Update financial year if date changed
    if 'request_date' in update_data:
        update_data['financial_year'] = get_capex_financial_year(update_data['request_date'])

    for key, value in update_data.items():
        setattr(capex, key, value)

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.delete("/capex/{capex_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permissions("assets:delete"))])
async def delete_capex_request(
    capex_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete CAPEX request (only DRAFT status)."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete CAPEX request with status {capex.status}"
        )

    await db.delete(capex)
    await db.commit()


# ==================== CAPEX Workflow Endpoints ====================

@router.post("/capex/{capex_id}/submit", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def submit_capex_request(
    capex_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Submit CAPEX request for approval."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit CAPEX request with status {capex.status}"
        )

    # Determine approval level
    approval_level = get_capex_approval_level(capex.estimated_total)

    capex.status = CapexRequestStatus.PENDING_APPROVAL.value
    capex.submitted_at = datetime.now(timezone.utc)
    capex.approval_level = approval_level

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.post("/capex/{capex_id}/approve", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:approve"))])
async def approve_capex_request(
    capex_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Approve CAPEX request (maker cannot be checker)."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve CAPEX request with status {capex.status}"
        )

    # Maker-Checker validation
    if capex.requested_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requester cannot approve their own CAPEX request"
        )

    capex.status = CapexRequestStatus.APPROVED.value
    capex.approved_by = current_user.id
    capex.approved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.post("/capex/{capex_id}/reject", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:approve"))])
async def reject_capex_request(
    capex_id: UUID,
    reject_in: CapexRejectionRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Reject CAPEX request."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject CAPEX request with status {capex.status}"
        )

    capex.status = CapexRequestStatus.REJECTED.value
    capex.rejected_by = current_user.id
    capex.rejected_at = datetime.now(timezone.utc)
    capex.rejection_reason = reject_in.reason

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.post("/capex/{capex_id}/create-po", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def create_po_from_capex(
    capex_id: UUID,
    po_in: CapexCreatePORequest,
    db: DB,
    current_user: CurrentUser,
):
    """Create Purchase Order from approved CAPEX request."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create PO for CAPEX request with status {capex.status}"
        )

    # In a real implementation, this would call the purchase service to create PO
    # For now, we'll just update the CAPEX status
    po_number = f"PO-CAPEX-{datetime.now().strftime('%Y%m%d')}-{str(capex.id)[:4].upper()}"

    capex.status = CapexRequestStatus.PO_CREATED.value
    capex.vendor_id = po_in.vendor_id
    capex.po_number = po_number
    capex.po_created_at = datetime.now(timezone.utc)
    if po_in.expected_delivery_date:
        capex.expected_delivery_date = po_in.expected_delivery_date

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.post("/capex/{capex_id}/receive", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def receive_capex_goods(
    capex_id: UUID,
    receive_in: CapexReceiveRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Mark CAPEX goods as received (after GRN)."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.PO_CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive goods for CAPEX request with status {capex.status}"
        )

    capex.status = CapexRequestStatus.RECEIVED.value
    capex.grn_id = receive_in.grn_id
    capex.received_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.post("/capex/{capex_id}/capitalize", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:create"))])
async def capitalize_capex(
    capex_id: UUID,
    cap_in: CapexCapitalizeRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Capitalize CAPEX and create asset."""
    result = await db.execute(
        select(CapexRequest)
        .options(selectinload(CapexRequest.asset_category))
        .where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status != CapexRequestStatus.RECEIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot capitalize CAPEX request with status {capex.status}"
        )

    # Generate asset code
    asset_code = await generate_asset_code(db)

    # Calculate capitalized value
    capitalized_value = cap_in.actual_cost + cap_in.installation_cost + cap_in.other_costs

    # Create the asset
    asset = Asset(
        asset_code=asset_code,
        name=capex.asset_name,
        description=capex.description,
        category_id=capex.asset_category_id,
        serial_number=cap_in.serial_number,
        model_number=cap_in.model_number,
        warehouse_id=cap_in.warehouse_id,
        location_details=cap_in.location_details,
        custodian_employee_id=cap_in.custodian_employee_id,
        department_id=capex.department_id,
        purchase_date=capex.request_date,
        purchase_price=cap_in.actual_cost,
        vendor_id=capex.vendor_id,
        po_number=capex.po_number,
        capitalization_date=cap_in.capitalization_date,
        installation_cost=cap_in.installation_cost,
        other_costs=cap_in.other_costs,
        capitalized_value=capitalized_value,
        salvage_value=Decimal("0"),
        accumulated_depreciation=Decimal("0"),
        current_book_value=capitalized_value,
        status=AssetStatus.ACTIVE,
    )

    db.add(asset)
    await db.flush()  # Get the asset ID

    # Update CAPEX request
    capex.status = CapexRequestStatus.CAPITALIZED.value
    capex.asset_id = asset.id
    capex.actual_cost = cap_in.actual_cost
    capex.capitalized_at = datetime.now(timezone.utc)
    capex.capitalized_by = current_user.id

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


@router.post("/capex/{capex_id}/attachments", response_model=CapexRequestDetailResponse, dependencies=[Depends(require_permissions("assets:update"))])
async def add_capex_attachment(
    capex_id: UUID,
    attachment_in: CapexAttachmentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Add attachment to CAPEX request."""
    result = await db.execute(
        select(CapexRequest).where(CapexRequest.id == capex_id)
    )
    capex = result.scalar_one_or_none()

    if not capex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CAPEX request not found"
        )

    if capex.status in [CapexRequestStatus.CAPITALIZED, CapexRequestStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add attachment to CAPEX request with status {capex.status}"
        )

    # Initialize attachments if needed
    if not capex.attachments:
        capex.attachments = {"files": []}

    # Add attachment
    attachment = {
        "url": attachment_in.file_url,
        "name": attachment_in.file_name,
        "type": attachment_in.file_type,
        "size": attachment_in.file_size,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": str(current_user.id),
    }
    capex.attachments["files"].append(attachment)

    await db.commit()
    await db.refresh(capex)

    return await get_capex_request(capex_id, db, current_user)


# ==================== CAPEX Dashboard ====================

@router.get("/capex/dashboard/stats", response_model=CapexDashboard, dependencies=[Depends(require_permissions("assets:view"))])
async def get_capex_dashboard(
    db: DB,
    current_user: CurrentUser,
):
    """Get CAPEX dashboard statistics."""
    today = date.today()
    fy_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)

    # Request counts by status
    status_counts = await db.execute(
        select(CapexRequest.status, func.count(CapexRequest.id))
        .group_by(CapexRequest.status)
    )
    status_dict = dict(status_counts.all())

    total_requests = sum(status_dict.values())
    draft_count = status_dict.get(CapexRequestStatus.DRAFT, 0)
    pending_approval_count = status_dict.get(CapexRequestStatus.PENDING_APPROVAL, 0)
    approved_count = status_dict.get(CapexRequestStatus.APPROVED, 0)
    po_created_count = status_dict.get(CapexRequestStatus.PO_CREATED, 0)
    received_count = status_dict.get(CapexRequestStatus.RECEIVED, 0)
    capitalized_count = status_dict.get(CapexRequestStatus.CAPITALIZED, 0)
    rejected_count = status_dict.get(CapexRequestStatus.REJECTED, 0)

    # Total estimated this year
    estimated_result = await db.execute(
        select(func.sum(CapexRequest.estimated_total))
        .where(CapexRequest.request_date >= fy_start)
    )
    total_estimated_this_year = estimated_result.scalar() or Decimal("0")

    # Total approved this year
    approved_result = await db.execute(
        select(func.sum(CapexRequest.estimated_total))
        .where(CapexRequest.request_date >= fy_start)
        .where(CapexRequest.status.in_([
            CapexRequestStatus.APPROVED, CapexRequestStatus.PO_CREATED,
            CapexRequestStatus.RECEIVED, CapexRequestStatus.CAPITALIZED
        ]))
    )
    total_approved_this_year = approved_result.scalar() or Decimal("0")

    # Total capitalized this year
    capitalized_result = await db.execute(
        select(func.sum(CapexRequest.actual_cost))
        .where(CapexRequest.request_date >= fy_start)
        .where(CapexRequest.status == CapexRequestStatus.CAPITALIZED)
    )
    total_capitalized_this_year = capitalized_result.scalar() or Decimal("0")

    # Pending approval amount
    pending_result = await db.execute(
        select(func.sum(CapexRequest.estimated_total))
        .where(CapexRequest.status == CapexRequestStatus.PENDING_APPROVAL)
    )
    pending_approval_amount = pending_result.scalar() or Decimal("0")

    # Category-wise distribution
    category_result = await db.execute(
        select(AssetCategory.name, func.count(CapexRequest.id), func.sum(CapexRequest.estimated_total))
        .join(CapexRequest, CapexRequest.asset_category_id == AssetCategory.id)
        .where(CapexRequest.request_date >= fy_start)
        .group_by(AssetCategory.id)
    )
    category_wise = [
        {"category": name, "count": count or 0, "amount": float(amt or 0)}
        for name, count, amt in category_result.all()
    ]

    # Monthly trend (last 6 months)
    monthly_trend = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        m_start = date(y, m, 1)
        m_end = date(y + (1 if m == 12 else 0), (m % 12) + 1, 1)

        m_result = await db.execute(
            select(func.count(CapexRequest.id), func.sum(CapexRequest.estimated_total))
            .where(CapexRequest.request_date >= m_start)
            .where(CapexRequest.request_date < m_end)
        )
        row = m_result.first()
        monthly_trend.append({
            "month": m_start.strftime("%b %Y"),
            "count": row[0] or 0,
            "amount": float(row[1] or 0)
        })

    return CapexDashboard(
        total_requests=total_requests,
        draft_count=draft_count,
        pending_approval_count=pending_approval_count,
        approved_count=approved_count,
        po_created_count=po_created_count,
        received_count=received_count,
        capitalized_count=capitalized_count,
        rejected_count=rejected_count,
        total_estimated_this_year=total_estimated_this_year,
        total_approved_this_year=total_approved_this_year,
        total_capitalized_this_year=total_capitalized_this_year,
        pending_approval_amount=pending_approval_amount,
        category_wise=category_wise,
        monthly_trend=monthly_trend,
    )
