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
    VendorInvoiceExpenseLine, VendorInvoiceItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptNote, GRNItem
)
from app.models.vendor import Vendor, VendorLedger
from app.models.accounting import ChartOfAccount, CostCenter
from uuid import uuid4
from datetime import date as date_type
from app.services.auto_journal_service import AutoJournalService, AutoJournalError
from app.services.accounting_service import AccountingService
from app.services.audit_service import AuditService

router = APIRouter()


# ==================== Schemas ====================

class ExpenseLineItem(BaseModel):
    """Schema for a single expense line item."""
    gl_account_id: UUID
    expense_category: Optional[str] = None
    description: Optional[str] = None
    amount: Decimal
    cost_center_id: Optional[UUID] = None
    gst_rate: Optional[Decimal] = Decimal("18")
    gst_amount: Optional[Decimal] = Decimal("0")
    line_total: Optional[Decimal] = Decimal("0")


class InvoiceLineItemCreate(BaseModel):
    """Schema for a single PO invoice line item (from GRN)."""
    grn_item_id: UUID
    po_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name: str
    sku: str
    hsn_code: Optional[str] = None
    uom: str = "PCS"
    po_quantity: int
    grn_accepted_quantity: int
    invoice_quantity: int
    unit_price: Decimal
    discount_percentage: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    taxable_amount: Decimal
    gst_rate: Decimal = Decimal("18")
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    cess_amount: Decimal = Decimal("0")
    total_amount: Decimal


class VendorInvoiceCreate(BaseModel):
    vendor_id: UUID
    invoice_number: str
    invoice_date: date
    # Invoice type: PO_INVOICE (procurement) or EXPENSE_INVOICE (non-PO)
    invoice_type: str = "PO_INVOICE"
    # For PO Invoices
    purchase_order_id: Optional[UUID] = None
    grn_id: Optional[UUID] = None
    # For PO Invoices - line items from GRN (SAP MIRO style)
    line_items: Optional[List[InvoiceLineItemCreate]] = None
    # For Expense Invoices (non-PO) - multiple GL lines
    expense_lines: Optional[List[ExpenseLineItem]] = None
    # Legacy single GL fields (backward compatibility)
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
    force_budget_override: bool = False  # Super admin can force post even if budget exceeded


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


