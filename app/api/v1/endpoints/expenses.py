"""
Expense Management API Endpoints

Handles:
- Expense Categories CRUD
- Expense Vouchers with approval workflow
- GL posting integration
"""

from typing import Optional
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from math import ceil
import uuid

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.expense import ExpenseCategory, ExpenseVoucher, ExpenseVoucherLine
from app.models.accounting import JournalEntry, ChartOfAccount, CostCenter
from app.models.user import User
from app.models.vendor import Vendor
from app.services.accounting_service import AccountingService
from app.schemas.expense import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse,
    ExpenseVoucherCreate, ExpenseVoucherUpdate, ExpenseVoucherResponse,
    ExpenseVoucherListResponse, SubmitRequest, ApproveRequest, RejectRequest,
    PostRequest, PaymentRequest, ExpenseDashboard,
    ExpenseVoucherLineResponse,
)


router = APIRouter(tags=["Expenses"])


async def _load_voucher_for_response(db: DB, voucher_id: uuid.UUID) -> ExpenseVoucher:
    """Re-fetch voucher with eagerly loaded relationships for serialization."""
    result = await db.execute(
        select(ExpenseVoucher)
        .options(
            selectinload(ExpenseVoucher.category),
            selectinload(ExpenseVoucher.lines).selectinload(ExpenseVoucherLine.category),
        )
        .where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one()
    # Populate journal_entry_number if linked
    if voucher.journal_entry_id:
        je_result = await db.execute(
            select(JournalEntry.entry_number).where(JournalEntry.id == voucher.journal_entry_id)
        )
        voucher.journal_entry_number = je_result.scalar()  # type: ignore[attr-defined]
    # Populate user names
    for field, name_field in [('created_by', 'created_by_name'), ('approved_by', 'approved_by_name')]:
        uid = getattr(voucher, field, None)
        if uid:
            u = await db.execute(select(User.first_name, User.last_name).where(User.id == uid))
            row = u.first()
            if row:
                setattr(voucher, name_field, f"{row[0]} {row[1]}" if row[1] else row[0])
    # Populate vendor name
    if voucher.vendor_id:
        v = await db.execute(select(Vendor.name).where(Vendor.id == voucher.vendor_id))
        voucher.vendor_name = v.scalar()  # type: ignore[attr-defined]
    # Populate cost center name
    if voucher.cost_center_id:
        cc = await db.execute(select(CostCenter.name).where(CostCenter.id == voucher.cost_center_id))
        voucher.cost_center_name = cc.scalar()  # type: ignore[attr-defined]
    return voucher


# ==================== EXPENSE CATEGORIES ====================

@router.get("/categories")
async def list_expense_categories(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
):
    """List all expense categories with pagination."""
    query = select(ExpenseCategory)

    # Filters
    if is_active is not None:
        query = query.where(ExpenseCategory.is_active == is_active)
    if search:
        query = query.where(
            or_(
                ExpenseCategory.code.ilike(f"%{search}%"),
                ExpenseCategory.name.ilike(f"%{search}%"),
            )
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Pagination
    query = query.order_by(ExpenseCategory.name)
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    categories = result.scalars().all()

    # Get voucher counts and GL account details for each category
    items = []
    for cat in categories:
        count_result = await db.execute(
            select(func.count())
            .where(ExpenseVoucher.expense_category_id == cat.id)
        )
        voucher_count = count_result.scalar() or 0

        # Fetch GL account name/code if linked
        gl_account_name = None
        gl_account_code = None
        if cat.gl_account_id:
            gl_result = await db.execute(
                select(ChartOfAccount.account_name, ChartOfAccount.account_code)
                .where(ChartOfAccount.id == cat.gl_account_id)
            )
            gl_row = gl_result.first()
            if gl_row:
                gl_account_name = gl_row.account_name
                gl_account_code = gl_row.account_code

        items.append({
            **ExpenseCategoryResponse.model_validate(cat).model_dump(),
            "voucher_count": voucher_count,
            "gl_account_name": gl_account_name,
            "gl_account_code": gl_account_code,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if total > 0 else 1
    }


@router.get("/categories/dropdown")
async def get_category_dropdown(
    db: DB,
):
    """Get expense categories for dropdown (active only)."""
    query = select(ExpenseCategory).where(ExpenseCategory.is_active == True).order_by(ExpenseCategory.name)
    result = await db.execute(query)
    categories = result.scalars().all()
    return [
        {
            "id": str(cat.id),
            "code": cat.code,
            "name": cat.name,
            "gl_account_id": str(cat.gl_account_id) if cat.gl_account_id else None,
            "requires_receipt": cat.requires_receipt
        }
        for cat in categories
    ]


@router.post("/categories", response_model=ExpenseCategoryResponse,
             dependencies=[Depends(require_permissions("EXPENSE_CATEGORY_MANAGE"))])
async def create_expense_category(
    db: DB,
    current_user: CurrentUser,
    data: ExpenseCategoryCreate,
):
    """Create a new expense category."""
    # Check duplicate code
    existing = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.code == data.code.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Category code '{data.code}' already exists")
    
    category = ExpenseCategory(
        **data.model_dump(),
        created_by=current_user.id
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=ExpenseCategoryResponse,
            dependencies=[Depends(require_permissions("EXPENSE_CATEGORY_MANAGE"))])
async def update_expense_category(
    db: DB,
    current_user: CurrentUser,
    category_id: uuid.UUID,
    data: ExpenseCategoryUpdate,
):
    """Update an expense category."""
    category = await db.get(ExpenseCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    
    category.updated_by = current_user.id
    await db.commit()
    await db.refresh(category)
    return category


# ==================== EXPENSE VOUCHERS ====================

async def generate_voucher_number(db: DB) -> str:
    """Generate next voucher number: EXP-YYYYMM-XXXX"""
    now = datetime.now(timezone.utc)
    prefix = f"EXP-{now.strftime('%Y%m')}-"
    
    result = await db.execute(
        select(func.max(ExpenseVoucher.voucher_number))
        .where(ExpenseVoucher.voucher_number.like(f"{prefix}%"))
    )
    last_number = result.scalar()
    
    if last_number:
        seq = int(last_number.split("-")[-1]) + 1
    else:
        seq = 1
    
    return f"{prefix}{str(seq).zfill(4)}"


@router.get("", response_model=ExpenseVoucherListResponse)
async def list_expense_vouchers(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
):
    """List expense vouchers with filters."""
    query = select(ExpenseVoucher).options(
        selectinload(ExpenseVoucher.category),
        selectinload(ExpenseVoucher.lines).selectinload(ExpenseVoucherLine.category),
    )
    
    # Filters
    if status:
        query = query.where(ExpenseVoucher.status == status.upper())
    if category_id:
        query = query.where(ExpenseVoucher.expense_category_id == category_id)
    if from_date:
        query = query.where(ExpenseVoucher.voucher_date >= from_date)
    if to_date:
        query = query.where(ExpenseVoucher.voucher_date <= to_date)
    if search:
        query = query.where(
            or_(
                ExpenseVoucher.voucher_number.ilike(f"%{search}%"),
                ExpenseVoucher.narration.ilike(f"%{search}%"),
                ExpenseVoucher.purpose.ilike(f"%{search}%"),
            )
        )
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Pagination
    query = query.order_by(ExpenseVoucher.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    vouchers = result.scalars().all()

    # Batch-resolve related names for all vouchers
    je_ids = [v.journal_entry_id for v in vouchers if v.journal_entry_id]
    user_ids = set()
    vendor_ids = set()
    cc_ids = set()
    for v in vouchers:
        if v.created_by:
            user_ids.add(v.created_by)
        if v.approved_by:
            user_ids.add(v.approved_by)
        if v.vendor_id:
            vendor_ids.add(v.vendor_id)
        if v.cost_center_id:
            cc_ids.add(v.cost_center_id)

    # Resolve JE numbers
    je_map: dict = {}
    if je_ids:
        je_result = await db.execute(
            select(JournalEntry.id, JournalEntry.entry_number)
            .where(JournalEntry.id.in_(je_ids))
        )
        je_map = {row[0]: row[1] for row in je_result.all()}

    # Resolve user names
    user_map: dict = {}
    if user_ids:
        user_result = await db.execute(
            select(User.id, User.first_name, User.last_name)
            .where(User.id.in_(list(user_ids)))
        )
        for row in user_result.all():
            name = f"{row[1]} {row[2]}" if row[2] else row[1]
            user_map[row[0]] = name

    # Resolve vendor names
    vendor_map: dict = {}
    if vendor_ids:
        vendor_result = await db.execute(
            select(Vendor.id, Vendor.name)
            .where(Vendor.id.in_(list(vendor_ids)))
        )
        vendor_map = {row[0]: row[1] for row in vendor_result.all()}

    # Resolve cost center names
    cc_map: dict = {}
    if cc_ids:
        cc_result = await db.execute(
            select(CostCenter.id, CostCenter.name)
            .where(CostCenter.id.in_(list(cc_ids)))
        )
        cc_map = {row[0]: row[1] for row in cc_result.all()}

    # Populate flat fields on each voucher
    for v in vouchers:
        if v.journal_entry_id and v.journal_entry_id in je_map:
            v.journal_entry_number = je_map[v.journal_entry_id]  # type: ignore[attr-defined]
        if v.created_by and v.created_by in user_map:
            v.created_by_name = user_map[v.created_by]  # type: ignore[attr-defined]
        if v.approved_by and v.approved_by in user_map:
            v.approved_by_name = user_map[v.approved_by]  # type: ignore[attr-defined]
        if v.vendor_id and v.vendor_id in vendor_map:
            v.vendor_name = vendor_map[v.vendor_id]  # type: ignore[attr-defined]
        if v.cost_center_id and v.cost_center_id in cc_map:
            v.cost_center_name = cc_map[v.cost_center_id]  # type: ignore[attr-defined]

    return ExpenseVoucherListResponse(
        items=vouchers,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1
    )


@router.post("", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("EXPENSE_CREATE"))])
async def create_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    data: ExpenseVoucherCreate,
):
    """Create a new expense voucher (DRAFT status)."""
    voucher_number = await generate_voucher_number(db)

    # If multi-line, compute header totals from lines
    has_lines = data.lines and len(data.lines) > 0
    if has_lines:
        total_amount = sum(line.amount for line in data.lines)
        total_gst = sum(line.gst_amount for line in data.lines)
    else:
        total_amount = data.amount
        total_gst = data.gst_amount

    # Calculate net amount
    net_amount = total_amount + total_gst - data.tds_amount

    # Get financial year and period
    fy = f"FY{data.voucher_date.year}-{str(data.voucher_date.year + 1)[2:]}"
    period = data.voucher_date.strftime("%Y-%m")

    voucher = ExpenseVoucher(
        voucher_number=voucher_number,
        voucher_date=data.voucher_date,
        financial_year=fy,
        period=period,
        expense_category_id=data.expense_category_id if not has_lines else None,
        amount=total_amount,
        gst_amount=total_gst,
        tds_amount=data.tds_amount,
        net_amount=net_amount,
        vendor_id=data.vendor_id,
        cost_center_id=data.cost_center_id,
        narration=data.narration,
        purpose=data.purpose,
        payment_mode=data.payment_mode,
        bank_account_id=data.bank_account_id,
        status="DRAFT",
        created_by=current_user.id,
    )

    db.add(voucher)
    await db.flush()  # Get voucher.id before adding lines

    # Create line items if multi-line
    if has_lines:
        for idx, line_data in enumerate(data.lines, start=1):
            line = ExpenseVoucherLine(
                voucher_id=voucher.id,
                line_number=idx,
                expense_category_id=line_data.expense_category_id,
                description=line_data.description,
                amount=line_data.amount,
                gst_rate=line_data.gst_rate,
                gst_amount=line_data.gst_amount,
                cost_center_id=line_data.cost_center_id,
            )
            db.add(line)

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


@router.get("/{voucher_id}", response_model=ExpenseVoucherResponse)
async def get_expense_voucher(
    db: DB,
    voucher_id: uuid.UUID,
):
    """Get expense voucher details."""
    result = await db.execute(
        select(ExpenseVoucher)
        .options(
            selectinload(ExpenseVoucher.category),
            selectinload(ExpenseVoucher.lines).selectinload(ExpenseVoucherLine.category),
        )
        .where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    # Populate journal_entry_number
    if voucher.journal_entry_id:
        je_result = await db.execute(
            select(JournalEntry.entry_number)
            .where(JournalEntry.id == voucher.journal_entry_id)
        )
        entry_number = je_result.scalar_one_or_none()
        if entry_number:
            voucher.journal_entry_number = entry_number  # type: ignore[attr-defined]

    return voucher


@router.put("/{voucher_id}", response_model=ExpenseVoucherResponse,
            dependencies=[Depends(require_permissions("EXPENSE_EDIT"))])
async def update_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
    data: ExpenseVoucherUpdate,
):
    """Update a DRAFT expense voucher."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    if voucher.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT vouchers can be updated")

    # Apply header field updates (exclude lines)
    for field, value in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        setattr(voucher, field, value)

    # Handle lines update
    has_lines = data.lines is not None and len(data.lines) > 0
    if has_lines:
        # Delete existing lines
        existing_lines = await db.execute(
            select(ExpenseVoucherLine).where(ExpenseVoucherLine.voucher_id == voucher_id)
        )
        for old_line in existing_lines.scalars().all():
            await db.delete(old_line)

        # Insert new lines
        total_amount = Decimal("0")
        total_gst = Decimal("0")
        for idx, line_data in enumerate(data.lines, start=1):
            line = ExpenseVoucherLine(
                voucher_id=voucher_id,
                line_number=idx,
                expense_category_id=line_data.expense_category_id,
                description=line_data.description,
                amount=line_data.amount,
                gst_rate=line_data.gst_rate,
                gst_amount=line_data.gst_amount,
                cost_center_id=line_data.cost_center_id,
            )
            db.add(line)
            total_amount += line_data.amount
            total_gst += line_data.gst_amount

        voucher.amount = total_amount
        voucher.gst_amount = total_gst
        voucher.expense_category_id = None  # Multi-line: no header category

    # Recalculate net amount
    voucher.net_amount = voucher.amount + voucher.gst_amount - voucher.tds_amount

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


@router.delete("/{voucher_id}", dependencies=[Depends(require_permissions("EXPENSE_DELETE"))])
async def delete_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
):
    """Delete an expense voucher. POSTED vouchers require reversal of JV first."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    if voucher.status == "PAID":
        raise HTTPException(status_code=400, detail="PAID vouchers cannot be deleted")

    # If voucher has a journal entry, reverse/delete it
    if voucher.journal_entry_id:
        from app.models.accounting import JournalEntry, JournalEntryLine, GeneralLedger
        # Delete GL entries
        gl_result = await db.execute(
            select(GeneralLedger).where(GeneralLedger.journal_entry_id == voucher.journal_entry_id)
        )
        for gl in gl_result.scalars().all():
            await db.delete(gl)
        # Delete JE lines
        jel_result = await db.execute(
            select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == voucher.journal_entry_id)
        )
        for jel in jel_result.scalars().all():
            await db.delete(jel)
        # Delete journal entry
        je = await db.get(JournalEntry, voucher.journal_entry_id)
        if je:
            await db.delete(je)

    await db.delete(voucher)
    await db.commit()
    return {"message": "Voucher and associated journal entry deleted"}


# ==================== WORKFLOW ACTIONS ====================

@router.post("/{voucher_id}/submit", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("EXPENSE_CREATE"))])
async def submit_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
):
    """Submit voucher for approval."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT vouchers can be submitted")
    
    voucher.status = "PENDING_APPROVAL"
    voucher.submitted_by = current_user.id
    voucher.submitted_at = datetime.now(timezone.utc)

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


@router.post("/{voucher_id}/approve", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("EXPENSE_APPROVE"))])
async def approve_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
    data: ApproveRequest = ApproveRequest(),
):
    """Approve expense voucher (maker-checker enforced)."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="Voucher is not pending approval")
    
    # Maker-checker: approver cannot be the creator
    if voucher.created_by == current_user.id:
        raise HTTPException(status_code=400, detail="Creator cannot approve their own voucher")
    
    # Determine approval level based on amount
    if voucher.net_amount <= 50000:
        approval_level = "L1"
    elif voucher.net_amount <= 500000:
        approval_level = "L2"
    else:
        approval_level = "L3"
    
    voucher.status = "APPROVED"
    voucher.approved_by = current_user.id
    voucher.approved_at = datetime.now(timezone.utc)
    voucher.approval_level = approval_level

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


