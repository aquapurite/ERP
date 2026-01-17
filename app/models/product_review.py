"""
Product Review Model for D2C Storefront

Allows customers to rate and review products they've purchased.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product import Product


class ProductReview(Base):
    """
    Customer review for a product.
    Reviews can only be submitted by verified purchasers.
    """
    __tablename__ = "product_reviews"
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        comment="Order in which this product was purchased"
    )

    # Review Content
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Rating from 1 to 5 stars"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Review title/headline"
    )
    review_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full review text"
    )

    # Verification & Moderation
    is_verified_purchase: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if customer actually purchased this product"
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Admin approval status"
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Featured review (shown prominently)"
    )

    # Helpful votes
    helpful_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of users who found this helpful"
    )
    not_helpful_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Images (JSON array of URLs)
    images: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of image URLs uploaded with review"
    )

    # Admin response
    admin_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Response from the seller/admin"
    )
    admin_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    customer: Mapped["Customer"] = relationship("Customer")

    def __repr__(self) -> str:
        return f"<ProductReview(product_id={self.product_id}, rating={self.rating})>"


class ReviewHelpful(Base):
    """
    Tracks which users found a review helpful.
    Prevents duplicate votes.
    """
    __tablename__ = "review_helpful"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_reviews.id", ondelete="CASCADE"),
        nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False
    )
    is_helpful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="True = helpful, False = not helpful"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        # Each customer can only vote once per review
        {'sqlite_autoincrement': True},
    )
