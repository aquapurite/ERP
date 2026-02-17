"""
Banking Background Jobs

Scheduled jobs for bank reconciliation:
- Auto-reconcile bank transactions using ML matching
"""

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def auto_reconcile_bank_transactions():
    """
    Auto-reconcile bank transactions using ML-based matching.

    Runs every 2 hours to:
    1. Find all bank accounts with unreconciled transactions (last 90 days)
    2. For each account, run ML auto-reconciliation
    3. Log results and statistics

    Uses BankReconciliationMLService with auto-match threshold of 0.85.
    """
    logger.info("Starting auto bank reconciliation...")
    start_time = datetime.now(timezone.utc)
    total_matched = 0
    total_skipped = 0
    accounts_processed = 0

    try:
        from app.database import get_db_session
        from app.services.bank_reconciliation_ml import BankReconciliationMLService
        from app.models.banking import BankAccount, BankTransaction
        from sqlalchemy import select, func, and_

        async with get_db_session() as session:
            # Find bank accounts that have unreconciled transactions in the last 90 days
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=90)).date()

            accounts_with_unreconciled = await session.execute(
                select(BankAccount.id, BankAccount.account_number, BankAccount.bank_name)
                .join(
                    BankTransaction,
                    BankTransaction.bank_account_id == BankAccount.id
                )
                .where(
                    and_(
                        BankTransaction.is_reconciled == False,
                        BankTransaction.transaction_date >= cutoff_date,
                    )
                )
                .group_by(BankAccount.id, BankAccount.account_number, BankAccount.bank_name)
                .having(func.count(BankTransaction.id) > 0)
            )
            accounts = accounts_with_unreconciled.fetchall()

            if not accounts:
                logger.info("No bank accounts with unreconciled transactions found")
                return

            for account in accounts:
                try:
                    ml_service = BankReconciliationMLService(session)
                    result = await ml_service.auto_reconcile(account.id)

                    matched = result.get('auto_matched_count', 0)
                    skipped = result.get('skipped_count', 0)
                    total_matched += matched
                    total_skipped += skipped
                    accounts_processed += 1

                    if matched > 0:
                        logger.info(
                            f"Bank account {account.bank_name} ({account.account_number}): "
                            f"auto-matched {matched}, skipped {skipped}"
                        )

                except Exception as e:
                    logger.error(
                        f"Reconciliation failed for account {account.account_number}: {e}"
                    )

            await session.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Auto bank reconciliation completed: "
            f"{accounts_processed} accounts processed, "
            f"{total_matched} transactions matched, "
            f"{total_skipped} skipped "
            f"in {elapsed:.2f}s"
        )

    except Exception as e:
        logger.error(f"Auto bank reconciliation failed: {e}")
        raise