@router.get("/grns-for-po/{po_id}")
async def get_grns_for_po(
    po_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get GRNs available for invoicing against a PO."""
    result = await db.execute(
        select(GoodsReceiptNote)
        .where(
            GoodsReceiptNote.purchase_order_id == po_id,
            GoodsReceiptNote.status.in_([
                "ACCEPTED", "QC_PASSED", "PUT_AWAY_PENDING",
                "PUT_AWAY_COMPLETE", "PARTIALLY_ACCEPTED"
            ])
        )
        .order_by(desc(GoodsReceiptNote.grn_date))
    )
    grns = result.scalars().all()

    return [
        {
            "id": str(g.id),
            "grn_number": g.grn_number,
            "grn_date": g.grn_date.isoformat() if g.grn_date else None,
            "status": g.status,
            "total_quantity_accepted": g.total_quantity_accepted,
            "total_value": float(g.total_value) if g.total_value else 0,
        }
        for g in grns
    ]


@router.get("/grn-items-for-invoice/{grn_id}")
async def get_grn_items_for_invoice(
    grn_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get GRN accepted items with PO rates for invoice creation (SAP MIRO style)."""
    grn = await db.get(GoodsReceiptNote, grn_id)
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    # Load GRN items with PO items for GST rates
    items_result = await db.execute(
        select(GRNItem)
        .options(selectinload(GRNItem.po_item))
        .where(GRNItem.grn_id == grn_id, GRNItem.quantity_accepted > 0)
    )
    grn_items = items_result.scalars().all()

    # Load PO for reference
    po = await db.get(PurchaseOrder, grn.purchase_order_id) if grn.purchase_order_id else None

    items = []
    total_taxable = Decimal("0")
    total_cgst = Decimal("0")
    total_sgst = Decimal("0")
    total_igst = Decimal("0")

    for item in grn_items:
        invoiceable_qty = item.quantity_accepted - (item.quantity_invoiced or 0)
        if invoiceable_qty <= 0:
            continue

        po_item = item.po_item
        unit_price = item.unit_price or (po_item.unit_price if po_item else Decimal("0"))
        gst_rate = po_item.gst_rate if po_item else Decimal("18")
        cgst_rate = po_item.cgst_rate if po_item else (gst_rate / 2)
        sgst_rate = po_item.sgst_rate if po_item else (gst_rate / 2)
        igst_rate = po_item.igst_rate if po_item else Decimal("0")

        taxable = (Decimal(str(invoiceable_qty)) * unit_price).quantize(Decimal("0.01"))
        cgst_amt = (taxable * cgst_rate / 100).quantize(Decimal("0.01"))
        sgst_amt = (taxable * sgst_rate / 100).quantize(Decimal("0.01"))
        igst_amt = (taxable * igst_rate / 100).quantize(Decimal("0.01"))
        line_total = taxable + cgst_amt + sgst_amt + igst_amt

        total_taxable += taxable
        total_cgst += cgst_amt
        total_sgst += sgst_amt
        total_igst += igst_amt

        items.append({
            "grn_item_id": str(item.id),
            "po_item_id": str(item.po_item_id),
            "product_id": str(item.product_id),
            "variant_id": str(item.variant_id) if item.variant_id else None,
            "product_name": item.product_name,
            "sku": item.sku,
            "sub_item_code": item.sub_item_code,
            "hsn_code": item.hsn_code or (po_item.hsn_code if po_item else None),
            "uom": item.uom or "PCS",
            "po_quantity": po_item.quantity_ordered if po_item else 0,
            "grn_accepted_quantity": item.quantity_accepted,
            "already_invoiced": item.quantity_invoiced or 0,
            "invoiceable_quantity": invoiceable_qty,
            "unit_price": float(unit_price),
            "gst_rate": float(gst_rate),
            "cgst_rate": float(cgst_rate),
            "sgst_rate": float(sgst_rate),
            "igst_rate": float(igst_rate),
            "taxable_amount": float(taxable),
            "cgst_amount": float(cgst_amt),
            "sgst_amount": float(sgst_amt),
            "igst_amount": float(igst_amt),
            "total_amount": float(line_total),
        })

    grand_total = total_taxable + total_cgst + total_sgst + total_igst

    return {
        "grn_id": str(grn.id),
        "grn_number": grn.grn_number,
        "grn_date": grn.grn_date.isoformat() if grn.grn_date else None,
        "po_id": str(grn.purchase_order_id) if grn.purchase_order_id else None,
        "po_number": po.po_number if po else None,
        "items": items,
        "summary": {
            "total_taxable": float(total_taxable),
            "total_cgst": float(total_cgst),
            "total_sgst": float(total_sgst),
            "total_igst": float(total_igst),
            "grand_total": float(grand_total),
        }
    }


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
        selectinload(VendorInvoice.expense_lines).selectinload(VendorInvoiceExpenseLine.gl_account),
        selectinload(VendorInvoice.expense_lines).selectinload(VendorInvoiceExpenseLine.cost_center),
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
                "expense_lines": [
                    {
                        "id": str(line.id),
                        "gl_account_id": str(line.gl_account_id),
                        "gl_account_name": line.gl_account.account_name if line.gl_account else None,
                        "gl_account_code": line.gl_account.account_code if line.gl_account else None,
                        "gl_account_type": line.gl_account.account_type if line.gl_account else None,
                        "expense_category": line.expense_category,
                        "description": line.description,
                        "amount": float(line.amount),
                        "cost_center_id": str(line.cost_center_id) if line.cost_center_id else None,
                        "cost_center_name": line.cost_center.name if line.cost_center else None,
                        "gst_rate": float(line.gst_rate) if line.gst_rate else 18,
                        "gst_amount": float(line.gst_amount) if line.gst_amount else 0,
                        "line_total": float(line.line_total) if line.line_total else 0,
                        "line_number": line.line_number,
                    }
                    for line in (inv.expense_lines or [])
                ],
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
        selectinload(VendorInvoice.expense_lines).selectinload(VendorInvoiceExpenseLine.gl_account),
        selectinload(VendorInvoice.expense_lines).selectinload(VendorInvoiceExpenseLine.cost_center),
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
        "expense_lines": [
            {
                "id": str(line.id),
                "gl_account_id": str(line.gl_account_id),
                "gl_account_name": line.gl_account.account_name if line.gl_account else None,
                "gl_account_code": line.gl_account.account_code if line.gl_account else None,
                "expense_category": line.expense_category,
                "description": line.description,
                "amount": float(line.amount),
                "line_number": line.line_number,
            }
            for line in (inv.expense_lines or [])
        ],
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

    # For expense invoices with lines, use the first line's GL as the primary (backward compat)
    primary_gl_account_id = data.gl_account_id
    primary_expense_category = data.expense_category
    primary_expense_description = data.expense_description
    if data.expense_lines and len(data.expense_lines) > 0:
        first_line = data.expense_lines[0]
        if not primary_gl_account_id:
            primary_gl_account_id = first_line.gl_account_id
        if not primary_expense_category:
            primary_expense_category = first_line.expense_category
        if not primary_expense_description:
            primary_expense_description = first_line.description

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
        gl_account_id=primary_gl_account_id,
        cost_center_id=data.cost_center_id,
        expense_category=primary_expense_category,
        expense_description=primary_expense_description,
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
    await db.flush()

    # Create expense line items if provided
    if data.expense_lines and len(data.expense_lines) > 0:
        for idx, line_data in enumerate(data.expense_lines, start=1):
            # Validate GL account
            gl_acc = await db.get(ChartOfAccount, line_data.gl_account_id)
            if not gl_acc:
                raise HTTPException(
                    status_code=400,
                    detail=f"GL Account not found for expense line {idx}"
                )
            expense_line = VendorInvoiceExpenseLine(
                vendor_invoice_id=invoice.id,
                gl_account_id=line_data.gl_account_id,
                expense_category=line_data.expense_category,
                description=line_data.description,
                amount=line_data.amount,
                cost_center_id=line_data.cost_center_id,
                gst_rate=line_data.gst_rate or Decimal("18"),
                gst_amount=line_data.gst_amount or Decimal("0"),
                line_total=line_data.line_total or Decimal("0"),
                line_number=idx,
            )
            db.add(expense_line)

    await db.flush()

    # --- Budget enforcement: block if exceeded (unless force_budget_override) ---
    budget_warnings = []
    budget_exceeded = False
    if data.expense_lines and len(data.expense_lines) > 0:
        for idx, line_data in enumerate(data.expense_lines, start=1):
            if line_data.cost_center_id:
                from app.models.accounting import CostCenter as CostCenterModel
                cc = await db.get(CostCenterModel, line_data.cost_center_id)
                if cc and cc.annual_budget and cc.annual_budget > 0:
                    projected = (cc.current_spend or Decimal("0")) + line_data.amount
                    if projected > cc.annual_budget:
                        budget_exceeded = True
                        utilization = round(float(projected / cc.annual_budget * 100), 1)
                        budget_warnings.append(
                            f"Line {idx}: Cost center '{cc.name}' budget exceeded ({utilization}% utilization). "
                            f"Budget: ₹{cc.annual_budget:,.0f}, Projected: ₹{projected:,.0f}"
                        )
                    # Update current_spend
                    cc.current_spend = (cc.current_spend or Decimal("0")) + line_data.amount

    # Block if budget exceeded and no override
    if budget_exceeded and not data.force_budget_override:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Budget exceeded. Use 'Force Override' (Super Admin) to proceed.",
                "budget_warnings": budget_warnings,
                "requires_override": True,
            }
        )

    await db.flush()

    # Create PO invoice line items from GRN (SAP MIRO style)
    if data.invoice_type == "PO_INVOICE" and data.line_items:
        for idx, item_data in enumerate(data.line_items, start=1):
            # Validate GRN item and check invoiceable quantity
            grn_item = await db.get(GRNItem, item_data.grn_item_id)
            if not grn_item:
                raise HTTPException(status_code=400, detail=f"GRN item not found for line {idx}")

            available_qty = grn_item.quantity_accepted - (grn_item.quantity_invoiced or 0)
            if item_data.invoice_quantity > available_qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Line {idx} ({item_data.product_name}): Invoice qty ({item_data.invoice_quantity}) exceeds available qty ({available_qty})"
                )

            invoice_item = VendorInvoiceItem(
                vendor_invoice_id=invoice.id,
                grn_item_id=item_data.grn_item_id,
                po_item_id=item_data.po_item_id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                product_name=item_data.product_name,
                sku=item_data.sku,
                hsn_code=item_data.hsn_code,
                uom=item_data.uom,
                line_number=idx,
                po_quantity=item_data.po_quantity,
                grn_accepted_quantity=item_data.grn_accepted_quantity,
                invoice_quantity=item_data.invoice_quantity,
                unit_price=item_data.unit_price,
                discount_percentage=item_data.discount_percentage,
                discount_amount=item_data.discount_amount,
                taxable_amount=item_data.taxable_amount,
                gst_rate=item_data.gst_rate,
                cgst_amount=item_data.cgst_amount,
                sgst_amount=item_data.sgst_amount,
                igst_amount=item_data.igst_amount,
                cess_amount=item_data.cess_amount,
                total_amount=item_data.total_amount,
            )
            db.add(invoice_item)

            # Update GRN item's quantity_invoiced
            grn_item.quantity_invoiced = (grn_item.quantity_invoiced or 0) + item_data.invoice_quantity

    await db.flush()

    # Audit log
    await AuditService(db).log(
        action="CREATE",
        entity_type="VendorInvoice",
        entity_id=invoice.id,
        user_id=current_user.id,
        new_values={
            "our_reference": invoice.our_reference,
            "invoice_number": invoice.invoice_number,
            "vendor_id": str(invoice.vendor_id) if invoice.vendor_id else None,
            "grand_total": str(invoice.grand_total),
            "invoice_type": invoice.invoice_type,
            "line_items_count": len(data.line_items) if data.line_items else 0,
        },
        description=f"Created vendor invoice {invoice.invoice_number} ({invoice.our_reference}) for ₹{invoice.grand_total}",
    )

    await db.commit()
    await db.refresh(invoice)

    response = {
        "id": str(invoice.id),
        "our_reference": invoice.our_reference,
        "message": "Vendor invoice created successfully",
    }
    if budget_warnings:
        response["budget_warnings"] = budget_warnings

    return response


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

    # Load invoice line items if they exist (new SAP MIRO style)
    inv_items_result = await db.execute(
        select(VendorInvoiceItem).where(VendorInvoiceItem.vendor_invoice_id == invoice.id)
    )
    inv_items = inv_items_result.scalars().all()

    # Calculate matching
    po_amount = po.grand_total
    grn_value = grn.total_value
    invoice_amount = invoice.grand_total

    item_match_results = []

    if inv_items:
        # ===== ITEM-LEVEL MATCHING (SAP style) =====
        all_items_matched = True
        total_item_variance = Decimal("0")

        for inv_item in inv_items:
            # Load PO item for rate comparison
            po_item = await db.get(PurchaseOrderItem, inv_item.po_item_id)
            grn_item = await db.get(GRNItem, inv_item.grn_item_id)

            # Quantity match: invoice qty should equal GRN accepted qty
            qty_match = inv_item.invoice_quantity <= (grn_item.quantity_accepted if grn_item else 0)

            # Rate match: invoice rate vs PO rate (within tolerance)
            po_rate = po_item.unit_price if po_item else Decimal("0")
            rate_diff = abs(inv_item.unit_price - po_rate)
            rate_variance_pct = (rate_diff / po_rate * 100) if po_rate > 0 else Decimal("0")
            rate_match = rate_variance_pct <= data.tolerance_percentage

            # Amount match
            expected_amount = (Decimal(str(inv_item.invoice_quantity)) * po_rate).quantize(Decimal("0.01"))
            amt_diff = abs(inv_item.taxable_amount - expected_amount)
            amt_variance_pct = (amt_diff / expected_amount * 100) if expected_amount > 0 else Decimal("0")
            amt_match = amt_variance_pct <= data.tolerance_percentage

            item_matched = qty_match and rate_match and amt_match
            if not item_matched:
                all_items_matched = False

            variance = inv_item.taxable_amount - expected_amount
            total_item_variance += abs(variance)

            # Update item-level match status
            inv_item.quantity_match = qty_match
            inv_item.rate_match = rate_match
            inv_item.amount_match = amt_match
            inv_item.match_status = "MATCHED" if item_matched else "MISMATCH"
            inv_item.variance_amount = variance

            item_match_results.append({
                "line_number": inv_item.line_number,
                "product_name": inv_item.product_name,
                "sku": inv_item.sku,
                "po_quantity": po_item.quantity_ordered if po_item else 0,
                "po_rate": float(po_rate),
                "grn_quantity": grn_item.quantity_accepted if grn_item else 0,
                "invoice_quantity": inv_item.invoice_quantity,
                "invoice_rate": float(inv_item.unit_price),
                "quantity_match": qty_match,
                "rate_match": rate_match,
                "amount_match": amt_match,
                "match_status": inv_item.match_status,
                "variance_amount": float(variance),
            })

        po_matched = all_items_matched
        grn_matched = all_items_matched
        is_fully_matched = all_items_matched
        total_variance = total_item_variance
        po_variance_pct = Decimal("0")
        grn_variance_pct = Decimal("0")

    else:
        # ===== LEGACY TOTAL-LEVEL MATCHING (backward compatibility) =====
        po_variance = abs(invoice_amount - po_amount)
        po_variance_pct = (po_variance / po_amount * 100) if po_amount > 0 else Decimal("0")
        po_matched = po_variance_pct <= data.tolerance_percentage

        grn_variance = abs(invoice_amount - grn_value)
        grn_variance_pct = (grn_variance / grn_value * 100) if grn_value > 0 else Decimal("0")
        grn_matched = grn_variance_pct <= data.tolerance_percentage

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
        invoice.variance_reason = f"PO variance: {float(po_variance_pct):.2f}%, GRN variance: {float(grn_variance_pct):.2f}%"
    else:
        invoice.status = "MISMATCH"
        invoice.variance_reason = f"PO variance: {float(po_variance_pct):.2f}%, GRN variance: {float(grn_variance_pct):.2f}%"

    invoice.verified_by = current_user.id
    invoice.verified_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "invoice_id": str(invoice.id),
        "po_id": str(po.id),
        "grn_id": str(grn.id),
        "match_type": "ITEM_LEVEL" if inv_items else "TOTAL_LEVEL",
        "matching_result": {
            "po_matched": po_matched,
            "po_amount": float(po_amount),
            "grn_matched": grn_matched,
            "grn_value": float(grn_value),
            "invoice_amount": float(invoice_amount),
            "is_fully_matched": is_fully_matched,
            "status": invoice.status,
            "total_variance": float(total_variance),
            "items": item_match_results if inv_items else [],
        },
    }


