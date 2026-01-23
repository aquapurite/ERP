"""Reports API endpoints for frontend dashboard."""
from typing import Optional, List
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case, or_
from sqlalchemy.orm import aliased

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.product_cost import ProductCost
from app.models.accounting import ChartOfAccount

router = APIRouter()


# ==================== Balance Sheet ====================

# Account sub-types that are considered "current"
CURRENT_ASSET_SUBTYPES = {"CASH", "BANK", "ACCOUNTS_RECEIVABLE", "INVENTORY", "PREPAID_EXPENSE", "CURRENT_ASSET"}
CURRENT_LIABILITY_SUBTYPES = {"ACCOUNTS_PAYABLE", "TAX_PAYABLE", "ACCRUED_EXPENSE", "SHORT_TERM_DEBT", "CURRENT_LIABILITY"}


def build_section_items(accounts: list, previous_balances: dict) -> List[dict]:
    """Build line items for a balance sheet section."""
    items = []
    for acc in accounts:
        current = float(acc.current_balance or 0)
        previous = previous_balances.get(str(acc.id), 0.0)
        variance = current - previous
        variance_pct = (variance / previous * 100) if previous != 0 else 0

        items.append({
            "account_code": acc.account_code,
            "account_name": acc.account_name,
            "current_balance": current,
            "previous_balance": previous,
            "variance": variance,
            "variance_percentage": round(variance_pct, 2),
            "is_group": acc.is_group,
            "indent_level": acc.level - 1 if acc.level else 0
        })
    return items


