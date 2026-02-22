"""Dashboard Charts API endpoints - Real data for dashboard visualizations."""
from typing import Optional
from uuid import UUID
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, and_, extract, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DB, get_current_user
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.category import Category
from app.models.inventory import InventorySummary as Inventory
from app.models.accounting import JournalEntry, JournalEntryLine, ChartOfAccount

router = APIRouter()


# ==================== Sales Overview ====================
@router.get("/sales/overview")
async def get_sales_overview(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
    channel_id: Optional[UUID] = None,
):
    """
    Get sales overview for dashboard.
    Returns today's sales, this month's sales, comparison with previous period.
    """
    today = date.today()
    start_date = today - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)
    month_start = today.replace(day=1)

    conditions = [Order.status.notin_(["CANCELLED", "DRAFT"])]
    if channel_id:
        conditions.append(Order.channel_id == channel_id)

    # Today's sales
    today_query = select(
        func.count(Order.id).label("count"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total")
    ).where(
        and_(*conditions, func.date(Order.created_at) == today)
    )
    today_result = await db.execute(today_query)
    today_data = today_result.one()

    # This month's sales
    month_query = select(
        func.count(Order.id).label("count"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total")
    ).where(
        and_(*conditions, Order.created_at >= datetime.combine(month_start, datetime.min.time()))
    )
    month_result = await db.execute(month_query)
    month_data = month_result.one()

    # Period sales (for trend)
    period_query = select(
        func.count(Order.id).label("count"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total")
    ).where(
        and_(*conditions, Order.created_at >= datetime.combine(start_date, datetime.min.time()))
    )
    period_result = await db.execute(period_query)
    period_data = period_result.one()

    # Previous period sales (for comparison)
    prev_query = select(
        func.coalesce(func.sum(Order.total_amount), 0).label("total")
    ).where(
        and_(
            *conditions,
            Order.created_at >= datetime.combine(prev_start, datetime.min.time()),
            Order.created_at < datetime.combine(start_date, datetime.min.time())
        )
    )
    prev_result = await db.execute(prev_query)
    prev_total = float(prev_result.scalar() or 0)

    period_total = float(period_data.total or 0)
    growth = ((period_total - prev_total) / prev_total * 100) if prev_total > 0 else 0

    return {
        "today": {
            "orders": today_data.count,
            "revenue": float(today_data.total or 0),
        },
        "this_month": {
            "orders": month_data.count,
            "revenue": float(month_data.total or 0),
        },
        "period": {
            "days": days,
            "orders": period_data.count,
            "revenue": period_total,
            "growth_percent": round(growth, 2),
        },
    }


# ==================== Sales Trend ====================
@router.get("/sales/trend")
async def get_sales_trend(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=7, le=365),
    channel_id: Optional[UUID] = None,
    group_by: str = Query("day", pattern="^(day|week|month)$"),
):
    """
    Get sales trend data for charts.
    Groups by day, week, or month.
    """
    start_date = date.today() - timedelta(days=days)

    conditions = [
        Order.status.notin_(["CANCELLED", "DRAFT"]),
        Order.created_at >= datetime.combine(start_date, datetime.min.time())
    ]
    if channel_id:
        conditions.append(Order.channel_id == channel_id)

    if group_by == "day":
        date_expr = func.date(Order.created_at)
    elif group_by == "week":
        date_expr = func.date_trunc('week', Order.created_at)
    else:
        date_expr = func.date_trunc('month', Order.created_at)

    query = select(
        date_expr.label("period"),
        func.count(Order.id).label("orders"),
        func.coalesce(func.sum(Order.total_amount), 0).label("revenue")
    ).where(
        and_(*conditions)
    ).group_by(date_expr).order_by(date_expr)

    result = await db.execute(query)
    data = result.all()

    return {
        "labels": [str(row.period)[:10] for row in data],
        "orders": [row.orders for row in data],
        "revenue": [float(row.revenue or 0) for row in data],
    }


# ==================== Top Products ====================
@router.get("/products/top")
async def get_top_products(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    metric: str = Query("revenue", pattern="^(revenue|quantity)$"),
):
    """Get top selling products by revenue or quantity."""
    start_date = date.today() - timedelta(days=days)

    query = select(
        Product.id,
        Product.name,
        Product.sku,
        func.sum(OrderItem.quantity).label("quantity_sold"),
        func.sum(OrderItem.total_amount).label("revenue")
    ).select_from(OrderItem).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Product, OrderItem.product_id == Product.id
    ).where(
        and_(
            Order.status.notin_(["CANCELLED", "DRAFT"]),
            Order.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    ).group_by(Product.id, Product.name, Product.sku)

    if metric == "revenue":
        query = query.order_by(desc("revenue"))
    else:
        query = query.order_by(desc("quantity_sold"))

    query = query.limit(limit)

    result = await db.execute(query)
    products = result.all()

    return {
        "items": [
            {
                "id": str(p.id),
                "name": p.name,
                "sku": p.sku,
                "quantity_sold": int(p.quantity_sold or 0),
                "revenue": float(p.revenue or 0),
            }
            for p in products
        ],
        "period_days": days,
        "metric": metric,
    }


# ==================== Category Sales ====================
@router.get("/categories/sales")
async def get_category_sales(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get sales breakdown by category."""
    start_date = date.today() - timedelta(days=days)

    query = select(
        Category.id,
        Category.name,
        func.count(OrderItem.id).label("items_sold"),
        func.sum(OrderItem.total_amount).label("revenue")
    ).select_from(OrderItem).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Product, OrderItem.product_id == Product.id
    ).join(
        Category, Product.category_id == Category.id
    ).where(
        and_(
            Order.status.notin_(["CANCELLED", "DRAFT"]),
            Order.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    ).group_by(Category.id, Category.name).order_by(desc("revenue"))

    result = await db.execute(query)
    categories = result.all()

    total_revenue = sum(float(c.revenue or 0) for c in categories)

    return {
        "items": [
            {
                "id": str(c.id),
                "name": c.name,
                "items_sold": c.items_sold,
                "revenue": float(c.revenue or 0),
                "percentage": round((float(c.revenue or 0) / total_revenue * 100) if total_revenue > 0 else 0, 2),
            }
            for c in categories
        ],
        "total_revenue": total_revenue,
        "period_days": days,
    }


# ==================== Customer Stats ====================
@router.get("/customers/stats")
async def get_customer_stats(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get customer statistics."""
    start_date = date.today() - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)

    # Total customers
    total_query = select(func.count(Customer.id)).select_from(Customer)
    total = await db.scalar(total_query) or 0

    # New customers in period
    new_query = select(func.count(Customer.id)).where(
        Customer.created_at >= datetime.combine(start_date, datetime.min.time())
    )
    new_customers = await db.scalar(new_query) or 0

    # New customers in previous period
    prev_new_query = select(func.count(Customer.id)).where(
        and_(
            Customer.created_at >= datetime.combine(prev_start, datetime.min.time()),
            Customer.created_at < datetime.combine(start_date, datetime.min.time())
        )
    )
    prev_new = await db.scalar(prev_new_query) or 0

    growth = ((new_customers - prev_new) / prev_new * 100) if prev_new > 0 else 0

    # Repeat customers (ordered more than once in period)
    repeat_query = select(func.count(func.distinct(Order.customer_id))).where(
        and_(
            Order.created_at >= datetime.combine(start_date, datetime.min.time()),
            Order.status.notin_(["CANCELLED", "DRAFT"])
        )
    ).group_by(Order.customer_id).having(func.count(Order.id) > 1)

    repeat_subq = select(func.count()).select_from(
        select(Order.customer_id).where(
            and_(
                Order.created_at >= datetime.combine(start_date, datetime.min.time()),
                Order.status.notin_(["CANCELLED", "DRAFT"])
            )
        ).group_by(Order.customer_id).having(func.count(Order.id) > 1).subquery()
    )
    repeat_customers = await db.scalar(repeat_subq) or 0

    return {
        "total_customers": total,
        "new_customers": new_customers,
        "new_customers_growth": round(growth, 2),
        "repeat_customers": repeat_customers,
        "period_days": days,
    }


# ==================== Inventory Overview ====================
@router.get("/inventory/overview")
async def get_inventory_overview(
    db: DB,
    current_user: User = Depends(get_current_user),
    warehouse_id: Optional[UUID] = None,
):
    """Get inventory overview - stock levels, low stock alerts."""
    conditions = []
    if warehouse_id:
        conditions.append(Inventory.warehouse_id == warehouse_id)

    # Total stock value
    value_query = select(
        func.coalesce(func.sum(Inventory.total_quantity * Inventory.average_cost), 0)
    ).select_from(Inventory)
    if conditions:
        value_query = value_query.where(and_(*conditions))
    total_value = await db.scalar(value_query) or 0

    # Total items
    items_query = select(func.count(Inventory.id)).select_from(Inventory)
    if conditions:
        items_query = items_query.where(and_(*conditions))
    total_items = await db.scalar(items_query) or 0

    # Low stock items (total_quantity <= reorder_level)
    low_stock_query = select(func.count(Inventory.id)).where(
        Inventory.total_quantity <= Inventory.reorder_level
    )
    if conditions:
        low_stock_query = low_stock_query.where(and_(*conditions))
    low_stock = await db.scalar(low_stock_query) or 0

    # Out of stock items
    out_of_stock_query = select(func.count(Inventory.id)).where(
        Inventory.total_quantity <= 0
    )
    if conditions:
        out_of_stock_query = out_of_stock_query.where(and_(*conditions))
    out_of_stock = await db.scalar(out_of_stock_query) or 0

    return {
        "total_stock_value": float(total_value),
        "total_sku_count": total_items,
        "low_stock_items": low_stock,
        "out_of_stock_items": out_of_stock,
    }


# ==================== Order Status Distribution ====================
@router.get("/orders/status-distribution")
async def get_order_status_distribution(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get order count by status."""
    start_date = date.today() - timedelta(days=days)

    query = select(
        Order.status,
        func.count(Order.id).label("count")
    ).where(
        Order.created_at >= datetime.combine(start_date, datetime.min.time())
    ).group_by(Order.status)

    result = await db.execute(query)
    statuses = result.all()

    return {
        "items": [
            {"status": s.status, "count": s.count}
            for s in statuses
        ],
        "period_days": days,
    }


# ==================== Revenue by Channel ====================
@router.get("/channels/revenue")
async def get_channel_revenue(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get revenue breakdown by sales channel."""
    from app.models.channel import SalesChannel

    start_date = date.today() - timedelta(days=days)

    query = select(
        SalesChannel.id,
        SalesChannel.name,
        SalesChannel.channel_type,
        func.count(Order.id).label("orders"),
        func.coalesce(func.sum(Order.total_amount), 0).label("revenue")
    ).select_from(Order).join(
        SalesChannel, Order.channel_id == SalesChannel.id
    ).where(
        and_(
            Order.status.notin_(["CANCELLED", "DRAFT"]),
            Order.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    ).group_by(SalesChannel.id, SalesChannel.name, SalesChannel.channel_type)

    result = await db.execute(query)
    channels = result.all()

    total_revenue = sum(float(c.revenue or 0) for c in channels)

    return {
        "items": [
            {
                "id": str(c.id),
                "name": c.name,
                "channel_type": c.channel_type,
                "orders": c.orders,
                "revenue": float(c.revenue or 0),
                "percentage": round((float(c.revenue or 0) / total_revenue * 100) if total_revenue > 0 else 0, 2),
            }
            for c in channels
        ],
        "total_revenue": total_revenue,
        "period_days": days,
    }


# ==================== Financial Summary ====================
@router.get("/finance/summary")
async def get_financial_summary(
    db: DB,
    current_user: User = Depends(get_current_user),
    month: Optional[int] = None,
    year: Optional[int] = None,
):
    """Get financial summary - receivables, payables, cash balance."""
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year

    # Get account balances from Chart of Accounts
    # Accounts Receivable (typically code 1200 or similar)
    ar_query = select(
        func.coalesce(func.sum(ChartOfAccount.current_balance), 0)
    ).where(ChartOfAccount.account_code.like("12%"))  # Receivables
    receivables = await db.scalar(ar_query) or 0

    # Accounts Payable (typically code 2100 or similar)
    ap_query = select(
        func.coalesce(func.sum(ChartOfAccount.current_balance), 0)
    ).where(ChartOfAccount.account_code.like("21%"))  # Payables
    payables = await db.scalar(ap_query) or 0

    # Cash & Bank (typically code 1000-1100)
    cash_query = select(
        func.coalesce(func.sum(ChartOfAccount.current_balance), 0)
    ).where(
        ChartOfAccount.account_code.like("10%")
    )  # Cash/Bank
    cash_balance = await db.scalar(cash_query) or 0

    # Revenue this month
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    revenue_query = select(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).where(
        and_(
            Order.status.notin_(["CANCELLED", "DRAFT"]),
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
            Order.created_at < datetime.combine(month_end, datetime.min.time())
        )
    )
    revenue = await db.scalar(revenue_query) or 0

    return {
        "month": month,
        "year": year,
        "accounts_receivable": float(receivables),
        "accounts_payable": float(payables),
        "cash_balance": float(cash_balance),
        "revenue_this_month": float(revenue),
    }


# ==================== Recent Activity ====================
@router.get("/activity/recent")
async def get_recent_activity(
    db: DB,
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
):
    """Get recent activity across the system."""
    from app.models.audit_log import AuditLog

    query = select(AuditLog).options(
        selectinload(AuditLog.user)
    ).order_by(desc(AuditLog.created_at)).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "user_name": f"{log.user.first_name} {log.user.last_name}" if log.user else "System",
                "description": log.description,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


# ==================== KPI Summary ====================
@router.get("/kpis")
async def get_kpi_summary(
    db: DB,
    current_user: User = Depends(get_current_user),
):
    """Get key performance indicators summary."""
    today = date.today()
    month_start = today.replace(day=1)

    # Orders today
    orders_today_query = select(func.count(Order.id)).where(
        and_(
            func.date(Order.created_at) == today,
            Order.status.notin_(["CANCELLED", "DRAFT"])
        )
    )
    orders_today = await db.scalar(orders_today_query) or 0

    # Revenue today
    revenue_today_query = select(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).where(
        and_(
            func.date(Order.created_at) == today,
            Order.status.notin_(["CANCELLED", "DRAFT"])
        )
    )
    revenue_today = await db.scalar(revenue_today_query) or 0

    # Orders this month
    orders_month_query = select(func.count(Order.id)).where(
        and_(
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
            Order.status.notin_(["CANCELLED", "DRAFT"])
        )
    )
    orders_month = await db.scalar(orders_month_query) or 0

    # Revenue this month
    revenue_month_query = select(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).where(
        and_(
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
            Order.status.notin_(["CANCELLED", "DRAFT"])
        )
    )
    revenue_month = await db.scalar(revenue_month_query) or 0

    # Average order value
    aov_query = select(
        func.coalesce(func.avg(Order.total_amount), 0)
    ).where(
        and_(
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
            Order.status.notin_(["CANCELLED", "DRAFT"])
        )
    )
    aov = await db.scalar(aov_query) or 0

    # Pending orders
    pending_query = select(func.count(Order.id)).where(
        Order.status.in_(["PENDING", "CONFIRMED", "PROCESSING"])
    )
    pending_orders = await db.scalar(pending_query) or 0

    return {
        "today": {
            "orders": orders_today,
            "revenue": float(revenue_today),
        },
        "this_month": {
            "orders": orders_month,
            "revenue": float(revenue_month),
            "average_order_value": float(aov),
        },
        "pending_orders": pending_orders,
    }


# ==================== Combined Dashboard (single-call) ====================

@router.get("/combined")
async def get_combined_dashboard(
    db: DB,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """
    Single combined endpoint — returns all dashboard data in one call.
    Replaces 14 separate API calls with 1, dramatically reducing dashboard load time.
    All queries run sequentially on the shared AsyncSession.
    """
    today = date.today()
    start_date = today - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=6)

    async def _safe(coro):
        try:
            return await coro
        except Exception:
            return None

    # ---------- 1. KPI Stats ----------
    try:
        # Orders stats
        orders_q = await db.execute(
            select(
                func.count(Order.id).label("total"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            ).where(Order.status.notin_(["CANCELLED", "DRAFT"]))
        )
        orders_row = orders_q.one()

        month_orders_q = await db.execute(
            select(
                func.count(Order.id).label("count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            ).where(
                and_(
                    Order.status.notin_(["CANCELLED", "DRAFT"]),
                    Order.created_at >= datetime.combine(month_start, datetime.min.time()),
                )
            )
        )
        month_row = month_orders_q.one()

        prev_revenue_q = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                and_(
                    Order.status.notin_(["CANCELLED", "DRAFT"]),
                    Order.created_at >= datetime.combine(prev_start, datetime.min.time()),
                    Order.created_at < datetime.combine(start_date, datetime.min.time()),
                )
            )
        )
        prev_revenue = float(prev_revenue_q.scalar() or 0)

        period_revenue_q = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                and_(
                    Order.status.notin_(["CANCELLED", "DRAFT"]),
                    Order.created_at >= datetime.combine(start_date, datetime.min.time()),
                )
            )
        )
        period_revenue = float(period_revenue_q.scalar() or 0)
        revenue_change = round(
            (period_revenue - prev_revenue) / prev_revenue * 100 if prev_revenue > 0 else 0, 2
        )

        pending_q = await db.execute(
            select(func.count(Order.id)).where(
                Order.status.in_(["PENDING", "CONFIRMED", "PROCESSING"])
            )
        )
        pending_orders = pending_q.scalar() or 0

        total_customers_q = await db.execute(select(func.count(Customer.id)))
        total_customers = total_customers_q.scalar() or 0

        total_products_q = await db.execute(select(func.count(Product.id)))
        total_products = total_products_q.scalar() or 0

        low_stock_q = await db.execute(
            select(func.count(Inventory.id)).where(
                and_(Inventory.total_quantity <= Inventory.reorder_level, Inventory.total_quantity > 0)
            )
        )
        low_stock = low_stock_q.scalar() or 0

        out_of_stock_q = await db.execute(
            select(func.count(Inventory.id)).where(Inventory.total_quantity <= 0)
        )
        out_of_stock = out_of_stock_q.scalar() or 0

        # Shipments in transit
        try:
            from app.models.shipment import Shipment
            transit_q = await db.execute(
                select(func.count(Shipment.id)).where(Shipment.status == "IN_TRANSIT")
            )
            shipments_in_transit = transit_q.scalar() or 0
        except Exception:
            shipments_in_transit = 0

        # Service requests
        try:
            from app.models.service import ServiceRequest
            service_q = await db.execute(
                select(func.count(ServiceRequest.id)).where(
                    ServiceRequest.status.in_(["PENDING", "OPEN"])
                )
            )
            pending_service = service_q.scalar() or 0
        except Exception:
            pending_service = 0

        stats = {
            "total_orders": int(orders_row.total),
            "total_revenue": float(orders_row.revenue),
            "total_customers": total_customers,
            "total_products": total_products,
            "pending_orders": pending_orders,
            "pending_service_requests": pending_service,
            "low_stock_items": low_stock,
            "out_of_stock_items": out_of_stock,
            "shipments_in_transit": shipments_in_transit,
            "this_month_orders": int(month_row.count),
            "this_month_revenue": float(month_row.revenue),
            "revenue_change": revenue_change,
            "orders_change": 0,
            "customers_change": 0,
        }
    except Exception as e:
        stats = {"error": str(e)}

    # ---------- 2. Sales Trend (last 7 days, by day) ----------
    try:
        trend_q = await db.execute(
            select(
                func.date(Order.created_at).label("period"),
                func.count(Order.id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            ).where(
                and_(
                    Order.status.notin_(["CANCELLED", "DRAFT"]),
                    Order.created_at >= datetime.combine(week_start, datetime.min.time()),
                )
            ).group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        trend_rows = trend_q.all()
        sales_trend = {
            "labels": [str(r.period)[:10] for r in trend_rows],
            "orders": [r.orders for r in trend_rows],
            "revenue": [float(r.revenue or 0) for r in trend_rows],
        }
    except Exception:
        sales_trend = {"labels": [], "orders": [], "revenue": []}

    # ---------- 3. Order Status Distribution ----------
    try:
        status_q = await db.execute(
            select(Order.status, func.count(Order.id).label("count"))
            .where(Order.created_at >= datetime.combine(start_date, datetime.min.time()))
            .group_by(Order.status)
        )
        order_status = {
            "items": [{"status": r.status, "count": r.count} for r in status_q.all()]
        }
    except Exception:
        order_status = {"items": []}

    # ---------- 4. Category Sales ----------
    try:
        cat_q = await db.execute(
            select(
                Category.name,
                func.sum(OrderItem.total_amount).label("revenue"),
            ).select_from(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .join(Category, Product.category_id == Category.id)
            .where(
                and_(
                    Order.status.notin_(["CANCELLED", "DRAFT"]),
                    Order.created_at >= datetime.combine(start_date, datetime.min.time()),
                )
            )
            .group_by(Category.name)
            .order_by(desc("revenue"))
            .limit(6)
        )
        cat_rows = cat_q.all()
        total_cat_rev = sum(float(r.revenue or 0) for r in cat_rows)
        category_sales = {
            "items": [
                {
                    "name": r.name,
                    "revenue": float(r.revenue or 0),
                    "percentage": round(
                        float(r.revenue or 0) / total_cat_rev * 100 if total_cat_rev > 0 else 0, 2
                    ),
                }
                for r in cat_rows
            ]
        }
    except Exception:
        category_sales = {"items": []}

    # ---------- 5. Top Products ----------
    try:
        top_q = await db.execute(
            select(
                Product.id,
                Product.name,
                Product.sku,
                func.sum(OrderItem.quantity).label("quantity_sold"),
                func.sum(OrderItem.total_amount).label("revenue"),
            ).select_from(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .where(
                and_(
                    Order.status.notin_(["CANCELLED", "DRAFT"]),
                    Order.created_at >= datetime.combine(start_date, datetime.min.time()),
                )
            )
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(desc("revenue"))
            .limit(5)
        )
        top_products = {
            "items": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "sku": r.sku,
                    "sales": int(r.quantity_sold or 0),
                    "revenue": float(r.revenue or 0),
                }
                for r in top_q.all()
            ]
        }
    except Exception:
        top_products = {"items": []}

    # ---------- 6. Recent Activity ----------
    try:
        from app.models.audit_log import AuditLog
        activity_q = await db.execute(
            select(AuditLog).options(selectinload(AuditLog.user))
            .order_by(desc(AuditLog.created_at))
            .limit(6)
        )
        activity_rows = activity_q.scalars().all()
        recent_activity = [
            {
                "id": str(log.id),
                "action": log.action,
                "entity_type": log.entity_type,
                "user_name": f"{log.user.first_name} {log.user.last_name}" if log.user else "System",
                "description": log.description,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "type": log.entity_type,
                "color": "blue",
                "title": f"{log.action} {log.entity_type}",
                "timestamp": log.created_at.isoformat() if log.created_at else None,
            }
            for log in activity_rows
        ]
    except Exception:
        recent_activity = []

    # ---------- 7. HR Dashboard ----------
    try:
        from app.api.v1.endpoints.hr import get_hr_dashboard
        hr_data = await get_hr_dashboard(db=db, current_user=current_user)
        hr_dashboard = hr_data if isinstance(hr_data, dict) else (
            hr_data.dict() if hasattr(hr_data, "dict") else hr_data.model_dump() if hasattr(hr_data, "model_dump") else None
        )
    except Exception:
        hr_dashboard = None

    # ---------- 8. Fixed Assets Dashboard ----------
    try:
        from app.api.v1.endpoints.fixed_assets import get_fixed_assets_dashboard
        fa_data = await get_fixed_assets_dashboard(db=db, current_user=current_user)
        fixed_assets = fa_data if isinstance(fa_data, dict) else (
            fa_data.dict() if hasattr(fa_data, "dict") else fa_data.model_dump() if hasattr(fa_data, "model_dump") else None
        )
    except Exception:
        fixed_assets = None

    return {
        "stats": stats,
        "sales_trend": sales_trend,
        "order_status": order_status,
        "category_sales": category_sales,
        "top_products": top_products,
        "recent_activity": recent_activity,
        "hr_dashboard": hr_dashboard,
        "fixed_assets": fixed_assets,
        "period_days": days,
    }