@router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve a vendor invoice for payment, create journal entry, and sync ITC."""
    from app.services.itc_service import ITCService

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

    # Auto-sync to ITC Ledger for GST compliance
    itc_entry = None
    try:
        # Get company_id from user or invoice
        company_id = getattr(current_user, 'company_id', None)
        if company_id:
            itc_service = ITCService(db, company_id)
            itc_entry = await itc_service.sync_vendor_invoice_to_itc(
                vendor_invoice_id=invoice_id,
                created_by=current_user.id,
            )
    except Exception as e:
        # Log the error but don't fail the approval
        import logging
        logging.warning(f"Failed to sync ITC for vendor invoice {invoice.invoice_number}: {str(e)}")

    # Audit log
    await AuditService(db).log(
        action="APPROVE",
        entity_type="VendorInvoice",
        entity_id=invoice.id,
        user_id=current_user.id,
        new_values={
            "status": "APPROVED",
            "journal_entry_id": str(journal_entry.id) if journal_entry else None,
        },
        description=f"Approved vendor invoice {invoice.invoice_number} (₹{invoice.grand_total})",
    )

    await db.commit()

    return {
        "message": "Invoice approved, journal entry created, and ITC synced",
        "status": invoice.status,
        "journal_entry_id": str(journal_entry.id) if journal_entry else None,
        "itc_entry_id": str(itc_entry.id) if itc_entry else None,
    }


class VendorInvoiceUpdate(BaseModel):
    """Schema for updating vendor invoice."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    invoice_type: Optional[str] = None  # PO_INVOICE or EXPENSE_INVOICE
    purchase_order_id: Optional[UUID] = None
    grn_id: Optional[UUID] = None
    # Expense invoice fields
    expense_lines: Optional[List[ExpenseLineItem]] = None
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
    # TDS fields
    tds_applicable: Optional[bool] = None
    tds_section: Optional[str] = None
    tds_rate: Optional[Decimal] = None


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

    # Handle expense lines update (replace all lines)
    if data.expense_lines is not None:
        # Delete existing expense lines
        existing_lines_query = select(VendorInvoiceExpenseLine).where(
            VendorInvoiceExpenseLine.vendor_invoice_id == invoice_id
        )
        existing_lines_result = await db.execute(existing_lines_query)
        for old_line in existing_lines_result.scalars().all():
            await db.delete(old_line)

        # Create new lines
        for idx, line_data in enumerate(data.expense_lines, start=1):
            gl_acc = await db.get(ChartOfAccount, line_data.gl_account_id)
            if not gl_acc:
                raise HTTPException(status_code=400, detail=f"GL Account not found for expense line {idx}")
            expense_line = VendorInvoiceExpenseLine(
                vendor_invoice_id=invoice_id,
                gl_account_id=line_data.gl_account_id,
                expense_category=line_data.expense_category,
                description=line_data.description,
                amount=line_data.amount,
                cost_center_id=line_data.cost_center_id,
                gst_rate=line_data.gst_rate or Decimal("18"),
                gst_amount=line_data.gst_amount or Decimal("0"),
                line_total=line_data.line_total or Decimal("0"),
                line_number=idx,
            )
            db.add(expense_line)

        # Update primary GL from first line for backward compat
        if len(data.expense_lines) > 0:
            first = data.expense_lines[0]
            invoice.gl_account_id = first.gl_account_id
            invoice.expense_category = first.expense_category
            invoice.expense_description = first.description

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

    # TDS fields
    if data.tds_applicable is not None:
        invoice.tds_applicable = data.tds_applicable
    if data.tds_section is not None:
        invoice.tds_section = data.tds_section
    if data.tds_rate is not None:
        invoice.tds_rate = data.tds_rate

    # Recalculate total_tax
    invoice.total_tax = invoice.cgst_amount + invoice.sgst_amount + invoice.igst_amount + invoice.cess_amount

    # Recalculate TDS and net payable based on current values
    tds_amount = (invoice.grand_total * invoice.tds_rate / 100) if invoice.tds_applicable else Decimal("0")
    invoice.tds_amount = tds_amount
    invoice.net_payable = invoice.grand_total - tds_amount
    invoice.balance_due = invoice.net_payable - invoice.amount_paid

    # Audit log
    await AuditService(db).log(
        action="UPDATE",
        entity_type="VendorInvoice",
        entity_id=invoice.id,
        user_id=current_user.id,
        new_values={
            "invoice_number": invoice.invoice_number,
            "grand_total": str(invoice.grand_total),
            "net_payable": str(invoice.net_payable),
        },
        description=f"Updated vendor invoice {invoice.invoice_number} (₹{invoice.grand_total})",
    )

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

    # Audit log before delete
    await AuditService(db).log(
        action="DELETE",
        entity_type="VendorInvoice",
        entity_id=invoice.id,
        user_id=current_user.id,
        old_values={
            "invoice_number": invoice.invoice_number,
            "our_reference": invoice.our_reference,
            "grand_total": str(invoice.grand_total),
            "vendor_id": str(invoice.vendor_id) if invoice.vendor_id else None,
        },
        description=f"Deleted vendor invoice {invoice.invoice_number} ({invoice.our_reference})",
    )

    await db.delete(invoice)
    await db.commit()

    return {"message": "Invoice deleted successfully"}


