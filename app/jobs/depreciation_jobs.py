"""
Depreciation Background Jobs

Scheduled job for monthly auto-depreciation:
- Runs on 1st of every month at 2 AM IST
- Depreciates all active assets for the previous month
- Creates depreciation entries + GL journal postings
- Skips assets already depreciated for that period
"""

import logging
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_financial_year(d: date) -> str:
    """Get Indian financial year string for a date (e.g., '2025-26')."""
    if d.month >= 4:
        return f"{d.year}-{str(d.year + 1)[-2:]}"
    else:
        return f"{d.year - 1}-{str(d.year)[-2:]}"


async def run_monthly_depreciation():
    """
    Auto-run monthly depreciation for all active assets.

    Runs on 1st of every month. Depreciates for the previous month.
    Example: Runs on 1st March → depreciates for February (period_date = Feb last day).

    Replicates the logic from POST /api/v1/fixed-assets/depreciation/run
    but runs automatically without user trigger.
    """
    logger.info("Starting monthly auto-depreciation...")
    start_time = datetime.now(timezone.utc)
    assets_processed = 0
    assets_skipped = 0
    total_depreciation = Decimal("0")

    try:
        from app.database import get_db_session
        from app.models.fixed_assets import (
            Asset, AssetCategory, AssetStatus,
            DepreciationEntry, DepreciationMethod,
        )
        from app.models.accounting import (
            JournalEntry, JournalEntryLine, GeneralLedger,
            JournalEntryStatus as JournalStatus,
            FinancialPeriod, FinancialPeriodStatus as PeriodStatus,
            ChartOfAccount,
        )
        from sqlalchemy import select, func, and_
        from sqlalchemy.orm import selectinload
        import uuid as uuid_module

        # Calculate period: previous month's last day
        today = date.today()
        first_of_this_month = today.replace(day=1)
        period_date = first_of_this_month - timedelta(days=1)  # Last day of prev month
        financial_year = get_financial_year(period_date)

        logger.info(
            f"Depreciation period: {period_date.strftime('%B %Y')} "
            f"(FY {financial_year}, period_date={period_date})"
        )

        async with get_db_session() as db:
            # Get all active assets with their categories
            query = (
                select(Asset)
                .options(selectinload(Asset.category))
                .where(Asset.status == AssetStatus.ACTIVE)
            )
            result = await db.execute(query)
            assets = result.scalars().all()

            if not assets:
                logger.info("No active assets found. Skipping depreciation.")
                return

            # Get open financial period
            period_r = await db.execute(
                select(FinancialPeriod).where(
                    and_(
                        FinancialPeriod.start_date <= period_date,
                        FinancialPeriod.end_date >= period_date,
                        FinancialPeriod.status == PeriodStatus.OPEN,
                    )
                ).limit(1)
            )
            period = period_r.scalar_one_or_none()

            if not period:
                logger.warning(
                    f"No open financial period found for {period_date}. "
                    "Depreciation entries will be created but GL posting skipped."
                )

            entries = []

            for asset in assets:
                # Check if already depreciated for this period
                existing = await db.execute(
                    select(DepreciationEntry)
                    .where(DepreciationEntry.asset_id == asset.id)
                    .where(DepreciationEntry.period_date == period_date)
                )
                if existing.scalar_one_or_none():
                    assets_skipped += 1
                    continue

                # Get depreciation settings
                method = asset.depreciation_method or (
                    asset.category.depreciation_method if asset.category else "SLM"
                )
                rate = asset.depreciation_rate or (
                    asset.category.depreciation_rate if asset.category else Decimal("10")
                )
                salvage = asset.salvage_value or Decimal("0")

                # Calculate depreciation
                opening_value = asset.current_book_value
                if method == "SLM" or method == DepreciationMethod.SLM:
                    annual_dep = (opening_value - salvage) * (rate / 100)
                    depreciation_amount = round(annual_dep / 12, 2)
                else:  # WDV
                    annual_dep = opening_value * (rate / 100)
                    depreciation_amount = round(annual_dep / 12, 2)

                # Don't depreciate below salvage value
                if opening_value - depreciation_amount < salvage:
                    depreciation_amount = opening_value - salvage
                    if depreciation_amount <= 0:
                        assets_skipped += 1
                        continue

                closing_value = opening_value - depreciation_amount
                new_accumulated = asset.accumulated_depreciation + depreciation_amount

                # Create depreciation entry
                entry = DepreciationEntry(
                    asset_id=asset.id,
                    period_date=period_date,
                    financial_year=financial_year,
                    opening_book_value=opening_value,
                    depreciation_method=method,
                    depreciation_rate=rate,
                    depreciation_amount=depreciation_amount,
                    closing_book_value=closing_value,
                    accumulated_depreciation=new_accumulated,
                    is_posted=False,
                    processed_at=datetime.now(timezone.utc),
                )

                db.add(entry)

                # Update asset
                asset.accumulated_depreciation = new_accumulated
                asset.current_book_value = closing_value
                asset.last_depreciation_date = period_date

                entries.append((entry, asset))
                assets_processed += 1
                total_depreciation += depreciation_amount

            # Flush to get entry IDs
            await db.flush()

            # GL Posting
            gl_posted = 0
            if entries and period:
                for dep_entry, asset in entries:
                    expense_account_id = (
                        asset.category.expense_account_id if asset.category else None
                    )
                    dep_account_id = (
                        asset.category.depreciation_account_id if asset.category else None
                    )

                    if not expense_account_id or not dep_account_id:
                        continue

                    # Generate journal entry number
                    count_r = await db.execute(
                        select(func.count(JournalEntry.id)).where(
                            func.date(JournalEntry.created_at) == today
                        )
                    )
                    jv_count = count_r.scalar() or 0
                    entry_number = (
                        f"JV-{today.strftime('%Y%m%d')}-{str(jv_count + 1).zfill(4)}"
                    )

                    journal = JournalEntry(
                        id=uuid_module.uuid4(),
                        entry_number=entry_number,
                        entry_type="DEPRECIATION",
                        entry_date=period_date,
                        period_id=period.id,
                        narration=(
                            f"Auto-depreciation for {asset.name} - "
                            f"{period_date.strftime('%B %Y')}"
                        ),
                        source_type="depreciation",
                        source_id=dep_entry.id,
                        total_debit=dep_entry.depreciation_amount,
                        total_credit=dep_entry.depreciation_amount,
                        status=JournalStatus.DRAFT.value,
                    )
                    db.add(journal)
                    await db.flush()

                    # Debit: Depreciation Expense
                    dr_line = JournalEntryLine(
                        id=uuid_module.uuid4(),
                        journal_entry_id=journal.id,
                        account_id=expense_account_id,
                        debit_amount=dep_entry.depreciation_amount,
                        credit_amount=Decimal("0"),
                        description=(
                            f"Depreciation expense - {asset.name} "
                            f"({period_date.strftime('%b %Y')})"
                        ),
                    )
                    db.add(dr_line)

                    # Credit: Accumulated Depreciation
                    cr_line = JournalEntryLine(
                        id=uuid_module.uuid4(),
                        journal_entry_id=journal.id,
                        account_id=dep_account_id,
                        debit_amount=Decimal("0"),
                        credit_amount=dep_entry.depreciation_amount,
                        description=(
                            f"Accumulated depreciation - {asset.name} "
                            f"({period_date.strftime('%b %Y')})"
                        ),
                    )
                    db.add(cr_line)

                    # Post journal
                    journal.status = JournalStatus.POSTED.value

                    # Link journal to depreciation entry
                    dep_entry.journal_entry_id = journal.id
                    dep_entry.is_posted = True

                    gl_posted += 1

            await db.commit()

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Monthly depreciation complete: "
                f"processed={assets_processed}, skipped={assets_skipped}, "
                f"total_depreciation=₹{total_depreciation:,.2f}, "
                f"gl_posted={gl_posted}, elapsed={elapsed:.1f}s"
            )

    except Exception as e:
        logger.error(f"Monthly depreciation failed: {e}", exc_info=True)
