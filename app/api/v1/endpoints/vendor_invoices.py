"""Vendor Invoice API endpoints for 3-way matching."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.purchase import (
    VendorInvoice, VendorInvoiceStatus,
    PurchaseOrder, GoodsReceiptNote
)
from app.models.vendor import Vendor
from app.models.accounting import ChartOfAccount, CostCenter
from uuid import uuid4
from datetime import date as date_type
from app.services.auto_journal_service import AutoJournalService, AutoJournalError

router = APIRouter()


# ==================== Schemas ====================

class VendorInvoiceCreate(BaseModel):
    vendor_id: UUID
    invoice_number: str
    invoice_date: date
    # Invoice type: PO_INVOICE (procurement) or EXPENSE_INVOICE (non-PO)
    invoice_type: str = "PO_INVOICE"
    # For PO Invoices
    purchase_order_id: Optional[UUID] = None
    grn_id: Optional[UUID] = None
    # For Expense Invoices (non-PO)
    gl_account_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    expense_category: Optional[str] = None
    expense_description: Optional[str] = None
    # Amounts
    subtotal: Decimal
    discount_amount: Decimal = Decimal("0")
    taxable_amount: Decimal
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    cess_amount: Decimal = Decimal("0")
    freight_charges: Decimal = Decimal("0")
    other_charges: Decimal = Decimal("0")
    round_off: Decimal = Decimal("0")
    grand_total: Decimal
    due_date: date
    tds_applicable: bool = True
    tds_section: Optional[str] = None
    tds_rate: Decimal = Decimal("0")
    vendor_irn: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    internal_notes: Optional[str] = None


class ThreeWayMatchRequest(BaseModel):
    invoice_id: UUID
    po_id: UUID
    grn_id: UUID
    tolerance_percentage: Decimal = Decimal("1")  # Allow 1% variance


# ==================== Endpoints ====================

@router.get("/next-reference")
async def get_next_reference(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get the next vendor invoice reference number."""
    today = date_type.today()
    random_suffix = str(uuid4())[:8].upper()
    next_ref = f"VI-{today.strftime('%Y%m%d')}-{random_suffix}"
    return {"reference": next_ref}


@router.get("/gl-accounts")
async def get_gl_accounts_dropdown(
    db: DB,
    current_user: User = Depends(get_current_user),
    account_type: Optional[str] = Query(None, description="Filter by account type: ASSET, EXPENSE"),
):
    """Get GL accounts for dropdown (for expense invoice coding)."""
    query = select(ChartOfAccount).where(
        ChartOfAccount.is_active == True,
        ChartOfAccount.allow_direct_posting == True,
    )

    if account_type:
        query = query.where(ChartOfAccount.account_type == account_type.upper())
    else:
        # Default: show ASSET and EXPENSE accounts for vendor invoices
        query = query.where(ChartOfAccount.account_type.in_(["ASSET", "EXPENSE"]))

    query = query.order_by(ChartOfAccount.account_code)
    result = await db.execute(query)
    accounts = result.scalars().all()

    return [
        {
            "id": str(acc.id),
            "account_code": acc.account_code,
            "account_name": acc.account_name,
            "account_type": acc.account_type,
            "account_sub_type": acc.account_sub_type,
        }
        for acc in accounts
    ]


@router.get("/expense-categories")
async def get_expense_categories(
    current_user: User = Depends(get_current_user),
):
    """Get expense categories for dropdown."""
    categories = [
        {"value": "FIXED_ASSET", "label": "Fixed Asset (Laptop, Furniture, Equipment)"},
        {"value": "SERVICE", "label": "Professional Services (Consulting, Legal)"},
        {"value": "UTILITIES", "label": "Utilities (Electricity, Water, Internet)"},
        {"value": "RENT", "label": "Rent & Lease"},
        {"value": "TRAVEL", "label": "Travel & Conveyance"},
        {"value": "OFFICE_SUPPLIES", "label": "Office Supplies & Stationery"},
        {"value": "REPAIRS", "label": "Repairs & Maintenance"},
        {"value": "INSURANCE", "label": "Insurance"},
        {"value": "SUBSCRIPTION", "label": "Software & Subscriptions"},
        {"value": "MARKETING", "label": "Marketing & Advertising"},
        {"value": "OTHER", "label": "Other Expenses"},
    ]
    return categories


