"""Batch Picking Service - FIFO/FEFO logic (SAP equivalent)."""
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import BatchMaster
from app.models.inventory import StockMovement


class BatchPickingService:
    """FIFO/FEFO batch picking logic - SAP equivalent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def pick_batches_fefo(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        quantity_needed: int,
    ) -> List[Dict[str, Any]]:
        """
        Pick batches using First Expiry First Out (FEFO) strategy.
        Returns list of {batch, pick_qty} dicts.
        """
        today = date.today()
        query = (
            select(BatchMaster)
            .where(
                and_(
                    BatchMaster.product_id == product_id,
                    BatchMaster.warehouse_id == warehouse_id,
                    BatchMaster.batch_status == "UNRESTRICTED",
                    BatchMaster.quantity_available > 0,
                )
            )
            .order_by(BatchMaster.expiry_date.asc().nullslast())
        )
        result = await self.db.execute(query)
        batches = result.scalars().all()

        picks = []
        remaining = quantity_needed

        for batch in batches:
            if remaining <= 0:
                break
            # Skip expired batches
            if batch.expiry_date and batch.expiry_date < today:
                continue

            pick_qty = min(batch.quantity_available, remaining)
            picks.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "pick_quantity": pick_qty,
                "quantity_available": batch.quantity_available,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "manufacturing_date": batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
                "quality_grade": batch.quality_grade,
                "days_until_expiry": (batch.expiry_date - today).days if batch.expiry_date else None,
            })
            remaining -= pick_qty

        return picks

    async def pick_batches_fifo(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        quantity_needed: int,
    ) -> List[Dict[str, Any]]:
        """
        Pick batches using First In First Out (FIFO) strategy.
        ORDER BY manufacturing_date ASC (oldest first).
        """
        today = date.today()
        query = (
            select(BatchMaster)
            .where(
                and_(
                    BatchMaster.product_id == product_id,
                    BatchMaster.warehouse_id == warehouse_id,
                    BatchMaster.batch_status == "UNRESTRICTED",
                    BatchMaster.quantity_available > 0,
                )
            )
            .order_by(BatchMaster.manufacturing_date.asc().nullslast())
        )
        result = await self.db.execute(query)
        batches = result.scalars().all()

        picks = []
        remaining = quantity_needed

        for batch in batches:
            if remaining <= 0:
                break
            # Skip expired batches
            if batch.expiry_date and batch.expiry_date < today:
                continue

            pick_qty = min(batch.quantity_available, remaining)
            picks.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "pick_quantity": pick_qty,
                "quantity_available": batch.quantity_available,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "manufacturing_date": batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
                "quality_grade": batch.quality_grade,
                "days_until_expiry": (batch.expiry_date - today).days if batch.expiry_date else None,
            })
            remaining -= pick_qty

        return picks

    async def check_batch_availability(
        self,
        product_id: UUID,
        warehouse_id: UUID,
        quantity_needed: int,
    ) -> Dict[str, Any]:
        """
        Check if enough unrestricted batch stock is available.
        Returns: {available: bool, total_available: int, shortfall: int, batches: [...]}
        """
        today = date.today()
        query = (
            select(BatchMaster)
            .where(
                and_(
                    BatchMaster.product_id == product_id,
                    BatchMaster.warehouse_id == warehouse_id,
                    BatchMaster.batch_status == "UNRESTRICTED",
                    BatchMaster.quantity_available > 0,
                )
            )
            .order_by(BatchMaster.expiry_date.asc().nullslast())
        )
        result = await self.db.execute(query)
        batches = result.scalars().all()

        total_available = 0
        batch_list = []
        for batch in batches:
            # Skip expired
            if batch.expiry_date and batch.expiry_date < today:
                continue
            total_available += batch.quantity_available
            batch_list.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "quantity_available": batch.quantity_available,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
            })

        shortfall = max(0, quantity_needed - total_available)
        return {
            "available": total_available >= quantity_needed,
            "total_available": total_available,
            "quantity_needed": quantity_needed,
            "shortfall": shortfall,
            "batches": batch_list,
        }

    async def reserve_batches(
        self,
        reservations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Reserve quantity from specific batches.
        Input: [{batch_id, quantity}]
        """
        results = []
        for res in reservations:
            batch = await self.db.get(BatchMaster, res["batch_id"])
            if not batch:
                results.append({"batch_id": str(res["batch_id"]), "error": "Batch not found"})
                continue
            if batch.quantity_available < res["quantity"]:
                results.append({
                    "batch_id": str(batch.id),
                    "error": f"Insufficient available qty. Available: {batch.quantity_available}, Requested: {res['quantity']}"
                })
                continue

            batch.quantity_available -= res["quantity"]
            batch.quantity_reserved += res["quantity"]
            batch.updated_at = datetime.now(timezone.utc)
            results.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "reserved": res["quantity"],
                "quantity_available": batch.quantity_available,
                "quantity_reserved": batch.quantity_reserved,
            })

        return results

    async def issue_batches(
        self,
        issues: List[Dict[str, Any]],
        user_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Issue stock from batches (after picking confirmed).
        Input: [{batch_id, quantity, reference_type, reference_id}]
        Creates StockMovement with batch_id.
        """
        results = []
        for issue in issues:
            batch = await self.db.get(BatchMaster, issue["batch_id"])
            if not batch:
                results.append({"batch_id": str(issue["batch_id"]), "error": "Batch not found"})
                continue

            qty = issue["quantity"]
            # Deduct from reserved first, then available
            if batch.quantity_reserved >= qty:
                batch.quantity_reserved -= qty
            else:
                # Partial from reserved, rest from available
                from_reserved = batch.quantity_reserved
                from_available = qty - from_reserved
                batch.quantity_reserved = 0
                batch.quantity_available -= from_available

            batch.quantity_issued += qty
            batch.updated_at = datetime.now(timezone.utc)

            # Recalculate total_value
            remaining_total = batch.quantity_available + batch.quantity_reserved
            batch.total_value = remaining_total * float(batch.unit_cost or 0)

            # Create stock movement
            import uuid as uuid_mod
            movement = StockMovement(
                id=uuid_mod.uuid4(),
                movement_number=f"BM-ISS-{uuid_mod.uuid4().hex[:8].upper()}",
                movement_type="ISSUE",
                warehouse_id=batch.warehouse_id,
                product_id=batch.product_id,
                quantity=-qty,
                batch_id=batch.id,
                batch_number=batch.batch_number,
                reference_type=issue.get("reference_type", "batch_issue"),
                reference_id=issue.get("reference_id"),
                unit_cost=float(batch.unit_cost or 0),
                total_cost=float(batch.unit_cost or 0) * qty,
                created_by=user_id,
                notes=f"Batch issue from {batch.batch_number}",
            )
            self.db.add(movement)

            results.append({
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "issued": qty,
                "quantity_available": batch.quantity_available,
                "quantity_reserved": batch.quantity_reserved,
                "quantity_issued": batch.quantity_issued,
            })

        return results
