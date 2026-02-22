"""
Dealer Orchestration Service

Central service that orchestrates all downstream actions when a dealer is approved.
Mirrors the VendorOrchestrationService pattern.

When a dealer is approved:
1. Send welcome email with brochure PDF attached
2. Future: Initialize dealer ledger, assign sales rep, etc.
"""
import uuid
import os
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dealer import Dealer
from app.services.email_service import get_email_service

logger = logging.getLogger(__name__)

# Path to brochure relative to project root
BROCHURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "static", "brochures", "Aquapurite_Brochure.pdf"
)


class DealerOrchestrationService:
    """
    Central service that orchestrates all downstream actions
    when a dealer status changes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def on_dealer_approved(self, dealer: Dealer, approved_by_id: uuid.UUID) -> dict:
        """
        Called when a dealer is approved. Triggers all downstream actions.

        Args:
            dealer: The dealer that was just approved
            approved_by_id: User ID who approved the dealer

        Returns:
            dict with results of all orchestration actions
        """
        results = {
            "dealer_id": str(dealer.id),
            "dealer_code": dealer.dealer_code,
            "actions_performed": [],
        }

        # 1. Send welcome email with brochure
        try:
            email_sent = self._send_welcome_email(dealer)
            if email_sent:
                results["actions_performed"].append("welcome_email_sent")
            else:
                results["actions_performed"].append("welcome_email_skipped")
        except Exception as e:
            logger.error(f"Failed to send dealer welcome email to {dealer.email}: {e}")
            results["actions_performed"].append("welcome_email_failed")

        return results

    def _send_welcome_email(self, dealer: Dealer) -> bool:
        """Send welcome email with brochure to the newly approved dealer."""
        if not dealer.email:
            logger.warning(f"Dealer {dealer.dealer_code} has no email, skipping welcome email")
            return False

        # Read brochure PDF
        brochure_bytes = None
        try:
            if os.path.exists(BROCHURE_PATH):
                with open(BROCHURE_PATH, "rb") as f:
                    brochure_bytes = f.read()
                logger.info(f"Loaded brochure ({len(brochure_bytes)} bytes)")
            else:
                logger.warning(f"Brochure not found at {BROCHURE_PATH}, sending email without attachment")
        except Exception as e:
            logger.error(f"Error reading brochure: {e}")

        email_service = get_email_service()

        contact_person = dealer.contact_person or dealer.name
        dealer_type = dealer.dealer_type if isinstance(dealer.dealer_type, str) else dealer.dealer_type.value
        credit_limit = dealer.credit_limit

        return email_service.send_dealer_welcome_email(
            to_email=dealer.email,
            dealer_name=dealer.name,
            contact_person=contact_person,
            dealer_code=dealer.dealer_code,
            dealer_type=dealer_type,
            credit_limit=credit_limit,
            brochure_bytes=brochure_bytes,
        )
