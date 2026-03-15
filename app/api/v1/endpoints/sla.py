"""SLA Automation & Escalation API endpoints."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service_request import ServiceRequest, SLARule, SLABreach
from app.api.deps import DB, CurrentUser

router = APIRouter()


# ==================== Pydantic Schemas ====================

class SLARuleCreate(BaseModel):
    name: str
    service_type: Optional[str] = None
    priority: Optional[str] = None
    response_hours: int = 24
    resolution_hours: int = 72
    escalation_level_1_hours: Optional[int] = 48
    escalation_level_2_hours: Optional[int] = 72
    escalation_level_1_user_id: Optional[UUID] = None
    escalation_level_2_user_id: Optional[UUID] = None
    is_active: bool = True


class SLARuleUpdate(BaseModel):
    name: Optional[str] = None
    service_type: Optional[str] = None
    priority: Optional[str] = None
    response_hours: Optional[int] = None
    resolution_hours: Optional[int] = None
    escalation_level_1_hours: Optional[int] = None
    escalation_level_2_hours: Optional[int] = None
    escalation_level_1_user_id: Optional[UUID] = None
    escalation_level_2_user_id: Optional[UUID] = None
    is_active: Optional[bool] = None


# ==================== SLA Rules ====================

@router.post("/sla-rules", status_code=status.HTTP_201_CREATED)
async def create_sla_rule(payload: SLARuleCreate, db: DB, current_user: CurrentUser):
    """Create a new SLA rule."""
    rule = SLARule(
        name=payload.name,
        service_type=payload.service_type,
        priority=payload.priority,
        response_hours=payload.response_hours,
        resolution_hours=payload.resolution_hours,
        escalation_level_1_hours=payload.escalation_level_1_hours,
        escalation_level_2_hours=payload.escalation_level_2_hours,
        escalation_level_1_user_id=payload.escalation_level_1_user_id,
        escalation_level_2_user_id=payload.escalation_level_2_user_id,
        is_active=payload.is_active,
    )
    db.add(rule)
    await db.flush()

    return {
        "id": str(rule.id),
        "name": rule.name,
        "service_type": rule.service_type,
        "priority": rule.priority,
        "response_hours": rule.response_hours,
        "resolution_hours": rule.resolution_hours,
        "escalation_level_1_hours": rule.escalation_level_1_hours,
        "escalation_level_2_hours": rule.escalation_level_2_hours,
        "escalation_level_1_user_id": str(rule.escalation_level_1_user_id) if rule.escalation_level_1_user_id else None,
        "escalation_level_2_user_id": str(rule.escalation_level_2_user_id) if rule.escalation_level_2_user_id else None,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


@router.get("/sla-rules")
async def list_sla_rules(db: DB, current_user: CurrentUser):
    """List all SLA rules."""
    result = await db.execute(select(SLARule).order_by(SLARule.created_at.desc()))
    rules = result.scalars().all()

    return {
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "service_type": r.service_type,
                "priority": r.priority,
                "response_hours": r.response_hours,
                "resolution_hours": r.resolution_hours,
                "escalation_level_1_hours": r.escalation_level_1_hours,
                "escalation_level_2_hours": r.escalation_level_2_hours,
                "escalation_level_1_user_id": str(r.escalation_level_1_user_id) if r.escalation_level_1_user_id else None,
                "escalation_level_2_user_id": str(r.escalation_level_2_user_id) if r.escalation_level_2_user_id else None,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rules
        ],
        "total": len(rules),
    }


@router.put("/sla-rules/{rule_id}")
async def update_sla_rule(rule_id: UUID, payload: SLARuleUpdate, db: DB, current_user: CurrentUser):
    """Update an SLA rule."""
    rule = await db.get(SLARule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="SLA rule not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.flush()

    return {
        "id": str(rule.id),
        "name": rule.name,
        "service_type": rule.service_type,
        "priority": rule.priority,
        "response_hours": rule.response_hours,
        "resolution_hours": rule.resolution_hours,
        "escalation_level_1_hours": rule.escalation_level_1_hours,
        "escalation_level_2_hours": rule.escalation_level_2_hours,
        "escalation_level_1_user_id": str(rule.escalation_level_1_user_id) if rule.escalation_level_1_user_id else None,
        "escalation_level_2_user_id": str(rule.escalation_level_2_user_id) if rule.escalation_level_2_user_id else None,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


# ==================== SLA Breaches ====================

@router.get("/sla-breaches")
async def list_sla_breaches(
    db: DB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List SLA breaches with service request details."""
    query = (
        select(SLABreach)
        .order_by(SLABreach.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    count_query = select(func.count(SLABreach.id))
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query)
    breaches = result.scalars().all()

    items = []
    for b in breaches:
        # Load service request for ticket number
        sr = await db.get(ServiceRequest, b.service_request_id)
        items.append({
            "id": str(b.id),
            "service_request_id": str(b.service_request_id),
            "ticket_number": sr.ticket_number if sr else None,
            "service_type": sr.service_type if sr else None,
            "priority": sr.priority if sr else None,
            "sr_status": sr.status if sr else None,
            "sla_rule_id": str(b.sla_rule_id) if b.sla_rule_id else None,
            "breach_type": b.breach_type,
            "breached_at": b.breached_at.isoformat() if b.breached_at else None,
            "escalation_level": b.escalation_level,
            "escalated_to": str(b.escalated_to) if b.escalated_to else None,
            "resolution_at": b.resolution_at.isoformat() if b.resolution_at else None,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "size": size}


# ==================== SLA Check ====================

@router.post("/check-sla")
async def check_sla(db: DB, current_user: CurrentUser):
    """Check all open service requests against SLA rules.

    Creates breach records for violations. Returns summary of new breaches.
    """
    now = datetime.now(timezone.utc)

    # Get all active SLA rules
    rules_result = await db.execute(select(SLARule).where(SLARule.is_active == True))
    rules = rules_result.scalars().all()

    if not rules:
        return {"message": "No active SLA rules found", "new_breaches": 0}

    # Get all open service requests (not COMPLETED, CLOSED, CANCELLED)
    open_statuses = ["PENDING", "ASSIGNED", "SCHEDULED", "EN_ROUTE", "IN_PROGRESS", "PARTS_REQUIRED", "ON_HOLD", "REOPENED"]
    sr_result = await db.execute(
        select(ServiceRequest).where(ServiceRequest.status.in_(open_statuses))
    )
    open_requests = sr_result.scalars().all()

    new_breaches = 0

    for sr in open_requests:
        # Find matching SLA rule (most specific first: match both type+priority, then type only, then priority only, then default)
        matching_rule = None
        for rule in rules:
            type_match = rule.service_type is None or rule.service_type == sr.service_type
            priority_match = rule.priority is None or rule.priority == sr.priority
            if type_match and priority_match:
                matching_rule = rule
                break

        if not matching_rule:
            continue

        sr_created = sr.created_at
        if not sr_created:
            continue

        # Make timezone-aware if needed
        if sr_created.tzinfo is None:
            sr_created = sr_created.replace(tzinfo=timezone.utc)

        hours_elapsed = (now - sr_created).total_seconds() / 3600

        # Check response SLA (based on assigned_at)
        if not sr.assigned_at and hours_elapsed > matching_rule.response_hours:
            # Check if breach already recorded
            existing = await db.execute(
                select(SLABreach).where(
                    and_(
                        SLABreach.service_request_id == sr.id,
                        SLABreach.breach_type == "RESPONSE",
                    )
                )
            )
            if not existing.scalar_one_or_none():
                breach = SLABreach(
                    service_request_id=sr.id,
                    sla_rule_id=matching_rule.id,
                    breach_type="RESPONSE",
                    breached_at=now,
                    escalation_level=1 if hours_elapsed > (matching_rule.escalation_level_1_hours or 999) else 0,
                    escalated_to=matching_rule.escalation_level_1_user_id if hours_elapsed > (matching_rule.escalation_level_1_hours or 999) else None,
                )
                db.add(breach)
                new_breaches += 1

        # Check resolution SLA
        if hours_elapsed > matching_rule.resolution_hours:
            existing = await db.execute(
                select(SLABreach).where(
                    and_(
                        SLABreach.service_request_id == sr.id,
                        SLABreach.breach_type == "RESOLUTION",
                    )
                )
            )
            if not existing.scalar_one_or_none():
                esc_level = 0
                esc_user = None
                if matching_rule.escalation_level_2_hours and hours_elapsed > matching_rule.escalation_level_2_hours:
                    esc_level = 2
                    esc_user = matching_rule.escalation_level_2_user_id
                elif matching_rule.escalation_level_1_hours and hours_elapsed > matching_rule.escalation_level_1_hours:
                    esc_level = 1
                    esc_user = matching_rule.escalation_level_1_user_id

                breach = SLABreach(
                    service_request_id=sr.id,
                    sla_rule_id=matching_rule.id,
                    breach_type="RESOLUTION",
                    breached_at=now,
                    escalation_level=esc_level,
                    escalated_to=esc_user,
                )
                db.add(breach)
                new_breaches += 1

    await db.flush()

    return {
        "message": f"SLA check completed. {new_breaches} new breaches found.",
        "new_breaches": new_breaches,
        "total_open_requests_checked": len(open_requests),
        "active_rules_count": len(rules),
    }
