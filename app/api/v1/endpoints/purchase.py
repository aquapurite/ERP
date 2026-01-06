"""API endpoints for Purchase/Procurement management (P2P Cycle)."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase import (
    PurchaseRequisition, PurchaseRequisitionItem, RequisitionStatus,
    PurchaseOrder, PurchaseOrderItem, POStatus,
    GoodsReceiptNote, GRNItem, GRNStatus, QualityCheckResult,
    VendorInvoice, VendorInvoiceStatus,
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
    # GRN Schemas
    GoodsReceiptCreate, GoodsReceiptUpdate, GoodsReceiptResponse,
    GRNListResponse, GRNBrief, GRNQualityCheckRequest, GRNPutAwayRequest,
    # Invoice Schemas
    VendorInvoiceCreate, VendorInvoiceUpdate, VendorInvoiceResponse,
    VendorInvoiceListResponse, VendorInvoiceBrief,
    ThreeWayMatchRequest, ThreeWayMatchResponse,
    # Report Schemas
    POSummaryRequest, POSummaryResponse, GRNSummaryResponse, PendingGRNResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from app.services.audit_service import AuditService

router = APIRouter()


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
        created_by=current_user.id,
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
    query = select(PurchaseRequisition).options(selectinload(PurchaseRequisition.items))
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

    return PRListResponse(
        items=[PurchaseRequisitionResponse.model_validate(pr) for pr in prs],
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
        .options(selectinload(PurchaseRequisition.items))
        .where(PurchaseRequisition.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Purchase Requisition not found")

    return pr


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

    if pr.status != RequisitionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot {request.action.lower()} PR in {pr.status.value} status"
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

    # Create PO
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

    # Load full PO with items
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
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
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    return po


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
        .options(selectinload(PurchaseOrder.items))
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
    else:
        po.status = POStatus.CANCELLED

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
    """Send PO to vendor (via email/portal)."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    if po.status not in [POStatus.APPROVED, POStatus.SENT]:
        raise HTTPException(
            status_code=400,
            detail="PO must be approved before sending to vendor"
        )

    # TODO: Generate PO PDF
    # TODO: Send email to vendor if request.send_email

    po.status = POStatus.SENT
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
        .options(selectinload(PurchaseOrder.items))
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
