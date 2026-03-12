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
Auth: JWT Bearer token (auto-refreshed via email/password login)
Rate limit: 100 req/min (standard), 10 req/min (bulk)
"""

import httpx
import logging
import time
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
    """HTTP client for CJDQuick OMS API with JWT auto-refresh."""

    # Class-level token cache (shared across all instances)
    _cached_token: Optional[str] = None
    _token_expires_at: float = 0

    def __init__(self):
        self.base_url = settings.CJDQUICK_BASE_URL.rstrip("/")
        self.email = settings.CJDQUICK_EMAIL
        self.password = settings.CJDQUICK_PASSWORD

    async def _get_token(self) -> str:
        """Get a valid JWT token, logging in or refreshing as needed."""
        now = time.time()

        # Return cached token if still valid (with 60s buffer)
        if CJDQuickService._cached_token and now < (CJDQuickService._token_expires_at - 60):
            return CJDQuickService._cached_token

        # Try refresh if we have an existing token
        if CJDQuickService._cached_token:
            try:
                token_data = await self._refresh_token()
                CJDQuickService._cached_token = token_data["token"]
                CJDQuickService._token_expires_at = now + token_data.get("expiresIn", 3600)
                logger.info("CJDQuick JWT token refreshed successfully")
                return CJDQuickService._cached_token
            except Exception:
                logger.warning("CJDQuick token refresh failed, re-logging in")

        # Login with email/password
        token_data = await self._login()
        CJDQuickService._cached_token = token_data["token"]
        CJDQuickService._token_expires_at = now + token_data.get("expiresIn", 3600)
        logger.info("CJDQuick JWT login successful")
        return CJDQuickService._cached_token

    async def _login(self) -> Dict[str, Any]:
        """Login to CJDQuick OMS and get JWT token."""
        if not self.email or not self.password:
            raise CJDQuickAPIError(
                status_code=401,
                message="CJDQUICK_EMAIL and CJDQUICK_PASSWORD not configured.",
            )

        url = f"{self.base_url}/auth/login"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    json={"email": self.email, "password": self.password},
                    headers={"Content-Type": "application/json"},
                )
            if response.status_code >= 400:
                raise CJDQuickAPIError(
                    status_code=response.status_code,
                    message=f"CJDQuick login failed: {response.text}",
                )
            return response.json()
        except httpx.RequestError as exc:
            raise CJDQuickAPIError(
                status_code=502,
                message=f"CJDQuick login connection error: {exc}",
            )

    async def _refresh_token(self) -> Dict[str, Any]:
        """Refresh the JWT token."""
        url = f"{self.base_url}/auth/refresh"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {CJDQuickService._cached_token}",
                    "Content-Type": "application/json",
                },
            )
        if response.status_code >= 400:
            raise CJDQuickAPIError(
                status_code=response.status_code,
                message="Token refresh failed",
            )
        return response.json()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to CJDQuick OMS API."""
        token = await self._get_token()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {token}",
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

            # If 401, clear cached token and retry once
            if response.status_code == 401:
                logger.warning("CJDQuick API 401 - clearing token cache and retrying")
                CJDQuickService._cached_token = None
                CJDQuickService._token_expires_at = 0
                token = await self._get_token()
                headers["Authorization"] = f"Bearer {token}"
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

    # ==================== Integration Endpoints (X-API-Key Auth) ====================

    async def _integration_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Make an API-key-authenticated request to CJDQuick integration endpoints.

        Uses X-API-Key header (not JWT Bearer).
        Per updated integration guide: POST /api/v1/integration/orders
        """
        if not settings.CJDQUICK_API_KEY:
            raise CJDQuickAPIError(
                status_code=401,
                message="CJDQUICK_API_KEY not configured. Get it from CJDQuick admin.",
            )

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "X-API-Key": settings.CJDQUICK_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info("CJDQuick Integration API %s %s", method.upper(), url)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                )

            # 207 Multi-Status is valid for bulk (partial success)
            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = {"detail": response.text}

                error_msg = error_body.get("detail") or error_body.get("message") or response.text
                logger.error(
                    "CJDQuick Integration error: %s %s -> %d: %s",
                    method.upper(), endpoint, response.status_code, error_msg,
                )
                raise CJDQuickAPIError(
                    status_code=response.status_code,
                    message=str(error_msg),
                    errors=error_body.get("errors"),
                )

            return response.json()

        except httpx.TimeoutException:
            logger.error("CJDQuick Integration timeout: %s %s", method.upper(), endpoint)
            raise CJDQuickAPIError(
                status_code=504,
                message=f"Integration request timed out: {method.upper()} {endpoint}",
            )
        except httpx.RequestError as exc:
            logger.error("CJDQuick Integration connection error: %s", exc)
            raise CJDQuickAPIError(
                status_code=502,
                message=f"Connection error to CJDQuick: {exc}",
            )

    async def push_integration_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Push a single order via the external orders endpoint.

        POST /api/v1/orders/external
        Uses X-API-Key auth. CJDQuick resolves SKUs automatically using Aquapurite's product codes.
        """
        return await self._integration_request("POST", "/orders/external", data=payload)

    async def push_integration_orders_bulk(self, orders: list) -> Dict[str, Any]:
        """Push up to 100 orders via the bulk integration endpoint.

        POST /api/v1/orders/external/bulk
        Each order processed independently — one failure doesn't roll back others.
        """
        if len(orders) > 100:
            raise ValueError("Maximum 100 orders per bulk request")
        return await self._integration_request(
            "POST", "/orders/external/bulk",
            data={"orders": orders},
            timeout=60.0,
        )

    # ==================== SKU Sync (External SKU Mappings) ====================

    async def sync_sku_mappings(self, skus: list) -> Dict[str, Any]:
        """Push product catalog to CJDQuick via external SKU mappings sync.

        POST /api/v1/external-sku-mappings/sync
        Uses X-API-Key auth. Per v3 guide: sends externalSystem, integrationProfileId,
        and skus array with autoCreate: true per SKU.
        """
        return await self._integration_request(
            "POST", "/external-sku-mappings/sync",
            data={
                "externalSystem": "AQUAPURITE",
                "integrationProfileId": settings.CJDQUICK_INTEGRATION_PROFILE_ID,
                "skus": skus,
            },
            timeout=60.0,
        )

    # ==================== SKU Methods (X-API-Key auth per v3 guide) ====================

    async def create_sku(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SKU in CJDQuick OMS. POST /api/v1/skus"""
        return await self._integration_request("POST", "/skus", data=payload)

    async def update_sku(self, sku_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing SKU."""
        return await self._integration_request("PATCH", f"/skus/{sku_id}", data=payload)

    async def get_sku(self, sku_id: str) -> Dict[str, Any]:
        """Get SKU details by ID."""
        return await self._integration_request("GET", f"/skus/{sku_id}")

    async def get_sku_by_code(self, code: str) -> Dict[str, Any]:
        """Get SKU by code."""
        return await self._integration_request("GET", f"/skus/code/{code}")

    async def list_skus(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List SKUs with optional filters."""
        return await self._integration_request("GET", "/skus", params=params)

    # ==================== Order Methods ====================

    async def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a D2C order in CJDQuick OMS."""
        return await self._request("POST", "/orders", data=payload)

    async def create_b2b_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a B2B order in CJDQuick OMS."""
        return await self._request("POST", "/b2b/orders", data=payload)

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
        return await self._request("POST", "/external-pos", data=payload)

    async def get_po(self, po_id: str) -> Dict[str, Any]:
        """Get PO details by ID."""
        return await self._request("GET", f"/external-pos/{po_id}")

    async def list_pos(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List Purchase Orders with optional filters."""
        return await self._request("GET", "/external-pos", params=params)

    # ==================== Goods Receipt Methods (X-API-Key auth per v3 guide) ====================

    async def create_goods_receipt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Goods Receipt in CJDQuick OMS (SAP MIGO equivalent).

        POST /api/v1/goods-receipts — creates DRAFT GRN, then items added separately.
        """
        return await self._integration_request("POST", "/goods-receipts", data=payload)

    async def add_goods_receipt_item(self, gr_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single item to an existing Goods Receipt.

        POST /api/v1/goods-receipts/{gr_id}/items — one call per PO line item.
        """
        return await self._integration_request("POST", f"/goods-receipts/{gr_id}/items", data=payload)

    async def update_goods_receipt(self, gr_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update GRN with vehicle/dispatch info (Step 3 in inbound flow).

        PATCH /api/v1/goods-receipts/{gr_id}
        """
        return await self._integration_request("PATCH", f"/goods-receipts/{gr_id}", data=payload)

    async def post_goods_receipt(self, gr_id: str) -> Dict[str, Any]:
        """Post/confirm a Goods Receipt (makes it final)."""
        return await self._integration_request("POST", f"/goods-receipts/{gr_id}/post")

    async def get_goods_receipt(self, gr_id: str) -> Dict[str, Any]:
        """Get Goods Receipt details by ID."""
        return await self._integration_request("GET", f"/goods-receipts/{gr_id}")

    # ==================== ASN Methods ====================

    async def create_asn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create an Advanced Shipping Notice."""
        return await self._request("POST", "/asns", data=payload)

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
        return await self._request("POST", "/brand-webhooks", data=payload)

    async def list_webhooks(self) -> Dict[str, Any]:
        """List registered webhooks."""
        return await self._request("GET", "/brand-webhooks")

    async def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Send a test event to a registered webhook."""
        return await self._request("POST", f"/brand-webhooks/{webhook_id}/test")
