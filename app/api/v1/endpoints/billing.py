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
    # Generate invoice number from sequence
    sequence_result = await db.execute(
        select(InvoiceNumberSequence).where(
            and_(
                InvoiceNumberSequence.invoice_type == invoice_in.invoice_type,
                InvoiceNumberSequence.financial_year == invoice_in.financial_year,
                InvoiceNumberSequence.is_active == True,
            )
        )
    )
    sequence = sequence_result.scalar_one_or_none()

    if not sequence:
        # Create default sequence
        sequence = InvoiceNumberSequence(
            invoice_type=invoice_in.invoice_type,
            financial_year=invoice_in.financial_year,
            prefix=f"INV/{invoice_in.financial_year}/",
            current_number=0,
            created_by=current_user.id,
        )
        db.add(sequence)
        await db.flush()

    sequence.current_number += 1
    invoice_number = f"{sequence.prefix}{str(sequence.current_number).zfill(sequence.padding_length)}"

    # Determine if inter-state
    is_inter_state = invoice_in.billing_state_code != invoice_in.shipping_state_code

    # Create invoice
    invoice = TaxInvoice(
        invoice_number=invoice_number,
        invoice_type=invoice_in.invoice_type,
        invoice_date=invoice_in.invoice_date,
        due_date=invoice_in.due_date,
        financial_year=invoice_in.financial_year,
        order_id=invoice_in.order_id,
        customer_id=invoice_in.customer_id,
        dealer_id=invoice_in.dealer_id,
        # Billing Address
        billing_name=invoice_in.billing_name,
        billing_gstin=invoice_in.billing_gstin,
        billing_address=invoice_in.billing_address,
        billing_city=invoice_in.billing_city,
        billing_state=invoice_in.billing_state,
        billing_state_code=invoice_in.billing_state_code,
        billing_pincode=invoice_in.billing_pincode,
        # Shipping Address
        shipping_name=invoice_in.shipping_name,
        shipping_address=invoice_in.shipping_address,
        shipping_city=invoice_in.shipping_city,
        shipping_state=invoice_in.shipping_state,
        shipping_state_code=invoice_in.shipping_state_code,
        shipping_pincode=invoice_in.shipping_pincode,
        # Seller Info
        seller_gstin=invoice_in.seller_gstin,
        place_of_supply=invoice_in.place_of_supply,
        is_inter_state=is_inter_state,
        # Terms
        payment_terms=invoice_in.payment_terms,
        delivery_terms=invoice_in.delivery_terms,
        notes=invoice_in.notes,
        created_by=current_user.id,
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

        item = InvoiceItem(
            invoice_id=invoice.id,
            line_number=line_number,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            product_name=item_data.product_name,
            product_description=item_data.product_description,
            hsn_code=item_data.hsn_code,
            sku=item_data.sku,
            quantity=item_data.quantity,
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
            cess_rate=item_data.cess_rate or Decimal("0"),
            cess_amount=cess_amount,
            total_amount=item_total,
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
    invoice.balance_due = grand_total

    await db.commit()

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
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        supply_type=ewb_in.supply_type,
        sub_supply_type=ewb_in.sub_supply_type,
        document_type=ewb_in.document_type,
        # From Address
        from_gstin=invoice.seller_gstin,
        from_name=ewb_in.from_name,
        from_address=ewb_in.from_address,
        from_place=ewb_in.from_place,
        from_pincode=ewb_in.from_pincode,
        from_state_code=ewb_in.from_state_code,
        # To Address
        to_gstin=invoice.billing_gstin,
        to_name=invoice.shipping_name,
        to_address=invoice.shipping_address,
        to_place=invoice.shipping_city,
        to_pincode=invoice.shipping_pincode,
        to_state_code=invoice.shipping_state_code,
        # Values
        taxable_value=invoice.taxable_amount,
        cgst_value=invoice.cgst_amount,
        sgst_value=invoice.sgst_amount,
        igst_value=invoice.igst_amount,
        cess_value=invoice.cess_amount,
        total_value=invoice.grand_total,
        # Transport
        transporter_id=ewb_in.transporter_id,
        transporter_name=ewb_in.transporter_name,
        transporter_gstin=ewb_in.transporter_gstin,
        transport_mode=ewb_in.transport_mode,
        transport_distance=ewb_in.transport_distance,
        vehicle_number=ewb_in.vehicle_number,
        vehicle_type=ewb_in.vehicle_type,
        created_by=current_user.id,
    )

    db.add(ewb)
    await db.flush()

    # Create E-Way Bill items
    for invoice_item in invoice.items:
        ewb_item = EWayBillItem(
            eway_bill_id=ewb.id,
            product_name=invoice_item.product_name,
            hsn_code=invoice_item.hsn_code,
            quantity=invoice_item.quantity,
            uom=invoice_item.uom,
            taxable_value=invoice_item.taxable_amount,
            cgst_rate=invoice_item.cgst_rate,
            sgst_rate=invoice_item.sgst_rate,
            igst_rate=invoice_item.igst_rate,
            cess_rate=invoice_item.cess_rate,
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

    if ewb.ewb_number:
        raise HTTPException(status_code=400, detail="E-Way Bill number already generated")

    # TODO: Integrate with GST E-Way Bill API
    # For now, generate a mock E-Way Bill number
    import random
    mock_ewb_number = f"EWB{random.randint(100000000000, 999999999999)}"

    ewb.ewb_number = mock_ewb_number
    ewb.ewb_date = datetime.utcnow()
    ewb.valid_from = datetime.utcnow()
    # Validity based on distance
    from datetime import timedelta
    if ewb.transport_distance <= 100:
        validity_days = 1
    elif ewb.transport_distance <= 300:
        validity_days = 3
    elif ewb.transport_distance <= 500:
        validity_days = 5
    else:
        validity_days = int(ewb.transport_distance / 100) + 1

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

    if receipt_in.amount > invoice.balance_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ({receipt_in.amount}) exceeds balance due ({invoice.balance_due})"
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
    invoice.balance_due -= receipt_in.amount

    if invoice.balance_due <= 0:
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