@router.post("/{voucher_id}/reject", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("EXPENSE_APPROVE"))])
async def reject_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
    data: RejectRequest,
):
    """Reject expense voucher."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="Voucher is not pending approval")
    
    voucher.status = "REJECTED"
    voucher.rejected_by = current_user.id
    voucher.rejected_at = datetime.now(timezone.utc)
    voucher.rejection_reason = data.reason

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


@router.post("/{voucher_id}/post", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("EXPENSE_POST"))])
async def post_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
):
    """Post approved voucher to GL."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status != "APPROVED":
        raise HTTPException(status_code=400, detail="Only APPROVED vouchers can be posted")
    
    # Create journal entry
    # DR: Expense Account (from category)
    # DR: GST Input (if applicable)
    # CR: TDS Payable (if applicable)
    # CR: Accounts Payable / Cash / Bank
    try:
        # Load lines for multi-line posting
        lines_result = await db.execute(
            select(ExpenseVoucherLine)
            .where(ExpenseVoucherLine.voucher_id == voucher.id)
            .order_by(ExpenseVoucherLine.line_number)
        )
        voucher_lines = lines_result.scalars().all()

        if voucher_lines:
            # Multi-line: build expense_lines list for accounting service
            expense_lines = []
            for vl in voucher_lines:
                cat = await db.get(ExpenseCategory, vl.expense_category_id) if vl.expense_category_id else None
                expense_lines.append({
                    "gl_account_id": cat.gl_account_id if cat else None,
                    "amount": vl.amount,
                    "gst_amount": vl.gst_amount,
                    "description": vl.description or "",
                })
            journal_entry = await AccountingService(db, created_by=current_user.id).post_expense_voucher(
                voucher_id=voucher.id,
                voucher_number=voucher.voucher_number,
                expense_account_id=None,
                amount=voucher.amount,
                gst_amount=voucher.gst_amount,
                tds_amount=voucher.tds_amount,
                net_amount=voucher.net_amount,
                payment_mode=voucher.payment_mode,
                bank_account_id=voucher.bank_account_id,
                narration=voucher.narration or f"Expense {voucher.voucher_number}",
                cost_center_id=voucher.cost_center_id,
                expense_lines=expense_lines,
            )
        else:
            # Single-line: existing behavior
            category = await db.get(ExpenseCategory, voucher.expense_category_id) if voucher.expense_category_id else None
            gl_account_id = category.gl_account_id if category else None
            journal_entry = await AccountingService(db, created_by=current_user.id).post_expense_voucher(
                voucher_id=voucher.id,
                voucher_number=voucher.voucher_number,
                expense_account_id=gl_account_id,
                amount=voucher.amount,
                gst_amount=voucher.gst_amount,
                tds_amount=voucher.tds_amount,
                net_amount=voucher.net_amount,
                payment_mode=voucher.payment_mode,
                bank_account_id=voucher.bank_account_id,
                narration=voucher.narration or f"Expense {voucher.voucher_number}",
                cost_center_id=voucher.cost_center_id,
            )
        voucher.journal_entry_id = journal_entry.id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journal entry: {str(e)}"
        )

    voucher.status = "POSTED"
    voucher.posted_by = current_user.id
    voucher.posted_at = datetime.now(timezone.utc)

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


