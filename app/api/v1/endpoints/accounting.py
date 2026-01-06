"""API endpoints for Accounting & Finance module."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounting import (
    ChartOfAccount, AccountType, AccountSubType,
    FinancialPeriod, FinancialPeriodStatus as PeriodStatus,
    CostCenter,
    JournalEntry, JournalEntryLine, JournalEntryStatus as JournalStatus,
    GeneralLedger,
    TaxConfiguration,
)
from app.models.user import User
from app.schemas.accounting import (
    # Chart of Accounts
    ChartOfAccountCreate, ChartOfAccountUpdate, ChartOfAccountResponse,
    ChartOfAccountTree, AccountListResponse,
    # Financial Period
    FinancialPeriodCreate, FinancialPeriodResponse, PeriodListResponse,
    # Cost Center
    CostCenterCreate, CostCenterUpdate, CostCenterResponse,
    # Journal Entry
    JournalEntryCreate, JournalEntryResponse, JournalListResponse,
    JournalEntryLineCreate, JournalApproveRequest, JournalReverseRequest,
    # General Ledger
    GeneralLedgerResponse, LedgerListResponse,
    # Reports
    TrialBalanceResponse, TrialBalanceItem,
    BalanceSheetResponse, ProfitLossResponse,
    # Tax
    TaxConfigurationCreate, TaxConfigurationResponse,
)
from app.api.deps import DB, CurrentUser, get_current_user, require_permissions
from app.services.audit_service import AuditService

router = APIRouter()


# ==================== Chart of Accounts ====================

@router.post("/accounts", response_model=ChartOfAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: ChartOfAccountCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new account in Chart of Accounts."""
    # Check for duplicate code
    existing = await db.execute(
        select(ChartOfAccount).where(ChartOfAccount.account_code == account_in.account_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Account code {account_in.account_code} already exists"
        )

    # Validate parent if provided
    if account_in.parent_id:
        parent = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == account_in.parent_id)
        )
        if not parent.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent account not found")

    account = ChartOfAccount(
        **account_in.model_dump(),
        created_by=current_user.id,
    )

    db.add(account)
    await db.commit()
    await db.refresh(account)

    return account


