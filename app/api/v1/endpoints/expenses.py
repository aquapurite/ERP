"""API endpoints for Expense Voucher module."""
from datetime import date, datetime, timezone
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense import ExpenseCategory, ExpenseVoucher, ExpenseVoucherStatus, PaymentMode
from app.models.accounting import ChartOfAccount, CostCenter
from app.models.user import User
from app.schemas.expense import (
    # Category
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse, ExpenseCategoryListResponse,
    ExpenseCategoryDropdown,
    # Voucher
    ExpenseVoucherCreate, ExpenseVoucherUpdate, ExpenseVoucherResponse, ExpenseVoucherDetailResponse,
    ExpenseVoucherListResponse,
    # Workflow
    ExpenseSubmitRequest, ExpenseApprovalRequest, ExpenseRejectionRequest,
    ExpensePostRequest, ExpensePaymentRequest, ExpenseAttachmentRequest,
    # Dashboard
    ExpenseDashboard,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions

router = APIRouter()


# ==================== Helper Functions ====================

async def generate_voucher_number(db: AsyncSession) -> str:
    """Generate unique expense voucher number."""
    today = date.today()
    prefix = f"EXP-{today.strftime('%Y%m')}"

    result = await db.execute(
        select(func.count(ExpenseVoucher.id))
        .where(ExpenseVoucher.voucher_number.like(f"{prefix}%"))
    )
    count = result.scalar() or 0

    return f"{prefix}-{(count + 1):04d}"


def get_financial_year(dt: date) -> str:
    """Get financial year string for a date."""
    if dt.month >= 4:  # April onwards
        return f"{dt.year}-{str(dt.year + 1)[2:]}"
    else:
        return f"{dt.year - 1}-{str(dt.year)[2:]}"


def get_period(dt: date) -> str:
    """Get period string for a date."""
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    return f"{months[dt.month - 1]}-{dt.year}"


def get_approval_level(amount: Decimal) -> str:
    """Determine approval level based on amount."""
    if amount <= Decimal("50000"):
        return "LEVEL_1"
    elif amount <= Decimal("500000"):
        return "LEVEL_2"
    else:
        return "LEVEL_3"


# ==================== Expense Categories ====================

@router.get("/categories", response_model=ExpenseCategoryListResponse, dependencies=[Depends(require_permissions("expenses:view"))])
async def list_expense_categories(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
):
    """List expense categories."""
    query = select(ExpenseCategory).options(
        selectinload(ExpenseCategory.gl_account)
    )

    if is_active is not None:
        query = query.where(ExpenseCategory.is_active == is_active)
    if search:
        query = query.where(
            (ExpenseCategory.code.ilike(f"%{search}%")) |
            (ExpenseCategory.name.ilike(f"%{search}%"))
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(ExpenseCategory.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    items = []
    for cat in categories:
        # Get voucher count
        voucher_count_result = await db.execute(
            select(func.count(ExpenseVoucher.id))
            .where(ExpenseVoucher.expense_category_id == cat.id)
        )
        voucher_count = voucher_count_result.scalar() or 0

        items.append(ExpenseCategoryResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            gl_account_id=cat.gl_account_id,
            gl_account_name=cat.gl_account.account_name if cat.gl_account else None,
            gl_account_code=cat.gl_account.account_code if cat.gl_account else None,
            requires_receipt=cat.requires_receipt,
            max_amount_without_approval=cat.max_amount_without_approval,
            is_active=cat.is_active,
            voucher_count=voucher_count,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        ))

    pages = (total + size - 1) // size
    return ExpenseCategoryListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get("/categories/dropdown", response_model=List[ExpenseCategoryDropdown], dependencies=[Depends(require_permissions("expenses:view"))])
async def get_expense_categories_dropdown(
    db: DB,
    current_user: CurrentUser,
):
    """Get expense categories for dropdown."""
    result = await db.execute(
        select(ExpenseCategory)
        .where(ExpenseCategory.is_active == True)
        .order_by(ExpenseCategory.name)
    )
    categories = result.scalars().all()

    return [
        ExpenseCategoryDropdown(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            gl_account_id=cat.gl_account_id,
            requires_receipt=cat.requires_receipt,
        )
        for cat in categories
    ]


@router.post("/categories", response_model=ExpenseCategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("expenses:create"))])
async def create_expense_category(
    category_in: ExpenseCategoryCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create expense category."""
    # Check code uniqueness
    existing = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.code == category_in.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category code already exists"
        )

    # Verify GL account if provided
    gl_account = None
    if category_in.gl_account_id:
        gl_result = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == category_in.gl_account_id)
        )
        gl_account = gl_result.scalar_one_or_none()
        if not gl_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GL Account not found"
            )

    category = ExpenseCategory(
        code=category_in.code,
        name=category_in.name,
        description=category_in.description,
        gl_account_id=category_in.gl_account_id,
        requires_receipt=category_in.requires_receipt,
        max_amount_without_approval=category_in.max_amount_without_approval,
        is_active=True,
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return ExpenseCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        gl_account_id=category.gl_account_id,
        gl_account_name=gl_account.account_name if gl_account else None,
        gl_account_code=gl_account.account_code if gl_account else None,
        requires_receipt=category.requires_receipt,
        max_amount_without_approval=category.max_amount_without_approval,
        is_active=category.is_active,
        voucher_count=0,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("/categories/{category_id}", response_model=ExpenseCategoryResponse, dependencies=[Depends(require_permissions("expenses:view"))])
async def get_expense_category(
    category_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get expense category by ID."""
    result = await db.execute(
        select(ExpenseCategory)
        .options(selectinload(ExpenseCategory.gl_account))
        .where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Get voucher count
    voucher_count_result = await db.execute(
        select(func.count(ExpenseVoucher.id))
        .where(ExpenseVoucher.expense_category_id == category.id)
    )
    voucher_count = voucher_count_result.scalar() or 0

    return ExpenseCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        gl_account_id=category.gl_account_id,
        gl_account_name=category.gl_account.account_name if category.gl_account else None,
        gl_account_code=category.gl_account.account_code if category.gl_account else None,
        requires_receipt=category.requires_receipt,
        max_amount_without_approval=category.max_amount_without_approval,
        is_active=category.is_active,
        voucher_count=voucher_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put("/categories/{category_id}", response_model=ExpenseCategoryResponse, dependencies=[Depends(require_permissions("expenses:update"))])
async def update_expense_category(
    category_id: UUID,
    category_in: ExpenseCategoryUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update expense category."""
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    update_data = category_in.model_dump(exclude_unset=True)

    # Verify GL account if updated
    if 'gl_account_id' in update_data and update_data['gl_account_id']:
        gl_result = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == update_data['gl_account_id'])
        )
        if not gl_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GL Account not found"
            )

    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)

    # Reload with GL account
    result = await db.execute(
        select(ExpenseCategory)
        .options(selectinload(ExpenseCategory.gl_account))
        .where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one()

    # Get voucher count
    voucher_count_result = await db.execute(
        select(func.count(ExpenseVoucher.id))
        .where(ExpenseVoucher.expense_category_id == category.id)
    )
    voucher_count = voucher_count_result.scalar() or 0

    return ExpenseCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        gl_account_id=category.gl_account_id,
        gl_account_name=category.gl_account.account_name if category.gl_account else None,
        gl_account_code=category.gl_account.account_code if category.gl_account else None,
        requires_receipt=category.requires_receipt,
        max_amount_without_approval=category.max_amount_without_approval,
        is_active=category.is_active,
        voucher_count=voucher_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


# ==================== Expense Vouchers ====================

@router.get("", response_model=ExpenseVoucherListResponse, dependencies=[Depends(require_permissions("expenses:view"))])
async def list_expense_vouchers(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status_filter: Optional[ExpenseVoucherStatus] = Query(None, alias="status"),
    category_id: Optional[UUID] = None,
    cost_center_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
):
    """List expense vouchers with filters."""
    query = select(ExpenseVoucher).options(
        selectinload(ExpenseVoucher.category),
        selectinload(ExpenseVoucher.cost_center),
        selectinload(ExpenseVoucher.creator),
        selectinload(ExpenseVoucher.approver),
    )

    if status_filter:
        query = query.where(ExpenseVoucher.status == status_filter)
    if category_id:
        query = query.where(ExpenseVoucher.expense_category_id == category_id)
    if cost_center_id:
        query = query.where(ExpenseVoucher.cost_center_id == cost_center_id)
    if date_from:
        query = query.where(ExpenseVoucher.voucher_date >= date_from)
    if date_to:
        query = query.where(ExpenseVoucher.voucher_date <= date_to)
    if search:
        query = query.where(
            (ExpenseVoucher.voucher_number.ilike(f"%{search}%")) |
            (ExpenseVoucher.narration.ilike(f"%{search}%"))
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(ExpenseVoucher.voucher_date.desc(), ExpenseVoucher.voucher_number.desc())

    result = await db.execute(query)
    vouchers = result.scalars().all()

    items = [
        ExpenseVoucherResponse(
            id=v.id,
            voucher_number=v.voucher_number,
            voucher_date=v.voucher_date,
            financial_year=v.financial_year,
            period=v.period,
            expense_category_id=v.expense_category_id,
            category_code=v.category.code if v.category else None,
            category_name=v.category.name if v.category else None,
            amount=v.amount,
            gst_amount=v.gst_amount,
            tds_amount=v.tds_amount,
            net_amount=v.net_amount,
            cost_center_name=v.cost_center.name if v.cost_center else None,
            narration=v.narration,
            payment_mode=v.payment_mode,
            status=v.status,
            created_by_name=v.creator.full_name if v.creator else None,
            approved_by_name=v.approver.full_name if v.approver else None,
            approved_at=v.approved_at,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in vouchers
    ]

    pages = (total + size - 1) // size
    return ExpenseVoucherListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("", response_model=ExpenseVoucherDetailResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permissions("expenses:create"))])
async def create_expense_voucher(
    voucher_in: ExpenseVoucherCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create expense voucher (DRAFT status)."""
    # Verify category exists
    cat_result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == voucher_in.expense_category_id)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found"
        )

    # Verify cost center if provided
    cost_center = None
    if voucher_in.cost_center_id:
        cc_result = await db.execute(
            select(CostCenter).where(CostCenter.id == voucher_in.cost_center_id)
        )
        cost_center = cc_result.scalar_one_or_none()
        if not cost_center:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cost center not found"
            )

    # Generate voucher number
    voucher_number = await generate_voucher_number(db)

    # Calculate net amount
    net_amount = voucher_in.amount + voucher_in.gst_amount - voucher_in.tds_amount

    voucher = ExpenseVoucher(
        voucher_number=voucher_number,
        voucher_date=voucher_in.voucher_date,
        financial_year=get_financial_year(voucher_in.voucher_date),
        period=get_period(voucher_in.voucher_date),
        expense_category_id=voucher_in.expense_category_id,
        amount=voucher_in.amount,
        gst_amount=voucher_in.gst_amount,
        tds_amount=voucher_in.tds_amount,
        net_amount=net_amount,
        vendor_id=voucher_in.vendor_id,
        vendor_invoice_no=voucher_in.vendor_invoice_no,
        vendor_invoice_date=voucher_in.vendor_invoice_date,
        cost_center_id=voucher_in.cost_center_id,
        narration=voucher_in.narration,
        purpose=voucher_in.purpose,
        payment_mode=voucher_in.payment_mode,
        bank_account_id=voucher_in.bank_account_id,
        notes=voucher_in.notes,
        status=ExpenseVoucherStatus.DRAFT,
        created_by=current_user.id,
    )

    db.add(voucher)
    await db.commit()
    await db.refresh(voucher)

    return ExpenseVoucherDetailResponse(
        id=voucher.id,
        voucher_number=voucher.voucher_number,
        voucher_date=voucher.voucher_date,
        financial_year=voucher.financial_year,
        period=voucher.period,
        expense_category_id=voucher.expense_category_id,
        category_code=category.code,
        category_name=category.name,
        amount=voucher.amount,
        gst_amount=voucher.gst_amount,
        tds_amount=voucher.tds_amount,
        net_amount=voucher.net_amount,
        cost_center_id=voucher.cost_center_id,
        cost_center_name=cost_center.name if cost_center else None,
        narration=voucher.narration,
        purpose=voucher.purpose,
        payment_mode=voucher.payment_mode,
        bank_account_id=voucher.bank_account_id,
        notes=voucher.notes,
        status=voucher.status,
        created_by_name=current_user.full_name,
        created_at=voucher.created_at,
        updated_at=voucher.updated_at,
    )


