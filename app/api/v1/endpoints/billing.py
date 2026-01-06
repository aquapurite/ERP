"""API endpoints for Billing & E-Invoice module (GST Compliant)."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.billing import (
    TaxInvoice, InvoiceItem, InvoiceType, InvoiceStatus,
    CreditDebitNote, CreditDebitNoteItem, DocumentType, NoteReason,
    EWayBill, EWayBillItem, EWayBillStatus,
    PaymentReceipt, PaymentMode,
    InvoiceNumberSequence,
)
from app.models.order import Order
from app.models.customer import Customer
from app.models.dealer import Dealer
from app.models.user import User
from app.schemas.billing import (
    # TaxInvoice
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceBrief, InvoiceListResponse,
    InvoiceItemCreate,
    # Credit/Debit Note
    CreditDebitNoteCreate, CreditDebitNoteResponse, CreditDebitNoteListResponse,
    # E-Way Bill
    EWayBillCreate, EWayBillUpdate, EWayBillResponse, EWayBillListResponse,
    # Payment Receipt
    PaymentReceiptCreate, PaymentReceiptResponse, PaymentReceiptListResponse,
    # Reports
    GSTReportRequest, GSTR1Response, GSTR3BResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from app.services.audit_service import AuditService

router = APIRouter()


# ==================== TaxInvoice ====================

@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new tax invoice."""
    # Map invoice type to series code
    series_code_map = {
        InvoiceType.TAX_INVOICE: "INV",
        InvoiceType.PROFORMA: "PI",
        InvoiceType.DELIVERY_CHALLAN: "DC",
        InvoiceType.EXPORT: "EXP",
        InvoiceType.SEZ: "SEZ",
        InvoiceType.DEEMED_EXPORT: "DE",
    }
    series_code = series_code_map.get(invoice_in.invoice_type, "INV")

    # Get current financial year
    from datetime import datetime
    now = datetime.now()
    if now.month >= 4:
        financial_year = f"{now.year}-{str(now.year + 1)[2:]}"
    else:
        financial_year = f"{now.year - 1}-{str(now.year)[2:]}"

    # Generate invoice number from sequence
    sequence_result = await db.execute(
        select(InvoiceNumberSequence).where(
            and_(
                InvoiceNumberSequence.series_code == series_code,
                InvoiceNumberSequence.financial_year == financial_year,
                InvoiceNumberSequence.is_active == True,
            )
        )
    )
    sequence = sequence_result.scalar_one_or_none()

    if not sequence:
        # Create default sequence
        sequence = InvoiceNumberSequence(
            series_code=series_code,
            series_name=f"{invoice_in.invoice_type.value} Series",
            financial_year=financial_year,
            prefix=f"{series_code}/{financial_year}/",
            current_number=0,
        )
        db.add(sequence)
        await db.flush()

    sequence.current_number += 1
    invoice_number = f"{sequence.prefix}{str(sequence.current_number).zfill(sequence.padding_length)}"

    # Determine if inter-state
    shipping_state_code = invoice_in.shipping_state_code or invoice_in.billing_state_code
    is_inter_state = invoice_in.billing_state_code != shipping_state_code

    # Create invoice with initial zero values (will be updated after items)
    invoice = TaxInvoice(
        invoice_number=invoice_number,
        invoice_type=invoice_in.invoice_type,
        invoice_date=invoice_in.invoice_date,
        due_date=invoice_in.due_date,
        order_id=invoice_in.order_id,
        customer_id=invoice_in.customer_id,
        # Customer name (mapped from schema)
        customer_name=invoice_in.customer_name,
        customer_gstin=invoice_in.customer_gstin,
        # Billing Address (mapped from schema)
        billing_address_line1=invoice_in.billing_address_line1,
        billing_address_line2=invoice_in.billing_address_line2,
        billing_city=invoice_in.billing_city,
        billing_state=invoice_in.billing_state,
        billing_state_code=invoice_in.billing_state_code,
        billing_pincode=invoice_in.billing_pincode,
        # Shipping Address
        shipping_address_line1=invoice_in.shipping_address_line1 or invoice_in.billing_address_line1,
        shipping_address_line2=invoice_in.shipping_address_line2,
        shipping_city=invoice_in.shipping_city or invoice_in.billing_city,
        shipping_state=invoice_in.shipping_state or invoice_in.billing_state,
        shipping_state_code=shipping_state_code,
        shipping_pincode=invoice_in.shipping_pincode or invoice_in.billing_pincode,
        # Seller Info
        seller_gstin=invoice_in.seller_gstin,
        seller_name=invoice_in.seller_name,
        seller_address=invoice_in.seller_address,
        seller_state_code=invoice_in.seller_state_code,
        place_of_supply=invoice_in.place_of_supply,
        place_of_supply_code=invoice_in.place_of_supply_code,
        is_interstate=is_inter_state,
        is_reverse_charge=invoice_in.is_reverse_charge,
        # Other charges
        shipping_charges=invoice_in.shipping_charges,
        packaging_charges=invoice_in.packaging_charges,
        other_charges=invoice_in.other_charges,
        # Terms
        payment_terms=invoice_in.payment_terms,
        terms_and_conditions=invoice_in.terms_and_conditions,
        internal_notes=invoice_in.internal_notes,
        customer_notes=invoice_in.customer_notes,
        created_by=current_user.id,
        # Initialize totals to zero (will be updated after items are added)
        subtotal=Decimal("0"),
        taxable_amount=Decimal("0"),
        total_tax=Decimal("0"),
        grand_total=Decimal("0"),
        amount_due=Decimal("0"),
    )

    db.add(invoice)
    await db.flush()

    # Create invoice items and calculate totals
    subtotal = Decimal("0")
    total_discount = Decimal("0")
    taxable_amount = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    igst_total = Decimal("0")
    cess_total = Decimal("0")
    line_number = 0

    for item_data in invoice_in.items:
        line_number += 1

        # Calculate item amounts
        gross_amount = item_data.quantity * item_data.unit_price
        discount_amount = gross_amount * (item_data.discount_percentage / 100)
        item_taxable = gross_amount - discount_amount

        # GST calculation based on inter/intra state
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
        cess_amount = item_taxable * (item_data.cess_rate / 100) if item_data.cess_rate else Decimal("0")

        item_total = item_taxable + cgst_amount + sgst_amount + igst_amount + cess_amount

        # Calculate total tax for this item
        item_total_tax = cgst_amount + sgst_amount + igst_amount + cess_amount

        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            sku=item_data.sku,
            item_name=item_data.item_name,
            item_description=item_data.item_description,
            hsn_code=item_data.hsn_code,
            is_service=item_data.is_service,
            serial_numbers={"serials": item_data.serial_numbers} if item_data.serial_numbers else None,
            quantity=item_data.quantity,
            uom=item_data.uom,
            unit_price=item_data.unit_price,
            mrp=item_data.mrp,
            discount_percentage=item_data.discount_percentage,
            discount_amount=discount_amount,
            taxable_value=item_taxable,
            gst_rate=gst_rate,
            cgst_rate=cgst_rate,
            sgst_rate=sgst_rate,
            igst_rate=igst_rate,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount,
            cess_rate=Decimal("0"),  # No cess for now
            cess_amount=cess_amount,
            total_tax=item_total_tax,
            line_total=item_total,
            warranty_months=item_data.warranty_months,
            order_item_id=item_data.order_item_id,
        )
        db.add(item)

        subtotal += gross_amount
        total_discount += discount_amount
        taxable_amount += item_taxable
        cgst_total += cgst_amount
        sgst_total += sgst_amount
        igst_total += igst_amount
        cess_total += cess_amount

    # Update invoice totals
    total_tax = cgst_total + sgst_total + igst_total + cess_total
    grand_total = taxable_amount + total_tax

    # Apply round off
    round_off = round(grand_total) - grand_total
    grand_total = round(grand_total)

    invoice.subtotal = subtotal
    invoice.discount_amount = total_discount
    invoice.taxable_amount = taxable_amount
    invoice.cgst_amount = cgst_total
    invoice.sgst_amount = sgst_total
    invoice.igst_amount = igst_total
    invoice.cess_amount = cess_total
    invoice.total_tax = total_tax
    invoice.round_off = round_off
    invoice.grand_total = grand_total
    invoice.amount_due = grand_total

    await db.commit()

    # Post accounting entry for the invoice
    try:
        from app.services.accounting_service import AccountingService
        accounting = AccountingService(db)
        await accounting.post_sales_invoice(
            invoice_id=invoice.id,
            customer_name=invoice.customer_name,
            subtotal=taxable_amount,
            cgst=cgst_total,
            sgst=sgst_total,
            igst=igst_total,
            total=grand_total,
            is_interstate=is_inter_state,
            product_type="purifier",  # Default, can be enhanced to detect from items
        )
        await db.commit()
    except Exception as e:
        # Log but don't fail invoice creation if accounting fails
        import logging
        logging.warning(f"Failed to post accounting entry for invoice {invoice.invoice_number}: {e}")

    # Load full invoice
    result = await db.execute(
        select(TaxInvoice)
        .options(selectinload(TaxInvoice.items))
        .where(TaxInvoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    return invoice


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    invoice_type: Optional[InvoiceType] = None,
    status: Optional[InvoiceStatus] = None,
    customer_id: Optional[UUID] = None,
    dealer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List invoices with filters."""
    query = select(TaxInvoice)
    count_query = select(func.count(TaxInvoice.id))
    value_query = select(func.coalesce(func.sum(TaxInvoice.grand_total), 0))

    filters = []
    if invoice_type:
        filters.append(TaxInvoice.invoice_type == invoice_type)
    if status:
        filters.append(TaxInvoice.status == status)
    if customer_id:
        filters.append(TaxInvoice.customer_id == customer_id)
    if dealer_id:
        filters.append(TaxInvoice.dealer_id == dealer_id)
    if start_date:
        filters.append(TaxInvoice.invoice_date >= start_date)
    if end_date:
        filters.append(TaxInvoice.invoice_date <= end_date)
    if search:
        filters.append(or_(
            TaxInvoice.invoice_number.ilike(f"%{search}%"),
            TaxInvoice.billing_name.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
        value_query = value_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_value_result = await db.execute(value_query)
    total_value = total_value_result.scalar() or Decimal("0")

    query = query.order_by(TaxInvoice.invoice_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    invoices = result.scalars().all()

    return InvoiceListResponse(
        items=[InvoiceBrief.model_validate(inv) for inv in invoices],
        total=total,
        total_value=total_value,
        skip=skip,
        limit=limit
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get invoice by ID."""
    result = await db.execute(
        select(TaxInvoice)
        .options(selectinload(TaxInvoice.items))
        .where(TaxInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice


@router.post("/invoices/{invoice_id}/generate-irn", response_model=InvoiceResponse)
async def generate_einvoice_irn(
    invoice_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Generate IRN from GST E-Invoice portal."""
    result = await db.execute(
        select(TaxInvoice)
        .options(selectinload(TaxInvoice.items))
        .where(TaxInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.irn:
        raise HTTPException(status_code=400, detail="IRN already generated")

    # TODO: Integrate with GST E-Invoice API
    # For now, generate a mock IRN
    import hashlib
    mock_irn = hashlib.sha256(
        f"{invoice.invoice_number}{invoice.invoice_date}".encode()
    ).hexdigest()[:64]

    invoice.irn = mock_irn
    invoice.irn_generated_at = datetime.utcnow()
    invoice.ack_number = f"ACK-{invoice.invoice_number}"
    invoice.ack_date = datetime.utcnow()
    invoice.status = InvoiceStatus.IRN_GENERATED
    # invoice.signed_qr_code = "..." # Would come from GST portal
    # invoice.signed_invoice_data = "..." # Would come from GST portal

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.post("/invoices/{invoice_id}/cancel-irn", response_model=InvoiceResponse)
async def cancel_einvoice_irn(
    invoice_id: UUID,
    cancel_reason: str,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Cancel IRN within 24 hours."""
    result = await db.execute(
        select(TaxInvoice)
        .options(selectinload(TaxInvoice.items))
        .where(TaxInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if not invoice.irn:
        raise HTTPException(status_code=400, detail="No IRN to cancel")

    # Check 24 hour window
    if invoice.irn_generated_at:
        hours_elapsed = (datetime.utcnow() - invoice.irn_generated_at).total_seconds() / 3600
        if hours_elapsed > 24:
            raise HTTPException(
                status_code=400,
                detail="IRN can only be cancelled within 24 hours of generation"
            )

    # TODO: Call GST portal to cancel IRN

    invoice.irn_cancelled_at = datetime.utcnow()
    invoice.irn_cancel_reason = cancel_reason
    invoice.status = InvoiceStatus.IRN_CANCELLED

    await db.commit()
    await db.refresh(invoice)

    return invoice


# ==================== Credit/Debit Notes ====================

@router.post("/credit-debit-notes", response_model=CreditDebitNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_credit_debit_note(
    note_in: CreditDebitNoteCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a Credit or Debit Note."""
    # Verify original invoice
    invoice_result = await db.execute(
        select(TaxInvoice).where(TaxInvoice.id == note_in.original_invoice_id)
    )
    original_invoice = invoice_result.scalar_one_or_none()

    if not original_invoice:
        raise HTTPException(status_code=404, detail="Original invoice not found")

    # Generate note number
    prefix = "CN" if note_in.document_type == DocumentType.CREDIT_NOTE else "DN"
    today = date.today()
    count_result = await db.execute(
        select(func.count(CreditDebitNote.id)).where(
            and_(
                CreditDebitNote.document_type == note_in.document_type,
                func.date(CreditDebitNote.created_at) == today,
            )
        )
    )
    count = count_result.scalar() or 0
    note_number = f"{prefix}-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Calculate totals from items
    taxable_amount = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    igst_total = Decimal("0")
    cess_total = Decimal("0")

    for item in note_in.items:
        taxable_amount += item.taxable_amount
        cgst_total += item.cgst_amount
        sgst_total += item.sgst_amount
        igst_total += item.igst_amount
        cess_total += item.cess_amount

    total_tax = cgst_total + sgst_total + igst_total + cess_total
    grand_total = taxable_amount + total_tax

    note = CreditDebitNote(
        note_number=note_number,
        document_type=note_in.document_type,
        note_date=note_in.note_date,
        original_invoice_id=note_in.original_invoice_id,
        original_invoice_number=original_invoice.invoice_number,
        original_invoice_date=original_invoice.invoice_date,
        reason=note_in.reason,
        reason_description=note_in.reason_description,
        customer_id=original_invoice.customer_id,
        dealer_id=original_invoice.dealer_id,
        billing_gstin=original_invoice.billing_gstin,
        taxable_amount=taxable_amount,
        cgst_amount=cgst_total,
        sgst_amount=sgst_total,
        igst_amount=igst_total,
        cess_amount=cess_total,
        total_tax=total_tax,
        grand_total=grand_total,
        created_by=current_user.id,
    )

    db.add(note)
    await db.flush()

    # Create note items
    line_number = 0
    for item_data in note_in.items:
        line_number += 1
        item = CreditDebitNoteItem(
            note_id=note.id,
            line_number=line_number,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            hsn_code=item_data.hsn_code,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            taxable_amount=item_data.taxable_amount,
            cgst_rate=item_data.cgst_rate,
            sgst_rate=item_data.sgst_rate,
            igst_rate=item_data.igst_rate,
            cgst_amount=item_data.cgst_amount,
            sgst_amount=item_data.sgst_amount,
            igst_amount=item_data.igst_amount,
            cess_amount=item_data.cess_amount,
            total_amount=item_data.taxable_amount + item_data.cgst_amount + item_data.sgst_amount + item_data.igst_amount + item_data.cess_amount,
        )
        db.add(item)

    await db.commit()

    # Load full note
    result = await db.execute(
        select(CreditDebitNote)
        .options(selectinload(CreditDebitNote.items))
        .where(CreditDebitNote.id == note.id)
    )
    note = result.scalar_one()

    return note


@router.get("/credit-debit-notes", response_model=CreditDebitNoteListResponse)
async def list_credit_debit_notes(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    document_type: Optional[DocumentType] = None,
    customer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """List Credit/Debit Notes."""
    query = select(CreditDebitNote)
    count_query = select(func.count(CreditDebitNote.id))

    filters = []
    if document_type:
        filters.append(CreditDebitNote.document_type == document_type)
    if customer_id:
        filters.append(CreditDebitNote.customer_id == customer_id)
    if start_date:
        filters.append(CreditDebitNote.note_date >= start_date)
    if end_date:
        filters.append(CreditDebitNote.note_date <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(CreditDebitNote.note_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    notes = result.scalars().all()

    return CreditDebitNoteListResponse(
        items=[CreditDebitNoteResponse.model_validate(n) for n in notes],
        total=total,
        skip=skip,
        limit=limit
    )


# ==================== E-Way Bill ====================

@router.post("/eway-bills", response_model=EWayBillResponse, status_code=status.HTTP_201_CREATED)
async def create_eway_bill(
    ewb_in: EWayBillCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create an E-Way Bill."""
    # Verify invoice
    invoice_result = await db.execute(
        select(TaxInvoice)
        .options(selectinload(TaxInvoice.items))
        .where(TaxInvoice.id == ewb_in.invoice_id)
    )
    invoice = invoice_result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check if E-Way Bill already exists
    existing = await db.execute(
        select(EWayBill).where(EWayBill.invoice_id == ewb_in.invoice_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="E-Way Bill already exists for this invoice")

    # E-Way Bill is required for goods value > ₹50,000
    if invoice.taxable_amount < 50000:
        raise HTTPException(
            status_code=400,
            detail="E-Way Bill not required for invoice value below ₹50,000"
        )

    # Create E-Way Bill
    ewb = EWayBill(
        invoice_id=invoice.id,
        document_number=ewb_in.document_number,
        document_date=ewb_in.document_date,
        supply_type=ewb_in.supply_type,
        sub_supply_type=ewb_in.sub_supply_type,
        document_type=ewb_in.document_type,
        transaction_type=ewb_in.transaction_type,
        # From Address
        from_gstin=ewb_in.from_gstin,
        from_name=ewb_in.from_name,
        from_address1=ewb_in.from_address1,
        from_address2=ewb_in.from_address2,
        from_place=ewb_in.from_place,
        from_pincode=ewb_in.from_pincode,
        from_state_code=ewb_in.from_state_code,
        # To Address
        to_gstin=ewb_in.to_gstin,
        to_name=ewb_in.to_name,
        to_address1=ewb_in.to_address1,
        to_address2=ewb_in.to_address2,
        to_place=ewb_in.to_place,
        to_pincode=ewb_in.to_pincode,
        to_state_code=ewb_in.to_state_code,
        # Values from invoice
        total_value=invoice.grand_total,
        cgst_amount=invoice.cgst_amount,
        sgst_amount=invoice.sgst_amount,
        igst_amount=invoice.igst_amount,
        cess_amount=invoice.cess_amount,
        # Transport
        transporter_id=ewb_in.transporter_id,
        transporter_name=ewb_in.transporter_name,
        transporter_gstin=ewb_in.transporter_gstin,
        transport_mode=ewb_in.transport_mode,
        distance_km=ewb_in.distance_km,
        vehicle_number=ewb_in.vehicle_number,
        vehicle_type=ewb_in.vehicle_type,
        transport_doc_number=ewb_in.transport_doc_number,
        transport_doc_date=ewb_in.transport_doc_date,
    )

    db.add(ewb)
    await db.flush()

    # Create E-Way Bill items
    for invoice_item in invoice.items:
        ewb_item = EWayBillItem(
            eway_bill_id=ewb.id,
            product_name=invoice_item.item_name,
            hsn_code=invoice_item.hsn_code,
            quantity=invoice_item.quantity,
            uom=invoice_item.uom,
            taxable_value=invoice_item.taxable_value,
            gst_rate=invoice_item.gst_rate,
            cgst_amount=invoice_item.cgst_amount,
            sgst_amount=invoice_item.sgst_amount,
            igst_amount=invoice_item.igst_amount,
        )
        db.add(ewb_item)

    await db.commit()

    # Load full E-Way Bill
    result = await db.execute(
        select(EWayBill)
        .options(selectinload(EWayBill.items))
        .where(EWayBill.id == ewb.id)
    )
    ewb = result.scalar_one()

    return ewb


@router.post("/eway-bills/{ewb_id}/generate", response_model=EWayBillResponse)
async def generate_eway_bill_number(
    ewb_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Generate E-Way Bill number from GST portal."""
    result = await db.execute(
        select(EWayBill)
        .options(selectinload(EWayBill.items))
        .where(EWayBill.id == ewb_id)
    )
    ewb = result.scalar_one_or_none()

    if not ewb:
        raise HTTPException(status_code=404, detail="E-Way Bill not found")

    if ewb.eway_bill_number:
        raise HTTPException(status_code=400, detail="E-Way Bill number already generated")

    # TODO: Integrate with GST E-Way Bill API
    # For now, generate a mock E-Way Bill number
    import random
    mock_ewb_number = f"EWB{random.randint(100000000000, 999999999999)}"

    ewb.eway_bill_number = mock_ewb_number
    ewb.generated_at = datetime.utcnow()
    ewb.valid_from = datetime.utcnow()
    # Validity based on distance
    from datetime import timedelta
    if ewb.distance_km <= 100:
        validity_days = 1
    elif ewb.distance_km <= 300:
        validity_days = 3
    elif ewb.distance_km <= 500:
        validity_days = 5
    else:
        validity_days = int(ewb.distance_km / 100) + 1

    ewb.valid_until = datetime.utcnow() + timedelta(days=validity_days)
    ewb.status = EWayBillStatus.GENERATED

    await db.commit()
    await db.refresh(ewb)

    return ewb


@router.put("/eway-bills/{ewb_id}/vehicle", response_model=EWayBillResponse)
async def update_eway_bill_vehicle(
    ewb_id: UUID,
    vehicle_number: str,
    db: DB,
    vehicle_type: Optional[str] = None,
    reason: str = "BREAKDOWN",
    current_user: User = Depends(get_current_user),
):
    """Update vehicle details for E-Way Bill (Part-B update)."""
    result = await db.execute(
        select(EWayBill).where(EWayBill.id == ewb_id)
    )
    ewb = result.scalar_one_or_none()

    if not ewb:
        raise HTTPException(status_code=404, detail="E-Way Bill not found")

    if ewb.status == EWayBillStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot update cancelled E-Way Bill")

    # TODO: Call GST portal to update Part-B

    ewb.vehicle_number = vehicle_number
    if vehicle_type:
        ewb.vehicle_type = vehicle_type
    ewb.updated_by = current_user.id

    await db.commit()
    await db.refresh(ewb)

    return ewb


@router.post("/eway-bills/{ewb_id}/cancel", response_model=EWayBillResponse)
async def cancel_eway_bill(
    ewb_id: UUID,
    cancel_reason: str,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Cancel E-Way Bill within 24 hours."""
    result = await db.execute(
        select(EWayBill).where(EWayBill.id == ewb_id)
    )
    ewb = result.scalar_one_or_none()

    if not ewb:
        raise HTTPException(status_code=404, detail="E-Way Bill not found")

    if ewb.status == EWayBillStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="E-Way Bill already cancelled")

    # Check 24 hour window
    if ewb.ewb_date:
        hours_elapsed = (datetime.utcnow() - ewb.ewb_date).total_seconds() / 3600
        if hours_elapsed > 24:
            raise HTTPException(
                status_code=400,
                detail="E-Way Bill can only be cancelled within 24 hours"
            )

    # TODO: Call GST portal to cancel

    ewb.status = EWayBillStatus.CANCELLED
    ewb.cancel_reason = cancel_reason
    ewb.cancelled_at = datetime.utcnow()
    ewb.cancelled_by = current_user.id

    await db.commit()
    await db.refresh(ewb)

    return ewb


@router.get("/eway-bills", response_model=EWayBillListResponse)
async def list_eway_bills(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[EWayBillStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """List E-Way Bills."""
    query = select(EWayBill)
    count_query = select(func.count(EWayBill.id))

    filters = []
    if status:
        filters.append(EWayBill.status == status)
    if start_date:
        filters.append(func.date(EWayBill.created_at) >= start_date)
    if end_date:
        filters.append(func.date(EWayBill.created_at) <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(EWayBill.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    ewbs = result.scalars().all()

    return EWayBillListResponse(
        items=[EWayBillResponse.model_validate(e) for e in ewbs],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/eway-bills/{ewb_id}/print")
async def print_eway_bill(
    ewb_id: UUID,
    db: DB,
):
    """Generate printable E-Way Bill in HTML format."""
    from fastapi.responses import HTMLResponse

    result = await db.execute(
        select(EWayBill)
        .options(selectinload(EWayBill.items))
        .where(EWayBill.id == ewb_id)
    )
    ewb = result.scalar_one_or_none()

    if not ewb:
        raise HTTPException(status_code=404, detail="E-Way Bill not found")

    if not ewb.eway_bill_number:
        raise HTTPException(status_code=400, detail="E-Way Bill number not yet generated")

    # Format dates
    doc_date = ewb.document_date.strftime("%d-%m-%Y") if ewb.document_date else "N/A"
    valid_from = ewb.valid_from.strftime("%d-%m-%Y %H:%M") if ewb.valid_from else "N/A"
    valid_until = ewb.valid_until.strftime("%d-%m-%Y %H:%M") if ewb.valid_until else "N/A"
    generated_at = ewb.generated_at.strftime("%d-%m-%Y %H:%M") if ewb.generated_at else "N/A"

    # Transport mode mapping
    transport_modes = {"1": "Road", "2": "Rail", "3": "Air", "4": "Ship"}
    transport_mode_text = transport_modes.get(ewb.transport_mode, "Road")

    # Build items HTML
    items_html = ""
    for idx, item in enumerate(ewb.items, 1):
        items_html += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td>{item.product_name}</td>
            <td style="text-align: center;">{item.hsn_code}</td>
            <td style="text-align: right;">{float(item.quantity):.2f}</td>
            <td style="text-align: center;">{item.uom}</td>
            <td style="text-align: right;">₹{float(item.taxable_value):,.2f}</td>
            <td style="text-align: right;">{float(item.gst_rate):.1f}%</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>E-Way Bill - {ewb.eway_bill_number}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; font-size: 12px; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; border-bottom: 3px solid #1a5276; padding-bottom: 15px; margin-bottom: 20px; }}
            .header h1 {{ color: #1a5276; font-size: 24px; margin-bottom: 5px; }}
            .header .subtitle {{ color: #666; font-size: 14px; }}
            .ewb-number {{ background: #1a5276; color: white; padding: 10px 20px; font-size: 18px; font-weight: bold; display: inline-block; margin: 10px 0; border-radius: 5px; }}
            .status {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-left: 10px; }}
            .status.generated {{ background: #27ae60; color: white; }}
            .status.pending {{ background: #f39c12; color: white; }}
            .status.cancelled {{ background: #e74c3c; color: white; }}
            .section {{ margin-bottom: 20px; }}
            .section-title {{ background: #ecf0f1; padding: 8px 15px; font-weight: bold; color: #2c3e50; border-left: 4px solid #1a5276; margin-bottom: 10px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            .info-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
            .info-box h4 {{ color: #1a5276; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            .info-row {{ display: flex; margin-bottom: 5px; }}
            .info-label {{ width: 120px; color: #666; font-weight: 500; }}
            .info-value {{ flex: 1; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background: #1a5276; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background: #f9f9f9; }}
            .totals {{ text-align: right; margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
            .totals .row {{ display: flex; justify-content: flex-end; margin-bottom: 5px; }}
            .totals .label {{ width: 150px; color: #666; }}
            .totals .value {{ width: 120px; text-align: right; font-weight: 500; }}
            .totals .grand-total {{ font-size: 16px; font-weight: bold; color: #1a5276; border-top: 2px solid #1a5276; padding-top: 10px; margin-top: 10px; }}
            .validity {{ background: #e8f6f3; border: 1px solid #1abc9c; padding: 15px; border-radius: 5px; margin-top: 20px; }}
            .validity h4 {{ color: #16a085; margin-bottom: 10px; }}
            .qr-section {{ text-align: center; margin-top: 20px; padding: 20px; border: 2px dashed #ddd; }}
            .footer {{ text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; font-size: 10px; }}
            @media print {{
                body {{ background: white; padding: 0; }}
                .container {{ box-shadow: none; }}
                .no-print {{ display: none; }}
            }}
            .print-btn {{ background: #1a5276; color: white; padding: 10px 30px; border: none; cursor: pointer; font-size: 14px; border-radius: 5px; margin-bottom: 20px; }}
            .print-btn:hover {{ background: #154360; }}
        </style>
    </head>
    <body>
        <div class="container">
            <button class="print-btn no-print" onclick="window.print()">🖨️ Print E-Way Bill</button>

            <div class="header">
                <h1>E-WAY BILL</h1>
                <div class="subtitle">Generated under GST (Goods and Services Tax)</div>
                <div class="ewb-number">{ewb.eway_bill_number}</div>
                <span class="status {ewb.status.value.lower()}">{ewb.status.value}</span>
            </div>

            <div class="section">
                <div class="section-title">Document Details</div>
                <div class="info-grid">
                    <div class="info-box">
                        <div class="info-row">
                            <span class="info-label">Document No:</span>
                            <span class="info-value"><strong>{ewb.document_number}</strong></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Document Date:</span>
                            <span class="info-value">{doc_date}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Document Type:</span>
                            <span class="info-value">{ewb.document_type}</span>
                        </div>
                    </div>
                    <div class="info-box">
                        <div class="info-row">
                            <span class="info-label">Supply Type:</span>
                            <span class="info-value">{"Outward" if ewb.supply_type == "O" else "Inward"}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Generated On:</span>
                            <span class="info-value">{generated_at}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Distance:</span>
                            <span class="info-value">{ewb.distance_km} KM</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Party Details</div>
                <div class="info-grid">
                    <div class="info-box">
                        <h4>FROM (Consignor)</h4>
                        <div class="info-row">
                            <span class="info-label">GSTIN:</span>
                            <span class="info-value"><strong>{ewb.from_gstin}</strong></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Name:</span>
                            <span class="info-value">{ewb.from_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Address:</span>
                            <span class="info-value">{ewb.from_address1}{', ' + ewb.from_address2 if ewb.from_address2 else ''}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Place/Pincode:</span>
                            <span class="info-value">{ewb.from_place} - {ewb.from_pincode}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">State Code:</span>
                            <span class="info-value">{ewb.from_state_code}</span>
                        </div>
                    </div>
                    <div class="info-box">
                        <h4>TO (Consignee)</h4>
                        <div class="info-row">
                            <span class="info-label">GSTIN:</span>
                            <span class="info-value">{ewb.to_gstin or "Unregistered"}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Name:</span>
                            <span class="info-value">{ewb.to_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Address:</span>
                            <span class="info-value">{ewb.to_address1}{', ' + ewb.to_address2 if ewb.to_address2 else ''}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Place/Pincode:</span>
                            <span class="info-value">{ewb.to_place} - {ewb.to_pincode}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">State Code:</span>
                            <span class="info-value">{ewb.to_state_code}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Transport Details</div>
                <div class="info-grid">
                    <div class="info-box">
                        <div class="info-row">
                            <span class="info-label">Mode:</span>
                            <span class="info-value">{transport_mode_text}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Transporter:</span>
                            <span class="info-value">{ewb.transporter_name or "N/A"}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Trans. GSTIN:</span>
                            <span class="info-value">{ewb.transporter_gstin or "N/A"}</span>
                        </div>
                    </div>
                    <div class="info-box">
                        <div class="info-row">
                            <span class="info-label">Vehicle No:</span>
                            <span class="info-value">{ewb.vehicle_number or "Not Updated"}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Vehicle Type:</span>
                            <span class="info-value">{ewb.vehicle_type or "N/A"}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">LR/RR No:</span>
                            <span class="info-value">{ewb.transport_doc_number or "N/A"}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Goods Details</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 40px;">#</th>
                            <th>Product Name</th>
                            <th style="width: 80px;">HSN</th>
                            <th style="width: 70px;">Qty</th>
                            <th style="width: 50px;">UOM</th>
                            <th style="width: 100px;">Taxable Value</th>
                            <th style="width: 60px;">GST%</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>

                <div class="totals">
                    <div class="row">
                        <span class="label">CGST:</span>
                        <span class="value">₹{float(ewb.cgst_amount):,.2f}</span>
                    </div>
                    <div class="row">
                        <span class="label">SGST:</span>
                        <span class="value">₹{float(ewb.sgst_amount):,.2f}</span>
                    </div>
                    <div class="row">
                        <span class="label">IGST:</span>
                        <span class="value">₹{float(ewb.igst_amount):,.2f}</span>
                    </div>
                    <div class="row">
                        <span class="label">CESS:</span>
                        <span class="value">₹{float(ewb.cess_amount):,.2f}</span>
                    </div>
                    <div class="row grand-total">
                        <span class="label">TOTAL VALUE:</span>
                        <span class="value">₹{float(ewb.total_value):,.2f}</span>
                    </div>
                </div>
            </div>

            <div class="validity">
                <h4>⏰ E-Way Bill Validity</h4>
                <div class="info-grid" style="margin-top: 10px;">
                    <div>
                        <div class="info-row">
                            <span class="info-label">Valid From:</span>
                            <span class="info-value"><strong>{valid_from}</strong></span>
                        </div>
                    </div>
                    <div>
                        <div class="info-row">
                            <span class="info-label">Valid Until:</span>
                            <span class="info-value"><strong>{valid_until}</strong></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="qr-section">
                <p style="color: #666;">QR Code will be displayed here when integrated with GST Portal</p>
                <p style="font-size: 10px; margin-top: 5px;">[Scan to verify E-Way Bill authenticity]</p>
            </div>

            <div class="footer">
                <p>This is a computer generated E-Way Bill and does not require signature.</p>
                <p>Generated by Consumer Durable ERP System | Verify at: ewaybillgst.gov.in</p>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


# ==================== Payment Receipts ====================

@router.post("/receipts", response_model=PaymentReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_receipt(
    receipt_in: PaymentReceiptCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Record a payment receipt against invoice."""
    # Verify invoice
    invoice_result = await db.execute(
        select(TaxInvoice).where(TaxInvoice.id == receipt_in.invoice_id)
    )
    invoice = invoice_result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if receipt_in.amount > invoice.amount_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ({receipt_in.amount}) exceeds balance due ({invoice.amount_due})"
        )

    # Generate receipt number
    today = date.today()
    count_result = await db.execute(
        select(func.count(PaymentReceipt.id)).where(
            func.date(PaymentReceipt.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    receipt_number = f"RCP-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    receipt = PaymentReceipt(
        receipt_number=receipt_number,
        receipt_date=receipt_in.receipt_date,
        invoice_id=receipt_in.invoice_id,
        customer_id=invoice.customer_id,
        dealer_id=invoice.dealer_id,
        amount=receipt_in.amount,
        payment_mode=receipt_in.payment_mode,
        payment_reference=receipt_in.payment_reference,
        bank_name=receipt_in.bank_name,
        cheque_number=receipt_in.cheque_number,
        cheque_date=receipt_in.cheque_date,
        transaction_id=receipt_in.transaction_id,
        narration=receipt_in.narration,
        received_by=current_user.id,
        created_by=current_user.id,
    )

    db.add(receipt)

    # Update invoice
    invoice.amount_paid += receipt_in.amount
    invoice.amount_due -= receipt_in.amount

    if invoice.amount_due <= 0:
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    await db.commit()
    await db.refresh(receipt)

    return receipt


@router.get("/receipts", response_model=PaymentReceiptListResponse)
async def list_payment_receipts(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    customer_id: Optional[UUID] = None,
    invoice_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """List payment receipts."""
    query = select(PaymentReceipt)
    count_query = select(func.count(PaymentReceipt.id))
    amount_query = select(func.coalesce(func.sum(PaymentReceipt.amount), 0))

    filters = []
    if customer_id:
        filters.append(PaymentReceipt.customer_id == customer_id)
    if invoice_id:
        filters.append(PaymentReceipt.invoice_id == invoice_id)
    if start_date:
        filters.append(PaymentReceipt.receipt_date >= start_date)
    if end_date:
        filters.append(PaymentReceipt.receipt_date <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
        amount_query = amount_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_amount_result = await db.execute(amount_query)
    total_amount = total_amount_result.scalar() or Decimal("0")

    query = query.order_by(PaymentReceipt.receipt_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    receipts = result.scalars().all()

    return PaymentReceiptListResponse(
        items=[PaymentReceiptResponse.model_validate(r) for r in receipts],
        total=total,
        total_amount=total_amount,
        skip=skip,
        limit=limit
    )


# ==================== GST Reports ====================

@router.get("/reports/gstr1")
async def get_gstr1_report(
    db: DB,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2017),
    current_user: User = Depends(get_current_user),
):
    """Generate GSTR-1 (Outward Supplies) report data."""
    from calendar import monthrange
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    # B2B Invoices (to registered dealers/businesses)
    b2b_query = select(TaxInvoice).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            TaxInvoice.billing_gstin.isnot(None),
            TaxInvoice.billing_gstin != "",
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    )
    b2b_result = await db.execute(b2b_query)
    b2b_invoices = b2b_result.scalars().all()

    # B2C Large (> 2.5L inter-state to unregistered)
    b2cl_query = select(TaxInvoice).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            or_(TaxInvoice.billing_gstin.is_(None), TaxInvoice.billing_gstin == ""),
            TaxInvoice.is_inter_state == True,
            TaxInvoice.grand_total > 250000,
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    )
    b2cl_result = await db.execute(b2cl_query)
    b2cl_invoices = b2cl_result.scalars().all()

    # B2CS (B2C Small - remaining unregistered)
    b2cs_query = select(
        TaxInvoice.place_of_supply,
        func.sum(TaxInvoice.taxable_amount).label("taxable_value"),
        func.sum(TaxInvoice.cgst_amount).label("cgst"),
        func.sum(TaxInvoice.sgst_amount).label("sgst"),
        func.sum(TaxInvoice.igst_amount).label("igst"),
    ).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            or_(TaxInvoice.billing_gstin.is_(None), TaxInvoice.billing_gstin == ""),
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    ).group_by(TaxInvoice.place_of_supply)

    b2cs_result = await db.execute(b2cs_query)
    b2cs_data = b2cs_result.all()

    # Credit/Debit Notes
    cdn_query = select(CreditDebitNote).where(
        and_(
            CreditDebitNote.note_date >= start_date,
            CreditDebitNote.note_date <= end_date,
        )
    )
    cdn_result = await db.execute(cdn_query)
    credit_debit_notes = cdn_result.scalars().all()

    # HSN Summary
    hsn_query = select(
        InvoiceItem.hsn_code,
        func.sum(InvoiceItem.quantity).label("qty"),
        func.sum(InvoiceItem.taxable_amount).label("taxable"),
        func.sum(InvoiceItem.igst_amount).label("igst"),
        func.sum(InvoiceItem.cgst_amount).label("cgst"),
        func.sum(InvoiceItem.sgst_amount).label("sgst"),
    ).join(TaxInvoice).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    ).group_by(InvoiceItem.hsn_code)

    hsn_result = await db.execute(hsn_query)
    hsn_summary = hsn_result.all()

    return {
        "return_period": f"{month:02d}{year}",
        "b2b": [
            {
                "gstin": inv.billing_gstin,
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date.isoformat(),
                "invoice_value": float(inv.grand_total),
                "place_of_supply": inv.place_of_supply,
                "taxable_value": float(inv.taxable_amount),
                "cgst": float(inv.cgst_amount),
                "sgst": float(inv.sgst_amount),
                "igst": float(inv.igst_amount),
                "cess": float(inv.cess_amount),
            }
            for inv in b2b_invoices
        ],
        "b2cl": [
            {
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date.isoformat(),
                "invoice_value": float(inv.grand_total),
                "place_of_supply": inv.place_of_supply,
                "taxable_value": float(inv.taxable_amount),
                "igst": float(inv.igst_amount),
            }
            for inv in b2cl_invoices
        ],
        "b2cs": [
            {
                "place_of_supply": row.place_of_supply,
                "taxable_value": float(row.taxable_value or 0),
                "cgst": float(row.cgst or 0),
                "sgst": float(row.sgst or 0),
                "igst": float(row.igst or 0),
            }
            for row in b2cs_data
        ],
        "cdnr": [
            {
                "note_number": note.note_number,
                "note_date": note.note_date.isoformat(),
                "note_type": note.document_type.value,
                "original_invoice_number": note.original_invoice_number,
                "original_invoice_date": note.original_invoice_date.isoformat() if note.original_invoice_date else None,
                "taxable_value": float(note.taxable_amount),
                "cgst": float(note.cgst_amount),
                "sgst": float(note.sgst_amount),
                "igst": float(note.igst_amount),
            }
            for note in credit_debit_notes
        ],
        "hsn": [
            {
                "hsn_code": row.hsn_code,
                "quantity": float(row.qty or 0),
                "taxable_value": float(row.taxable or 0),
                "igst": float(row.igst or 0),
                "cgst": float(row.cgst or 0),
                "sgst": float(row.sgst or 0),
            }
            for row in hsn_summary
        ],
    }


@router.get("/reports/gstr3b")
async def get_gstr3b_report(
    db: DB,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2017),
    current_user: User = Depends(get_current_user),
):
    """Generate GSTR-3B (Monthly Summary) report data."""
    from calendar import monthrange
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    # Outward taxable supplies
    outward_query = select(
        func.sum(TaxInvoice.taxable_amount).label("taxable"),
        func.sum(TaxInvoice.igst_amount).label("igst"),
        func.sum(TaxInvoice.cgst_amount).label("cgst"),
        func.sum(TaxInvoice.sgst_amount).label("sgst"),
        func.sum(TaxInvoice.cess_amount).label("cess"),
    ).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    )

    outward_result = await db.execute(outward_query)
    outward = outward_result.one()

    # Inter-state supplies
    inter_state_query = select(
        func.sum(TaxInvoice.taxable_amount).label("taxable"),
        func.sum(TaxInvoice.igst_amount).label("igst"),
    ).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            TaxInvoice.is_inter_state == True,
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    )

    inter_result = await db.execute(inter_state_query)
    inter_state = inter_result.one()

    # Intra-state supplies
    intra_state_query = select(
        func.sum(TaxInvoice.taxable_amount).label("taxable"),
        func.sum(TaxInvoice.cgst_amount).label("cgst"),
        func.sum(TaxInvoice.sgst_amount).label("sgst"),
    ).where(
        and_(
            TaxInvoice.invoice_date >= start_date,
            TaxInvoice.invoice_date <= end_date,
            TaxInvoice.is_inter_state == False,
            TaxInvoice.status != InvoiceStatus.CANCELLED,
        )
    )

    intra_result = await db.execute(intra_state_query)
    intra_state = intra_result.one()

    return {
        "return_period": f"{month:02d}{year}",
        "outward_taxable_supplies": {
            "taxable_value": float(outward.taxable or 0),
            "igst": float(outward.igst or 0),
            "cgst": float(outward.cgst or 0),
            "sgst": float(outward.sgst or 0),
            "cess": float(outward.cess or 0),
        },
        "inter_state_supplies": {
            "taxable_value": float(inter_state.taxable or 0),
            "igst": float(inter_state.igst or 0),
        },
        "intra_state_supplies": {
            "taxable_value": float(intra_state.taxable or 0),
            "cgst": float(intra_state.cgst or 0),
            "sgst": float(intra_state.sgst or 0),
        },
        "tax_payable": {
            "igst": float(outward.igst or 0),
            "cgst": float(outward.cgst or 0),
            "sgst": float(outward.sgst or 0),
            "cess": float(outward.cess or 0),
            "total": float((outward.igst or 0) + (outward.cgst or 0) + (outward.sgst or 0) + (outward.cess or 0)),
        },
    }
