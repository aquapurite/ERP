"""
Document Sequence Service for Atomic Number Generation

INDUSTRY BEST PRACTICE:
- Financial year based numbering (April-March)
- Continuous sequence within financial year (NO daily reset)
- Atomic number generation with database-level locking
- Format: {PREFIX}/{COMPANY_CODE}/{FY}/{SEQUENCE}

USAGE:
    from app.services.document_sequence_service import DocumentSequenceService

    async def create_pr(db: AsyncSession):
        service = DocumentSequenceService(db)
        pr_number = await service.get_next_number("PR")
        # Returns: PR/APL/25-26/00001

SUPPORTED DOCUMENT TYPES:
    PR  - Purchase Requisition
    PO  - Purchase Order
    GRN - Goods Receipt Note
    SRN - Sales Return Note
    ST  - Stock Transfer
    SA  - Stock Adjustment
    MF  - Manifest
    PL  - Picklist
"""

from typing import Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_sequence import DocumentSequence, DocumentType


# Document type metadata
DOCUMENT_METADATA = {
    "PR": {"name": "Purchase Requisition", "padding": 5},
    "PO": {"name": "Purchase Order", "padding": 5},
    "GRN": {"name": "Goods Receipt Note", "padding": 5},
    "SRN": {"name": "Sales Return Note", "padding": 5},
    "ST": {"name": "Stock Transfer", "padding": 5},
    "SA": {"name": "Stock Adjustment", "padding": 5},
    "MF": {"name": "Manifest", "padding": 5},
    "PL": {"name": "Picklist", "padding": 5},
}


