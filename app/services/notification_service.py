"""
Customer Notification Service

Handles sending notifications to customers via various channels:
- SMS (via provider like MSG91, Twilio, etc.)
- Email (via SMTP or provider like SendGrid, SES)
- Push Notifications (via Firebase FCM)
- WhatsApp (via provider API)

This is a placeholder implementation that logs notifications.
In production, integrate with actual providers.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    WHATSAPP = "whatsapp"


class NotificationType(str, Enum):
    """Types of notifications."""
    # Order related
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"

    # Installation related
    INSTALLATION_SCHEDULED = "installation_scheduled"
    INSTALLATION_REMINDER = "installation_reminder"
    INSTALLATION_COMPLETED = "installation_completed"
    TECHNICIAN_ASSIGNED = "technician_assigned"
    TECHNICIAN_ON_THE_WAY = "technician_on_the_way"

    # Service related
    SERVICE_REQUEST_CREATED = "service_request_created"
    SERVICE_REQUEST_ASSIGNED = "service_request_assigned"
    SERVICE_COMPLETED = "service_completed"

    # Warranty related
    WARRANTY_EXPIRY_REMINDER = "warranty_expiry_reminder"
    AMC_RENEWAL_REMINDER = "amc_renewal_reminder"

    # Marketing
    PROMOTIONAL = "promotional"
    CAMPAIGN = "campaign"


# SMS Templates
SMS_TEMPLATES = {
    NotificationType.ORDER_CONFIRMED: (
        "Dear {customer_name}, your order #{order_number} has been confirmed. "
        "Total: Rs.{amount}. Thank you for shopping with Aquapurite!"
    ),
    NotificationType.ORDER_SHIPPED: (
        "Your order #{order_number} has been shipped via {transporter}. "
        "Track: {tracking_url}"
    ),
    NotificationType.ORDER_DELIVERED: (
        "Dear {customer_name}, your order #{order_number} has been delivered. "
        "Installation will be scheduled within 2 days. Installation ID: {installation_number}"
    ),
    NotificationType.INSTALLATION_SCHEDULED: (
        "Your installation #{installation_number} is scheduled for {scheduled_date} "
        "between {time_slot}. Our technician will contact you before arriving."
    ),
    NotificationType.INSTALLATION_REMINDER: (
        "Reminder: Your installation is scheduled for tomorrow ({scheduled_date}). "
        "Please ensure someone is available at the installation address."
    ),
    NotificationType.INSTALLATION_COMPLETED: (
        "Installation complete! Your {product_name} has been installed. "
        "Warranty valid until {warranty_end_date}. Rate your experience: {feedback_link}"
    ),
    NotificationType.TECHNICIAN_ASSIGNED: (
        "Technician {technician_name} ({technician_phone}) has been assigned "
        "for your installation/service. They will contact you shortly."
    ),
    NotificationType.TECHNICIAN_ON_THE_WAY: (
        "Our technician {technician_name} is on the way to your location. "
        "Expected arrival: {eta}"
    ),
    NotificationType.SERVICE_REQUEST_CREATED: (
        "Your service request #{request_number} has been created. "
        "We will assign a technician shortly."
    ),
    NotificationType.SERVICE_COMPLETED: (
        "Your service request #{request_number} has been completed. "
        "Rate your experience: {feedback_link}"
    ),
    NotificationType.WARRANTY_EXPIRY_REMINDER: (
        "Reminder: Your warranty for {product_name} (S/N: {serial_number}) "
        "expires on {expiry_date}. Extend your warranty now!"
    ),
}


class NotificationService:
    """
    Service for sending notifications to customers.

    In production, this would integrate with:
    - MSG91/Twilio for SMS
    - SendGrid/SES for Email
    - Firebase FCM for Push
    - WhatsApp Business API
    """

    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def send_notification(
        self,
        recipient_phone: str,
        recipient_email: Optional[str],
        notification_type: NotificationType,
        channel: NotificationChannel,
        template_data: Dict[str, Any],
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a notification to a customer.

        Args:
            recipient_phone: Customer phone number
            recipient_email: Customer email address
            notification_type: Type of notification
            channel: Delivery channel (SMS, Email, etc.)
            template_data: Data to populate the template
            custom_message: Optional custom message override

        Returns:
            Dict with send status and message ID
        """
        notification_id = str(uuid4())

        # Get message content
        if custom_message:
            message = custom_message
        else:
            template = SMS_TEMPLATES.get(notification_type, "")
            try:
                message = template.format(**template_data)
            except KeyError as e:
                logger.warning(f"Missing template variable: {e}")
                message = template

        # Log the notification (in production, send via actual provider)
        log_entry = {
            "notification_id": notification_id,
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel.value,
            "type": notification_type.value,
            "recipient_phone": recipient_phone,
            "recipient_email": recipient_email,
            "message": message,
            "status": "sent",  # In production, track actual delivery status
        }

        logger.info(f"[NOTIFICATION] {channel.value.upper()} to {recipient_phone}: {message[:100]}...")

        # In production, call actual provider APIs here
        if channel == NotificationChannel.SMS:
            await self._send_sms(recipient_phone, message)
        elif channel == NotificationChannel.EMAIL:
            await self._send_email(recipient_email, notification_type.value, message)
        elif channel == NotificationChannel.WHATSAPP:
            await self._send_whatsapp(recipient_phone, message)
        elif channel == NotificationChannel.PUSH:
            await self._send_push_notification(recipient_phone, notification_type.value, message)

        return {
            "success": True,
            "notification_id": notification_id,
            "channel": channel.value,
            "message": message,
        }

    async def send_order_delivered_notifications(
        self,
        customer_phone: str,
        customer_email: Optional[str],
        customer_name: str,
        order_number: str,
        installation_number: str,
    ) -> List[Dict[str, Any]]:
        """
        Send all notifications for order delivered event.
        """
        results = []

        # SMS notification
        sms_result = await self.send_notification(
            recipient_phone=customer_phone,
            recipient_email=customer_email,
            notification_type=NotificationType.ORDER_DELIVERED,
            channel=NotificationChannel.SMS,
            template_data={
                "customer_name": customer_name,
                "order_number": order_number,
                "installation_number": installation_number,
            }
        )
        results.append(sms_result)

        # Email notification (if email available)
        if customer_email:
            email_result = await self.send_notification(
                recipient_phone=customer_phone,
                recipient_email=customer_email,
                notification_type=NotificationType.ORDER_DELIVERED,
                channel=NotificationChannel.EMAIL,
                template_data={
                    "customer_name": customer_name,
                    "order_number": order_number,
                    "installation_number": installation_number,
                }
            )
            results.append(email_result)

        return results

    async def send_installation_scheduled_notification(
        self,
        customer_phone: str,
        customer_email: Optional[str],
        installation_number: str,
        scheduled_date: str,
        time_slot: str,
        technician_name: Optional[str] = None,
        technician_phone: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send notifications when installation is scheduled.
        """
        results = []

        # Installation scheduled SMS
        sms_result = await self.send_notification(
            recipient_phone=customer_phone,
            recipient_email=customer_email,
            notification_type=NotificationType.INSTALLATION_SCHEDULED,
            channel=NotificationChannel.SMS,
            template_data={
                "installation_number": installation_number,
                "scheduled_date": scheduled_date,
                "time_slot": time_slot,
            }
        )
        results.append(sms_result)

        # Technician assigned SMS (if assigned)
        if technician_name and technician_phone:
            tech_result = await self.send_notification(
                recipient_phone=customer_phone,
                recipient_email=customer_email,
                notification_type=NotificationType.TECHNICIAN_ASSIGNED,
                channel=NotificationChannel.SMS,
                template_data={
                    "technician_name": technician_name,
                    "technician_phone": technician_phone,
                }
            )
            results.append(tech_result)

        return results

    async def send_installation_completed_notification(
        self,
        customer_phone: str,
        customer_email: Optional[str],
        product_name: str,
        warranty_end_date: str,
        feedback_link: str = "https://aquapurite.com/feedback",
    ) -> List[Dict[str, Any]]:
        """
        Send notifications when installation is completed.
        """
        results = []

        sms_result = await self.send_notification(
            recipient_phone=customer_phone,
            recipient_email=customer_email,
            notification_type=NotificationType.INSTALLATION_COMPLETED,
            channel=NotificationChannel.SMS,
            template_data={
                "product_name": product_name,
                "warranty_end_date": warranty_end_date,
                "feedback_link": feedback_link,
            }
        )
        results.append(sms_result)

        return results

    # ==================== Provider Integration Stubs ====================

    async def _send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS via provider (MSG91, Twilio, etc.)

        In production, implement actual API call:
        - MSG91: POST to https://api.msg91.com/api/v5/flow/
        - Twilio: POST to https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json
        """
        logger.info(f"[SMS] Sending to {phone}: {message[:50]}...")
        # Placeholder - in production, call actual API
        return True

    async def _send_email(self, email: str, subject: str, body: str) -> bool:
        """
        Send email via provider (SendGrid, SES, SMTP).

        In production, implement actual API call:
        - SendGrid: POST to https://api.sendgrid.com/v3/mail/send
        - SES: Use boto3 ses.send_email()
        """
        logger.info(f"[EMAIL] Sending to {email}: Subject={subject}")
        # Placeholder - in production, call actual API
        return True

    async def _send_whatsapp(self, phone: str, message: str) -> bool:
        """
        Send WhatsApp message via Business API.

        In production, implement actual API call to WhatsApp Business API
        or providers like Gupshup, Twilio, etc.
        """
        logger.info(f"[WHATSAPP] Sending to {phone}: {message[:50]}...")
        # Placeholder - in production, call actual API
        return True

    async def _send_push_notification(
        self,
        device_token: str,
        title: str,
        body: str
    ) -> bool:
        """
        Send push notification via Firebase FCM.

        In production, implement actual Firebase Admin SDK call.
        """
        logger.info(f"[PUSH] Sending: Title={title}, Body={body[:50]}...")
        # Placeholder - in production, call Firebase Admin SDK
        return True


# Convenience functions for use in other services
async def notify_order_delivered(
    db: AsyncSession,
    customer_phone: str,
    customer_email: Optional[str],
    customer_name: str,
    order_number: str,
    installation_number: str,
) -> List[Dict[str, Any]]:
    """Send order delivered notifications."""
    service = NotificationService(db)
    return await service.send_order_delivered_notifications(
        customer_phone=customer_phone,
        customer_email=customer_email,
        customer_name=customer_name,
        order_number=order_number,
        installation_number=installation_number,
    )


async def notify_installation_scheduled(
    db: AsyncSession,
    customer_phone: str,
    customer_email: Optional[str],
    installation_number: str,
    scheduled_date: str,
    time_slot: str,
    technician_name: Optional[str] = None,
    technician_phone: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Send installation scheduled notifications."""
    service = NotificationService(db)
    return await service.send_installation_scheduled_notification(
        customer_phone=customer_phone,
        customer_email=customer_email,
        installation_number=installation_number,
        scheduled_date=scheduled_date,
        time_slot=time_slot,
        technician_name=technician_name,
        technician_phone=technician_phone,
    )