@router.get("/{voucher_id}", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:view"))])
async def get_expense_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Get expense voucher by ID."""
    result = await db.execute(
        select(ExpenseVoucher)
        .options(
            selectinload(ExpenseVoucher.category),
            selectinload(ExpenseVoucher.cost_center),
            selectinload(ExpenseVoucher.creator),
            selectinload(ExpenseVoucher.submitter),
            selectinload(ExpenseVoucher.approver),
            selectinload(ExpenseVoucher.poster),
        )
        .where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    # Get rejected by name if rejected
    rejected_by_name = None
    if voucher.rejected_by:
        rejected_result = await db.execute(
            select(User).where(User.id == voucher.rejected_by)
        )
        rejected_user = rejected_result.scalar_one_or_none()
        rejected_by_name = rejected_user.full_name if rejected_user else None

    # Get paid by name if paid
    paid_by_name = None
    if voucher.paid_by:
        paid_result = await db.execute(
            select(User).where(User.id == voucher.paid_by)
        )
        paid_user = paid_result.scalar_one_or_none()
        paid_by_name = paid_user.full_name if paid_user else None

    # Get bank account name if set
    bank_account_name = None
    if voucher.bank_account_id:
        bank_result = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == voucher.bank_account_id)
        )
        bank_account = bank_result.scalar_one_or_none()
        bank_account_name = bank_account.account_name if bank_account else None

    return ExpenseVoucherDetailResponse(
        id=voucher.id,
        voucher_number=voucher.voucher_number,
        voucher_date=voucher.voucher_date,
        financial_year=voucher.financial_year,
        period=voucher.period,
        expense_category_id=voucher.expense_category_id,
        category_code=voucher.category.code if voucher.category else None,
        category_name=voucher.category.name if voucher.category else None,
        amount=voucher.amount,
        gst_amount=voucher.gst_amount,
        tds_amount=voucher.tds_amount,
        net_amount=voucher.net_amount,
        vendor_id=voucher.vendor_id,
        vendor_invoice_no=voucher.vendor_invoice_no,
        vendor_invoice_date=voucher.vendor_invoice_date,
        cost_center_id=voucher.cost_center_id,
        cost_center_name=voucher.cost_center.name if voucher.cost_center else None,
        narration=voucher.narration,
        purpose=voucher.purpose,
        payment_mode=voucher.payment_mode,
        bank_account_id=voucher.bank_account_id,
        bank_account_name=bank_account_name,
        notes=voucher.notes,
        status=voucher.status,
        approval_level=voucher.approval_level,
        rejection_reason=voucher.rejection_reason,
        rejected_by_name=rejected_by_name,
        rejected_at=voucher.rejected_at,
        posted_by_name=voucher.poster.full_name if voucher.poster else None,
        posted_at=voucher.posted_at,
        journal_entry_id=voucher.journal_entry_id,
        paid_at=voucher.paid_at,
        payment_reference=voucher.payment_reference,
        paid_by_name=paid_by_name,
        attachments=voucher.attachments,
        created_by_name=voucher.creator.full_name if voucher.creator else None,
        submitted_at=voucher.submitted_at,
        submitted_by_name=voucher.submitter.full_name if voucher.submitter else None,
        approved_by_name=voucher.approver.full_name if voucher.approver else None,
        approved_at=voucher.approved_at,
        created_at=voucher.created_at,
        updated_at=voucher.updated_at,
    )


@router.put("/{voucher_id}", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:update"))])
async def update_expense_voucher(
    voucher_id: UUID,
    voucher_in: ExpenseVoucherUpdate,
    db: DB,
    current_user: CurrentUser,
):
    """Update expense voucher (only DRAFT status)."""
    result = await db.execute(
        select(ExpenseVoucher).where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update voucher with status {voucher.status}"
        )

    update_data = voucher_in.model_dump(exclude_unset=True)

    # Recalculate net amount if amounts changed
    amount = update_data.get('amount', voucher.amount)
    gst_amount = update_data.get('gst_amount', voucher.gst_amount)
    tds_amount = update_data.get('tds_amount', voucher.tds_amount)
    update_data['net_amount'] = amount + gst_amount - tds_amount

    # Update financial year and period if date changed
    if 'voucher_date' in update_data:
        update_data['financial_year'] = get_financial_year(update_data['voucher_date'])
        update_data['period'] = get_period(update_data['voucher_date'])

    for key, value in update_data.items():
        setattr(voucher, key, value)

    await db.commit()
    await db.refresh(voucher)

    # Reload with relationships
    return await get_expense_voucher(voucher_id, db, current_user)


@router.delete("/{voucher_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permissions("expenses:delete"))])
async def delete_expense_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Delete expense voucher (only DRAFT status)."""
    result = await db.execute(
        select(ExpenseVoucher).where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete voucher with status {voucher.status}"
        )

    await db.delete(voucher)
    await db.commit()


# ==================== Workflow Endpoints ====================

@router.post("/{voucher_id}/submit", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:update"))])
async def submit_expense_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Submit expense voucher for approval."""
    result = await db.execute(
        select(ExpenseVoucher)
        .options(selectinload(ExpenseVoucher.category))
        .where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit voucher with status {voucher.status}"
        )

    # Check if receipt is required but not attached
    if voucher.category.requires_receipt and (not voucher.attachments or len(voucher.attachments.get('files', [])) == 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt attachment is required for this expense category"
        )

    # Determine approval level
    approval_level = get_approval_level(voucher.net_amount)

    # Check if auto-approval applies
    if voucher.net_amount <= voucher.category.max_amount_without_approval:
        # Auto-approve
        voucher.status = ExpenseVoucherStatus.APPROVED.value
        voucher.approved_by = current_user.id
        voucher.approved_at = datetime.now(timezone.utc)
    else:
        voucher.status = ExpenseVoucherStatus.PENDING_APPROVAL.value

    voucher.submitted_by = current_user.id
    voucher.submitted_at = datetime.now(timezone.utc)
    voucher.approval_level = approval_level

    await db.commit()
    await db.refresh(voucher)

    return await get_expense_voucher(voucher_id, db, current_user)


@router.post("/{voucher_id}/approve", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:approve"))])
async def approve_expense_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Approve expense voucher (maker cannot be checker)."""
    result = await db.execute(
        select(ExpenseVoucher).where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve voucher with status {voucher.status}"
        )

    # Maker-Checker validation
    if voucher.created_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maker cannot approve their own expense voucher"
        )

    voucher.status = ExpenseVoucherStatus.APPROVED.value
    voucher.approved_by = current_user.id
    voucher.approved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(voucher)

    return await get_expense_voucher(voucher_id, db, current_user)


@router.post("/{voucher_id}/reject", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:approve"))])
async def reject_expense_voucher(
    voucher_id: UUID,
    reject_in: ExpenseRejectionRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Reject expense voucher."""
    result = await db.execute(
        select(ExpenseVoucher).where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject voucher with status {voucher.status}"
        )

    voucher.status = ExpenseVoucherStatus.REJECTED.value
    voucher.rejected_by = current_user.id
    voucher.rejected_at = datetime.now(timezone.utc)
    voucher.rejection_reason = reject_in.reason

    await db.commit()
    await db.refresh(voucher)

    return await get_expense_voucher(voucher_id, db, current_user)


@router.post("/{voucher_id}/post", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:post"))])
async def post_expense_voucher(
    voucher_id: UUID,
    db: DB,
    current_user: CurrentUser,
):
    """Post expense voucher to GL."""
    from app.services.accounting_service import AccountingService

    result = await db.execute(
        select(ExpenseVoucher)
        .options(selectinload(ExpenseVoucher.category))
        .where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot post voucher with status {voucher.status}"
        )

    # Post to GL using accounting service
    try:
        accounting_service = AccountingService(db, created_by=current_user.id)
        journal_entry = await accounting_service.post_expense_voucher(
            voucher_id=voucher.id,
            voucher_number=voucher.voucher_number,
            expense_account_id=voucher.category.gl_account_id,
            amount=voucher.amount,
            gst_amount=voucher.gst_amount,
            tds_amount=voucher.tds_amount,
            net_amount=voucher.net_amount,
            payment_mode=voucher.payment_mode,
            bank_account_id=voucher.bank_account_id,
            narration=voucher.narration,
            cost_center_id=voucher.cost_center_id,
        )

        voucher.status = ExpenseVoucherStatus.POSTED.value
        voucher.posted_by = current_user.id
        voucher.posted_at = datetime.now(timezone.utc)
        voucher.journal_entry_id = journal_entry.id

        await db.commit()
        await db.refresh(voucher)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to post expense: {str(e)}"
        )

    return await get_expense_voucher(voucher_id, db, current_user)


@router.post("/{voucher_id}/pay", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:pay"))])
async def mark_expense_paid(
    voucher_id: UUID,
    pay_in: ExpensePaymentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Mark expense voucher as paid."""
    result = await db.execute(
        select(ExpenseVoucher).where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status != ExpenseVoucherStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark as paid voucher with status {voucher.status}"
        )

    voucher.status = ExpenseVoucherStatus.PAID.value
    voucher.paid_by = current_user.id
    voucher.paid_at = datetime.now(timezone.utc)
    voucher.payment_reference = pay_in.payment_reference

    if pay_in.payment_mode:
        voucher.payment_mode = pay_in.payment_mode
    if pay_in.bank_account_id:
        voucher.bank_account_id = pay_in.bank_account_id

    await db.commit()
    await db.refresh(voucher)

    return await get_expense_voucher(voucher_id, db, current_user)


@router.post("/{voucher_id}/attachments", response_model=ExpenseVoucherDetailResponse, dependencies=[Depends(require_permissions("expenses:update"))])
async def add_expense_attachment(
    voucher_id: UUID,
    attachment_in: ExpenseAttachmentRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Add attachment to expense voucher."""
    result = await db.execute(
        select(ExpenseVoucher).where(ExpenseVoucher.id == voucher_id)
    )
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense voucher not found"
        )

    if voucher.status not in [ExpenseVoucherStatus.DRAFT, ExpenseVoucherStatus.PENDING_APPROVAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add attachment to voucher with status {voucher.status}"
        )

    # Initialize attachments if needed
    if not voucher.attachments:
        voucher.attachments = {"files": []}

    # Add attachment
    attachment = {
        "url": attachment_in.file_url,
        "name": attachment_in.file_name,
        "type": attachment_in.file_type,
        "size": attachment_in.file_size,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": str(current_user.id),
    }
    voucher.attachments["files"].append(attachment)

    await db.commit()
    await db.refresh(voucher)

    return await get_expense_voucher(voucher_id, db, current_user)


# ==================== Dashboard ====================

@router.get("/dashboard/stats", response_model=ExpenseDashboard, dependencies=[Depends(require_permissions("expenses:view"))])
async def get_expense_dashboard(
    db: DB,
    current_user: CurrentUser,
):
    """Get expense dashboard statistics."""
    today = date.today()
    fy_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)
    month_start = today.replace(day=1)

    # Voucher counts by status
    status_counts = await db.execute(
        select(ExpenseVoucher.status, func.count(ExpenseVoucher.id))
        .group_by(ExpenseVoucher.status)
    )
    status_dict = dict(status_counts.all())

    total_vouchers = sum(status_dict.values())
    draft_count = status_dict.get(ExpenseVoucherStatus.DRAFT, 0)
    pending_approval_count = status_dict.get(ExpenseVoucherStatus.PENDING_APPROVAL, 0)
    approved_count = status_dict.get(ExpenseVoucherStatus.APPROVED, 0)
    posted_count = status_dict.get(ExpenseVoucherStatus.POSTED, 0)
    paid_count = status_dict.get(ExpenseVoucherStatus.PAID, 0)
    rejected_count = status_dict.get(ExpenseVoucherStatus.REJECTED, 0)

    # Total amount this month
    month_result = await db.execute(
        select(func.sum(ExpenseVoucher.net_amount))
        .where(ExpenseVoucher.voucher_date >= month_start)
        .where(ExpenseVoucher.status.in_([ExpenseVoucherStatus.POSTED, ExpenseVoucherStatus.PAID]))
    )
    total_amount_this_month = month_result.scalar() or Decimal("0")

    # Total amount this year
    year_result = await db.execute(
        select(func.sum(ExpenseVoucher.net_amount))
        .where(ExpenseVoucher.voucher_date >= fy_start)
        .where(ExpenseVoucher.status.in_([ExpenseVoucherStatus.POSTED, ExpenseVoucherStatus.PAID]))
    )
    total_amount_this_year = year_result.scalar() or Decimal("0")

    # Pending approval amount
    pending_result = await db.execute(
        select(func.sum(ExpenseVoucher.net_amount))
        .where(ExpenseVoucher.status == ExpenseVoucherStatus.PENDING_APPROVAL)
    )
    pending_approval_amount = pending_result.scalar() or Decimal("0")

    # Category-wise spending
    category_result = await db.execute(
        select(ExpenseCategory.name, func.sum(ExpenseVoucher.net_amount))
        .join(ExpenseVoucher, ExpenseVoucher.expense_category_id == ExpenseCategory.id)
        .where(ExpenseVoucher.voucher_date >= fy_start)
        .where(ExpenseVoucher.status.in_([ExpenseVoucherStatus.POSTED, ExpenseVoucherStatus.PAID]))
        .group_by(ExpenseCategory.id)
    )
    category_wise_spending = [{"category": name, "amount": float(amt or 0)} for name, amt in category_result.all()]

    # Cost center-wise spending
    cc_result = await db.execute(
        select(CostCenter.name, func.sum(ExpenseVoucher.net_amount))
        .join(ExpenseVoucher, ExpenseVoucher.cost_center_id == CostCenter.id)
        .where(ExpenseVoucher.voucher_date >= fy_start)
        .where(ExpenseVoucher.status.in_([ExpenseVoucherStatus.POSTED, ExpenseVoucherStatus.PAID]))
        .group_by(CostCenter.id)
    )
    cost_center_wise_spending = [{"cost_center": name, "amount": float(amt or 0)} for name, amt in cc_result.all()]

    # Monthly trend (last 6 months)
    monthly_trend = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        m_start = date(y, m, 1)
        m_end = date(y + (1 if m == 12 else 0), (m % 12) + 1, 1)

        m_result = await db.execute(
            select(func.sum(ExpenseVoucher.net_amount))
            .where(ExpenseVoucher.voucher_date >= m_start)
            .where(ExpenseVoucher.voucher_date < m_end)
            .where(ExpenseVoucher.status.in_([ExpenseVoucherStatus.POSTED, ExpenseVoucherStatus.PAID]))
        )
        m_amount = m_result.scalar() or Decimal("0")
        monthly_trend.append({
            "month": m_start.strftime("%b %Y"),
            "amount": float(m_amount)
        })

    return ExpenseDashboard(
        total_vouchers=total_vouchers,
        draft_count=draft_count,
        pending_approval_count=pending_approval_count,
        approved_count=approved_count,
        posted_count=posted_count,
        paid_count=paid_count,
        rejected_count=rejected_count,
        total_amount_this_month=total_amount_this_month,
        total_amount_this_year=total_amount_this_year,
        pending_approval_amount=pending_approval_amount,
        category_wise_spending=category_wise_spending,
        cost_center_wise_spending=cost_center_wise_spending,
        monthly_trend=monthly_trend,
    )
