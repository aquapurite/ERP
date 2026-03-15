"""Bill of Materials (BOM) API endpoints - SAP CS01/CS02 equivalent."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bom import BillOfMaterials, BOMItem
from app.models.product import Product
from app.api.deps import DB, CurrentUser

router = APIRouter()


# ==================== Pydantic Schemas ====================

class BOMItemCreate(BaseModel):
    component_product_id: UUID
    quantity: float = 1.0
    uom: str = "PCS"
    unit_cost: float = 0.0
    scrap_percentage: float = 0.0
    is_critical: bool = False
    notes: Optional[str] = None


class BOMCreate(BaseModel):
    parent_product_id: UUID
    name: str
    bom_type: str = "PRODUCTION"
    base_quantity: int = 1
    notes: Optional[str] = None
    items: List[BOMItemCreate] = []


class BOMItemUpdate(BaseModel):
    id: Optional[UUID] = None  # None means new item
    component_product_id: UUID
    quantity: float = 1.0
    uom: str = "PCS"
    unit_cost: float = 0.0
    scrap_percentage: float = 0.0
    is_critical: bool = False
    notes: Optional[str] = None


class BOMUpdate(BaseModel):
    name: Optional[str] = None
    bom_type: Optional[str] = None
    status: Optional[str] = None
    base_quantity: Optional[int] = None
    notes: Optional[str] = None
    items: Optional[List[BOMItemUpdate]] = None


class BOMItemResponse(BaseModel):
    id: UUID
    bom_id: UUID
    component_product_id: UUID
    component_product_name: Optional[str] = None
    component_sku: Optional[str] = None
    line_number: int
    quantity: float
    uom: str
    unit_cost: float
    total_cost: float
    scrap_percentage: float
    is_critical: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BOMResponse(BaseModel):
    id: UUID
    parent_product_id: UUID
    parent_product_name: Optional[str] = None
    bom_number: str
    name: str
    bom_type: str
    status: str
    version: int
    base_quantity: int
    total_component_cost: float
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[BOMItemResponse] = []

    class Config:
        from_attributes = True


# ==================== Helper ====================

async def _generate_bom_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(BillOfMaterials.id)))
    count = result.scalar() or 0
    return f"BOM-{count + 1:06d}"


def _build_item_response(item: BOMItem) -> BOMItemResponse:
    return BOMItemResponse(
        id=item.id,
        bom_id=item.bom_id,
        component_product_id=item.component_product_id,
        component_product_name=item.component_product.name if item.component_product else None,
        component_sku=item.component_product.sku if item.component_product else None,
        line_number=item.line_number,
        quantity=float(item.quantity),
        uom=item.uom or "PCS",
        unit_cost=float(item.unit_cost),
        total_cost=float(item.total_cost),
        scrap_percentage=float(item.scrap_percentage),
        is_critical=item.is_critical,
        notes=item.notes,
    )


def _build_bom_response(bom: BillOfMaterials) -> BOMResponse:
    return BOMResponse(
        id=bom.id,
        parent_product_id=bom.parent_product_id,
        parent_product_name=bom.parent_product.name if bom.parent_product else None,
        bom_number=bom.bom_number,
        name=bom.name,
        bom_type=bom.bom_type,
        status=bom.status,
        version=bom.version,
        base_quantity=bom.base_quantity,
        total_component_cost=float(bom.total_component_cost or 0),
        notes=bom.notes,
        created_at=bom.created_at,
        updated_at=bom.updated_at,
        items=[_build_item_response(i) for i in bom.items] if bom.items else [],
    )


# ==================== Endpoints ====================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_bom(payload: BOMCreate, db: DB, current_user: CurrentUser):
    """Create a new Bill of Materials with component items."""
    # Validate parent product exists
    product = await db.get(Product, payload.parent_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Parent product not found")

    bom_number = await _generate_bom_number(db)

    bom = BillOfMaterials(
        parent_product_id=payload.parent_product_id,
        bom_number=bom_number,
        name=payload.name,
        bom_type=payload.bom_type,
        status="DRAFT",
        base_quantity=payload.base_quantity,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(bom)
    await db.flush()

    total_cost = Decimal("0")
    for idx, item_data in enumerate(payload.items, start=1):
        line_total = Decimal(str(item_data.quantity)) * Decimal(str(item_data.unit_cost))
        bom_item = BOMItem(
            bom_id=bom.id,
            component_product_id=item_data.component_product_id,
            line_number=idx,
            quantity=Decimal(str(item_data.quantity)),
            uom=item_data.uom,
            unit_cost=Decimal(str(item_data.unit_cost)),
            total_cost=line_total,
            scrap_percentage=Decimal(str(item_data.scrap_percentage)),
            is_critical=item_data.is_critical,
            notes=item_data.notes,
        )
        db.add(bom_item)
        total_cost += line_total

    bom.total_component_cost = total_cost
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(BillOfMaterials)
        .options(selectinload(BillOfMaterials.parent_product), selectinload(BillOfMaterials.items).selectinload(BOMItem.component_product))
        .where(BillOfMaterials.id == bom.id)
    )
    bom = result.scalar_one()
    return _build_bom_response(bom)


@router.get("")
async def list_boms(
    db: DB,
    current_user: CurrentUser,
    product_id: Optional[UUID] = Query(None),
    bom_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List BOMs with optional filters."""
    query = select(BillOfMaterials).options(
        selectinload(BillOfMaterials.parent_product),
        selectinload(BillOfMaterials.items).selectinload(BOMItem.component_product),
    )
    count_query = select(func.count(BillOfMaterials.id))

    if product_id:
        query = query.where(BillOfMaterials.parent_product_id == product_id)
        count_query = count_query.where(BillOfMaterials.parent_product_id == product_id)
    if bom_status:
        query = query.where(BillOfMaterials.status == bom_status)
        count_query = count_query.where(BillOfMaterials.status == bom_status)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(BillOfMaterials.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    boms = result.scalars().all()

    return {
        "items": [_build_bom_response(b) for b in boms],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{bom_id}")
async def get_bom(bom_id: UUID, db: DB, current_user: CurrentUser):
    """Get BOM detail with items."""
    result = await db.execute(
        select(BillOfMaterials)
        .options(
            selectinload(BillOfMaterials.parent_product),
            selectinload(BillOfMaterials.items).selectinload(BOMItem.component_product),
        )
        .where(BillOfMaterials.id == bom_id)
    )
    bom = result.scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    return _build_bom_response(bom)


@router.put("/{bom_id}")
async def update_bom(bom_id: UUID, payload: BOMUpdate, db: DB, current_user: CurrentUser):
    """Update BOM and its items."""
    result = await db.execute(
        select(BillOfMaterials)
        .options(selectinload(BillOfMaterials.items))
        .where(BillOfMaterials.id == bom_id)
    )
    bom = result.scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    if payload.name is not None:
        bom.name = payload.name
    if payload.bom_type is not None:
        bom.bom_type = payload.bom_type
    if payload.status is not None:
        bom.status = payload.status
    if payload.base_quantity is not None:
        bom.base_quantity = payload.base_quantity
    if payload.notes is not None:
        bom.notes = payload.notes

    # Replace items if provided
    if payload.items is not None:
        # Delete existing items
        for old_item in bom.items:
            await db.delete(old_item)
        await db.flush()

        total_cost = Decimal("0")
        for idx, item_data in enumerate(payload.items, start=1):
            line_total = Decimal(str(item_data.quantity)) * Decimal(str(item_data.unit_cost))
            bom_item = BOMItem(
                bom_id=bom.id,
                component_product_id=item_data.component_product_id,
                line_number=idx,
                quantity=Decimal(str(item_data.quantity)),
                uom=item_data.uom,
                unit_cost=Decimal(str(item_data.unit_cost)),
                total_cost=line_total,
                scrap_percentage=Decimal(str(item_data.scrap_percentage)),
                is_critical=item_data.is_critical,
                notes=item_data.notes,
            )
            db.add(bom_item)
            total_cost += line_total
        bom.total_component_cost = total_cost

    bom.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # Reload
    result = await db.execute(
        select(BillOfMaterials)
        .options(selectinload(BillOfMaterials.parent_product), selectinload(BillOfMaterials.items).selectinload(BOMItem.component_product))
        .where(BillOfMaterials.id == bom_id)
    )
    bom = result.scalar_one()
    return _build_bom_response(bom)


@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bom(bom_id: UUID, db: DB, current_user: CurrentUser):
    """Delete BOM (only if DRAFT)."""
    bom = await db.get(BillOfMaterials, bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT BOMs can be deleted")
    await db.delete(bom)
    await db.flush()


@router.post("/{bom_id}/calculate-cost")
async def calculate_bom_cost(bom_id: UUID, db: DB, current_user: CurrentUser):
    """Recalculate total component cost from items."""
    result = await db.execute(
        select(BillOfMaterials)
        .options(selectinload(BillOfMaterials.items).selectinload(BOMItem.component_product))
        .where(BillOfMaterials.id == bom_id)
    )
    bom = result.scalar_one_or_none()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    total_cost = Decimal("0")
    for item in bom.items:
        # Try to use product cost_price if unit_cost is 0
        unit_cost = item.unit_cost or Decimal("0")
        if unit_cost == 0 and item.component_product and item.component_product.cost_price:
            unit_cost = item.component_product.cost_price
            item.unit_cost = unit_cost

        line_total = item.quantity * unit_cost
        item.total_cost = line_total
        total_cost += line_total

    bom.total_component_cost = total_cost
    bom.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # Reload with parent product
    result = await db.execute(
        select(BillOfMaterials)
        .options(selectinload(BillOfMaterials.parent_product), selectinload(BillOfMaterials.items).selectinload(BOMItem.component_product))
        .where(BillOfMaterials.id == bom_id)
    )
    bom = result.scalar_one()
    return _build_bom_response(bom)
