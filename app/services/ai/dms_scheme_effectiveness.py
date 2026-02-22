"""
DMS Scheme Effectiveness Agent

Analyses dealer schemes for:
- ROI: (order_value - discount) / discount * 100
- Budget utilization % with high/low flags
- Participation rate: participating dealers / eligible
- Recommendations: retire low-ROI, extend high-ROI near budget
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dealer import Dealer, DealerScheme, DealerSchemeApplication


class SchemeEffectivenessAgent:
    """
    Evaluates effectiveness of dealer schemes and promotions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self) -> Dict[str, Any]:
        today = date.today()

        # Get active schemes
        schemes_result = await self.db.execute(
            select(DealerScheme)
            .where(and_(
                DealerScheme.is_active == True,
                DealerScheme.end_date >= today
            ))
            .order_by(DealerScheme.start_date.desc())
        )
        schemes = schemes_result.scalars().all()

        if not schemes:
            return self._empty_result()

        scheme_ids = [s.id for s in schemes]

        # Get application stats per scheme
        app_stats_result = await self.db.execute(
            select(
                DealerSchemeApplication.scheme_id,
                func.count(distinct(DealerSchemeApplication.dealer_id)).label("participating_dealers"),
                func.count(DealerSchemeApplication.id).label("application_count"),
                func.sum(DealerSchemeApplication.order_value).label("total_order_value"),
                func.sum(DealerSchemeApplication.discount_calculated).label("total_discount"),
            )
            .where(DealerSchemeApplication.scheme_id.in_(scheme_ids))
            .group_by(DealerSchemeApplication.scheme_id)
        )
        app_stats = {r.scheme_id: {
            "participating_dealers": r.participating_dealers,
            "application_count": r.application_count,
            "total_order_value": float(r.total_order_value or 0),
            "total_discount": float(r.total_discount or 0),
        } for r in app_stats_result.fetchall()}

        # Get total active dealers for participation rate
        total_dealers_result = await self.db.execute(
            select(func.count(Dealer.id)).where(Dealer.status == "ACTIVE")
        )
        total_active_dealers = total_dealers_result.scalar() or 1

        # Analyse each scheme
        analysed_schemes = []
        alerts = []

        for s in schemes:
            stats = app_stats.get(s.id, {
                "participating_dealers": 0,
                "application_count": 0,
                "total_order_value": 0.0,
                "total_discount": 0.0,
            })

            total_discount = stats["total_discount"]
            total_order_value = stats["total_order_value"]
            participating = stats["participating_dealers"]
            utilized = float(s.utilized_budget or 0)
            total_budget = float(s.total_budget) if s.total_budget else None

            # ROI calculation
            roi_pct = None
            if total_discount > 0:
                net_revenue = total_order_value - total_discount
                roi_pct = round((net_revenue / total_discount) * 100, 1)

            # Budget utilization
            budget_utilization_pct = None
            if total_budget and total_budget > 0:
                budget_utilization_pct = round(utilized / total_budget * 100, 1)

            # Participation rate
            participation_rate = round(participating / total_active_dealers * 100, 1)

            # Days remaining
            days_remaining = (s.end_date - today).days

            # Status flags
            flags = []
            if budget_utilization_pct is not None and budget_utilization_pct > 90:
                flags.append("NEAR_BUDGET_LIMIT")
            if budget_utilization_pct is not None and budget_utilization_pct < 20 and days_remaining < 30:
                flags.append("LOW_UTILIZATION")
            if participation_rate < 10:
                flags.append("LOW_PARTICIPATION")
            if roi_pct is not None and roi_pct < 200:
                flags.append("LOW_ROI")
            if days_remaining <= 7:
                flags.append("EXPIRING_SOON")

            # Recommendation
            if "LOW_ROI" in flags and "LOW_PARTICIPATION" in flags:
                recommendation = "RETIRE"
                rec_detail = "Low ROI and low participation — consider retiring this scheme"
            elif "NEAR_BUDGET_LIMIT" in flags and roi_pct and roi_pct > 500:
                recommendation = "EXTEND"
                rec_detail = "High ROI, near budget — recommend extending budget and scheme duration"
            elif "EXPIRING_SOON" in flags and participation_rate > 30:
                recommendation = "EXTEND"
                rec_detail = "Popular scheme expiring soon — consider extending"
            elif "LOW_UTILIZATION" in flags:
                recommendation = "PROMOTE"
                rec_detail = "Low utilization — increase dealer awareness and push marketing"
            else:
                recommendation = "MAINTAIN"
                rec_detail = "Scheme performing within normal parameters"

            scheme_data = {
                "scheme_id": str(s.id),
                "scheme_code": s.scheme_code,
                "scheme_name": s.scheme_name,
                "scheme_type": s.scheme_type,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
                "days_remaining": days_remaining,
                "participating_dealers": participating,
                "application_count": stats["application_count"],
                "total_order_value": round(total_order_value, 2),
                "total_discount": round(total_discount, 2),
                "roi_pct": roi_pct,
                "total_budget": total_budget,
                "utilized_budget": round(utilized, 2),
                "budget_utilization_pct": budget_utilization_pct,
                "participation_rate": participation_rate,
                "flags": flags,
                "recommendation": recommendation,
                "recommendation_detail": rec_detail,
            }
            analysed_schemes.append(scheme_data)

            # Alerts
            if "NEAR_BUDGET_LIMIT" in flags:
                alerts.append({
                    "type": "SCHEME_BUDGET",
                    "severity": "HIGH",
                    "scheme": s.scheme_name,
                    "message": f"'{s.scheme_name}' at {budget_utilization_pct:.0f}% budget utilization",
                    "action": "Review and approve budget extension"
                })
            if "EXPIRING_SOON" in flags and participation_rate > 20:
                alerts.append({
                    "type": "SCHEME_EXPIRY",
                    "severity": "MEDIUM",
                    "scheme": s.scheme_name,
                    "message": f"'{s.scheme_name}' expires in {days_remaining} days (participation: {participation_rate:.0f}%)",
                    "action": "Decide on extension or replacement scheme"
                })

        # Sort by ROI descending
        analysed_schemes.sort(key=lambda x: -(x["roi_pct"] or 0))

        total_discount_given = sum(s["total_discount"] for s in analysed_schemes)
        total_order_driven = sum(s["total_order_value"] for s in analysed_schemes)
        avg_roi = (
            sum(s["roi_pct"] for s in analysed_schemes if s["roi_pct"] is not None) /
            max(1, sum(1 for s in analysed_schemes if s["roi_pct"] is not None))
        )

        return {
            "agent": "scheme-effectiveness",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "active_schemes": len(schemes),
                "total_discount_given": round(total_discount_given, 2),
                "total_order_value_driven": round(total_order_driven, 2),
                "avg_roi_pct": round(avg_roi, 1),
                "extend_count": sum(1 for s in analysed_schemes if s["recommendation"] == "EXTEND"),
                "retire_count": sum(1 for s in analysed_schemes if s["recommendation"] == "RETIRE"),
            },
            "schemes": analysed_schemes,
            "alerts": alerts[:8],
            "status": "completed"
        }

    def _empty_result(self) -> Dict:
        return {
            "agent": "scheme-effectiveness",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": {"active_schemes": 0, "total_discount_given": 0, "total_order_value_driven": 0, "avg_roi_pct": 0, "extend_count": 0, "retire_count": 0},
            "schemes": [],
            "alerts": [],
            "status": "completed"
        }
