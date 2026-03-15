"""Vendor Portal API endpoints (SAP SRM simplified).

Read-only self-service endpoints for vendors to check PO status,
invoice status, payments, and GRNs. Uses vendor_code as identifier.
"""
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, and_, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import DB


router = APIRouter()


# --- Response Models ---

class VendorDashboardStats(BaseModel):
    vendor_code: str
    vendor_name: str = ""
    total_pos: int = 0
    pending_deliveries: int = 0
    invoices_submitted: int = 0
    payments_received: int = 0
    total_payment_amount: float = 0


class VendorPOItem(BaseModel):
    id: str
    po_number: str
    order_date: Optional[str] = None
    status: str = ""
    total_amount: float = 0
    currency: str = "INR"
    delivery_date: Optional[str] = None
    items_count: int = 0


class VendorInvoiceItem(BaseModel):
    id: str
    invoice_number: str
    invoice_date: Optional[str] = None
    status: str = ""
    total_amount: float = 0
    due_date: Optional[str] = None
    payment_status: str = ""


class VendorPaymentItem(BaseModel):
    id: str
    payment_number: Optional[str] = None
    payment_date: Optional[str] = None
    amount: float = 0
    payment_mode: str = ""
    reference: Optional[str] = None
    status: str = ""


class VendorGRNItem(BaseModel):
    id: str
    grn_number: str
    grn_date: Optional[str] = None
    po_number: Optional[str] = None
    status: str = ""
    total_received: int = 0
    total_accepted: int = 0
    total_rejected: int = 0


async def _get_vendor_id(db: AsyncSession, vendor_code: str):
    """Resolve vendor_code to vendor id and name."""
    result = await db.execute(sa_text("""
        SELECT id, name FROM vendors WHERE vendor_code = :vc LIMIT 1
    """), {"vc": vendor_code})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Vendor with code '{vendor_code}' not found")
    return str(row[0]), row[1]


@router.get("/dashboard", response_model=VendorDashboardStats,
            summary="Vendor dashboard stats")
async def vendor_dashboard(
    vendor_code: str = Query(..., description="Vendor code e.g. VND-00001"),
    db: DB = None,
):
    """Get dashboard stats for a vendor: POs, deliveries, invoices, payments."""
    vendor_id, vendor_name = await _get_vendor_id(db, vendor_code)

    # Total POs
    po_result = await db.execute(sa_text("""
        SELECT COUNT(*) FROM purchase_orders WHERE vendor_id = :vid
    """), {"vid": vendor_id})
    total_pos = po_result.scalar() or 0

    # Pending deliveries (POs not fully received)
    pending_result = await db.execute(sa_text("""
        SELECT COUNT(*) FROM purchase_orders
        WHERE vendor_id = :vid AND status IN ('APPROVED', 'SENT_TO_VENDOR', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED')
    """), {"vid": vendor_id})
    pending_deliveries = pending_result.scalar() or 0

    # Invoices submitted
    inv_result = await db.execute(sa_text("""
        SELECT COUNT(*) FROM vendor_invoices WHERE vendor_id = :vid
    """), {"vid": vendor_id})
    invoices_submitted = inv_result.scalar() or 0

    # Payments (from vendor_ledger - credit entries are payments)
    pay_result = await db.execute(sa_text("""
        SELECT COUNT(*), COALESCE(SUM(credit_amount), 0)
        FROM vendor_ledger
        WHERE vendor_id = :vid AND credit_amount > 0
    """), {"vid": vendor_id})
    pay_row = pay_result.fetchone()
    payments_received = pay_row[0] or 0
    total_payment_amount = float(pay_row[1] or 0)

    return VendorDashboardStats(
        vendor_code=vendor_code,
        vendor_name=vendor_name or "",
        total_pos=total_pos,
        pending_deliveries=pending_deliveries,
        invoices_submitted=invoices_submitted,
        payments_received=payments_received,
        total_payment_amount=total_payment_amount,
    )


@router.get("/purchase-orders", summary="List POs for a vendor")
async def vendor_purchase_orders(
    vendor_code: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: DB = None,
):
    """List purchase orders for a vendor."""
    vendor_id, _ = await _get_vendor_id(db, vendor_code)
    offset = (page - 1) * size

    where_clause = "WHERE po.vendor_id = :vid"
    params = {"vid": vendor_id, "lim": size, "off": offset}
    if status:
        where_clause += " AND po.status = :st"
        params["st"] = status

    count_result = await db.execute(sa_text(f"""
        SELECT COUNT(*) FROM purchase_orders po {where_clause}
    """), params)
    total = count_result.scalar() or 0

    result = await db.execute(sa_text(f"""
        SELECT po.id, po.po_number, po.po_date, po.status, po.grand_total,
               po.expected_delivery_date,
               (SELECT COUNT(*) FROM purchase_order_items WHERE purchase_order_id = po.id) as items_count
        FROM purchase_orders po
        {where_clause}
        ORDER BY po.created_at DESC
        LIMIT :lim OFFSET :off
    """), params)
    rows = result.fetchall()

    items = [VendorPOItem(
        id=str(r[0]), po_number=r[1] or "", order_date=str(r[2]) if r[2] else None,
        status=r[3] or "", total_amount=float(r[4] or 0),
        delivery_date=str(r[5]) if r[5] else None, items_count=r[6] or 0,
    ) for r in rows]

    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/invoices", summary="List invoices for a vendor")