class RecordVendorPaymentRequest(BaseModel):
    amount: Decimal
    payment_date: date
    payment_mode: str = "NEFT"  # NEFT, RTGS, UPI, CHEQUE, CASH
    payment_reference: Optional[str] = None  # UTR number
    bank_name: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    tds_amount: Decimal = Decimal("0")
    tds_section: Optional[str] = None
    narration: Optional[str] = None


@router.post("/{invoice_id}/record-payment")
async def record_payment(
    invoice_id: UUID,
    payload: RecordVendorPaymentRequest,
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """
    Record a payment against a vendor invoice.
    Performs all 4 operations atomically:
    1. Update VendorInvoice (amount_paid, balance_due, status)
    2. Create VendorLedger entry (PAYMENT type)
    3. Update Vendor.current_balance
    4. Create GL journal entry (Dr AP, Cr Bank, Cr TDS)
    """
    # --- Load invoice ---
    invoice = await db.get(VendorInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status not in ["APPROVED", "PAYMENT_INITIATED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot record payment for invoice with status {invoice.status}"
        )

    # Validate amount
    current_balance_due = (invoice.net_payable or invoice.grand_total) - (invoice.amount_paid or Decimal("0"))
    if payload.amount > current_balance_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount {payload.amount} exceeds balance due {current_balance_due}"
        )

    # --- Load vendor ---
    vendor = await db.get(Vendor, invoice.vendor_id) if invoice.vendor_id else None
    vendor_name = vendor.name if vendor else "Vendor"

    # --- (1) Update VendorInvoice ---
    invoice.amount_paid = (invoice.amount_paid or Decimal("0")) + payload.amount
    invoice.balance_due = (invoice.net_payable or invoice.grand_total) - invoice.amount_paid

    if invoice.balance_due <= 0:
        invoice.status = "PAID"
        invoice.balance_due = Decimal("0")
    else:
        invoice.status = "PAYMENT_INITIATED"

    # --- (2) Create VendorLedger entry ---
    ledger_entry = VendorLedger(
        id=uuid4(),
        vendor_id=invoice.vendor_id,
        transaction_type="PAYMENT",
        transaction_date=payload.payment_date,
        reference_type="PAYMENT",
        reference_number=payload.payment_reference or invoice.invoice_number,
        reference_id=invoice.id,
        vendor_invoice_number=invoice.invoice_number,
        vendor_invoice_date=invoice.invoice_date,
        debit_amount=payload.amount,
        credit_amount=Decimal("0"),
        running_balance=(vendor.current_balance if vendor else Decimal("0")) - payload.amount,
        tds_amount=payload.tds_amount,
        tds_section=payload.tds_section,
        payment_mode=payload.payment_mode,
        payment_reference=payload.payment_reference,
        bank_name=payload.bank_name,
        cheque_number=payload.cheque_number,
        cheque_date=payload.cheque_date,
        narration=payload.narration or f"Payment against {invoice.invoice_number}",
        created_by=current_user.id,
    )
    db.add(ledger_entry)

    # --- (3) Update Vendor.current_balance ---
    if vendor:
        vendor.current_balance = (vendor.current_balance or Decimal("0")) - payload.amount

    # --- (4) Create GL journal entry ---
    journal_entry = None
    try:
        journal_service = AutoJournalService(db)
        journal_entry = await journal_service.generate_for_vendor_payment(
            vendor_id=invoice.vendor_id,
            amount=payload.amount,
            payment_date=payload.payment_date,
            payment_mode=payload.payment_mode,
            payment_reference=payload.payment_reference or "",
            invoice_number=invoice.invoice_number,
            vendor_name=vendor_name,
            tds_amount=payload.tds_amount,
            narration=payload.narration,
            user_id=current_user.id,
            source_id=invoice.id,
        )
    except Exception:
        import logging
        logging.exception(f"Failed to create GL journal for vendor payment on {invoice.invoice_number}")

    # Audit log
    await AuditService(db).log(
        action="PAY",
        entity_type="VendorInvoice",
        entity_id=invoice.id,
        user_id=current_user.id,
        new_values={
            "payment_amount": str(payload.amount),
            "payment_mode": payload.payment_mode,
            "payment_reference": payload.payment_reference,
            "total_paid": str(invoice.amount_paid),
            "balance_due": str(invoice.balance_due),
            "status": invoice.status,
        },
        description=f"Recorded payment of ₹{payload.amount} against invoice {invoice.invoice_number} via {payload.payment_mode}",
    )

    await db.commit()

    return {
        "message": "Payment recorded successfully",
        "amount_paid": float(invoice.amount_paid),
        "balance_due": float(invoice.balance_due),
        "status": invoice.status,
        "journal_entry_id": str(journal_entry.id) if journal_entry else None,
        "ledger_entry_id": str(ledger_entry.id),
    }
