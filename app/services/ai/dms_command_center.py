"""
DMS AI Command Centre — Orchestrates all DMS AI agents.

Runs all 4 agents in parallel via asyncio.gather() and combines results
into a unified command centre view with aggregated alerts.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.dms_dealer_performance import DealerPerformanceAgent
from app.services.ai.dms_demand_sensing import DemandSensingAgent
from app.services.ai.dms_scheme_effectiveness import SchemeEffectivenessAgent
from app.services.ai.dms_collection_optimizer import CollectionOptimizerAgent


class DMSCommandCenterAgent:
    """
    Runs all DMS AI agents in parallel and combines their results
    into a unified command centre view.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self) -> Dict[str, Any]:
        # Run all agents in parallel
        results = await asyncio.gather(
            DealerPerformanceAgent(self.db).run(),
            DemandSensingAgent(self.db).run(),
            SchemeEffectivenessAgent(self.db).run(),
            CollectionOptimizerAgent(self.db).run(),
            return_exceptions=True,
        )

        dealer_perf, demand, schemes, collections = results

        # Handle any agent failures gracefully
        def _safe(r: Any, agent_name: str) -> Dict:
            if isinstance(r, Exception):
                return {
                    "agent": agent_name,
                    "status": "error",
                    "error": str(r),
                    "summary": {},
                    "alerts": [],
                }
            return r

        dealer_perf = _safe(dealer_perf, "dealer-performance")
        demand = _safe(demand, "demand-sensing")
        schemes = _safe(schemes, "scheme-effectiveness")
        collections = _safe(collections, "collection-optimizer")

        # Combine + deduplicate alerts (top 15), sorted by severity
        all_alerts = []
        for result in [dealer_perf, demand, schemes, collections]:
            all_alerts.extend(result.get("alerts", []))

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_alerts.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

        dp_sum = dealer_perf.get("summary", {})
        col_sum = collections.get("summary", {})
        dem_sum = demand.get("summary", {})
        sch_sum = schemes.get("summary", {})

        summary = {
            "active_dealers": dp_sum.get("total", 0),
            "critical_dealers": dp_sum.get("critical", 0),
            "high_risk_dealers": dp_sum.get("high", 0),
            "total_outstanding": col_sum.get("total_outstanding", 0),
            "total_overdue": col_sum.get("total_overdue", 0),
            "dealers_with_overdue": col_sum.get("dealers_with_overdue", 0),
            "forecast_next_month": dem_sum.get("forecast_next_month_total", 0),
            "inactive_dealers": dem_sum.get("inactive_dealers", 0),
            "active_schemes": sch_sum.get("active_schemes", 0),
            "avg_scheme_roi_pct": sch_sum.get("avg_roi_pct", 0),
            "total_alerts": len(all_alerts),
            "agents_status": {
                "dealer_performance": dealer_perf.get("status", "error"),
                "demand_sensing": demand.get("status", "error"),
                "scheme_effectiveness": schemes.get("status", "error"),
                "collection_optimizer": collections.get("status", "error"),
            },
        }

        return {
            "agent": "dms-command-center",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "alerts": all_alerts[:15],
            "dealer_performance": dealer_perf,
            "demand_sensing": demand,
            "scheme_effectiveness": schemes,
            "collection_optimizer": collections,
            "status": "completed",
        }
