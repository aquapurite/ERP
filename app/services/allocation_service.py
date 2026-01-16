"""
Allocation Service.

Order Allocation Engine that handles:
1. Channel-specific routing (Amazon → Amazon FBA warehouse)
2. Proximity-based allocation (nearest warehouse)
3. Inventory-based allocation (warehouse with stock)
4. Cost-optimized allocation (lowest shipping cost)
5. SLA-based allocation (fastest delivery)
6. Rate card-based carrier selection with pricing engine

Priority-Based Flow:
1. Get applicable allocation rules for the channel
2. For each rule (by priority), find matching warehouse
3. Check inventory availability
4. Select best transporter using pricing engine
5. Log allocation decision with cost breakdown
"""
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
import json

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.serviceability import (
    WarehouseServiceability,
    AllocationRule,
    AllocationLog,
    AllocationType,
    ChannelCode,
    AllocationPriority,
)
from app.models.transporter import Transporter, TransporterServiceability
from app.models.warehouse import Warehouse
from app.models.inventory import InventorySummary, StockItem, StockItemStatus
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.serviceability import (
    OrderAllocationRequest,
    AllocationDecision,
    WarehouseCandidate,
    AllocationRuleCreate,
    AllocationRuleUpdate,
    AllocationRuleResponse,
)

# Import pricing engine for rate card-based allocation
try:
    from app.services.pricing_engine import (
        PricingEngine,
        RateCalculationRequest,
        AllocationStrategy,
        CarrierQuote,
    )
    PRICING_ENGINE_AVAILABLE = True
except ImportError:
    PRICING_ENGINE_AVAILABLE = False


