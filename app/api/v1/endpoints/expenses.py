"""
Expense Management API Endpoints

Handles:
- Expense Categories CRUD
- Expense Vouchers with approval workflow
- GL posting integration
"""

from typing import Optional
from datetime import datetime, timezone, date
from decimal import Decimal
from math import ceil
import uuid

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.expense import ExpenseCategory, ExpenseVoucher
from app.schemas.expense import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse,
    ExpenseVoucherCreate, ExpenseVoucherUpdate, ExpenseVoucherResponse,
    ExpenseVoucherListResponse, SubmitRequest, ApproveRequest, RejectRequest,
    PostRequest, PaymentRequest, ExpenseDashboard
)


router = APIRouter(tags=["Expenses"])


# ==================== EXPENSE CATEGORIES ====================

@router.get("/categories", response_model=list[ExpenseCategoryResponse])
async def list_expense_categories(
    db: DB,
    is_active: Optional[bool] = Query(None),
):
    """List all expense categories."""
    query = select(ExpenseCategory)
    if is_active is not None:
        query = query.where(ExpenseCategory.is_active == is_active)
    query = query.order_by(ExpenseCategory.name)
    
    result = await db.execute(query)
    return result.scalars().all()


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
    await db.refresh(voucher)
    return voucher


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
    await db.refresh(voucher)
    return voucher


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
    await db.refresh(voucher)
    return voucher


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
    await db.refresh(voucher)
    return voucher


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
    
    # TODO: Create journal entry
    # DR: Expense Account (from category)
    # DR: GST Input (if applicable)
    # CR: Accounts Payable / Cash / Bank
    
    voucher.status = "POSTED"
    voucher.posted_by = current_user.id
    voucher.posted_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(voucher)
    return voucher


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
    await db.refresh(voucher)
    return voucher


# ==================== DASHBOARD ====================

@router.get("/dashboard/summary", response_model=ExpenseDashboard,
            dependencies=[Depends(require_permissions("expenses:view"))])
async def get_expense_dashboard(
    db: DB,
):
    """Get expense dashboard summary."""
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
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
    
    # Pending approval
    result = await db.execute(
        select(func.count(), func.coalesce(func.sum(ExpenseVoucher.net_amount), 0))
        .where(ExpenseVoucher.status == "PENDING_APPROVAL")
    )
    pending = result.one()
    pending_count = pending[0] or 0
    pending_amount = pending[1] or Decimal("0")
    
    # Category-wise summary
    result = await db.execute(
        select(
            ExpenseCategory.name,
            func.coalesce(func.sum(ExpenseVoucher.net_amount), 0).label("total")
        )
        .join(ExpenseVoucher, ExpenseVoucher.expense_category_id == ExpenseCategory.id)
        .where(and_(
            ExpenseVoucher.voucher_date >= first_of_month.date(),
            ExpenseVoucher.status.in_(["APPROVED", "POSTED", "PAID"])
        ))
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(ExpenseVoucher.net_amount).desc())
    )
    category_summary = [{"category": row[0], "total": row[1]} for row in result.all()]
    
    # Recent vouchers
    result = await db.execute(
        select(ExpenseVoucher)
        .options(selectinload(ExpenseVoucher.category))
        .order_by(ExpenseVoucher.created_at.desc())
        .limit(5)
    )
    recent = result.scalars().all()
    
    return ExpenseDashboard(
        total_expenses_this_month=total_this_month,
        total_expenses_this_year=total_this_year,
        pending_approval_count=pending_count,
        pending_approval_amount=pending_amount,
        category_wise_summary=category_summary,
        recent_vouchers=recent
    )