class DocumentSequenceService:
    """
    Service for generating atomic document numbers.

    Uses database-level locking (SELECT FOR UPDATE) to ensure
    no duplicate numbers are generated even under concurrent load.
    """

    def __init__(self, db: AsyncSession, company_code: str = "APL"):
        """
        Initialize the service.

        Args:
            db: Async database session
            company_code: Company code for document numbers (default: APL)
        """
        self.db = db
        self.company_code = company_code

    async def get_next_number(
        self,
        document_type: str,
        financial_year: Optional[str] = None
    ) -> str:
        """
        Get next document number with atomic increment.

        Uses SELECT FOR UPDATE to prevent race conditions.
        Creates sequence record if it doesn't exist.

        Args:
            document_type: Document type code (PR, PO, GRN, etc.)
            financial_year: Optional FY string. Auto-calculated if not provided.

        Returns:
            Formatted document number, e.g., PR/APL/25-26/00001

        Raises:
            ValueError: If document_type is invalid
        """
        # Validate document type
        doc_type = document_type.upper()
        if doc_type not in DOCUMENT_METADATA:
            valid_types = ", ".join(DOCUMENT_METADATA.keys())
            raise ValueError(f"Invalid document type '{doc_type}'. Valid types: {valid_types}")

        # Get current financial year if not provided
        if not financial_year:
            financial_year = DocumentSequence.get_financial_year()

        # Lock and get/create sequence record
        sequence = await self._get_or_create_sequence(doc_type, financial_year)

        # Generate the next number
        doc_number = sequence.get_next_number()

        # Commit to release lock and persist increment
        await self.db.flush()

        return doc_number

    async def preview_next_number(
        self,
        document_type: str,
        financial_year: Optional[str] = None
    ) -> str:
        """
        Preview what the next number would be without incrementing.

        Args:
            document_type: Document type code
            financial_year: Optional FY string

        Returns:
            What the next document number would be
        """
        doc_type = document_type.upper()
        if doc_type not in DOCUMENT_METADATA:
            valid_types = ", ".join(DOCUMENT_METADATA.keys())
            raise ValueError(f"Invalid document type '{doc_type}'. Valid types: {valid_types}")

        if not financial_year:
            financial_year = DocumentSequence.get_financial_year()

        # Get sequence without locking
        result = await self.db.execute(
            select(DocumentSequence)
            .where(
                DocumentSequence.document_type == doc_type,
                DocumentSequence.financial_year == financial_year,
                DocumentSequence.is_active == True
            )
        )
        sequence = result.scalar_one_or_none()

        if sequence:
            return sequence.preview_next_number()

        # No sequence exists yet - would be first number
        metadata = DOCUMENT_METADATA[doc_type]
        padding = metadata["padding"]
        seq = "1".zfill(padding)
        return f"{doc_type}/{self.company_code}/{financial_year}/{seq}"

    async def get_current_number(
        self,
        document_type: str,
        financial_year: Optional[str] = None
    ) -> int:
        """
        Get the current (last used) sequence number.

        Args:
            document_type: Document type code
            financial_year: Optional FY string

        Returns:
            Current sequence number (0 if no sequence exists)
        """
        doc_type = document_type.upper()
        if not financial_year:
            financial_year = DocumentSequence.get_financial_year()

        result = await self.db.execute(
            select(DocumentSequence.current_number)
            .where(
                DocumentSequence.document_type == doc_type,
                DocumentSequence.financial_year == financial_year,
                DocumentSequence.is_active == True
            )
        )
        current = result.scalar_one_or_none()
        return current or 0

    async def initialize_sequence(
        self,
        document_type: str,
        starting_number: int = 0,
        financial_year: Optional[str] = None
    ) -> DocumentSequence:
        """
        Initialize or reset a sequence to a specific number.

        Use this to migrate existing data or correct sequences.

        Args:
            document_type: Document type code
            starting_number: Number to start from (next will be +1)
            financial_year: Optional FY string

        Returns:
            The sequence record
        """
        doc_type = document_type.upper()
        if doc_type not in DOCUMENT_METADATA:
            raise ValueError(f"Invalid document type: {doc_type}")

        if not financial_year:
            financial_year = DocumentSequence.get_financial_year()

        metadata = DOCUMENT_METADATA[doc_type]

        # Get existing or create new
        result = await self.db.execute(
            select(DocumentSequence)
            .where(
                DocumentSequence.document_type == doc_type,
                DocumentSequence.financial_year == financial_year
            )
            .with_for_update()
        )
        sequence = result.scalar_one_or_none()

        if sequence:
            sequence.current_number = starting_number
            sequence.is_active = True
        else:
            sequence = DocumentSequence(
                document_type=doc_type,
                document_name=metadata["name"],
                company_code=self.company_code,
                financial_year=financial_year,
                current_number=starting_number,
                padding_length=metadata["padding"],
            )
            self.db.add(sequence)

        await self.db.flush()
        return sequence

    async def _get_or_create_sequence(
        self,
        document_type: str,
        financial_year: str
    ) -> DocumentSequence:
        """
        Get existing sequence with row lock, or create new one.

        Uses SELECT FOR UPDATE for atomic operations.

        Args:
            document_type: Document type code
            financial_year: Financial year string

        Returns:
            DocumentSequence record (locked for update)
        """
        # Try to get existing sequence with lock
        result = await self.db.execute(
            select(DocumentSequence)
            .where(
                DocumentSequence.document_type == document_type,
                DocumentSequence.financial_year == financial_year,
                DocumentSequence.is_active == True
            )
            .with_for_update()
        )
        sequence = result.scalar_one_or_none()

        if sequence:
            return sequence

        # Create new sequence
        metadata = DOCUMENT_METADATA[document_type]
        sequence = DocumentSequence(
            document_type=document_type,
            document_name=metadata["name"],
            company_code=self.company_code,
            financial_year=financial_year,
            current_number=0,
            padding_length=metadata["padding"],
        )
        self.db.add(sequence)
        await self.db.flush()

        # Re-fetch with lock to ensure atomicity
        result = await self.db.execute(
            select(DocumentSequence)
            .where(DocumentSequence.id == sequence.id)
            .with_for_update()
        )
        return result.scalar_one()


# Convenience function for quick access
async def get_next_document_number(
    db: AsyncSession,
    document_type: str,
    company_code: str = "APL",
    financial_year: Optional[str] = None
) -> str:
    """
    Quick function to get next document number.

    Usage:
        pr_number = await get_next_document_number(db, "PR")
        po_number = await get_next_document_number(db, "PO")
    """
    service = DocumentSequenceService(db, company_code)
    return await service.get_next_number(document_type, financial_year)
