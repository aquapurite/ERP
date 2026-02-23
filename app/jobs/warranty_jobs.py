"""
Warranty & AMC Expiry Alert Jobs

Scheduled jobs for warranty and AMC contract management:
- Warranty expiry funnel: 90/60/30/15/7 day notifications
- AMC renewal reminders: 60/30/15/7 day cadence
- Auto-expire ACTIVE contracts past end_date
- Grace period management for lapsed contracts
"""

import logging
from datetime import date, datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Warranty expiry notification windows (days before expiry)
WARRANTY_EXPIRY_WINDOWS = [90, 60, 30, 15, 7]

# AMC renewal reminder windows
AMC_RENEWAL_WINDOWS = [60, 30, 15, 7]


async def check_warranty_expiry():
    """
    Combined daily job for warranty and AMC management.

    Runs daily at 9 AM IST to:
    1. Send warranty expiry notifications (90/60/30/15/7 days) to push AMC conversion
    2. Send AMC renewal reminders (60/30/15/7 days) before contract expiry
    3. Auto-expire ACTIVE AMC contracts past their end_date
    4. Set grace_end_date on newly expired contracts
    """
    logger.info("Starting warranty/AMC expiry check...")
    start_time = datetime.now(timezone.utc)
    warranty_alerts_sent = 0
    amc_reminders_sent = 0
    contracts_expired = 0

    try:
        from app.database import get_db_session
        from app.models.amc import AMCContract, AMCPlan
        from app.models.installation import Installation
        from app.models.customer import Customer
        from app.models.product import Product
        from app.services.notification_service import (
            NotificationService, NotificationType, NotificationChannel
        )
        from sqlalchemy import select, and_, or_, not_, exists

        async with get_db_session() as session:
            today = date.today()

            # ========== PART 1: WARRANTY EXPIRY FUNNEL ==========
            # Find installations with warranty expiring in each window
            # that do NOT have an active AMC contract (these are AMC conversion leads)
            for days_ahead in WARRANTY_EXPIRY_WINDOWS:
                target_date = today + timedelta(days=days_ahead)

                try:
                    # Subquery: installations that have an active AMC
                    active_amc_subq = (
                        select(AMCContract.serial_number)
                        .where(AMCContract.status.in_(["ACTIVE", "PENDING"]))
                        .correlate(Installation)
                    )

                    result = await session.execute(
                        select(Installation, Customer, Product)
                        .join(Customer, Customer.id == Installation.customer_id)
                        .join(Product, Product.id == Installation.product_id)
                        .where(
                            and_(
                                Installation.warranty_end_date == target_date,
                                Installation.status.in_(["COMPLETED", "ACTIVE"]),
                                not_(Installation.serial_number.in_(active_amc_subq)),
                            )
                        )
                    )
                    expiring_installs = result.all()

                    for install, customer, product in expiring_installs:
                        try:
                            notification_service = NotificationService(session)

                            urgency = "soon" if days_ahead <= 15 else "in the coming months"
                            message = (
                                f"Dear {customer.first_name}, your warranty for "
                                f"{product.name} (S/N: {install.serial_number}) "
                                f"expires on {target_date.strftime('%d-%b-%Y')} "
                                f"({days_ahead} days). "
                            )

                            if days_ahead <= 7:
                                message += (
                                    "Last chance to get an AMC at the best price! "
                                    "Avoid expensive repairs - call us now or visit aquapurite.com/account/amc"
                                )
                            elif days_ahead <= 30:
                                message += (
                                    "Protect your purifier with an AMC plan starting at just Rs 999/year. "
                                    "Visit aquapurite.com/account/amc"
                                )
                            else:
                                message += (
                                    "Consider an Annual Maintenance Contract for continued "
                                    "peace of mind. Visit aquapurite.com/account/amc"
                                )

                            if customer.phone:
                                await notification_service.send_notification(
                                    recipient_phone=customer.phone,
                                    recipient_email=getattr(customer, 'email', None),
                                    notification_type=NotificationType.WARRANTY_EXPIRY_REMINDER,
                                    channel=NotificationChannel.SMS,
                                    custom_message=message,
                                    template_data={},
                                )

                            if getattr(customer, 'email', None):
                                await notification_service.send_notification(
                                    recipient_phone=customer.phone or "",
                                    recipient_email=customer.email,
                                    notification_type=NotificationType.WARRANTY_EXPIRY_REMINDER,
                                    channel=NotificationChannel.EMAIL,
                                    custom_message=message,
                                    template_data={},
                                )

                            warranty_alerts_sent += 1
                            logger.info(
                                f"Warranty expiry alert sent ({days_ahead}d) for "
                                f"{install.serial_number} to {customer.phone}"
                            )

                        except Exception as e:
                            logger.error(
                                f"Failed to send warranty alert for "
                                f"{install.serial_number}: {e}"
                            )

                except Exception as e:
                    logger.error(f"Warranty expiry check failed for {days_ahead}d window: {e}")

            # ========== PART 2: AMC RENEWAL REMINDERS ==========
            for days_ahead in AMC_RENEWAL_WINDOWS:
                target_date = today + timedelta(days=days_ahead)

                try:
                    result = await session.execute(
                        select(AMCContract, Customer, Product)
                        .join(Customer, Customer.id == AMCContract.customer_id)
                        .join(Product, Product.id == AMCContract.product_id)
                        .where(
                            and_(
                                AMCContract.status == "ACTIVE",
                                AMCContract.end_date == target_date,
                            )
                        )
                    )
                    expiring_contracts = result.all()

                    for contract, customer, product in expiring_contracts:
                        try:
                            notification_service = NotificationService(session)

                            if days_ahead <= 7:
                                message = (
                                    f"URGENT: Dear {customer.first_name}, your AMC "
                                    f"({contract.contract_number}) for {product.name} "
                                    f"expires in {days_ahead} days! Renew now to avoid "
                                    f"inspection fees. Visit aquapurite.com/account/amc "
                                    f"or call us at 1800-123-4567"
                                )
                            elif days_ahead <= 15:
                                message = (
                                    f"Dear {customer.first_name}, your AMC "
                                    f"({contract.contract_number}) for {product.name} "
                                    f"expires on {contract.end_date.strftime('%d-%b-%Y')}. "
                                    f"Renew before expiry for seamless coverage! "
                                    f"Multi-year plans save up to 20%."
                                )
                            else:
                                message = (
                                    f"Dear {customer.first_name}, your AMC "
                                    f"({contract.contract_number}) for {product.name} "
                                    f"(S/N: {contract.serial_number}) expires on "
                                    f"{contract.end_date.strftime('%d-%b-%Y')} "
                                    f"({days_ahead} days). Renew now for uninterrupted "
                                    f"service! Visit aquapurite.com/account/amc"
                                )

                            if customer.phone:
                                await notification_service.send_notification(
                                    recipient_phone=customer.phone,
                                    recipient_email=getattr(customer, 'email', None),
                                    notification_type=NotificationType.AMC_RENEWAL_REMINDER,
                                    channel=NotificationChannel.SMS,
                                    custom_message=message,
                                    template_data={},
                                )

                            if getattr(customer, 'email', None):
                                await notification_service.send_notification(
                                    recipient_phone=customer.phone or "",
                                    recipient_email=customer.email,
                                    notification_type=NotificationType.AMC_RENEWAL_REMINDER,
                                    channel=NotificationChannel.EMAIL,
                                    custom_message=message,
                                    template_data={},
                                )

                            # Mark reminder sent on the final reminder
                            if days_ahead == 7:
                                contract.renewal_reminder_sent = True

                            amc_reminders_sent += 1
                            logger.info(
                                f"AMC renewal reminder sent ({days_ahead}d) for "
                                f"{contract.contract_number} to {customer.phone}"
                            )

                        except Exception as e:
                            logger.error(
                                f"Failed to send AMC reminder for "
                                f"{contract.contract_number}: {e}"
                            )

                except Exception as e:
                    logger.error(f"AMC renewal check failed for {days_ahead}d window: {e}")

            # ========== PART 3: AUTO-EXPIRE CONTRACTS & SET GRACE ==========
            try:
                expired_result = await session.execute(
                    select(AMCContract).options(
                        selectinload(AMCContract.plan)
                    ).where(
                        and_(
                            AMCContract.status == "ACTIVE",
                            AMCContract.end_date < today,
                        )
                    )
                )
                expired_contracts = expired_result.scalars().all()

                for contract in expired_contracts:
                    contract.status = "EXPIRED"

                    # Set grace period from plan or default 15 days
                    grace_days = 15
                    if contract.plan and hasattr(contract.plan, 'grace_period_days'):
                        grace_days = contract.plan.grace_period_days or 15
                    contract.grace_end_date = contract.end_date + timedelta(days=grace_days)

                    contracts_expired += 1
                    logger.info(
                        f"AMC contract {contract.contract_number} auto-expired "
                        f"(end_date: {contract.end_date}, grace until: {contract.grace_end_date})"
                    )

                # Mark contracts past grace period as requiring inspection
                past_grace_result = await session.execute(
                    select(AMCContract).where(
                        and_(
                            AMCContract.status == "EXPIRED",
                            AMCContract.grace_end_date < today,
                            AMCContract.requires_inspection == False,
                        )
                    )
                )
                past_grace_contracts = past_grace_result.scalars().all()

                for contract in past_grace_contracts:
                    contract.requires_inspection = True
                    logger.info(
                        f"AMC contract {contract.contract_number} now requires inspection "
                        f"(grace ended: {contract.grace_end_date})"
                    )

            except Exception as e:
                logger.error(f"Auto-expire/grace check failed: {e}")

            await session.commit()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Warranty/AMC expiry check completed: "
            f"{warranty_alerts_sent} warranty alerts, "
            f"{amc_reminders_sent} AMC reminders, "
            f"{contracts_expired} contracts expired "
            f"in {elapsed:.2f}s"
        )

    except Exception as e:
        logger.error(f"Warranty/AMC expiry check failed: {e}")
        raise