@router.get("/accounts", response_model=AccountListResponse)
async def list_accounts(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    account_type: Optional[AccountType] = None,
    sub_type: Optional[AccountSubType] = None,
    parent_id: Optional[UUID] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
    current_user: User = Depends(get_current_user),
):
    """List accounts from Chart of Accounts."""
    query = select(ChartOfAccount)
    count_query = select(func.count(ChartOfAccount.id))

    filters = []
    if account_type:
        filters.append(ChartOfAccount.account_type == account_type)
    if sub_type:
        filters.append(ChartOfAccount.sub_type == sub_type)
    if parent_id:
        filters.append(ChartOfAccount.parent_id == parent_id)
    if is_active is not None:
        filters.append(ChartOfAccount.is_active == is_active)
    if search:
        filters.append(or_(
            ChartOfAccount.account_code.ilike(f"%{search}%"),
            ChartOfAccount.name.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(ChartOfAccount.account_code).offset(skip).limit(limit)
    result = await db.execute(query)
    accounts = result.scalars().all()

    return AccountListResponse(
        items=[ChartOfAccountResponse.model_validate(a) for a in accounts],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/accounts/tree", response_model=List[ChartOfAccountTree])
async def get_accounts_tree(
    db: DB,
    account_type: Optional[AccountType] = None,
    current_user: User = Depends(get_current_user),
):
    """Get Chart of Accounts as a hierarchical tree."""
    query = select(ChartOfAccount).where(ChartOfAccount.is_active == True)

    if account_type:
        query = query.where(ChartOfAccount.account_type == account_type)

    query = query.order_by(ChartOfAccount.account_code)
    result = await db.execute(query)
    accounts = result.scalars().all()

    # Build tree structure
    account_map = {a.id: a for a in accounts}
    root_accounts = []

    for account in accounts:
        if account.parent_id is None:
            root_accounts.append(account)

    def build_tree(account) -> ChartOfAccountTree:
        children = [a for a in accounts if a.parent_id == account.id]
        return ChartOfAccountTree(
            id=account.id,
            account_code=account.account_code,
            name=account.name,
            account_type=account.account_type,
            sub_type=account.sub_type,
            is_group=account.is_group,
            current_balance=account.current_balance,
            children=[build_tree(c) for c in children] if children else []
        )

    return [build_tree(a) for a in root_accounts]


@router.get("/accounts/dropdown")
async def get_accounts_dropdown(
    db: DB,
    account_type: Optional[AccountType] = None,
    postable_only: bool = True,
    current_user: User = Depends(get_current_user),
):
    """Get accounts for dropdown selection."""
    query = select(ChartOfAccount).where(ChartOfAccount.is_active == True)

    if account_type:
        query = query.where(ChartOfAccount.account_type == account_type)
    if postable_only:
        query = query.where(ChartOfAccount.is_group == False)

    query = query.order_by(ChartOfAccount.account_code)
    result = await db.execute(query)
    accounts = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "code": a.account_code,
            "name": a.name,
            "full_name": f"{a.account_code} - {a.name}",
            "type": a.account_type.value,
        }
        for a in accounts
    ]


@router.get("/accounts/{account_id}", response_model=ChartOfAccountResponse)
async def get_account(
    account_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get account by ID."""
    result = await db.execute(
        select(ChartOfAccount).where(ChartOfAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.put("/accounts/{account_id}", response_model=ChartOfAccountResponse)
async def update_account(
    account_id: UUID,
    account_in: ChartOfAccountUpdate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Update account details."""
    result = await db.execute(
        select(ChartOfAccount).where(ChartOfAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = account_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    account.updated_by = current_user.id

    await db.commit()
    await db.refresh(account)

    return account


# ==================== Financial Periods ====================

@router.post("/periods", response_model=FinancialPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_period(
    period_in: FinancialPeriodCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new financial period."""
    # Check for overlapping periods
    overlap = await db.execute(
        select(FinancialPeriod).where(
            and_(
                FinancialPeriod.start_date <= period_in.end_date,
                FinancialPeriod.end_date >= period_in.start_date,
            )
        )
    )
    if overlap.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Period overlaps with existing financial period"
        )

    period = FinancialPeriod(
        **period_in.model_dump(),
        created_by=current_user.id,
    )

    db.add(period)
    await db.commit()
    await db.refresh(period)

    return period


@router.get("/periods", response_model=PeriodListResponse)
async def list_financial_periods(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    status: Optional[PeriodStatus] = None,
    current_user: User = Depends(get_current_user),
):
    """List financial periods."""
    query = select(FinancialPeriod)
    count_query = select(func.count(FinancialPeriod.id))

    if status:
        query = query.where(FinancialPeriod.status == status)
        count_query = count_query.where(FinancialPeriod.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(FinancialPeriod.start_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    periods = result.scalars().all()

    return PeriodListResponse(
        items=[FinancialPeriodResponse.model_validate(p) for p in periods],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/periods/current", response_model=FinancialPeriodResponse)
async def get_current_period(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get the current open financial period."""
    today = date.today()
    result = await db.execute(
        select(FinancialPeriod).where(
            and_(
                FinancialPeriod.start_date <= today,
                FinancialPeriod.end_date >= today,
                FinancialPeriod.status == PeriodStatus.OPEN,
            )
        )
    )
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=404,
            detail="No open financial period for current date"
        )

    return period


@router.post("/periods/{period_id}/close", response_model=FinancialPeriodResponse)
async def close_financial_period(
    period_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Close a financial period (year-end closing)."""
    result = await db.execute(
        select(FinancialPeriod).where(FinancialPeriod.id == period_id)
    )
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    if period.status != PeriodStatus.OPEN:
        raise HTTPException(status_code=400, detail="Period is not open")

    # Check for unposted journal entries
    unposted = await db.execute(
        select(func.count(JournalEntry.id)).where(
            and_(
                JournalEntry.entry_date >= period.start_date,
                JournalEntry.entry_date <= period.end_date,
                JournalEntry.status != JournalStatus.POSTED,
            )
        )
    )
    unposted_count = unposted.scalar() or 0

    if unposted_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close period with {unposted_count} unposted journal entries"
        )

    # TODO: Generate closing entries (transfer P&L to Retained Earnings)

    period.status = PeriodStatus.CLOSED
    period.closed_at = datetime.utcnow()
    period.closed_by = current_user.id

    await db.commit()
    await db.refresh(period)

    return period


# ==================== Cost Centers ====================

@router.post("/cost-centers", response_model=CostCenterResponse, status_code=status.HTTP_201_CREATED)
async def create_cost_center(
    cc_in: CostCenterCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new cost center."""
    cost_center = CostCenter(
        **cc_in.model_dump(),
        created_by=current_user.id,
    )

    db.add(cost_center)
    await db.commit()
    await db.refresh(cost_center)

    return cost_center


@router.get("/cost-centers", response_model=List[CostCenterResponse])
async def list_cost_centers(
    db: DB,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
):
    """List all cost centers."""
    query = select(CostCenter)
    if is_active is not None:
        query = query.where(CostCenter.is_active == is_active)

    query = query.order_by(CostCenter.code)
    result = await db.execute(query)
    cost_centers = result.scalars().all()

    return [CostCenterResponse.model_validate(cc) for cc in cost_centers]


# ==================== Journal Entries ====================

@router.post("/journals", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    journal_in: JournalEntryCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new journal entry."""
    # Validate the current period
    period_result = await db.execute(
        select(FinancialPeriod).where(
            and_(
                FinancialPeriod.start_date <= journal_in.entry_date,
                FinancialPeriod.end_date >= journal_in.entry_date,
                FinancialPeriod.status == PeriodStatus.OPEN,
            )
        )
    )
    period = period_result.scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=400,
            detail="No open financial period for the entry date"
        )

    # Validate debit = credit
    total_debit = sum(line.debit_amount for line in journal_in.lines)
    total_credit = sum(line.credit_amount for line in journal_in.lines)

    if total_debit != total_credit:
        raise HTTPException(
            status_code=400,
            detail=f"Debits ({total_debit}) must equal Credits ({total_credit})"
        )

    if total_debit == 0:
        raise HTTPException(status_code=400, detail="Journal entry cannot have zero amount")

    # Generate journal number
    today = date.today()
    count_result = await db.execute(
        select(func.count(JournalEntry.id)).where(
            func.date(JournalEntry.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    entry_number = f"JV-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Create journal entry
    journal = JournalEntry(
        entry_number=entry_number,
        journal_type=journal_in.journal_type,
        entry_date=journal_in.entry_date,
        period_id=period.id,
        narration=journal_in.narration,
        reference_type=journal_in.reference_type,
        reference_number=journal_in.reference_number,
        reference_id=journal_in.reference_id,
        total_debit=total_debit,
        total_credit=total_credit,
        created_by=current_user.id,
    )

    db.add(journal)
    await db.flush()

    # Create journal lines
    line_number = 0
    for line_data in journal_in.lines:
        line_number += 1

        # Verify account exists
        account_result = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == line_data.account_id)
        )
        account = account_result.scalar_one_or_none()
        if not account:
            raise HTTPException(
                status_code=400,
                detail=f"Account {line_data.account_id} not found"
            )
        if account.is_group:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot post to group account: {account.name}"
            )

        line = JournalEntryLine(
            journal_id=journal.id,
            line_number=line_number,
            account_id=line_data.account_id,
            account_code=account.account_code,
            account_name=account.name,
            debit_amount=line_data.debit_amount,
            credit_amount=line_data.credit_amount,
            cost_center_id=line_data.cost_center_id,
            narration=line_data.narration,
        )
        db.add(line)

    await db.commit()

    # Load full journal
    result = await db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .where(JournalEntry.id == journal.id)
    )
    journal = result.scalar_one()

    return journal


@router.get("/journals", response_model=JournalListResponse)
async def list_journal_entries(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    entry_type: Optional[str] = None,
    status: Optional[JournalStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List journal entries."""
    query = select(JournalEntry).options(selectinload(JournalEntry.lines))
    count_query = select(func.count(JournalEntry.id))

    filters = []
    if entry_type:
        filters.append(JournalEntry.entry_type == entry_type)
    if status:
        filters.append(JournalEntry.status == status)
    if start_date:
        filters.append(JournalEntry.entry_date >= start_date)
    if end_date:
        filters.append(JournalEntry.entry_date <= end_date)
    if search:
        filters.append(or_(
            JournalEntry.entry_number.ilike(f"%{search}%"),
            JournalEntry.narration.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    journals = result.scalars().all()

    return JournalListResponse(
        items=[JournalEntryResponse.model_validate(j) for j in journals],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/journals/{journal_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    journal_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get journal entry by ID."""
    result = await db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .where(JournalEntry.id == journal_id)
    )
    journal = result.scalar_one_or_none()

    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return journal


@router.post("/journals/{journal_id}/approve", response_model=JournalEntryResponse)
async def approve_journal_entry(
    journal_id: UUID,
    request: JournalApproveRequest,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a journal entry."""
    result = await db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .where(JournalEntry.id == journal_id)
    )
    journal = result.scalar_one_or_none()

    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if journal.status != JournalStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve journal in {journal.status.value} status"
        )

    if request.action == "APPROVE":
        journal.status = JournalStatus.APPROVED
        journal.approved_by = current_user.id
        journal.approved_at = datetime.utcnow()
    else:
        journal.status = JournalStatus.REJECTED

    await db.commit()
    await db.refresh(journal)

    return journal


@router.post("/journals/{journal_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(
    journal_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Post an approved journal entry to the General Ledger."""
    result = await db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .where(JournalEntry.id == journal_id)
    )
    journal = result.scalar_one_or_none()

    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if journal.status != JournalStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Only approved journals can be posted"
        )

    # Create General Ledger entries for each line
    for line in journal.lines:
        gl_entry = GeneralLedger(
            account_id=line.account_id,
            period_id=journal.period_id,
            entry_date=journal.entry_date,
            journal_id=journal.id,
            entry_number=journal.entry_number,
            journal_type=journal.journal_type,
            debit_amount=line.debit_amount,
            credit_amount=line.credit_amount,
            balance=line.debit_amount - line.credit_amount,
            narration=line.narration or journal.narration,
            cost_center_id=line.cost_center_id,
            reference_type=journal.reference_type,
            reference_number=journal.reference_number,
            created_by=current_user.id,
        )
        db.add(gl_entry)

        # Update account balance
        account_result = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.id == line.account_id)
        )
        account = account_result.scalar_one()

        # For Assets and Expenses, debit increases; for Liabilities, Equity, Revenue, credit increases
        if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            account.current_balance += (line.debit_amount - line.credit_amount)
        else:  # LIABILITY, EQUITY, REVENUE
            account.current_balance += (line.credit_amount - line.debit_amount)

    # Update journal status
    journal.status = JournalStatus.POSTED
    journal.posted_by = current_user.id
    journal.posted_at = datetime.utcnow()

    await db.commit()
    await db.refresh(journal)

    return journal


@router.post("/journals/{journal_id}/reverse", response_model=JournalEntryResponse)
async def reverse_journal_entry(
    journal_id: UUID,
    reversal_date: date,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a reversal journal entry."""
    result = await db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .where(JournalEntry.id == journal_id)
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if original.status != JournalStatus.POSTED:
        raise HTTPException(status_code=400, detail="Only posted journals can be reversed")

    if original.is_reversed:
        raise HTTPException(status_code=400, detail="Journal already reversed")

    # Verify period is open
    period_result = await db.execute(
        select(FinancialPeriod).where(
            and_(
                FinancialPeriod.start_date <= reversal_date,
                FinancialPeriod.end_date >= reversal_date,
                FinancialPeriod.status == PeriodStatus.OPEN,
            )
        )
    )
    period = period_result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=400, detail="No open period for reversal date")

    # Generate reversal journal number
    today = date.today()
    count_result = await db.execute(
        select(func.count(JournalEntry.id)).where(
            func.date(JournalEntry.created_at) == today
        )
    )
    count = count_result.scalar() or 0
    reversal_number = f"JV-{today.strftime('%Y%m%d')}-{str(count + 1).zfill(4)}"

    # Create reversal journal
    reversal = JournalEntry(
        entry_number=reversal_number,
        entry_type="REVERSAL",
        entry_date=reversal_date,
        period_id=period.id,
        narration=f"Reversal of {original.entry_number}",
        source_type="REVERSAL",
        source_number=original.entry_number,
        source_id=original.id,
        total_debit=original.total_credit,  # Swap
        total_credit=original.total_debit,
        reversal_of_id=original.id,
        status=JournalStatus.APPROVED,
        approved_by=current_user.id,
        approved_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(reversal)
    await db.flush()

    # Create reversed lines (swap debit/credit)
    line_number = 0
    for orig_line in original.lines:
        line_number += 1
        line = JournalEntryLine(
            journal_id=reversal.id,
            line_number=line_number,
            account_id=orig_line.account_id,
            account_code=orig_line.account_code,
            account_name=orig_line.account_name,
            debit_amount=orig_line.credit_amount,  # Swap
            credit_amount=orig_line.debit_amount,
            cost_center_id=orig_line.cost_center_id,
            narration=f"Reversal: {orig_line.narration or ''}",
        )
        db.add(line)

    # Mark original as reversed
    original.is_reversed = True
    original.reversed_by_id = reversal.id

    await db.commit()

    # Load full reversal
    result = await db.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .where(JournalEntry.id == reversal.id)
    )
    reversal = result.scalar_one()

    return reversal


# ==================== General Ledger ====================

@router.get("/ledger/{account_id}", response_model=LedgerListResponse)
async def get_account_ledger(
    account_id: UUID,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """Get General Ledger entries for an account."""
    # Verify account
    account_result = await db.execute(
        select(ChartOfAccount).where(ChartOfAccount.id == account_id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    query = select(GeneralLedger).where(GeneralLedger.account_id == account_id)
    count_query = select(func.count(GeneralLedger.id)).where(
        GeneralLedger.account_id == account_id
    )

    if start_date:
        query = query.where(GeneralLedger.entry_date >= start_date)
        count_query = count_query.where(GeneralLedger.entry_date >= start_date)
    if end_date:
        query = query.where(GeneralLedger.entry_date <= end_date)
        count_query = count_query.where(GeneralLedger.entry_date <= end_date)

    # Get totals
    totals_query = select(
        func.coalesce(func.sum(GeneralLedger.debit_amount), 0).label("total_debit"),
        func.coalesce(func.sum(GeneralLedger.credit_amount), 0).label("total_credit"),
    ).where(GeneralLedger.account_id == account_id)

    if start_date:
        totals_query = totals_query.where(GeneralLedger.entry_date >= start_date)
    if end_date:
        totals_query = totals_query.where(GeneralLedger.entry_date <= end_date)

    totals_result = await db.execute(totals_query)
    totals = totals_result.one()

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(GeneralLedger.entry_date, GeneralLedger.created_at)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    entries = result.scalars().all()

    return LedgerListResponse(
        account_id=account_id,
        account_code=account.account_code,
        account_name=account.name,
        items=[GeneralLedgerResponse.model_validate(e) for e in entries],
        total=total,
        total_debit=totals.total_debit,
        total_credit=totals.total_credit,
        closing_balance=account.current_balance,
        skip=skip,
        limit=limit
    )


# ==================== Reports ====================

@router.get("/reports/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    db: DB,
    as_of_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
):
    """Get Trial Balance report."""
    # Get all accounts with balances
    query = select(ChartOfAccount).where(
        and_(
            ChartOfAccount.is_active == True,
            ChartOfAccount.is_group == False,
        )
    ).order_by(ChartOfAccount.account_code)

    result = await db.execute(query)
    accounts = result.scalars().all()

    items = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for account in accounts:
        balance = account.current_balance

        if balance == 0:
            continue

        debit = Decimal("0")
        credit = Decimal("0")

        # Assets and Expenses have debit balances
        if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            if balance > 0:
                debit = balance
            else:
                credit = abs(balance)
        else:  # Liabilities, Equity, Revenue have credit balances
            if balance > 0:
                credit = balance
            else:
                debit = abs(balance)

        total_debit += debit
        total_credit += credit

        items.append(TrialBalanceItem(
            account_id=account.id,
            account_code=account.account_code,
            account_name=account.name,
            account_type=account.account_type,
            debit_balance=debit,
            credit_balance=credit,
        ))

    return TrialBalanceResponse(
        as_of_date=as_of_date,
        items=items,
        total_debit=total_debit,
        total_credit=total_credit,
        is_balanced=total_debit == total_credit,
    )


@router.get("/reports/balance-sheet")
async def get_balance_sheet(
    db: DB,
    as_of_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
):
    """Get Balance Sheet report."""
    # Assets
    assets_query = select(
        ChartOfAccount.sub_type,
        func.sum(ChartOfAccount.current_balance).label("total")
    ).where(
        and_(
            ChartOfAccount.account_type == AccountType.ASSET,
            ChartOfAccount.is_group == False,
        )
    ).group_by(ChartOfAccount.sub_type)

    assets_result = await db.execute(assets_query)
    assets_data = {row.sub_type.value if row.sub_type else "other": float(row.total or 0) for row in assets_result.all()}

    # Liabilities
    liabilities_query = select(
        ChartOfAccount.sub_type,
        func.sum(ChartOfAccount.current_balance).label("total")
    ).where(
        and_(
            ChartOfAccount.account_type == AccountType.LIABILITY,
            ChartOfAccount.is_group == False,
        )
    ).group_by(ChartOfAccount.sub_type)

    liabilities_result = await db.execute(liabilities_query)
    liabilities_data = {row.sub_type.value if row.sub_type else "other": float(row.total or 0) for row in liabilities_result.all()}

    # Equity
    equity_query = select(
        func.sum(ChartOfAccount.current_balance)
    ).where(
        and_(
            ChartOfAccount.account_type == AccountType.EQUITY,
            ChartOfAccount.is_group == False,
        )
    )
    equity_result = await db.execute(equity_query)
    total_equity = float(equity_result.scalar() or 0)

    total_assets = sum(assets_data.values())
    total_liabilities = sum(liabilities_data.values())

    return {
        "as_of_date": as_of_date.isoformat(),
        "assets": {
            "breakdown": assets_data,
            "total": total_assets,
        },
        "liabilities": {
            "breakdown": liabilities_data,
            "total": total_liabilities,
        },
        "equity": {
            "total": total_equity,
        },
        "total_liabilities_and_equity": total_liabilities + total_equity,
        "is_balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01,
    }


@router.get("/reports/profit-loss")
async def get_profit_loss(
    start_date: date,
    end_date: date,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get Profit & Loss statement."""
    # Revenue
    revenue_query = select(
        ChartOfAccount.sub_type,
        func.sum(GeneralLedger.credit_amount - GeneralLedger.debit_amount).label("total")
    ).join(
        GeneralLedger, GeneralLedger.account_id == ChartOfAccount.id
    ).where(
        and_(
            ChartOfAccount.account_type == AccountType.REVENUE,
            GeneralLedger.entry_date >= start_date,
            GeneralLedger.entry_date <= end_date,
        )
    ).group_by(ChartOfAccount.sub_type)

    revenue_result = await db.execute(revenue_query)
    revenue_data = {row.sub_type.value if row.sub_type else "other": float(row.total or 0) for row in revenue_result.all()}

    # Expenses
    expense_query = select(
        ChartOfAccount.sub_type,
        func.sum(GeneralLedger.debit_amount - GeneralLedger.credit_amount).label("total")
    ).join(
        GeneralLedger, GeneralLedger.account_id == ChartOfAccount.id
    ).where(
        and_(
            ChartOfAccount.account_type == AccountType.EXPENSE,
            GeneralLedger.entry_date >= start_date,
            GeneralLedger.entry_date <= end_date,
        )
    ).group_by(ChartOfAccount.sub_type)

    expense_result = await db.execute(expense_query)
    expense_data = {row.sub_type.value if row.sub_type else "other": float(row.total or 0) for row in expense_result.all()}

    total_revenue = sum(revenue_data.values())
    total_expense = sum(expense_data.values())
    net_income = total_revenue - total_expense

    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "revenue": {
            "breakdown": revenue_data,
            "total": total_revenue,
        },
        "expenses": {
            "breakdown": expense_data,
            "total": total_expense,
        },
        "gross_profit": total_revenue,  # Simplified
        "operating_income": net_income,
        "net_income": net_income,
    }


# ==================== Tax Configuration ====================

@router.get("/tax-configs", response_model=List[TaxConfigurationResponse])
async def list_tax_configurations(
    db: DB,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
):
    """List tax configurations."""
    query = select(TaxConfiguration)
    if is_active is not None:
        query = query.where(TaxConfiguration.is_active == is_active)

    query = query.order_by(TaxConfiguration.tax_name)
    result = await db.execute(query)
    configs = result.scalars().all()

    return [TaxConfigurationResponse.model_validate(c) for c in configs]


@router.post("/tax-configs", response_model=TaxConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_configuration(
    config_in: TaxConfigurationCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new tax configuration."""
    config = TaxConfiguration(
        **config_in.model_dump(),
        created_by=current_user.id,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return config
