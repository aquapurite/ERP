"""
Stock Reservation Service for D2C Storefront.

Prevents overselling by temporarily reserving stock when:
1. Customer proceeds to checkout
2. Customer initiates payment

Reservations auto-expire after TTL to prevent stuck inventory.
"""
import uuid
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventorySummary, StockItem
from app.services.cache_service import get_cache
from app.config import settings


# Reservation TTL in seconds (10 minutes default)
RESERVATION_TTL = 600


@dataclass
class ReservationItem:
    """Single item in a reservation."""
    product_id: str
    quantity: int
    warehouse_id: Optional[str] = None


@dataclass
class ReservationResult:
    """Result of a reservation attempt."""
    success: bool
    reservation_id: Optional[str] = None
    message: str = ""
    reserved_items: List[Dict] = None
    failed_items: List[Dict] = None

    def __post_init__(self):
        if self.reserved_items is None:
            self.reserved_items = []
        if self.failed_items is None:
            self.failed_items = []


class StockReservationService:
    """
    Manages temporary stock reservations for checkout process.

    Flow:
    1. create_reservation() - Called when customer clicks "Proceed to Checkout"
    2. confirm_reservation() - Called when payment succeeds
    3. release_reservation() - Called when payment fails/times out

    Uses Redis for fast reservation tracking with auto-expiry.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()

    def _reservation_key(self, reservation_id: str) -> str:
        """Generate cache key for reservation."""
        return f"stock:reservation:{reservation_id}"

    def _product_reserved_key(self, product_id: str) -> str:
        """Generate cache key for product's total reserved quantity."""
        return f"stock:reserved:{product_id}"

    async def check_availability(
        self,
        items: List[ReservationItem],
        channel: str = "D2C"
    ) -> Dict[str, Dict]:
        """
        Check stock availability for multiple items.
        Returns dict with product_id -> availability info.
        """
        result = {}

        for item in items:
            # Get inventory summary across all warehouses that can fulfill orders
            query = (
                select(
                    func.sum(InventorySummary.available_quantity).label('total_available'),
                    func.sum(InventorySummary.reserved_quantity).label('total_reserved'),
                )
                .join(
                    # Only warehouses that can fulfill orders
                    # This would join with warehouse table if needed
                )
                .where(InventorySummary.product_id == item.product_id)
            )

            # Simplified query without join for now
            query = (
                select(
                    func.sum(InventorySummary.available_quantity).label('total_available'),
                    func.sum(InventorySummary.reserved_quantity).label('total_reserved'),
                )
                .where(InventorySummary.product_id == item.product_id)
            )

            db_result = await self.db.execute(query)
            row = db_result.first()

            total_available = row.total_available or 0 if row else 0
            total_reserved = row.total_reserved or 0 if row else 0

            # Also get soft reservations from cache (checkout reservations)
            soft_reserved = await self._get_soft_reserved(item.product_id)

            # Actual available = DB available - DB reserved - soft reserved
            actual_available = total_available - total_reserved - soft_reserved

            result[item.product_id] = {
                "product_id": item.product_id,
                "requested": item.quantity,
                "available": max(0, actual_available),
                "is_available": actual_available >= item.quantity,
                "db_available": total_available,
                "db_reserved": total_reserved,
                "soft_reserved": soft_reserved,
            }

        return result

    async def _get_soft_reserved(self, product_id: str) -> int:
        """Get total soft-reserved quantity from cache."""
        key = self._product_reserved_key(product_id)
        value = await self.cache.get(key)
        return int(value) if value else 0

    async def _increment_soft_reserved(self, product_id: str, quantity: int) -> bool:
        """Increment soft-reserved quantity in cache."""
        key = self._product_reserved_key(product_id)
        current = await self._get_soft_reserved(product_id)
        new_value = current + quantity
        # Set with longer TTL than individual reservations to handle cleanup
        return await self.cache.set(key, new_value, ttl=RESERVATION_TTL + 60)

    async def _decrement_soft_reserved(self, product_id: str, quantity: int) -> bool:
        """Decrement soft-reserved quantity in cache."""
        key = self._product_reserved_key(product_id)
        current = await self._get_soft_reserved(product_id)
        new_value = max(0, current - quantity)
        if new_value == 0:
            await self.cache.delete(key)
            return True
        return await self.cache.set(key, new_value, ttl=RESERVATION_TTL + 60)

    async def create_reservation(
        self,
        items: List[ReservationItem],
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl: int = RESERVATION_TTL,
    ) -> ReservationResult:
        """
        Create a stock reservation for checkout.

        Args:
            items: List of products and quantities to reserve
            customer_id: Customer ID (for logged-in users)
            session_id: Session ID (for guests)
            ttl: Time-to-live in seconds (default 10 minutes)

        Returns:
            ReservationResult with reservation_id if successful
        """
        # Check availability first
        availability = await self.check_availability(items)

        reserved_items = []
        failed_items = []

        for item in items:
            avail = availability.get(item.product_id, {})
            if avail.get("is_available", False):
                reserved_items.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "warehouse_id": item.warehouse_id,
                })
            else:
                failed_items.append({
                    "product_id": item.product_id,
                    "requested": item.quantity,
                    "available": avail.get("available", 0),
                    "reason": "Insufficient stock",
                })

        if failed_items:
            return ReservationResult(
                success=False,
                message=f"{len(failed_items)} item(s) have insufficient stock",
                reserved_items=[],
                failed_items=failed_items,
            )

        # Create reservation
        reservation_id = str(uuid.uuid4())
        reservation_data = {
            "reservation_id": reservation_id,
            "customer_id": customer_id,
            "session_id": session_id,
            "items": reserved_items,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat(),
            "status": "ACTIVE",
        }

        # Store reservation in cache
        await self.cache.set(
            self._reservation_key(reservation_id),
            reservation_data,
            ttl=ttl
        )

        # Increment soft-reserved quantities
        for item in reserved_items:
            await self._increment_soft_reserved(item["product_id"], item["quantity"])

        return ReservationResult(
            success=True,
            reservation_id=reservation_id,
            message="Stock reserved successfully",
            reserved_items=reserved_items,
            failed_items=[],
        )

    async def get_reservation(self, reservation_id: str) -> Optional[Dict]:
        """Get reservation details by ID."""
        return await self.cache.get(self._reservation_key(reservation_id))

    async def confirm_reservation(
        self,
        reservation_id: str,
        order_id: str,
    ) -> bool:
        """
        Confirm a reservation after successful payment.
        Converts soft reservation to hard allocation.

        Args:
            reservation_id: The reservation to confirm
            order_id: The order ID to allocate stock to

        Returns:
            True if successful
        """
        reservation = await self.get_reservation(reservation_id)
        if not reservation:
            return False

        if reservation.get("status") != "ACTIVE":
            return False

        # Update reservation status
        reservation["status"] = "CONFIRMED"
        reservation["order_id"] = order_id
        reservation["confirmed_at"] = datetime.now(timezone.utc).isoformat()

        # Store updated reservation (short TTL since it's confirmed)
        await self.cache.set(
            self._reservation_key(reservation_id),
            reservation,
            ttl=300  # Keep for 5 minutes for audit
        )

        # Decrement soft-reserved (will be handled by actual allocation)
        for item in reservation.get("items", []):
            await self._decrement_soft_reserved(item["product_id"], item["quantity"])

        # TODO: Create actual stock allocation in database
        # This should call the allocation service to allocate specific stock items

        return True

    async def release_reservation(self, reservation_id: str) -> bool:
        """
        Release a reservation (payment failed/cancelled).

        Args:
            reservation_id: The reservation to release

        Returns:
            True if successful
        """
        reservation = await self.get_reservation(reservation_id)
        if not reservation:
            return False

        if reservation.get("status") != "ACTIVE":
            return False

        # Decrement soft-reserved quantities
        for item in reservation.get("items", []):
            await self._decrement_soft_reserved(item["product_id"], item["quantity"])

        # Delete the reservation
        await self.cache.delete(self._reservation_key(reservation_id))

        return True

    async def extend_reservation(
        self,
        reservation_id: str,
        additional_seconds: int = 300,
    ) -> bool:
        """
        Extend a reservation's TTL (e.g., when payment is processing).

        Args:
            reservation_id: The reservation to extend
            additional_seconds: Extra time to add (default 5 minutes)

        Returns:
            True if successful
        """
        reservation = await self.get_reservation(reservation_id)
        if not reservation:
            return False

        if reservation.get("status") != "ACTIVE":
            return False

        # Update expiry
        new_expiry = datetime.now(timezone.utc) + timedelta(seconds=additional_seconds)
        reservation["expires_at"] = new_expiry.isoformat()

        # Re-store with new TTL
        await self.cache.set(
            self._reservation_key(reservation_id),
            reservation,
            ttl=additional_seconds
        )

        return True


# ==================== API Helper Functions ====================

async def reserve_stock_for_checkout(
    db: AsyncSession,
    items: List[Dict],
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> ReservationResult:
    """
    Helper function to create stock reservation.

    Args:
        db: Database session
        items: List of {"product_id": str, "quantity": int}
        customer_id: Customer ID if logged in
        session_id: Session ID for tracking

    Returns:
        ReservationResult
    """
    service = StockReservationService(db)
    reservation_items = [
        ReservationItem(
            product_id=item["product_id"],
            quantity=item["quantity"],
            warehouse_id=item.get("warehouse_id"),
        )
        for item in items
    ]
    return await service.create_reservation(
        items=reservation_items,
        customer_id=customer_id,
        session_id=session_id,
    )


async def confirm_checkout_reservation(
    db: AsyncSession,
    reservation_id: str,
    order_id: str,
) -> bool:
    """Helper to confirm reservation after payment."""
    service = StockReservationService(db)
    return await service.confirm_reservation(reservation_id, order_id)


async def release_checkout_reservation(
    db: AsyncSession,
    reservation_id: str,
) -> bool:
    """Helper to release reservation on payment failure."""
    service = StockReservationService(db)
    return await service.release_reservation(reservation_id)
