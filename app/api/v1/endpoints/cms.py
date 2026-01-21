"""CMS Admin API endpoints for D2C content management.

Provides CRUD operations for:
- Banners
- USPs (Features)
- Testimonials
- Announcements
- Static Pages (with version history)
- SEO Settings

All endpoints require authentication and CMS permissions.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import DB, CurrentUser, require_permissions
from app.models.cms import (
    CMSBanner,
    CMSUsp,
    CMSTestimonial,
    CMSAnnouncement,
    CMSPage,
    CMSPageVersion,
    CMSSeo,
)
from app.schemas.cms import (
    # Banner schemas
    CMSBannerCreate,
    CMSBannerUpdate,
    CMSBannerResponse,
    CMSBannerListResponse,
    # USP schemas
    CMSUspCreate,
    CMSUspUpdate,
    CMSUspResponse,
    CMSUspListResponse,
    # Testimonial schemas
    CMSTestimonialCreate,
    CMSTestimonialUpdate,
    CMSTestimonialResponse,
    CMSTestimonialListResponse,
    # Announcement schemas
    CMSAnnouncementCreate,
    CMSAnnouncementUpdate,
    CMSAnnouncementResponse,
    CMSAnnouncementListResponse,
    # Page schemas
    CMSPageCreate,
    CMSPageUpdate,
    CMSPageResponse,
    CMSPageListResponse,
    CMSPageVersionResponse,
    # SEO schemas
    CMSSeoCreate,
    CMSSeoUpdate,
    CMSSeoResponse,
    CMSSeoListResponse,
    # Common schemas
    CMSReorderRequest,
)

router = APIRouter()


# ==================== Banner Endpoints ====================

@router.get("/banners", response_model=CMSBannerListResponse)
async def list_banners(
    db: DB,
    current_user: CurrentUser,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """List all banners (admin view - includes inactive)."""
    query = select(CMSBanner).order_by(CMSBanner.sort_order.asc(), CMSBanner.created_at.desc())

    if is_active is not None:
        query = query.where(CMSBanner.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch items
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    banners = result.scalars().all()

    return CMSBannerListResponse(
        items=[CMSBannerResponse.model_validate(b) for b in banners],
        total=total
    )


@router.post("/banners", response_model=CMSBannerResponse, status_code=201)
async def create_banner(
    data: CMSBannerCreate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_CREATE"])),
):
    """Create a new banner."""
    banner = CMSBanner(
        **data.model_dump(),
        created_by=current_user.id,
    )
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return CMSBannerResponse.model_validate(banner)


@router.get("/banners/{banner_id}", response_model=CMSBannerResponse)
async def get_banner(
    banner_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get a single banner by ID."""
    result = await db.execute(
        select(CMSBanner).where(CMSBanner.id == banner_id)
    )
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return CMSBannerResponse.model_validate(banner)


