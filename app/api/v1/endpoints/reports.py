"""Reports API endpoints for frontend dashboard."""
from typing import Optional
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.channel import SalesChannel
from app.models.accounting import GeneralLedger, ChartOfAccount

router = APIRouter()


def parse_period(period: str) -> tuple[date, date]:
    """Parse period string to start/end dates."""
    today = date.today()

    if period == "this_month":
        start = today.replace(day=1)
        end = today
    elif period == "last_month":
        first_of_this_month = today.replace(day=1)
        end = first_of_this_month - timedelta(days=1)
        start = end.replace(day=1)
    elif period == "this_quarter":
        quarter = (today.month - 1) // 3
        start = date(today.year, quarter * 3 + 1, 1)
        end = today
    elif period == "last_quarter":
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start = date(today.year - 1, 10, 1)
            end = date(today.year - 1, 12, 31)
        else:
            start = date(today.year, (quarter - 1) * 3 + 1, 1)
            end_month = quarter * 3
            if end_month == 3:
                end = date(today.year, 3, 31)
            elif end_month == 6:
                end = date(today.year, 6, 30)
            else:
                end = date(today.year, 9, 30)
    elif period == "this_year":
        start = date(today.year, 1, 1)
        end = today
    elif period == "last_year":
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
    else:
        # Default to this month
        start = today.replace(day=1)
        end = today

    return start, end


