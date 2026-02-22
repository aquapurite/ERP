"""
DMS AI API Endpoints

Provides AI-powered intelligence for the Dealer Management System:
- GET  /dms-ai/command-center       — all 4 agents in one call
- GET  /dms-ai/dealer-performance   — dealer scoring & severity
- GET  /dms-ai/demand-sensing       — demand forecasting & anomalies
- GET  /dms-ai/scheme-effectiveness — scheme ROI & recommendations
- GET  /dms-ai/collection-optimizer — aging buckets & priority collection
- POST /dms-ai/chat                 — natural language DMS queries
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ai.dms_command_center import DMSCommandCenterAgent
from app.services.ai.dms_dealer_performance import DealerPerformanceAgent
from app.services.ai.dms_demand_sensing import DemandSensingAgent
from app.services.ai.dms_scheme_effectiveness import SchemeEffectivenessAgent
from app.services.ai.dms_collection_optimizer import CollectionOptimizerAgent
from app.services.ai.dms_chatbot import DMSChatbotService


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/command-center", summary="DMS Command Centre — all agents")
async def get_dms_command_center(db: AsyncSession = Depends(get_db)):
    """
    Run all 4 DMS AI agents in parallel and return a unified command centre view.

    Includes dealer performance, demand sensing, scheme effectiveness,
    and collection optimizer results along with aggregated alerts.
    """
    return await DMSCommandCenterAgent(db).run()


@router.get("/dealer-performance", summary="DMS Dealer Performance Agent")
async def get_dealer_performance(db: AsyncSession = Depends(get_db)):
    """
    Score all active dealers on:
    - Sales achievement vs monthly target
    - Payment compliance (overdue amounts)
    - Revenue growth trajectory (6 months)

    Severity: CRITICAL (<50%), HIGH (<70%), MEDIUM (<85%), OK (≥85%)
    """
    return await DealerPerformanceAgent(db).run()


@router.get("/demand-sensing", summary="DMS Demand Sensing Agent")
async def get_demand_sensing(db: AsyncSession = Depends(get_db)):
    """
    Analyse dealer order trends:
    - 6-month monthly revenue per dealer
    - Weighted moving average forecast (alpha=0.3)
    - Z-score anomaly detection (SPIKE / DROP)
    - Inactive dealer flagging (30+ days no order)
    """
    return await DemandSensingAgent(db).run()


@router.get("/scheme-effectiveness", summary="DMS Scheme Effectiveness Agent")
async def get_scheme_effectiveness(db: AsyncSession = Depends(get_db)):
    """
    Evaluate active dealer schemes:
    - ROI: (order_value - discount) / discount × 100
    - Budget utilization % (NEAR_BUDGET_LIMIT / LOW_UTILIZATION flags)
    - Participation rate
    - Recommendations: RETIRE / EXTEND / PROMOTE / MAINTAIN
    """
    return await SchemeEffectivenessAgent(db).run()


@router.get("/collection-optimizer", summary="DMS Collection Optimizer Agent")
async def get_collection_optimizer(db: AsyncSession = Depends(get_db)):
    """
    Optimise collections from dealers:
    - Aging buckets (0-30, 31-60, 61-90, 90+ days)
    - Priority score = overdue_amount × days_weight × (1 / payment_rating)
    - Collection strategy per dealer
    - Predicted payment date from historical avg
    """
    return await CollectionOptimizerAgent(db).run()


@router.post("/chat", summary="DMS AI Chatbot — natural language queries")
async def dms_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Natural language interface for DMS intelligence.

    Example queries:
    - "Which dealers are underperforming?"
    - "What is next month's demand forecast?"
    - "Which dealers haven't ordered in 30 days?"
    - "What is our outstanding collection position?"
    - "How are our schemes performing?"
    - "Who are the top dealers this month?"
    - "What alerts need my attention?"
    """
    return await DMSChatbotService(db).chat(request.message)
