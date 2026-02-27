"""
CJDQuick OMS Integration Service.

Handles all CJDQuick OMS/WMS API interactions:
- SKU management (product catalog sync)
- Order management (D2C & B2B)
- Purchase Orders & ASN
- Inventory queries and adjustments
- Customer management
- Returns processing
- Shipment tracking
- Invoice retrieval
- Webhook registration

API Base: https://lsp-oms-api.onrender.com/api/v1
Auth: Bearer token in Authorization header
Rate limit: 100 req/min (standard), 10 req/min (bulk)
"""

import httpx
import logging
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class CJDQuickAPIError(Exception):
    """Custom exception for CJDQuick API errors."""

    def __init__(self, status_code: int, message: str, errors: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.errors = errors or {}
        super().__init__(f"CJDQuick API Error {status_code}: {message}")


class CJDQuickService:
    """HTTP client for CJDQuick OMS API."""

    def __init__(self):
        self.api_key = settings.CJDQUICK_API_KEY
        self.base_url = settings.CJDQUICK_BASE_URL.rstrip("/")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to CJDQuick OMS API."""
        if not self.api_key:
            raise CJDQuickAPIError(
                status_code=401,
                message="CJDQUICK_API_KEY not configured. Set it in .env file.",
            )

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info("CJDQuick API %s %s", method.upper(), url)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                )

            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = {"detail": response.text}

                error_msg = error_body.get("message") or error_body.get("detail") or response.text
                logger.error(
                    "CJDQuick API error: %s %s -> %d: %s",
                    method.upper(),
                    endpoint,
                    response.status_code,
                    error_msg,
                )
                raise CJDQuickAPIError(
                    status_code=response.status_code,
                    message=str(error_msg),
                    errors=error_body.get("errors"),
                )

            return response.json()

        except httpx.TimeoutException:
            logger.error("CJDQuick API timeout: %s %s", method.upper(), endpoint)
            raise CJDQuickAPIError(
                status_code=504,
                message=f"Request to CJDQuick OMS timed out: {method.upper()} {endpoint}",
            )
        except httpx.RequestError as exc:
            logger.error("CJDQuick API connection error: %s %s - %s", method.upper(), endpoint, exc)
            raise CJDQuickAPIError(
                status_code=502,
                message=f"Connection error to CJDQuick OMS: {exc}",
            )

    # ==================== SKU Methods ====================

    async def create_sku(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SKU in CJDQuick OMS."""
        return await self._request("POST", "/skus", data=payload)

    async def update_sku(self, sku_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing SKU."""
        return await self._request("PUT", f"/skus/{sku_id}", data=payload)

    async def get_sku(self, sku_id: str) -> Dict[str, Any]:
        """Get SKU details by ID."""
        return await self._request("GET", f"/skus/{sku_id}")

    async def list_skus(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List SKUs with optional filters."""
        return await self._request("GET", "/skus", params=params)

    # ==================== Order Methods ====================

    async def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a D2C order in CJDQuick OMS."""
        return await self._request("POST", "/orders", data=payload)

    async def create_b2b_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a B2B order in CJDQuick OMS."""
        return await self._request("POST", "/orders/b2b", data=payload)

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details by ID."""
        return await self._request("GET", f"/orders/{order_id}")

    async def list_orders(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List orders with optional filters."""
        return await self._request("GET", "/orders", params=params)

    async def confirm_order(self, order_id: str) -> Dict[str, Any]:
        """Confirm an order in CJDQuick OMS."""
        return await self._request("POST", f"/orders/{order_id}/confirm")

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order in CJDQuick OMS."""
        return await self._request("POST", f"/orders/{order_id}/cancel")

    # ==================== Purchase Order Methods ====================

    async def create_po(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Purchase Order in CJDQuick OMS."""
        return await self._request("POST", "/purchase-orders", data=payload)

    async def get_po(self, po_id: str) -> Dict[str, Any]:
        """Get PO details by ID."""
        return await self._request("GET", f"/purchase-orders/{po_id}")

    async def list_pos(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List Purchase Orders with optional filters."""
        return await self._request("GET", "/purchase-orders", params=params)

    # ==================== ASN Methods ====================

    async def create_asn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create an Advanced Shipping Notice."""
        return await self._request("POST", "/asn", data=payload)

    # ==================== Inventory Methods ====================

    async def adjust_inventory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust inventory levels in CJDQuick OMS."""
        return await self._request("POST", "/inventory/adjust", data=payload)

    async def get_inventory(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get inventory details."""
        return await self._request("GET", "/inventory", params=params)

    async def get_inventory_summary(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get inventory summary/aggregates."""
        return await self._request("GET", "/inventory/summary", params=params)

    # ==================== Customer Methods ====================

    async def create_customer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer in CJDQuick OMS."""
        return await self._request("POST", "/customers", data=payload)

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details by ID."""
        return await self._request("GET", f"/customers/{customer_id}")

    # ==================== Return Methods ====================

    async def create_return(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a return request in CJDQuick OMS."""
        return await self._request("POST", "/returns", data=payload)

    async def get_return(self, return_id: str) -> Dict[str, Any]:
        """Get return details by ID."""
        return await self._request("GET", f"/returns/{return_id}")

    # ==================== Shipment Methods ====================

    async def get_shipments(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get shipment details with optional filters."""
        return await self._request("GET", "/shipments", params=params)

    # ==================== Invoice Methods ====================

    async def get_order_invoice(self, order_id: str) -> Dict[str, Any]:
        """Get invoice for a specific order."""
        return await self._request("GET", f"/orders/{order_id}/invoice")

    # ==================== Webhook Methods ====================

    async def register_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Register a webhook endpoint with CJDQuick OMS."""
        return await self._request("POST", "/webhooks", data=payload)

    async def list_webhooks(self) -> Dict[str, Any]:
        """List registered webhooks."""
        return await self._request("GET", "/webhooks")

    async def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Send a test event to a registered webhook."""
        return await self._request("POST", f"/webhooks/{webhook_id}/test")