@router.get("/channel-pl")
async def get_channel_pl(
    db: DB,
    current_user: User = Depends(get_current_user),
    period: str = Query("this_month"),
    channel_id: Optional[str] = None,
):
    """
    Get Channel-wise Profit & Loss report.

    Response format matches frontend ConsolidatedPL interface.
    """
    start_date, end_date = parse_period(period)

    # Get previous period for comparison
    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    # Get channels
    channels_query = select(SalesChannel).where(SalesChannel.status == "ACTIVE")
    if channel_id and channel_id != "all":
        # Map frontend channel codes to actual channel IDs or types
        if channel_id in ["d2c", "D2C"]:
            channels_query = channels_query.where(
                or_(
                    SalesChannel.channel_type == "D2C",
                    func.lower(SalesChannel.name).contains("d2c"),
                    func.lower(SalesChannel.name).contains("website")
                )
            )
        elif channel_id.lower() == "amazon":
            channels_query = channels_query.where(
                func.lower(SalesChannel.name).contains("amazon")
            )
        elif channel_id.lower() == "flipkart":
            channels_query = channels_query.where(
                func.lower(SalesChannel.name).contains("flipkart")
            )
        elif channel_id.lower() == "b2b":
            channels_query = channels_query.where(
                or_(
                    SalesChannel.channel_type == "B2B",
                    func.lower(SalesChannel.name).contains("b2b"),
                    func.lower(SalesChannel.name).contains("gtmt")
                )
            )
        else:
            # Try parsing as UUID
            try:
                uuid_val = UUID(channel_id)
                channels_query = channels_query.where(SalesChannel.id == uuid_val)
            except (ValueError, AttributeError):
                pass

    channels_result = await db.execute(channels_query)
    channels = channels_result.scalars().all()

    total_revenue = Decimal("0")
    total_cogs = Decimal("0")
    total_gross_profit = Decimal("0")
    total_operating_expenses = Decimal("0")
    total_net_income = Decimal("0")

    channel_data = []

    for channel in channels:
        # Current period revenue
        revenue_query = select(
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.coalesce(func.sum(Order.discount_amount), 0).label("discounts"),
            func.count(Order.id).label("order_count")
        ).where(
            and_(
                Order.channel_id == channel.id,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        revenue_result = await db.execute(revenue_query)
        revenue_data = revenue_result.one()

        gross_revenue = Decimal(str(revenue_data.revenue or 0))
        discounts = Decimal(str(revenue_data.discounts or 0))
        net_revenue = gross_revenue - discounts

        # Previous period revenue
        prev_revenue_query = select(
            func.coalesce(func.sum(Order.total_amount - Order.discount_amount), 0)
        ).where(
            and_(
                Order.channel_id == channel.id,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                func.date(Order.created_at) >= prev_start,
                func.date(Order.created_at) <= prev_end
            )
        )
        prev_net_revenue = Decimal(str(await db.scalar(prev_revenue_query) or 0))

        # COGS from order items
        cogs_query = select(
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_cost), 0)
        ).select_from(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).where(
            and_(
                Order.channel_id == channel.id,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        cogs = Decimal(str(await db.scalar(cogs_query) or 0))

        # Previous COGS
        prev_cogs_query = select(
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_cost), 0)
        ).select_from(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).where(
            and_(
                Order.channel_id == channel.id,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                func.date(Order.created_at) >= prev_start,
                func.date(Order.created_at) <= prev_end
            )
        )
        prev_cogs = Decimal(str(await db.scalar(prev_cogs_query) or 0))

        gross_profit = net_revenue - cogs
        gross_margin = float((gross_profit / net_revenue * 100) if net_revenue > 0 else 0)

        prev_gross_profit = prev_net_revenue - prev_cogs

        # Operating expenses (channel fees + shipping + payment processing)
        commission_rate = Decimal(str(channel.commission_percent or 0)) / 100
        channel_fees = net_revenue * commission_rate

        shipping_query = select(
            func.coalesce(func.sum(Order.shipping_amount), 0)
        ).where(
            and_(
                Order.channel_id == channel.id,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        shipping = Decimal(str(await db.scalar(shipping_query) or 0))

        payment_fees = net_revenue * Decimal("0.02")  # 2% payment processing

        operating_expenses = channel_fees + shipping + payment_fees
        operating_income = gross_profit - operating_expenses
        net_income = operating_income  # Simplified: net = operating for now
        net_margin = float((net_income / net_revenue * 100) if net_revenue > 0 else 0)

        prev_operating_expenses = prev_net_revenue * (commission_rate + Decimal("0.02"))
        prev_net_income = prev_gross_profit - prev_operating_expenses

        # Build revenue line items
        revenue_change = float(((net_revenue - prev_net_revenue) / prev_net_revenue * 100) if prev_net_revenue > 0 else 0)

        channel_data.append({
            "channel_id": str(channel.id),
            "channel_name": channel.name,
            "channel_type": channel.channel_type or "OTHER",
            "revenue": [
                {
                    "account_code": "4000",
                    "account_name": "Product Sales",
                    "amount": float(gross_revenue),
                    "previous_amount": float(prev_net_revenue + (prev_cogs * Decimal("0.1"))),  # Estimate
                    "change_percent": revenue_change,
                    "is_header": False,
                    "indent_level": 0
                },
                {
                    "account_code": "4900",
                    "account_name": "Discounts & Allowances",
                    "amount": float(-discounts),
                    "previous_amount": 0,
                    "change_percent": 0,
                    "is_header": False,
                    "indent_level": 0
                }
            ],
            "cost_of_goods_sold": [
                {
                    "account_code": "5000",
                    "account_name": "Cost of Goods Sold",
                    "amount": float(cogs),
                    "previous_amount": float(prev_cogs),
                    "change_percent": float(((cogs - prev_cogs) / prev_cogs * 100) if prev_cogs > 0 else 0),
                    "is_header": False,
                    "indent_level": 0
                }
            ],
            "gross_profit": float(gross_profit),
            "gross_margin_percent": round(gross_margin, 2),
            "operating_expenses": [
                {
                    "account_code": "6100",
                    "account_name": "Channel/Platform Fees",
                    "amount": float(channel_fees),
                    "previous_amount": 0,
                    "change_percent": 0,
                    "is_header": False,
                    "indent_level": 0
                },
                {
                    "account_code": "6200",
                    "account_name": "Shipping & Logistics",
                    "amount": float(shipping),
                    "previous_amount": 0,
                    "change_percent": 0,
                    "is_header": False,
                    "indent_level": 0
                },
                {
                    "account_code": "6300",
                    "account_name": "Payment Processing Fees",
                    "amount": float(payment_fees),
                    "previous_amount": 0,
                    "change_percent": 0,
                    "is_header": False,
                    "indent_level": 0
                }
            ],
            "operating_income": float(operating_income),
            "other_income_expense": [],
            "net_income": float(net_income),
            "net_margin_percent": round(net_margin, 2),
            "previous_gross_profit": float(prev_gross_profit),
            "previous_net_income": float(prev_net_income),
        })

        total_revenue += net_revenue
        total_cogs += cogs
        total_gross_profit += gross_profit
        total_operating_expenses += operating_expenses
        total_net_income += net_income

    return {
        "total_revenue": float(total_revenue),
        "total_cogs": float(total_cogs),
        "total_gross_profit": float(total_gross_profit),
        "total_operating_expenses": float(total_operating_expenses),
        "total_net_income": float(total_net_income),
        "channels": channel_data
    }
