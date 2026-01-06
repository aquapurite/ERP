"""
Serialization Service for Barcode Generation

Barcode Structure: APFSZAIEL000001 (15 characters)
- AP: Brand Prefix (Aquapurite)
- FS: Supplier Code (2 letters)
- Z: Year Code (A=2000, B=2001, ... Z=2025, AA=2026...)
- A: Month Code (A=Jan, B=Feb, ... L=Dec)
- IEL: Model Code (3+ letters)
- 000001: Serial Number (6 digits, 000001-999999)
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.serialization import (
    SerialSequence,
    POSerial,
    ModelCodeReference,
    SupplierCode,
    SerialStatus,
    ItemType,
)
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote
from app.models.product import Product
from app.models.inventory import StockItem
from app.schemas.serialization import (
    GenerateSerialsRequest,
    GenerateSerialItem,
    GenerateSerialsResponse,
    GeneratedSerialSummary,
    POSerialResponse,
    ScanSerialResponse,
    SequenceStatusResponse,
    CodePreviewResponse,
    FGCodeGenerateResponse,
)


class SerializationService:
    """Service for generating and managing product serial numbers/barcodes"""

    BRAND_PREFIX = "AP"  # Aquapurite

    # Year code mapping: A=2000, B=2001, ... Z=2025
    # After Z, we use AA=2026, AB=2027, etc.
    YEAR_BASE = 2000

    # Month code mapping: A=Jan, B=Feb, ... L=Dec
    MONTH_CODES = "ABCDEFGHIJKL"

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Year/Month Code Helpers ====================

    def get_year_code(self, year: int = None) -> str:
        """Convert year to code (A=2000, Z=2025, AA=2026, AB=2027...)"""
        if year is None:
            year = datetime.now().year

        offset = year - self.YEAR_BASE

        if offset < 0:
            raise ValueError(f"Year {year} is before base year {self.YEAR_BASE}")

        if offset <= 25:
            # Single letter A-Z
            return chr(65 + offset)  # A=65 in ASCII
        else:
            # Double letter AA, AB, AC...
            first = (offset - 26) // 26
            second = (offset - 26) % 26
            return chr(65 + first) + chr(65 + second)

    def get_month_code(self, month: int = None) -> str:
        """Convert month to code (A=Jan, L=Dec)"""
        if month is None:
            month = datetime.now().month

        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}")

        return self.MONTH_CODES[month - 1]

    def parse_year_code(self, code: str) -> int:
        """Parse year code back to year number"""
        if len(code) == 1:
            return self.YEAR_BASE + (ord(code.upper()) - 65)
        else:
            first = ord(code[0].upper()) - 65
            second = ord(code[1].upper()) - 65
            return self.YEAR_BASE + 26 + (first * 26) + second

    def parse_month_code(self, code: str) -> int:
        """Parse month code back to month number"""
        return self.MONTH_CODES.index(code.upper()) + 1

    # ==================== Barcode Generation ====================

    def generate_barcode(
        self,
        supplier_code: str,
        year_code: str,
        month_code: str,
        model_code: str,
        serial_number: int
    ) -> str:
        """
        Generate a barcode string.

        Format: APFSZAIEL000001
        - AP: Brand prefix
        - FS: Supplier code (2 letters)
        - Z: Year code
        - A: Month code
        - IEL: Model code (3+ letters)
        - 000001: Serial number (6 digits)
        """
        return f"{self.BRAND_PREFIX}{supplier_code.upper()}{year_code}{month_code}{model_code.upper()}{serial_number:06d}"

    def parse_barcode(self, barcode: str) -> Dict:
        """
        Parse a barcode into its components.

        Returns dict with: brand_prefix, supplier_code, year_code, month_code, model_code, serial_number
        """
        if len(barcode) < 14:
            raise ValueError(f"Invalid barcode length: {len(barcode)}, expected at least 14")

        # Brand prefix is first 2 chars
        brand_prefix = barcode[:2]

        # Supplier code is next 2 chars
        supplier_code = barcode[2:4]

        # Year code is 1-2 chars (check if double letter)
        if barcode[5].isalpha() and barcode[4].isalpha():
            # Double letter year code (AA, AB, etc.)
            year_code = barcode[4:6]
            remaining = barcode[6:]
        else:
            year_code = barcode[4]
            remaining = barcode[5:]

        # Month code is 1 char
        month_code = remaining[0]
        remaining = remaining[1:]

        # Serial is last 6 digits
        serial_number = int(remaining[-6:])

        # Model code is everything between month and serial
        model_code = remaining[:-6]

        return {
            "brand_prefix": brand_prefix,
            "supplier_code": supplier_code,
            "year_code": year_code,
            "month_code": month_code,
            "model_code": model_code,
            "serial_number": serial_number,
        }

    # ==================== Sequence Management ====================

    async def get_or_create_sequence(
        self,
        model_code: str,
        supplier_code: str,
        year_code: str = None,
        month_code: str = None,
        product_id: str = None,
        item_type: ItemType = ItemType.FINISHED_GOODS
    ) -> SerialSequence:
        """Get existing sequence or create new one"""

        if year_code is None:
            year_code = self.get_year_code()
        if month_code is None:
            month_code = self.get_month_code()

        # Try to find existing sequence
        result = await self.db.execute(
            select(SerialSequence).where(
                and_(
                    SerialSequence.model_code == model_code.upper(),
                    SerialSequence.supplier_code == supplier_code.upper(),
                    SerialSequence.year_code == year_code,
                    SerialSequence.month_code == month_code,
                )
            )
        )
        sequence = result.scalar_one_or_none()

        if sequence:
            return sequence

        # Create new sequence
        sequence = SerialSequence(
            id=str(uuid.uuid4()).replace("-", ""),
            model_code=model_code.upper(),
            supplier_code=supplier_code.upper(),
            year_code=year_code,
            month_code=month_code,
            product_id=product_id,
            item_type=item_type,
            last_serial=0,
            total_generated=0,
        )
        self.db.add(sequence)
        await self.db.flush()

        return sequence

    async def get_next_serial_range(
        self,
        sequence: SerialSequence,
        quantity: int
    ) -> Tuple[int, int]:
        """
        Reserve a range of serial numbers.

        Returns (start_serial, end_serial)
        """
        start_serial = sequence.last_serial + 1
        end_serial = start_serial + quantity - 1

        if end_serial > 999999:
            raise ValueError(
                f"Serial number overflow! Max is 999999, requested end: {end_serial}. "
                f"Current last serial for {sequence.supplier_code}/{sequence.model_code}: {sequence.last_serial}"
            )

        # Update sequence
        sequence.last_serial = end_serial
        sequence.total_generated += quantity
        sequence.updated_at = datetime.utcnow()

        return start_serial, end_serial

    # ==================== Serial Generation ====================

    async def generate_serials_for_po(
        self,
        request: GenerateSerialsRequest
    ) -> GenerateSerialsResponse:
        """
        Generate serial numbers for a Purchase Order.

        This is called when a PO is sent to the vendor.
        """
        year_code = self.get_year_code()
        month_code = self.get_month_code()

        all_barcodes = []
        item_summaries = []

        for item in request.items:
            # Get or create sequence for this model
            sequence = await self.get_or_create_sequence(
                model_code=item.model_code,
                supplier_code=request.supplier_code,
                year_code=year_code,
                month_code=month_code,
                product_id=item.product_id,
                item_type=item.item_type,
            )

            # Reserve serial range
            start_serial, end_serial = await self.get_next_serial_range(
                sequence, item.quantity
            )

            # Generate individual serial records
            item_barcodes = []
            for serial_num in range(start_serial, end_serial + 1):
                barcode = self.generate_barcode(
                    supplier_code=request.supplier_code,
                    year_code=year_code,
                    month_code=month_code,
                    model_code=item.model_code,
                    serial_number=serial_num,
                )

                po_serial = POSerial(
                    id=str(uuid.uuid4()).replace("-", ""),
                    po_id=request.po_id,
                    po_item_id=item.po_item_id,
                    product_id=item.product_id,
                    product_sku=item.product_sku,
                    model_code=item.model_code.upper(),
                    item_type=item.item_type,
                    brand_prefix=self.BRAND_PREFIX,
                    supplier_code=request.supplier_code.upper(),
                    year_code=year_code,
                    month_code=month_code,
                    serial_number=serial_num,
                    barcode=barcode,
                    status=SerialStatus.GENERATED,
                )
                self.db.add(po_serial)
                item_barcodes.append(barcode)

            all_barcodes.extend(item_barcodes)

            # Create summary for this item
            item_summaries.append(GeneratedSerialSummary(
                model_code=item.model_code.upper(),
                quantity=item.quantity,
                start_serial=start_serial,
                end_serial=end_serial,
                start_barcode=item_barcodes[0],
                end_barcode=item_barcodes[-1],
            ))

        await self.db.commit()

        return GenerateSerialsResponse(
            po_id=request.po_id,
            supplier_code=request.supplier_code.upper(),
            total_generated=len(all_barcodes),
            items=item_summaries,
            barcodes=all_barcodes,
        )

    # ==================== Serial Retrieval ====================

    async def get_serials_by_po(
        self,
        po_id: str,
        status: SerialStatus = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[POSerial]:
        """Get all serials for a PO"""
        query = select(POSerial).where(POSerial.po_id == po_id)

        if status:
            query = query.where(POSerial.status == status)

        query = query.order_by(POSerial.serial_number).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_serial_by_barcode(self, barcode: str) -> Optional[POSerial]:
        """Get serial details by barcode"""
        result = await self.db.execute(
            select(POSerial).where(POSerial.barcode == barcode.upper())
        )
        return result.scalar_one_or_none()

    async def get_serials_count_by_po(self, po_id: str) -> Dict[str, int]:
        """Get count of serials by status for a PO"""
        result = await self.db.execute(
            select(
                POSerial.status,
                func.count(POSerial.id).label("count")
            ).where(POSerial.po_id == po_id)
            .group_by(POSerial.status)
        )

        counts = {"total": 0}
        for row in result:
            counts[row.status.value] = row.count
            counts["total"] += row.count

        return counts

    # ==================== Serial Scanning (GRN) ====================

    async def scan_serial(
        self,
        barcode: str,
        grn_id: str,
        grn_item_id: str = None,
        user_id: str = None
    ) -> ScanSerialResponse:
        """
        Scan and validate a serial during GRN receiving.

        Marks the serial as RECEIVED if valid.
        """
        serial = await self.get_serial_by_barcode(barcode)

        if not serial:
            return ScanSerialResponse(
                barcode=barcode,
                is_valid=False,
                status=SerialStatus.GENERATED,
                message=f"Barcode {barcode} not found in system",
                serial_details=None,
            )

        # Check if already received
        if serial.status in [SerialStatus.RECEIVED, SerialStatus.ASSIGNED, SerialStatus.SOLD]:
            return ScanSerialResponse(
                barcode=barcode,
                is_valid=False,
                status=serial.status,
                message=f"Barcode already processed. Current status: {serial.status.value}",
                serial_details=POSerialResponse.model_validate(serial),
            )

        # Check if cancelled
        if serial.status == SerialStatus.CANCELLED:
            return ScanSerialResponse(
                barcode=barcode,
                is_valid=False,
                status=serial.status,
                message="Barcode has been cancelled",
                serial_details=POSerialResponse.model_validate(serial),
            )

        # Mark as received
        serial.status = SerialStatus.RECEIVED
        serial.grn_id = grn_id
        serial.grn_item_id = grn_item_id
        serial.received_at = datetime.utcnow()
        serial.received_by = user_id
        serial.updated_at = datetime.utcnow()

        await self.db.commit()

        return ScanSerialResponse(
            barcode=barcode,
            is_valid=True,
            status=SerialStatus.RECEIVED,
            message="Serial received successfully",
            serial_details=POSerialResponse.model_validate(serial),
        )

    async def bulk_scan_serials(
        self,
        barcodes: List[str],
        grn_id: str,
        user_id: str = None
    ) -> List[ScanSerialResponse]:
        """Scan multiple barcodes at once"""
        results = []
        for barcode in barcodes:
            result = await self.scan_serial(barcode, grn_id, user_id=user_id)
            results.append(result)
        return results

    # ==================== Serial Assignment (Stock) ====================

    async def assign_serial_to_stock(
        self,
        barcode: str,
        stock_item_id: str
    ) -> POSerial:
        """Assign a serial to a stock item"""
        serial = await self.get_serial_by_barcode(barcode)

        if not serial:
            raise ValueError(f"Barcode {barcode} not found")

        if serial.status != SerialStatus.RECEIVED:
            raise ValueError(
                f"Serial must be in RECEIVED status to assign. Current: {serial.status.value}"
            )

        serial.status = SerialStatus.ASSIGNED
        serial.stock_item_id = stock_item_id
        serial.assigned_at = datetime.utcnow()
        serial.updated_at = datetime.utcnow()

        await self.db.commit()
        return serial

    # ==================== Serial Sale ====================

    async def mark_serial_sold(
        self,
        barcode: str,
        order_id: str,
        order_item_id: str = None,
        customer_id: str = None,
        warranty_months: int = 12
    ) -> POSerial:
        """Mark a serial as sold and set warranty dates"""
        serial = await self.get_serial_by_barcode(barcode)

        if not serial:
            raise ValueError(f"Barcode {barcode} not found")

        if serial.status not in [SerialStatus.ASSIGNED, SerialStatus.RECEIVED]:
            raise ValueError(
                f"Serial must be in ASSIGNED or RECEIVED status to sell. Current: {serial.status.value}"
            )

        now = datetime.utcnow()
        serial.status = SerialStatus.SOLD
        serial.order_id = order_id
        serial.order_item_id = order_item_id
        serial.customer_id = customer_id
        serial.sold_at = now
        serial.warranty_start_date = now
        serial.warranty_end_date = datetime(
            now.year + (now.month + warranty_months - 1) // 12,
            (now.month + warranty_months - 1) % 12 + 1,
            now.day
        )
        serial.updated_at = now

        await self.db.commit()
        return serial

    # ==================== Sequence Status ====================

    async def get_sequence_status(
        self,
        model_code: str,
        supplier_code: str,
        year_code: str = None,
        month_code: str = None
    ) -> SequenceStatusResponse:
        """Get current status of a serial sequence"""

        if year_code is None:
            year_code = self.get_year_code()
        if month_code is None:
            month_code = self.get_month_code()

        sequence = await self.get_or_create_sequence(
            model_code=model_code,
            supplier_code=supplier_code,
            year_code=year_code,
            month_code=month_code,
        )

        next_barcode = self.generate_barcode(
            supplier_code=supplier_code,
            year_code=year_code,
            month_code=month_code,
            model_code=model_code,
            serial_number=sequence.last_serial + 1,
        )

        return SequenceStatusResponse(
            model_code=model_code.upper(),
            supplier_code=supplier_code.upper(),
            year_code=year_code,
            month_code=month_code,
            last_serial=sequence.last_serial,
            next_serial=sequence.last_serial + 1,
            total_generated=sequence.total_generated,
            next_barcode_preview=next_barcode,
        )

    # ==================== Code Preview ====================

    async def preview_codes(
        self,
        supplier_code: str,
        model_code: str,
        quantity: int = 5
    ) -> CodePreviewResponse:
        """Preview what codes would be generated without saving"""

        year_code = self.get_year_code()
        month_code = self.get_month_code()

        # Get current sequence to know where we'd start
        sequence = await self.get_or_create_sequence(
            model_code=model_code,
            supplier_code=supplier_code,
            year_code=year_code,
            month_code=month_code,
        )

        # Generate preview barcodes
        preview_barcodes = []
        for i in range(quantity):
            barcode = self.generate_barcode(
                supplier_code=supplier_code,
                year_code=year_code,
                month_code=month_code,
                model_code=model_code,
                serial_number=sequence.last_serial + 1 + i,
            )
            preview_barcodes.append(barcode)

        # Rollback any changes (we don't want to commit the sequence if it was newly created)
        await self.db.rollback()

        return CodePreviewResponse(
            supplier_code=supplier_code.upper(),
            model_code=model_code.upper(),
            year_code=year_code,
            month_code=month_code,
            current_last_serial=sequence.last_serial,
            preview_barcodes=preview_barcodes,
        )

    # ==================== FG Code Generation ====================

    async def generate_fg_code(
        self,
        category_code: str,  # WP
        subcategory_code: str,  # R
        brand_code: str,  # A
        model_name: str,  # IELITZ -> IEL
    ) -> FGCodeGenerateResponse:
        """
        Generate a new FG Code.

        Example: WPRAIEL001
        - WP: Water Purifier
        - R: RO
        - A: Aquapurite
        - IEL: Model code (first 3 letters of model name)
        - 001: Sequential number
        """
        # Extract model code (first 3 letters, uppercase)
        model_code = model_name[:3].upper()

        # Find the next available number for this prefix
        prefix = f"{category_code.upper()}{subcategory_code.upper()}{brand_code.upper()}{model_code}"

        result = await self.db.execute(
            select(ModelCodeReference)
            .where(ModelCodeReference.fg_code.like(f"{prefix}%"))
            .order_by(ModelCodeReference.fg_code.desc())
        )
        last_ref = result.scalar_one_or_none()

        if last_ref:
            # Extract number from last FG code
            last_num = int(last_ref.fg_code[-3:])
            next_num = last_num + 1
        else:
            next_num = 1

        fg_code = f"{prefix}{next_num:03d}"

        return FGCodeGenerateResponse(
            fg_code=fg_code,
            model_code=model_code,
            description=f"{category_code} {subcategory_code} {brand_code} {model_name}",
            next_available_number=next_num,
        )

    # ==================== Supplier Code Management ====================

    async def get_supplier_codes(self, active_only: bool = True) -> List[SupplierCode]:
        """Get all supplier codes"""
        query = select(SupplierCode)
        if active_only:
            query = query.where(SupplierCode.is_active == True)
        query = query.order_by(SupplierCode.code)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_supplier_code(
        self,
        code: str,
        name: str,
        vendor_id: str = None,
        description: str = None
    ) -> SupplierCode:
        """Create a new supplier code"""

        # Check if code already exists
        result = await self.db.execute(
            select(SupplierCode).where(SupplierCode.code == code.upper())
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Supplier code {code} already exists")

        supplier_code = SupplierCode(
            id=str(uuid.uuid4()).replace("-", ""),
            code=code.upper(),
            name=name,
            vendor_id=vendor_id,
            description=description,
            is_active=True,
        )
        self.db.add(supplier_code)
        await self.db.commit()

        return supplier_code

    # ==================== Model Code Management ====================

    async def get_model_codes(self, active_only: bool = True) -> List[ModelCodeReference]:
        """Get all model code references"""
        query = select(ModelCodeReference)
        if active_only:
            query = query.where(ModelCodeReference.is_active == True)
        query = query.order_by(ModelCodeReference.fg_code)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_model_code_reference(
        self,
        fg_code: str,
        model_code: str,
        item_type: ItemType = ItemType.FINISHED_GOODS,
        product_id: str = None,
        product_sku: str = None,
        description: str = None
    ) -> ModelCodeReference:
        """Create a new model code reference"""

        # Check if FG code already exists
        result = await self.db.execute(
            select(ModelCodeReference).where(ModelCodeReference.fg_code == fg_code.upper())
        )
        if result.scalar_one_or_none():
            raise ValueError(f"FG code {fg_code} already exists")

        model_ref = ModelCodeReference(
            id=str(uuid.uuid4()).replace("-", ""),
            fg_code=fg_code.upper(),
            model_code=model_code.upper(),
            item_type=item_type,
            product_id=product_id,
            product_sku=product_sku,
            description=description,
            is_active=True,
        )
        self.db.add(model_ref)
        await self.db.commit()

        return model_ref

    # ==================== Update PO Status ====================

    async def mark_serials_sent_to_vendor(self, po_id: str) -> int:
        """Mark all serials for a PO as sent to vendor"""
        result = await self.db.execute(
            select(POSerial).where(
                and_(
                    POSerial.po_id == po_id,
                    POSerial.status == SerialStatus.GENERATED
                )
            )
        )
        serials = result.scalars().all()

        count = 0
        for serial in serials:
            serial.status = SerialStatus.SENT_TO_VENDOR
            serial.updated_at = datetime.utcnow()
            count += 1

        await self.db.commit()
        return count

    async def cancel_serials(self, po_id: str, reason: str = None) -> int:
        """Cancel all unreceived serials for a PO"""
        result = await self.db.execute(
            select(POSerial).where(
                and_(
                    POSerial.po_id == po_id,
                    POSerial.status.in_([
                        SerialStatus.GENERATED,
                        SerialStatus.PRINTED,
                        SerialStatus.SENT_TO_VENDOR
                    ])
                )
            )
        )
        serials = result.scalars().all()

        count = 0
        for serial in serials:
            serial.status = SerialStatus.CANCELLED
            serial.notes = reason
            serial.updated_at = datetime.utcnow()
            count += 1

        await self.db.commit()
        return count