@router.get("")
async def list_vendor_invoices(
    db: DB,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    vendor_id: Optional[UUID] = None,
    invoice_type: Optional[str] = Query(None, description="PO_INVOICE or EXPENSE_INVOICE"),
    is_matched: Optional[bool] = None,
    is_overdue: Optional[bool] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
):
    """List vendor invoices with filtering."""
    query = select(VendorInvoice).options(
        selectinload(VendorInvoice.vendor),
        selectinload(VendorInvoice.purchase_order),
        selectinload(VendorInvoice.grn),
        selectinload(VendorInvoice.gl_account),
        selectinload(VendorInvoice.cost_center),
    )

    conditions = []

    if status:
        conditions.append(VendorInvoice.status == status.upper())

    if vendor_id:
        conditions.append(VendorInvoice.vendor_id == vendor_id)

    if invoice_type:
        conditions.append(VendorInvoice.invoice_type == invoice_type.upper())

    if is_matched is not None:
        conditions.append(VendorInvoice.is_fully_matched == is_matched)

    if is_overdue:
        conditions.append(
            and_(
                VendorInvoice.due_date < date.today(),
                VendorInvoice.balance_due > 0
            )
        )

    if start_date:
        conditions.append(VendorInvoice.invoice_date >= start_date)

    if end_date:
        conditions.append(VendorInvoice.invoice_date <= end_date)

    if search:
        conditions.append(
            or_(
                VendorInvoice.our_reference.ilike(f"%{search}%"),
                VendorInvoice.invoice_number.ilike(f"%{search}%"),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(VendorInvoice)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(desc(VendorInvoice.created_at))
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    return {
        "items": [
            {
                "id": str(inv.id),
                "our_reference": inv.our_reference,
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                "invoice_type": inv.invoice_type or "PO_INVOICE",
                "status": inv.status,
                "vendor_id": str(inv.vendor_id),
                "vendor_name": inv.vendor.name if inv.vendor else None,
                "vendor_code": inv.vendor.vendor_code if inv.vendor else None,
                # PO Invoice fields
                "po_number": inv.purchase_order.po_number if inv.purchase_order else None,
                "grn_number": inv.grn.grn_number if inv.grn else None,
                # Expense Invoice fields
                "gl_account_id": str(inv.gl_account_id) if inv.gl_account_id else None,
                "gl_account_name": inv.gl_account.account_name if inv.gl_account else None,
                "cost_center_id": str(inv.cost_center_id) if inv.cost_center_id else None,
                "cost_center_name": inv.cost_center.name if inv.cost_center else None,
                "expense_category": inv.expense_category,
                "expense_description": inv.expense_description,
                # Amounts
                "subtotal": float(inv.subtotal),
                "taxable_amount": float(inv.taxable_amount),
                "cgst_amount": float(inv.cgst_amount),
                "sgst_amount": float(inv.sgst_amount),
                "igst_amount": float(inv.igst_amount),
                "total_tax": float(inv.total_tax),
                "grand_total": float(inv.grand_total),
                "amount_paid": float(inv.amount_paid),
                "balance_due": float(inv.balance_due),
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "is_overdue": inv.is_overdue,
                "days_overdue": inv.days_overdue,
                # Match status (for PO invoices)
                "is_fully_matched": inv.is_fully_matched,
                "po_matched": inv.po_matched,
                "grn_matched": inv.grn_matched,
                # Computed match_status for frontend
                "match_status": (
                    "MATCHED" if inv.is_fully_matched else
                    "PARTIAL" if (inv.po_matched or inv.grn_matched) else
                    "MISMATCH" if inv.status == "MISMATCH" else
                    "NOT_MATCHED"
                ),
                # Computed payment_status for frontend
                "payment_status": (
                    "UNPAID" if inv.grand_total <= 0 else  # No amount = unpaid
                    "PAID" if inv.balance_due <= 0 else
                    "PARTIAL" if inv.amount_paid > 0 else
                    "UNPAID"
                ),
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            }
            for inv in invoices
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/stats")
async def get_invoice_stats(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get vendor invoice statistics."""
    today = date.today()

    # Total invoices count
    total_query = select(func.count()).select_from(VendorInvoice)
    total_invoices = await db.scalar(total_query) or 0

    # Pending review (RECEIVED + UNDER_VERIFICATION)
    pending_review_query = select(func.count()).select_from(VendorInvoice).where(
        VendorInvoice.status.in_(["RECEIVED", "UNDER_VERIFICATION"])
    )
    pending_review = await db.scalar(pending_review_query) or 0

    # Matched count
    matched_query = select(func.count()).select_from(VendorInvoice).where(
        VendorInvoice.status == "MATCHED"
    )
    matched = await db.scalar(matched_query) or 0

    # Mismatch count
    mismatch_query = select(func.count()).select_from(VendorInvoice).where(
        VendorInvoice.status == "MISMATCH"
    )
    mismatch = await db.scalar(mismatch_query) or 0

    # Overdue count (due_date < today and balance_due > 0)
    overdue_count_query = select(func.count()).select_from(VendorInvoice).where(
        and_(
            VendorInvoice.due_date < today,
            VendorInvoice.balance_due > 0
        )
    )
    overdue = await db.scalar(overdue_count_query) or 0

    # Total pending amount
    pending_query = select(func.sum(VendorInvoice.balance_due)).where(
        VendorInvoice.balance_due > 0
    )
    pending_amount = await db.scalar(pending_query) or Decimal("0")

    # Total overdue amount
    overdue_query = select(func.sum(VendorInvoice.balance_due)).where(
        and_(
            VendorInvoice.due_date < today,
            VendorInvoice.balance_due > 0
        )
    )
    overdue_amount = await db.scalar(overdue_query) or Decimal("0")

    return {
        "total_invoices": total_invoices,
        "pending_review": pending_review,
        "matched": matched,
        "mismatch": mismatch,
        "overdue": overdue,
        "total_pending_amount": float(pending_amount),
        "total_overdue_amount": float(overdue_amount),
    }


@router.get("/{invoice_id}")
async def get_vendor_invoice(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get vendor invoice details."""
    query = select(VendorInvoice).options(
        selectinload(VendorInvoice.vendor),
        selectinload(VendorInvoice.purchase_order),
        selectinload(VendorInvoice.grn),
        selectinload(VendorInvoice.received_by_user),
        selectinload(VendorInvoice.verified_by_user),
        selectinload(VendorInvoice.approved_by_user),
    ).where(VendorInvoice.id == invoice_id)

    result = await db.execute(query)
    inv = result.scalar_one_or_none()

    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor invoice not found"
        )

    return {
        "id": str(inv.id),
        "our_reference": inv.our_reference,
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "status": inv.status,
        "vendor": {
            "id": str(inv.vendor_id),
            "name": inv.vendor.name if inv.vendor else None,
        },
        "purchase_order": {
            "id": str(inv.purchase_order_id) if inv.purchase_order_id else None,
            "po_number": inv.purchase_order.po_number if inv.purchase_order else None,
        } if inv.purchase_order_id else None,
        "grn": {
            "id": str(inv.grn_id) if inv.grn_id else None,
            "grn_number": inv.grn.grn_number if inv.grn else None,
        } if inv.grn_id else None,
        "subtotal": float(inv.subtotal),
        "discount_amount": float(inv.discount_amount),
        "taxable_amount": float(inv.taxable_amount),
        "cgst_amount": float(inv.cgst_amount),
        "sgst_amount": float(inv.sgst_amount),
        "igst_amount": float(inv.igst_amount),
        "cess_amount": float(inv.cess_amount),
        "total_tax": float(inv.total_tax),
        "freight_charges": float(inv.freight_charges),
        "other_charges": float(inv.other_charges),
        "round_off": float(inv.round_off),
        "grand_total": float(inv.grand_total),
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "amount_paid": float(inv.amount_paid),
        "balance_due": float(inv.balance_due),
        "is_overdue": inv.is_overdue,
        "days_overdue": inv.days_overdue,
        "tds_applicable": inv.tds_applicable,
        "tds_section": inv.tds_section,
        "tds_rate": float(inv.tds_rate),
        "tds_amount": float(inv.tds_amount),
        "net_payable": float(inv.net_payable),
        "po_matched": inv.po_matched,
        "grn_matched": inv.grn_matched,
        "is_fully_matched": inv.is_fully_matched,
        "matching_variance": float(inv.matching_variance),
        "variance_reason": inv.variance_reason,
        "vendor_irn": inv.vendor_irn,
        "vendor_ack_number": inv.vendor_ack_number,
        "invoice_pdf_url": inv.invoice_pdf_url,
        "internal_notes": inv.internal_notes,
        "received_by": inv.received_by_user.email if inv.received_by_user else None,
        "received_at": inv.received_at.isoformat() if inv.received_at else None,
        "verified_by": inv.verified_by_user.email if inv.verified_by_user else None,
        "verified_at": inv.verified_at.isoformat() if inv.verified_at else None,
        "approved_by": inv.approved_by_user.email if inv.approved_by_user else None,
        "approved_at": inv.approved_at.isoformat() if inv.approved_at else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_vendor_invoice(
    data: VendorInvoiceCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new vendor invoice."""
    # Validate vendor
    vendor = await db.get(Vendor, data.vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Check for duplicate
    existing_query = select(VendorInvoice).where(
        and_(
            VendorInvoice.vendor_id == data.vendor_id,
            VendorInvoice.invoice_number == data.invoice_number
        )
    )
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice with this number already exists for this vendor"
        )

    # Get next reference
    today = date_type.today()
    random_suffix = str(uuid4())[:8].upper()
    our_reference = f"VI-{today.strftime('%Y%m%d')}-{random_suffix}"

    # Calculate TDS and net payable
    tds_amount = (data.grand_total * data.tds_rate / 100) if data.tds_applicable else Decimal("0")
    net_payable = data.grand_total - tds_amount
    total_tax = data.cgst_amount + data.sgst_amount + data.igst_amount + data.cess_amount

    invoice = VendorInvoice(
        our_reference=our_reference,
        invoice_number=data.invoice_number,
        invoice_date=data.invoice_date,
        invoice_type=data.invoice_type or "PO_INVOICE",
        status="RECEIVED",
        vendor_id=data.vendor_id,
        # PO Invoice fields
        purchase_order_id=data.purchase_order_id,
        grn_id=data.grn_id,
        # Expense Invoice fields
        gl_account_id=data.gl_account_id,
        cost_center_id=data.cost_center_id,
        expense_category=data.expense_category,
        expense_description=data.expense_description,
        # Amounts
        subtotal=data.subtotal,
        discount_amount=data.discount_amount,
        taxable_amount=data.taxable_amount,
        cgst_amount=data.cgst_amount,
        sgst_amount=data.sgst_amount,
        igst_amount=data.igst_amount,
        cess_amount=data.cess_amount,
        total_tax=total_tax,
        freight_charges=data.freight_charges,
        other_charges=data.other_charges,
        round_off=data.round_off,
        grand_total=data.grand_total,
        due_date=data.due_date,
        balance_due=net_payable,  # Initially balance = net payable
        tds_applicable=data.tds_applicable,
        tds_section=data.tds_section,
        tds_rate=data.tds_rate,
        tds_amount=tds_amount,
        net_payable=net_payable,
        vendor_irn=data.vendor_irn,
        invoice_pdf_url=data.invoice_pdf_url,
        internal_notes=data.internal_notes,
        received_by=current_user.id,
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    return {
        "id": str(invoice.id),
        "our_reference": invoice.our_reference,
        "message": "Vendor invoice created successfully",
    }


@router.post("/three-way-match")
async def perform_three_way_match(
    data: ThreeWayMatchRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Perform 3-way matching between PO, GRN, and Vendor Invoice.

    Checks:
    1. PO amount vs Invoice amount
    2. GRN received quantity/value vs Invoice amount
    3. Variance within tolerance
    """
    # Get all documents
    invoice = await db.get(VendorInvoice, data.invoice_id)
    po = await db.get(PurchaseOrder, data.po_id)
    grn = await db.get(GoodsReceiptNote, data.grn_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    # Verify relationships
    if grn.purchase_order_id != po.id:
        raise HTTPException(
            status_code=400,
            detail="GRN is not linked to the specified PO"
        )

    # Calculate matching
    po_amount = po.grand_total
    grn_value = grn.total_value
    invoice_amount = invoice.grand_total

    # Check PO match
    po_variance = abs(invoice_amount - po_amount)
    po_variance_pct = (po_variance / po_amount * 100) if po_amount > 0 else Decimal("0")
    po_matched = po_variance_pct <= data.tolerance_percentage

    # Check GRN match
    grn_variance = abs(invoice_amount - grn_value)
    grn_variance_pct = (grn_variance / grn_value * 100) if grn_value > 0 else Decimal("0")
    grn_matched = grn_variance_pct <= data.tolerance_percentage

    # Overall match
    is_fully_matched = po_matched and grn_matched
    total_variance = max(po_variance, grn_variance)

    # Update invoice
    invoice.purchase_order_id = po.id
    invoice.grn_id = grn.id
    invoice.po_matched = po_matched
    invoice.grn_matched = grn_matched
    invoice.is_fully_matched = is_fully_matched
    invoice.matching_variance = total_variance

    if is_fully_matched:
        invoice.status = "MATCHED"
    elif po_matched or grn_matched:
        invoice.status = "PARTIALLY_MATCHED"
        invoice.variance_reason = f"PO variance: {po_variance_pct:.2f}%, GRN variance: {grn_variance_pct:.2f}%"
    else:
        invoice.status = "MISMATCH"
        invoice.variance_reason = f"PO variance: {po_variance_pct:.2f}%, GRN variance: {grn_variance_pct:.2f}%"

    invoice.verified_by = current_user.id
    invoice.verified_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "invoice_id": str(invoice.id),
        "po_id": str(po.id),
        "grn_id": str(grn.id),
        "matching_result": {
            "po_matched": po_matched,
            "po_amount": float(po_amount),
            "po_variance": float(po_variance),
            "po_variance_pct": float(po_variance_pct),
            "grn_matched": grn_matched,
            "grn_value": float(grn_value),
            "grn_variance": float(grn_variance),
            "grn_variance_pct": float(grn_variance_pct),
            "invoice_amount": float(invoice_amount),
            "is_fully_matched": is_fully_matched,
            "status": invoice.status,
        },
    }


@router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve a vendor invoice for payment and create journal entry."""
    invoice = await db.get(VendorInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Different approval rules for PO vs Expense invoices
    if invoice.invoice_type == "EXPENSE_INVOICE":
        # Expense invoices can be approved from RECEIVED, UNDER_REVIEW, or UNDER_VERIFICATION
        allowed_statuses = ["RECEIVED", "UNDER_REVIEW", "UNDER_VERIFICATION"]
        if invoice.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve expense invoice with status {invoice.status}. Must be in {allowed_statuses}"
            )
    else:
        # PO invoices require 3-way matching first
        if invoice.status not in ["MATCHED", "PARTIALLY_MATCHED"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve PO invoice with status {invoice.status}. Complete 3-way matching first."
            )

    invoice.status = "APPROVED"
    invoice.approved_by = current_user.id
    invoice.approved_at = datetime.now(timezone.utc)

    # Auto-generate journal entry for vendor invoice approval
    journal_entry = None
    try:
        auto_journal_service = AutoJournalService(db)
        journal_entry = await auto_journal_service.generate_for_vendor_invoice(
            vendor_invoice_id=invoice_id,
            user_id=current_user.id,
            auto_post=True  # Auto-post the journal entry
        )
    except AutoJournalError as e:
        # Log the error but don't fail the approval
        import logging
        logging.warning(f"Failed to auto-generate journal for vendor invoice {invoice.invoice_number}: {e.message}")

    await db.commit()

    return {
        "message": "Invoice approved and journal entry created",
        "status": invoice.status,
        "journal_entry_id": str(journal_entry.id) if journal_entry else None
    }


class VendorInvoiceUpdate(BaseModel):
    """Schema for updating vendor invoice."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    invoice_type: Optional[str] = None  # PO_INVOICE or EXPENSE_INVOICE
    purchase_order_id: Optional[UUID] = None
    grn_id: Optional[UUID] = None
    # Expense invoice fields
    gl_account_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    expense_category: Optional[str] = None
    expense_description: Optional[str] = None
    # Amount fields
    subtotal: Optional[Decimal] = None
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None
    due_date: Optional[date] = None
    internal_notes: Optional[str] = None


@router.put("/{invoice_id}")
async def update_vendor_invoice(
    invoice_id: UUID,
    data: VendorInvoiceUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update an existing vendor invoice."""
    invoice = await db.get(VendorInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Only allow updates on RECEIVED or UNDER_VERIFICATION status
    if invoice.status not in ["RECEIVED", "UNDER_VERIFICATION"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update invoice with status {invoice.status}. Only RECEIVED or UNDER_VERIFICATION invoices can be edited."
        )

    # Update fields if provided
    if data.invoice_number is not None:
        invoice.invoice_number = data.invoice_number
    if data.invoice_date is not None:
        invoice.invoice_date = data.invoice_date
    if data.purchase_order_id is not None:
        # Validate PO exists
        po = await db.get(PurchaseOrder, data.purchase_order_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase Order not found")
        invoice.purchase_order_id = data.purchase_order_id
    if data.grn_id is not None:
        # Validate GRN exists
        grn = await db.get(GoodsReceiptNote, data.grn_id)
        if not grn:
            raise HTTPException(status_code=404, detail="GRN not found")
        invoice.grn_id = data.grn_id

    # Invoice type and expense coding fields
    if data.invoice_type is not None:
        invoice.invoice_type = data.invoice_type
    if data.gl_account_id is not None:
        # Validate GL account exists
        gl_account = await db.get(ChartOfAccount, data.gl_account_id)
        if not gl_account:
            raise HTTPException(status_code=404, detail="GL Account not found")
        invoice.gl_account_id = data.gl_account_id
    if data.cost_center_id is not None:
        invoice.cost_center_id = data.cost_center_id
    if data.expense_category is not None:
        invoice.expense_category = data.expense_category
    if data.expense_description is not None:
        invoice.expense_description = data.expense_description

    if data.subtotal is not None:
        invoice.subtotal = data.subtotal
        invoice.taxable_amount = data.subtotal  # Sync taxable amount
    if data.taxable_amount is not None:
        invoice.taxable_amount = data.taxable_amount
    if data.cgst_amount is not None:
        invoice.cgst_amount = data.cgst_amount
    if data.sgst_amount is not None:
        invoice.sgst_amount = data.sgst_amount
    if data.igst_amount is not None:
        invoice.igst_amount = data.igst_amount
    if data.grand_total is not None:
        invoice.grand_total = data.grand_total
        # Recalculate TDS and net payable
        tds_amount = (data.grand_total * invoice.tds_rate / 100) if invoice.tds_applicable else Decimal("0")
        invoice.tds_amount = tds_amount
        invoice.net_payable = data.grand_total - tds_amount
        invoice.balance_due = invoice.net_payable - invoice.amount_paid
    if data.due_date is not None:
        invoice.due_date = data.due_date
    if data.internal_notes is not None:
        invoice.internal_notes = data.internal_notes

    # Recalculate total_tax
    invoice.total_tax = invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount + invoice.cess_amount

    await db.commit()
    await db.refresh(invoice)

    return {
        "id": str(invoice.id),
        "our_reference": invoice.our_reference,
        "invoice_number": invoice.invoice_number,
        "grand_total": float(invoice.grand_total),
        "purchase_order_id": str(invoice.purchase_order_id) if invoice.purchase_order_id else None,
        "message": "Invoice updated successfully",
    }


@router.delete("/{invoice_id}")
async def delete_vendor_invoice(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Delete a vendor invoice (only if status is RECEIVED)."""
    invoice = await db.get(VendorInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status != "RECEIVED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete invoice with status {invoice.status}. Only RECEIVED invoices can be deleted."
        )

    await db.delete(invoice)
    await db.commit()

    return {"message": "Invoice deleted successfully"}


@router.post("/{invoice_id}/record-payment")
async def record_payment(
    invoice_id: UUID,
    amount: Decimal = Body(..., embed=True),
    payment_reference: Optional[str] = Body(None, embed=True),
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """Record a payment against the invoice."""
    invoice = await db.get(VendorInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status not in ["APPROVED", "PAYMENT_INITIATED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot record payment for invoice with status {invoice.status}"
        )

    invoice.amount_paid += amount
    invoice.balance_due = invoice.net_payable - invoice.amount_paid

    if invoice.balance_due <= 0:
        invoice.status = "PAID"
        invoice.balance_due = Decimal("0")
    else:
        invoice.status = "PAYMENT_INITIATED"

    await db.commit()

    return {
        "message": "Payment recorded",
        "amount_paid": float(invoice.amount_paid),
        "balance_due": float(invoice.balance_due),
        "status": invoice.status,
    }
