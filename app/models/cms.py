"""
CMS Models for D2C Storefront Content Management

Content types:
- CMSBanner: Hero banners with images, CTAs, scheduling
- CMSUsp: USPs/Features with icons
- CMSTestimonial: Customer testimonials
- CMSAnnouncement: Announcement bar messages
- CMSPage: Static pages with rich text content
- CMSPageVersion: Version history for pages
- CMSSeo: SEO settings per page
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


# ==================== Enums (stored as VARCHAR in DB) ====================

class CMSPageStatus(str, Enum):
    """Page publish status"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class CMSAnnouncementType(str, Enum):
    """Announcement bar type/style"""
    INFO = "INFO"
    WARNING = "WARNING"
    PROMO = "PROMO"
    SUCCESS = "SUCCESS"


# ==================== CMS Banner Model ====================

class CMSBanner(Base):
    """
    Hero banner for D2C storefront homepage.
    Supports scheduling, multiple banners with sort order.
    """
    __tablename__ = "cms_banners"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Content
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Banner headline"
    )
    subtitle: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Banner subheadline/description"
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Full-size banner image URL"
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Thumbnail image for admin preview"
    )
    mobile_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Mobile-optimized image URL"
    )

    # CTA (Call to Action)
    cta_text: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Button text e.g., 'Shop Now'"
    )
    cta_link: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Button link URL"
    )

    # Positioning
    text_position: Mapped[str] = mapped_column(
        String(20),
        default="left",
        nullable=False,
        comment="Text alignment: left, center, right"
    )
    text_color: Mapped[str] = mapped_column(
        String(20),
        default="white",
        nullable=False,
        comment="Text color: white, dark"
    )

    # Display settings
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Display order (lower = first)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Scheduling
    starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Start showing banner at this time"
    )
    ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Stop showing banner after this time"
    )

    # Audit
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<CMSBanner(title='{self.title}', active={self.is_active})>"


# ==================== CMS USP Model ====================

class CMSUsp(Base):
    """
    USPs (Unique Selling Points) / Features for homepage.
    E.g., "Free Installation", "2 Year Warranty", etc.
    """
    __tablename__ = "cms_usps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Content
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="USP headline"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="Short description"
    )
    icon: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Lucide icon name e.g., 'truck', 'shield-check'"
    )
    icon_color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Icon color class e.g., 'text-blue-500'"
    )

    # Link (optional)
    link_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    link_text: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # Display
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Audit
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<CMSUsp(title='{self.title}', icon='{self.icon}')>"


# ==================== CMS Testimonial Model ====================

class CMSTestimonial(Base):
    """
    Customer testimonials for homepage.
    """
    __tablename__ = "cms_testimonials"
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_testimonial_rating'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Customer info
    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    customer_location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="City/State"
    )
    customer_avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    customer_designation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Job title or role (optional)"
    )

    # Review content
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Rating from 1-5 stars"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Testimonial text"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Review title/headline"
    )

    # Product reference (optional)
    product_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Product being reviewed"
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True
    )

    # Display
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Featured testimonials shown first"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Audit
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<CMSTestimonial(customer='{self.customer_name}', rating={self.rating})>"


# ==================== CMS Announcement Model ====================

class CMSAnnouncement(Base):
    """
    Announcement bar messages for storefront header.
    E.g., "Free shipping on orders above ₹999!"
    """
    __tablename__ = "cms_announcements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Content
    text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Announcement message"
    )
    link_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Link when clicked"
    )
    link_text: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Link text e.g., 'Learn More'"
    )

    # Style
    announcement_type: Mapped[str] = mapped_column(
        String(20),
        default="INFO",
        nullable=False,
        comment="INFO, WARNING, PROMO, SUCCESS"
    )
    background_color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Custom background color"
    )
    text_color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Custom text color"
    )

    # Scheduling
    starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Display
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_dismissible: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Can user close this announcement"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Audit
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<CMSAnnouncement(text='{self.text[:50]}...', type={self.announcement_type})>"


# ==================== CMS Page Model ====================

class CMSPage(Base):
    """
    Static pages with rich text content.
    E.g., About Us, Privacy Policy, Terms & Conditions.
    """
    __tablename__ = "cms_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Identification
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Page title"
    )
    slug: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="URL slug e.g., 'about-us'"
    )

    # Content
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rich text HTML content"
    )
    excerpt: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Short summary for listings"
    )

    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="SEO meta title"
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="SEO meta description"
    )
    meta_keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="SEO keywords (comma-separated)"
    )
    og_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Open Graph image URL"
    )
    canonical_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Canonical URL if different"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="DRAFT",
        nullable=False,
        comment="DRAFT, PUBLISHED, ARCHIVED"
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When page was published"
    )

    # Template
    template: Mapped[str] = mapped_column(
        String(50),
        default="default",
        nullable=False,
        comment="Page template: default, full-width, landing"
    )

    # Navigation
    show_in_footer: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    show_in_header: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Audit
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    versions: Mapped[List["CMSPageVersion"]] = relationship(
        "CMSPageVersion",
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="CMSPageVersion.version_number.desc()"
    )
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<CMSPage(title='{self.title}', slug='{self.slug}', status={self.status})>"


# ==================== CMS Page Version Model ====================

class CMSPageVersion(Base):
    """
    Version history for CMS pages.
    Created automatically when a page is updated.
    """
    __tablename__ = "cms_page_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Page reference
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cms_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential version number"
    )

    # Snapshot of content at this version
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Change metadata
    change_summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Description of changes in this version"
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    page: Mapped["CMSPage"] = relationship("CMSPage", back_populates="versions")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<CMSPageVersion(page_id={self.page_id}, version={self.version_number})>"


# ==================== CMS SEO Settings Model ====================

class CMSSeo(Base):
    """
    SEO settings for specific routes/pages.
    Allows overriding default SEO for any URL path.
    """
    __tablename__ = "cms_seo"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # URL/Route
    url_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        comment="URL path e.g., '/', '/products', '/products/aqua-ro'"
    )

    # SEO fields
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    meta_keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    og_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    og_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    og_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    og_type: Mapped[str] = mapped_column(
        String(50),
        default="website",
        nullable=False
    )
    canonical_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Robots
    robots_index: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Allow search engine indexing"
    )
    robots_follow: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Allow following links"
    )

    # Structured data (JSON-LD)
    structured_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON-LD structured data"
    )

    # Audit
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<CMSSeo(url_path='{self.url_path}')>"