@router.get("/balance-sheet")
async def get_balance_sheet(
    db: DB,
    current_user: User = Depends(get_current_user),
    as_of_date: str = Query("today"),
    compare: bool = Query(True),
):
    """
    Get Balance Sheet report with line items and comparison.

    Returns assets, liabilities, equity with individual account breakdowns.
    """
    today = date.today()

    # For now, we use current balances from chart_of_accounts
    # In a full implementation, we'd query GL entries up to as_of_date

    # Get all non-group asset accounts
    asset_query = select(ChartOfAccount).where(
        and_(
            ChartOfAccount.account_type == "ASSET",
            ChartOfAccount.is_group == False,
            ChartOfAccount.is_active == True,
        )
    ).order_by(ChartOfAccount.account_code)

    asset_result = await db.execute(asset_query)
    all_assets = asset_result.scalars().all()

    # Split into current and non-current
    current_assets = [a for a in all_assets if a.account_sub_type in CURRENT_ASSET_SUBTYPES or a.account_sub_type is None]
    non_current_assets = [a for a in all_assets if a.account_sub_type and a.account_sub_type not in CURRENT_ASSET_SUBTYPES]

    # Get all non-group liability accounts
    liability_query = select(ChartOfAccount).where(
        and_(
            ChartOfAccount.account_type == "LIABILITY",
            ChartOfAccount.is_group == False,
            ChartOfAccount.is_active == True,
        )
    ).order_by(ChartOfAccount.account_code)

    liability_result = await db.execute(liability_query)
    all_liabilities = liability_result.scalars().all()

    # Split into current and non-current
    current_liabilities = [l for l in all_liabilities if l.account_sub_type in CURRENT_LIABILITY_SUBTYPES or l.account_sub_type is None]
    non_current_liabilities = [l for l in all_liabilities if l.account_sub_type and l.account_sub_type not in CURRENT_LIABILITY_SUBTYPES]

    # Get all equity accounts
    equity_query = select(ChartOfAccount).where(
        and_(
            ChartOfAccount.account_type == "EQUITY",
            ChartOfAccount.is_group == False,
            ChartOfAccount.is_active == True,
        )
    ).order_by(ChartOfAccount.account_code)

    equity_result = await db.execute(equity_query)
    equity_accounts = equity_result.scalars().all()

    # For comparison, use opening_balance as "previous" (simplified)
    # In a full implementation, we'd query GL at a previous date
    previous_balances = {}
    for acc in all_assets + all_liabilities + equity_accounts:
        previous_balances[str(acc.id)] = float(acc.opening_balance or 0)

    # Build sections
    current_assets_items = build_section_items(current_assets, previous_balances)
    non_current_assets_items = build_section_items(non_current_assets, previous_balances)
    current_liabilities_items = build_section_items(current_liabilities, previous_balances)
    non_current_liabilities_items = build_section_items(non_current_liabilities, previous_balances)
    equity_items = build_section_items(equity_accounts, previous_balances)

    # Calculate totals
    total_current_assets = sum(float(a.current_balance or 0) for a in current_assets)
    total_non_current_assets = sum(float(a.current_balance or 0) for a in non_current_assets)
    total_assets = total_current_assets + total_non_current_assets

    total_current_liabilities = sum(float(l.current_balance or 0) for l in current_liabilities)
    total_non_current_liabilities = sum(float(l.current_balance or 0) for l in non_current_liabilities)
    total_liabilities = total_current_liabilities + total_non_current_liabilities

    total_equity = sum(float(e.current_balance or 0) for e in equity_accounts)

    # Previous totals
    prev_current_assets = sum(previous_balances.get(str(a.id), 0) for a in current_assets)
    prev_non_current_assets = sum(previous_balances.get(str(a.id), 0) for a in non_current_assets)
    prev_total_assets = prev_current_assets + prev_non_current_assets

    prev_current_liabilities = sum(previous_balances.get(str(l.id), 0) for l in current_liabilities)
    prev_non_current_liabilities = sum(previous_balances.get(str(l.id), 0) for l in non_current_liabilities)
    prev_total_liabilities = prev_current_liabilities + prev_non_current_liabilities

    prev_total_equity = sum(previous_balances.get(str(e.id), 0) for e in equity_accounts)

    total_liabilities_and_equity = total_liabilities + total_equity
    prev_total_liabilities_and_equity = prev_total_liabilities + prev_total_equity

    # Ratios
    working_capital = total_current_assets - total_current_liabilities
    current_ratio = total_current_assets / total_current_liabilities if total_current_liabilities > 0 else 0
    debt_to_equity = total_liabilities / total_equity if total_equity > 0 else 0

    difference = total_assets - total_liabilities_and_equity
    is_balanced = abs(difference) < 0.01

    return {
        "as_of_date": today.isoformat(),
        "previous_date": (today - timedelta(days=30)).isoformat(),
        "assets": {
            "current_assets": {
                "title": "Current Assets",
                "items": current_assets_items,
                "total": total_current_assets,
                "previous_total": prev_current_assets,
            },
            "non_current_assets": {
                "title": "Non-Current Assets",
                "items": non_current_assets_items,
                "total": total_non_current_assets,
                "previous_total": prev_non_current_assets,
            },
            "total": total_assets,
            "previous_total": prev_total_assets,
        },
        "liabilities": {
            "current_liabilities": {
                "title": "Current Liabilities",
                "items": current_liabilities_items,
                "total": total_current_liabilities,
                "previous_total": prev_current_liabilities,
            },
            "non_current_liabilities": {
                "title": "Non-Current Liabilities",
                "items": non_current_liabilities_items,
                "total": total_non_current_liabilities,
                "previous_total": prev_non_current_liabilities,
            },
            "total": total_liabilities,
            "previous_total": prev_total_liabilities,
        },
        "equity": {
            "title": "Shareholders Equity",
            "items": equity_items,
            "total": total_equity,
            "previous_total": prev_total_equity,
        },
        "total_liabilities_and_equity": total_liabilities_and_equity,
        "previous_total_liabilities_and_equity": prev_total_liabilities_and_equity,
        "is_balanced": is_balanced,
        "difference": difference,
        "current_ratio": round(current_ratio, 2),
        "debt_to_equity": round(debt_to_equity, 2),
        "working_capital": working_capital,
    }

# Map source codes to display names
SOURCE_DISPLAY_NAMES = {
    "WEBSITE": "D2C Website",
    "D2C": "D2C Website",
    "MOBILE_APP": "Mobile App",
    "STORE": "Retail Store",
    "PHONE": "Phone Orders",
    "DEALER": "Dealer/B2B",
    "AMAZON": "Amazon",
    "FLIPKART": "Flipkart",
    "OTHER": "Other Channels",
}