@router.put("/banners/{banner_id}", response_model=CMSBannerResponse)
async def update_banner(
    banner_id: UUID,
    data: CMSBannerUpdate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Update a banner."""
    result = await db.execute(
        select(CMSBanner).where(CMSBanner.id == banner_id)
    )
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(banner, key, value)

    await db.commit()
    await db.refresh(banner)
    return CMSBannerResponse.model_validate(banner)


@router.delete("/banners/{banner_id}", status_code=204)
async def delete_banner(
    banner_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_DELETE"])),
):
    """Delete a banner."""
    result = await db.execute(
        select(CMSBanner).where(CMSBanner.id == banner_id)
    )
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    await db.delete(banner)
    await db.commit()


@router.put("/banners/reorder", response_model=List[CMSBannerResponse])
async def reorder_banners(
    data: CMSReorderRequest,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Reorder banners by providing list of IDs in desired order."""
    banners = []
    for idx, banner_id in enumerate(data.ids):
        result = await db.execute(
            select(CMSBanner).where(CMSBanner.id == banner_id)
        )
        banner = result.scalar_one_or_none()
        if banner:
            banner.sort_order = idx
            banners.append(banner)

    await db.commit()
    for banner in banners:
        await db.refresh(banner)

    return [CMSBannerResponse.model_validate(b) for b in banners]


# ==================== USP Endpoints ====================

@router.get("/usps", response_model=CMSUspListResponse)
async def list_usps(
    db: DB,
    current_user: CurrentUser,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """List all USPs."""
    query = select(CMSUsp).order_by(CMSUsp.sort_order.asc())

    if is_active is not None:
        query = query.where(CMSUsp.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    usps = result.scalars().all()

    return CMSUspListResponse(
        items=[CMSUspResponse.model_validate(u) for u in usps],
        total=total
    )


@router.post("/usps", response_model=CMSUspResponse, status_code=201)
async def create_usp(
    data: CMSUspCreate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_CREATE"])),
):
    """Create a new USP."""
    usp = CMSUsp(
        **data.model_dump(),
        created_by=current_user.id,
    )
    db.add(usp)
    await db.commit()
    await db.refresh(usp)
    return CMSUspResponse.model_validate(usp)


@router.get("/usps/{usp_id}", response_model=CMSUspResponse)
async def get_usp(
    usp_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get a single USP by ID."""
    result = await db.execute(
        select(CMSUsp).where(CMSUsp.id == usp_id)
    )
    usp = result.scalar_one_or_none()
    if not usp:
        raise HTTPException(status_code=404, detail="USP not found")
    return CMSUspResponse.model_validate(usp)


@router.put("/usps/{usp_id}", response_model=CMSUspResponse)
async def update_usp(
    usp_id: UUID,
    data: CMSUspUpdate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Update a USP."""
    result = await db.execute(
        select(CMSUsp).where(CMSUsp.id == usp_id)
    )
    usp = result.scalar_one_or_none()
    if not usp:
        raise HTTPException(status_code=404, detail="USP not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(usp, key, value)

    await db.commit()
    await db.refresh(usp)
    return CMSUspResponse.model_validate(usp)


@router.delete("/usps/{usp_id}", status_code=204)
async def delete_usp(
    usp_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_DELETE"])),
):
    """Delete a USP."""
    result = await db.execute(
        select(CMSUsp).where(CMSUsp.id == usp_id)
    )
    usp = result.scalar_one_or_none()
    if not usp:
        raise HTTPException(status_code=404, detail="USP not found")

    await db.delete(usp)
    await db.commit()


@router.put("/usps/reorder", response_model=List[CMSUspResponse])
async def reorder_usps(
    data: CMSReorderRequest,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Reorder USPs."""
    usps = []
    for idx, usp_id in enumerate(data.ids):
        result = await db.execute(
            select(CMSUsp).where(CMSUsp.id == usp_id)
        )
        usp = result.scalar_one_or_none()
        if usp:
            usp.sort_order = idx
            usps.append(usp)

    await db.commit()
    for usp in usps:
        await db.refresh(usp)

    return [CMSUspResponse.model_validate(u) for u in usps]


# ==================== Testimonial Endpoints ====================

@router.get("/testimonials", response_model=CMSTestimonialListResponse)
async def list_testimonials(
    db: DB,
    current_user: CurrentUser,
    is_active: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """List all testimonials."""
    query = select(CMSTestimonial).order_by(
        CMSTestimonial.is_featured.desc(),
        CMSTestimonial.sort_order.asc()
    )

    if is_active is not None:
        query = query.where(CMSTestimonial.is_active == is_active)
    if is_featured is not None:
        query = query.where(CMSTestimonial.is_featured == is_featured)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    testimonials = result.scalars().all()

    return CMSTestimonialListResponse(
        items=[CMSTestimonialResponse.model_validate(t) for t in testimonials],
        total=total
    )


@router.post("/testimonials", response_model=CMSTestimonialResponse, status_code=201)
async def create_testimonial(
    data: CMSTestimonialCreate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_CREATE"])),
):
    """Create a new testimonial."""
    testimonial = CMSTestimonial(
        **data.model_dump(),
        created_by=current_user.id,
    )
    db.add(testimonial)
    await db.commit()
    await db.refresh(testimonial)
    return CMSTestimonialResponse.model_validate(testimonial)


@router.get("/testimonials/{testimonial_id}", response_model=CMSTestimonialResponse)
async def get_testimonial(
    testimonial_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get a single testimonial by ID."""
    result = await db.execute(
        select(CMSTestimonial).where(CMSTestimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return CMSTestimonialResponse.model_validate(testimonial)


@router.put("/testimonials/{testimonial_id}", response_model=CMSTestimonialResponse)
async def update_testimonial(
    testimonial_id: UUID,
    data: CMSTestimonialUpdate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Update a testimonial."""
    result = await db.execute(
        select(CMSTestimonial).where(CMSTestimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(testimonial, key, value)

    await db.commit()
    await db.refresh(testimonial)
    return CMSTestimonialResponse.model_validate(testimonial)


@router.delete("/testimonials/{testimonial_id}", status_code=204)
async def delete_testimonial(
    testimonial_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_DELETE"])),
):
    """Delete a testimonial."""
    result = await db.execute(
        select(CMSTestimonial).where(CMSTestimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")

    await db.delete(testimonial)
    await db.commit()


# ==================== Announcement Endpoints ====================

@router.get("/announcements", response_model=CMSAnnouncementListResponse)
async def list_announcements(
    db: DB,
    current_user: CurrentUser,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """List all announcements."""
    query = select(CMSAnnouncement).order_by(CMSAnnouncement.sort_order.asc())

    if is_active is not None:
        query = query.where(CMSAnnouncement.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    announcements = result.scalars().all()

    return CMSAnnouncementListResponse(
        items=[CMSAnnouncementResponse.model_validate(a) for a in announcements],
        total=total
    )


@router.post("/announcements", response_model=CMSAnnouncementResponse, status_code=201)
async def create_announcement(
    data: CMSAnnouncementCreate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_CREATE"])),
):
    """Create a new announcement."""
    announcement = CMSAnnouncement(
        **data.model_dump(),
        created_by=current_user.id,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return CMSAnnouncementResponse.model_validate(announcement)


@router.get("/announcements/{announcement_id}", response_model=CMSAnnouncementResponse)
async def get_announcement(
    announcement_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get a single announcement by ID."""
    result = await db.execute(
        select(CMSAnnouncement).where(CMSAnnouncement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return CMSAnnouncementResponse.model_validate(announcement)


@router.put("/announcements/{announcement_id}", response_model=CMSAnnouncementResponse)
async def update_announcement(
    announcement_id: UUID,
    data: CMSAnnouncementUpdate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Update an announcement."""
    result = await db.execute(
        select(CMSAnnouncement).where(CMSAnnouncement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == 'announcement_type' and value is not None:
            setattr(announcement, key, value.value if hasattr(value, 'value') else value)
        else:
            setattr(announcement, key, value)

    await db.commit()
    await db.refresh(announcement)
    return CMSAnnouncementResponse.model_validate(announcement)


@router.delete("/announcements/{announcement_id}", status_code=204)
async def delete_announcement(
    announcement_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_DELETE"])),
):
    """Delete an announcement."""
    result = await db.execute(
        select(CMSAnnouncement).where(CMSAnnouncement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    await db.delete(announcement)
    await db.commit()


# ==================== Page Endpoints ====================

@router.get("/pages", response_model=CMSPageListResponse)
async def list_pages(
    db: DB,
    current_user: CurrentUser,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """List all pages."""
    query = select(CMSPage).order_by(CMSPage.sort_order.asc(), CMSPage.created_at.desc())

    if status:
        query = query.where(CMSPage.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    pages = result.scalars().all()

    return CMSPageListResponse(
        items=[
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "status": p.status,
                "published_at": p.published_at,
                "updated_at": p.updated_at,
            }
            for p in pages
        ],
        total=total
    )


@router.post("/pages", response_model=CMSPageResponse, status_code=201)
async def create_page(
    data: CMSPageCreate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_CREATE"])),
):
    """Create a new page."""
    # Check for duplicate slug
    existing = await db.execute(
        select(CMSPage).where(CMSPage.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Page with this slug already exists")

    page = CMSPage(
        **data.model_dump(),
        created_by=current_user.id,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)

    # Create initial version
    version = CMSPageVersion(
        page_id=page.id,
        version_number=1,
        title=page.title,
        content=page.content,
        meta_title=page.meta_title,
        meta_description=page.meta_description,
        change_summary="Initial version",
        created_by=current_user.id,
    )
    db.add(version)
    await db.commit()

    # Reload with versions
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page.id)
    )
    page = result.scalar_one()

    return CMSPageResponse.model_validate(page)


@router.get("/pages/{page_id}", response_model=CMSPageResponse)
async def get_page(
    page_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get a single page by ID with version history."""
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page_id)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return CMSPageResponse.model_validate(page)


@router.put("/pages/{page_id}", response_model=CMSPageResponse)
async def update_page(
    page_id: UUID,
    data: CMSPageUpdate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Update a page (creates new version)."""
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page_id)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check for duplicate slug if slug is being updated
    if data.slug and data.slug != page.slug:
        existing = await db.execute(
            select(CMSPage).where(CMSPage.slug == data.slug, CMSPage.id != page_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Page with this slug already exists")

    update_data = data.model_dump(exclude_unset=True)

    # Create new version before update
    max_version = max([v.version_number for v in page.versions], default=0)
    version = CMSPageVersion(
        page_id=page.id,
        version_number=max_version + 1,
        title=update_data.get('title', page.title),
        content=update_data.get('content', page.content),
        meta_title=update_data.get('meta_title', page.meta_title),
        meta_description=update_data.get('meta_description', page.meta_description),
        change_summary=f"Updated by user",
        created_by=current_user.id,
    )
    db.add(version)

    # Apply updates
    for key, value in update_data.items():
        if key == 'status' and value is not None:
            setattr(page, key, value.value if hasattr(value, 'value') else value)
        else:
            setattr(page, key, value)

    page.updated_by = current_user.id

    await db.commit()

    # Reload with versions
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page_id)
    )
    page = result.scalar_one()

    return CMSPageResponse.model_validate(page)


@router.delete("/pages/{page_id}", status_code=204)
async def delete_page(
    page_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_DELETE"])),
):
    """Delete a page and all its versions."""
    result = await db.execute(
        select(CMSPage).where(CMSPage.id == page_id)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    await db.delete(page)
    await db.commit()


@router.post("/pages/{page_id}/publish", response_model=CMSPageResponse)
async def publish_page(
    page_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_PUBLISH"])),
):
    """Publish a draft page."""
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page_id)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    page.status = "PUBLISHED"
    page.published_at = datetime.now(timezone.utc)
    page.updated_by = current_user.id

    await db.commit()
    await db.refresh(page)

    return CMSPageResponse.model_validate(page)


@router.get("/pages/{page_id}/versions", response_model=List[CMSPageVersionResponse])
async def get_page_versions(
    page_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get version history for a page."""
    result = await db.execute(
        select(CMSPageVersion)
        .where(CMSPageVersion.page_id == page_id)
        .order_by(CMSPageVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return [CMSPageVersionResponse.model_validate(v) for v in versions]


@router.post("/pages/{page_id}/revert/{version_number}", response_model=CMSPageResponse)
async def revert_page_to_version(
    page_id: UUID,
    version_number: int,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Revert a page to a specific version."""
    # Get page
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page_id)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Find version
    version_result = await db.execute(
        select(CMSPageVersion)
        .where(
            CMSPageVersion.page_id == page_id,
            CMSPageVersion.version_number == version_number
        )
    )
    version = version_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Create new version from old content
    max_version = max([v.version_number for v in page.versions], default=0)
    new_version = CMSPageVersion(
        page_id=page.id,
        version_number=max_version + 1,
        title=version.title,
        content=version.content,
        meta_title=version.meta_title,
        meta_description=version.meta_description,
        change_summary=f"Reverted to version {version_number}",
        created_by=current_user.id,
    )
    db.add(new_version)

    # Update page with old version content
    page.title = version.title
    page.content = version.content
    page.meta_title = version.meta_title
    page.meta_description = version.meta_description
    page.updated_by = current_user.id

    await db.commit()

    # Reload
    result = await db.execute(
        select(CMSPage)
        .options(selectinload(CMSPage.versions))
        .where(CMSPage.id == page_id)
    )
    page = result.scalar_one()

    return CMSPageResponse.model_validate(page)


# ==================== SEO Endpoints ====================

@router.get("/seo", response_model=CMSSeoListResponse)
async def list_seo_settings(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """List all SEO settings."""
    query = select(CMSSeo).order_by(CMSSeo.url_path.asc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    seo_settings = result.scalars().all()

    return CMSSeoListResponse(
        items=[CMSSeoResponse.model_validate(s) for s in seo_settings],
        total=total
    )


@router.post("/seo", response_model=CMSSeoResponse, status_code=201)
async def create_seo_settings(
    data: CMSSeoCreate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_CREATE"])),
):
    """Create SEO settings for a URL path."""
    # Check for duplicate
    existing = await db.execute(
        select(CMSSeo).where(CMSSeo.url_path == data.url_path)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="SEO settings for this URL already exist")

    seo = CMSSeo(
        **data.model_dump(),
        created_by=current_user.id,
    )
    db.add(seo)
    await db.commit()
    await db.refresh(seo)
    return CMSSeoResponse.model_validate(seo)


@router.get("/seo/{seo_id}", response_model=CMSSeoResponse)
async def get_seo_settings(
    seo_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_VIEW"])),
):
    """Get SEO settings by ID."""
    result = await db.execute(
        select(CMSSeo).where(CMSSeo.id == seo_id)
    )
    seo = result.scalar_one_or_none()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO settings not found")
    return CMSSeoResponse.model_validate(seo)


@router.put("/seo/{seo_id}", response_model=CMSSeoResponse)
async def update_seo_settings(
    seo_id: UUID,
    data: CMSSeoUpdate,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_EDIT"])),
):
    """Update SEO settings."""
    result = await db.execute(
        select(CMSSeo).where(CMSSeo.id == seo_id)
    )
    seo = result.scalar_one_or_none()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO settings not found")

    # Check for duplicate URL path
    if data.url_path and data.url_path != seo.url_path:
        existing = await db.execute(
            select(CMSSeo).where(CMSSeo.url_path == data.url_path, CMSSeo.id != seo_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="SEO settings for this URL already exist")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(seo, key, value)

    await db.commit()
    await db.refresh(seo)
    return CMSSeoResponse.model_validate(seo)


@router.delete("/seo/{seo_id}", status_code=204)
async def delete_seo_settings(
    seo_id: UUID,
    db: DB,
    current_user: CurrentUser,
    _: bool = Depends(require_permissions(["CMS_DELETE"])),
):
    """Delete SEO settings."""
    result = await db.execute(
        select(CMSSeo).where(CMSSeo.id == seo_id)
    )
    seo = result.scalar_one_or_none()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO settings not found")

    await db.delete(seo)
    await db.commit()
