"""
DMS Demand Sensing Agent

Analyses dealer order trends:
- Monthly order values over 6 months per dealer
- Weighted moving average forecast (alpha=0.3)
- Seasonal z-score anomaly detection
- Inactive dealer flagging (30+ days no order)
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
import statistics

from app.models.dealer import Dealer
from app.models.order import Order


def _weighted_moving_average(values: List[float], alpha: float = 0.3) -> float:
    """Simple exponential weighted moving average forecast."""
    if not values:
        return 0.0
    forecast = values[0]
    for v in values[1:]:
        forecast = alpha * v + (1 - alpha) * forecast
    return forecast


def _z_score(value: float, values: List[float]) -> Optional[float]:
    """Calculate z-score for anomaly detection."""
    if len(values) < 2:
        return None
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    if stdev == 0:
        return 0.0
    return (value - mean) / stdev


class DemandSensingAgent:
    """
    Senses demand patterns from dealer orders and generates forecasts.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self) -> Dict[str, Any]:
        today = date.today()
        six_months_ago = today - timedelta(days=180)
        thirty_days_ago = today - timedelta(days=30)

        # Get active dealers
        dealers_result = await self.db.execute(
            select(Dealer.id, Dealer.name, Dealer.dealer_code, Dealer.tier, Dealer.region)
            .where(Dealer.status == "ACTIVE")
        )
        dealers = {d.id: d for d in dealers_result.fetchall()}

        if not dealers:
            return self._empty_result()

        dealer_ids = list(dealers.keys())

        # Monthly order aggregates per dealer (last 6 months)
        monthly_result = await self.db.execute(
            select(
                Order.dealer_id,
                extract('year', Order.created_at).label("year"),
                extract('month', Order.created_at).label("month"),
                func.sum(Order.total_amount).label("revenue"),
                func.count(Order.id).label("order_count")
            )
            .where(and_(
                Order.dealer_id.in_(dealer_ids),
                func.date(Order.created_at) >= six_months_ago,
                Order.status.notin_(["CANCELLED"])
            ))
            .group_by(
                Order.dealer_id,
                extract('year', Order.created_at),
                extract('month', Order.created_at)
            )
            .order_by(
                Order.dealer_id,
                extract('year', Order.created_at),
                extract('month', Order.created_at)
            )
        )
        monthly_rows = monthly_result.fetchall()

        # Build monthly timeline
        dealer_monthly: Dict = {}
        for row in monthly_rows:
            did = row.dealer_id
            if did not in dealer_monthly:
                dealer_monthly[did] = []
            dealer_monthly[did].append({
                "year": int(row.year),
                "month": int(row.month),
                "revenue": float(row.revenue or 0),
                "order_count": int(row.order_count),
            })

        # Last order date per dealer
        last_order_result = await self.db.execute(
            select(Order.dealer_id, func.max(func.date(Order.created_at)).label("last_order"))
            .where(and_(
                Order.dealer_id.in_(dealer_ids),
                Order.status.notin_(["CANCELLED"])
            ))
            .group_by(Order.dealer_id)
        )
        last_order = {r.dealer_id: r.last_order for r in last_order_result.fetchall()}

        # Overall monthly trend (all dealers combined)
        overall_monthly_result = await self.db.execute(
            select(
                extract('year', Order.created_at).label("year"),
                extract('month', Order.created_at).label("month"),
                func.sum(Order.total_amount).label("revenue"),
                func.count(Order.id).label("orders")
            )
            .where(and_(
                Order.dealer_id.in_(dealer_ids),
                func.date(Order.created_at) >= six_months_ago,
                Order.status.notin_(["CANCELLED"])
            ))
            .group_by(extract('year', Order.created_at), extract('month', Order.created_at))
            .order_by(extract('year', Order.created_at), extract('month', Order.created_at))
        )
        overall_monthly = [{"year": int(r.year), "month": int(r.month),
                            "revenue": float(r.revenue or 0), "orders": int(r.orders)}
                          for r in overall_monthly_result.fetchall()]

        # Per-dealer forecasts
        dealer_forecasts = []
        inactive_dealers = []
        alerts = []

        for did, dealer in dealers.items():
            monthly_data = dealer_monthly.get(did, [])
            revenues = [m["revenue"] for m in monthly_data]
            lo = last_order.get(did)
            days_since_order = (today - lo).days if lo else 999

            # Forecast
            forecast_next_month = _weighted_moving_average(revenues) if revenues else 0.0

            # Anomaly detection on latest month
            anomaly = None
            if len(revenues) >= 3:
                z = _z_score(revenues[-1], revenues)
                if z is not None and abs(z) > 2:
                    anomaly = "SPIKE" if z > 0 else "DROP"

            # Growth trend
            growth_pct = None
            if len(revenues) >= 2 and revenues[-2] > 0:
                growth_pct = round((revenues[-1] - revenues[-2]) / revenues[-2] * 100, 1)

            dealer_data = {
                "dealer_id": str(did),
                "dealer_code": dealer.dealer_code,
                "name": dealer.name,
                "tier": dealer.tier,
                "region": dealer.region,
                "monthly_revenues": revenues[-6:],
                "monthly_labels": [f"{m['year']}-{m['month']:02d}" for m in monthly_data[-6:]],
                "total_6m_revenue": round(sum(revenues), 2),
                "avg_monthly_revenue": round(sum(revenues) / len(revenues), 2) if revenues else 0,
                "forecast_next_month": round(forecast_next_month, 2),
                "growth_pct": growth_pct,
                "anomaly": anomaly,
                "days_since_last_order": days_since_order,
                "last_order_date": lo.isoformat() if lo else None,
                "is_inactive": days_since_order > 30,
            }
            dealer_forecasts.append(dealer_data)

            if days_since_order > 30:
                inactive_dealers.append({
                    "dealer": dealer.name,
                    "days_inactive": days_since_order,
                    "last_order": lo.isoformat() if lo else "Never"
                })
                alerts.append({
                    "type": "INACTIVE_DEALER",
                    "severity": "MEDIUM" if days_since_order < 60 else "HIGH",
                    "dealer": dealer.name,
                    "message": f"{dealer.name} has not ordered in {days_since_order} days",
                    "action": "Initiate re-engagement: call + special offer"
                })

            if anomaly == "DROP":
                alerts.append({
                    "type": "DEMAND_DROP",
                    "severity": "HIGH",
                    "dealer": dealer.name,
                    "message": f"Significant demand drop detected for {dealer.name} (statistical anomaly)",
                    "action": "Investigate root cause: competition, stock issues, or relationship"
                })

        # Sort by forecast descending
        dealer_forecasts.sort(key=lambda x: -x["forecast_next_month"])

        # Overall forecast
        all_revenues = [m["revenue"] for m in overall_monthly]
        total_forecast = _weighted_moving_average(all_revenues) if all_revenues else 0.0

        return {
            "agent": "demand-sensing",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "active_dealers_analysed": len(dealers),
                "inactive_dealers": len(inactive_dealers),
                "forecast_next_month_total": round(total_forecast, 2),
                "current_month_revenue": round(all_revenues[-1] if all_revenues else 0, 2),
                "mom_growth_pct": round(
                    (all_revenues[-1] - all_revenues[-2]) / all_revenues[-2] * 100
                    if len(all_revenues) >= 2 and all_revenues[-2] > 0 else 0, 1
                ),
            },
            "overall_trend": overall_monthly,
            "dealer_forecasts": dealer_forecasts[:20],
            "inactive_dealers": inactive_dealers[:10],
            "alerts": alerts[:10],
            "status": "completed"
        }

    def _empty_result(self) -> Dict:
        return {
            "agent": "demand-sensing",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": {"active_dealers_analysed": 0, "inactive_dealers": 0, "forecast_next_month_total": 0, "current_month_revenue": 0, "mom_growth_pct": 0},
            "overall_trend": [],
            "dealer_forecasts": [],
            "inactive_dealers": [],
            "alerts": [],
            "status": "completed"
        }
