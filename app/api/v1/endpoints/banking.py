"""API endpoints for Banking module - Statement Import & Reconciliation."""
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.banking import BankAccount, BankTransaction, TransactionType
from app.api.deps import DB, get_current_user
from app.schemas.banking import (
    BankAccountCreate,
    BankAccountResponse,
    BankTransactionResponse,
    ImportResult,
    ReconciliationMatch,
)
from app.services.bank_import_service import BankImportService, BankImportError

router = APIRouter()


# ==================== Bank Accounts ====================

@router.post("/accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account_in: BankAccountCreate,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Create a new bank account."""
    # Check for duplicate account number
    existing = await db.execute(
        select(BankAccount).where(BankAccount.account_number == account_in.account_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Bank account with this account number already exists"
        )

    account = BankAccount(
        account_name=account_in.account_name,
        account_number=account_in.account_number,
        bank_name=account_in.bank_name,
        branch_name=account_in.branch_name,
        ifsc_code=account_in.ifsc_code,
        account_type=account_in.account_type,
        opening_balance=account_in.opening_balance,
        current_balance=account_in.opening_balance,
        ledger_account_id=account_in.ledger_account_id,
        created_by=current_user.id,
    )

    db.add(account)
    await db.commit()
    await db.refresh(account)

    return account


@router.get("/accounts", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    db: DB,
    is_active: Optional[bool] = True,
    current_user: User = Depends(get_current_user),
):
    """List all bank accounts."""
    query = select(BankAccount)
    if is_active is not None:
        query = query.where(BankAccount.is_active == is_active)

    query = query.order_by(BankAccount.bank_name, BankAccount.account_name)

    result = await db.execute(query)
    accounts = result.scalars().all()

    return accounts


@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get bank account by ID."""
    result = await db.execute(
        select(BankAccount).where(BankAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    return account


# ==================== Statement Import ====================

@router.post("/accounts/{account_id}/import-statement", response_model=ImportResult)
async def import_bank_statement(
    account_id: UUID,
    file: UploadFile = File(...),
    bank_format: str = Form(default="AUTO"),
    skip_duplicates: bool = Form(default=True),
    db: DB = None,
    current_user: User = Depends(get_current_user),
):
    """
    Import bank statement from CSV or Excel file.

    Supported formats:
    - AUTO: Auto-detect bank format
    - HDFC: HDFC Bank statement format
    - ICICI: ICICI Bank statement format
    - SBI: State Bank of India format
    - GENERIC: Generic CSV with standard columns

    Expected columns:
    - Date: Transaction date
    - Description/Narration: Transaction description
    - Debit/Withdrawal: Debit amount
    - Credit/Deposit: Credit amount
    - Balance: Running balance (optional)
    - Reference: Transaction reference (optional)
    """
    # Validate file type
    filename = file.filename or ""
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or Excel file."
        )

    # Verify bank account exists
    result = await db.execute(
        select(BankAccount).where(BankAccount.id == account_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bank account not found")

    try:
        import_service = BankImportService(db)

        # Read file content
        file_content = await file.read()

        if filename.endswith('.csv'):
            # Decode CSV content
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                try:
                    content_str = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    content_str = file_content.decode('cp1252')

            result = await import_service.import_csv_statement(
                bank_account_id=account_id,
                file_content=content_str,
                filename=filename,
                bank_format=bank_format,
                skip_duplicates=skip_duplicates,
                user_id=current_user.id
            )
        else:
            # Excel file
            result = await import_service.import_excel_statement(
                bank_account_id=account_id,
                file_bytes=file_content,
                filename=filename,
                bank_format=bank_format,
                skip_duplicates=skip_duplicates,
                user_id=current_user.id
            )

        return result

    except BankImportError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Import failed: {e.message}",
            headers={"X-Row-Number": str(e.row_number) if e.row_number else None}
        )


# ==================== Transactions ====================

@router.get("/accounts/{account_id}/transactions", response_model=List[BankTransactionResponse])
async def list_bank_transactions(
    account_id: UUID,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_reconciled: Optional[bool] = None,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List bank transactions for an account."""
    query = select(BankTransaction).where(BankTransaction.bank_account_id == account_id)

    filters = []
    if start_date:
        filters.append(BankTransaction.transaction_date >= start_date)
    if end_date:
        filters.append(BankTransaction.transaction_date <= end_date)
    if is_reconciled is not None:
        filters.append(BankTransaction.is_reconciled == is_reconciled)
    if transaction_type:
        filters.append(BankTransaction.transaction_type == TransactionType(transaction_type))

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(BankTransaction.transaction_date.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return [
        BankTransactionResponse(
            id=t.id,
            transaction_date=t.transaction_date,
            description=t.description,
            reference_number=t.reference_number,
            transaction_type=t.transaction_type.value if t.transaction_type else "UNKNOWN",
            amount=t.amount,
            debit_amount=t.debit_amount or Decimal("0"),
            credit_amount=t.credit_amount or Decimal("0"),
            running_balance=t.running_balance,
            is_reconciled=t.is_reconciled
        )
        for t in transactions
    ]


@router.get("/accounts/{account_id}/transactions/summary")
async def get_transaction_summary(
    account_id: UUID,
    db: DB,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """Get summary of bank transactions."""
    filters = [BankTransaction.bank_account_id == account_id]

    if start_date:
        filters.append(BankTransaction.transaction_date >= start_date)
    if end_date:
        filters.append(BankTransaction.transaction_date <= end_date)

    # Total count
    count_query = select(func.count(BankTransaction.id)).where(and_(*filters))
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    # Total debit
    debit_query = select(func.coalesce(func.sum(BankTransaction.debit_amount), 0)).where(and_(*filters))
    debit_result = await db.execute(debit_query)
    total_debit = debit_result.scalar() or Decimal("0")

    # Total credit
    credit_query = select(func.coalesce(func.sum(BankTransaction.credit_amount), 0)).where(and_(*filters))
    credit_result = await db.execute(credit_query)
    total_credit = credit_result.scalar() or Decimal("0")

    # Reconciled count
    reconciled_filters = filters + [BankTransaction.is_reconciled == True]
    reconciled_query = select(func.count(BankTransaction.id)).where(and_(*reconciled_filters))
    reconciled_result = await db.execute(reconciled_query)
    reconciled_count = reconciled_result.scalar() or 0

    return {
        "total_transactions": total_count,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "net_change": float(total_credit - total_debit),
        "reconciled_count": reconciled_count,
        "unreconciled_count": total_count - reconciled_count,
        "reconciliation_percentage": round((reconciled_count / total_count * 100), 2) if total_count > 0 else 0
    }


# ==================== Reconciliation ====================

@router.get("/accounts/{account_id}/unreconciled")
async def get_unreconciled_transactions(
    account_id: UUID,
    db: DB,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    """Get unreconciled bank transactions for matching."""
    import_service = BankImportService(db)
    transactions = await import_service.get_unreconciled_transactions(
        bank_account_id=account_id,
        limit=limit
    )

    return [
        {
            "id": str(t.id),
            "date": str(t.transaction_date),
            "description": t.description,
            "reference": t.reference_number,
            "type": t.transaction_type.value if t.transaction_type else None,
            "amount": float(t.amount),
            "debit": float(t.debit_amount) if t.debit_amount else 0,
            "credit": float(t.credit_amount) if t.credit_amount else 0,
        }
        for t in transactions
    ]


@router.post("/reconcile/match")
async def match_transaction_with_journal(
    match_request: ReconciliationMatch,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Match a bank transaction with a journal entry for reconciliation."""
    import_service = BankImportService(db)

    try:
        result = await import_service.match_with_journal_entries(
            bank_transaction_id=match_request.bank_transaction_id,
            journal_entry_id=match_request.journal_entry_id
        )
        return result

    except BankImportError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/transactions/{transaction_id}/suggest-matches")
async def suggest_journal_matches(
    transaction_id: UUID,
    db: DB,
    tolerance_days: int = Query(3, ge=0, le=30),
    tolerance_amount: float = Query(1.0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """
    Get suggested journal entry matches for a bank transaction.

    Uses fuzzy matching on date and amount to find potential matches.
    """
    import_service = BankImportService(db)

    suggestions = await import_service.suggest_matches(
        bank_transaction_id=transaction_id,
        tolerance_days=tolerance_days,
        tolerance_amount=Decimal(str(tolerance_amount))
    )

    return {"suggestions": suggestions}


@router.post("/transactions/{transaction_id}/unreconcile")
async def unreconcile_transaction(
    transaction_id: UUID,
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Mark a transaction as unreconciled."""
    result = await db.execute(
        select(BankTransaction).where(BankTransaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.is_reconciled = False
    transaction.reconciled_at = None
    transaction.matched_journal_entry_id = None

    await db.commit()

    return {"success": True, "message": "Transaction marked as unreconciled"}
