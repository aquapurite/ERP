"""
DMS Dealer Performance Agent

Scores dealers on:
- Sales achievement (revenue vs target)
- Payment compliance (overdue amounts, days overdue)
- Growth trajectory (MoM trend)
- Claim rate (claims per orders)
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dealer import Dealer, DealerTarget, DealerCreditLedger
from app.models.order import Order


class DealerPerformanceAgent:
    """
    Analyses dealer performance and scores dealers.
    Severity: CRITICAL (<50%), HIGH (<70%), MEDIUM (<85%), OK (>=85%)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self) -> Dict[str, Any]:
        today = date.today()
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)
        six_months_ago = today - timedelta(days=180)

        # Get active dealers
        dealers_result = await self.db.execute(
            select(Dealer.id, Dealer.name, Dealer.dealer_code, Dealer.tier,
                   Dealer.credit_limit, Dealer.outstanding_amount, Dealer.status)
            .where(Dealer.status == "ACTIVE")
            .order_by(Dealer.name)
        )
        dealers = dealers_result.fetchall()

        if not dealers:
            return self._empty_result()

        dealer_ids = [d.id for d in dealers]

        # Get current month orders per dealer
        orders_result = await self.db.execute(
            select(Order.dealer_id,
                   func.count(Order.id).label("order_count"),
                   func.sum(Order.total_amount).label("revenue"))
            .where(and_(
                Order.dealer_id.in_(dealer_ids),
                func.date(Order.created_at) >= month_start,
                Order.status.notin_(["CANCELLED"])
            ))
            .group_by(Order.dealer_id)
        )
        current_orders = {r.dealer_id: {"count": r.order_count, "revenue": float(r.revenue or 0)}
                         for r in orders_result.fetchall()}

        # Get monthly targets for current month
        targets_result = await self.db.execute(
            select(DealerTarget.dealer_id,
                   DealerTarget.revenue_target,
                   DealerTarget.quantity_target)
            .where(and_(
                DealerTarget.dealer_id.in_(dealer_ids),
                DealerTarget.target_period == "MONTHLY",
                DealerTarget.target_year == today.year,
                DealerTarget.target_month == today.month
            ))
        )
        targets = {r.dealer_id: {"revenue": float(r.revenue_target or 0),
                                  "orders": int(r.quantity_target or 0)}
                  for r in targets_result.fetchall()}

        # Get overdue ledger entries
        overdue_result = await self.db.execute(
            select(DealerCreditLedger.dealer_id,
                   func.sum(DealerCreditLedger.debit_amount - DealerCreditLedger.credit_amount).label("overdue"),
                   func.avg(DealerCreditLedger.days_overdue).label("avg_days"))
            .where(and_(
                DealerCreditLedger.dealer_id.in_(dealer_ids),
                DealerCreditLedger.is_settled == False,
                DealerCreditLedger.days_overdue > 0,
                DealerCreditLedger.transaction_type == "INVOICE"
            ))
            .group_by(DealerCreditLedger.dealer_id)
        )
        overdue_data = {r.dealer_id: {"amount": float(r.overdue or 0),
                                       "avg_days": float(r.avg_days or 0)}
                       for r in overdue_result.fetchall()}

        # Get 6-month revenue trend
        trend_result = await self.db.execute(
            select(Order.dealer_id,
                   func.date_trunc('month', Order.created_at).label("month"),
                   func.sum(Order.total_amount).label("revenue"))
            .where(and_(
                Order.dealer_id.in_(dealer_ids),
                func.date(Order.created_at) >= six_months_ago,
                Order.status.notin_(["CANCELLED"])
            ))
            .group_by(Order.dealer_id, func.date_trunc('month', Order.created_at))
        )
        trend_rows = trend_result.fetchall()
        trend_by_dealer: Dict = {}
        for row in trend_rows:
            did = row.dealer_id
            if did not in trend_by_dealer:
                trend_by_dealer[did] = []
            trend_by_dealer[did].append(float(row.revenue or 0))

        # Score each dealer
        scored_dealers = []
        alerts = []
        summary = {"critical": 0, "high": 0, "medium": 0, "ok": 0, "total": len(dealers)}

        for d in dealers:
            ord_data = current_orders.get(d.id, {"count": 0, "revenue": 0})
            tgt_data = targets.get(d.id, {"revenue": 0, "orders": 0})
            ovd_data = overdue_data.get(d.id, {"amount": 0, "avg_days": 0})
            trend = trend_by_dealer.get(d.id, [])

            # Achievement %
            revenue_achieved = ord_data["revenue"]
            revenue_target = tgt_data["revenue"]
            achievement_pct = (revenue_achieved / revenue_target * 100) if revenue_target > 0 else None

            # Credit utilization %
            outstanding = float(d.outstanding_amount or 0)
            credit_limit = float(d.credit_limit or 1)
            credit_utilization = min(100, outstanding / credit_limit * 100) if credit_limit > 0 else 0

            # Growth: compare last 2 months in trend
            growth_pct = None
            declining_months = 0
            if len(trend) >= 2:
                growth_pct = ((trend[-1] - trend[-2]) / trend[-2] * 100) if trend[-2] > 0 else 0
                # Count declining months
                for i in range(1, len(trend)):
                    if trend[i] < trend[i - 1]:
                        declining_months += 1

            # Severity
            if achievement_pct is not None:
                if achievement_pct < 50:
                    severity = "CRITICAL"
                    summary["critical"] += 1
                elif achievement_pct < 70:
                    severity = "HIGH"
                    summary["high"] += 1
                elif achievement_pct < 85:
                    severity = "MEDIUM"
                    summary["medium"] += 1
                else:
                    severity = "OK"
                    summary["ok"] += 1
            else:
                severity = "NO_TARGET"
                summary["ok"] += 1

            dealer_score = {
                "dealer_id": str(d.id),
                "dealer_code": d.dealer_code,
                "name": d.name,
                "tier": d.tier,
                "severity": severity,
                "revenue_achieved": revenue_achieved,
                "revenue_target": revenue_target,
                "achievement_pct": round(achievement_pct, 1) if achievement_pct is not None else None,
                "order_count": ord_data["count"],
                "outstanding_amount": outstanding,
                "credit_limit": credit_limit,
                "credit_utilization_pct": round(credit_utilization, 1),
                "overdue_amount": ovd_data["amount"],
                "avg_days_overdue": round(ovd_data["avg_days"], 0),
                "revenue_trend": trend[-6:] if trend else [],
                "growth_pct": round(growth_pct, 1) if growth_pct is not None else None,
                "declining_months": declining_months,
            }
            scored_dealers.append(dealer_score)

            # Generate alerts
            if severity == "CRITICAL":
                alerts.append({
                    "type": "DEALER_PERFORMANCE",
                    "severity": "CRITICAL",
                    "dealer": d.name,
                    "message": f"{d.name} achievement is {achievement_pct:.0f}% of target — immediate attention needed",
                    "action": "Schedule urgent review call with dealer"
                })
            elif ovd_data["avg_days"] > 90:
                alerts.append({
                    "type": "PAYMENT_OVERDUE",
                    "severity": "HIGH",
                    "dealer": d.name,
                    "message": f"{d.name} has ₹{ovd_data['amount']:,.0f} overdue for {ovd_data['avg_days']:.0f}+ days",
                    "action": "Initiate credit hold + field visit"
                })
            elif declining_months >= 3:
                alerts.append({
                    "type": "DECLINING_TREND",
                    "severity": "MEDIUM",
                    "dealer": d.name,
                    "message": f"{d.name} has {declining_months} consecutive declining months",
                    "action": "Review market conditions and support needs"
                })

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "OK": 3, "NO_TARGET": 4}
        scored_dealers.sort(key=lambda x: (severity_order.get(x["severity"], 5), -(x["achievement_pct"] or 0)))

        recommendations = self._generate_recommendations(summary, scored_dealers)

        return {
            "agent": "dealer-performance",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "alerts": alerts[:10],
            "dealer_scores": scored_dealers[:20],
            "recommendations": recommendations,
            "status": "completed"
        }

    def _generate_recommendations(self, summary: Dict, dealers: List) -> List[Dict]:
        recs = []
        if summary["critical"] > 0:
            recs.append({
                "priority": "CRITICAL",
                "title": f"{summary['critical']} dealer(s) critically underperforming",
                "detail": "Launch emergency support programme: joint sales visits, marketing support, extended credit terms",
                "impact": "HIGH"
            })
        if summary["high"] > 0:
            recs.append({
                "priority": "HIGH",
                "title": f"{summary['high']} dealer(s) need performance improvement",
                "detail": "Schedule monthly review calls, offer scheme incentives to boost offtake",
                "impact": "MEDIUM"
            })
        overdue_dealers = [d for d in dealers if d["overdue_amount"] > 0]
        if overdue_dealers:
            total_overdue = sum(d["overdue_amount"] for d in overdue_dealers)
            recs.append({
                "priority": "HIGH",
                "title": f"₹{total_overdue:,.0f} overdue across {len(overdue_dealers)} dealers",
                "detail": "Initiate structured collection drive with aging-based priority",
                "impact": "HIGH"
            })
        return recs

    def _empty_result(self) -> Dict:
        return {
            "agent": "dealer-performance",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": {"critical": 0, "high": 0, "medium": 0, "ok": 0, "total": 0},
            "alerts": [],
            "dealer_scores": [],
            "recommendations": [{"priority": "INFO", "title": "No active dealers found", "detail": "Add dealers to start tracking performance", "impact": "LOW"}],
            "status": "completed"
        }
