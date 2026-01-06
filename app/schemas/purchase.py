"""Pydantic schemas for Purchase/Procurement module."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.purchase import (
    RequisitionStatus, POStatus, GRNStatus, VendorInvoiceStatus, QualityCheckResult
)


# ==================== Purchase Requisition Schemas ====================

class PRItemBase(BaseModel):
    """Base schema for PR item."""
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name: str
    sku: str
    quantity_requested: int = Field(..., gt=0)
    uom: str = "PCS"
    estimated_unit_price: Decimal = Field(Decimal("0"), ge=0)
    preferred_vendor_id: Optional[UUID] = None
    notes: Optional[str] = None


class PRItemCreate(PRItemBase):
    """Schema for creating PR item."""
    pass


class PRItemResponse(PRItemBase):
    """Response schema for PR item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimated_total: Decimal


class PurchaseRequisitionBase(BaseModel):
    """Base schema for Purchase Requisition."""
    requesting_department: Optional[str] = None
    required_by_date: Optional[date] = None
    delivery_warehouse_id: UUID
    priority: int = Field(5, ge=1, le=10)
    reason: Optional[str] = None
    notes: Optional[str] = None


class PurchaseRequisitionCreate(PurchaseRequisitionBase):
    """Schema for creating PR."""
    items: List[PRItemCreate]


class PurchaseRequisitionUpdate(BaseModel):
    """Schema for updating PR."""
    required_by_date: Optional[date] = None
    priority: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class PurchaseRequisitionResponse(PurchaseRequisitionBase):
    """Response schema for PR."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requisition_number: str
    status: RequisitionStatus
    request_date: date
    requested_by: UUID
    estimated_total: Decimal
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    converted_to_po_id: Optional[UUID] = None
    items: List[PRItemResponse] = []
    created_at: datetime
    updated_at: datetime


class PRListResponse(BaseModel):
    """Response for listing PRs."""
    items: List[PurchaseRequisitionResponse]
    total: int
    skip: int
    limit: int


class PRApproveRequest(BaseModel):
    """Request to approve/reject PR."""
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    rejection_reason: Optional[str] = None


# ==================== Purchase Order Schemas ====================

class POItemBase(BaseModel):
    """Base schema for PO item."""
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name: str
    sku: str
    hsn_code: Optional[str] = None
    quantity_ordered: int = Field(..., gt=0)
    uom: str = "PCS"
    unit_price: Decimal = Field(..., ge=0)
    discount_percentage: Decimal = Field(Decimal("0"), ge=0, le=100)
    gst_rate: Decimal = Field(Decimal("18"), ge=0, le=28)
    expected_date: Optional[date] = None
    notes: Optional[str] = None


class POItemCreate(POItemBase):
    """Schema for creating PO item."""
    pass


class POItemResponse(POItemBase):
    """Response schema for PO item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_number: int
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_rate: Decimal
    sgst_rate: Decimal
    igst_rate: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    total_amount: Decimal
    quantity_received: int
    quantity_accepted: int
    quantity_rejected: int
    quantity_pending: int
    is_closed: bool


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""
    vendor_id: UUID
    delivery_warehouse_id: UUID
    expected_delivery_date: Optional[date] = None
    delivery_address: Optional[dict] = None
    payment_terms: Optional[str] = None
    credit_days: int = 30
    advance_required: Decimal = Field(Decimal("0"), ge=0)
    quotation_reference: Optional[str] = None
    quotation_date: Optional[date] = None
    freight_charges: Decimal = Field(Decimal("0"), ge=0)
    packing_charges: Decimal = Field(Decimal("0"), ge=0)
    other_charges: Decimal = Field(Decimal("0"), ge=0)
    terms_and_conditions: Optional[str] = None
    special_instructions: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating PO."""
    requisition_id: Optional[UUID] = None
    items: List[POItemCreate]


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating PO."""
    expected_delivery_date: Optional[date] = None
    payment_terms: Optional[str] = None
    freight_charges: Optional[Decimal] = None
    packing_charges: Optional[Decimal] = None
    other_charges: Optional[Decimal] = None
    terms_and_conditions: Optional[str] = None
    special_instructions: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Response schema for PO."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    po_date: date
    status: POStatus
    requisition_id: Optional[UUID] = None
    vendor_name: str
    vendor_gstin: Optional[str] = None
    subtotal: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    total_tax: Decimal
    grand_total: Decimal
    total_received_value: Decimal
    advance_paid: Decimal
    po_pdf_url: Optional[str] = None
    sent_to_vendor_at: Optional[datetime] = None
    vendor_acknowledged_at: Optional[datetime] = None
    items: List[POItemResponse] = []
    created_by: UUID
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class POBrief(BaseModel):
    """Brief PO for dropdowns."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    po_date: date
    vendor_name: str
    status: POStatus
    grand_total: Decimal
    total_received_value: Decimal


class POListResponse(BaseModel):
    """Response for listing POs."""
    items: List[POBrief]
    total: int
    total_value: Decimal
    skip: int
    limit: int


class POApproveRequest(BaseModel):
    """Request to approve/reject PO."""
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    rejection_reason: Optional[str] = None


class POSendToVendorRequest(BaseModel):
    """Request to send PO to vendor."""
    send_email: bool = True
    email_recipients: Optional[List[str]] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None


# ==================== GRN Schemas ====================

class GRNItemBase(BaseModel):
    """Base schema for GRN item."""
    po_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name: str
    sku: str
    quantity_expected: int
    quantity_received: int = Field(..., ge=0)
    quantity_accepted: int = Field(0, ge=0)
    quantity_rejected: int = Field(0, ge=0)
    uom: str = "PCS"
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    serial_numbers: Optional[List[str]] = None
    bin_id: Optional[UUID] = None
    bin_location: Optional[str] = None
    rejection_reason: Optional[str] = None
    remarks: Optional[str] = None


class GRNItemCreate(GRNItemBase):
    """Schema for creating GRN item."""
    pass


class GRNItemResponse(GRNItemBase):
    """Response schema for GRN item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    unit_price: Decimal
    accepted_value: Decimal
    qc_result: Optional[QualityCheckResult] = None


