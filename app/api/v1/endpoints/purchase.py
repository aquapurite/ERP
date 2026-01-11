"""API endpoints for Purchase/Procurement management (P2P Cycle)."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase import (
    PurchaseRequisition, PurchaseRequisitionItem, RequisitionStatus,
    PurchaseOrder, PurchaseOrderItem, POStatus,
    PODeliverySchedule, DeliveryLotStatus,
    GoodsReceiptNote, GRNItem, GRNStatus, QualityCheckResult,
    VendorInvoice, VendorInvoiceStatus,
    VendorProformaInvoice, VendorProformaItem, ProformaStatus,
)
from app.models.vendor import Vendor, VendorLedger, VendorTransactionType
from app.models.inventory import StockItem, StockItemStatus, InventorySummary, StockMovement, StockMovementType
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.user import User
from app.schemas.purchase import (
    # PR Schemas
    PurchaseRequisitionCreate, PurchaseRequisitionUpdate, PurchaseRequisitionResponse,
    PRListResponse, PRApproveRequest,
    # PO Schemas
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    POListResponse, POBrief, POApproveRequest, POSendToVendorRequest,
    # PO Delivery Schedule Schemas
    PODeliveryScheduleResponse, PODeliveryPaymentRequest,
    # GRN Schemas
    GoodsReceiptCreate, GoodsReceiptUpdate, GoodsReceiptResponse,
    GRNListResponse, GRNBrief, GRNQualityCheckRequest, GRNPutAwayRequest,
    # Vendor Invoice Schemas
    VendorInvoiceCreate, VendorInvoiceUpdate, VendorInvoiceResponse,
    VendorInvoiceListResponse, VendorInvoiceBrief,
    ThreeWayMatchRequest, ThreeWayMatchResponse,
    # Vendor Proforma Schemas
    VendorProformaCreate, VendorProformaUpdate, VendorProformaResponse,
    VendorProformaListResponse, VendorProformaBrief,
    VendorProformaApproveRequest, VendorProformaConvertToPORequest,
    # Report Schemas
    POSummaryRequest, POSummaryResponse, GRNSummaryResponse, PendingGRNResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from app.services.audit_service import AuditService
from app.services.approval_service import ApprovalService
from app.models.approval import ApprovalEntityType

router = APIRouter()


# ==================== Debug Test Endpoint ====================

@router.post("/orders/debug-create", response_model=PurchaseOrderResponse)
async def debug_create_po(
    po_in: PurchaseOrderCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Debug endpoint to test PO creation and return detailed error."""
    import traceback
    try:
        # Verify vendor
        vendor_result = await db.execute(
            select(Vendor).where(Vendor.id == po_in.vendor_id)
        )
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            return {"error": "Vendor not found", "vendor_id": str(po_in.vendor_id)}

        # Verify warehouse
        wh_result = await db.execute(
            select(Warehouse).where(Warehouse.id == po_in.delivery_warehouse_id)
        )
        warehouse = wh_result.scalar_one_or_none()
        if not warehouse:
            return {"error": "Warehouse not found", "warehouse_id": str(po_in.delivery_warehouse_id)}

        # Generate PO number
        today = date.today()
        count_result = await db.execute(
            select(func.count(PurchaseOrder.id)).where(
                func.date(PurchaseOrder.created_at) == today
            )
        )
        count = count_result.scalar() or 0
        po_number = f"PO-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

        # Create PO with minimal fields
        po = PurchaseOrder(
            po_number=po_number,
            po_date=today,
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            vendor_gstin=vendor.gstin,
            delivery_warehouse_id=po_in.delivery_warehouse_id,
            created_by=current_user.id,
            subtotal=Decimal("0"),
            taxable_amount=Decimal("0"),
            grand_total=Decimal("0"),
        )
        db.add(po)
        await db.flush()

        # Create one item
        for item_data in po_in.items:
            gross_amount = item_data.quantity_ordered * item_data.unit_price
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                line_number=1,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                sku=item_data.sku,
                quantity_ordered=item_data.quantity_ordered,
                unit_price=item_data.unit_price,
                taxable_amount=gross_amount,
                gst_rate=item_data.gst_rate,
                cgst_rate=item_data.gst_rate / 2,
                sgst_rate=item_data.gst_rate / 2,
                igst_rate=Decimal("0"),
                cgst_amount=gross_amount * (item_data.gst_rate / 200),
                sgst_amount=gross_amount * (item_data.gst_rate / 200),
                igst_amount=Decimal("0"),
                cess_amount=Decimal("0"),
                total_amount=gross_amount * (1 + item_data.gst_rate / 100),
            )
            db.add(item)

        # Update PO totals
        po.subtotal = gross_amount
        po.taxable_amount = gross_amount
        po.grand_total = gross_amount * (1 + item_data.gst_rate / 100)

        await db.commit()

        # Test load relationships like the real endpoint
        try:
            result = await db.execute(
                select(PurchaseOrder)
                .options(
                    selectinload(PurchaseOrder.items),
                    selectinload(PurchaseOrder.delivery_schedules)
                )
                .where(PurchaseOrder.id == po.id)
            )
            po_loaded = result.scalar_one()
            # Return the PO object - FastAPI will serialize with PurchaseOrderResponse
            return po_loaded
        except Exception as e2:
            return {"error": "Failed at selectinload", "detail": str(e2), "traceback": traceback.format_exc()}

    except Exception as e:
        await db.rollback()
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


# ==================== Next Number Generation ====================

@router.get("/requisitions/next-number")
async def get_next_pr_number(
    db: DB,
):
    """Get the next available Purchase Requisition number."""
    today = date.today()

    # Find the highest PR number for today
    result = await db.execute(
        select(PurchaseRequisition.requisition_number)
        .where(func.date(PurchaseRequisition.created_at) == today)
        .order_by(PurchaseRequisition.requisition_number.desc())
        .limit(1)
    )
    last_pr = result.scalar_one_or_none()

    if last_pr:
        try:
            # Extract the sequence number from PR-YYYYMMDD-XXXX
            last_num = int(last_pr.split("-")[-1])
            next_num = last_num + 1
        except (IndexError, ValueError):
            next_num = 1
    else:
        next_num = 1

    next_pr = f"PR-{today.strftime('%Y%m%d')}-{str(next_num).zfill(4)}"
    return {"next_number": next_pr, "prefix": f"PR-{today.strftime('%Y%m%d')}"}


@router.get("/orders/next-number")
async def get_next_po_number(
    db: DB,
):
    """Get the next available Purchase Order number."""
    today = date.today()
    fy_year = today.year if today.month >= 4 else today.year - 1
    fy_suffix = f"{str(fy_year)[-2:]}-{str(fy_year + 1)[-2:]}"

    # Find the highest PO number for this financial year
    result = await db.execute(
        select(PurchaseOrder.po_number)
        .where(PurchaseOrder.po_number.like(f"PO/APL/{fy_suffix}/%"))
        .order_by(PurchaseOrder.po_number.desc())
        .limit(1)
    )
    last_po = result.scalar_one_or_none()

    if last_po:
        try:
            # Extract the sequence number from PO/APL/YY-YY/XXXX
            last_num = int(last_po.split("/")[-1])
            next_num = last_num + 1
        except (IndexError, ValueError):
            next_num = 1
    else:
        next_num = 1

    next_po = f"PO/APL/{fy_suffix}/{str(next_num).zfill(4)}"
    return {"next_number": next_po, "prefix": f"PO/APL/{fy_suffix}"}


@router.get("/grn/next-number")
async def get_next_grn_number(
    db: DB,
):
    """Get the next available Goods Receipt Note number."""
    today = date.today()
    fy_year = today.year if today.month >= 4 else today.year - 1
    fy_suffix = f"{str(fy_year)[-2:]}-{str(fy_year + 1)[-2:]}"

    # Find the highest GRN number for this financial year
    result = await db.execute(
        select(GoodsReceiptNote.grn_number)
        .where(GoodsReceiptNote.grn_number.like(f"GRN/APL/{fy_suffix}/%"))
        .order_by(GoodsReceiptNote.grn_number.desc())
        .limit(1)
    )
    last_grn = result.scalar_one_or_none()

    if last_grn:
        try:
            last_num = int(last_grn.split("/")[-1])
            next_num = last_num + 1
        except (IndexError, ValueError):
            next_num = 1
    else:
        next_num = 1

    next_grn = f"GRN/APL/{fy_suffix}/{str(next_num).zfill(4)}"
    return {"next_number": next_grn, "prefix": f"GRN/APL/{fy_suffix}"}


# ==================== Purchase Requisition (PR) ====================

