"""
DMS AI Chatbot Service

Natural language interface for DMS intelligence queries:
- Dealer performance ("Which dealers are underperforming?")
- Demand forecasting ("What's the forecast for next month?")
- Inactive dealers ("Who hasn't ordered recently?")
- Collection status ("What's the outstanding collection?")
- Scheme effectiveness ("How are our schemes performing?")
- Top dealers ("Who are the top performers?")
- Alerts ("What needs immediate attention?")
- Help
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.dms_dealer_performance import DealerPerformanceAgent
from app.services.ai.dms_demand_sensing import DemandSensingAgent
from app.services.ai.dms_scheme_effectiveness import SchemeEffectivenessAgent
from app.services.ai.dms_collection_optimizer import CollectionOptimizerAgent


INTENT_PATTERNS = {
    "dealer_performance": [
        r"(dealer|distributor).*(perform|achiev|target|score|rank)",
        r"(perform|achiev|target|score).*(dealer|distributor)",
        r"(who|which).*(underperform|behind|missing|struggling)",
        r"(critical|struggling|failing|poor).*(dealer)",
    ],
    "demand_forecast": [
        r"(demand|forecast|predict|next month|order.*next)",
        r"(what|how much).*(order|buy|sell).*next",
        r"(trend|growth|declining).*(dealer|order)",
        r"(moving average|wma|forecast)",
    ],
    "inactive_dealers": [
        r"(inactive|not ordered|no order|dormant|silent)",
        r"(dealer|distributor).*(order|active|last order)",
        r"(who|which).*(not ordering|inactive|dormant|haven.t ordered)",
        r"(30 day|60 day|lapsed)",
    ],
    "collection_status": [
        r"(collection|outstanding|overdue|payment|receivable)",
        r"(who|which).*(ow|unpaid|due|owing)",
        r"(aging|bucket|0.30|31.60|61.90|90.plus|90\+)",
        r"(how much).*(owed|due|outstanding|collect)",
        r"(credit|debt|ledger)",
    ],
    "scheme_effectiveness": [
        r"(scheme|promotion|incentive|discount).*(effect|roi|perform|work)",
        r"(which|what|how).*(scheme|promotion|incentive)",
        r"(roi|return|budget|utilization).*(scheme|promotion)",
        r"(retire|extend|promote).*(scheme)",
    ],
    "top_dealers": [
        r"(top|best|highest|leading|star).*(dealer|distributor)",
        r"(who|which).*(top|best|perform.*well|highest|leading)",
        r"(revenue|sales).*(leader|top|best)",
        r"(champion|winner|star)",
    ],
    "alerts": [
        r"(alert|warning|issue|problem|attention|urgent)",
        r"(what|any).*(alert|issue|risk|concern|problem)",
        r"(critical|urgent|immediate|action needed)",
        r"(what.s happening|status|overview)",
    ],
    "help": [
        r"(help|what can|how to|guide|what do|show me)",
        r"(capabilities|features|options|commands|examples)",
        r"^(hi|hello|hey|hola)$",
    ],
}


class DMSChatbotService:
    """NL chatbot for DMS intelligence queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _classify_intent(self, message: str) -> Tuple[str, float]:
        """Classify user message intent. Returns (intent, confidence 0-1)."""
        msg_lower = message.lower().strip()
        scores: Dict[str, int] = {}
        for intent, patterns in INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, msg_lower))
            if score > 0:
                scores[intent] = score
        if not scores:
            return "help", 0.0
        best = max(scores, key=lambda k: scores[k])
        return best, min(1.0, scores[best] / 2)

    async def chat(self, message: str) -> Dict[str, Any]:
        intent, confidence = self._classify_intent(message)
        response = await self._handle_intent(intent)
        return {
            "query": message,
            "intent": intent,
            "confidence": round(confidence, 2),
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_intent(self, intent: str) -> Dict[str, Any]:
        async_handlers = {
            "dealer_performance": self._dealer_performance,
            "demand_forecast": self._demand_forecast,
            "inactive_dealers": self._inactive_dealers,
            "collection_status": self._collection_status,
            "scheme_effectiveness": self._scheme_effectiveness,
            "top_dealers": self._top_dealers,
            "alerts": self._alerts,
        }
        if intent in async_handlers:
            return await async_handlers[intent]()
        return self._help()

    # ---- Intent Handlers ----

    async def _dealer_performance(self) -> Dict:
        data = await DealerPerformanceAgent(self.db).run()
        s = data.get("summary", {})
        total = s.get("total", 0)
        critical = s.get("critical", 0)
        high = s.get("high", 0)
        medium = s.get("medium", 0)
        ok = s.get("ok", 0)
        scores = data.get("dealer_scores", [])
        needs_attention = [
            d["name"] for d in scores if d.get("severity") in ("CRITICAL", "HIGH")
        ][:4]

        lines = [f"Dealer Performance Overview ({total} active dealers):"]
        if critical:
            lines.append(f"🔴 {critical} CRITICAL — below 50% of target")
        if high:
            lines.append(f"🟠 {high} HIGH risk — 50–70% of target")
        if medium:
            lines.append(f"🟡 {medium} MEDIUM — 70–85% of target")
        if ok:
            lines.append(f"🟢 {ok} on track (≥ 85% of target)")
        if needs_attention:
            lines.append(f"\nNeeds attention: {', '.join(needs_attention)}")
        if not total:
            lines = ["No dealer performance data found. Add dealer targets to see scores."]

        return {
            "type": "dealer_performance",
            "text": "\n".join(lines),
            "data": scores[:5],
            "summary": s,
        }

    async def _demand_forecast(self) -> Dict:
        data = await DemandSensingAgent(self.db).run()
        s = data.get("summary", {})
        forecast = s.get("forecast_next_month_total", 0)
        current = s.get("current_month_revenue", 0)
        mom = s.get("mom_growth_pct", 0)
        forecasts = data.get("dealer_forecasts", [])
        top3 = forecasts[:3]

        lines = [
            f"Demand Forecast:",
            f"📅 Next month forecast: ₹{forecast:,.0f}",
            f"📊 Current month revenue: ₹{current:,.0f}",
            f"📈 Month-on-month growth: {mom:+.1f}%",
        ]
        if top3:
            lines.append("\nTop dealers by next-month forecast:")
            for d in top3:
                lines.append(f"  • {d['name']}: ₹{d.get('forecast_next_month', 0):,.0f}")
        anomalies = [d for d in forecasts if d.get("anomaly")]
        if anomalies:
            lines.append(f"\n⚠️ {len(anomalies)} dealer(s) with demand anomaly detected")

        return {
            "type": "demand_forecast",
            "text": "\n".join(lines),
            "data": top3,
            "summary": s,
        }

    async def _inactive_dealers(self) -> Dict:
        data = await DemandSensingAgent(self.db).run()
        inactive = data.get("inactive_dealers", [])
        n = len(inactive)

        if not inactive:
            text = "✅ All dealers have placed orders within the last 30 days."
        else:
            lines = [f"⚠️ {n} dealer(s) inactive for 30+ days:"]
            for d in inactive[:5]:
                lines.append(
                    f"  • {d['dealer']}: {d['days_inactive']} days "
                    f"(last order: {d['last_order']})"
                )
            if n > 5:
                lines.append(f"  ... and {n - 5} more")
            lines.append("\nRecommendation: Initiate re-engagement calls + special offer.")
            text = "\n".join(lines)

        return {"type": "inactive_dealers", "text": text, "data": inactive[:10]}

    async def _collection_status(self) -> Dict:
        data = await CollectionOptimizerAgent(self.db).run()
        s = data.get("summary", {})
        buckets = data.get("aging_buckets", {})
        total_overdue = s.get("total_overdue", 0)
        critical = s.get("critical_dealers", 0)
        priority = data.get("priority_list", [])[:4]

        lines = [
            f"Collection Status:",
            f"💰 Total outstanding: ₹{s.get('total_outstanding', 0):,.0f}",
            f"⏰ Overdue: ₹{total_overdue:,.0f} across {s.get('dealers_with_overdue', 0)} dealers",
        ]
        if critical:
            lines.append(f"🔴 {critical} dealer(s) CRITICAL (90+ days overdue)")
        lines.append("\nAging buckets:")
        for key, label in [
            ("0_30_days", "0–30 days"),
            ("31_60_days", "31–60 days"),
            ("61_90_days", "61–90 days"),
            ("90_plus_days", "90+ days"),
        ]:
            amt = buckets.get(key, {}).get("amount", 0)
            if amt > 0:
                lines.append(f"  • {label}: ₹{amt:,.0f}")
        if priority:
            lines.append("\nPriority collections:")
            for d in priority:
                lines.append(
                    f"  • {d['dealer_name']}: ₹{d.get('total_overdue', 0):,.0f} "
                    f"({d.get('max_days_overdue', 0)} days)"
                )

        return {
            "type": "collection_status",
            "text": "\n".join(lines),
            "data": priority,
            "summary": s,
        }

    async def _scheme_effectiveness(self) -> Dict:
        data = await SchemeEffectivenessAgent(self.db).run()
        s = data.get("summary", {})
        schemes = data.get("schemes", [])

        if not schemes:
            return {
                "type": "scheme_effectiveness",
                "text": "No active schemes found. Create a scheme in Distribution > Dealers.",
                "data": [],
            }

        retire = [sc["scheme_name"] for sc in schemes if sc.get("recommendation") == "RETIRE"]
        extend = [sc["scheme_name"] for sc in schemes if sc.get("recommendation") == "EXTEND"]
        promote = [sc["scheme_name"] for sc in schemes if sc.get("recommendation") == "PROMOTE"]

        lines = [
            f"Scheme Effectiveness:",
            f"📋 Active schemes: {s.get('active_schemes', 0)}",
            f"📊 Average ROI: {s.get('avg_roi_pct', 0):.1f}%",
            f"💸 Total discount given: ₹{s.get('total_discount_given', 0):,.0f}",
            f"📦 Orders driven: ₹{s.get('total_order_value_driven', 0):,.0f}",
        ]
        if retire:
            lines.append(f"\n⛔ Retire (low ROI + low participation): {', '.join(retire[:2])}")
        if extend:
            lines.append(f"\n✅ Extend (high ROI, near budget): {', '.join(extend[:2])}")
        if promote:
            lines.append(f"\n📢 Promote (low utilization): {', '.join(promote[:2])}")

        return {
            "type": "scheme_effectiveness",
            "text": "\n".join(lines),
            "data": schemes[:5],
            "summary": s,
        }

    async def _top_dealers(self) -> Dict:
        data = await DealerPerformanceAgent(self.db).run()
        scores = data.get("dealer_scores", [])
        ranked = [d for d in scores if d.get("achievement_pct") is not None]
        ranked.sort(key=lambda x: -(x.get("achievement_pct") or 0))
        top5 = ranked[:5]

        if not top5:
            return {
                "type": "top_dealers",
                "text": "No dealer performance data available yet. Set monthly targets to enable ranking.",
                "data": [],
            }

        lines = ["🏆 Top Performing Dealers:"]
        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        for i, d in enumerate(top5):
            line = f"  {medals[i]} {d['name']} ({d.get('tier', 'N/A')}): {d.get('achievement_pct', 0):.0f}%"
            if d.get("growth_pct") is not None:
                line += f"  |  {d['growth_pct']:+.1f}% MoM"
            lines.append(line)

        return {"type": "top_dealers", "text": "\n".join(lines), "data": top5}

    async def _alerts(self) -> Dict:
        from app.services.ai.dms_command_center import DMSCommandCenterAgent

        data = await DMSCommandCenterAgent(self.db).run()
        alerts = data.get("alerts", [])

        if not alerts:
            return {
                "type": "alerts",
                "text": "✅ No active alerts. All DMS metrics within normal range.",
                "data": [],
            }

        critical = [a for a in alerts if a.get("severity") == "CRITICAL"]
        high = [a for a in alerts if a.get("severity") == "HIGH"]
        medium = [a for a in alerts if a.get("severity") == "MEDIUM"]

        lines = [f"⚠️ {len(alerts)} active DMS alerts:"]
        if critical:
            lines.append(f"\n🔴 CRITICAL ({len(critical)}):")
            for a in critical[:3]:
                lines.append(f"  • {a.get('message', '')}")
                lines.append(f"    → {a.get('action', '')}")
        if high:
            lines.append(f"\n🟠 HIGH ({len(high)}):")
            for a in high[:3]:
                lines.append(f"  • {a.get('message', '')}")
        if medium:
            lines.append(f"\n🟡 MEDIUM ({len(medium)}):")
            for a in medium[:2]:
                lines.append(f"  • {a.get('message', '')}")

        return {"type": "alerts", "text": "\n".join(lines), "data": alerts[:10]}

    def _help(self) -> Dict:
        text = (
            "Hi! I'm your DMS AI Assistant. I can answer questions about your dealer network.\n\n"
            "Try asking:\n"
            "📊 'Which dealers are underperforming?'\n"
            "📈 'What is next month's demand forecast?'\n"
            "😴 'Which dealers haven't ordered recently?'\n"
            "💰 'What is our outstanding collection?'\n"
            "🎯 'How are our schemes performing?'\n"
            "🏆 'Who are the top dealers?'\n"
            "⚠️  'What alerts need attention?'"
        )
        return {"type": "help", "text": text, "data": []}


