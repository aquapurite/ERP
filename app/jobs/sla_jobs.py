"""
SLA Enforcement Jobs

Scheduled jobs for SLA monitoring and auto-escalation:
- Calculate SLA breach times for service requests linked to AMC contracts
- Auto-escalate priority when approaching SLA breach
- Flag breached SLA requests
"""

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def check_sla_compliance():
    """
    Check service request SLA compliance and auto-escalate.

    Runs every 30 minutes to:
    1. Calculate SLA breach time for AMC-linked service requests
    2. Auto-escalate priority when 75% of SLA time has elapsed
    3. Mark SLA as breached when time exceeded
    4. Send escalation notifications
    """
    logger.info("Starting SLA compliance check...")
    start_time = datetime.now(timezone.utc)
    escalated = 0
    breached = 0

    try:
        from app.database import get_db_session
        from app.models.service_request import ServiceRequest
        from app.models.amc import AMCContract, AMCPlan
        from sqlalchemy import select, and_, or_
        from sqlalchemy.orm import selectinload

        async with get_db_session() as session:
            now = datetime.now(timezone.utc)

            # Find open service requests linked to AMC contracts
            result = await session.execute(
                select(ServiceRequest)
                .options(
                    selectinload(ServiceRequest.amc_contract).selectinload(AMCContract.plan)
                )
                .where(
                    and_(
                        ServiceRequest.amc_id.isnot(None),
                        ServiceRequest.status.in_([
                            "PENDING", "ASSIGNED", "SCHEDULED",
                            "EN_ROUTE", "IN_PROGRESS", "PARTS_REQUIRED"
                        ]),
                        ServiceRequest.is_sla_breached == False,
                    )
                )
            )
            open_requests = result.scalars().all()

            for sr in open_requests:
                try:
                    contract = sr.amc_contract
                    if not contract or not contract.plan:
                        continue

                    plan = contract.plan
                    response_sla = plan.response_sla_hours or 48
                    resolution_sla = plan.resolution_sla_hours or 72

                    created_at = sr.created_at
                    if not created_at:
                        continue

                    # Make timezone-aware if needed
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)

                    elapsed_hours = (now - created_at).total_seconds() / 3600

                    # Determine which SLA to check based on status
                    if sr.status in ["PENDING"]:
                        # Response SLA - time until first assignment
                        sla_hours = response_sla
                        sla_type = "response"
                    else:
                        # Resolution SLA - time until completion
                        sla_hours = resolution_sla
                        sla_type = "resolution"

                    # Set SLA breach time if not set
                    if not sr.sla_breach_at:
                        sr.sla_breach_at = created_at + timedelta(hours=sla_hours)

                    # Check for actual SLA breach
                    if elapsed_hours >= sla_hours:
                        sr.is_sla_breached = True
                        breached += 1
                        logger.warning(
                            f"SLA BREACHED: Service request {sr.id} "
                            f"({sla_type} SLA: {sla_hours}h, elapsed: {elapsed_hours:.1f}h)"
                        )
                        continue

                    # Auto-escalate at 75% of SLA time
                    threshold_75 = sla_hours * 0.75
                    if elapsed_hours >= threshold_75:
                        # Escalate priority
                        priority_escalation = {
                            "LOW": "NORMAL",
                            "NORMAL": "HIGH",
                            "HIGH": "URGENT",
                        }
                        current_priority = sr.priority or "NORMAL"
                        new_priority = priority_escalation.get(current_priority)

                        if new_priority and current_priority != "URGENT":
                            sr.priority = new_priority
                            escalated += 1
                            logger.info(
                                f"SLA escalation: Service request {sr.id} "
                                f"priority {current_priority} -> {new_priority} "
                                f"({sla_type} SLA: {sla_hours}h, "
                                f"elapsed: {elapsed_hours:.1f}h, "
                                f"threshold: {threshold_75:.1f}h)"
                            )

                except Exception as e:
                    logger.error(f"SLA check failed for SR {sr.id}: {e}")

            await session.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"SLA compliance check completed: "
            f"{escalated} escalated, {breached} breached "
            f"in {elapsed:.2f}s"
        )

    except Exception as e:
        logger.error(f"SLA compliance check failed: {e}")
        raise