class AllocationService:
    """Service for allocating orders to warehouses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def allocate_order(
        self,
        request: OrderAllocationRequest
    ) -> AllocationDecision:
        """
        Main allocation engine.

        Flow:
        1. Get order details
        2. Check pincode serviceability
        3. Get applicable allocation rules
        4. For each rule, find matching warehouse
        5. Check stock availability
        6. Select transporter
        7. Log and return decision
        """
        order_id = request.order_id
        pincode = request.customer_pincode
        channel_code = request.channel_code or "D2C"

        # 1. Get order if exists
        order = await self._get_order(order_id)
        order_items = request.items or []
        product_ids = [item.get("product_id") for item in order_items if item.get("product_id")]

        if order:
            # Get product IDs from order items
            order_items_query = select(OrderItem).where(OrderItem.order_id == order_id)
            items_result = await self.db.execute(order_items_query)
            order_items_db = items_result.scalars().all()
            product_ids = [str(item.product_id) for item in order_items_db]

        # 2. Get applicable allocation rules
        rules = await self._get_allocation_rules(channel_code, request.payment_mode, request.order_value)

        if not rules:
            # Use default rule (NEAREST)
            rules = [AllocationRule(
                name="Default",
                channel_code=ChannelCode.ALL,
                allocation_type=AllocationType.NEAREST,
                priority=999
            )]

        # 3. Find serviceable warehouses
        serviceable_warehouses = await self._get_serviceable_warehouses(pincode)

        if not serviceable_warehouses:
            return await self._create_failed_allocation(
                order_id,
                pincode,
                None,
                "Location not serviceable - no warehouse covers this pincode"
            )

        # 4. Apply allocation rules
        selected_warehouse = None
        applied_rule = None
        decision_factors = {}

        for rule in rules:
            selected_warehouse, decision_factors = await self._apply_rule(
                rule,
                serviceable_warehouses,
                product_ids,
                pincode,
                request.payment_mode
            )

            if selected_warehouse:
                applied_rule = rule
                break

        if not selected_warehouse:
            # No warehouse found with available stock
            return await self._create_failed_allocation(
                order_id,
                pincode,
                rules[0].id if rules else None,
                "No warehouse has sufficient inventory",
                [self._ws_to_candidate(ws) for ws in serviceable_warehouses[:5]]
            )

        # 5. Find best transporter using pricing engine
        transporter, shipping_info = await self._select_transporter(
            selected_warehouse,
            pincode,
            payment_mode=request.payment_mode,
            weight_kg=request.weight_kg if hasattr(request, 'weight_kg') and request.weight_kg else 1.0,
            order_value=float(request.order_value) if request.order_value else 0,
            dimensions=request.dimensions if hasattr(request, 'dimensions') else None,
            allocation_strategy=request.allocation_strategy if hasattr(request, 'allocation_strategy') else "BALANCED"
        )

        # 6. Log allocation
        await self._log_allocation(
            order_id=order_id,
            rule_id=applied_rule.id if applied_rule and hasattr(applied_rule, 'id') else None,
            warehouse_id=selected_warehouse.warehouse_id,
            customer_pincode=pincode,
            is_successful=True,
            decision_factors=decision_factors,
            candidates=[self._ws_to_candidate(ws) for ws in serviceable_warehouses[:5]]
        )

        # 7. Update order if exists
        if order:
            await self._update_order_warehouse(order, selected_warehouse.warehouse_id)

        return AllocationDecision(
            order_id=order_id,
            is_allocated=True,
            warehouse_id=selected_warehouse.warehouse_id,
            warehouse_code=selected_warehouse.warehouse.code,
            warehouse_name=selected_warehouse.warehouse.name,
            is_split=False,
            rule_applied=applied_rule.name if applied_rule else "Default",
            allocation_type=applied_rule.allocation_type if applied_rule and hasattr(applied_rule.allocation_type, 'value') else "NEAREST",
            decision_factors=decision_factors,
            recommended_transporter_id=transporter.id if transporter else None,
            recommended_transporter_code=transporter.code if transporter else shipping_info.get("carrier_code") if shipping_info else None,
            recommended_transporter_name=transporter.name if transporter else shipping_info.get("carrier_name") if shipping_info else None,
            estimated_delivery_days=shipping_info.get("estimated_days") if shipping_info else selected_warehouse.estimated_days,
            estimated_delivery_days_min=shipping_info.get("estimated_days_min") if shipping_info else None,
            estimated_shipping_cost=shipping_info.get("rate") if shipping_info else selected_warehouse.shipping_cost,
            # Pricing engine details
            cost_breakdown=shipping_info.get("cost_breakdown") if shipping_info else None,
            rate_card_id=shipping_info.get("rate_card_id") if shipping_info else None,
            rate_card_code=shipping_info.get("rate_card_code") if shipping_info else None,
            allocation_score=shipping_info.get("allocation_score") if shipping_info else None,
            segment=shipping_info.get("segment") if shipping_info else None,
            zone=shipping_info.get("zone") if shipping_info else None,
            allocation_strategy=shipping_info.get("strategy") if shipping_info else None,
            alternative_carriers=shipping_info.get("alternatives") if shipping_info else None,
        )

    async def _get_order(self, order_id: uuid.UUID) -> Optional[Order]:
        """Get order by ID."""
        query = select(Order).where(Order.id == order_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_allocation_rules(
        self,
        channel_code: str,
        payment_mode: Optional[str] = None,
        order_value: Optional[Decimal] = None
    ) -> List[AllocationRule]:
        """Get applicable allocation rules sorted by priority."""
        query = (
            select(AllocationRule)
            .where(
                and_(
                    AllocationRule.is_active == True,
                    or_(
                        AllocationRule.channel_code == channel_code,
                        AllocationRule.channel_code == ChannelCode.ALL
                    )
                )
            )
            .order_by(AllocationRule.priority)
        )
        result = await self.db.execute(query)
        rules = result.scalars().all()

        # Filter by additional conditions
        filtered_rules = []
        for rule in rules:
            # Check payment mode
            if rule.payment_mode and payment_mode:
                if rule.payment_mode != payment_mode:
                    continue

            # Check order value range
            if order_value:
                if rule.min_order_value and order_value < Decimal(str(rule.min_order_value)):
                    continue
                if rule.max_order_value and order_value > Decimal(str(rule.max_order_value)):
                    continue

            filtered_rules.append(rule)

        return filtered_rules

    async def _get_serviceable_warehouses(
        self,
        pincode: str
    ) -> List[WarehouseServiceability]:
        """Get all serviceable warehouses for a pincode."""
        query = (
            select(WarehouseServiceability)
            .join(Warehouse)
            .where(
                and_(
                    WarehouseServiceability.pincode == pincode,
                    WarehouseServiceability.is_serviceable == True,
                    WarehouseServiceability.is_active == True,
                    Warehouse.is_active == True,
                    Warehouse.can_fulfill_orders == True
                )
            )
            .options(selectinload(WarehouseServiceability.warehouse))
            .order_by(WarehouseServiceability.priority)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _apply_rule(
        self,
        rule: AllocationRule,
        serviceable_warehouses: List[WarehouseServiceability],
        product_ids: List[str],
        customer_pincode: str,
        payment_mode: Optional[str] = None
    ) -> Tuple[Optional[WarehouseServiceability], Dict]:
        """Apply allocation rule and return selected warehouse."""
        decision_factors = {
            "rule_name": rule.name,
            "allocation_type": rule.allocation_type if hasattr(rule.allocation_type, 'value') else str(rule.allocation_type),
            "candidates_count": len(serviceable_warehouses)
        }

        # Filter by payment mode
        candidates = serviceable_warehouses
        if payment_mode == "COD":
            candidates = [ws for ws in candidates if ws.cod_available]
        elif payment_mode == "PREPAID":
            candidates = [ws for ws in candidates if ws.prepaid_available]

        if not candidates:
            decision_factors["failure"] = "No warehouse supports payment mode"
            return None, decision_factors

        # Handle FIXED allocation
        if rule.allocation_type == AllocationType.FIXED and rule.fixed_warehouse_id:
            for ws in candidates:
                if ws.warehouse_id == rule.fixed_warehouse_id:
                    # Check stock
                    has_stock = await self._check_stock(ws.warehouse_id, product_ids)
                    if has_stock:
                        decision_factors["selected_by"] = "FIXED_WAREHOUSE"
                        return ws, decision_factors
            decision_factors["failure"] = "Fixed warehouse doesn't have stock"
            return None, decision_factors

        # Get priority factors
        priority_factors = rule.get_priority_factors() if hasattr(rule, 'get_priority_factors') else ["PROXIMITY", "INVENTORY"]

        # Score each warehouse
        scored_candidates = []
        for ws in candidates:
            score = 0

            for factor in priority_factors:
                if factor == "PROXIMITY":
                    # Use priority (lower = better, so invert for scoring)
                    score += (1000 - ws.priority)
                elif factor == "INVENTORY":
                    has_stock = await self._check_stock(ws.warehouse_id, product_ids)
                    if has_stock:
                        score += 500
                elif factor == "COST":
                    if ws.shipping_cost:
                        # Lower cost = better
                        score += max(0, 100 - ws.shipping_cost)
                elif factor == "SLA":
                    if ws.estimated_days:
                        # Fewer days = better
                        score += max(0, 50 - (ws.estimated_days * 5))

            scored_candidates.append((ws, score))

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Select best candidate with stock
        for ws, score in scored_candidates:
            has_stock = await self._check_stock(ws.warehouse_id, product_ids)
            if has_stock or not product_ids:  # If no products specified, any warehouse works
                decision_factors["selected_by"] = priority_factors[0] if priority_factors else "PRIORITY"
                decision_factors["score"] = score
                return ws, decision_factors

        decision_factors["failure"] = "No candidate has sufficient inventory"
        return None, decision_factors

    async def _check_stock(
        self,
        warehouse_id: uuid.UUID,
        product_ids: List[str]
    ) -> bool:
        """Check if warehouse has stock for all products."""
        if not product_ids:
            return True

        for product_id in product_ids:
            try:
                pid = uuid.UUID(str(product_id))
            except ValueError:
                continue

            query = select(InventorySummary).where(
                and_(
                    InventorySummary.warehouse_id == warehouse_id,
                    InventorySummary.product_id == pid,
                    InventorySummary.available_quantity > 0
                )
            )
            result = await self.db.execute(query)
            if not result.scalar_one_or_none():
                return False

        return True

    async def _select_transporter(
        self,
        warehouse_serviceability: WarehouseServiceability,
        destination_pincode: str,
        payment_mode: Optional[str] = None,
        weight_kg: float = 1.0,
        order_value: float = 0,
        dimensions: Optional[Dict] = None,
        allocation_strategy: str = "BALANCED"
    ) -> Tuple[Optional[Transporter], Optional[Dict]]:
        """
        Select best transporter for the route.

        Uses pricing engine if available for rate card-based selection,
        falls back to TransporterServiceability otherwise.
        """
        warehouse = warehouse_serviceability.warehouse
        origin_pincode = warehouse.pincode

        # Try pricing engine first for rate card-based selection
        if PRICING_ENGINE_AVAILABLE:
            transporter, shipping_info = await self._select_transporter_with_pricing_engine(
                origin_pincode=origin_pincode,
                destination_pincode=destination_pincode,
                payment_mode=payment_mode,
                weight_kg=weight_kg,
                order_value=order_value,
                dimensions=dimensions,
                allocation_strategy=allocation_strategy
            )
            if transporter or shipping_info:
                return transporter, shipping_info

        # Fallback to TransporterServiceability
        return await self._select_transporter_legacy(
            origin_pincode=origin_pincode,
            destination_pincode=destination_pincode,
            payment_mode=payment_mode
        )

    async def _select_transporter_with_pricing_engine(
        self,
        origin_pincode: str,
        destination_pincode: str,
        payment_mode: Optional[str] = None,
        weight_kg: float = 1.0,
        order_value: float = 0,
        dimensions: Optional[Dict] = None,
        allocation_strategy: str = "BALANCED"
    ) -> Tuple[Optional[Transporter], Optional[Dict]]:
        """
        Select transporter using pricing engine and rate cards.

        Returns carrier with full cost breakdown and performance data.
        """
        try:
            engine = PricingEngine(self.db)

            # Build rate calculation request
            request = RateCalculationRequest(
                origin_pincode=origin_pincode,
                destination_pincode=destination_pincode,
                weight_kg=weight_kg,
                length_cm=dimensions.get("length") if dimensions else None,
                width_cm=dimensions.get("width") if dimensions else None,
                height_cm=dimensions.get("height") if dimensions else None,
                payment_mode=payment_mode or "PREPAID",
                order_value=order_value,
            )

            # Get allocation strategy enum
            strategy = AllocationStrategy.BALANCED
            if allocation_strategy == "CHEAPEST_FIRST":
                strategy = AllocationStrategy.CHEAPEST_FIRST
            elif allocation_strategy == "FASTEST_FIRST":
                strategy = AllocationStrategy.FASTEST_FIRST
            elif allocation_strategy == "BEST_SLA":
                strategy = AllocationStrategy.BEST_SLA

            # Allocate carrier
            result = await engine.allocate(request, strategy)

            if not result.get("success") or not result.get("allocation"):
                return None, None

            allocation = result["allocation"]
            carrier = allocation.get("carrier", {})

            # Get transporter from database
            transporter = None
            if carrier.get("id"):
                try:
                    transporter_id = uuid.UUID(carrier["id"])
                    query = select(Transporter).where(Transporter.id == transporter_id)
                    db_result = await self.db.execute(query)
                    transporter = db_result.scalar_one_or_none()
                except (ValueError, Exception):
                    pass

            # Build shipping info with full cost breakdown
            shipping_info = {
                "estimated_days": allocation.get("estimated_delivery", {}).get("max_days", 5),
                "estimated_days_min": allocation.get("estimated_delivery", {}).get("min_days", 2),
                "rate": allocation.get("total_cost", 0),
                "cost_breakdown": allocation.get("cost_breakdown", {}),
                "rate_card_id": allocation.get("rate_card_id"),
                "rate_card_code": allocation.get("rate_card_code"),
                "carrier_code": carrier.get("code"),
                "carrier_name": carrier.get("name"),
                "allocation_score": allocation.get("score", 0),
                "segment": result.get("segment"),
                "zone": result.get("zone"),
                "strategy": result.get("strategy"),
                "cod_available": payment_mode == "COD",
                "alternatives": result.get("alternatives", []),
            }

            return transporter, shipping_info

        except Exception as e:
            # Log error and fall back to legacy method
            import logging
            logging.warning(f"Pricing engine error: {e}, falling back to legacy method")
            return None, None

    async def _select_transporter_legacy(
        self,
        origin_pincode: str,
        destination_pincode: str,
        payment_mode: Optional[str] = None
    ) -> Tuple[Optional[Transporter], Optional[Dict]]:
        """Legacy transporter selection using TransporterServiceability."""
        query = (
            select(TransporterServiceability)
            .join(Transporter)
            .where(
                and_(
                    TransporterServiceability.origin_pincode == origin_pincode,
                    TransporterServiceability.destination_pincode == destination_pincode,
                    TransporterServiceability.is_serviceable == True,
                    Transporter.is_active == True
                )
            )
            .options(selectinload(TransporterServiceability.transporter))
            .order_by(TransporterServiceability.rate)  # Cheapest first
        )

        # Filter by payment mode
        if payment_mode == "COD":
            query = query.where(TransporterServiceability.cod_available == True)

        result = await self.db.execute(query)
        ts = result.scalars().first()

        if ts:
            return ts.transporter, {
                "estimated_days": ts.estimated_days,
                "rate": ts.rate,
                "cod_available": ts.cod_available,
                "source": "legacy_serviceability"
            }

        return None, None

    async def _log_allocation(
        self,
        order_id: uuid.UUID,
        rule_id: Optional[uuid.UUID],
        warehouse_id: Optional[uuid.UUID],
        customer_pincode: str,
        is_successful: bool,
        decision_factors: Dict = None,
        candidates: List[WarehouseCandidate] = None,
        failure_reason: str = None
    ):
        """Log allocation decision."""
        log = AllocationLog(
            order_id=order_id,
            rule_id=rule_id,
            warehouse_id=warehouse_id,
            customer_pincode=customer_pincode,
            is_successful=is_successful,
            failure_reason=failure_reason,
            decision_factors=json.dumps(decision_factors) if decision_factors else None,
            candidates_considered=json.dumps([c.model_dump(mode='json') for c in candidates]) if candidates else None
        )
        self.db.add(log)
        await self.db.commit()

    async def _update_order_warehouse(
        self,
        order: Order,
        warehouse_id: uuid.UUID
    ):
        """Update order with allocated warehouse."""
        order.warehouse_id = warehouse_id
        order.allocated_at = datetime.utcnow()
        # Update status to ALLOCATED for orders in NEW or CONFIRMED status
        if order.status in [OrderStatus.NEW, OrderStatus.CONFIRMED]:
            order.status = OrderStatus.ALLOCATED
            # Also mark as confirmed if it wasn't
            if not order.confirmed_at:
                order.confirmed_at = datetime.utcnow()
        await self.db.commit()

    async def _create_failed_allocation(
        self,
        order_id: uuid.UUID,
        pincode: str,
        rule_id: Optional[uuid.UUID],
        failure_reason: str,
        alternatives: List[WarehouseCandidate] = None
    ) -> AllocationDecision:
        """Create failed allocation response and log."""
        await self._log_allocation(
            order_id=order_id,
            rule_id=rule_id,
            warehouse_id=None,
            customer_pincode=pincode,
            is_successful=False,
            failure_reason=failure_reason,
            candidates=alternatives
        )

        return AllocationDecision(
            order_id=order_id,
            is_allocated=False,
            failure_reason=failure_reason,
            alternatives=alternatives
        )

    def _ws_to_candidate(self, ws: WarehouseServiceability) -> WarehouseCandidate:
        """Convert WarehouseServiceability to WarehouseCandidate."""
        return WarehouseCandidate(
            warehouse_id=ws.warehouse_id,
            warehouse_code=ws.warehouse.code,
            warehouse_name=ws.warehouse.name,
            city=ws.warehouse.city,
            estimated_days=ws.estimated_days,
            shipping_cost=ws.shipping_cost,
            priority=ws.priority,
            cod_available=ws.cod_available,
            prepaid_available=ws.prepaid_available
        )

    # ==================== Allocation Rule CRUD ====================

    async def create_rule(
        self,
        data: AllocationRuleCreate,
        created_by: Optional[uuid.UUID] = None
    ) -> AllocationRule:
        """Create an allocation rule."""
        rule = AllocationRule(
            name=data.name,
            description=data.description,
            channel_code=ChannelCode(data.channel_code) if data.channel_code else ChannelCode.ALL,
            channel_id=data.channel_id,
            priority=data.priority,
            allocation_type=AllocationType(data.allocation_type) if data.allocation_type else AllocationType.NEAREST,
            fixed_warehouse_id=data.fixed_warehouse_id,
            priority_factors=data.priority_factors,
            min_order_value=data.min_order_value,
            max_order_value=data.max_order_value,
            payment_mode=data.payment_mode,
            allow_split=data.allow_split,
            max_splits=data.max_splits,
            is_active=data.is_active,
            created_by=created_by
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_rules(
        self,
        channel_code: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[AllocationRule]:
        """Get allocation rules."""
        query = select(AllocationRule)

        conditions = []
        if channel_code:
            conditions.append(AllocationRule.channel_code == ChannelCode(channel_code))
        if is_active is not None:
            conditions.append(AllocationRule.is_active == is_active)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AllocationRule.priority)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_rule(self, rule_id: uuid.UUID) -> Optional[AllocationRule]:
        """Get allocation rule by ID."""
        query = select(AllocationRule).where(AllocationRule.id == rule_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        data: AllocationRuleUpdate
    ) -> Optional[AllocationRule]:
        """Update an allocation rule."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle enum conversions
        if "channel_code" in update_data and update_data["channel_code"]:
            update_data["channel_code"] = ChannelCode(update_data["channel_code"])
        if "allocation_type" in update_data and update_data["allocation_type"]:
            update_data["allocation_type"] = AllocationType(update_data["allocation_type"])

        for key, value in update_data.items():
            setattr(rule, key, value)

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        """Delete an allocation rule."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return False

        await self.db.delete(rule)
        await self.db.commit()
        return True

    # ==================== Allocation Logs ====================

    async def get_allocation_logs(
        self,
        order_id: Optional[uuid.UUID] = None,
        is_successful: Optional[bool] = None,
        limit: int = 100
    ) -> List[AllocationLog]:
        """Get allocation logs."""
        query = select(AllocationLog)

        conditions = []
        if order_id:
            conditions.append(AllocationLog.order_id == order_id)
        if is_successful is not None:
            conditions.append(AllocationLog.is_successful == is_successful)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AllocationLog.created_at)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
