"""Service for managing manifests and transporter handover operations."""
from typing import List, Optional, Tuple
from datetime import datetime
from math import ceil
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manifest import Manifest, ManifestItem, ManifestStatus, BusinessType
from app.models.shipment import Shipment, ShipmentStatus
from app.models.order import Order, OrderStatus
from app.models.transporter import Transporter
from app.schemas.manifest import ManifestCreate, ManifestUpdate


class ManifestService:
    """Service for manifest management and transporter handover."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== MANIFEST NUMBER GENERATION ====================

    async def generate_manifest_number(self) -> str:
        """Generate unique manifest number: MF-YYYYMMDD-XXXX"""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"MF-{today}-"

        stmt = select(func.count(Manifest.id)).where(
            Manifest.manifest_number.like(f"{prefix}%")
        )
        count = (await self.db.execute(stmt)).scalar() or 0

        return f"{prefix}{(count + 1):04d}"

    # ==================== MANIFEST CRUD ====================

    async def get_manifest(self, manifest_id: uuid.UUID) -> Optional[Manifest]:
        """Get manifest by ID with items."""
        stmt = (
            select(Manifest)
            .options(
                selectinload(Manifest.items),
                selectinload(Manifest.warehouse),
                selectinload(Manifest.transporter),
            )
            .where(Manifest.id == manifest_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_manifests(
        self,
        warehouse_id: Optional[uuid.UUID] = None,
        transporter_id: Optional[uuid.UUID] = None,
        status: Optional[ManifestStatus] = None,
        business_type: Optional[BusinessType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Manifest], int]:
        """Get paginated manifests with filters."""
        stmt = (
            select(Manifest)
            .options(
                selectinload(Manifest.transporter),
                selectinload(Manifest.warehouse)
            )
            .order_by(Manifest.created_at.desc())
        )

        filters = []
        if warehouse_id:
            filters.append(Manifest.warehouse_id == warehouse_id)
        if transporter_id:
            filters.append(Manifest.transporter_id == transporter_id)
        if status:
            filters.append(Manifest.status == status)
        if business_type:
            filters.append(Manifest.business_type == business_type)
        if date_from:
            filters.append(Manifest.manifest_date >= date_from)
        if date_to:
            filters.append(Manifest.manifest_date <= date_to)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Count
        count_stmt = select(func.count(Manifest.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Paginate
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create_manifest(
        self,
        data: ManifestCreate,
        created_by: Optional[uuid.UUID] = None
    ) -> Manifest:
        """Create new manifest."""
        manifest_number = await self.generate_manifest_number()

        manifest = Manifest(
            manifest_number=manifest_number,
            warehouse_id=data.warehouse_id,
            transporter_id=data.transporter_id,
            business_type=data.business_type,
            manifest_date=data.manifest_date or datetime.utcnow(),
            vehicle_number=data.vehicle_number,
            driver_name=data.driver_name,
            driver_phone=data.driver_phone,
            remarks=data.remarks,
            created_by=created_by,
            status=ManifestStatus.DRAFT,
        )

        self.db.add(manifest)
        await self.db.commit()
        await self.db.refresh(manifest)

        return manifest

    async def update_manifest(
        self,
        manifest_id: uuid.UUID,
        data: ManifestUpdate
    ) -> Manifest:
        """Update manifest."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status not in [ManifestStatus.DRAFT, ManifestStatus.PENDING]:
            raise ValueError(f"Cannot update manifest in {manifest.status} status")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(manifest, key, value)

        await self.db.commit()
        await self.db.refresh(manifest)
        return manifest

    # ==================== SHIPMENT MANAGEMENT ====================

    async def add_shipments(
        self,
        manifest_id: uuid.UUID,
        shipment_ids: List[uuid.UUID]
    ) -> Manifest:
        """Add shipments to manifest."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status not in [ManifestStatus.DRAFT, ManifestStatus.PENDING]:
            raise ValueError(f"Cannot add shipments to manifest in {manifest.status} status")

        # Get shipments
        stmt = select(Shipment).where(
            Shipment.id.in_(shipment_ids),
            Shipment.status == ShipmentStatus.PACKED,
            Shipment.manifest_id.is_(None)
        )
        result = await self.db.execute(stmt)
        shipments = list(result.scalars().all())

        if not shipments:
            raise ValueError("No valid shipments found to add")

        # Add to manifest
        for shipment in shipments:
            # Create manifest item
            manifest_item = ManifestItem(
                manifest_id=manifest.id,
                shipment_id=shipment.id,
                awb_number=shipment.awb_number or "",
                tracking_number=shipment.tracking_number,
                order_number=shipment.shipment_number,  # Will link to actual order
                weight_kg=shipment.weight_kg,
                no_of_boxes=shipment.no_of_boxes,
                destination_pincode=shipment.ship_to_pincode,
                destination_city=shipment.ship_to_city,
            )
            manifest.items.append(manifest_item)

            # Update shipment
            shipment.manifest_id = manifest.id
            shipment.status = ShipmentStatus.READY_FOR_PICKUP

        # Update manifest totals
        manifest.total_shipments = len(manifest.items)
        manifest.total_weight_kg = sum(item.weight_kg for item in manifest.items)
        manifest.total_boxes = sum(item.no_of_boxes for item in manifest.items)

        if manifest.status == ManifestStatus.DRAFT:
            manifest.status = ManifestStatus.PENDING

        await self.db.commit()
        await self.db.refresh(manifest)
        return manifest

    async def remove_shipments(
        self,
        manifest_id: uuid.UUID,
        shipment_ids: List[uuid.UUID]
    ) -> Manifest:
        """Remove shipments from manifest."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status not in [ManifestStatus.DRAFT, ManifestStatus.PENDING]:
            raise ValueError(f"Cannot remove shipments from manifest in {manifest.status} status")

        # Remove items
        items_to_remove = [
            item for item in manifest.items
            if item.shipment_id in shipment_ids
        ]

        for item in items_to_remove:
            # Update shipment
            stmt = select(Shipment).where(Shipment.id == item.shipment_id)
            result = await self.db.execute(stmt)
            shipment = result.scalar_one_or_none()
            if shipment:
                shipment.manifest_id = None
                shipment.status = ShipmentStatus.PACKED

            manifest.items.remove(item)
            await self.db.delete(item)

        # Update manifest totals
        manifest.total_shipments = len(manifest.items)
        manifest.total_weight_kg = sum(item.weight_kg for item in manifest.items)
        manifest.total_boxes = sum(item.no_of_boxes for item in manifest.items)

        await self.db.commit()
        await self.db.refresh(manifest)
        return manifest

    # ==================== SCANNING OPERATIONS ====================

    async def scan_shipment(
        self,
        manifest_id: uuid.UUID,
        awb_number: Optional[str] = None,
        shipment_id: Optional[uuid.UUID] = None,
        scanned_by: Optional[uuid.UUID] = None
    ) -> Tuple[ManifestItem, int, int]:
        """Scan shipment for handover confirmation."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status not in [ManifestStatus.PENDING, ManifestStatus.CONFIRMED]:
            raise ValueError(f"Cannot scan shipments in manifest {manifest.status} status")

        # Find item
        item = None
        for manifest_item in manifest.items:
            if awb_number and manifest_item.awb_number == awb_number:
                item = manifest_item
                break
            if shipment_id and manifest_item.shipment_id == shipment_id:
                item = manifest_item
                break

        if not item:
            raise ValueError("Shipment not found in manifest")

        if item.is_scanned:
            raise ValueError("Shipment already scanned")

        # Mark as scanned
        item.is_scanned = True
        item.scanned_at = datetime.utcnow()
        item.scanned_by = scanned_by

        # Update manifest counters
        manifest.scanned_shipments = sum(1 for i in manifest.items if i.is_scanned)

        await self.db.commit()

        total_scanned = manifest.scanned_shipments
        total_pending = manifest.total_shipments - total_scanned

        return item, total_scanned, total_pending

    # ==================== MANIFEST LIFECYCLE ====================

    async def confirm_manifest(
        self,
        manifest_id: uuid.UUID,
        vehicle_number: Optional[str] = None,
        driver_name: Optional[str] = None,
        driver_phone: Optional[str] = None,
        confirmed_by: Optional[uuid.UUID] = None,
        remarks: Optional[str] = None
    ) -> Manifest:
        """Confirm manifest for handover."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status != ManifestStatus.PENDING:
            raise ValueError(f"Cannot confirm manifest in {manifest.status} status")

        if manifest.total_shipments == 0:
            raise ValueError("Cannot confirm empty manifest")

        manifest.status = ManifestStatus.CONFIRMED
        manifest.confirmed_at = datetime.utcnow()
        manifest.confirmed_by = confirmed_by

        if vehicle_number:
            manifest.vehicle_number = vehicle_number
        if driver_name:
            manifest.driver_name = driver_name
        if driver_phone:
            manifest.driver_phone = driver_phone
        if remarks:
            manifest.remarks = remarks

        # Update shipments to MANIFESTED
        for item in manifest.items:
            stmt = select(Shipment).where(Shipment.id == item.shipment_id)
            result = await self.db.execute(stmt)
            shipment = result.scalar_one_or_none()
            if shipment:
                shipment.status = ShipmentStatus.MANIFESTED

        await self.db.commit()
        await self.db.refresh(manifest)
        return manifest

    async def complete_handover(
        self,
        manifest_id: uuid.UUID,
        handover_by: Optional[uuid.UUID] = None,
        remarks: Optional[str] = None
    ) -> Manifest:
        """Complete handover to transporter."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status != ManifestStatus.CONFIRMED:
            raise ValueError(f"Cannot complete handover for manifest in {manifest.status} status")

        # Check if all shipments are scanned
        if not manifest.all_scanned:
            raise ValueError(f"Cannot complete handover. {manifest.total_shipments - manifest.scanned_shipments} shipments not scanned")

        manifest.status = ManifestStatus.HANDED_OVER
        manifest.handover_at = datetime.utcnow()
        manifest.handover_by = handover_by

        if remarks:
            manifest.remarks = (manifest.remarks or "") + "\n" + remarks

        # Update shipments and orders
        for item in manifest.items:
            item.is_handed_over = True
            item.handed_over_at = datetime.utcnow()

            # Update shipment
            stmt = select(Shipment).where(Shipment.id == item.shipment_id)
            result = await self.db.execute(stmt)
            shipment = result.scalar_one_or_none()
            if shipment:
                shipment.status = ShipmentStatus.PICKED_UP
                shipment.shipped_at = datetime.utcnow()

                # Update order
                order_stmt = select(Order).where(Order.id == shipment.order_id)
                order_result = await self.db.execute(order_stmt)
                order = order_result.scalar_one_or_none()
                if order:
                    order.status = OrderStatus.SHIPPED
                    order.shipped_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(manifest)
        return manifest

    async def cancel_manifest(
        self,
        manifest_id: uuid.UUID,
        reason: str
    ) -> Manifest:
        """Cancel manifest."""
        manifest = await self.get_manifest(manifest_id)
        if not manifest:
            raise ValueError("Manifest not found")

        if manifest.status in [ManifestStatus.HANDED_OVER, ManifestStatus.IN_TRANSIT, ManifestStatus.COMPLETED, ManifestStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel manifest in {manifest.status} status")

        manifest.status = ManifestStatus.CANCELLED
        manifest.cancelled_at = datetime.utcnow()
        manifest.cancellation_reason = reason

        # Revert shipments
        for item in manifest.items:
            stmt = select(Shipment).where(Shipment.id == item.shipment_id)
            result = await self.db.execute(stmt)
            shipment = result.scalar_one_or_none()
            if shipment:
                shipment.manifest_id = None
                shipment.status = ShipmentStatus.PACKED

        await self.db.commit()
        await self.db.refresh(manifest)
        return manifest
