"""Fulfillment Dispatcher — thin routing layer.

Resolves warehouse → fulfillment partner → service instance.
Falls back to settings.CJDQUICK_* if no partner is linked.
"""

import logging
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.warehouse import Warehouse
from app.models.fulfillment_partner import FulfillmentPartner
from app.services.cjdquick_service import CJDQuickService

logger = logging.getLogger(__name__)


class PartnerConfig:
    """Resolved config for a fulfillment partner + warehouse."""

    def __init__(
        self,
        provider_code: str,
        provider_type: str,
        location_id: str,
        warehouse_code: str,
        company_id: str,
        api_base_url: str,
        api_key: str,
        email: str,
        password: str,
        integration_profile_id: str,
        webhook_secret: Optional[str] = None,
    ):
        self.provider_code = provider_code
        self.provider_type = provider_type
        self.location_id = location_id
        self.warehouse_code = warehouse_code
        self.company_id = company_id
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.email = email
        self.password = password
        self.integration_profile_id = integration_profile_id
        self.webhook_secret = webhook_secret

    @property
    def is_3pl(self) -> bool:
        return self.provider_type == "3PL"


def _fallback_config() -> PartnerConfig:
    """Build config from hardcoded settings (legacy fallback)."""
    return PartnerConfig(
        provider_code="CJDQUICK",
        provider_type="3PL",
        location_id=settings.CJDQUICK_DELHI_LOCATION_ID,
        warehouse_code=settings.CJDQUICK_WAREHOUSE_CODE,
        company_id=settings.CJDQUICK_COMPANY_ID,
        api_base_url=settings.CJDQUICK_BASE_URL,
        api_key=settings.CJDQUICK_API_KEY,
        email=settings.CJDQUICK_EMAIL,
        password=settings.CJDQUICK_PASSWORD,
        integration_profile_id=settings.CJDQUICK_INTEGRATION_PROFILE_ID,
        webhook_secret=settings.CJDQUICK_WEBHOOK_SECRET,
    )


async def resolve_partner_config(
    db: AsyncSession, warehouse_id: Optional[str] = None
) -> PartnerConfig:
    """Resolve fulfillment partner config from warehouse.

    1. If warehouse_id given, load warehouse + linked partner.
    2. Extract credentials from partner.auth_config + warehouse partner fields.
    3. Falls back to settings.CJDQUICK_* if no partner linked.
    """
    if not warehouse_id:
        return _fallback_config()

    result = await db.execute(
        select(Warehouse)
        .options(joinedload(Warehouse.fulfillment_partner))
        .where(Warehouse.id == warehouse_id)
    )
    warehouse = result.unique().scalar_one_or_none()

    if not warehouse or not warehouse.fulfillment_partner:
        logger.debug(
            "No fulfillment partner for warehouse %s, using fallback config",
            warehouse_id,
        )
        return _fallback_config()

    partner = warehouse.fulfillment_partner
    auth = partner.auth_config or {}

    return PartnerConfig(
        provider_code=partner.code,
        provider_type=partner.provider_type,
        location_id=warehouse.partner_location_id or settings.CJDQUICK_DELHI_LOCATION_ID,
        warehouse_code=warehouse.partner_warehouse_code or settings.CJDQUICK_WAREHOUSE_CODE,
        company_id=auth.get("company_id", settings.CJDQUICK_COMPANY_ID),
        api_base_url=partner.api_base_url or settings.CJDQUICK_BASE_URL,
        api_key=partner.api_key or settings.CJDQUICK_API_KEY,
        email=auth.get("email", settings.CJDQUICK_EMAIL),
        password=auth.get("password", settings.CJDQUICK_PASSWORD),
        integration_profile_id=auth.get(
            "integration_profile_id", settings.CJDQUICK_INTEGRATION_PROFILE_ID
        ),
        webhook_secret=partner.webhook_secret,
    )


def get_service_for_config(config: PartnerConfig) -> CJDQuickService:
    """Create a CJDQuickService instance with dynamic credentials."""
    return CJDQuickService(
        base_url=config.api_base_url,
        email=config.email,
        password=config.password,
        api_key=config.api_key,
    )