# Map source codes to channel types
SOURCE_CHANNEL_TYPES = {
    "WEBSITE": "D2C",
    "D2C": "D2C",
    "MOBILE_APP": "D2C",
    "STORE": "RETAIL",
    "PHONE": "D2C",
    "DEALER": "B2B",
    "AMAZON": "MARKETPLACE",
    "FLIPKART": "MARKETPLACE",
    "OTHER": "OTHER",
}

# Commission rates by channel
COMMISSION_RATES = {
    "WEBSITE": Decimal("0"),
    "D2C": Decimal("0"),
    "MOBILE_APP": Decimal("0"),
    "STORE": Decimal("0"),
    "PHONE": Decimal("0"),
    "DEALER": Decimal("0.05"),  # 5%
    "AMAZON": Decimal("0.15"),  # 15%
    "FLIPKART": Decimal("0.12"),  # 12%
    "OTHER": Decimal("0.05"),
}


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


def map_channel_filter_to_sources(channel_id: str) -> list[str]:
    """Map frontend channel filter to Order.source values."""
    if not channel_id or channel_id == "all":
        return []  # No filter = all sources

    channel_lower = channel_id.lower()
    if channel_lower in ["d2c", "website"]:
        return ["WEBSITE", "D2C", "MOBILE_APP", "PHONE"]
    elif channel_lower == "amazon":
        return ["AMAZON"]
    elif channel_lower == "flipkart":
        return ["FLIPKART"]
    elif channel_lower in ["b2b", "dealer"]:
        return ["DEALER"]
    elif channel_lower == "store":
        return ["STORE"]
    else:
        return [channel_id.upper()]


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
    COGS calculated from ProductCost.average_cost (PO → GRN flow).
    """
    start_date, end_date = parse_period(period)

    # Get previous period for comparison
    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    # Get source filter
    source_filter = map_channel_filter_to_sources(channel_id) if channel_id else []

    # Get distinct sources with data
    # Only count orders with payment_status = 'PAID' (same as Dashboard)
    sources_query = select(Order.source).where(
        and_(
            Order.status.notin_(["CANCELLED", "DRAFT"]),
            or_(
                Order.payment_status == "PAID",
                Order.payment_status == "paid",
                func.upper(Order.payment_status) == "PAID"
            ),
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date
        )
    )
    if source_filter:
        sources_query = sources_query.where(Order.source.in_(source_filter))

    sources_query = sources_query.distinct()
    sources_result = await db.execute(sources_query)
    sources = [row[0] for row in sources_result.all() if row[0]]

    # If no data, return empty but with structure
    if not sources:
        return {
            "total_revenue": 0.0,
            "total_cogs": 0.0,
            "total_gross_profit": 0.0,
            "total_operating_expenses": 0.0,
            "total_net_income": 0.0,
            "channels": []
        }

    total_revenue = Decimal("0")
    total_cogs = Decimal("0")
    total_gross_profit = Decimal("0")
    total_operating_expenses = Decimal("0")
    total_net_income = Decimal("0")

    channel_data = []

    for source in sources:
        source_value = source or "OTHER"

        # Current period revenue (only PAID orders - same as Dashboard)
        revenue_query = select(
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.coalesce(func.sum(Order.discount_amount), 0).label("discounts"),
            func.count(Order.id).label("order_count")
        ).where(
            and_(
                Order.source == source_value,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                or_(
                    Order.payment_status == "PAID",
                    func.upper(Order.payment_status) == "PAID"
                ),
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        revenue_result = await db.execute(revenue_query)
        revenue_data = revenue_result.one()

        gross_revenue = Decimal(str(revenue_data.revenue or 0))
        discounts = Decimal(str(revenue_data.discounts or 0))
        net_revenue = gross_revenue - discounts

        # Previous period revenue (only PAID orders)
        prev_revenue_query = select(
            func.coalesce(func.sum(Order.total_amount - Order.discount_amount), 0)
        ).where(
            and_(
                Order.source == source_value,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                or_(
                    Order.payment_status == "PAID",
                    func.upper(Order.payment_status) == "PAID"
                ),
                func.date(Order.created_at) >= prev_start,
                func.date(Order.created_at) <= prev_end
            )
        )
        prev_net_revenue = Decimal(str(await db.scalar(prev_revenue_query) or 0))

        # COGS from OrderItem joined with ProductCost (proper WAC from PO → GRN)
        # Join OrderItem with ProductCost on product_id to get average_cost
        # Use LEFT JOIN so orders without ProductCost still show (with 0 COGS)
        cogs_query = select(
            func.coalesce(
                func.sum(
                    OrderItem.quantity * func.coalesce(ProductCost.average_cost, Decimal("0"))
                ),
                0
            )
        ).select_from(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).outerjoin(
            ProductCost,
            and_(
                ProductCost.product_id == OrderItem.product_id,
                # Get company-wide cost (warehouse_id IS NULL)
                or_(
                    ProductCost.warehouse_id.is_(None),
                    ProductCost.warehouse_id == Order.warehouse_id
                )
            )
        ).where(
            and_(
                Order.source == source_value,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                or_(
                    Order.payment_status == "PAID",
                    func.upper(Order.payment_status) == "PAID"
                ),
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        cogs = Decimal(str(await db.scalar(cogs_query) or 0))

        # Previous COGS
        prev_cogs_query = select(
            func.coalesce(
                func.sum(
                    OrderItem.quantity * func.coalesce(ProductCost.average_cost, Decimal("0"))
                ),
                0
            )
        ).select_from(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).outerjoin(
            ProductCost,
            and_(
                ProductCost.product_id == OrderItem.product_id,
                or_(
                    ProductCost.warehouse_id.is_(None),
                    ProductCost.warehouse_id == Order.warehouse_id
                )
            )
        ).where(
            and_(
                Order.source == source_value,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                or_(
                    Order.payment_status == "PAID",
                    func.upper(Order.payment_status) == "PAID"
                ),
                func.date(Order.created_at) >= prev_start,
                func.date(Order.created_at) <= prev_end
            )
        )
        prev_cogs = Decimal(str(await db.scalar(prev_cogs_query) or 0))

        gross_profit = net_revenue - cogs
        gross_margin = float((gross_profit / net_revenue * 100) if net_revenue > 0 else 0)

        prev_gross_profit = prev_net_revenue - prev_cogs

        # Operating expenses (channel fees + shipping + payment processing)
        commission_rate = COMMISSION_RATES.get(source_value, Decimal("0.05"))
        channel_fees = net_revenue * commission_rate

        shipping_query = select(
            func.coalesce(func.sum(Order.shipping_amount), 0)
        ).where(
            and_(
                Order.source == source_value,
                Order.status.notin_(["CANCELLED", "DRAFT"]),
                or_(
                    Order.payment_status == "PAID",
                    func.upper(Order.payment_status) == "PAID"
                ),
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        shipping = Decimal(str(await db.scalar(shipping_query) or 0))

        payment_fees = net_revenue * Decimal("0.02")  # 2% payment processing

        operating_expenses = channel_fees + shipping + payment_fees
        operating_income = gross_profit - operating_expenses
        net_income = operating_income
        net_margin = float((net_income / net_revenue * 100) if net_revenue > 0 else 0)

        prev_operating_expenses = prev_net_revenue * (commission_rate + Decimal("0.02"))
        prev_net_income = prev_gross_profit - prev_operating_expenses

        # Build revenue line items
        revenue_change = float(((net_revenue - prev_net_revenue) / prev_net_revenue * 100) if prev_net_revenue > 0 else 0)

        channel_data.append({
            "channel_id": source_value,
            "channel_name": SOURCE_DISPLAY_NAMES.get(source_value, source_value),
            "channel_type": SOURCE_CHANNEL_TYPES.get(source_value, "OTHER"),
            "revenue": [
                {
                    "account_code": "4000",
                    "account_name": "Product Sales",
                    "amount": float(gross_revenue),
                    "previous_amount": float(prev_net_revenue + (prev_cogs * Decimal("0.1"))),
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
