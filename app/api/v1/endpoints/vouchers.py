"""API endpoints for Voucher module - Unified Voucher System."""
from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.voucher import VoucherStatus
from app.schemas.voucher import (
    VoucherCreate, VoucherUpdate, VoucherResponse, VoucherListResponse,
    VoucherLineResponse, VoucherAllocationResponse,
    VoucherSubmitRequest, VoucherApproveRequest, VoucherRejectRequest,
    VoucherCancelRequest, VoucherReverseRequest, VoucherWorkflowResponse,
    VoucherTypesResponse, VoucherTypeMetadata,
    PartyAccountsResponse, VoucherSummary,
)
from app.services.voucher_service import VoucherService
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions

router = APIRouter()


def _get_user_name(user: Optional[User]) -> Optional[str]:
    """Get formatted user name."""
    if not user:
        return None
    return f"{user.first_name} {user.last_name or ''}".strip()


def _build_voucher_response(voucher) -> dict:
    """Build voucher response with account info in lines."""
    lines = []
    for line in voucher.lines:
        lines.append({
            "id": line.id,
            "line_number": line.line_number,
            "account_id": line.account_id,
            "account_code": line.account.account_code if line.account else None,
            "account_name": line.account.account_name if line.account else None,
            "debit_amount": line.debit_amount,
            "credit_amount": line.credit_amount,
            "description": line.description,
            "cost_center_id": line.cost_center_id,
            "hsn_code": line.hsn_code,
            "tax_rate": line.tax_rate,
            "is_tax_line": line.is_tax_line,
            "reference_line_id": line.reference_line_id,
            "created_at": line.created_at,
        })

    allocations = []
    for alloc in voucher.allocations:
        allocations.append({
            "id": alloc.id,
            "voucher_id": alloc.voucher_id,
            "source_type": alloc.source_type,
            "source_id": alloc.source_id,
            "source_number": alloc.source_number,
            "allocated_amount": alloc.allocated_amount,
            "tds_amount": alloc.tds_amount,
            "created_at": alloc.created_at,
            "created_by": alloc.created_by,
        })

    return {
        "id": voucher.id,
        "voucher_number": voucher.voucher_number,
        "voucher_type": voucher.voucher_type,
        "voucher_date": voucher.voucher_date,
        "period_id": voucher.period_id,
        "narration": voucher.narration,
        "total_debit": voucher.total_debit,
        "total_credit": voucher.total_credit,
        "party_type": voucher.party_type,
        "party_id": voucher.party_id,
        "party_name": voucher.party_name,
        "reference_type": voucher.reference_type,
        "reference_id": voucher.reference_id,
        "reference_number": voucher.reference_number,
        "is_gst_applicable": voucher.is_gst_applicable,
        "gstin": voucher.gstin,
        "place_of_supply": voucher.place_of_supply,
        "place_of_supply_code": voucher.place_of_supply_code,
        "is_rcm": voucher.is_rcm,
        "is_interstate": voucher.is_interstate,
        "taxable_amount": voucher.taxable_amount,
        "cgst_amount": voucher.cgst_amount,
        "sgst_amount": voucher.sgst_amount,
        "igst_amount": voucher.igst_amount,
        "cess_amount": voucher.cess_amount,
        "tds_amount": voucher.tds_amount,
        "payment_mode": voucher.payment_mode,
        "bank_account_id": voucher.bank_account_id,
        "cheque_number": voucher.cheque_number,
        "cheque_date": voucher.cheque_date,
        "transaction_reference": voucher.transaction_reference,
        "status": voucher.status,
        "approval_level": voucher.approval_level,
        "rejection_reason": voucher.rejection_reason,
        "is_reversed": voucher.is_reversed,
        "reversal_voucher_id": voucher.reversal_voucher_id,
        "original_voucher_id": voucher.original_voucher_id,
        "journal_entry_id": voucher.journal_entry_id,
        "created_by": voucher.created_by,
        "created_at": voucher.created_at,
        "updated_at": voucher.updated_at,
        "submitted_by": voucher.submitted_by,
        "submitted_at": voucher.submitted_at,
        "approved_by": voucher.approved_by,
        "approved_at": voucher.approved_at,
        "posted_by": voucher.posted_by,
        "posted_at": voucher.posted_at,
        "cancelled_by": voucher.cancelled_by,
        "cancelled_at": voucher.cancelled_at,
        "cancellation_reason": voucher.cancellation_reason,
        "notes": voucher.notes,
        "attachments": voucher.attachments,
        "lines": lines,
        "allocations": allocations,
        "creator_name": _get_user_name(voucher.creator) if hasattr(voucher, 'creator') else None,
        "submitter_name": _get_user_name(voucher.submitter) if hasattr(voucher, 'submitter') else None,
        "approver_name": _get_user_name(voucher.approver) if hasattr(voucher, 'approver') else None,
    }