class GoodsReceiptBase(BaseModel):
    """Base schema for GRN."""
    purchase_order_id: UUID
    warehouse_id: UUID
    vendor_challan_number: Optional[str] = None
    vendor_challan_date: Optional[date] = None
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    qc_required: bool = True
    receiving_remarks: Optional[str] = None


class GoodsReceiptCreate(GoodsReceiptBase):
    """Schema for creating GRN."""
    grn_date: date
    items: List[GRNItemCreate]


class GoodsReceiptUpdate(BaseModel):
    """Schema for updating GRN."""
    vendor_challan_number: Optional[str] = None
    vendor_challan_date: Optional[date] = None
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    receiving_remarks: Optional[str] = None


class GoodsReceiptResponse(GoodsReceiptBase):
    """Response schema for GRN."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_number: str
    grn_date: date
    status: GRNStatus
    vendor_id: UUID
    total_items: int
    total_quantity_received: int
    total_quantity_accepted: int
    total_quantity_rejected: int
    total_value: Decimal
    qc_status: Optional[QualityCheckResult] = None
    qc_done_by: Optional[UUID] = None
    qc_done_at: Optional[datetime] = None
    qc_remarks: Optional[str] = None
    received_by: UUID
    put_away_complete: bool
    put_away_at: Optional[datetime] = None
    items: List[GRNItemResponse] = []
    grn_pdf_url: Optional[str] = None
    photos_urls: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


class GRNBrief(BaseModel):
    """Brief GRN for listing."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_number: str
    grn_date: date
    po_number: str
    vendor_name: str
    status: GRNStatus
    total_quantity_received: int
    total_value: Decimal


class GRNListResponse(BaseModel):
    """Response for listing GRNs."""
    items: List[GRNBrief]
    total: int
    total_value: Decimal
    skip: int
    limit: int


class GRNQualityCheckRequest(BaseModel):
    """Request for QC on GRN."""
    item_results: List[dict]  # [{item_id, qc_result, rejection_reason}]
    overall_remarks: Optional[str] = None


class GRNPutAwayRequest(BaseModel):
    """Request for put-away after GRN."""
    item_locations: List[dict]  # [{item_id, bin_id, bin_location}]


# ==================== Vendor Invoice Schemas ====================

