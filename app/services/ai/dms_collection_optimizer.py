"""
DMS Collection Optimizer Agent

Analyses dealer outstanding balances with:
- Aging buckets (0-30, 31-60, 61-90, 90+ days)
- Payment prediction (historical avg days)
- Priority ranking by overdue score
- Collection strategies per bucket
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dealer import Dealer, DealerCreditLedger


COLLECTION_STRATEGIES = {
    "bucket_90_plus": "Credit hold + mandatory field visit + legal notice",
    "bucket_61_90":   "Escalate to senior management + daily follow-up",
    "bucket_31_60":   "Weekly follow-up call + email reminder",
    "bucket_0_30":    "Auto-reminder SMS/email at 7 & 15 days",
}


class CollectionOptimizerAgent:
    """
    Optimises collections from dealers using aging analysis and payment prediction.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self) -> Dict[str, Any]:
        today = date.today()

        # Get all unsettled INVOICE entries with dealer info
        ledger_result = await self.db.execute(
            select(
                DealerCreditLedger.dealer_id,
                DealerCreditLedger.id,
                DealerCreditLedger.reference_number,
                DealerCreditLedger.transaction_date,
                DealerCreditLedger.due_date,
                DealerCreditLedger.debit_amount,
                DealerCreditLedger.credit_amount,
                DealerCreditLedger.days_overdue,
                Dealer.name.label("dealer_name"),
                Dealer.dealer_code,
                Dealer.tier,
                Dealer.credit_limit,
                Dealer.outstanding_amount
            )
            .join(Dealer, Dealer.id == DealerCreditLedger.dealer_id)
            .where(and_(
                DealerCreditLedger.is_settled == False,
                DealerCreditLedger.transaction_type == "INVOICE",
                Dealer.status == "ACTIVE"
            ))
            .order_by(DealerCreditLedger.days_overdue.desc())
        )
        entries = ledger_result.fetchall()

        # Get payment history (settled invoices) for prediction
        payment_history_result = await self.db.execute(
            select(
                DealerCreditLedger.dealer_id,
                func.avg(DealerCreditLedger.days_overdue).label("avg_days_to_pay")
            )
            .where(and_(
                DealerCreditLedger.is_settled == True,
                DealerCreditLedger.transaction_type == "INVOICE"
            ))
            .group_by(DealerCreditLedger.dealer_id)
        )
        payment_history = {r.dealer_id: float(r.avg_days_to_pay or 0)
                          for r in payment_history_result.fetchall()}

        # Build aging buckets
        buckets = {
            "0_30": {"amount": 0.0, "count": 0, "dealers": set()},
            "31_60": {"amount": 0.0, "count": 0, "dealers": set()},
            "61_90": {"amount": 0.0, "count": 0, "dealers": set()},
            "90_plus": {"amount": 0.0, "count": 0, "dealers": set()},
        }

        dealer_outstanding: Dict = {}

        for e in entries:
            net = float(e.debit_amount or 0) - float(e.credit_amount or 0)
            if net <= 0:
                continue

            days = int(e.days_overdue or 0)
            if days <= 30:
                bucket = "0_30"
            elif days <= 60:
                bucket = "31_60"
            elif days <= 90:
                bucket = "61_90"
            else:
                bucket = "90_plus"

            buckets[bucket]["amount"] += net
            buckets[bucket]["count"] += 1
            buckets[bucket]["dealers"].add(e.dealer_id)

            # Per-dealer aggregation
            did = e.dealer_id
            if did not in dealer_outstanding:
                dealer_outstanding[did] = {
                    "dealer_id": str(did),
                    "dealer_name": e.dealer_name,
                    "dealer_code": e.dealer_code,
                    "tier": e.tier,
                    "total_outstanding": float(e.outstanding_amount or 0),
                    "invoices": [],
                    "max_days_overdue": 0,
                    "total_overdue": 0.0,
                    "credit_limit": float(e.credit_limit or 0),
                }
            dealer_outstanding[did]["invoices"].append({
                "reference": e.reference_number,
                "amount": net,
                "days_overdue": days,
                "due_date": e.due_date.isoformat() if e.due_date else None,
            })
            dealer_outstanding[did]["max_days_overdue"] = max(
                dealer_outstanding[did]["max_days_overdue"], days
            )
            dealer_outstanding[did]["total_overdue"] += net

        # Convert set to count
        for b in buckets.values():
            b["dealer_count"] = len(b["dealers"])
            del b["dealers"]

        # Priority ranking: score = overdue_amount × days_weight
        prioritized = []
        for did, data in dealer_outstanding.items():
            days_weight = 1 + (data["max_days_overdue"] / 30)
            avg_payment = payment_history.get(did, 45)
            payment_rating = max(0.1, 1 / (1 + avg_payment / 30))
            score = data["total_overdue"] * days_weight * (1 / payment_rating)

            # Collection strategy
            max_days = data["max_days_overdue"]
            if max_days > 90:
                strategy = COLLECTION_STRATEGIES["bucket_90_plus"]
                priority = "CRITICAL"
            elif max_days > 60:
                strategy = COLLECTION_STRATEGIES["bucket_61_90"]
                priority = "HIGH"
            elif max_days > 30:
                strategy = COLLECTION_STRATEGIES["bucket_31_60"]
                priority = "MEDIUM"
            else:
                strategy = COLLECTION_STRATEGIES["bucket_0_30"]
                priority = "LOW"

            # Predicted payment date
            predicted_days = max(0, avg_payment - data["max_days_overdue"])
            predicted_date = (date.today() + timedelta(days=int(predicted_days))).isoformat()

            prioritized.append({
                **data,
                "collection_score": round(score, 0),
                "priority": priority,
                "strategy": strategy,
                "avg_historical_payment_days": round(avg_payment, 0),
                "predicted_payment_date": predicted_date,
                "invoice_count": len(data["invoices"]),
            })

        prioritized.sort(key=lambda x: -x["collection_score"])

        # Summary stats
        total_outstanding = sum(d["total_outstanding"] for d in prioritized)
        total_overdue = sum(d["total_overdue"] for d in prioritized)
        critical_count = sum(1 for d in prioritized if d["priority"] == "CRITICAL")

        alerts = []
        for d in prioritized[:5]:
            if d["priority"] in ("CRITICAL", "HIGH"):
                alerts.append({
                    "type": "COLLECTION",
                    "severity": d["priority"],
                    "dealer": d["dealer_name"],
                    "message": f"₹{d['total_overdue']:,.0f} overdue ({d['max_days_overdue']} days) — {d['strategy'][:50]}",
                    "action": d["strategy"]
                })

        return {
            "agent": "collection-optimizer",
            "run_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_outstanding": round(total_outstanding, 2),
                "total_overdue": round(total_overdue, 2),
                "dealers_with_overdue": len(prioritized),
                "critical_dealers": critical_count,
            },
            "aging_buckets": {
                "0_30_days": {"amount": round(buckets["0_30"]["amount"], 2), "invoices": buckets["0_30"]["count"], "dealers": buckets["0_30"]["dealer_count"]},
                "31_60_days": {"amount": round(buckets["31_60"]["amount"], 2), "invoices": buckets["31_60"]["count"], "dealers": buckets["31_60"]["dealer_count"]},
                "61_90_days": {"amount": round(buckets["61_90"]["amount"], 2), "invoices": buckets["61_90"]["count"], "dealers": buckets["61_90"]["dealer_count"]},
                "90_plus_days": {"amount": round(buckets["90_plus"]["amount"], 2), "invoices": buckets["90_plus"]["count"], "dealers": buckets["90_plus"]["dealer_count"]},
            },
            "priority_list": prioritized[:15],
            "alerts": alerts,
            "strategies": COLLECTION_STRATEGIES,
            "status": "completed"
        }
