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

    # ==================== Non-Blocking Auto-Sync ====================

    @staticmethod
    async def fire_and_forget_sync(db: AsyncSession, entity_type: str, entity_id: uuid.UUID):
        """Non-blocking sync trigger. Logs failure but never raises."""
        if not settings.CJDQUICK_ENABLED:
            return
        try:
            svc = CJDQuickSyncService(db)
            if entity_type == "PRODUCT":
                await svc.sync_product(entity_id)
            elif entity_type == "ORDER":
                await svc.sync_order(entity_id)
            elif entity_type == "CUSTOMER":
                await svc.sync_customer(entity_id)
            elif entity_type == "PO":
                await svc.sync_purchase_order(entity_id)
            elif entity_type == "RETURN":
                await svc.sync_return(entity_id)
            elif entity_type == "GR":
                await svc.sync_goods_receipt_for_po(entity_id)
            await db.commit()
        except Exception as e:
            logger.warning("CJDQuick auto-sync failed for %s %s: %s", entity_type, entity_id, e)
            try:
                await db.rollback()
            except Exception:
                pass

    # ==================== Transformer Methods ====================

    def _build_sku_payload(self, product: Product) -> Dict[str, Any]:
        """Map Aquapurite Product fields to CJDQuick OMS SKU format.

        Per v3 guide: POST /skus uses fields: code, name, description, category,
        brand, mrp, costPrice, sellingPrice, weight, length, width, height,
        hsnCode, taxRate, isSerialized, hasBatchTracking, isActive, tags.
        """
        payload: Dict[str, Any] = {
            "code": product.sku,
            "name": product.name,
            "brand": "Aquapurite",
            "hsnCode": product.hsn_code or "",
            "mrp": _decimal_to_float(product.mrp),
            "costPrice": _decimal_to_float(product.cost_price),
            "sellingPrice": _decimal_to_float(product.selling_price),
            "taxRate": _decimal_to_float(product.gst_rate),
            "weight": _decimal_to_float(product.dead_weight_kg),
            "length": _decimal_to_float(product.length_cm),
            "width": _decimal_to_float(product.width_cm),
            "height": _decimal_to_float(product.height_cm),
            "isSerialized": True,
            "hasBatchTracking": False,
            "isActive": product.status == "ACTIVE",
        }
        if hasattr(product, "description") and product.description:
            payload["description"] = product.description
        # Add category from product's item_type
        item_type_category = {
            "FG": "Water Purifiers",
            "SP": "Spare Parts",
            "CO": "Components",
            "CN": "Consumables",
            "AC": "Accessories",
        }
        payload["category"] = item_type_category.get(
            getattr(product, "item_type", "FG") or "FG", "Water Purifiers"
        )
        return payload

    def _build_order_payload(self, order: Order, customer: Customer) -> Dict[str, Any]:
        """Map Aquapurite Order + Customer to CJDQuick OMS order format.

        Uses the direct /orders endpoint (JWT auth) since the integration endpoint's
        field mapping engine is not yet operational on CJDQuick's side.
        """
        # Build line items
        items = []
        if hasattr(order, "items") and order.items:
            for item in order.items:
                unit_price = _decimal_to_float(item.unit_price) or 0
                quantity = item.quantity or 1
                tax_amount = _decimal_to_float(item.tax_amount) or 0
                total_price = _decimal_to_float(item.total_amount) or (unit_price * quantity)
                discount = _decimal_to_float(item.discount_amount) or 0

                item_data: Dict[str, Any] = {
                    "externalItemId": item.product_sku,
                    "quantity": quantity,
                    "unitPrice": unit_price,
                    "taxAmount": tax_amount,
                    "totalPrice": total_price,
                }
                if discount:
                    item_data["discount"] = discount
                items.append(item_data)

        # Map payment method to OMS payment mode
        payment_mode = self._map_payment_method(order.payment_method)

        # Map order source to OMS channel
        channel = "D2C" if order.source == "WEBSITE" else (order.source or "D2C")

        # Build shipping address from JSONB
        shipping = order.shipping_address or {}
        customer_name = f"{customer.first_name} {customer.last_name or ''}".strip()

        return {
            "companyId": settings.CJDQUICK_COMPANY_ID,
            "externalOrderNo": order.order_number,
            "channel": channel,
            "paymentMode": payment_mode,
            "orderDate": order.created_at.isoformat() if order.created_at else None,
            "locationId": settings.CJDQUICK_LOCATION_ID,
            "customerName": customer_name,
            "customerPhone": customer.phone or "",
            "customerEmail": customer.email or "",
            "shippingAddress": {
                "name": shipping.get("name", shipping.get("contact_name", customer_name)),
                "phone": shipping.get("phone", shipping.get("contact_phone", customer.phone or "")),
                "address1": shipping.get("address", shipping.get("address_line1", shipping.get("address_line_1", ""))),
                "address2": shipping.get("address_2", shipping.get("address_line2", shipping.get("address_line_2", ""))),
                "city": shipping.get("city", ""),
                "state": shipping.get("state", ""),
                "pincode": str(shipping.get("pincode", shipping.get("zip_code", ""))),
                "country": shipping.get("country", "India"),
            },
            "items": items,
            "subtotal": _decimal_to_float(order.subtotal) or 0,
            "taxAmount": _decimal_to_float(order.tax_amount) or 0,
            "shippingCharges": _decimal_to_float(order.shipping_amount) if hasattr(order, "shipping_amount") else 0,
            "discount": _decimal_to_float(order.discount_amount) or 0,
            "totalAmount": _decimal_to_float(order.total_amount) or 0,
        }

    def _build_integration_order_payload(self, order: Order, customer: Customer) -> Dict[str, Any]:
        """Build order payload for POST /api/v1/orders/external.

        Per v3 guide: Uses X-API-Key auth. Complete payload reference with all
        required and optional fields. CJDQuick resolves SKU automatically.
        """
        customer_name = f"{customer.first_name} {customer.last_name or ''}".strip()
        shipping = order.shipping_address or {}

        items = []
        if hasattr(order, "items") and order.items:
            for item in order.items:
                items.append({
                    "sku": item.product_sku,
                    "name": item.product_name,
                    "quantity": item.quantity or 1,
                    "unitPrice": _decimal_to_float(item.unit_price) or 0,
                    "discount": _decimal_to_float(item.discount_amount) or 0,
                    "taxRate": _decimal_to_float(item.tax_rate) or 18.0,
                })

        payment_mode = self._map_payment_method(order.payment_method)

        payload: Dict[str, Any] = {
            # Required fields
            "externalOrderId": order.order_number,
            "customer": {
                "name": customer_name,
                "phone": customer.phone or "",
                "email": customer.email or "",
            },
            "shippingAddress": {
                "name": shipping.get("contact_name", shipping.get("name", customer_name)),
                "line1": shipping.get("address_line1", shipping.get("address_line_1", shipping.get("address", ""))),
                "line2": shipping.get("address_line2", shipping.get("address_line_2", shipping.get("address_2", ""))),
                "city": shipping.get("city", ""),
                "state": shipping.get("state", ""),
                "pincode": str(shipping.get("pincode", shipping.get("zip_code", ""))),
                "country": shipping.get("country", "India"),
                "phone": shipping.get("contact_phone", shipping.get("phone", customer.phone or "")),
            },
            "items": items,
            # Optional fields
            "channel": "AQUAPURITE_ERP",
            "orderDate": order.created_at.isoformat() if order.created_at else None,
            "paymentMode": payment_mode,
            "paymentStatus": "PAID" if order.payment_status == "PAID" else "PENDING",
            "charges": {
                "subtotal": _decimal_to_float(order.subtotal) or 0,
                "discount": _decimal_to_float(order.discount_amount) or 0,
                "shippingCharges": _decimal_to_float(order.shipping_amount) if hasattr(order, "shipping_amount") else 0,
                "codCharges": 0,
                "giftWrap": 0,
                "taxAmount": _decimal_to_float(order.tax_amount) or 0,
                "totalAmount": _decimal_to_float(order.total_amount) or 0,
            },
            "notes": getattr(order, "notes", "") or "",
            "tags": [],
            "isPriority": False,
            "preferredWarehouse": settings.CJDQUICK_WAREHOUSE_CODE,
        }
        return payload

    def _build_customer_payload(self, customer: Customer) -> Dict[str, Any]:
        """Map Aquapurite Customer to CJDQuick OMS customer format.

        API spec requires billingAddress (object) as mandatory field.
        """
        customer_name = f"{customer.first_name} {customer.last_name or ''}".strip()

        # Build billing address from customer's address data
        billing_address = {
            "name": customer_name,
            "phone": customer.phone or "",
            "address1": "",
            "city": "",
            "state": "",
            "pincode": "",
            "country": "India",
        }
        # Try to get address from customer model
        if hasattr(customer, "address") and customer.address:
            addr = customer.address if isinstance(customer.address, dict) else {}
            billing_address.update({
                "address1": addr.get("address", addr.get("address_line_1", "")),
                "address2": addr.get("address_2", addr.get("address_line_2", "")),
                "city": addr.get("city", ""),
                "state": addr.get("state", ""),
                "pincode": str(addr.get("pincode", addr.get("zip_code", ""))),
            })
        elif hasattr(customer, "city") and customer.city:
            billing_address.update({
                "address1": getattr(customer, "address_line_1", "") or "",
                "city": customer.city or "",
                "state": getattr(customer, "state", "") or "",
                "pincode": str(getattr(customer, "pincode", "") or ""),
            })

        return {
            "companyId": settings.CJDQUICK_COMPANY_ID,
            "code": customer.customer_code,
            "name": customer_name,
            "phone": customer.phone or "",
            "email": customer.email or "",
            "type": customer.customer_type or "RETAIL",
            "gst": customer.gst_number or "NA",
            "billingAddress": billing_address,
        }

    def _build_po_payload(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Map Aquapurite PurchaseOrder to CJDQuick OMS external-PO format.

        API endpoint: POST /external-pos
        Required fields: externalPoNumber, locationId, items[].externalSkuCode, items[].orderedQty
        """
        items = []
        if hasattr(po, "items") and po.items:
            for item in po.items:
                sku_code = ""
                sku_name = ""
                if hasattr(item, "product") and item.product:
                    sku_code = item.product.sku or ""
                    sku_name = item.product.name or ""

                item_data: Dict[str, Any] = {
                    "externalSkuCode": sku_code,
                    "externalSkuName": sku_name,
                    "orderedQty": item.quantity if hasattr(item, "quantity") else 0,
                }
                if hasattr(item, "unit_price") and item.unit_price:
                    item_data["unitPrice"] = _decimal_to_float(item.unit_price)
                items.append(item_data)

        payload: Dict[str, Any] = {
            "companyId": settings.CJDQUICK_COMPANY_ID,
            "externalPoNumber": po.po_number if hasattr(po, "po_number") else str(po.id),
            "locationId": settings.CJDQUICK_DELHI_LOCATION_ID,
            "items": items,
        }
        # Add vendor info if available
        if hasattr(po, "vendor") and po.vendor:
            payload["externalVendorCode"] = getattr(po.vendor, "vendor_code", "") or ""
            payload["externalVendorName"] = getattr(po.vendor, "name", "") or ""
        # Add dates
        if hasattr(po, "created_at") and po.created_at:
            payload["poDate"] = po.created_at.strftime("%Y-%m-%d")
        if hasattr(po, "expected_delivery_date") and po.expected_delivery_date:
            payload["expectedDeliveryDate"] = po.expected_delivery_date.strftime("%Y-%m-%d")

        return payload

    def _build_goods_receipt_payload(self, po: PurchaseOrder) -> Dict[str, Any]:
        """Build GRN creation payload per v3 guide.

        POST /api/v1/goods-receipts — creates DRAFT GRN.
        Per v3 guide: locationId, movementType, inboundSource, source,
        externalReferenceType, externalReferenceNo, notes.
        Items are added separately via POST /goods-receipts/{id}/items.
        """
        vendor_name = ""
        if hasattr(po, "vendor") and po.vendor:
            vendor_name = getattr(po.vendor, "name", "") or ""

        expected_date = ""
        if hasattr(po, "expected_delivery_date") and po.expected_delivery_date:
            expected_date = po.expected_delivery_date.strftime("%Y-%m-%d")

        notes = f"PO from Aquapurite ERP. Vendor: {vendor_name}."
        if expected_date:
            notes += f" Expected delivery: {expected_date}."

        return {
            "locationId": settings.CJDQUICK_DELHI_LOCATION_ID,
            "movementType": "101",
            "inboundSource": "PURCHASE",
            "source": "API",
            "externalReferenceType": "EXTERNAL_PO",
            "externalReferenceNo": po.po_number if hasattr(po, "po_number") else str(po.id),
            "notes": notes,
        }

    def _build_goods_receipt_item_payloads(self, po: PurchaseOrder, gr_id: str) -> list:
        """Build individual GRN item payloads per v3 guide.

        POST /goods-receipts/{gr_id}/items — one call per PO line item.
        Fields: goodsReceiptId, skuId (UUID from SKU sync), expectedQty, costPrice, mrp.
        """
        item_payloads = []
        if hasattr(po, "items") and po.items:
            for item in po.items:
                sku_code = ""
                if hasattr(item, "product") and item.product:
                    sku_code = item.product.sku or ""

                qty = item.quantity if hasattr(item, "quantity") else 0
                item_data: Dict[str, Any] = {
                    "goodsReceiptId": gr_id,
                    "expectedQty": qty,
                }
                # skuId needs to be the CJDQuick UUID — we pass code for resolution
                # The API resolves by code when skuId is not a UUID
                if sku_code:
                    item_data["skuCode"] = sku_code
                if hasattr(item, "unit_price") and item.unit_price:
                    item_data["costPrice"] = _decimal_to_float(item.unit_price)
                if hasattr(item, "product") and item.product:
                    item_data["mrp"] = _decimal_to_float(item.product.mrp)
                item_payloads.append(item_data)
        return item_payloads

    def _build_return_payload(self, return_order: ReturnOrder) -> Dict[str, Any]:
        """Map Aquapurite ReturnOrder to CJDQuick OMS return format.

        API spec requires: type (RTO/REPLACEMENT/REFUND/DAMAGE), orderId, reason, items[].skuId
        """
        items = []
        if hasattr(return_order, "items") and return_order.items:
            for item in return_order.items:
                item_data: Dict[str, Any] = {
                    "quantity": item.quantity if hasattr(item, "quantity") else 0,
                }
                # Use product_id as reference since we may not have OMS skuId
                if hasattr(item, "product_id") and item.product_id:
                    item_data["externalItemId"] = str(item.product_id)
                if hasattr(item, "reason") and item.reason:
                    item_data["reason"] = item.reason
                items.append(item_data)

        # Map return type
        return_type = "RTO"  # Default
        if hasattr(return_order, "return_type") and return_order.return_type:
            type_mapping = {
                "RTO": "RTO",
                "REPLACEMENT": "REPLACEMENT",
                "REFUND": "REFUND",
                "DAMAGE": "DAMAGE",
                "CUSTOMER_RETURN": "REFUND",
            }
            return_type = type_mapping.get(return_order.return_type, "RTO")

        return {
            "companyId": settings.CJDQUICK_COMPANY_ID,
            "type": return_type,
            "orderId": str(return_order.order_id),
            "reason": getattr(return_order, "reason", "") or "Customer return",
            "remarks": getattr(return_order, "rma_number", "") or "",
            "items": items,
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
        """Push a product to CJDQuick OMS as an SKU (upsert: create or update)."""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        payload = self._build_sku_payload(product)

        try:
            # Try create first
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
            logger.info("Product %s created in CJDQuick OMS: %s", product.sku, oms_id)
            return log
        except CJDQuickAPIError as e:
            if "already exists" in (e.message or "").lower():
                # SKU exists — update instead
                try:
                    existing = await self.client.get_sku_by_code(product.sku)
                    sku_id = str(existing.get("id") or existing.get("_id") or "")
                    if sku_id:
                        response = await self.client.update_sku(sku_id, payload)
                        log = await self._write_sync_log(
                            entity_type="PRODUCT",
                            entity_id=product_id,
                            operation="UPDATE",
                            status="SUCCESS",
                            request_payload=payload,
                            response_payload=response,
                            oms_id=sku_id,
                        )
                        logger.info("Product %s updated in CJDQuick OMS: %s", product.sku, sku_id)
                        return log
                except CJDQuickAPIError as update_err:
                    log = await self._write_sync_log(
                        entity_type="PRODUCT",
                        entity_id=product_id,
                        operation="UPDATE",
                        status="FAILED",
                        request_payload=payload,
                        error_message=update_err.message,
                    )
                    logger.error("Failed to update product %s: %s", product.sku, update_err.message)
                    raise

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
        """Push an order to CJDQuick OMS via the integration endpoint.

        Uses POST /api/v1/integration/orders with X-API-Key auth.
        Sends ERP's native JSON format — CJDQuick does field mapping server-side.
        """
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

        payload = self._build_integration_order_payload(order, customer)

        try:
            response = await self.client.push_integration_order(payload)
            oms_id = response.get("orderId") or response.get("orderNo")
            log = await self._write_sync_log(
                entity_type="ORDER",
                entity_id=order_id,
                operation="INTEGRATION_PUSH",
                status="SUCCESS",
                request_payload=payload,
                response_payload=response,
                oms_id=str(oms_id) if oms_id else None,
            )
            logger.info(
                "Order %s pushed to CJDQuick integration: %s (OMS: %s)",
                order.order_number, response.get("orderNo"), oms_id,
            )
            return log
        except CJDQuickAPIError as e:
            log = await self._write_sync_log(
                entity_type="ORDER",
                entity_id=order_id,
                operation="INTEGRATION_PUSH",
                status="FAILED",
                request_payload=payload,
                error_message=e.message,
            )
            logger.error("Failed to push order %s: %s", order.order_number, e.message)
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

    async def sync_goods_receipt_for_po(self, po_id: uuid.UUID) -> CJDQuickSyncLog:
        """Push a Goods Receipt to CJDQuick OMS for a PO (SAP MIGO equivalent).

        Per v3 guide — 2-step flow:
        1. POST /goods-receipts → creates DRAFT GRN
        2. POST /goods-receipts/{id}/items → add each PO line item

        Called on PO approval to notify the 3PL warehouse about incoming goods.
        """
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
                selectinload(PurchaseOrder.vendor),
            )
            .where(PurchaseOrder.id == po_id)
        )
        po = result.scalar_one_or_none()
        if not po:
            raise ValueError(f"PurchaseOrder {po_id} not found")

        gr_payload = self._build_goods_receipt_payload(po)

        try:
            # Step 1: Create DRAFT GRN
            gr_response = await self.client.create_goods_receipt(gr_payload)
            gr_id = str(gr_response.get("id") or gr_response.get("_id") or "")
            gr_no = gr_response.get("grNo", "")

            # Step 2: Add items individually
            item_payloads = self._build_goods_receipt_item_payloads(po, gr_id)
            items_added = 0
            for item_payload in item_payloads:
                try:
                    await self.client.add_goods_receipt_item(gr_id, item_payload)
                    items_added += 1
                except CJDQuickAPIError as item_err:
                    logger.warning("Failed to add GRN item for PO %s: %s", po.po_number, item_err.message)

            # Update PO with CJDQuick GR tracking
            po.cjdquick_gr_id = gr_id or None
            po.cjdquick_gr_status = "DRAFT"

            log = await self._write_sync_log(
                entity_type="GR",
                entity_id=po_id,
                operation="CREATE",
                status="SUCCESS",
                request_payload=gr_payload,
                response_payload={
                    "grId": gr_id,
                    "grNo": gr_no,
                    "itemsAdded": items_added,
                    "totalItems": len(item_payloads),
                },
                oms_id=gr_id or None,
            )
            logger.info("GR %s for PO %s synced to CJDQuick (%d/%d items)",
                         gr_no, po.po_number, items_added, len(item_payloads))
            return log
        except CJDQuickAPIError as e:
            po.cjdquick_gr_status = "FAILED"

            log = await self._write_sync_log(
                entity_type="GR",
                entity_id=po_id,
                operation="CREATE",
                status="FAILED",
                request_payload=gr_payload,
                error_message=e.message,
            )
            logger.error("Failed to sync GR for PO %s: %s", po.po_number, e.message)
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

    # ==================== Retry & Bulk Sync Methods ====================

    async def retry_failed_sync(self, log_id: uuid.UUID) -> CJDQuickSyncLog:
        """Retry a single failed sync log entry."""
        result = await self.db.execute(
            select(CJDQuickSyncLog).where(CJDQuickSyncLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            raise ValueError(f"Sync log {log_id} not found")
        if log.status != "FAILED":
            raise ValueError(f"Sync log {log_id} is not in FAILED status")

        # Re-dispatch based on entity_type
        if log.entity_type == "PRODUCT":
            return await self.sync_product(log.entity_id)
        elif log.entity_type == "ORDER":
            return await self.sync_order(log.entity_id)
        elif log.entity_type == "CUSTOMER":
            return await self.sync_customer(log.entity_id)
        elif log.entity_type == "PO":
            return await self.sync_purchase_order(log.entity_id)
        elif log.entity_type == "RETURN":
            return await self.sync_return(log.entity_id)
        elif log.entity_type == "GR":
            return await self.sync_goods_receipt_for_po(log.entity_id)
        else:
            raise ValueError(f"Unknown entity type: {log.entity_type}")

    async def retry_all_failed(self, max_retries: int = 3) -> dict:
        """Retry all failed sync logs (up to max_retries attempts each)."""
        result = await self.db.execute(
            select(CJDQuickSyncLog)
            .where(CJDQuickSyncLog.status == "FAILED")
            .where(CJDQuickSyncLog.retry_count < max_retries)
            .order_by(CJDQuickSyncLog.created_at)
            .limit(100)
        )
        failed_logs = result.scalars().all()

        success_count, fail_count = 0, 0
        for log in failed_logs:
            try:
                await self.retry_failed_sync(log.id)
                log.retry_count += 1
                log.status = "SUCCESS"
                success_count += 1
            except Exception:
                log.retry_count += 1
                fail_count += 1

        await self.db.commit()
        return {"retried": len(failed_logs), "success": success_count, "failed": fail_count}

    async def bulk_sync_products(self) -> dict:
        """Sync all active products to CJDQuick via external-sku-mappings/sync.

        Uses POST /api/v1/external-sku-mappings/sync with autoCreate: true.
        CJDQuick creates/maps SKUs using Aquapurite's own product codes.
        Falls back to individual SKU creation if the bulk endpoint fails.
        """
        result = await self.db.execute(
            select(Product).where(Product.status == "ACTIVE")
        )
        products = result.scalars().all()
        if not products:
            return {"total": 0, "success": 0, "failed": 0, "errors": []}

        # Build SKU array per v3 guide format for /external-sku-mappings/sync
        item_type_category = {
            "FG": "Water Purifiers", "SP": "Spare Parts",
            "CO": "Components", "CN": "Consumables", "AC": "Accessories",
        }
        skus = []
        for product in products:
            skus.append({
                "externalSkuCode": product.sku,
                "externalSkuName": product.name,
                "autoCreate": True,
                "category": item_type_category.get(
                    getattr(product, "item_type", "FG") or "FG", "Water Purifiers"
                ),
                "brand": "Aquapurite",
                "hsn": product.hsn_code or "",
                "mrp": _decimal_to_float(product.mrp),
                "costPrice": _decimal_to_float(product.cost_price),
                "sellingPrice": _decimal_to_float(product.selling_price),
                "weight": _decimal_to_float(product.dead_weight_kg),
            })

        try:
            response = await self.client.sync_sku_mappings(skus)
            synced = response.get("created", 0) + response.get("updated", 0)
            failed_count = response.get("failed", 0)

            # Log the bulk sync
            await self._write_sync_log(
                entity_type="PRODUCT",
                entity_id=uuid.uuid4(),  # Bulk operation — no single entity
                operation="BULK_SKU_SYNC",
                status="SUCCESS" if failed_count == 0 else "PARTIAL",
                request_payload={"count": len(mappings), "autoCreate": True},
                response_payload=response,
            )
            await self.db.commit()
            return {
                "total": len(products),
                "success": synced,
                "failed": failed_count,
                "errors": response.get("errors", []),
            }
        except CJDQuickAPIError as e:
            logger.warning("Bulk SKU sync endpoint failed (%s), falling back to individual sync", e.message)

            # Fallback: sync products individually via /skus
            success, failed = 0, 0
            errors = []
            for product in products:
                try:
                    await self.sync_product(product.id)
                    success += 1
                except Exception as ex:
                    failed += 1
                    errors.append({"sku": product.sku, "error": str(ex)})
                    logger.error("Bulk product sync failed for %s: %s", product.sku, ex)
            await self.db.commit()
            return {"total": len(products), "success": success, "failed": failed, "errors": errors}

    async def bulk_sync_orders(self, status_filter: str = "CONFIRMED") -> dict:
        """Push orders to CJDQuick OMS via the bulk external orders endpoint.

        Uses POST /api/v1/orders/external/bulk (max 100 per request).
        Falls back to individual pushes if bulk endpoint fails.
        """
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status == status_filter)
            .limit(100)
        )
        orders = result.scalars().all()
        if not orders:
            return {"total": 0, "success": 0, "failed": 0}

        # Build payloads for all orders
        payloads = []
        order_map = {}  # index -> order
        for i, order in enumerate(orders):
            cust_result = await self.db.execute(
                select(Customer).where(Customer.id == order.customer_id)
            )
            customer = cust_result.scalar_one_or_none()
            if not customer:
                logger.warning("Skipping order %s — customer not found", order.order_number)
                continue
            payload = self._build_integration_order_payload(order, customer)
            payloads.append(payload)
            order_map[len(payloads) - 1] = order

        if not payloads:
            return {"total": len(orders), "success": 0, "failed": len(orders)}

        # Try bulk push
        success, failed = 0, 0
        try:
            response = await self.client.push_integration_orders_bulk(payloads)
            total_created = response.get("totalCreated", 0)
            total_failed = response.get("totalFailed", 0)

            # Log individual results
            for order_result in response.get("orders", []):
                if order_result.get("success"):
                    ext_id = order_result.get("externalOrderId", "")
                    oms_id = order_result.get("orderId", "")
                    # Find matching order
                    for idx, o in order_map.items():
                        if o.order_number == ext_id:
                            await self._write_sync_log(
                                entity_type="ORDER",
                                entity_id=o.id,
                                operation="BULK_INTEGRATION_PUSH",
                                status="SUCCESS",
                                request_payload=payloads[idx],
                                response_payload=order_result,
                                oms_id=str(oms_id),
                            )
                            break

            success = total_created
            failed = total_failed
        except CJDQuickAPIError:
            # Bulk failed — fall back to individual pushes
            logger.warning("Bulk push failed, falling back to individual pushes")
            for order in orders:
                try:
                    await self.sync_order(order.id)
                    success += 1
                except Exception:
                    failed += 1

        await self.db.commit()
        return {"total": len(orders), "success": success, "failed": failed}

    async def get_sync_stats(self) -> dict:
        """Get sync health statistics."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                CJDQuickSyncLog.entity_type,
                CJDQuickSyncLog.status,
                func.count().label("count"),
            )
            .group_by(CJDQuickSyncLog.entity_type, CJDQuickSyncLog.status)
        )
        rows = result.all()

        by_entity: Dict[str, Dict[str, int]] = {}
        total_syncs, success_count, failed_count, pending_count = 0, 0, 0, 0

        for entity_type, sync_status, count in rows:
            if entity_type not in by_entity:
                by_entity[entity_type] = {}
            by_entity[entity_type][sync_status] = count
            total_syncs += count
            if sync_status == "SUCCESS":
                success_count += count
            elif sync_status == "FAILED":
                failed_count += count
            elif sync_status == "PENDING":
                pending_count += count

        # Get last sync timestamp
        last_sync_result = await self.db.execute(
            select(CJDQuickSyncLog.synced_at)
            .where(CJDQuickSyncLog.synced_at.isnot(None))
            .order_by(CJDQuickSyncLog.synced_at.desc())
            .limit(1)
        )
        last_sync_row = last_sync_result.scalar_one_or_none()

        return {
            "total_syncs": total_syncs,
            "success_count": success_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "by_entity": by_entity,
            "last_sync_at": last_sync_row,
        }