# ==================== Voucher Types & Metadata ====================

@router.get(
    "/types",
    response_model=VoucherTypesResponse,
    dependencies=[Depends(require_permissions("vouchers:view"))]
)
async def get_voucher_types(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get all voucher types with their metadata."""
    service = VoucherService(db, current_user.id)
    types = service.get_voucher_types_metadata()
    return VoucherTypesResponse(types=types)


@router.get(
    "/party-accounts",
    response_model=PartyAccountsResponse,
    dependencies=[Depends(require_permissions("vouchers:view"))]
)
async def get_party_accounts(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get accounts categorized for party selection dropdowns."""
    service = VoucherService(db, current_user.id)
    accounts = await service.get_party_accounts()
    return accounts


@router.get(
    "/summary",
    response_model=VoucherSummary,
    dependencies=[Depends(require_permissions("vouchers:view"))]
)
async def get_voucher_summary(
    db: DB,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    voucher_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Get summary statistics for vouchers."""
    service = VoucherService(db, current_user.id)
    summary = await service.get_voucher_summary(start_date, end_date, voucher_type)
    return summary


# ==================== CRUD Operations ====================

@router.post(
    "",
    response_model=VoucherResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("vouchers:create"))]
)
async def create_voucher(
    voucher_in: VoucherCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new voucher in DRAFT status.

    Supported voucher types:
    - CONTRA: Cash ↔ Bank transfers
    - PAYMENT: Outward payments to vendors
    - RECEIPT: Inward receipts from customers
    - RCM_PAYMENT: RCM tax payment to government
    - JOURNAL: General double-entry vouchers
    - And more...
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.create_voucher(voucher_in)
        return _build_voucher_response(voucher)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=VoucherListResponse,
    dependencies=[Depends(require_permissions("vouchers:view"))]
)
async def list_vouchers(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    voucher_type: Optional[str] = Query(None, description="Filter by voucher type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    party_type: Optional[str] = Query(None, description="Filter by party type"),
    party_id: Optional[UUID] = Query(None, description="Filter by party ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    search: Optional[str] = Query(None, description="Search in voucher number, narration, party name"),
    current_user: User = Depends(get_current_user),
):
    """List vouchers with filters and pagination."""
    service = VoucherService(db, current_user.id)
    vouchers, total = await service.list_vouchers(
        voucher_type=voucher_type,
        status=status,
        party_type=party_type,
        party_id=party_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        size=size,
    )

    pages = (total + size - 1) // size if size > 0 else 1

    return VoucherListResponse(
        items=[_build_voucher_response(v) for v in vouchers],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{voucher_id}",
    response_model=VoucherResponse,
    dependencies=[Depends(require_permissions("vouchers:view"))]
)
async def get_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get voucher by ID with full details."""
    service = VoucherService(db, current_user.id)
    voucher = await service.get_voucher(voucher_id)

    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    return _build_voucher_response(voucher)


@router.put(
    "/{voucher_id}",
    response_model=VoucherResponse,
    dependencies=[Depends(require_permissions("vouchers:edit"))]
)
async def update_voucher(
    voucher_id: UUID,
    voucher_in: VoucherUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Update a DRAFT voucher.

    Only vouchers in DRAFT status can be updated.
    Once submitted for approval, vouchers cannot be modified.
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.update_voucher(voucher_id, voucher_in)
        return _build_voucher_response(voucher)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{voucher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("vouchers:delete"))]
)
async def delete_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a DRAFT voucher.

    Only vouchers in DRAFT status can be deleted.
    Use cancel endpoint for other statuses.
    """
    service = VoucherService(db, current_user.id)
    try:
        await service.delete_voucher(voucher_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Workflow Operations ====================

@router.post(
    "/{voucher_id}/submit",
    response_model=VoucherWorkflowResponse,
    dependencies=[Depends(require_permissions("vouchers:create"))]
)
async def submit_voucher(
    voucher_id: UUID,
    request: VoucherSubmitRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Submit a DRAFT voucher for approval (Maker action).

    This moves the voucher from DRAFT to PENDING_APPROVAL status.
    The approval level is determined based on the voucher amount.
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.submit_voucher(voucher_id, request.remarks)
        return VoucherWorkflowResponse(
            id=voucher.id,
            voucher_number=voucher.voucher_number,
            voucher_type=voucher.voucher_type,
            status=voucher.status,
            total_amount=float(voucher.total_debit),
            narration=voucher.narration,
            approval_level=voucher.approval_level,
            message=f"Voucher submitted for {voucher.approval_level} approval"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{voucher_id}/approve",
    response_model=VoucherWorkflowResponse,
    dependencies=[Depends(require_permissions("vouchers:approve"))]
)
async def approve_voucher(
    voucher_id: UUID,
    request: VoucherApproveRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Approve a pending voucher (Checker action).

    The approver (checker) must be different from the maker (creator).
    If auto_post is True (default), the voucher will be automatically posted to GL.
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.approve_voucher(voucher_id, request.auto_post, request.remarks)
        message = "Voucher approved"
        if voucher.status == VoucherStatus.POSTED.value:
            message = "Voucher approved and posted to General Ledger"

        return VoucherWorkflowResponse(
            id=voucher.id,
            voucher_number=voucher.voucher_number,
            voucher_type=voucher.voucher_type,
            status=voucher.status,
            total_amount=float(voucher.total_debit),
            narration=voucher.narration,
            approval_level=voucher.approval_level,
            message=message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{voucher_id}/reject",
    response_model=VoucherWorkflowResponse,
    dependencies=[Depends(require_permissions("vouchers:approve"))]
)
async def reject_voucher(
    voucher_id: UUID,
    request: VoucherRejectRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Reject a pending voucher (Checker action).

    A rejection reason is required. The voucher will move to REJECTED status
    and can be edited and resubmitted by the maker.
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.reject_voucher(voucher_id, request.reason)
        return VoucherWorkflowResponse(
            id=voucher.id,
            voucher_number=voucher.voucher_number,
            voucher_type=voucher.voucher_type,
            status=voucher.status,
            total_amount=float(voucher.total_debit),
            narration=voucher.narration,
            approval_level=voucher.approval_level,
            message=f"Voucher rejected: {request.reason}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{voucher_id}/post",
    response_model=VoucherWorkflowResponse,
    dependencies=[Depends(require_permissions("vouchers:approve"))]
)
async def post_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Post an approved voucher to General Ledger.

    This creates journal entries and updates account balances.
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.post_voucher(voucher_id)
        return VoucherWorkflowResponse(
            id=voucher.id,
            voucher_number=voucher.voucher_number,
            voucher_type=voucher.voucher_type,
            status=voucher.status,
            total_amount=float(voucher.total_debit),
            narration=voucher.narration,
            approval_level=voucher.approval_level,
            message="Voucher posted to General Ledger"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{voucher_id}/cancel",
    response_model=VoucherWorkflowResponse,
    dependencies=[Depends(require_permissions("vouchers:delete"))]
)
async def cancel_voucher(
    voucher_id: UUID,
    request: VoucherCancelRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a DRAFT or REJECTED voucher.

    Posted vouchers cannot be cancelled - use reverse endpoint instead.
    """
    service = VoucherService(db, current_user.id)
    try:
        voucher = await service.cancel_voucher(voucher_id, request.reason)
        return VoucherWorkflowResponse(
            id=voucher.id,
            voucher_number=voucher.voucher_number,
            voucher_type=voucher.voucher_type,
            status=voucher.status,
            total_amount=float(voucher.total_debit),
            narration=voucher.narration,
            approval_level=voucher.approval_level,
            message=f"Voucher cancelled: {request.reason}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{voucher_id}/reverse",
    response_model=VoucherResponse,
    dependencies=[Depends(require_permissions("vouchers:reverse"))]
)
async def reverse_voucher(
    voucher_id: UUID,
    request: VoucherReverseRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """
    Create a reversal entry for a POSTED voucher.

    This creates a new voucher with swapped debit/credit amounts
    and links it to the original voucher.
    """
    service = VoucherService(db, current_user.id)
    try:
        reversal = await service.reverse_voucher(
            voucher_id,
            request.reversal_date,
            request.reason
        )
        return _build_voucher_response(reversal)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Pending Approvals ====================

@router.get(
    "/pending-approval",
    response_model=VoucherListResponse,
    dependencies=[Depends(require_permissions("vouchers:approve"))]
)
async def get_pending_approvals(
    db: DB,
    approval_level: Optional[str] = Query(None, description="Filter by LEVEL_1, LEVEL_2, LEVEL_3"),
    voucher_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Get vouchers pending approval."""
    service = VoucherService(db, current_user.id)
    vouchers, total = await service.list_vouchers(
        voucher_type=voucher_type,
        status=VoucherStatus.PENDING_APPROVAL.value,
        page=page,
        size=size,
    )

    # Filter by approval level if specified
    if approval_level:
        vouchers = [v for v in vouchers if v.approval_level == approval_level]
        total = len(vouchers)

    pages = (total + size - 1) // size if size > 0 else 1

    return VoucherListResponse(
        items=[_build_voucher_response(v) for v in vouchers],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
