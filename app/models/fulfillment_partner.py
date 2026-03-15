"""Fulfillment Partner model for multi-3PL support."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class FulfillmentPartner(Base):
    """Registered 3PL or self-managed fulfillment provider."""

    __tablename__ = "fulfillment_partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    provider_type = Column(String(50), nullable=False, default="SELF_MANAGED",
                           comment="3PL or SELF_MANAGED")

    # API credentials
    api_base_url = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    auth_config = Column(JSONB, default=dict,
                         comment="email, password, company_id, integration_profile_id")
    webhook_secret = Column(String(500), nullable=True)

    # Status & extensible config
    is_active = Column(Boolean, nullable=False, default=True)
    config = Column(JSONB, default=dict, comment="Extensible provider config")

    # Timestamps
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    warehouses = relationship("Warehouse", back_populates="fulfillment_partner")

    def __repr__(self):
        return f"<FulfillmentPartner {self.code}: {self.name}>"