@router.post("/requisitions", response_model=PurchaseRequisitionResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_requisition(
    pr_in: PurchaseRequisitionCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new Purchase Requisition."""
    # Generate PR number
    today = date.today()
    count_result = await db.execute(
        select(func.count(PurchaseRequisition.id)).where(
            func.date(PurchaseRequisition.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    pr_number = f"PR-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Calculate estimated total
    estimated_total = sum(
        item.quantity_requested * item.estimated_unit_price
        for item in pr_in.items
    )

    # Create PR
    pr = PurchaseRequisition(
        requisition_number=pr_number,
        requesting_department=pr_in.requesting_department,
        required_by_date=pr_in.required_by_date,
        delivery_warehouse_id=pr_in.delivery_warehouse_id,
        priority=pr_in.priority,
        reason=pr_in.reason,
        notes=pr_in.notes,
        request_date=today,
        requested_by=current_user.id,
        estimated_total=estimated_total,
    )

    db.add(pr)
    await db.flush()

    # Create PR items
    for item_data in pr_in.items:
        item = PurchaseRequisitionItem(
            requisition_id=pr.id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            product_name=item_data.product_name,
            sku=item_data.sku,
            quantity_requested=item_data.quantity_requested,
            uom=item_data.uom,
            estimated_unit_price=item_data.estimated_unit_price,
            estimated_total=item_data.quantity_requested * item_data.estimated_unit_price,
            preferred_vendor_id=item_data.preferred_vendor_id,
            notes=item_data.notes,
            # Multi-delivery support
            monthly_quantities=item_data.monthly_quantities,
        )
        db.add(item)

    await db.commit()
    await db.refresh(pr)

    # Load items
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr.id)
    )
    pr = result.scalar_one()

    return pr


@router.get("/requisitions/stats")
async def get_requisition_stats(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get purchase requisition statistics."""
    # Count by status
    draft_result = await db.execute(
        select(func.count(PurchaseRequisition.id))
        .where(PurchaseRequisition.status == RequisitionStatus.DRAFT)
    )
    draft_count = draft_result.scalar() or 0

    submitted_result = await db.execute(
        select(func.count(PurchaseRequisition.id))
        .where(PurchaseRequisition.status == RequisitionStatus.SUBMITTED)
    )
    submitted_count = submitted_result.scalar() or 0

    approved_result = await db.execute(
        select(func.count(PurchaseRequisition.id))
        .where(PurchaseRequisition.status == RequisitionStatus.APPROVED)
    )
    approved_count = approved_result.scalar() or 0

    rejected_result = await db.execute(
        select(func.count(PurchaseRequisition.id))
        .where(PurchaseRequisition.status == RequisitionStatus.REJECTED)
    )
    rejected_count = rejected_result.scalar() or 0

    converted_result = await db.execute(
        select(func.count(PurchaseRequisition.id))
        .where(PurchaseRequisition.status == RequisitionStatus.CONVERTED)
    )
    converted_count = converted_result.scalar() or 0

    total_result = await db.execute(
        select(func.count(PurchaseRequisition.id))
    )
    total_count = total_result.scalar() or 0

    return {
        "total": total_count,
        "draft": draft_count,
        "submitted": submitted_count,
        "approved": approved_count,
        "rejected": rejected_count,
        "converted": converted_count,
    }


@router.get("/requisitions", response_model=PRListResponse)
async def list_purchase_requisitions(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[RequisitionStatus] = None,
    warehouse_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """List purchase requisitions."""
    query = select(PurchaseRequisition).options(
        selectinload(PurchaseRequisition.items),
        selectinload(PurchaseRequisition.requested_by_user),
        selectinload(PurchaseRequisition.delivery_warehouse),
    )
    count_query = select(func.count(PurchaseRequisition.id))

    filters = []
    if status:
        filters.append(PurchaseRequisition.status == status)
    if warehouse_id:
        filters.append(PurchaseRequisition.delivery_warehouse_id == warehouse_id)
    if start_date:
        filters.append(PurchaseRequisition.request_date >= start_date)
    if end_date:
        filters.append(PurchaseRequisition.request_date <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(PurchaseRequisition.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    prs = result.scalars().all()

    # Build response with computed fields
    pr_responses = []
    for pr in prs:
        pr_dict = {
            "id": pr.id,
            "requisition_number": pr.requisition_number,
            "status": pr.status,
            "request_date": pr.request_date,
            "requested_by": pr.requested_by,
            "requested_by_name": pr.requested_by_user.full_name if pr.requested_by_user else None,
            "requesting_department": pr.requesting_department,
            "required_by_date": pr.required_by_date,
            "delivery_warehouse_id": pr.delivery_warehouse_id,
            "delivery_warehouse_name": pr.delivery_warehouse.name if pr.delivery_warehouse else None,
            "priority": pr.priority,
            "reason": pr.reason,
            "notes": pr.notes,
            "estimated_total": pr.estimated_total,
            "approved_by": pr.approved_by,
            "approved_at": pr.approved_at,
            "rejection_reason": pr.rejection_reason,
            "converted_to_po_id": pr.converted_to_po_id,
            "items": pr.items,
            "created_at": pr.created_at,
            "updated_at": pr.updated_at,
        }
        pr_responses.append(PurchaseRequisitionResponse.model_validate(pr_dict))

    return PRListResponse(
        items=pr_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/requisitions/{pr_id}", response_model=PurchaseRequisitionResponse)
async def get_purchase_requisition(
    pr_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get purchase requisition by ID."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(
            selectinload(PurchaseRequisition.items),
            selectinload(PurchaseRequisition.requested_by_user),
            selectinload(PurchaseRequisition.delivery_warehouse),
        )
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    # Build response with computed fields
    pr_dict = {
        "id": pr.id,
        "requisition_number": pr.requisition_number,
        "status": pr.status,
        "request_date": pr.request_date,
        "requested_by": pr.requested_by,
        "requested_by_name": pr.requested_by_user.full_name if pr.requested_by_user else None,
        "requesting_department": pr.requesting_department,
        "required_by_date": pr.required_by_date,
        "delivery_warehouse_id": pr.delivery_warehouse_id,
        "delivery_warehouse_name": pr.delivery_warehouse.name if pr.delivery_warehouse else None,
        "priority": pr.priority,
        "reason": pr.reason,
        "notes": pr.notes,
        "estimated_total": pr.estimated_total,
        "approved_by": pr.approved_by,
        "approved_at": pr.approved_at,
        "rejection_reason": pr.rejection_reason,
        "converted_to_po_id": pr.converted_to_po_id,
        "items": pr.items,
        "created_at": pr.created_at,
        "updated_at": pr.updated_at,
    }

    return PurchaseRequisitionResponse.model_validate(pr_dict)


@router.post("/requisitions/{pr_id}/approve", response_model=PurchaseRequisitionResponse)
async def approve_purchase_requisition(
    pr_id: UUID,
    request: PRApproveRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a purchase requisition."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    if pr.status != RequisitionStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot {request.action.lower()} PR in {pr.status.value} status. Only SUBMITTED PRs can be approved/rejected."
        )

    if request.action == "APPROVE":
        pr.status = RequisitionStatus.APPROVED
        pr.approved_by = current_user.id
        pr.approved_at = datetime.utcnow()
    else:  # REJECT
        if not request.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        pr.status = RequisitionStatus.REJECTED
        pr.rejection_reason = request.rejection_reason

    await db.commit()
    await db.refresh(pr)

    return pr


@router.post("/requisitions/{pr_id}/submit", response_model=PurchaseRequisitionResponse)
async def submit_purchase_requisition(
    pr_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Submit a draft purchase requisition for approval."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    if pr.status != RequisitionStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit PR in {pr.status.value} status. Only DRAFT PRs can be submitted."
        )

    # Validate PR has items
    if not pr.items:
        raise HTTPException(status_code=400, detail="Cannot submit PR without items")

    pr.status = RequisitionStatus.SUBMITTED

    # Create approval request
    approval = await ApprovalService.create_approval_request(
        db=db,
        entity_type=ApprovalEntityType.PURCHASE_REQUISITION,
        entity_id=pr.id,
        entity_number=pr.requisition_number,
        amount=pr.estimated_total or Decimal("0"),
        title=f"Purchase Requisition: {pr.requisition_number}",
        requested_by=current_user.id,
        description=pr.reason,
        priority=pr.priority if hasattr(pr, 'priority') and pr.priority else 5,
    )

    await db.commit()
    await db.refresh(pr)

    return pr


@router.post("/requisitions/{pr_id}/cancel", response_model=PurchaseRequisitionResponse)
async def cancel_purchase_requisition(
    pr_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Cancel a purchase requisition."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    if pr.status == RequisitionStatus.CONVERTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel PR that has been converted to PO"
        )

    pr.status = RequisitionStatus.CANCELLED
    await db.commit()
    await db.refresh(pr)

    return pr


@router.delete("/requisitions/{pr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_requisition(
    pr_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete a purchase requisition. Only DRAFT and CANCELLED PRs can be deleted."""
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    # Only allow deletion of DRAFT or CANCELLED PRs
    if pr.status not in [RequisitionStatus.DRAFT, RequisitionStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete PR in {pr.status} status. Only DRAFT or CANCELLED PRs can be deleted."
        )

    # Delete items first (due to foreign key constraint)
    await db.execute(
        delete(PurchaseRequisitionItem).where(PurchaseRequisitionItem.requisition_id == pr_id)
    )

    # Delete the PR
    await db.delete(pr)
    await db.commit()

    return None


@router.post("/requisitions/{pr_id}/convert-to-po", response_model=PurchaseOrderResponse)
async def convert_requisition_to_po(
    pr_id: UUID,
    request: dict,  # expects {"vendor_id": "uuid"}
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Convert an approved PR to a Purchase Order with multi-delivery support."""
    # Get PR with items
    result = await db.execute(
        select(PurchaseRequisition)
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    if pr.status != RequisitionStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Only APPROVED PRs can be converted to PO. Current status: {pr.status.value}"
        )

    # Validate vendor
    vendor_id = request.get("vendor_id")
    if not vendor_id:
        raise HTTPException(status_code=400, detail="vendor_id is required")

    vendor_result = await db.execute(select(Vendor).where(Vendor.id == UUID(vendor_id)))
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Generate PO number
    today = date.today()
    count_result = await db.execute(
        select(func.count(PurchaseOrder.id)).where(
            func.date(PurchaseOrder.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    po_number = f"PO-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Get warehouse
    wh_result = await db.execute(
        select(Warehouse).where(Warehouse.id == pr.delivery_warehouse_id)
    )
    warehouse = wh_result.scalar_one_or_none()

    # Determine inter-state
    is_inter_state = False
    if warehouse and vendor.gst_state_code:
        wh_state = getattr(warehouse, 'state_code', None)
        if wh_state and wh_state != vendor.gst_state_code:
            is_inter_state = True

    # Create PO
    po = PurchaseOrder(
        po_number=po_number,
        po_date=today,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        vendor_gstin=vendor.gstin,
        delivery_warehouse_id=pr.delivery_warehouse_id,
        requisition_id=pr.id,
        expected_delivery_date=pr.required_by_date or (today + datetime.timedelta(days=30)),
        created_by=current_user.id,
        subtotal=Decimal("0"),
        taxable_amount=Decimal("0"),
        grand_total=Decimal("0"),
    )
    db.add(po)
    await db.flush()

    # Create PO items from PR items with multi-delivery support
    subtotal = Decimal("0")
    total_discount = Decimal("0")
    taxable_amount = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    igst_total = Decimal("0")
    line_number = 0
    month_totals = {}

    for pr_item in pr.items:
        line_number += 1
        gst_rate = Decimal("18")  # Default GST

        # Calculate amounts
        gross_amount = pr_item.quantity_requested * pr_item.estimated_unit_price
        item_taxable = gross_amount  # No discount from PR

        # GST calculation
        if is_inter_state:
            igst_rate = gst_rate
            cgst_rate = Decimal("0")
            sgst_rate = Decimal("0")
        else:
            igst_rate = Decimal("0")
            cgst_rate = gst_rate / 2
            sgst_rate = gst_rate / 2

        cgst_amount = item_taxable * (cgst_rate / 100)
        sgst_amount = item_taxable * (sgst_rate / 100)
        igst_amount = item_taxable * (igst_rate / 100)
        item_total = item_taxable + cgst_amount + sgst_amount + igst_amount

        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            line_number=line_number,
            product_id=pr_item.product_id,
            variant_id=pr_item.variant_id,
            product_name=pr_item.product_name,
            sku=pr_item.sku,
            quantity_ordered=pr_item.quantity_requested,
            uom=pr_item.uom,
            unit_price=pr_item.estimated_unit_price,
            taxable_amount=item_taxable,
            gst_rate=gst_rate,
            cgst_rate=cgst_rate,
            sgst_rate=sgst_rate,
            igst_rate=igst_rate,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount,
            total_amount=item_total,
            # Multi-delivery: carry over monthly_quantities from PR item
            monthly_quantities=pr_item.monthly_quantities,
        )
        db.add(po_item)

        subtotal += gross_amount
        taxable_amount += item_taxable
        cgst_total += cgst_amount
        sgst_total += sgst_amount
        igst_total += igst_amount

        # Collect month totals for delivery schedules
        if pr_item.monthly_quantities:
            for month_code, qty in pr_item.monthly_quantities.items():
                if month_code not in month_totals:
                    month_totals[month_code] = {"qty": 0, "value": Decimal("0"), "tax": Decimal("0")}
                item_value = qty * pr_item.estimated_unit_price
                item_tax = item_value * (gst_rate / 100)
                month_totals[month_code]["qty"] += qty
                month_totals[month_code]["value"] += item_value
                month_totals[month_code]["tax"] += item_tax

    # Update PO totals
    total_tax = cgst_total + sgst_total + igst_total
    grand_total = taxable_amount + total_tax

    po.subtotal = subtotal
    po.taxable_amount = taxable_amount
    po.cgst_amount = cgst_total
    po.sgst_amount = sgst_total
    po.igst_amount = igst_total
    po.total_tax = total_tax
    po.grand_total = grand_total

    # Create delivery schedules from monthly_quantities
    if month_totals:
        from calendar import monthrange

        # Get the last serial number from all previous delivery schedules
        last_serial_result = await db.execute(
            select(func.max(PODeliverySchedule.serial_number_end))
        )
        last_serial = last_serial_result.scalar() or 0
        current_serial = last_serial

        sorted_months = sorted(month_totals.keys())
        lot_number = 0

        for month_code in sorted_months:
            lot_number += 1
            month_data = month_totals[month_code]

            year, month = int(month_code.split("-")[0]), int(month_code.split("-")[1])
            expected_date = date(year, month, 15)
            window_start = date(year, month, 10)
            last_day = monthrange(year, month)[1]
            window_end = date(year, month, min(20, last_day))

            lot_value = month_data["value"]
            lot_tax = month_data["tax"]
            lot_total = lot_value + lot_tax

            month_names = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            lot_name = f"{month_names[month]} {year}"

            # Calculate serial number range for this lot
            lot_qty = month_data["qty"]
            serial_start = current_serial + 1
            serial_end = current_serial + lot_qty
            current_serial = serial_end

            delivery_schedule = PODeliverySchedule(
                purchase_order_id=po.id,
                lot_number=lot_number,
                lot_name=lot_name,
                month_code=month_code,
                expected_delivery_date=expected_date,
                delivery_window_start=window_start,
                delivery_window_end=window_end,
                total_quantity=lot_qty,
                lot_value=lot_value,
                lot_tax=lot_tax,
                lot_total=lot_total,
                status=DeliveryLotStatus.PENDING,
                serial_number_start=serial_start,
                serial_number_end=serial_end,
            )
            db.add(delivery_schedule)

    # Mark PR as converted
    pr.status = RequisitionStatus.CONVERTED
    pr.converted_to_po_id = po.id

    await db.commit()

    # Load full PO with items and delivery schedules
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po.id)
    )
    po = result.scalar_one()

    return po


# ==================== Purchase Order (PO) ====================

@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new Purchase Order."""
    # Verify vendor
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == po_in.vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Generate PO number
    today = date.today()
    count_result = await db.execute(
        select(func.count(PurchaseOrder.id)).where(
            func.date(PurchaseOrder.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    po_number = f"PO-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Determine if inter-state (for IGST)
    # Get warehouse state
    wh_result = await db.execute(
        select(Warehouse).where(Warehouse.id == po_in.delivery_warehouse_id)
    )
    warehouse = wh_result.scalar_one_or_none()

    is_inter_state = False
    if warehouse and vendor.gst_state_code:
        # Compare state codes (first 2 digits of GSTIN)
        wh_state = getattr(warehouse, 'state_code', None)
        if wh_state and wh_state != vendor.gst_state_code:
            is_inter_state = True

    # Prepare Bill To (from input or default to company details)
    bill_to = po_in.bill_to
    if not bill_to:
        # Fetch company details for Bill To
        from sqlalchemy import text
        company_result = await db.execute(text("""
            SELECT legal_name, gstin, state_code, address_line1, address_line2,
                   city, state, pincode, email, phone
            FROM companies LIMIT 1
        """))
        company_row = company_result.fetchone()
        if company_row:
            bill_to = {
                "name": company_row[0],
                "gstin": company_row[1],
                "state_code": company_row[2],
                "address_line1": company_row[3],
                "address_line2": company_row[4],
                "city": company_row[5],
                "state": company_row[6],
                "pincode": company_row[7],
                "email": company_row[8],
                "phone": company_row[9],
            }

    # Prepare Ship To (from input or default to warehouse address)
    ship_to = po_in.ship_to
    if not ship_to and warehouse:
        ship_to = {
            "name": warehouse.name,
            "address_line1": getattr(warehouse, 'address_line1', None),
            "address_line2": getattr(warehouse, 'address_line2', None),
            "city": getattr(warehouse, 'city', None),
            "state": getattr(warehouse, 'state', None),
            "pincode": getattr(warehouse, 'pincode', None),
            "state_code": getattr(warehouse, 'state_code', None),
            "gstin": bill_to.get('gstin') if bill_to else None,  # Same GSTIN as buyer
        }

    # Create PO with initial zero values for NOT NULL fields
    po = PurchaseOrder(
        po_number=po_number,
        po_date=today,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        vendor_gstin=vendor.gstin,
        delivery_warehouse_id=po_in.delivery_warehouse_id,
        requisition_id=po_in.requisition_id,
        expected_delivery_date=po_in.expected_delivery_date,
        delivery_address=po_in.delivery_address,
        bill_to=bill_to,
        ship_to=ship_to,
        payment_terms=po_in.payment_terms,
        credit_days=po_in.credit_days,
        advance_required=po_in.advance_required,
        quotation_reference=po_in.quotation_reference,
        quotation_date=po_in.quotation_date,
        freight_charges=po_in.freight_charges,
        packing_charges=po_in.packing_charges,
        other_charges=po_in.other_charges,
        terms_and_conditions=po_in.terms_and_conditions,
        special_instructions=po_in.special_instructions,
        internal_notes=po_in.internal_notes,
        created_by=current_user.id,
        # Initialize NOT NULL fields with zero
        subtotal=Decimal("0"),
        taxable_amount=Decimal("0"),
        grand_total=Decimal("0"),
    )

    db.add(po)
    await db.flush()

    # Create PO items and calculate totals
    subtotal = Decimal("0")
    total_discount = Decimal("0")
    taxable_amount = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    igst_total = Decimal("0")
    cess_total = Decimal("0")
    line_number = 0

    for item_data in po_in.items:
        line_number += 1

        # Calculate item amounts
        gross_amount = item_data.quantity_ordered * item_data.unit_price
        discount_amount = gross_amount * (item_data.discount_percentage / 100)
        item_taxable = gross_amount - discount_amount

        # GST calculation
        gst_rate = item_data.gst_rate
        if is_inter_state:
            igst_rate = gst_rate
            cgst_rate = Decimal("0")
            sgst_rate = Decimal("0")
        else:
            igst_rate = Decimal("0")
            cgst_rate = gst_rate / 2
            sgst_rate = gst_rate / 2

        cgst_amount = item_taxable * (cgst_rate / 100)
        sgst_amount = item_taxable * (sgst_rate / 100)
        igst_amount = item_taxable * (igst_rate / 100)
        cess_amount = Decimal("0")  # Can be added if needed

        item_total = item_taxable + cgst_amount + sgst_amount + igst_amount + cess_amount

        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            line_number=line_number,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            product_name=item_data.product_name,
            sku=item_data.sku,
            hsn_code=item_data.hsn_code,
            quantity_ordered=item_data.quantity_ordered,
            uom=item_data.uom,
            unit_price=item_data.unit_price,
            discount_percentage=item_data.discount_percentage,
            discount_amount=discount_amount,
            taxable_amount=item_taxable,
            gst_rate=gst_rate,
            cgst_rate=cgst_rate,
            sgst_rate=sgst_rate,
            igst_rate=igst_rate,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount,
            cess_amount=cess_amount,
            total_amount=item_total,
            expected_date=item_data.expected_date,
            notes=item_data.notes,
            # Month-wise quantity breakdown for multi-delivery POs
            monthly_quantities=item_data.monthly_quantities,
        )
        db.add(item)

        subtotal += gross_amount
        total_discount += discount_amount
        taxable_amount += item_taxable
        cgst_total += cgst_amount
        sgst_total += sgst_amount
        igst_total += igst_amount
        cess_total += cess_amount

    # Update PO totals
    total_tax = cgst_total + sgst_total + igst_total + cess_total
    grand_total = (
        taxable_amount + total_tax +
        po_in.freight_charges + po_in.packing_charges + po_in.other_charges
    )

    po.subtotal = subtotal
    po.discount_amount = total_discount
    po.taxable_amount = taxable_amount
    po.cgst_amount = cgst_total
    po.sgst_amount = sgst_total
    po.igst_amount = igst_total
    po.cess_amount = cess_total
    po.total_tax = total_tax
    po.grand_total = grand_total

    # Create delivery schedules (lot-wise) from monthly_quantities
    # Collect all months and calculate per-month values
    month_totals = {}  # {month_code: {qty: X, value: Y, tax: Z}}

    for item_data in po_in.items:
        if item_data.monthly_quantities:
            item_unit_price = item_data.unit_price * (1 - item_data.discount_percentage / 100)
            gst_multiplier = 1 + (item_data.gst_rate / 100)

            for month_code, qty in item_data.monthly_quantities.items():
                if month_code not in month_totals:
                    month_totals[month_code] = {"qty": 0, "value": Decimal("0"), "tax": Decimal("0")}

                item_value = qty * item_unit_price
                item_tax = item_value * (item_data.gst_rate / 100)

                month_totals[month_code]["qty"] += qty
                month_totals[month_code]["value"] += item_value
                month_totals[month_code]["tax"] += item_tax

    # Create PODeliverySchedule for each month
    if month_totals:
        from datetime import timedelta
        from calendar import monthrange
        from sqlalchemy import func

        # Get the last serial number from all previous delivery schedules
        # Serial numbers are global across all POs and continue from the last used
        last_serial_result = await db.execute(
            select(func.max(PODeliverySchedule.serial_number_end))
        )
        last_serial = last_serial_result.scalar() or 0  # Start from 0 if no previous serials

        sorted_months = sorted(month_totals.keys())
        lot_number = 0
        current_serial = last_serial  # Track running serial number

        for month_code in sorted_months:
            lot_number += 1
            month_data = month_totals[month_code]

            # Parse month_code (YYYY-MM) to date
            year, month = int(month_code.split("-")[0]), int(month_code.split("-")[1])
            # Expected delivery: 15th of the month
            expected_date = date(year, month, 15)
            # Delivery window: 10th to 20th of the month
            window_start = date(year, month, 10)
            last_day = monthrange(year, month)[1]
            window_end = date(year, month, min(20, last_day))

            lot_value = month_data["value"]
            lot_tax = month_data["tax"]
            lot_total = lot_value + lot_tax

            # Calculate advance (default 25%) and balance
            advance_percentage = po_in.advance_required if po_in.advance_required > 0 else Decimal("25")
            advance_amount = lot_total * (advance_percentage / 100)
            balance_amount = lot_total - advance_amount

            # Balance due 45 days after delivery
            balance_due_date = expected_date + timedelta(days=po_in.credit_days)

            # Generate lot name (e.g., "JAN 2026")
            month_names = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            lot_name = f"{month_names[month]} {year}"

            # Calculate serial number range for this lot
            lot_qty = month_data["qty"]
            serial_start = current_serial + 1
            serial_end = current_serial + lot_qty
            current_serial = serial_end  # Update for next lot

            delivery_schedule = PODeliverySchedule(
                purchase_order_id=po.id,
                lot_number=lot_number,
                lot_name=lot_name,
                month_code=month_code,
                expected_delivery_date=expected_date,
                delivery_window_start=window_start,
                delivery_window_end=window_end,
                total_quantity=lot_qty,
                lot_value=lot_value,
                lot_tax=lot_tax,
                lot_total=lot_total,
                advance_percentage=advance_percentage,
                advance_amount=advance_amount,
                balance_amount=balance_amount,
                balance_due_days=po_in.credit_days,
                balance_due_date=balance_due_date,
                status=DeliveryLotStatus.PENDING,
                # Serial number range for this lot
                serial_number_start=serial_start,
                serial_number_end=serial_end,
            )
            db.add(delivery_schedule)

    # If created from PR, update PR status
    if po_in.requisition_id:
        pr_result = await db.execute(
            select(PurchaseRequisition).where(PurchaseRequisition.id == po_in.requisition_id)
        )
        pr = pr_result.scalar_one_or_none()
        if pr:
            pr.status = RequisitionStatus.CONVERTED
            pr.converted_to_po_id = po.id

    await db.commit()

    # Load full PO with items and delivery schedules
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po.id)
    )
    po = result.scalar_one()

    return po


@router.get("/orders", response_model=POListResponse)
async def list_purchase_orders(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[POStatus] = None,
    vendor_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List purchase orders."""
    query = select(PurchaseOrder)
    count_query = select(func.count(PurchaseOrder.id))
    total_value_query = select(func.coalesce(func.sum(PurchaseOrder.grand_total), 0))

    filters = []
    if status:
        filters.append(PurchaseOrder.status == status)
    if vendor_id:
        filters.append(PurchaseOrder.vendor_id == vendor_id)
    if warehouse_id:
        filters.append(PurchaseOrder.delivery_warehouse_id == warehouse_id)
    if start_date:
        filters.append(PurchaseOrder.po_date >= start_date)
    if end_date:
        filters.append(PurchaseOrder.po_date <= end_date)
    if search:
        filters.append(or_(
            PurchaseOrder.po_number.ilike(f"%{search}%"),
            PurchaseOrder.vendor_name.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
        total_value_query = total_value_query.where(and_(*filters))

    # Get totals
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    value_result = await db.execute(total_value_query)
    total_value = value_result.scalar() or Decimal("0")

    # Get paginated results
    query = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    pos = result.scalars().all()

    return POListResponse(
        items=[POBrief.model_validate(po) for po in pos],
        total=total,
        total_value=total_value,
        skip=skip,
        limit=limit
    )


@router.get("/orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    return po


@router.delete("/orders/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete a purchase order. Only DRAFT or REJECTED POs can be deleted."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # Only allow deletion of DRAFT or CANCELLED POs
    allowed_statuses = [POStatus.DRAFT, POStatus.CANCELLED]
    if po.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete PO with status '{po.status.value}'. Only DRAFT or CANCELLED POs can be deleted."
        )

    # Delete PO items first (cascade should handle this, but being explicit)
    await db.execute(
        delete(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po_id)
    )

    # Delete the PO
    await db.execute(
        delete(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )

    await db.commit()
    return None


@router.post("/orders/{po_id}/approve", response_model=PurchaseOrderResponse)
async def approve_purchase_order(
    po_id: UUID,
    request: POApproveRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot {request.action.lower()} PO in {po.status.value} status"
        )

    if request.action == "APPROVE":
        po.status = POStatus.APPROVED
        po.approved_by = current_user.id
        po.approved_at = datetime.utcnow()
        # Update all delivery schedules to ADVANCE_PENDING status
        for schedule in po.delivery_schedules:
            schedule.status = DeliveryLotStatus.ADVANCE_PENDING
    else:
        po.status = POStatus.CANCELLED
        # Cancel all delivery schedules
        for schedule in po.delivery_schedules:
            schedule.status = DeliveryLotStatus.CANCELLED

    await db.commit()
    await db.refresh(po)

    return po


@router.post("/orders/{po_id}/send", response_model=PurchaseOrderResponse)
async def send_po_to_vendor(
    po_id: UUID,
    request: POSendToVendorRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Send PO to vendor (via email/portal). Auto-generates serial numbers."""
    from app.services.serialization import SerializationService
    from app.schemas.serialization import GenerateSerialsRequest, GenerateSerialItem, ItemType
    from app.models.serialization import POSerial, ModelCodeReference

    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    if po.status not in [POStatus.APPROVED, POStatus.SENT_TO_VENDOR]:
        raise HTTPException(
            status_code=400,
            detail="PO must be approved before sending to vendor"
        )

    # Get vendor details to find supplier code
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == po.vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()

    # Default supplier code - check if vendor has a code assigned
    from app.models.serialization import SupplierCode
    supplier_code = "AP"  # Default to Aquapurite

    if vendor:
        # Try to find supplier code for this vendor
        supplier_code_result = await db.execute(
            select(SupplierCode).where(SupplierCode.vendor_id == str(vendor.id))
        )
        supplier_code_obj = supplier_code_result.scalar_one_or_none()
        if supplier_code_obj:
            supplier_code = supplier_code_obj.code

    # Check if serials already exist for this PO
    existing_serials = await db.execute(
        select(func.count(POSerial.id)).where(POSerial.po_id == str(po.id))
    )
    existing_count = existing_serials.scalar() or 0

    serials_generated = 0
    serial_summaries = []

    # Only generate serials if none exist
    if existing_count == 0 and po.items:
        serial_service = SerializationService(db)

        # Build items for serial generation
        serial_items = []
        for item in po.items:
            # Try to get model code from ModelCodeReference by product_id or SKU
            model_code = None
            item_type = ItemType.FINISHED_GOODS

            if item.product_id:
                ref_result = await db.execute(
                    select(ModelCodeReference).where(
                        ModelCodeReference.product_id == str(item.product_id)
                    )
                )
                ref = ref_result.scalar_one_or_none()
                if ref:
                    model_code = ref.model_code
                    item_type = ref.item_type

            if not model_code and item.sku:
                # Try by SKU
                ref_result = await db.execute(
                    select(ModelCodeReference).where(
                        ModelCodeReference.product_sku == item.sku
                    )
                )
                ref = ref_result.scalar_one_or_none()
                if ref:
                    model_code = ref.model_code
                    item_type = ref.item_type

            if not model_code:
                # Generate model code from product name (first 3 letters)
                product_name = item.product_name or item.sku or "UNK"
                # Remove common prefixes and get first 3 alphabetic characters
                clean_name = ''.join(c for c in product_name if c.isalpha())
                model_code = clean_name[:3].upper() if len(clean_name) >= 3 else clean_name.upper().ljust(3, 'X')

            serial_items.append(GenerateSerialItem(
                po_item_id=str(item.id),
                product_id=str(item.product_id) if item.product_id else None,
                product_sku=item.sku,
                model_code=model_code,
                quantity=item.quantity_ordered,
                item_type=item_type,
            ))

        if serial_items:
            try:
                gen_request = GenerateSerialsRequest(
                    po_id=str(po.id),
                    supplier_code=supplier_code,
                    items=serial_items,
                )
                gen_result = await serial_service.generate_serials_for_po(gen_request)
                serials_generated = gen_result.total_generated
                serial_summaries = gen_result.items

                # Mark as sent to vendor
                await serial_service.mark_serials_sent_to_vendor(str(po.id))
            except Exception as e:
                # Log error but don't fail the send operation
                print(f"Warning: Failed to generate serials for PO {po.po_number}: {e}")

    po.status = POStatus.SENT_TO_VENDOR
    po.sent_to_vendor_at = datetime.utcnow()

    await db.commit()
    await db.refresh(po)

    return po


@router.post("/orders/{po_id}/confirm", response_model=PurchaseOrderResponse)
async def confirm_purchase_order(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Mark PO as confirmed by vendor."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    po.status = POStatus.CONFIRMED
    po.vendor_acknowledged_at = datetime.utcnow()

    await db.commit()
    await db.refresh(po)

    return po


# ==================== Delivery Schedule (Lot-wise Payment) ====================

@router.get("/orders/{po_id}/schedules", response_model=List[PODeliveryScheduleResponse])
async def get_delivery_schedules(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get delivery schedules for a PO."""
    result = await db.execute(
        select(PODeliverySchedule)
        .where(PODeliverySchedule.purchase_order_id == po_id)
        .order_by(PODeliverySchedule.lot_number)
    )
    schedules = result.scalars().all()

    return schedules


@router.post("/orders/{po_id}/schedules/{lot_id}/payment", response_model=PODeliveryScheduleResponse)
async def record_lot_payment(
    po_id: UUID,
    lot_id: UUID,
    payment: PODeliveryPaymentRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Record advance or balance payment for a delivery lot."""
    result = await db.execute(
        select(PODeliverySchedule)
        .where(
            PODeliverySchedule.id == lot_id,
            PODeliverySchedule.purchase_order_id == po_id
        )
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Delivery schedule not found")

    if payment.payment_type == "ADVANCE":
        if schedule.status not in [DeliveryLotStatus.PENDING, DeliveryLotStatus.ADVANCE_PENDING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot record advance payment for lot in {schedule.status.value} status"
            )

        schedule.advance_paid = payment.amount
        schedule.advance_paid_date = payment.payment_date
        schedule.advance_payment_ref = payment.payment_reference
        schedule.status = DeliveryLotStatus.ADVANCE_PAID

    elif payment.payment_type == "BALANCE":
        if schedule.status not in [DeliveryLotStatus.DELIVERED, DeliveryLotStatus.PAYMENT_PENDING]:
            raise HTTPException(
                status_code=400,
                detail=f"Balance payment can only be recorded after delivery. Current status: {schedule.status.value}"
            )

        schedule.balance_paid = payment.amount
        schedule.balance_paid_date = payment.payment_date
        schedule.balance_payment_ref = payment.payment_reference
        schedule.status = DeliveryLotStatus.COMPLETED

    await db.commit()
    await db.refresh(schedule)

    return schedule


@router.post("/orders/{po_id}/schedules/{lot_id}/delivered", response_model=PODeliveryScheduleResponse)
async def mark_lot_delivered(
    po_id: UUID,
    lot_id: UUID,
    delivery_date: date,
    db: DB,
    current_user: CurrentUser,
    grn_id: Optional[UUID] = None,
):
    """Mark a delivery lot as delivered."""
    result = await db.execute(
        select(PODeliverySchedule)
        .where(
            PODeliverySchedule.id == lot_id,
            PODeliverySchedule.purchase_order_id == po_id
        )
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Delivery schedule not found")

    if schedule.status != DeliveryLotStatus.ADVANCE_PAID:
        raise HTTPException(
            status_code=400,
            detail=f"Lot must have advance paid before marking as delivered. Current status: {schedule.status.value}"
        )

    from datetime import timedelta

    schedule.actual_delivery_date = delivery_date
    schedule.grn_id = grn_id
    schedule.status = DeliveryLotStatus.PAYMENT_PENDING
    schedule.balance_due_date = delivery_date + timedelta(days=schedule.balance_due_days)

    await db.commit()
    await db.refresh(schedule)

    return schedule


# ==================== Serial Number Preview ====================

@router.get("/orders/next-serial")
async def get_next_serial_number(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Get the next available serial number for PO delivery schedules.
    Used for preview in PO creation form.
    """
    last_serial_result = await db.execute(
        select(func.max(PODeliverySchedule.serial_number_end))
    )
    last_serial = last_serial_result.scalar() or 0
    next_serial = last_serial + 1

    return {
        "last_serial": last_serial,
        "next_serial": next_serial,
        "message": f"Next available serial starts from {next_serial}"
    }


# ==================== Goods Receipt Note (GRN) ====================

@router.post("/grn", response_model=GoodsReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_grn(
    grn_in: GoodsReceiptCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a Goods Receipt Note against a PO."""
    # Verify PO
    po_result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == grn_in.purchase_order_id)
    )
    po = po_result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    if po.status not in [POStatus.CONFIRMED, POStatus.PARTIAL]:
        raise HTTPException(
            status_code=400,
            detail="PO must be confirmed before receiving goods"
        )

    # Generate GRN number
    today = date.today()
    count_result = await db.execute(
        select(func.count(GoodsReceiptNote.id)).where(
            func.date(GoodsReceiptNote.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    grn_number = f"GRN-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Create GRN
    grn = GoodsReceiptNote(
        grn_number=grn_number,
        grn_date=grn_in.grn_date,
        purchase_order_id=po.id,
        vendor_id=po.vendor_id,
        warehouse_id=grn_in.warehouse_id,
        vendor_challan_number=grn_in.vendor_challan_number,
        vendor_challan_date=grn_in.vendor_challan_date,
        transporter_name=grn_in.transporter_name,
        vehicle_number=grn_in.vehicle_number,
        lr_number=grn_in.lr_number,
        e_way_bill_number=grn_in.e_way_bill_number,
        qc_required=grn_in.qc_required,
        receiving_remarks=grn_in.receiving_remarks,
        received_by=current_user.id,
        created_by=current_user.id,
    )

    db.add(grn)
    await db.flush()

    # Create GRN items
    total_received = 0
    total_accepted = 0
    total_rejected = 0
    total_value = Decimal("0")

    for item_data in grn_in.items:
        # Get PO item for unit price
        po_item_result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_data.po_item_id)
        )
        po_item = po_item_result.scalar_one_or_none()
        if not po_item:
            raise HTTPException(status_code=400, detail=f"PO item {item_data.po_item_id} not found")

        # Validate quantity - prevent over-receiving
        pending_qty = po_item.quantity_ordered - po_item.quantity_received
        if item_data.quantity_received > pending_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot receive {item_data.quantity_received} units for {po_item.product_name}. "
                       f"PO ordered: {po_item.quantity_ordered}, "
                       f"Already received: {po_item.quantity_received}, "
                       f"Pending: {pending_qty} units"
            )

        unit_price = po_item.unit_price
        accepted_value = item_data.quantity_accepted * unit_price

        grn_item = GRNItem(
            grn_id=grn.id,
            po_item_id=item_data.po_item_id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            product_name=item_data.product_name,
            sku=item_data.sku,
            quantity_expected=item_data.quantity_expected,
            quantity_received=item_data.quantity_received,
            quantity_accepted=item_data.quantity_accepted,
            quantity_rejected=item_data.quantity_rejected,
            uom=item_data.uom,
            unit_price=unit_price,
            accepted_value=accepted_value,
            batch_number=item_data.batch_number,
            manufacturing_date=item_data.manufacturing_date,
            expiry_date=item_data.expiry_date,
            serial_numbers=item_data.serial_numbers,
            bin_id=item_data.bin_id,
            bin_location=item_data.bin_location,
            rejection_reason=item_data.rejection_reason,
            remarks=item_data.remarks,
        )
        db.add(grn_item)

        total_received += item_data.quantity_received
        total_accepted += item_data.quantity_accepted
        total_rejected += item_data.quantity_rejected
        total_value += accepted_value

        # Update PO item quantities
        po_item.quantity_received += item_data.quantity_received
        po_item.quantity_accepted += item_data.quantity_accepted
        po_item.quantity_rejected += item_data.quantity_rejected
        po_item.quantity_pending = po_item.quantity_ordered - po_item.quantity_received

        if po_item.quantity_pending <= 0:
            po_item.is_closed = True

    # Update GRN totals
    grn.total_items = len(grn_in.items)
    grn.total_quantity_received = total_received
    grn.total_quantity_accepted = total_accepted
    grn.total_quantity_rejected = total_rejected
    grn.total_value = total_value

    # Update PO status
    all_closed = all(item.is_closed for item in po.items)
    if all_closed:
        po.status = POStatus.FULLY_RECEIVED
    else:
        po.status = POStatus.PARTIAL

    po.total_received_value += total_value

    # Skip QC if not required
    if not grn_in.qc_required:
        grn.status = GRNStatus.PENDING_PUTAWAY
        grn.qc_status = QualityCheckResult.ACCEPTED

    await db.commit()

    # Load full GRN
    result = await db.execute(
        select(GoodsReceiptNote)
        .options(selectinload(GoodsReceiptNote.items))
        .where(GoodsReceiptNote.id == grn.id)
    )
    grn = result.scalar_one()

    return grn


@router.get("/grn", response_model=GRNListResponse)
async def list_grns(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[GRNStatus] = None,
    vendor_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    po_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """List Goods Receipt Notes."""
    query = select(GoodsReceiptNote)
    count_query = select(func.count(GoodsReceiptNote.id))
    value_query = select(func.coalesce(func.sum(GoodsReceiptNote.total_value), 0))

    filters = []
    if status:
        filters.append(GoodsReceiptNote.status == status)
    if vendor_id:
        filters.append(GoodsReceiptNote.vendor_id == vendor_id)
    if warehouse_id:
        filters.append(GoodsReceiptNote.warehouse_id == warehouse_id)
    if po_id:
        filters.append(GoodsReceiptNote.purchase_order_id == po_id)
    if start_date:
        filters.append(GoodsReceiptNote.grn_date >= start_date)
    if end_date:
        filters.append(GoodsReceiptNote.grn_date <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
        value_query = value_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_value_result = await db.execute(value_query)
    total_value = total_value_result.scalar() or Decimal("0")

    query = query.order_by(GoodsReceiptNote.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    grns = result.scalars().all()

    # Get PO numbers and vendor names for brief response
    items = []
    for grn in grns:
        # Get PO number
        po_result = await db.execute(
            select(PurchaseOrder.po_number).where(PurchaseOrder.id == grn.purchase_order_id)
        )
        po_number = po_result.scalar() or ""

        # Get vendor name
        vendor_result = await db.execute(
            select(Vendor.name).where(Vendor.id == grn.vendor_id)
        )
        vendor_name = vendor_result.scalar() or ""

        items.append(GRNBrief(
            id=grn.id,
            grn_number=grn.grn_number,
            grn_date=grn.grn_date,
            po_number=po_number,
            vendor_name=vendor_name,
            status=grn.status,
            total_quantity_received=grn.total_quantity_received,
            total_value=grn.total_value,
        ))

    return GRNListResponse(
        items=items,
        total=total,
        total_value=total_value,
        skip=skip,
        limit=limit
    )


@router.get("/grn/{grn_id}", response_model=GoodsReceiptResponse)
async def get_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get GRN by ID."""
    result = await db.execute(
        select(GoodsReceiptNote)
        .options(selectinload(GoodsReceiptNote.items))
        .where(GoodsReceiptNote.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    return grn


@router.post("/grn/{grn_id}/qc", response_model=GoodsReceiptResponse)
async def process_grn_quality_check(
    grn_id: UUID,
    qc_request: GRNQualityCheckRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Process quality check for GRN items."""
    result = await db.execute(
        select(GoodsReceiptNote)
        .options(selectinload(GoodsReceiptNote.items))
        .where(GoodsReceiptNote.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    if grn.status != GRNStatus.PENDING_QC:
        raise HTTPException(status_code=400, detail="GRN is not pending QC")

    # Process each item's QC result
    all_accepted = True
    all_rejected = True

    for item_result in qc_request.item_results:
        item_id = item_result.get("item_id")
        qc_result = item_result.get("qc_result")
        rejection_reason = item_result.get("rejection_reason")

        # Find the GRN item
        item_query = await db.execute(
            select(GRNItem).where(GRNItem.id == UUID(item_id))
        )
        item = item_query.scalar_one_or_none()
        if item:
            item.qc_result = QualityCheckResult(qc_result)
            if rejection_reason:
                item.rejection_reason = rejection_reason

            if item.qc_result == QualityCheckResult.ACCEPTED:
                all_rejected = False
            elif item.qc_result == QualityCheckResult.REJECTED:
                all_accepted = False
                # Update accepted quantity to 0 if rejected
                item.quantity_accepted = 0
                item.quantity_rejected = item.quantity_received
            else:  # PARTIAL
                all_accepted = False
                all_rejected = False

    # Set overall QC status
    if all_accepted:
        grn.qc_status = QualityCheckResult.ACCEPTED
    elif all_rejected:
        grn.qc_status = QualityCheckResult.REJECTED
    else:
        grn.qc_status = QualityCheckResult.PARTIAL

    grn.qc_done_by = current_user.id
    grn.qc_done_at = datetime.utcnow()
    grn.qc_remarks = qc_request.overall_remarks
    grn.status = GRNStatus.PENDING_PUTAWAY

    await db.commit()
    await db.refresh(grn)

    return grn


@router.post("/grn/{grn_id}/putaway", response_model=GoodsReceiptResponse)
async def process_grn_putaway(
    grn_id: UUID,
    putaway_request: GRNPutAwayRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Process put-away for GRN items (add to inventory)."""
    result = await db.execute(
        select(GoodsReceiptNote)
        .options(selectinload(GoodsReceiptNote.items))
        .where(GoodsReceiptNote.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    if grn.status != GRNStatus.PENDING_PUTAWAY:
        raise HTTPException(status_code=400, detail="GRN is not pending put-away")

    # Process each item location
    for loc_data in putaway_request.item_locations:
        item_id = loc_data.get("item_id")
        bin_id = loc_data.get("bin_id")
        bin_location = loc_data.get("bin_location")

        item_query = await db.execute(
            select(GRNItem).where(GRNItem.id == UUID(item_id))
        )
        item = item_query.scalar_one_or_none()

        if item and item.quantity_accepted > 0:
            item.bin_id = UUID(bin_id) if bin_id else None
            item.bin_location = bin_location

            # Create stock items for accepted quantity
            for i in range(item.quantity_accepted):
                serial = None
                if item.serial_numbers and i < len(item.serial_numbers):
                    serial = item.serial_numbers[i]

                stock_item = StockItem(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    warehouse_id=grn.warehouse_id,
                    sku=item.sku,
                    serial_number=serial,
                    batch_number=item.batch_number,
                    manufacturing_date=item.manufacturing_date,
                    expiry_date=item.expiry_date,
                    status=StockItemStatus.AVAILABLE,
                    purchase_price=item.unit_price,
                    grn_id=grn.id,
                    grn_item_id=item.id,
                    bin_id=item.bin_id,
                    created_by=current_user.id,
                )
                db.add(stock_item)

            # Update inventory summary
            summary_result = await db.execute(
                select(InventorySummary).where(
                    and_(
                        InventorySummary.product_id == item.product_id,
                        InventorySummary.warehouse_id == grn.warehouse_id,
                    )
                )
            )
            summary = summary_result.scalar_one_or_none()

            if summary:
                summary.total_quantity += item.quantity_accepted
                summary.available_quantity += item.quantity_accepted
            else:
                summary = InventorySummary(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    warehouse_id=grn.warehouse_id,
                    total_quantity=item.quantity_accepted,
                    available_quantity=item.quantity_accepted,
                )
                db.add(summary)

            # Create stock movement record
            movement = StockMovement(
                product_id=item.product_id,
                variant_id=item.variant_id,
                warehouse_id=grn.warehouse_id,
                movement_type=StockMovementType.INWARD,
                quantity=item.quantity_accepted,
                reference_type="GRN",
                reference_id=grn.id,
                reference_number=grn.grn_number,
                unit_price=item.unit_price,
                total_value=item.accepted_value,
                notes=f"GRN Put-away from PO",
                created_by=current_user.id,
            )
            db.add(movement)

    # Update GRN status
    grn.status = GRNStatus.COMPLETED
    grn.put_away_complete = True
    grn.put_away_at = datetime.utcnow()

    await db.commit()
    await db.refresh(grn)

    # Post accounting entry for GRN
    try:
        from app.services.accounting_service import AccountingService
        accounting = AccountingService(db)

        # Get vendor name from PO
        vendor_name = grn.purchase_order.vendor.company_name if grn.purchase_order and grn.purchase_order.vendor else "Unknown Vendor"

        # Calculate tax amounts from GRN
        subtotal = grn.accepted_value or Decimal("0")
        cgst = grn.cgst_amount or Decimal("0")
        sgst = grn.sgst_amount or Decimal("0")
        igst = grn.igst_amount or Decimal("0")
        total = grn.total_value or subtotal

        await accounting.post_grn_entry(
            grn_id=grn.id,
            grn_number=grn.grn_number,
            vendor_name=vendor_name,
            subtotal=subtotal,
            cgst=cgst,
            sgst=sgst,
            igst=igst,
            total=total,
            is_interstate=igst > 0,
            product_type="purifier",
        )
        await db.commit()
    except Exception as e:
        import logging
        logging.warning(f"Failed to post accounting entry for GRN {grn.grn_number}: {e}")

    return grn


# ==================== Vendor Invoice & 3-Way Matching ====================

@router.post("/invoices", response_model=VendorInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor_invoice(
    invoice_in: VendorInvoiceCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Record a vendor invoice."""
    # Verify vendor
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == invoice_in.vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Check for duplicate invoice number
    dup_result = await db.execute(
        select(VendorInvoice).where(
            and_(
                VendorInvoice.vendor_id == invoice_in.vendor_id,
                VendorInvoice.invoice_number == invoice_in.invoice_number,
            )
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Invoice {invoice_in.invoice_number} already exists for this vendor"
        )

    # Generate our reference
    count_result = await db.execute(
        select(func.count(VendorInvoice.id))
    )
    count = count_result.scalar() or 0
    our_reference = f"VINV-{date.today().strftime('%Y%m')}-{str(count + 1).zfill(5)}"

    # Calculate amounts
    taxable_amount = invoice_in.subtotal - invoice_in.discount_amount
    total_tax = (
        invoice_in.cgst_amount + invoice_in.sgst_amount +
        invoice_in.igst_amount + invoice_in.cess_amount
    )

    # TDS calculation
    tds_amount = Decimal("0")
    if invoice_in.tds_applicable and invoice_in.tds_rate > 0:
        tds_amount = taxable_amount * (invoice_in.tds_rate / 100)

    net_payable = invoice_in.grand_total - tds_amount

    invoice = VendorInvoice(
        **invoice_in.model_dump(),
        our_reference=our_reference,
        taxable_amount=taxable_amount,
        total_tax=total_tax,
        tds_amount=tds_amount,
        net_payable=net_payable,
        balance_due=net_payable,
        received_by=current_user.id,
        received_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(invoice)

    # Create vendor ledger entry
    ledger_entry = VendorLedger(
        vendor_id=invoice_in.vendor_id,
        transaction_type=VendorTransactionType.INVOICE,
        transaction_date=invoice_in.invoice_date,
        due_date=invoice_in.due_date,
        reference_type="VENDOR_INVOICE",
        reference_number=our_reference,
        reference_id=invoice.id,
        vendor_invoice_number=invoice_in.invoice_number,
        vendor_invoice_date=invoice_in.invoice_date,
        credit_amount=net_payable,
        running_balance=vendor.current_balance + net_payable,
        narration=f"Vendor Invoice: {invoice_in.invoice_number}",
        created_by=current_user.id,
    )
    db.add(ledger_entry)

    # Update vendor balance
    vendor.current_balance += net_payable

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.get("/invoices", response_model=VendorInvoiceListResponse)
async def list_vendor_invoices(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[VendorInvoiceStatus] = None,
    vendor_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    overdue_only: bool = False,
    current_user: User = Depends(get_current_user),
):
    """List vendor invoices."""
    query = select(VendorInvoice)
    count_query = select(func.count(VendorInvoice.id))
    value_query = select(func.coalesce(func.sum(VendorInvoice.grand_total), 0))
    balance_query = select(func.coalesce(func.sum(VendorInvoice.balance_due), 0))

    filters = []
    if status:
        filters.append(VendorInvoice.status == status)
    if vendor_id:
        filters.append(VendorInvoice.vendor_id == vendor_id)
    if start_date:
        filters.append(VendorInvoice.invoice_date >= start_date)
    if end_date:
        filters.append(VendorInvoice.invoice_date <= end_date)
    if overdue_only:
        filters.append(VendorInvoice.due_date < date.today())
        filters.append(VendorInvoice.balance_due > 0)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
        value_query = value_query.where(and_(*filters))
        balance_query = balance_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_value_result = await db.execute(value_query)
    total_value = total_value_result.scalar() or Decimal("0")

    total_balance_result = await db.execute(balance_query)
    total_balance = total_balance_result.scalar() or Decimal("0")

    query = query.order_by(VendorInvoice.invoice_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    invoices = result.scalars().all()

    # Build brief responses with vendor names
    items = []
    for inv in invoices:
        vendor_result = await db.execute(
            select(Vendor.name).where(Vendor.id == inv.vendor_id)
        )
        vendor_name = vendor_result.scalar() or ""

        items.append(VendorInvoiceBrief(
            id=inv.id,
            our_reference=inv.our_reference,
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            vendor_name=vendor_name,
            grand_total=inv.grand_total,
            balance_due=inv.balance_due,
            due_date=inv.due_date,
            status=inv.status,
        ))

    return VendorInvoiceListResponse(
        items=items,
        total=total,
        total_value=total_value,
        total_balance=total_balance,
        skip=skip,
        limit=limit
    )


@router.post("/invoices/3way-match", response_model=ThreeWayMatchResponse)
async def perform_three_way_match(
    match_request: ThreeWayMatchRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Perform 3-way matching: PO ↔ GRN ↔ Invoice."""
    # Get PO
    po_result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == match_request.purchase_order_id)
    )
    po = po_result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # Get GRN
    grn_result = await db.execute(
        select(GoodsReceiptNote).where(GoodsReceiptNote.id == match_request.grn_id)
    )
    grn = grn_result.scalar_one_or_none()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    # Get Invoice
    invoice_result = await db.execute(
        select(VendorInvoice).where(VendorInvoice.id == match_request.vendor_invoice_id)
    )
    invoice = invoice_result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Vendor Invoice not found")

    # Perform matching
    po_total = po.grand_total
    grn_value = grn.total_value
    invoice_total = invoice.grand_total

    # Calculate variances
    variance_amount = abs(invoice_total - grn_value)
    variance_percentage = (variance_amount / grn_value * 100) if grn_value > 0 else Decimal("0")

    discrepancies = []
    recommendations = []

    # Check PO vs GRN
    if po.vendor_id != grn.vendor_id:
        discrepancies.append({"type": "vendor_mismatch", "message": "GRN vendor doesn't match PO vendor"})

    # Check PO vs Invoice
    if po.vendor_id != invoice.vendor_id:
        discrepancies.append({"type": "vendor_mismatch", "message": "Invoice vendor doesn't match PO vendor"})

    # Check GRN vs Invoice amounts
    if variance_percentage > match_request.tolerance_percentage:
        discrepancies.append({
            "type": "amount_variance",
            "message": f"Invoice amount ({invoice_total}) differs from GRN value ({grn_value}) by {variance_percentage:.2f}%",
            "grn_value": str(grn_value),
            "invoice_total": str(invoice_total),
        })
        recommendations.append("Review invoice line items against GRN received quantities")

    # Determine if matched
    is_matched = len(discrepancies) == 0

    if is_matched:
        # Update invoice status
        invoice.po_matched = True
        invoice.grn_matched = True
        invoice.is_fully_matched = True
        invoice.matching_variance = variance_amount
        invoice.status = VendorInvoiceStatus.VERIFIED
        invoice.verified_by = current_user.id
        invoice.verified_at = datetime.utcnow()

        recommendations.append("Invoice matched successfully. Ready for payment approval.")
    else:
        invoice.matching_variance = variance_amount
        invoice.variance_reason = "; ".join([d["message"] for d in discrepancies])

        if variance_percentage <= 5:
            recommendations.append("Minor variance detected. Consider manual override if acceptable.")
        else:
            recommendations.append("Significant variance. Contact vendor for clarification.")

    await db.commit()

    return ThreeWayMatchResponse(
        is_matched=is_matched,
        po_total=po_total,
        grn_value=grn_value,
        invoice_total=invoice_total,
        variance_amount=variance_amount,
        variance_percentage=variance_percentage,
        discrepancies=discrepancies,
        recommendations=recommendations,
    )


# ==================== Reports ====================

@router.get("/reports/pending-grn", response_model=List[PendingGRNResponse])
async def get_pending_grn_report(
    db: DB,
    vendor_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Get pending GRN report - POs awaiting goods receipt."""
    query = select(PurchaseOrder).options(
        selectinload(PurchaseOrder.items)
    ).where(
        PurchaseOrder.status.in_([POStatus.CONFIRMED, POStatus.PARTIAL])
    )

    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
    if warehouse_id:
        query = query.where(PurchaseOrder.delivery_warehouse_id == warehouse_id)

    result = await db.execute(query)
    pos = result.scalars().all()

    pending_list = []
    today = date.today()

    for po in pos:
        total_ordered = sum(item.quantity_ordered for item in po.items)
        total_received = sum(item.quantity_received for item in po.items)
        pending_qty = total_ordered - total_received

        if pending_qty > 0:
            # Calculate pending value
            pending_value = Decimal("0")
            for item in po.items:
                item_pending = item.quantity_ordered - item.quantity_received
                if item_pending > 0:
                    pending_value += item_pending * item.unit_price

            days_pending = (today - po.po_date).days

            pending_list.append(PendingGRNResponse(
                po_id=po.id,
                po_number=po.po_number,
                vendor_name=po.vendor_name,
                po_date=po.po_date,
                expected_date=po.expected_delivery_date,
                total_ordered=total_ordered,
                total_received=total_received,
                pending_quantity=pending_qty,
                pending_value=pending_value,
                days_pending=days_pending,
            ))

    return sorted(pending_list, key=lambda x: x.days_pending, reverse=True)


@router.get("/reports/po-summary", response_model=POSummaryResponse)
async def get_po_summary_report(
    start_date: date,
    end_date: date,
    db: DB,
    vendor_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
):
    """Get PO summary report for a date range."""
    base_filter = and_(
        PurchaseOrder.po_date >= start_date,
        PurchaseOrder.po_date <= end_date,
    )

    if vendor_id:
        base_filter = and_(base_filter, PurchaseOrder.vendor_id == vendor_id)
    if warehouse_id:
        base_filter = and_(base_filter, PurchaseOrder.delivery_warehouse_id == warehouse_id)

    # Total POs
    total_query = select(
        func.count(PurchaseOrder.id),
        func.coalesce(func.sum(PurchaseOrder.grand_total), 0)
    ).where(base_filter)
    total_result = await db.execute(total_query)
    total_row = total_result.one()

    # By status
    status_query = select(
        PurchaseOrder.status,
        func.count(PurchaseOrder.id),
        func.coalesce(func.sum(PurchaseOrder.grand_total), 0)
    ).where(base_filter).group_by(PurchaseOrder.status)
    status_result = await db.execute(status_query)
    status_data = {row[0].value: {"count": row[1], "value": float(row[2])} for row in status_result.all()}

    # By vendor
    vendor_query = select(
        PurchaseOrder.vendor_name,
        func.count(PurchaseOrder.id),
        func.coalesce(func.sum(PurchaseOrder.grand_total), 0)
    ).where(base_filter).group_by(PurchaseOrder.vendor_name)
    vendor_result = await db.execute(vendor_query)
    vendor_data = [
        {"vendor": row[0], "count": row[1], "value": float(row[2])}
        for row in vendor_result.all()
    ]

    # Categorize
    pending_statuses = [POStatus.DRAFT, POStatus.APPROVED, POStatus.SENT, POStatus.CONFIRMED]
    received_statuses = [POStatus.PARTIAL, POStatus.FULLY_RECEIVED, POStatus.CLOSED]
    cancelled_statuses = [POStatus.CANCELLED]

    pending_count = sum(status_data.get(s.value, {}).get("count", 0) for s in pending_statuses)
    pending_value = sum(status_data.get(s.value, {}).get("value", 0) for s in pending_statuses)
    received_count = sum(status_data.get(s.value, {}).get("count", 0) for s in received_statuses)
    received_value = sum(status_data.get(s.value, {}).get("value", 0) for s in received_statuses)
    cancelled_count = sum(status_data.get(s.value, {}).get("count", 0) for s in cancelled_statuses)
    cancelled_value = sum(status_data.get(s.value, {}).get("value", 0) for s in cancelled_statuses)

    return POSummaryResponse(
        period_start=start_date,
        period_end=end_date,
        total_po_count=total_row[0],
        total_po_value=Decimal(str(total_row[1])),
        pending_count=pending_count,
        pending_value=Decimal(str(pending_value)),
        received_count=received_count,
        received_value=Decimal(str(received_value)),
        cancelled_count=cancelled_count,
        cancelled_value=Decimal(str(cancelled_value)),
        by_vendor=vendor_data,
        by_status=status_data,
    )


# ==================== Document Downloads ====================

def _number_to_words(num: float) -> str:
    """Convert number to words for Indian currency."""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
            'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    if num == 0:
        return 'Zero'

    def words(n):
        if n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 else '')
        elif n < 1000:
            return ones[n // 100] + ' Hundred' + (' ' + words(n % 100) if n % 100 else '')
        elif n < 100000:
            return words(n // 1000) + ' Thousand' + (' ' + words(n % 1000) if n % 1000 else '')
        elif n < 10000000:
            return words(n // 100000) + ' Lakh' + (' ' + words(n % 100000) if n % 100000 else '')
        else:
            return words(n // 10000000) + ' Crore' + (' ' + words(n % 10000000) if n % 10000000 else '')

    rupees = int(num)
    paise = int(round((num - rupees) * 100))

    result = 'Rupees ' + words(rupees)
    if paise:
        result += ' and ' + words(paise) + ' Paise'
    return result + ' Only'


@router.get("/orders/{po_id}/download")
async def download_purchase_order(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Download Purchase Order as printable HTML (Multi-Delivery Template with Month-wise breakdown)."""
    from fastapi.responses import HTMLResponse
    from app.models.serialization import POSerial
    from app.models.company import Company

    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.delivery_schedules)
        )
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # Get company details
    company_result = await db.execute(select(Company).limit(1))
    company = company_result.scalar_one_or_none()

    # Get vendor details
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == po.vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()

    # Get warehouse details
    warehouse_result = await db.execute(
        select(Warehouse).where(Warehouse.id == po.delivery_warehouse_id)
    )
    warehouse = warehouse_result.scalar_one_or_none()

    # Get PO serials - grouped by model code for summary
    serials_result = await db.execute(
        select(
            POSerial.model_code,
            POSerial.item_type,
            func.count(POSerial.id).label('quantity'),
            func.min(POSerial.serial_number).label('start_serial'),
            func.max(POSerial.serial_number).label('end_serial'),
            func.min(POSerial.barcode).label('start_barcode'),
            func.max(POSerial.barcode).label('end_barcode'),
        )
        .where(POSerial.po_id == str(po.id))
        .group_by(POSerial.model_code, POSerial.item_type)
        .order_by(POSerial.model_code)
    )
    serial_groups = serials_result.all()
    total_serials = sum(sg.quantity for sg in serial_groups) if serial_groups else 0

    # Check if this is a multi-delivery PO (has monthly_quantities or delivery_schedules)
    has_monthly_breakdown = any(item.monthly_quantities for item in po.items)
    delivery_schedules = sorted(po.delivery_schedules, key=lambda x: x.lot_number) if po.delivery_schedules else []

    # Collect all unique months from all items
    all_months = set()
    for item in po.items:
        if item.monthly_quantities:
            all_months.update(item.monthly_quantities.keys())
    sorted_months = sorted(all_months) if all_months else []

    # Month name mapping for headers
    month_names_short = {
        "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
        "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"
    }

    # Build items table HTML
    items_html = ""
    subtotal = Decimal("0")
    total_qty = 0
    month_totals = {m: 0 for m in sorted_months}  # Track totals per month

    for idx, item in enumerate(po.items, 1):
        unit_price = Decimal(str(item.unit_price)) if item.unit_price else Decimal("0")
        amount = Decimal(str(item.quantity_ordered)) * unit_price
        subtotal += amount
        total_qty += item.quantity_ordered
        # Use SKU as item code (e.g., SP-SDF001)
        item_code = item.sku or '-'

        # Build month columns if multi-delivery
        month_cells = ""
        if has_monthly_breakdown and sorted_months:
            for month in sorted_months:
                qty = item.monthly_quantities.get(month, 0) if item.monthly_quantities else 0
                month_totals[month] += qty
                month_cells += f'<td class="text-center">{qty if qty > 0 else "-"}</td>'

        items_html += f"""
                <tr>
                    <td class="text-center">{idx}</td>
                    <td class="item-code">{item_code}</td>
                    <td>
                        <strong>{item.product_name or '-'}</strong>
                    </td>
                    <td class="text-center">{item.hsn_code or '84212190'}</td>
                    {month_cells}
                    <td class="text-center"><strong>{item.quantity_ordered}</strong></td>
                    <td class="text-center">{item.uom or 'Nos'}</td>
                    <td class="text-right">Rs. {float(unit_price):,.2f}</td>
                    <td class="text-right"><strong>Rs. {float(amount):,.2f}</strong></td>
                </tr>"""

    # Build total row with month totals
    month_total_cells = ""
    if has_monthly_breakdown and sorted_months:
        for month in sorted_months:
            month_total_cells += f'<td class="text-center"><strong>{month_totals[month]}</strong></td>'

    # Build month headers for table
    month_headers = ""
    if has_monthly_breakdown and sorted_months:
        for month in sorted_months:
            year_part = month.split("-")[0][-2:]  # Last 2 digits of year (e.g., "26")
            month_part = month.split("-")[1]
            month_name = month_names_short.get(month_part, month_part)
            month_headers += f'<th style="width:6%">{month_name} \'{year_part}</th>'

    # Build delivery schedule section HTML
    delivery_schedule_html = ""
    if delivery_schedules:
        schedule_rows = ""
        total_qty_sched = 0
        total_lot_value = Decimal("0")
        total_advance = Decimal("0")
        total_balance = Decimal("0")

        # Track total serial range
        first_serial = None
        last_serial = None

        for sched in delivery_schedules:
            total_qty_sched += sched.total_quantity
            total_lot_value += Decimal(str(sched.lot_total))
            total_advance += Decimal(str(sched.advance_amount))
            total_balance += Decimal(str(sched.balance_amount))

            # Track overall serial range
            if sched.serial_number_start is not None:
                if first_serial is None:
                    first_serial = sched.serial_number_start
                last_serial = sched.serial_number_end

            adv_due_text = "With PO" if sched.lot_number == 1 else f"{sched.expected_delivery_date.strftime('%d %b %Y') if sched.expected_delivery_date else 'TBD'}"
            balance_due_text = sched.balance_due_date.strftime('%d %b %Y') if sched.balance_due_date else "TBD"

            # Serial number range display
            serial_range_text = f"{sched.serial_number_start} - {sched.serial_number_end}" if sched.serial_number_start and sched.serial_number_end else "-"

            schedule_rows += f"""
                <tr>
                    <td class="text-center"><strong>LOT {sched.lot_number} ({sched.lot_name})</strong></td>
                    <td class="text-center">{sched.expected_delivery_date.strftime('%d %b %Y') if sched.expected_delivery_date else 'TBD'}</td>
                    <td class="text-center">{sched.total_quantity:,}</td>
                    <td class="text-center" style="font-family: monospace; font-size: 9px;">{serial_range_text}</td>
                    <td class="text-right">Rs. {float(sched.lot_total):,.2f}</td>
                    <td class="text-right">Rs. {float(sched.advance_amount):,.2f}</td>
                    <td class="text-center">{adv_due_text}</td>
                    <td class="text-right">Rs. {float(sched.balance_amount):,.2f}</td>
                    <td class="text-center">{balance_due_text}</td>
                </tr>"""

        # Total serial range display
        total_serial_range = f"{first_serial} - {last_serial}" if first_serial and last_serial else "-"

        delivery_schedule_html = f"""
        <!-- Delivery Schedule Section -->
        <div style="margin-top: 15px; border: 2px solid #1a5f7a; page-break-inside: avoid;">
            <div style="background: #1a5f7a; color: white; padding: 10px; font-weight: bold; font-size: 12px;">
                DELIVERY SCHEDULE & LOT-WISE PAYMENT PLAN
            </div>
            <table style="font-size: 10px;">
                <thead>
                    <tr style="background: #e0e0e0;">
                        <th style="width: 12%">LOT</th>
                        <th style="width: 10%">DELIVERY DATE</th>
                        <th style="width: 6%">QTY</th>
                        <th style="width: 12%">SERIAL NO. RANGE</th>
                        <th style="width: 12%">LOT VALUE (incl. GST)</th>
                        <th style="width: 10%">ADVANCE (25%)</th>
                        <th style="width: 10%">ADVANCE DUE</th>
                        <th style="width: 10%">BALANCE (75%)</th>
                        <th style="width: 10%">BALANCE DUE</th>
                    </tr>
                </thead>
                <tbody>
                    {schedule_rows}
                    <tr style="background: #f5f5f5; font-weight: bold;">
                        <td class="text-center">TOTAL</td>
                        <td class="text-center"></td>
                        <td class="text-center">{total_qty_sched:,}</td>
                        <td class="text-center" style="font-family: monospace; font-size: 9px;">{total_serial_range}</td>
                        <td class="text-right">Rs. {float(total_lot_value):,.2f}</td>
                        <td class="text-right">Rs. {float(total_advance):,.2f}</td>
                        <td class="text-center"></td>
                        <td class="text-right">Rs. {float(total_balance):,.2f}</td>
                        <td class="text-center"></td>
                    </tr>
                </tbody>
            </table>
            <p style="padding: 8px; font-size: 9px; color: #666; background: #fff3cd;">
                <strong>Note:</strong> Serial numbers indicate the range to be supplied by vendor. Advance for each lot must be paid before delivery. Balance is due 45 days after each lot's delivery.
            </p>
        </div>
        """

    # Tax calculations
    cgst_rate = Decimal("9")
    sgst_rate = Decimal("9")
    cgst_amount = Decimal(str(po.cgst_amount or 0))
    sgst_amount = Decimal(str(po.sgst_amount or 0))
    grand_total = Decimal(str(po.grand_total or 0))
    advance_paid = Decimal(str(getattr(po, 'advance_paid', 0) or 0))
    balance_due = grand_total - advance_paid

    # Company info
    company_name = company.legal_name if company else "AQUAPURITE INDIA PRIVATE LIMITED"
    company_gstin = company.gstin if company else "07AADCA1234L1ZP"
    company_cin = getattr(company, 'cin', None) if company else "U12345DL2024PTC123456"
    company_address = f"{company.address_line1 if company else 'Plot No. 123, Sector 5'}, {company.city if company else 'New Delhi'}, {company.state if company else 'Delhi'} - {company.pincode if company else '110001'}"
    company_phone = company.phone if company else "+91-11-12345678"
    company_email = company.email if company else "info@aquapurite.com"
    company_state_code = getattr(company, 'state_code', '07') if company else "07"

    # Vendor info
    vendor_name = vendor.legal_name if vendor else (po.vendor_name or "Vendor")
    vendor_gstin = vendor.gstin if vendor else (po.vendor_gstin or "N/A")
    vendor_state_code = vendor.gst_state_code if vendor else "07"
    vendor_code = vendor.vendor_code if vendor else "N/A"
    vendor_contact = vendor.contact_person if vendor else "N/A"
    vendor_phone = vendor.phone if vendor else "N/A"

    vendor_address_parts = []
    if vendor:
        if vendor.address_line1:
            vendor_address_parts.append(vendor.address_line1)
        if vendor.address_line2:
            vendor_address_parts.append(vendor.address_line2)
        if vendor.city:
            vendor_address_parts.append(vendor.city)
        if vendor.state:
            vendor_address_parts.append(vendor.state)
        if vendor.pincode:
            vendor_address_parts.append(str(vendor.pincode))
    vendor_full_address = ", ".join(vendor_address_parts) if vendor_address_parts else "N/A"

    # Warehouse (Ship To) info
    warehouse_name = warehouse.name if warehouse else "Central Warehouse"
    warehouse_address_parts = []
    if warehouse:
        if warehouse.address_line1:
            warehouse_address_parts.append(warehouse.address_line1)
        if warehouse.city:
            warehouse_address_parts.append(warehouse.city)
        if warehouse.state:
            warehouse_address_parts.append(warehouse.state)
        if warehouse.pincode:
            warehouse_address_parts.append(str(warehouse.pincode))
    warehouse_full_address = ", ".join(warehouse_address_parts) if warehouse_address_parts else "N/A"

    # Bank details
    bank_name = vendor.bank_name if vendor else "N/A"
    bank_branch = vendor.bank_branch if vendor else "N/A"
    bank_account = vendor.bank_account_number if vendor else "N/A"
    bank_ifsc = vendor.bank_ifsc if vendor else "N/A"
    beneficiary_name = vendor.beneficiary_name if vendor else vendor_name

    # Tax type determination
    is_intra_state = company_state_code == vendor_state_code
    tax_type = "CGST + SGST (Intra-State)" if is_intra_state else "IGST (Inter-State)"

    # PO details
    po_date_str = po.po_date.strftime('%d.%m.%Y') if po.po_date else datetime.now().strftime('%d.%m.%Y')
    expected_delivery_str = po.expected_delivery_date.strftime('%d.%m.%Y') if po.expected_delivery_date else "TBD"

    # Terms & Conditions from PO (user-entered, not hardcoded)
    po_terms = getattr(po, 'terms_and_conditions', None) or ""
    if po_terms:
        # Convert newlines to HTML line breaks and escape HTML
        import html
        po_terms_html = html.escape(po_terms).replace('\n', '<br>')
    else:
        # Default message if no terms entered
        po_terms_html = "<em>Terms and conditions as per agreement.</em>"

    # Build serial numbers section HTML (goes after Terms & Conditions)
    serials_html = ""
    if serial_groups:
        serial_rows = ""
        for sg in serial_groups:
            item_type = sg.item_type.value if hasattr(sg.item_type, 'value') else str(sg.item_type)
            serial_rows += f"""
                    <tr>
                        <td class="text-center"><span class="fg-code">{sg.model_code}</span></td>
                        <td class="text-center">{item_type}</td>
                        <td class="text-center"><strong>{sg.quantity}</strong></td>
                        <td class="text-center">{sg.start_serial:08d} - {sg.end_serial:08d}</td>
                        <td style="font-family: 'Courier New', monospace; font-size: 9px;">{sg.start_barcode}</td>
                        <td style="font-family: 'Courier New', monospace; font-size: 9px;">{sg.end_barcode}</td>
                    </tr>"""

        serials_html = f"""
        <!-- Serial Numbers Section (Footer) -->
        <div style="margin-top: 15px; page-break-inside: avoid; border: 1px solid #000;">
            <div style="background: #1a5f7a; color: white; padding: 8px; font-weight: bold; font-size: 11px;">
                PRE-ALLOCATED SERIAL NUMBERS / BARCODES
            </div>
            <div style="padding: 10px;">
                <p style="font-size: 9px; color: #666; margin-bottom: 8px;">
                    The following serial numbers have been pre-allocated for this Purchase Order.
                    Please ensure barcodes are printed and affixed to each unit before dispatch.
                </p>
                <table style="font-size: 9px;">
                    <thead>
                        <tr style="background: #e0e0e0;">
                            <th style="width: 12%;">Model Code</th>
                            <th style="width: 10%;">Type</th>
                            <th style="width: 10%;">Qty</th>
                            <th style="width: 20%;">Serial Range</th>
                            <th style="width: 24%;">Start Barcode</th>
                            <th style="width: 24%;">End Barcode</th>
                        </tr>
                    </thead>
                    <tbody>
                        {serial_rows}
                    </tbody>
                </table>
                <p style="font-size: 9px; color: #666; margin-top: 5px;">
                    Total Serial Numbers: <strong>{total_serials}</strong> |
                    <a href="/api/v1/serialization/po/{str(po.id)}/export?format=csv" class="no-print" style="color: #1a5f7a;">Download CSV</a>
                </p>
            </div>
        </div>
        """

    # APPROVED TEMPLATE STRUCTURE (from generate_po_fasttrack_001.py)
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Purchase Order - {po.po_number}</title>
    <style>
        @page {{ size: A4; margin: 10mm; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; font-size: 11px; line-height: 1.4; padding: 10px; background: #fff; }}
        .document {{ max-width: 210mm; margin: 0 auto; border: 2px solid #000; }}

        /* Header */
        .header {{ background: linear-gradient(135deg, #1a5f7a 0%, #0d3d4d 100%); color: white; padding: 15px; text-align: center; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; letter-spacing: 2px; }}
        .header .contact {{ font-size: 9px; }}

        /* Document Title */
        .doc-title {{ background: #f0f0f0; padding: 12px; text-align: center; border-bottom: 2px solid #000; }}
        .doc-title h2 {{ font-size: 18px; color: #1a5f7a; }}

        /* Info Grid */
        .info-grid {{ display: flex; flex-wrap: wrap; border-bottom: 1px solid #000; }}
        .info-box {{ flex: 1; min-width: 25%; padding: 8px 10px; border-right: 1px solid #000; }}
        .info-box:last-child {{ border-right: none; }}
        .info-box label {{ display: block; font-size: 9px; color: #666; text-transform: uppercase; margin-bottom: 3px; }}
        .info-box value {{ display: block; font-weight: bold; font-size: 11px; }}

        /* Party Section */
        .party-section {{ display: flex; border-bottom: 1px solid #000; }}
        .party-box {{ flex: 1; padding: 10px; border-right: 1px solid #000; }}
        .party-box:last-child {{ border-right: none; }}
        .party-header {{ background: #1a5f7a; color: white; padding: 5px 8px; margin: -10px -10px 10px -10px; font-size: 10px; font-weight: bold; }}
        .party-box p {{ margin-bottom: 3px; }}
        .party-box .company-name {{ font-weight: bold; font-size: 12px; color: #1a5f7a; }}

        /* Table */
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #1a5f7a; color: white; padding: 8px 5px; font-size: 10px; text-align: center; border: 1px solid #000; }}
        td {{ padding: 8px 5px; border: 1px solid #000; font-size: 10px; }}
        .text-center {{ text-align: center; }}
        .text-right {{ text-align: right; }}
        .fg-code {{ font-family: 'Courier New', monospace; font-weight: bold; color: #1a5f7a; font-size: 9px; }}
        .item-code {{ font-family: 'Courier New', monospace; font-weight: bold; color: #333; font-size: 9px; }}

        /* Totals */
        .totals-section {{ display: flex; border-bottom: 1px solid #000; }}
        .totals-left {{ flex: 1; padding: 10px; border-right: 1px solid #000; }}
        .totals-right {{ width: 300px; }}
        .totals-row {{ display: flex; padding: 5px 10px; border-bottom: 1px solid #ddd; }}
        .totals-row:last-child {{ border-bottom: none; }}
        .totals-label {{ flex: 1; text-align: right; padding-right: 15px; }}
        .totals-value {{ width: 110px; text-align: right; font-weight: bold; }}
        .grand-total {{ background: #1a5f7a; color: white; font-size: 12px; }}
        .advance-paid {{ background: #28a745; color: white; }}
        .balance-due {{ background: #dc3545; color: white; }}

        /* Amount in Words */
        .amount-words {{ padding: 10px; background: #f9f9f9; border-bottom: 1px solid #000; font-style: italic; }}

        /* Payment Section */
        .payment-section {{ padding: 10px; border-bottom: 1px solid #000; background: #e8f5e9; }}
        .payment-section h4 {{ color: #2e7d32; margin-bottom: 8px; }}
        .payment-detail {{ display: flex; margin-bottom: 5px; }}
        .payment-detail label {{ width: 150px; font-weight: bold; }}

        /* Bank Details */
        .bank-section {{ padding: 10px; border-bottom: 1px solid #000; background: #fff3cd; }}
        .bank-section h4 {{ color: #856404; margin-bottom: 8px; }}

        /* Terms */
        .terms {{ padding: 10px; font-size: 9px; border-bottom: 1px solid #000; }}
        .terms h4 {{ margin-bottom: 5px; color: #1a5f7a; }}
        .terms ol {{ margin-left: 15px; }}
        .terms li {{ margin-bottom: 3px; }}

        /* Signature */
        .signature-section {{ display: flex; padding: 20px; }}
        .signature-box {{ flex: 1; text-align: center; }}
        .signature-line {{ border-top: 1px solid #000; margin-top: 50px; padding-top: 5px; width: 180px; margin-left: auto; margin-right: auto; }}

        /* Footer */
        .footer {{ background: #f0f0f0; padding: 8px; text-align: center; font-size: 9px; color: #666; }}

        /* Print Button */
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #1a5f7a 0%, #0d3d4d 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .print-btn:hover {{
            background: linear-gradient(135deg, #0d3d4d 0%, #1a5f7a 100%);
        }}

        @media print {{
            body {{ padding: 0; }}
            .document {{ border: 1px solid #000; }}
            .print-btn {{ display: none !important; }}
            .no-print {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <!-- Print PDF Button -->
    <button class="print-btn no-print" onclick="window.print()">Print PDF</button>

    <div class="document">
        <!-- Header -->
        <div class="header">
            <h1>{company_name}</h1>
            <div class="contact">
                {company_address}<br>
                GSTIN: {company_gstin} | CIN: {company_cin or 'N/A'}<br>
                Phone: {company_phone} | Email: {company_email}
            </div>
        </div>

        <!-- Document Title -->
        <div class="doc-title">
            <h2>PURCHASE ORDER</h2>
        </div>

        <!-- PO Info Grid -->
        <div class="info-grid">
            <div class="info-box">
                <label>PO Number</label>
                <value style="font-size: 13px; color: #1a5f7a;">{po.po_number}</value>
            </div>
            <div class="info-box">
                <label>PO Date</label>
                <value>{po_date_str}</value>
            </div>
            <div class="info-box">
                <label>PI Reference</label>
                <value>{getattr(po, 'pi_reference', None) or 'N/A'}</value>
            </div>
            <div class="info-box">
                <label>PI Date</label>
                <value>{getattr(po, 'pi_date', None).strftime('%d.%m.%Y') if getattr(po, 'pi_date', None) else 'N/A'}</value>
            </div>
        </div>

        <div class="info-grid">
            <div class="info-box">
                <label>Expected Delivery</label>
                <value style="color: #dc3545;">{expected_delivery_str}</value>
            </div>
            <div class="info-box">
                <label>Delivery Terms</label>
                <value>{getattr(po, 'delivery_terms', None) or 'Ex-Works'}</value>
            </div>
            <div class="info-box">
                <label>Payment Terms</label>
                <value>{getattr(po, 'payment_terms', None) or f'{po.credit_days or 30} days credit'}</value>
            </div>
            <div class="info-box">
                <label>Tax Type</label>
                <value>{tax_type}</value>
            </div>
        </div>

        <!-- Vendor & Delivery Details -->
        <div class="party-section">
            <div class="party-box">
                <div class="party-header">SUPPLIER / VENDOR DETAILS</div>
                <p class="company-name">{vendor_name}</p>
                <p>{vendor_full_address}</p>
                <p><strong>GSTIN:</strong> {vendor_gstin}</p>
                <p><strong>State Code:</strong> {vendor_state_code}</p>
                <p><strong>Contact:</strong> {vendor_contact}</p>
                <p><strong>Phone:</strong> {vendor_phone}</p>
                <p><strong>Vendor Code:</strong> {vendor_code}</p>
            </div>
            <div class="party-box">
                <div class="party-header">SHIP TO / DELIVERY ADDRESS</div>
                <p class="company-name">{company_name}</p>
                <p>{warehouse_full_address}</p>
                <p><strong>Warehouse:</strong> {warehouse_name}</p>
                <p><strong>GSTIN:</strong> {company_gstin}</p>
                <p><strong>State Code:</strong> {company_state_code}</p>
                <p><strong>Contact:</strong> Store Manager</p>
                <p><strong>Phone:</strong> {company_phone}</p>
            </div>
        </div>

        <!-- Order Items Table -->
        <table>
            <thead>
                <tr>
                    <th style="width:4%">S.N.</th>
                    <th style="width:10%">SKU</th>
                    <th style="width:{'15%' if has_monthly_breakdown else '25%'}">Description</th>
                    <th style="width:8%">HSN</th>
                    {month_headers}
                    <th style="width:7%">TOTAL</th>
                    <th style="width:5%">UOM</th>
                    <th style="width:10%">Rate</th>
                    <th style="width:12%">Amount</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
                <tr style="background: #f5f5f5; font-weight: bold;">
                    <td colspan="4" class="text-right">TOTAL QUANTITIES</td>
                    {month_total_cells}
                    <td class="text-center">{total_qty}</td>
                    <td class="text-center">Nos</td>
                    <td></td>
                    <td class="text-right">Rs. {float(subtotal):,.2f}</td>
                </tr>
            </tbody>
        </table>

        <!-- Totals Section -->
        <div class="totals-section">
            <div class="totals-left">
                <strong>HSN Summary ({tax_type}):</strong>
                <table style="margin-top: 5px; font-size: 9px;">
                    <tr style="background: #e0e0e0;">
                        <th>HSN Code</th>
                        <th>Taxable Value</th>
                        <th>CGST @{cgst_rate}%</th>
                        <th>SGST @{sgst_rate}%</th>
                        <th>Total Tax</th>
                    </tr>
                    <tr>
                        <td class="text-center">84212110</td>
                        <td class="text-right">Rs. {float(subtotal):,.2f}</td>
                        <td class="text-right">Rs. {float(cgst_amount):,.2f}</td>
                        <td class="text-right">Rs. {float(sgst_amount):,.2f}</td>
                        <td class="text-right">Rs. {float(cgst_amount + sgst_amount):,.2f}</td>
                    </tr>
                </table>
                <p style="margin-top: 10px; font-size: 9px; color: #666;">
                    <strong>Note:</strong> {tax_type} applicable
                </p>
            </div>
            <div class="totals-right">
                <div class="totals-row">
                    <span class="totals-label">Sub Total:</span>
                    <span class="totals-value">Rs. {float(subtotal):,.2f}</span>
                </div>
                <div class="totals-row">
                    <span class="totals-label">CGST @ {cgst_rate}%:</span>
                    <span class="totals-value">Rs. {float(cgst_amount):,.2f}</span>
                </div>
                <div class="totals-row">
                    <span class="totals-label">SGST @ {sgst_rate}%:</span>
                    <span class="totals-value">Rs. {float(sgst_amount):,.2f}</span>
                </div>
                <div class="totals-row grand-total">
                    <span class="totals-label">GRAND TOTAL:</span>
                    <span class="totals-value">Rs. {float(grand_total):,.2f}</span>
                </div>
                <div class="totals-row advance-paid">
                    <span class="totals-label">Advance Paid:</span>
                    <span class="totals-value">Rs. {float(advance_paid):,.2f}</span>
                </div>
                <div class="totals-row balance-due">
                    <span class="totals-label">Balance Due:</span>
                    <span class="totals-value">Rs. {float(balance_due):,.2f}</span>
                </div>
            </div>
        </div>

        <!-- Amount in Words -->
        <div class="amount-words">
            <strong>Grand Total in Words:</strong> {_number_to_words(float(grand_total))}<br>
            <strong>Advance Paid in Words:</strong> {_number_to_words(float(advance_paid))}
        </div>

        {delivery_schedule_html}

        <!-- Payment Details -->
        <div class="payment-section">
            <h4>ADVANCE PAYMENT DETAILS</h4>
            <div class="payment-detail">
                <label>Payment Date:</label>
                <span>{getattr(po, 'advance_date', None).strftime('%d.%m.%Y') if getattr(po, 'advance_date', None) else 'N/A'}</span>
            </div>
            <div class="payment-detail">
                <label>Transaction Reference:</label>
                <span>{getattr(po, 'advance_reference', None) or 'RTGS/NEFT Transfer'}</span>
            </div>
            <div class="payment-detail">
                <label>Amount Transferred:</label>
                <span><strong>Rs. {float(advance_paid):,.2f}</strong></span>
            </div>
            <div class="payment-detail">
                <label>Balance Payment:</label>
                <span><strong>Rs. {float(balance_due):,.2f}</strong></span>
            </div>
        </div>

        <!-- Bank Details -->
        <div class="bank-section">
            <h4>SUPPLIER BANK DETAILS (For Future Payments)</h4>
            <div class="payment-detail">
                <label>Bank Name:</label>
                <span>{bank_name}</span>
            </div>
            <div class="payment-detail">
                <label>Branch:</label>
                <span>{bank_branch}</span>
            </div>
            <div class="payment-detail">
                <label>Account Number:</label>
                <span><strong>{bank_account}</strong></span>
            </div>
            <div class="payment-detail">
                <label>IFSC Code:</label>
                <span>{bank_ifsc}</span>
            </div>
            <div class="payment-detail">
                <label>Account Name:</label>
                <span>{beneficiary_name}</span>
            </div>
        </div>

        <!-- Terms & Conditions -->
        <div class="terms">
            <h4>TERMS & CONDITIONS:</h4>
            <div style="white-space: pre-wrap; font-size: 11px; line-height: 1.5;">{po_terms_html}</div>
        </div>

        {serials_html}

        <!-- System Generated Notice -->
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; text-align: center;">
            <p style="margin: 0; font-size: 12px; color: #495057;">
                <strong>SYSTEM GENERATED PURCHASE ORDER</strong>
            </p>
            <p style="margin: 5px 0 0 0; font-size: 10px; color: #6c757d;">
                This is an electronically generated document from Aquapurite ERP System.<br>
                No signature required. Document ID: {po.po_number}
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            System Generated Purchase Order | Aquapurite ERP | Document ID: {po.po_number} | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html_content)


@router.get("/grn/{grn_id}/download")
async def download_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Download Goods Receipt Note as printable HTML."""
    from fastapi.responses import HTMLResponse
    from app.models.company import Company

    result = await db.execute(
        select(GoodsReceiptNote)
        .options(selectinload(GoodsReceiptNote.items))
        .where(GoodsReceiptNote.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    # Get company details
    company_result = await db.execute(select(Company).where(Company.is_primary == True).limit(1))
    company = company_result.scalar_one_or_none()
    if not company:
        company_result = await db.execute(select(Company).limit(1))
        company = company_result.scalar_one_or_none()

    # Get PO details
    po_result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == grn.purchase_order_id)
    )
    po = po_result.scalar_one_or_none()

    # Get vendor details
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == grn.vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()

    # Get warehouse details
    warehouse_result = await db.execute(
        select(Warehouse).where(Warehouse.id == grn.warehouse_id)
    )
    warehouse = warehouse_result.scalar_one_or_none()

    # Build items table
    items_html = ""
    for idx, item in enumerate(grn.items, 1):
        unit_price = float(item.unit_price) if item.unit_price else 0.0
        accepted_value = float(item.accepted_value) if item.accepted_value else 0.0

        items_html += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{idx}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.product_name or '-'}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.sku or '-'}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{item.quantity_expected}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{item.quantity_received}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: green;">{item.quantity_accepted}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: red;">{item.quantity_rejected}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">₹{unit_price:,.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">₹{accepted_value:,.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.batch_number or '-'}</td>
        </tr>
        """

    vendor_name = vendor.legal_name if vendor else "N/A"
    warehouse_name = warehouse.name if warehouse else "N/A"
    po_number = po.po_number if po else "N/A"

    qc_status_color = "green" if grn.qc_status and grn.qc_status.value == "ACCEPTED" else "orange"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Goods Receipt Note - {grn.grn_number}</title>
        <style>
            @media print {{
                body {{ margin: 0; padding: 20px; }}
                .no-print {{ display: none; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }}
            .company-name {{
                font-size: 24px;
                font-weight: bold;
                color: #34a853;
            }}
            .document-title {{
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                background: #e6f4ea;
                padding: 10px;
            }}
            .info-section {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .info-box {{
                width: 48%;
                background: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
            }}
            .info-box h3 {{
                margin: 0 0 10px 0;
                color: #34a853;
                font-size: 14px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .info-box p {{
                margin: 5px 0;
                font-size: 12px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th {{
                background: #34a853;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 11px;
            }}
            .summary-box {{
                background: #e6f4ea;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .summary-box h3 {{
                margin: 0 0 10px 0;
                color: #34a853;
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
            }}
            .summary-item {{
                text-align: center;
            }}
            .summary-item .label {{
                font-size: 11px;
                color: #666;
            }}
            .summary-item .value {{
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }}
            .signatures {{
                display: flex;
                justify-content: space-between;
                margin-top: 60px;
            }}
            .signature-box {{
                text-align: center;
                width: 200px;
            }}
            .signature-line {{
                border-top: 1px solid #333;
                margin-top: 40px;
                padding-top: 5px;
            }}
            .print-btn {{
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 10px 20px;
                background: #34a853;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <button class="print-btn no-print" onclick="window.print()">🖨️ Print / Save PDF</button>

        <div class="header">
            <div class="company-name">{company.legal_name if company else 'AQUAPURITE PRIVATE LIMITED'}</div>
            <div style="font-size: 12px; color: #666;">
                {company.address_line1 if company else 'PLOT 36-A, KH NO 181, PH-1, SHYAM VIHAR, DINDAPUR EXT'}, {company.city if company else 'New Delhi'} - {company.pincode if company else '110043'}, {company.state if company else 'Delhi'}
            </div>
            <div style="font-size: 10px; color: #888; margin-top: 5px;">
                GSTIN: {company.gstin if company else '07ABDCA6170C1Z0'} | PAN: {company.pan if company else 'ABDCA6170C'} | CIN: {getattr(company, 'cin', None) or 'U32909DL2025PTC454115'}
            </div>
            <div class="document-title">GOODS RECEIPT NOTE (GRN)</div>
        </div>

        <div class="info-section">
            <div class="info-box">
                <h3>VENDOR DETAILS</h3>
                <p><strong>{vendor_name}</strong></p>
                <p>Challan No: {grn.vendor_challan_number or 'N/A'}</p>
                <p>Challan Date: {grn.vendor_challan_date or 'N/A'}</p>
            </div>
            <div class="info-box">
                <h3>GRN DETAILS</h3>
                <p><strong>GRN Number:</strong> {grn.grn_number}</p>
                <p><strong>GRN Date:</strong> {grn.grn_date}</p>
                <p><strong>PO Reference:</strong> {po_number}</p>
                <p><strong>Status:</strong> {grn.status.value if grn.status else 'N/A'}</p>
                <p><strong>QC Status:</strong> <span style="color: {qc_status_color};">{grn.qc_status.value if grn.qc_status else 'PENDING'}</span></p>
            </div>
        </div>

        <div class="info-section">
            <div class="info-box">
                <h3>RECEIVING WAREHOUSE</h3>
                <p><strong>{warehouse_name}</strong></p>
            </div>
            <div class="info-box">
                <h3>TRANSPORT DETAILS</h3>
                <p><strong>Transporter:</strong> {grn.transporter_name or 'N/A'}</p>
                <p><strong>Vehicle No:</strong> {grn.vehicle_number or 'N/A'}</p>
                <p><strong>LR Number:</strong> {grn.lr_number or 'N/A'}</p>
                <p><strong>E-Way Bill:</strong> {grn.e_way_bill_number or 'N/A'}</p>
            </div>
        </div>

        <div class="summary-box">
            <h3>RECEIPT SUMMARY</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="label">Total Items</div>
                    <div class="value">{grn.total_items or 0}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Qty Received</div>
                    <div class="value">{grn.total_quantity_received or 0}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Qty Accepted</div>
                    <div class="value" style="color: green;">{grn.total_quantity_accepted or 0}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Qty Rejected</div>
                    <div class="value" style="color: red;">{grn.total_quantity_rejected or 0}</div>
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">#</th>
                    <th>Product</th>
                    <th>SKU</th>
                    <th style="width: 60px;">Expected</th>
                    <th style="width: 60px;">Received</th>
                    <th style="width: 60px;">Accepted</th>
                    <th style="width: 60px;">Rejected</th>
                    <th style="width: 80px;">Unit Price</th>
                    <th style="width: 90px;">Accepted Value</th>
                    <th>Batch No</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div style="text-align: right; font-size: 16px; font-weight: bold; background: #e6f4ea; padding: 15px; border-radius: 5px;">
            Total Accepted Value: ₹{float(grn.total_value or 0):,.2f}
        </div>

        <p><strong>Receiving Remarks:</strong> {grn.receiving_remarks or 'None'}</p>

        <div class="signatures">
            <div class="signature-box">
                <div class="signature-line">Received By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">QC Inspector</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Store In-charge</div>
            </div>
        </div>

        <p style="text-align: center; font-size: 10px; color: #999; margin-top: 40px;">
            This is a computer-generated document. Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/invoices/{invoice_id}/download")
async def download_vendor_invoice(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Download Vendor Invoice as printable HTML."""
    from fastapi.responses import HTMLResponse
    from app.models.company import Company

    result = await db.execute(
        select(VendorInvoice).where(VendorInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Vendor Invoice not found")

    # Get company details
    company_result = await db.execute(select(Company).where(Company.is_primary == True).limit(1))
    company = company_result.scalar_one_or_none()
    if not company:
        company_result = await db.execute(select(Company).limit(1))
        company = company_result.scalar_one_or_none()

    # Get vendor details
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == invoice.vendor_id)
    )
    vendor = vendor_result.scalar_one_or_none()

    # Get PO details
    po_result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == invoice.purchase_order_id)
    )
    po = po_result.scalar_one_or_none()

    # Get GRN details
    grn_result = await db.execute(
        select(GoodsReceiptNote).where(GoodsReceiptNote.id == invoice.grn_id)
    )
    grn = grn_result.scalar_one_or_none()

    vendor_name = vendor.legal_name if vendor else "N/A"
    vendor_address = ""
    if vendor:
        addr_parts = [vendor.address_line1, vendor.address_line2, vendor.city, vendor.state, str(vendor.pincode) if vendor.pincode else None]
        vendor_address = ", ".join(filter(None, addr_parts))

    po_number = po.po_number if po else "N/A"
    grn_number = grn.grn_number if grn else "N/A"

    # Handle both enum and string status values
    status_val = invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status) if invoice.status else ""
    status_color = "green" if status_val in ["VERIFIED", "PAID", "MATCHED", "APPROVED"] else "orange"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Vendor Invoice - {invoice.invoice_number}</title>
        <style>
            @media print {{
                body {{ margin: 0; padding: 20px; }}
                .no-print {{ display: none; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }}
            .company-name {{
                font-size: 24px;
                font-weight: bold;
                color: #ea4335;
            }}
            .document-title {{
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                background: #fce8e6;
                padding: 10px;
            }}
            .info-section {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .info-box {{
                width: 48%;
                background: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
            }}
            .info-box h3 {{
                margin: 0 0 10px 0;
                color: #ea4335;
                font-size: 14px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .info-box p {{
                margin: 5px 0;
                font-size: 12px;
            }}
            .amount-box {{
                background: #fce8e6;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .amount-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
            }}
            .amount-item {{
                text-align: center;
            }}
            .amount-item .label {{
                font-size: 11px;
                color: #666;
            }}
            .amount-item .value {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th {{
                background: #ea4335;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 12px;
            }}
            td {{
                border: 1px solid #ddd;
                padding: 10px 8px;
            }}
            .match-status {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            .match-yes {{ background: #e6f4ea; color: #137333; }}
            .match-no {{ background: #fce8e6; color: #c5221f; }}
            .signatures {{
                display: flex;
                justify-content: space-between;
                margin-top: 60px;
            }}
            .signature-box {{
                text-align: center;
                width: 200px;
            }}
            .signature-line {{
                border-top: 1px solid #333;
                margin-top: 40px;
                padding-top: 5px;
            }}
            .print-btn {{
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 10px 20px;
                background: #ea4335;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <button class="print-btn no-print" onclick="window.print()">🖨️ Print / Save PDF</button>

        <div class="header">
            <div class="company-name">{company.legal_name if company else 'AQUAPURITE PRIVATE LIMITED'}</div>
            <div style="font-size: 12px; color: #666;">
                {company.address_line1 if company else 'PLOT 36-A, KH NO 181, PH-1, SHYAM VIHAR, DINDAPUR EXT'}, {company.city if company else 'New Delhi'} - {company.pincode if company else '110043'}, {company.state if company else 'Delhi'}<br>
                GSTIN: {company.gstin if company else '07ABDCA6170C1Z0'} | PAN: {company.pan if company else 'ABDCA6170C'}
            </div>
            <div class="document-title">VENDOR INVOICE RECORD</div>
        </div>

        <div class="info-section">
            <div class="info-box">
                <h3>VENDOR DETAILS</h3>
                <p><strong>{vendor_name}</strong></p>
                <p>{vendor_address}</p>
                <p>GSTIN: {vendor.gstin if vendor else 'N/A'}</p>
            </div>
            <div class="info-box">
                <h3>INVOICE DETAILS</h3>
                <p><strong>Invoice Number:</strong> {invoice.invoice_number}</p>
                <p><strong>Invoice Date:</strong> {invoice.invoice_date}</p>
                <p><strong>Due Date:</strong> {invoice.due_date or 'N/A'}</p>
                <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_val or 'N/A'}</span></p>
            </div>
        </div>

        <div class="info-section">
            <div class="info-box" style="width: 100%;">
                <h3>REFERENCE DOCUMENTS</h3>
                <p><strong>PO Number:</strong> {po_number}</p>
                <p><strong>GRN Number:</strong> {grn_number}</p>
            </div>
        </div>

        <div class="amount-box">
            <h3 style="margin: 0 0 15px 0; color: #ea4335;">INVOICE AMOUNTS</h3>
            <div class="amount-grid">
                <div class="amount-item">
                    <div class="label">Taxable Amount</div>
                    <div class="value">₹{float(invoice.taxable_amount or 0):,.2f}</div>
                </div>
                <div class="amount-item">
                    <div class="label">Total Tax (GST)</div>
                    <div class="value">₹{float(invoice.total_tax or 0):,.2f}</div>
                </div>
                <div class="amount-item">
                    <div class="label">Total Amount</div>
                    <div class="value" style="color: #ea4335;">₹{float(invoice.grand_total or 0):,.2f}</div>
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Tax Breakup</th>
                    <th style="text-align: right;">Amount (₹)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>CGST</td>
                    <td style="text-align: right;">₹{float(invoice.cgst_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>SGST</td>
                    <td style="text-align: right;">₹{float(invoice.sgst_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>IGST</td>
                    <td style="text-align: right;">₹{float(invoice.igst_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>TDS Deducted</td>
                    <td style="text-align: right;">₹{float(invoice.tds_amount or 0):,.2f}</td>
                </tr>
                <tr style="background: #f5f5f5; font-weight: bold;">
                    <td>Net Payable</td>
                    <td style="text-align: right;">₹{float(invoice.net_payable or invoice.grand_total or 0):,.2f}</td>
                </tr>
            </tbody>
        </table>

        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 10px 0; color: #333;">3-WAY MATCH STATUS</h3>
            <p>
                <strong>PO Match:</strong>
                <span class="match-status {'match-yes' if invoice.po_matched else 'match-no'}">
                    {'✓ Matched' if invoice.po_matched else '✗ Not Matched'}
                </span>
            </p>
            <p>
                <strong>GRN Match:</strong>
                <span class="match-status {'match-yes' if invoice.grn_matched else 'match-no'}">
                    {'✓ Matched' if invoice.grn_matched else '✗ Not Matched'}
                </span>
            </p>
            <p>
                <strong>Invoice Match:</strong>
                <span class="match-status {'match-yes' if invoice.is_fully_matched else 'match-no'}">
                    {'✓ Matched' if invoice.is_fully_matched else '✗ Not Matched'}
                </span>
            </p>
            {f'<p><strong>Variance:</strong> ₹{float(invoice.matching_variance or 0):,.2f} - {invoice.variance_reason or "N/A"}</p>' if invoice.matching_variance else ''}
        </div>

        <p><strong>Notes:</strong> {invoice.internal_notes or 'None'}</p>

        <div class="signatures">
            <div class="signature-box">
                <div class="signature-line">Verified By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Approved By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Finance Head</div>
            </div>
        </div>

        <p style="text-align: center; font-size: 10px; color: #999; margin-top: 40px;">
            This is a computer-generated document. Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


# ==================== Vendor Proforma Invoice (Quotations from Vendors) ====================

@router.post("/proformas", response_model=VendorProformaResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor_proforma(
    proforma_in: VendorProformaCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new Vendor Proforma Invoice (quotation from vendor)."""
    # Verify vendor exists
    vendor = await db.get(Vendor, proforma_in.vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Generate our reference number
    today = date.today()
    count_result = await db.execute(
        select(func.count(VendorProformaInvoice.id)).where(
            func.date(VendorProformaInvoice.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    our_reference = f"VPI-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Calculate item totals
    subtotal = Decimal("0")
    total_discount = Decimal("0")
    total_cgst = Decimal("0")
    total_sgst = Decimal("0")
    total_igst = Decimal("0")

    items_to_create = []
    for item_data in proforma_in.items:
        base_amount = Decimal(str(item_data.quantity)) * item_data.unit_price
        discount_amount = base_amount * (item_data.discount_percent / 100)
        taxable_amount = base_amount - discount_amount

        # Calculate GST (assuming intra-state - CGST+SGST)
        gst_amount = taxable_amount * (item_data.gst_rate / 100)
        cgst_amount = gst_amount / 2
        sgst_amount = gst_amount / 2
        igst_amount = Decimal("0")

        total_amount = taxable_amount + gst_amount

        subtotal += base_amount
        total_discount += discount_amount
        total_cgst += cgst_amount
        total_sgst += sgst_amount

        items_to_create.append({
            "data": item_data,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "igst_amount": igst_amount,
            "total_amount": total_amount,
        })

    taxable_amount = subtotal - total_discount
    total_tax = total_cgst + total_sgst + total_igst
    grand_total = taxable_amount + total_tax + proforma_in.freight_charges + proforma_in.packing_charges + proforma_in.other_charges + proforma_in.round_off

    # Create proforma
    # Use vendor_pi_number or proforma_number for the vendor's document number
    vendor_doc_number = proforma_in.vendor_pi_number or proforma_in.proforma_number or our_reference

    proforma = VendorProformaInvoice(
        our_reference=our_reference,
        proforma_number=vendor_doc_number,
        proforma_date=proforma_in.proforma_date,
        validity_date=proforma_in.validity_date,
        status=ProformaStatus.RECEIVED,
        vendor_id=proforma_in.vendor_id,
        requisition_id=proforma_in.requisition_id,
        delivery_warehouse_id=proforma_in.delivery_warehouse_id,
        delivery_days=proforma_in.delivery_days,
        delivery_terms=proforma_in.delivery_terms,
        payment_terms=proforma_in.payment_terms,
        credit_days=proforma_in.credit_days,
        subtotal=subtotal,
        discount_amount=total_discount,
        discount_percent=(total_discount / subtotal * 100) if subtotal else Decimal("0"),
        taxable_amount=taxable_amount,
        cgst_amount=total_cgst,
        sgst_amount=total_sgst,
        igst_amount=total_igst,
        total_tax=total_tax,
        freight_charges=proforma_in.freight_charges,
        packing_charges=proforma_in.packing_charges,
        other_charges=proforma_in.other_charges,
        round_off=proforma_in.round_off,
        grand_total=grand_total,
        proforma_pdf_url=proforma_in.proforma_pdf_url,
        vendor_remarks=proforma_in.vendor_remarks,
        internal_notes=proforma_in.internal_notes,
        received_by=current_user.id,
        received_at=datetime.utcnow(),
    )

    db.add(proforma)
    await db.flush()

    # Create items
    for item_info in items_to_create:
        item_data = item_info["data"]
        item = VendorProformaItem(
            proforma_id=proforma.id,
            product_id=item_data.product_id,
            item_code=item_data.item_code,
            description=item_data.description,
            hsn_code=item_data.hsn_code,
            uom=item_data.uom,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_percent=item_data.discount_percent,
            discount_amount=item_info["discount_amount"],
            taxable_amount=item_info["taxable_amount"],
            gst_rate=item_data.gst_rate,
            cgst_amount=item_info["cgst_amount"],
            sgst_amount=item_info["sgst_amount"],
            igst_amount=item_info["igst_amount"],
            total_amount=item_info["total_amount"],
            lead_time_days=item_data.lead_time_days,
        )
        db.add(item)

    await db.commit()

    # Reload with items
    result = await db.execute(
        select(VendorProformaInvoice)
        .options(selectinload(VendorProformaInvoice.items))
        .where(VendorProformaInvoice.id == proforma.id)
    )
    proforma = result.scalar_one()

    return proforma


@router.get("/proformas", response_model=VendorProformaListResponse)
async def list_vendor_proformas(
    db: DB,
    current_user: User = Depends(get_current_user),
    vendor_id: Optional[UUID] = None,
    proforma_status: Optional[ProformaStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List vendor proforma invoices with filters."""
    query = select(VendorProformaInvoice).options(
        selectinload(VendorProformaInvoice.vendor)
    )

    if vendor_id:
        query = query.where(VendorProformaInvoice.vendor_id == vendor_id)
    if proforma_status:
        query = query.where(VendorProformaInvoice.status == proforma_status)
    if from_date:
        query = query.where(VendorProformaInvoice.proforma_date >= from_date)
    if to_date:
        query = query.where(VendorProformaInvoice.proforma_date <= to_date)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sum
    sum_query = select(func.sum(VendorProformaInvoice.grand_total)).select_from(query.subquery())
    total_value = (await db.execute(sum_query)).scalar() or Decimal("0")

    # Paginate
    query = query.order_by(VendorProformaInvoice.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    proformas = result.scalars().all()

    items = []
    for p in proformas:
        items.append(VendorProformaBrief(
            id=p.id,
            our_reference=p.our_reference,
            proforma_number=p.proforma_number,
            proforma_date=p.proforma_date,
            vendor_name=p.vendor.legal_name if p.vendor else "Unknown",
            grand_total=p.grand_total,
            validity_date=p.validity_date,
            status=p.status,
        ))

    return VendorProformaListResponse(
        items=items,
        total=total,
        total_value=total_value,
        skip=skip,
        limit=limit,
    )


@router.get("/proformas/{proforma_id}", response_model=VendorProformaResponse)
async def get_vendor_proforma(
    proforma_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get vendor proforma invoice details."""
    result = await db.execute(
        select(VendorProformaInvoice)
        .options(
            selectinload(VendorProformaInvoice.items),
            selectinload(VendorProformaInvoice.vendor),
        )
        .where(VendorProformaInvoice.id == proforma_id)
    )
    proforma = result.scalar_one_or_none()

    if not proforma:
        raise HTTPException(status_code=404, detail="Vendor Proforma not found")

    return proforma


@router.put("/proformas/{proforma_id}", response_model=VendorProformaResponse)
async def update_vendor_proforma(
    proforma_id: UUID,
    update_data: VendorProformaUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update vendor proforma invoice."""
    proforma = await db.get(VendorProformaInvoice, proforma_id)
    if not proforma:
        raise HTTPException(status_code=404, detail="Vendor Proforma not found")

    if proforma.status in [ProformaStatus.CONVERTED_TO_PO, ProformaStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update proforma with status {proforma.status}"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(proforma, key, value)

    await db.commit()
    await db.refresh(proforma)

    return proforma


@router.post("/proformas/{proforma_id}/approve", response_model=VendorProformaResponse)
async def approve_vendor_proforma(
    proforma_id: UUID,
    request: VendorProformaApproveRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a vendor proforma invoice."""
    proforma = await db.get(VendorProformaInvoice, proforma_id)
    if not proforma:
        raise HTTPException(status_code=404, detail="Vendor Proforma not found")

    if proforma.status not in [ProformaStatus.RECEIVED, ProformaStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve/reject proforma with status {proforma.status}"
        )

    if request.action == "APPROVE":
        proforma.status = ProformaStatus.APPROVED
        proforma.approved_by = current_user.id
        proforma.approved_at = datetime.utcnow()
    else:
        proforma.status = ProformaStatus.REJECTED
        proforma.rejection_reason = request.rejection_reason

    await db.commit()

    # Reload with items
    result = await db.execute(
        select(VendorProformaInvoice)
        .options(selectinload(VendorProformaInvoice.items))
        .where(VendorProformaInvoice.id == proforma_id)
    )
    proforma = result.scalar_one()

    return proforma


@router.post("/proformas/{proforma_id}/convert-to-po", response_model=PurchaseOrderResponse)
async def convert_proforma_to_po(
    proforma_id: UUID,
    request: VendorProformaConvertToPORequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Convert an approved vendor proforma invoice to a Purchase Order."""
    result = await db.execute(
        select(VendorProformaInvoice)
        .options(selectinload(VendorProformaInvoice.items))
        .where(VendorProformaInvoice.id == proforma_id)
    )
    proforma = result.scalar_one_or_none()

    if not proforma:
        raise HTTPException(status_code=404, detail="Vendor Proforma not found")

    if proforma.status != ProformaStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Only approved proformas can be converted to PO"
        )

    # Generate PO number
    today = date.today()
    count_result = await db.execute(
        select(func.count(PurchaseOrder.id)).where(
            func.date(PurchaseOrder.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    po_number = f"PO-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Get vendor
    vendor = await db.get(Vendor, proforma.vendor_id)

    # Create PO (convert Decimal values to float for SQLite compatibility)
    po = PurchaseOrder(
        po_number=po_number,
        po_date=today,
        status=POStatus.DRAFT,
        vendor_id=proforma.vendor_id,
        vendor_name=vendor.legal_name if vendor else "Unknown",
        vendor_gstin=vendor.gstin if vendor else None,
        delivery_warehouse_id=request.delivery_warehouse_id or proforma.delivery_warehouse_id,
        expected_delivery_date=request.expected_delivery_date,
        payment_terms=proforma.payment_terms,
        credit_days=proforma.credit_days,
        quotation_reference=proforma.proforma_number,
        quotation_date=proforma.proforma_date,
        freight_charges=float(proforma.freight_charges or 0),
        packing_charges=float(proforma.packing_charges or 0),
        other_charges=float(proforma.other_charges or 0),
        special_instructions=request.special_instructions,
        subtotal=float(proforma.subtotal or 0),
        discount_amount=float(proforma.discount_amount or 0),
        taxable_amount=float(proforma.taxable_amount or 0),
        cgst_amount=float(proforma.cgst_amount or 0),
        sgst_amount=float(proforma.sgst_amount or 0),
        igst_amount=float(proforma.igst_amount or 0),
        total_tax=float(proforma.total_tax or 0),
        grand_total=float(proforma.grand_total or 0),
        created_by=current_user.id,
    )

    db.add(po)
    await db.flush()

    # Create PO items from proforma items
    for idx, item in enumerate(proforma.items, 1):
        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            line_number=idx,
            product_id=item.product_id,
            product_name=item.description,
            sku=item.item_code or f"ITEM-{idx}",
            hsn_code=item.hsn_code,
            quantity_ordered=int(item.quantity),  # Convert Decimal to int for SQLite
            uom=item.uom,
            unit_price=float(item.unit_price),
            discount_percentage=float(item.discount_percent or 0),
            discount_amount=float(item.discount_amount or 0),
            taxable_amount=float(item.taxable_amount),
            gst_rate=float(item.gst_rate),
            cgst_rate=float(item.gst_rate / 2),
            sgst_rate=float(item.gst_rate / 2),
            igst_rate=0.0,
            cgst_amount=float(item.cgst_amount or 0),
            sgst_amount=float(item.sgst_amount or 0),
            igst_amount=float(item.igst_amount or 0),
            total_amount=float(item.total_amount),
        )
        db.add(po_item)

    # Update proforma status
    proforma.status = ProformaStatus.CONVERTED_TO_PO
    proforma.purchase_order_id = po.id

    await db.commit()

    # Reload PO with items
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == po.id)
    )
    po = result.scalar_one()

    return po


@router.delete("/proformas/{proforma_id}")
async def cancel_vendor_proforma(
    proforma_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Cancel a vendor proforma invoice."""
    proforma = await db.get(VendorProformaInvoice, proforma_id)
    if not proforma:
        raise HTTPException(status_code=404, detail="Vendor Proforma not found")

    if proforma.status == ProformaStatus.CONVERTED_TO_PO:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel proforma that has been converted to PO"
        )

    proforma.status = ProformaStatus.CANCELLED
    await db.commit()

    return {"message": "Vendor Proforma cancelled successfully"}


@router.get("/proformas/{proforma_id}/download")
async def download_vendor_proforma(
    proforma_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Download vendor proforma invoice as printable HTML."""
    from fastapi.responses import HTMLResponse
    from app.models.company import Company

    result = await db.execute(
        select(VendorProformaInvoice)
        .options(
            selectinload(VendorProformaInvoice.items),
            selectinload(VendorProformaInvoice.vendor),
        )
        .where(VendorProformaInvoice.id == proforma_id)
    )
    proforma = result.scalar_one_or_none()

    if not proforma:
        raise HTTPException(status_code=404, detail="Vendor Proforma not found")

    # Get company details
    company_result = await db.execute(select(Company).where(Company.is_primary == True).limit(1))
    company = company_result.scalar_one_or_none()
    if not company:
        company_result = await db.execute(select(Company).limit(1))
        company = company_result.scalar_one_or_none()

    vendor = proforma.vendor
    status_val = proforma.status.value if hasattr(proforma.status, 'value') else str(proforma.status) if proforma.status else ""
    status_color = "green" if status_val in ["APPROVED", "CONVERTED_TO_PO"] else "red" if status_val in ["REJECTED", "CANCELLED", "EXPIRED"] else "orange"

    # Generate items rows
    items_html = ""
    for idx, item in enumerate(proforma.items, 1):
        items_html += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td>
                <strong>{item.description}</strong><br>
                <small>Code: {item.item_code or 'N/A'} | HSN: {item.hsn_code or 'N/A'}</small>
            </td>
            <td style="text-align: center;">{item.quantity} {item.uom}</td>
            <td style="text-align: right;">₹{float(item.unit_price or 0):,.2f}</td>
            <td style="text-align: right;">{float(item.discount_percent or 0):.1f}%</td>
            <td style="text-align: right;">₹{float(item.taxable_amount or 0):,.2f}</td>
            <td style="text-align: center;">{float(item.gst_rate or 0):.0f}%</td>
            <td style="text-align: right;">₹{float(item.total_amount or 0):,.2f}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Vendor Proforma - {proforma.our_reference}</title>
        <style>
            @media print {{
                body {{ margin: 0; padding: 20px; }}
                .no-print {{ display: none; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }}
            .company-name {{
                font-size: 24px;
                font-weight: bold;
                color: #0066cc;
            }}
            .document-title {{
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                background: #e6f0ff;
                padding: 10px;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                color: white;
                background: {status_color};
            }}
            .info-section {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .info-box {{
                width: 48%;
                background: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
            }}
            .info-box h3 {{
                margin: 0 0 10px 0;
                color: #0066cc;
                font-size: 14px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .info-box p {{
                margin: 5px 0;
                font-size: 12px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th {{
                background: #0066cc;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 12px;
            }}
            td {{
                border: 1px solid #ddd;
                padding: 10px 8px;
                font-size: 12px;
            }}
            .totals-section {{
                margin-left: auto;
                width: 350px;
            }}
            .totals-section table td {{
                padding: 8px;
            }}
            .totals-section .grand-total {{
                background: #e6f0ff;
                font-size: 16px;
                font-weight: bold;
            }}
            .terms-box {{
                background: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .signatures {{
                display: flex;
                justify-content: space-between;
                margin-top: 60px;
            }}
            .signature-box {{
                text-align: center;
                width: 200px;
            }}
            .signature-line {{
                border-top: 1px solid #333;
                margin-top: 40px;
                padding-top: 5px;
            }}
            .print-btn {{
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 10px 20px;
                background: #0066cc;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <button class="print-btn no-print" onclick="window.print()">Print / Save PDF</button>

        <div class="header">
            <div class="company-name">{company.legal_name if company else 'AQUAPURITE PRIVATE LIMITED'}</div>
            <div style="font-size: 12px; color: #666;">
                {company.address_line1 if company else 'PLOT 36-A, KH NO 181, PH-1, SHYAM VIHAR, DINDAPUR EXT'}, {company.city if company else 'New Delhi'} - {company.pincode if company else '110043'}, {company.state if company else 'Delhi'}<br>
                GSTIN: {company.gstin if company else '07ABDCA6170C1Z0'} | PAN: {company.pan if company else 'ABDCA6170C'}
            </div>
            <div class="document-title">VENDOR PROFORMA INVOICE / QUOTATION</div>
        </div>

        <div style="text-align: center; margin-bottom: 20px;">
            <span class="status-badge">{status_val}</span>
        </div>

        <div class="info-section">
            <div class="info-box">
                <h3>VENDOR DETAILS</h3>
                <p><strong>{vendor.legal_name if vendor else 'N/A'}</strong></p>
                <p>{vendor.address_line1 if vendor and vendor.address_line1 else ''} {vendor.address_line2 if vendor and vendor.address_line2 else ''}</p>
                <p>{vendor.city if vendor else ''}, {vendor.state if vendor else ''} - {vendor.pincode if vendor else ''}</p>
                <p>GSTIN: {vendor.gstin if vendor else 'N/A'}</p>
                <p>PAN: {vendor.pan if vendor else 'N/A'}</p>
            </div>
            <div class="info-box">
                <h3>PROFORMA DETAILS</h3>
                <p><strong>Our Reference:</strong> {proforma.our_reference}</p>
                <p><strong>Vendor PI Number:</strong> {proforma.proforma_number}</p>
                <p><strong>PI Date:</strong> {proforma.proforma_date}</p>
                <p><strong>Valid Until:</strong> {proforma.validity_date or 'Not Specified'}</p>
                <p><strong>Delivery Days:</strong> {proforma.delivery_days or 'N/A'} days</p>
                <p><strong>Credit Days:</strong> {proforma.credit_days or 0} days</p>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 40px;">#</th>
                    <th>Item Description</th>
                    <th style="width: 80px; text-align: center;">Qty</th>
                    <th style="width: 90px; text-align: right;">Unit Price</th>
                    <th style="width: 60px; text-align: right;">Disc%</th>
                    <th style="width: 100px; text-align: right;">Taxable</th>
                    <th style="width: 60px; text-align: center;">GST%</th>
                    <th style="width: 100px; text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div class="totals-section">
            <table>
                <tr>
                    <td>Subtotal</td>
                    <td style="text-align: right;">₹{float(proforma.subtotal or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>Discount ({float(proforma.discount_percent or 0):.1f}%)</td>
                    <td style="text-align: right;">- ₹{float(proforma.discount_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>Taxable Amount</td>
                    <td style="text-align: right;">₹{float(proforma.taxable_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>CGST</td>
                    <td style="text-align: right;">₹{float(proforma.cgst_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>SGST</td>
                    <td style="text-align: right;">₹{float(proforma.sgst_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>IGST</td>
                    <td style="text-align: right;">₹{float(proforma.igst_amount or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>Freight Charges</td>
                    <td style="text-align: right;">₹{float(proforma.freight_charges or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>Packing Charges</td>
                    <td style="text-align: right;">₹{float(proforma.packing_charges or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>Other Charges</td>
                    <td style="text-align: right;">₹{float(proforma.other_charges or 0):,.2f}</td>
                </tr>
                <tr>
                    <td>Round Off</td>
                    <td style="text-align: right;">₹{float(proforma.round_off or 0):,.2f}</td>
                </tr>
                <tr class="grand-total">
                    <td><strong>GRAND TOTAL</strong></td>
                    <td style="text-align: right;"><strong>₹{float(proforma.grand_total or 0):,.2f}</strong></td>
                </tr>
            </table>
        </div>

        <div class="terms-box">
            <h3 style="margin: 0 0 10px 0;">Terms & Conditions</h3>
            <p><strong>Payment Terms:</strong> {proforma.payment_terms or 'As per agreement'}</p>
            <p><strong>Delivery Terms:</strong> {proforma.delivery_terms or 'Ex-Works'}</p>
            <p><strong>Vendor Remarks:</strong> {proforma.vendor_remarks or 'None'}</p>
            <p><strong>Internal Notes:</strong> {proforma.internal_notes or 'None'}</p>
        </div>

        <div class="signatures">
            <div class="signature-box">
                <div class="signature-line">Prepared By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Reviewed By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Approved By</div>
            </div>
        </div>

        <p style="text-align: center; font-size: 10px; color: #999; margin-top: 40px;">
            This is a computer-generated document. Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
