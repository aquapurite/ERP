"""Banking module schemas for API requests/responses."""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal


class BankAccountCreate(BaseModel):
    """Create bank account request."""
    account_name: str = Field(..., description="Account display name")
    account_number: str = Field(..., description="Bank account number")
    bank_name: str = Field(..., description="Bank name")
    branch_name: Optional[str] = Field(None, description="Branch name")
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    account_type: str = Field("CURRENT", description="Account type: CURRENT, SAVINGS, CASH_CREDIT, OVERDRAFT")
    opening_balance: Decimal = Field(Decimal("0"), description="Opening balance")
    ledger_account_id: Optional[UUID] = Field(None, description="Linked ledger account ID")


class BankAccountResponse(BaseModel):
    """Bank account response."""
    id: UUID
    account_name: str
    account_number: str
    bank_name: str
    branch_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_type: str
    current_balance: Decimal
    is_active: bool

    class Config:
        from_attributes = True


class BankTransactionResponse(BaseModel):
    """Bank transaction response."""
    id: UUID
    transaction_date: date
    description: str
    reference_number: Optional[str] = None
    transaction_type: str
    amount: Decimal
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Optional[Decimal] = None
    is_reconciled: bool

    class Config:
        from_attributes = True


class ImportResult(BaseModel):
    """Import result response."""
    success: bool = Field(..., description="Whether import was successful")
    bank_format: str = Field(..., description="Detected bank format")
    statistics: dict = Field(..., description="Import statistics")
    transactions: List[dict] = Field(..., description="Imported transactions")
    errors: Optional[List[dict]] = Field(None, description="Any errors encountered")


class ReconciliationMatch(BaseModel):
    """Match bank transaction with journal entry."""
    bank_transaction_id: UUID = Field(..., description="Bank transaction ID")
    journal_entry_id: UUID = Field(..., description="Journal entry ID to match with")