class VendorInvoiceBase(BaseModel):
    """Base schema for Vendor Invoice."""
    vendor_id: UUID
    invoice_number: str = Field(..., max_length=50)
    invoice_date: date
    purchase_order_id: Optional[UUID] = None
    grn_id: Optional[UUID] = None
    subtotal: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(Decimal("0"), ge=0)
    cgst_amount: Decimal = Field(Decimal("0"), ge=0)
    sgst_amount: Decimal = Field(Decimal("0"), ge=0)
    igst_amount: Decimal = Field(Decimal("0"), ge=0)
    cess_amount: Decimal = Field(Decimal("0"), ge=0)
    freight_charges: Decimal = Field(Decimal("0"), ge=0)
    other_charges: Decimal = Field(Decimal("0"), ge=0)
    round_off: Decimal = Field(Decimal("0"))
    grand_total: Decimal = Field(..., ge=0)
    due_date: date
    tds_applicable: bool = True
    tds_section: Optional[str] = None
    tds_rate: Decimal = Field(Decimal("0"), ge=0, le=100)
    vendor_irn: Optional[str] = None
    vendor_ack_number: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    internal_notes: Optional[str] = None


class VendorInvoiceCreate(VendorInvoiceBase):
    """Schema for creating vendor invoice."""
    pass


class VendorInvoiceUpdate(BaseModel):
    """Schema for updating vendor invoice."""
    due_date: Optional[date] = None
    tds_rate: Optional[Decimal] = None
    internal_notes: Optional[str] = None


class VendorInvoiceResponse(VendorInvoiceBase):
    """Response schema for Vendor Invoice."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    our_reference: str
    status: VendorInvoiceStatus
    taxable_amount: Decimal
    total_tax: Decimal
    tds_amount: Decimal
    net_payable: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    po_matched: bool
    grn_matched: bool
    is_fully_matched: bool
    matching_variance: Decimal
    variance_reason: Optional[str] = None
    received_by: UUID
    received_at: datetime
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class VendorInvoiceBrief(BaseModel):
    """Brief vendor invoice."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    our_reference: str
    invoice_number: str
    invoice_date: date
    vendor_name: str
    grand_total: Decimal
    balance_due: Decimal
    due_date: date
    status: VendorInvoiceStatus


class VendorInvoiceListResponse(BaseModel):
    """Response for listing vendor invoices."""
    items: List[VendorInvoiceBrief]
    total: int
    total_value: Decimal
    total_balance: Decimal
    skip: int
    limit: int


class ThreeWayMatchRequest(BaseModel):
    """Request for 3-way matching."""
    vendor_invoice_id: UUID
    purchase_order_id: UUID
    grn_id: UUID
    tolerance_percentage: Decimal = Field(Decimal("2"), ge=0, le=10)


class ThreeWayMatchResponse(BaseModel):
    """Response for 3-way matching."""
    is_matched: bool
    po_total: Decimal
    grn_value: Decimal
    invoice_total: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    discrepancies: List[dict] = []
    recommendations: List[str] = []


# ==================== Report Schemas ====================

class POSummaryRequest(BaseModel):
    """Request for PO summary."""
    start_date: date
    end_date: date
    vendor_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None


class POSummaryResponse(BaseModel):
    """PO summary response."""
    period_start: date
    period_end: date
    total_po_count: int
    total_po_value: Decimal
    pending_count: int
    pending_value: Decimal
    received_count: int
    received_value: Decimal
    cancelled_count: int
    cancelled_value: Decimal
    by_vendor: List[dict] = []
    by_status: dict = {}


class GRNSummaryResponse(BaseModel):
    """GRN summary response."""
    period_start: date
    period_end: date
    total_grn_count: int
    total_received_value: Decimal
    total_accepted_value: Decimal
    total_rejected_value: Decimal
    rejection_rate: Decimal
    by_vendor: List[dict] = []
    by_warehouse: List[dict] = []


class PendingGRNResponse(BaseModel):
    """Pending GRNs against POs."""
    po_id: UUID
    po_number: str
    vendor_name: str
    po_date: date
    expected_date: Optional[date]
    total_ordered: int
    total_received: int
    pending_quantity: int
    pending_value: Decimal
    days_pending: int
