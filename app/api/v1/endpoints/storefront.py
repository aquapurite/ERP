"""Public Storefront API endpoints.

These endpoints are accessible without authentication for the D2C website.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import DB
from app.models.company import Company

router = APIRouter()


class StorefrontCompanyInfo(BaseModel):
    """Public company info for storefront."""
    name: str
    trade_name: Optional[str] = None
    logo_url: Optional[str] = None
    logo_small_url: Optional[str] = None
    favicon_url: Optional[str] = None
    email: str
    phone: str
    website: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str

    class Config:
        from_attributes = True


@router.get("/company", response_model=StorefrontCompanyInfo)
async def get_storefront_company(db: DB):
    """
    Get public company info for the storefront.
    No authentication required.
    """
    # Get primary company or first active company
    query = (
        select(Company)
        .where(Company.is_primary == True, Company.is_active == True)
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        # Try to get any active company
        query = (
            select(Company)
            .where(Company.is_active == True)
            .order_by(Company.created_at.asc())
        )
        result = await db.execute(query)
        company = result.scalar_one_or_none()

    if not company:
        # Return default company info if none configured
        return StorefrontCompanyInfo(
            name="AQUAPURITE",
            trade_name="AQUAPURITE",
            logo_url=None,
            email="support@aquapurite.com",
            phone="1800-123-4567",
            website="https://aquapurite.com",
            address="123 Industrial Area, Sector 62",
            city="Noida",
            state="Uttar Pradesh",
            pincode="201301"
        )

    return StorefrontCompanyInfo(
        name=company.legal_name,
        trade_name=company.trade_name or company.legal_name,
        logo_url=company.logo_url,
        logo_small_url=company.logo_small_url,
        favicon_url=company.favicon_url,
        email=company.email,
        phone=company.phone,
        website=company.website,
        address=company.address_line1 + (f", {company.address_line2}" if company.address_line2 else ""),
        city=company.city,
        state=company.state,
        pincode=company.pincode
    )