@router.post("/{voucher_id}/pay", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("EXPENSE_POST"))])
async def mark_expense_paid(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
    data: PaymentRequest,
):
    """Mark expense as paid."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status not in ["APPROVED", "POSTED"]:
        raise HTTPException(status_code=400, detail="Voucher must be approved or posted")
    
    voucher.status = "PAID"
    voucher.paid_at = data.paid_at or datetime.now(timezone.utc)
    voucher.payment_reference = data.payment_reference

    await db.commit()
    return await _load_voucher_for_response(db, voucher.id)


# ==================== DASHBOARD ====================

@router.get("/dashboard/stats", response_model=ExpenseDashboard,
            dependencies=[Depends(require_permissions("EXPENSE_VIEW"))])
async def get_expense_dashboard(
    db: DB,
):
    """Get expense dashboard summary."""
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total count
    result = await db.execute(select(func.count()).select_from(ExpenseVoucher))
    total_vouchers = result.scalar() or 0

    # Status counts (individual queries for simplicity)
    async def get_status_count(status: str) -> int:
        result = await db.execute(
            select(func.count()).where(ExpenseVoucher.status == status)
        )
        return result.scalar() or 0

    draft_count = await get_status_count("DRAFT")
    pending_approval_count = await get_status_count("PENDING_APPROVAL")
    approved_count = await get_status_count("APPROVED")
    posted_count = await get_status_count("POSTED")
    paid_count = await get_status_count("PAID")
    rejected_count = await get_status_count("REJECTED")

    # This month total
    result = await db.execute(
        select(func.coalesce(func.sum(ExpenseVoucher.net_amount), 0))
        .where(and_(
            ExpenseVoucher.voucher_date >= first_of_month.date(),
            ExpenseVoucher.status.in_(["APPROVED", "POSTED", "PAID"])
        ))
    )
    total_this_month = result.scalar() or Decimal("0")

    # This year total
    result = await db.execute(
        select(func.coalesce(func.sum(ExpenseVoucher.net_amount), 0))
        .where(and_(
            ExpenseVoucher.voucher_date >= first_of_year.date(),
            ExpenseVoucher.status.in_(["APPROVED", "POSTED", "PAID"])
        ))
    )
    total_this_year = result.scalar() or Decimal("0")

    # Pending approval amount
    result = await db.execute(
        select(func.coalesce(func.sum(ExpenseVoucher.net_amount), 0))
        .where(ExpenseVoucher.status == "PENDING_APPROVAL")
    )
    pending_amount = result.scalar() or Decimal("0")

    # Category-wise spending this year
    result = await db.execute(
        select(
            ExpenseCategory.name,
            func.coalesce(func.sum(ExpenseVoucher.net_amount), 0).label("amount")
        )
        .join(ExpenseVoucher, ExpenseVoucher.expense_category_id == ExpenseCategory.id)
        .where(and_(
            ExpenseVoucher.voucher_date >= first_of_year.date(),
            ExpenseVoucher.status.in_(["APPROVED", "POSTED", "PAID"])
        ))
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(ExpenseVoucher.net_amount).desc())
        .limit(10)
    )
    category_wise_spending = [{"category": row[0], "amount": float(row[1])} for row in result.all()]

    # Monthly trend (last 6 months)
    monthly_trend = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        result = await db.execute(
            select(func.coalesce(func.sum(ExpenseVoucher.net_amount), 0))
            .where(and_(
                ExpenseVoucher.voucher_date >= month_start.date(),
                ExpenseVoucher.voucher_date < month_end.date(),
                ExpenseVoucher.status.in_(["APPROVED", "POSTED", "PAID"])
            ))
        )
        amount = result.scalar() or Decimal("0")
        monthly_trend.append({
            "month": month_start.strftime("%b %Y"),
            "amount": float(amount)
        })

    # Recent vouchers
    result = await db.execute(
        select(ExpenseVoucher)
        .options(selectinload(ExpenseVoucher.category))
        .order_by(ExpenseVoucher.created_at.desc())
        .limit(5)
    )
    recent = result.scalars().all()

    return ExpenseDashboard(
        total_vouchers=total_vouchers,
        draft_count=draft_count,
        pending_approval_count=pending_approval_count,
        approved_count=approved_count,
        posted_count=posted_count,
        paid_count=paid_count,
        rejected_count=rejected_count,
        total_amount_this_month=total_this_month,
        total_amount_this_year=total_this_year,
        pending_approval_amount=pending_amount,
        category_wise_spending=category_wise_spending,
        cost_center_wise_spending=[],  # TODO: Implement when cost centers are linked
        monthly_trend=monthly_trend,
        recent_vouchers=recent
    )

