"""
CJDQuick OMS Sync Service.

Transforms Aquapurite ERP data models into CJDQuick OMS API payloads
and orchestrates sync operations with audit logging.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.return_order import ReturnOrder, ReturnItem
from app.models.cjdquick_sync_log import CJDQuickSyncLog
from app.services.cjdquick_service import CJDQuickService, CJDQuickAPIError

logger = logging.getLogger(__name__)


def _decimal_to_float(val: Optional[Decimal]) -> Optional[float]:
    """Safely convert Decimal to float for JSON serialization."""
    if val is None:
        return None
    return float(val)


class CJDQuickSyncService:
    """Orchestrates data sync between Aquapurite ERP and CJDQuick OMS."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = CJDQuickService()

    # ==================== Transformer Methods ====================

    def _build_sku_payload(self, product: Product) -> Dict[str, Any]:
        """Map Aquapurite Product fields to CJDQuick OMS SKU format."""
        return {
            "code": product.sku,
            "name": product.name,
            "hsn": product.hsn_code or "",
            "mrp": _decimal_to_float(product.mrp),
            "costPrice": _decimal_to_float(product.cost_price),
            "sellingPrice": _decimal_to_float(product.selling_price),
            "taxRate": _decimal_to_float(product.gst_rate),
            "weight": _decimal_to_float(product.dead_weight_kg),
            "length": _decimal_to_float(product.length_cm),
            "width": _decimal_to_float(product.width_cm),
            "height": _decimal_to_float(product.height_cm),
            "status": "ACTIVE" if product.status == "ACTIVE" else "INACTIVE",
        }

    def _build_order_payload(self, order: Order, customer: Customer) -> Dict[str, Any]:
        """Map Aquapurite Order + Customer to CJDQuick OMS order format."""
        # Build line items
        items = []
        if hasattr(order, "items") and order.items:
            for item in order.items:
                items.append({
                    "sku": item.sku if hasattr(item, "sku") else "",
                    "name": item.product_name if hasattr(item, "product_name") else "",
                    "quantity": item.quantity,
                    "unitPrice": _decimal_to_float(item.unit_price) if hasattr(item, "unit_price") else 0,
                    "totalPrice": _decimal_to_float(item.total_price) if hasattr(item, "total_price") else 0,
                })

        # Map payment method to OMS payment mode
        payment_mode = self._map_payment_method(order.payment_method)

        # Map order source to OMS channel
        channel = "D2C" if order.source == "WEBSITE" else order.source

        # Build shipping address from JSONB
        shipping = order.shipping_address or {}

        return {
            "externalOrderNo": order.order_number,
            "channel": channel,
            "paymentMode": payment_mode,
            "orderDate": order.created_at.isoformat() if order.created_at else None,
            "customer": {
                "code": customer.customer_code,
                "name": f"{customer.first_name} {customer.last_name or ''}".strip(),
                "phone": customer.phone,
                "email": customer.email or "",
            },
            "shippingAddress": {
                "name": shipping.get("name", ""),
                "phone": shipping.get("phone", customer.phone),
                "address1": shipping.get("address", shipping.get("address_line_1", "")),
                "address2": shipping.get("address_2", shipping.get("address_line_2", "")),
                "city": shipping.get("city", ""),
                "state": shipping.get("state", ""),
                "pincode": shipping.get("pincode", shipping.get("zip_code", "")),
                "country": shipping.get("country", "India"),
            },
            "items": items,
            "subtotal": _decimal_to_float(order.subtotal),
            "taxAmount": _decimal_to_float(order.tax_amount),
            "shippingAmount": _decimal_to_float(order.shipping_amount),
            "discountAmount": _decimal_to_float(order.discount_amount),
            "totalAmount": _decimal_to_float(order.total_amount),
            "locationId": settings.CJDQUICK_LOCATION_ID or None,
        }

    def _build_customer_payload(self, customer: Customer) -> Dict[str, Any]:
        """Map Aquapurite Customer to CJDQuick OMS customer format."""
        return {
            "code": customer.customer_code,
            "name": f"{customer.first_name} {customer.last_name or ''}".strip(),
            "phone": customer.phone,
            "email": customer.email or "",
            "type": customer.customer_type,
            "gst": customer.gst_number or "",
        }

    def _build_po_payload(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Map Aquapurite PurchaseOrder to CJDQuick OMS external-PO format."""
        items = []
        if hasattr(po, "items") and po.items:
            for item in po.items:
                items.append({
                    "sku": item.product.sku if hasattr(item, "product") and item.product else "",
                    "quantity": item.quantity if hasattr(item, "quantity") else 0,
                    "unitPrice": _decimal_to_float(item.unit_price) if hasattr(item, "unit_price") else 0,
                })

        return {
            "externalPoNo": po.po_number if hasattr(po, "po_number") else str(po.id),
            "items": items,
            "locationId": settings.CJDQUICK_LOCATION_ID or None,
        }

    def _build_return_payload(self, return_order: ReturnOrder) -> Dict[str, Any]:
        """Map Aquapurite ReturnOrder to CJDQuick OMS return format."""
        items = []
        if hasattr(return_order, "items") and return_order.items:
            for item in return_order.items:
                items.append({
                    "sku": item.sku if hasattr(item, "sku") else "",
                    "quantity": item.quantity if hasattr(item, "quantity") else 0,
                    "reason": item.reason if hasattr(item, "reason") else "",
                })

        return {
            "rmaNumber": return_order.rma_number,
            "orderId": str(return_order.order_id),
            "items": items,
            "locationId": settings.CJDQUICK_LOCATION_ID or None,
        }

    # ==================== Status Mapping ====================

    @staticmethod
    def _map_payment_method(payment_method: str) -> str:
        """Map ERP payment method to OMS payment mode."""
        prepaid_methods = {"CARD", "UPI", "NET_BANKING", "WALLET", "EMI"}
        if payment_method in prepaid_methods:
            return "PREPAID"
        if payment_method == "COD":
            return "COD"
        if payment_method == "CREDIT":
            return "POSTPAID"
        return "PREPAID"

    @staticmethod
    def _map_oms_status_to_erp(oms_status: str) -> str:
        """Map CJDQuick OMS status to Aquapurite ERP OrderStatus."""
        mapping = {
            "NEW": "NEW",
            "CONFIRMED": "CONFIRMED",
            "PROCESSING": "ALLOCATED",
            "PICKING": "PICKING",
            "PICKED": "PICKED",
            "PACKED": "PACKED",
            "READY_TO_SHIP": "READY_TO_SHIP",
            "SHIPPED": "SHIPPED",
            "IN_TRANSIT": "IN_TRANSIT",
            "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
            "DELIVERED": "DELIVERED",
            "CANCELLED": "CANCELLED",
            "RTO_INITIATED": "RTO_INITIATED",
            "RTO_IN_TRANSIT": "RTO_IN_TRANSIT",
            "RTO_DELIVERED": "RTO_DELIVERED",
            "RETURNED": "RETURNED",
        }
        return mapping.get(oms_status, oms_status)

    # ==================== Sync Methods ====================

    async def _write_sync_log(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        operation: str,
        status: str,
        request_payload: Optional[Dict] = None,
        response_payload: Optional[Dict] = None,
        error_message: Optional[str] = None,
        oms_id: Optional[str] = None,
    ) -> CJDQuickSyncLog:
        """Write a sync log entry."""
        log = CJDQuickSyncLog(
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload,
            error_message=error_message,
            oms_id=oms_id,
            synced_at=datetime.now(timezone.utc) if status != "PENDING" else None,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def sync_product(self, product_id: uuid.UUID) -> CJDQuickSyncLog:
        """Push a product to CJDQuick OMS as an SKU."""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        payload = self._build_sku_payload(product)

        try:
            response = await self.client.create_sku(payload)
            oms_id = response.get("id") or response.get("_id") or response.get("code")
            log = await self._write_sync_log(
                entity_type="PRODUCT",
                entity_id=product_id,
                operation="CREATE",
                status="SUCCESS",
                request_payload=payload,
                response_payload=response,
                oms_id=str(oms_id) if oms_id else None,
            )
            logger.info("Product %s synced to CJDQuick OMS: %s", product.sku, oms_id)
            return log
        except CJDQuickAPIError as e:
            log = await self._write_sync_log(
                entity_type="PRODUCT",
                entity_id=product_id,
                operation="CREATE",
                status="FAILED",
                request_payload=payload,
                error_message=e.message,
            )
            logger.error("Failed to sync product %s: %s", product.sku, e.message)
            raise

    async def sync_order(self, order_id: uuid.UUID) -> CJDQuickSyncLog:
        """Push an order to CJDQuick OMS."""
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Fetch customer
        cust_result = await self.db.execute(
            select(Customer).where(Customer.id == order.customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        if not customer:
            raise ValueError(f"Customer {order.customer_id} not found for order {order_id}")

        payload = self._build_order_payload(order, customer)

        try:
            response = await self.client.create_order(payload)
            oms_id = response.get("id") or response.get("_id") or response.get("orderNo")
            log = await self._write_sync_log(
                entity_type="ORDER",
                entity_id=order_id,
                operation="CREATE",
                status="SUCCESS",
                request_payload=payload,
                response_payload=response,
                oms_id=str(oms_id) if oms_id else None,
            )
            logger.info("Order %s synced to CJDQuick OMS: %s", order.order_number, oms_id)
            return log
        except CJDQuickAPIError as e:
            log = await self._write_sync_log(
                entity_type="ORDER",
                entity_id=order_id,
                operation="CREATE",
                status="FAILED",
                request_payload=payload,
                error_message=e.message,
            )
            logger.error("Failed to sync order %s: %s", order.order_number, e.message)
            raise

    async def sync_customer(self, customer_id: uuid.UUID) -> CJDQuickSyncLog:
        """Push a customer to CJDQuick OMS."""
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        payload = self._build_customer_payload(customer)

        try:
            response = await self.client.create_customer(payload)
            oms_id = response.get("id") or response.get("_id") or response.get("code")
            log = await self._write_sync_log(
                entity_type="CUSTOMER",
                entity_id=customer_id,
                operation="CREATE",
                status="SUCCESS",
                request_payload=payload,
                response_payload=response,
                oms_id=str(oms_id) if oms_id else None,
            )
            logger.info("Customer %s synced to CJDQuick OMS: %s", customer.customer_code, oms_id)
            return log
        except CJDQuickAPIError as e:
            log = await self._write_sync_log(
                entity_type="CUSTOMER",
                entity_id=customer_id,
                operation="CREATE",
                status="FAILED",
                request_payload=payload,
                error_message=e.message,
            )
            logger.error("Failed to sync customer %s: %s", customer.customer_code, e.message)
            raise

    async def sync_purchase_order(self, po_id: uuid.UUID) -> CJDQuickSyncLog:
        """Push a Purchase Order to CJDQuick OMS."""
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product))
            .where(PurchaseOrder.id == po_id)
        )
        po = result.scalar_one_or_none()
        if not po:
            raise ValueError(f"PurchaseOrder {po_id} not found")

        payload = self._build_po_payload(po)

        try:
            response = await self.client.create_po(payload)
            oms_id = response.get("id") or response.get("_id") or response.get("poNo")
            log = await self._write_sync_log(
                entity_type="PO",
                entity_id=po_id,
                operation="CREATE",
                status="SUCCESS",
                request_payload=payload,
                response_payload=response,
                oms_id=str(oms_id) if oms_id else None,
            )
            logger.info("PO %s synced to CJDQuick OMS: %s", po_id, oms_id)
            return log
        except CJDQuickAPIError as e:
            log = await self._write_sync_log(
                entity_type="PO",
                entity_id=po_id,
                operation="CREATE",
                status="FAILED",
                request_payload=payload,
                error_message=e.message,
            )
            logger.error("Failed to sync PO %s: %s", po_id, e.message)
            raise

    async def sync_return(self, return_id: uuid.UUID) -> CJDQuickSyncLog:
        """Push a return order to CJDQuick OMS."""
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(ReturnOrder)
            .options(selectinload(ReturnOrder.items))
            .where(ReturnOrder.id == return_id)
        )
        return_order = result.scalar_one_or_none()
        if not return_order:
            raise ValueError(f"ReturnOrder {return_id} not found")

        payload = self._build_return_payload(return_order)

        try:
            response = await self.client.create_return(payload)
            oms_id = response.get("id") or response.get("_id") or response.get("returnNo")
            log = await self._write_sync_log(
                entity_type="RETURN",
                entity_id=return_id,
                operation="CREATE",
                status="SUCCESS",
                request_payload=payload,
                response_payload=response,
                oms_id=str(oms_id) if oms_id else None,
            )
            logger.info("Return %s synced to CJDQuick OMS: %s", return_order.rma_number, oms_id)
            return log
        except CJDQuickAPIError as e:
            log = await self._write_sync_log(
                entity_type="RETURN",
                entity_id=return_id,
                operation="CREATE",
                status="FAILED",
                request_payload=payload,
                error_message=e.message,
            )
            logger.error("Failed to sync return %s: %s", return_order.rma_number, e.message)
            raise