async def vendor_invoices(
    vendor_code: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: DB = None,
):
    """List vendor invoices."""
    vendor_id, _ = await _get_vendor_id(db, vendor_code)
    offset = (page - 1) * size

    count_result = await db.execute(sa_text("""
        SELECT COUNT(*) FROM vendor_invoices WHERE vendor_id = :vid
    """), {"vid": vendor_id})
    total = count_result.scalar() or 0

    result = await db.execute(sa_text("""
        SELECT id, invoice_number, invoice_date, status, grand_total, due_date,
               CASE WHEN balance_due <= 0 THEN 'PAID'
                    WHEN amount_paid > 0 THEN 'PARTIALLY_PAID'
                    ELSE 'UNPAID' END as payment_status
        FROM vendor_invoices
        WHERE vendor_id = :vid
        ORDER BY created_at DESC
        LIMIT :lim OFFSET :off
    """), {"vid": vendor_id, "lim": size, "off": offset})
    rows = result.fetchall()

    items = [VendorInvoiceItem(
        id=str(r[0]), invoice_number=r[1] or "", invoice_date=str(r[2]) if r[2] else None,
        status=r[3] or "", total_amount=float(r[4] or 0),
        due_date=str(r[5]) if r[5] else None, payment_status=r[6] or "",
    ) for r in rows]

    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/payments", summary="Payment history for a vendor")
async def vendor_payments_list(
    vendor_code: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: DB = None,
):
    """List payments made to a vendor (from vendor_ledger credit entries)."""
    vendor_id, _ = await _get_vendor_id(db, vendor_code)
    offset = (page - 1) * size

    count_result = await db.execute(sa_text("""
        SELECT COUNT(*) FROM vendor_ledger WHERE vendor_id = :vid AND credit_amount > 0
    """), {"vid": vendor_id})
    total = count_result.scalar() or 0

    result = await db.execute(sa_text("""
        SELECT id, reference_number, transaction_date, credit_amount, payment_mode, payment_reference,
               CASE WHEN is_settled THEN 'COMPLETED' ELSE 'PENDING' END as status
        FROM vendor_ledger
        WHERE vendor_id = :vid AND credit_amount > 0
        ORDER BY transaction_date DESC NULLS LAST
        LIMIT :lim OFFSET :off
    """), {"vid": vendor_id, "lim": size, "off": offset})
    rows = result.fetchall()

    items = [VendorPaymentItem(
        id=str(r[0]), payment_number=r[1], payment_date=str(r[2]) if r[2] else None,
        amount=float(r[3] or 0), payment_mode=r[4] or "", reference=r[5],
        status=r[6] or "",
    ) for r in rows]

    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/grns", summary="GRNs for a vendor")
async def vendor_grns(
    vendor_code: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: DB = None,
):
    """List Goods Receipt Notes for a vendor's POs."""
    vendor_id, _ = await _get_vendor_id(db, vendor_code)
    offset = (page - 1) * size

    count_result = await db.execute(sa_text("""
        SELECT COUNT(*) FROM goods_receipt_notes g
        JOIN purchase_orders po ON g.purchase_order_id = po.id
        WHERE po.vendor_id = :vid
    """), {"vid": vendor_id})
    total = count_result.scalar() or 0

    result = await db.execute(sa_text("""
        SELECT g.id, g.grn_number, g.grn_date, po.po_number, g.status,
               g.total_quantity_received, g.total_quantity_accepted, g.total_quantity_rejected
        FROM goods_receipt_notes g
        JOIN purchase_orders po ON g.purchase_order_id = po.id
        WHERE po.vendor_id = :vid
        ORDER BY g.grn_date DESC NULLS LAST
        LIMIT :lim OFFSET :off
    """), {"vid": vendor_id, "lim": size, "off": offset})
    rows = result.fetchall()

    items = [VendorGRNItem(
        id=str(r[0]), grn_number=r[1] or "", grn_date=str(r[2]) if r[2] else None,
        po_number=r[3], status=r[4] or "",
        total_received=r[5] or 0, total_accepted=r[6] or 0, total_rejected=r[7] or 0,
    ) for r in rows]

    return {"items": items, "total": total, "page": page, "size": size}
