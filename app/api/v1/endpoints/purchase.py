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

@router.get("/orders/{po_id}/download")
async def download_purchase_order(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Download Purchase Order as printable HTML (can be saved as PDF via browser)."""
    from fastapi.responses import HTMLResponse

    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

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

    # Build items table
    items_html = ""
    for idx, item in enumerate(po.items, 1):
        unit_price = float(item.unit_price) if item.unit_price else 0.0
        taxable = float(item.taxable_amount) if item.taxable_amount else 0.0
        gst = float(item.gst_rate) if item.gst_rate else 0.0
        total = float(item.total_amount) if item.total_amount else 0.0

        items_html += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{idx}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.product_name or '-'}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.sku or '-'}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.hsn_code or '-'}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{item.quantity_ordered}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.uom or 'PCS'}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">₹{unit_price:,.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">₹{taxable:,.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{gst}%</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">₹{total:,.2f}</td>
        </tr>
        """

    vendor_name = vendor.legal_name if vendor else po.vendor_name
    vendor_address = ""
    if vendor:
        addr_parts = [vendor.address_line1, vendor.address_line2, vendor.city, vendor.state, str(vendor.pincode) if vendor.pincode else None]
        vendor_address = ", ".join(filter(None, addr_parts))

    warehouse_name = warehouse.name if warehouse else "N/A"
    warehouse_address = ""
    if warehouse:
        addr_parts = [warehouse.address_line1, warehouse.city, warehouse.state, warehouse.pincode]
        warehouse_address = ", ".join(filter(None, [str(p) for p in addr_parts if p]))

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Purchase Order - {po.po_number}</title>
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
                color: #1a73e8;
            }}
            .document-title {{
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                background: #f5f5f5;
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
                color: #1a73e8;
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
                background: #1a73e8;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 11px;
            }}
            .totals {{
                width: 300px;
                margin-left: auto;
            }}
            .totals tr td {{
                padding: 8px;
                border: 1px solid #ddd;
            }}
            .totals tr:last-child {{
                background: #1a73e8;
                color: white;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 40px;
                border-top: 1px solid #ddd;
                padding-top: 20px;
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
                background: #1a73e8;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            .status-approved {{ background: #e6f4ea; color: #137333; }}
            .status-draft {{ background: #fce8e6; color: #c5221f; }}
            .status-pending {{ background: #fef7e0; color: #b06000; }}
        </style>
    </head>
    <body>
        <button class="print-btn no-print" onclick="window.print()">🖨️ Print / Save PDF</button>

        <div class="header">
            <div class="company-name">AQUAPURITE INDIA PVT LTD</div>
            <div style="font-size: 12px; color: #666;">
                123 Industrial Area, Sector 5, Noida, UP - 201301<br>
                GSTIN: 09AAACA1234M1Z5 | PAN: AAACA1234M
            </div>
            <div class="document-title">PURCHASE ORDER</div>
        </div>

        <div class="info-section">
            <div class="info-box">
                <h3>VENDOR DETAILS</h3>
                <p><strong>{vendor_name}</strong></p>
                <p>{vendor_address}</p>
                <p>GSTIN: {po.vendor_gstin or 'N/A'}</p>
            </div>
            <div class="info-box">
                <h3>PO DETAILS</h3>
                <p><strong>PO Number:</strong> {po.po_number}</p>
                <p><strong>PO Date:</strong> {po.po_date}</p>
                <p><strong>Expected Delivery:</strong> {po.expected_delivery_date or 'TBD'}</p>
                <p><strong>Status:</strong> <span class="status-badge status-{'approved' if po.status.value == 'APPROVED' else 'draft'}">{po.status.value}</span></p>
                <p><strong>Payment Terms:</strong> {po.credit_days or 0} days credit</p>
            </div>
        </div>

        <div class="info-section">
            <div class="info-box" style="width: 100%;">
                <h3>DELIVERY ADDRESS</h3>
                <p><strong>{warehouse_name}</strong></p>
                <p>{warehouse_address}</p>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">#</th>
                    <th>Product</th>
                    <th>SKU</th>
                    <th>HSN</th>
                    <th style="width: 50px;">Qty</th>
                    <th>UOM</th>
                    <th style="width: 80px;">Unit Price</th>
                    <th style="width: 90px;">Taxable</th>
                    <th style="width: 50px;">GST%</th>
                    <th style="width: 90px;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <table class="totals">
            <tr>
                <td>Subtotal</td>
                <td style="text-align: right;">₹{float(po.subtotal or 0):,.2f}</td>
            </tr>
            <tr>
                <td>Discount</td>
                <td style="text-align: right;">₹{float(po.discount_amount or 0):,.2f}</td>
            </tr>
            <tr>
                <td>Taxable Amount</td>
                <td style="text-align: right;">₹{float(po.taxable_amount or 0):,.2f}</td>
            </tr>
            <tr>
                <td>CGST</td>
                <td style="text-align: right;">₹{float(po.cgst_amount or 0):,.2f}</td>
            </tr>
            <tr>
                <td>SGST</td>
                <td style="text-align: right;">₹{float(po.sgst_amount or 0):,.2f}</td>
            </tr>
            <tr>
                <td>IGST</td>
                <td style="text-align: right;">₹{float(po.igst_amount or 0):,.2f}</td>
            </tr>
            <tr>
                <td>Freight Charges</td>
                <td style="text-align: right;">₹{float(po.freight_charges or 0):,.2f}</td>
            </tr>
            <tr>
                <td><strong>Grand Total</strong></td>
                <td style="text-align: right;"><strong>₹{float(po.grand_total or 0):,.2f}</strong></td>
            </tr>
        </table>

        <div class="footer">
            <p><strong>Terms & Conditions:</strong></p>
            <p style="font-size: 11px;">{po.terms_and_conditions or 'Standard terms and conditions apply.'}</p>

            <p><strong>Special Instructions:</strong></p>
            <p style="font-size: 11px;">{po.special_instructions or 'None'}</p>
        </div>

        <div class="signatures">
            <div class="signature-box">
                <div class="signature-line">Prepared By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Approved By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line">Vendor Signature</div>
            </div>
        </div>

        <p style="text-align: center; font-size: 10px; color: #999; margin-top: 40px;">
            This is a computer-generated document. Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/grn/{grn_id}/download")
async def download_grn(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Download Goods Receipt Note as printable HTML."""
    from fastapi.responses import HTMLResponse

    result = await db.execute(
        select(GoodsReceiptNote)
        .options(selectinload(GoodsReceiptNote.items))
        .where(GoodsReceiptNote.id == grn_id)
    )
    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

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
            <div class="company-name">AQUAPURITE INDIA PVT LTD</div>
            <div style="font-size: 12px; color: #666;">
                123 Industrial Area, Sector 5, Noida, UP - 201301
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

    result = await db.execute(
        select(VendorInvoice).where(VendorInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Vendor Invoice not found")

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

    status_color = "green" if invoice.status and invoice.status.value in ["VERIFIED", "PAID"] else "orange"

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
            <div class="company-name">AQUAPURITE INDIA PVT LTD</div>
            <div style="font-size: 12px; color: #666;">
                123 Industrial Area, Sector 5, Noida, UP - 201301<br>
                GSTIN: 09AAACA1234M1Z5
            </div>
            <div class="document-title">VENDOR INVOICE RECORD</div>
        </div>

        <div class="info-section">
            <div class="info-box">
                <h3>VENDOR DETAILS</h3>
                <p><strong>{vendor_name}</strong></p>
                <p>{vendor_address}</p>
                <p>GSTIN: {invoice.vendor_gstin or 'N/A'}</p>
            </div>
            <div class="info-box">
                <h3>INVOICE DETAILS</h3>
                <p><strong>Invoice Number:</strong> {invoice.invoice_number}</p>
                <p><strong>Invoice Date:</strong> {invoice.invoice_date}</p>
                <p><strong>Due Date:</strong> {invoice.due_date or 'N/A'}</p>
                <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{invoice.status.value if invoice.status else 'N/A'}</span></p>
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
                    <div class="value" style="color: #ea4335;">₹{float(invoice.total_amount or 0):,.2f}</div>
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
                    <td style="text-align: right;">₹{float(invoice.net_payable or invoice.total_amount or 0):,.2f}</td>
                </tr>
            </tbody>
        </table>

        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 10px 0; color: #333;">3-WAY MATCH STATUS</h3>
            <p>
                <strong>PO Match:</strong>
                <span class="match-status {'match-yes' if invoice.po_match else 'match-no'}">
                    {'✓ Matched' if invoice.po_match else '✗ Not Matched'}
                </span>
            </p>
            <p>
                <strong>GRN Match:</strong>
                <span class="match-status {'match-yes' if invoice.grn_match else 'match-no'}">
                    {'✓ Matched' if invoice.grn_match else '✗ Not Matched'}
                </span>
            </p>
            <p>
                <strong>Invoice Match:</strong>
                <span class="match-status {'match-yes' if invoice.invoice_match else 'match-no'}">
                    {'✓ Matched' if invoice.invoice_match else '✗ Not Matched'}
                </span>
            </p>
            {f'<p><strong>Discrepancy:</strong> {invoice.match_discrepancy}</p>' if invoice.match_discrepancy else ''}
        </div>

        <p><strong>Remarks:</strong> {invoice.remarks or 'None'}</p>

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
