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
from app.models.expense import ExpenseCategory, ExpenseVoucher
from app.models.accounting import JournalEntry
from app.services.accounting_service import AccountingService
from app.schemas.expense import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse,
    ExpenseVoucherCreate, ExpenseVoucherUpdate, ExpenseVoucherResponse,
    ExpenseVoucherListResponse, SubmitRequest, ApproveRequest, RejectRequest,
    PostRequest, PaymentRequest, ExpenseDashboard
)


router = APIRouter(tags=["Expenses"])


async def _load_voucher_for_response(db: DB, voucher_id: uuid.UUID) -> ExpenseVoucher:
    """Re-fetch voucher with eagerly loaded relationships for serialization."""
    result = await db.execute(
        select(ExpenseVoucher)
        .options(selectinload(ExpenseVoucher.category))
        .where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one()
    # Populate journal_entry_number if linked
    if voucher.journal_entry_id:
        je_result = await db.execute(
            select(JournalEntry.entry_number).where(JournalEntry.id == voucher.journal_entry_id)
        )
        voucher.journal_entry_number = je_result.scalar()  # type: ignore[attr-defined]
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

    # Get voucher counts for each category
    items = []
    for cat in categories:
        count_result = await db.execute(
            select(func.count())
            .where(ExpenseVoucher.expense_category_id == cat.id)
        )
        voucher_count = count_result.scalar() or 0
        items.append({
            **ExpenseCategoryResponse.model_validate(cat).model_dump(),
            "voucher_count": voucher_count,
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
             dependencies=[Depends(require_permissions("expenses:create"))])
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
            dependencies=[Depends(require_permissions("expenses:update"))])
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
    query = select(ExpenseVoucher).options(selectinload(ExpenseVoucher.category))
    
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

    # Populate journal_entry_number for vouchers with journal_entry_id
    je_ids = [v.journal_entry_id for v in vouchers if v.journal_entry_id]
    je_map: dict = {}
    if je_ids:
        je_result = await db.execute(
            select(JournalEntry.id, JournalEntry.entry_number)
            .where(JournalEntry.id.in_(je_ids))
        )
        je_map = {row[0]: row[1] for row in je_result.all()}

    for v in vouchers:
        if v.journal_entry_id and v.journal_entry_id in je_map:
            v.journal_entry_number = je_map[v.journal_entry_id]  # type: ignore[attr-defined]

    return ExpenseVoucherListResponse(
        items=vouchers,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 1
    )


@router.post("", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("expenses:create"))])
async def create_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    data: ExpenseVoucherCreate,
):
    """Create a new expense voucher (DRAFT status)."""
    voucher_number = await generate_voucher_number(db)
    
    # Calculate net amount
    net_amount = data.amount + data.gst_amount - data.tds_amount
    
    # Get financial year and period
    fy = f"FY{data.voucher_date.year}-{str(data.voucher_date.year + 1)[2:]}"
    period = data.voucher_date.strftime("%Y-%m")
    
    voucher = ExpenseVoucher(
        voucher_number=voucher_number,
        voucher_date=data.voucher_date,
        financial_year=fy,
        period=period,
        expense_category_id=data.expense_category_id,
        amount=data.amount,
        gst_amount=data.gst_amount,
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
        .options(selectinload(ExpenseVoucher.category))
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
            dependencies=[Depends(require_permissions("expenses:update"))])
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
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(voucher, field, value)
    
    # Recalculate net amount
    voucher.net_amount = voucher.amount + voucher.gst_amount - voucher.tds_amount
    
    await db.commit()
    await db.refresh(voucher)
    return voucher


@router.delete("/{voucher_id}", dependencies=[Depends(require_permissions("expenses:delete"))])
async def delete_expense_voucher(
    db: DB,
    voucher_id: uuid.UUID,
):
    """Delete a DRAFT expense voucher."""
    voucher = await db.get(ExpenseVoucher, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    if voucher.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT vouchers can be deleted")
    
    await db.delete(voucher)
    await db.commit()
    return {"message": "Voucher deleted"}


# ==================== WORKFLOW ACTIONS ====================

@router.post("/{voucher_id}/submit", response_model=ExpenseVoucherResponse,
             dependencies=[Depends(require_permissions("expenses:submit"))])
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
             dependencies=[Depends(require_permissions("expenses:approve"))])
async def approve_expense_voucher(
    db: DB,
    current_user: CurrentUser,
    voucher_id: uuid.UUID,
    data: ApproveRequest,
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
             dependencies=[Depends(require_permissions("expenses:approve"))])
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
             dependencies=[Depends(require_permissions("expenses:post"))])
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
        # Load expense category to get GL account
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
             dependencies=[Depends(require_permissions("expenses:pay"))])
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
            dependencies=[Depends(require_permissions("expenses:view"))])
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

