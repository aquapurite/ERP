"""
Warranty & AMC Expiry Alert Jobs

Scheduled jobs for warranty and AMC contract management:
- Check for expiring AMC contracts (30/15/7 days)
- Send renewal reminders via SMS/Email
- Auto-expire past-due ACTIVE contracts
"""

import logging
from datetime import date, datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def check_warranty_expiry():
    """
    Check for AMC contracts nearing expiry and send reminders.

    Runs daily at 9 AM IST to:
    1. Find ACTIVE AMC contracts expiring in 30, 15, or 7 days
    2. Send SMS/email renewal reminders to customers
    3. Mark renewal_reminder_sent = true
    4. Auto-expire ACTIVE contracts past their end_date
    """
    logger.info("Starting warranty/AMC expiry check...")
    start_time = datetime.now(timezone.utc)
    reminders_sent = 0
    contracts_expired = 0

    try:
        from app.database import get_db_session
        from app.models.amc import AMCContract
        from app.models.customer import Customer
        from app.models.product import Product
        from app.services.notification_service import (
            NotificationService, NotificationType, NotificationChannel
        )
        from sqlalchemy import select, and_, or_

        async with get_db_session() as session:
            today = date.today()
            reminder_windows = [30, 15, 7]  # days before expiry

            for days_ahead in reminder_windows:
                target_date = today + timedelta(days=days_ahead)

                # Find ACTIVE contracts expiring on target_date that haven't been reminded
                result = await session.execute(
                    select(AMCContract, Customer, Product)
                    .join(Customer, Customer.id == AMCContract.customer_id)
                    .join(Product, Product.id == AMCContract.product_id)
                    .where(
                        and_(
                            AMCContract.status == "ACTIVE",
                            AMCContract.end_date == target_date,
                            AMCContract.renewal_reminder_sent == False,
                        )
                    )
                )
                expiring_contracts = result.all()

                for contract, customer, product in expiring_contracts:
                    try:
                        notification_service = NotificationService(session)

                        # Send SMS reminder
                        if customer.phone:
                            await notification_service.send_notification(
                                recipient_phone=customer.phone,
                                recipient_email=getattr(customer, 'email', None),
                                notification_type=NotificationType.AMC_RENEWAL_REMINDER,
                                channel=NotificationChannel.SMS,
                                custom_message=(
                                    f"Dear {customer.first_name}, your AMC contract "
                                    f"({contract.contract_number}) for {product.name} "
                                    f"(S/N: {contract.serial_number}) expires on "
                                    f"{contract.end_date.strftime('%d-%b-%Y')} "
                                    f"({days_ahead} days). Renew now to continue "
                                    f"uninterrupted service! Call us or visit aquapurite.com"
                                ),
                                template_data={},
                            )

                        # Send email reminder if email available
                        if getattr(customer, 'email', None):
                            await notification_service.send_notification(
                                recipient_phone=customer.phone or "",
                                recipient_email=customer.email,
                                notification_type=NotificationType.AMC_RENEWAL_REMINDER,
                                channel=NotificationChannel.EMAIL,
                                custom_message=(
                                    f"AMC Renewal Reminder: Your contract "
                                    f"{contract.contract_number} for {product.name} "
                                    f"expires on {contract.end_date.strftime('%d-%b-%Y')}. "
                                    f"Renew now to keep your warranty and service benefits."
                                ),
                                template_data={},
                            )

                        # Mark reminder as sent (only on the first reminder window hit)
                        if days_ahead == 7:
                            contract.renewal_reminder_sent = True

                        reminders_sent += 1
                        logger.info(
                            f"AMC expiry reminder sent for {contract.contract_number} "
                            f"({days_ahead} days) to {customer.phone}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to send AMC reminder for "
                            f"{contract.contract_number}: {e}"
                        )

            # Auto-expire ACTIVE contracts that have passed their end_date
            expired_result = await session.execute(
                select(AMCContract).where(
                    and_(
                        AMCContract.status == "ACTIVE",
                        AMCContract.end_date < today,
                    )
                )
            )
            expired_contracts = expired_result.scalars().all()

            for contract in expired_contracts:
                contract.status = "EXPIRED"
                contracts_expired += 1
                logger.info(
                    f"AMC contract {contract.contract_number} auto-expired "
                    f"(end_date: {contract.end_date})"
                )

            await session.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Warranty/AMC expiry check completed: "
            f"{reminders_sent} reminders sent, "
            f"{contracts_expired} contracts expired "
            f"in {elapsed:.2f}s"
        )

    except Exception as e:
        logger.error(f"Warranty/AMC expiry check failed: {e}")
        raise
